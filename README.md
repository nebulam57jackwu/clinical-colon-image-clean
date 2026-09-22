# Clinical colon image clean

GitHub repository: https://github.com/nebulam57jackwu/clinical-colon-image-clean

資料內容總覽與篩選沿革請先看 [資料目錄與分類 Menu](DATA_CATALOG.md)。它把 raw cohort、index visit、quarantine、去識別化版本和下游訓練資格分開說明，並標示每個數字的統計單位。

供學弟工程師執行大腸鏡影像整理的子專案：**影像檢索初篩 → 訓練品質審核 → 病灶分割提案 → 專家修正定稿 → 可追溯的訓練清單**。

影像由相鄰的 `clinical-image-lake` repo 提供，使用 `image_id` 和假名化 `patient_key` 串接；任務標籤、遮罩與審核紀錄留在本 repo。原始主影像維持一份，篩除是紀錄判定，不刪檔。

## 學弟從這裡開始

1. 先讀 [操作總覽與分工](docs/00-overview.md)，理解各階段何時可以往下走。
2. 按 [環境、候選清單與抽樣](docs/01-prepare.md) 完成第一次小批次匯出。
3. 與醫師依 [病灶檢索與校準](docs/02-retrieval.md) 建立範例庫，依 [影像品質判讀](docs/03-quality.md) 校準可用標準。
4. 按 [模型分割與專家修正](docs/04-segmentation-review.md) 產出遮罩，再依 [標註操作、格式轉換與多人覆核細則](docs/07-annotation-format.md) 完成往返及定稿。
5. 按 [驗收、交付與故障處理](docs/05-release-operations.md) 核對數量、版本與輸出。

要接手寫程式，另讀 [工程開發工作包](docs/06-implementation-plan.md) 和 [資料欄位契約](schemas/records.md)。每個批次複製 [批次紀錄表](templates/batch-record.md)，每次專家會議使用 [標註規範與校準表](templates/annotation-protocol.md)；分歧填 [多人覆核與裁決表](templates/review-adjudication.md)，發布前逐項填 [訓練集驗收表](templates/release-checklist.md)。本 repo 的 `Makefile verify` 只驗證 Python 語法和 whitespace；影像庫資料與模型環境需另外驗證。

## 已能執行與尚待開發

| 功能 | 目前狀態 |
|---|---|
| 讀取 lake 並匯出假名化候選清單 | **已實作**：`scripts/export_lake_manifest.py`；曾以 3 筆索引冒煙測試 |
| Walsh–Hadamard / KS 模糊分數 | **lake repo 已有**：`../clinical-image-lake/scripts/blur_detection/detect_blur.py`；門檻仍須針對本任務校準 |
| 患者抽樣與分區、影像解碼/雜湊全量驗證 | **待開發**：已有手冊與驗收契約 |
| Encoder、向量索引、檢索排序與閾值校準 | **待開發** |
| 污物、曝光、反光指標與綜合品質決策 | **待開發**；先以專家審核資料建立標準 |
| SAM adapter、標註工具匯入匯出、專家定稿閘門 | **待開發** |
| 訓練集版本化匯出與全流程自動驗收 | **待開發** |

手冊是完整實作與操作規劃，**目前不是已能一鍵跑完的 pipeline**。`configs/pipeline.yaml` 是規劃設定，現有匯出 CLI 不會讀取它；設定中的 `null` 表示尚未選型或校準，不能當作 0 或已通過。

## 第一個可執行命令

以下命令在這個子 repo 根目錄執行。它預設尋找同一層的 `../clinical-image-lake/`；若 lake 在其他位置，使用 `--lake-root` 或設定 `CLINICAL_IMAGE_LAKE_ROOT`。第一次先檢查目標檔不存在，以免既有 CLI 覆寫舊清單：

```bash
CLEAN_RUN=outputs/pilot-001
mkdir -p "$CLEAN_RUN"
test ! -e "$CLEAN_RUN/candidates.csv" && \
.venv/bin/python scripts/export_lake_manifest.py \
  --source-id colon-esd-t1crc-cropped-v0.1.0 \
  --limit 100 --output "$CLEAN_RUN/candidates.csv"
```

這是依 `image_id` 排序的 100 筆連通性測試，不是隨機研究樣本。正式抽樣要按患者分組，詳見第 1 章。MacBook 可作 SSH 操作端；候選圖與模型推論在有 lake 路徑和計算環境的伺服器上處理。

模型資料查核日期：2026-09-17。靜態影像比較 SAM 2.1、SAM 3 image 與適合的醫療候選；SAM 3.1 的 Object Multiplex 屬影片追蹤更新，不能只依版本號宣稱其為本地大腸鏡病灶分割 SOTA。來源及選型方法見第 4 章。
