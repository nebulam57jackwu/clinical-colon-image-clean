# 1. 環境、影像盤點與患者分區

## 1.1 執行前準備

操作者：工程師。輸入：指定的 `source_id`、repo 存取權、去識別化影像池。先在伺服器進入本子 repo 根目錄，確認以下命令成功：

```bash
pwd
.venv/bin/python --version
.venv/bin/python -c "import duckdb, PIL, numpy; print('base imports OK')"
.venv/bin/python scripts/export_lake_manifest.py --help
```

現有基礎環境要求 Python 3.11 以上，見根目錄 `pyproject.toml`。若 `.venv` 缺失，依主專案規範建立環境；不要在系統 Python 直接升級全機套件。GPU encoder/SAM 使用另一個固定版本環境，記錄 GPU 型號、可用 VRAM、driver、CUDA、PyTorch 和權重存放位置。先用 batch size 1 量測，再增加，不能預設某張卡能跑某個大型模型。

工程師只能從 `shared_image_lake/images` 取得本任務輸入。`data/` 原始影像和 `.private/` lineage 不是本流程的標註輸入；碰到燒錄文字殘留的圖，記 `privacy_suspect` 並交主專案處理。

## 1.2 唯讀盤點來源

以下為可執行的彙總查詢，沒有輸出患者識別欄位：

```bash
.venv/bin/python - <<'PY'
import duckdb
con = duckdb.connect('shared_image_lake/metadata/dataset_metadata.duckdb', read_only=True)
print(con.execute('''
SELECT m.source_id, count(*) AS images,
       count(DISTINCT m.patient_key) AS patients,
       count(*) FILTER (WHERE m.patient_key IS NULL) AS missing_patient,
       count(*) FILTER (WHERE q.is_usable IS NULL) AS unknown_blur_qc
FROM images_master m LEFT JOIN image_quality_qc q USING (image_id)
GROUP BY m.source_id ORDER BY m.source_id
''').fetchdf().to_string(index=False))
con.close()
PY
```

歷史交接曾記錄 43,831 張 / 571 位患者，但實際批次以這次查詢和候選清單為準。匯出欄位不含 `exam_key`、內視鏡設備、白光/NBI、病灶型態；需要分層時，新增經確認的任務 metadata，未知就保留 `unknown`，不可由舊資料夾名稱猜。

## 1.3 匯出小批次，再建立正式快照

```bash
CLEAN_RUN=outputs/pilot-001
mkdir -p "$CLEAN_RUN"
test ! -e "$CLEAN_RUN/candidates.csv" && \
.venv/bin/python scripts/export_lake_manifest.py \
  --source-id colon-esd-t1crc-cropped-v0.1.0 \
  --limit 100 --output "$CLEAN_RUN/candidates.csv"
cp projects/clinical-colon-image-clean/configs/pipeline.yaml "$CLEAN_RUN/config.snapshot.yaml"
sha256sum "$CLEAN_RUN/candidates.csv" > "$CLEAN_RUN/candidates.sha256"
```

`pilot-001` 已存在時另取新 `run_id`。正式全來源匯出使用新目錄，移除 `--limit 100`。不要拿前 100 張當代表性 cohort；CLI 是按 `image_id` 排序。

**现有 CLI 的界限**：唯讀開啟 DB、檢查非空患者 key、檔案存在和相對路徑、不允許 `..`。它會覆寫同名输出，尚無影像解碼、實體 symlink 逃逸檢查、重新計算 SHA256、患者抽樣或設定檔載入；前述 `test ! -e` 是目前操作保護，不是完整的原子化發布機制。程式開發需求見工作包 WP01。

## 1.4 建立影像完整性清單（待開發；先人工小批次）

1. 逐列用 `image_id` 對到原圖，不以行號 join。
2. `Pillow` 完整 decode，核對像素尺寸與 DB；另記 RGB/灰階/alpha 與 EXIF 方向。
3. 用影像檔案 bytes 計算 SHA256，對照 `content_sha256`；舊值為空要標記，不自行補寫主庫。
4. 解析實體路徑，必須仍在核准影像池內。讀不到、hash 不符、方向/尺寸不符的圖進 `errors.csv`，保留原列，暫停該圖。
5. 不自動做 EXIF transpose、銳化、調色或再裁切後覆蓋原圖。模型輸入 resize 僅在記憶體中，保留反向座標轉換。

產出 `integrity.csv`、`errors.csv`。驗收：每張候選都有 `ok` 或明確錯誤；錯誤不能被當作陰性或品質合格。

## 1.5 患者分區與抽樣

先固定患者角色，再挑影像。建議起始分配 **development 60%、calibration 20%、test 20%**，用固定 seed 20260917；比例可在第一次專家會議調整，之後記錄 `partition_version`。這是規劃值，小 cohort 應先評估每組陽性患者數是否足夠。

- Development：選 exemplar、選 encoder、訓練品質模型或分割模型；需要調模型時在此組內另做患者分組驗證。
- Calibration：只在模型/特徵定版後定檢索與 QC 閾值。不得放進 exemplar，也不拿來訓練。
- Test：凍結後只做最終評估，不能看結果後再調門檻並繼續宣稱同一測試集是獨立測試。

不同来源的同一 `patient_key` 必須同組。近似重複影像若跨患者 key，要先查身份/重複資料問題，不要默默刪其中一筆。序列近重複可減少人工重複工作，但仍保留每張影像的去向。**新檢查或新來源也不能把已出現在 development 的患者當新測試患者。**

建議先以 40–60 位 development 患者、每位最多 10–20 張作 400–1,000 張起始人工標註池；樣本不足就如實記錄。涵蓋白光/NBI/未知、不同品質、大小病灶、器械與切除後影像。每個亞組的資料量由實際可得性決定，不為湊數而假造標籤。

**兩份抽樣要分開保存**：代表性隨機抽樣供漏判率、工作量估算；難例加抽樣供模型改善。難例富集集的 precision 和疾病比例不能直接宣稱為全 cohort 表現。患者多圖是群聚資料，報告信賴區間以患者為重抽樣單位。

## 1.6 最低驗收

候選 `image_id` 唯一；缺失患者 key 為 0；三個角色患者交集為空；所有樣本記錄抽樣方式/seed；未解決的完整性錯誤不進模型。首次 20 張人工打開比對原圖、索引、尺寸和 ID，確認接線正確，再擴量。
