# 協作指南

這個 repo 是公開的流程與工具 repo；臨床影像、原始 cohort、mask、DuckDB、模型權重、工作清單和其他 lake-derived artifacts 留在受控環境，不要上傳到 GitHub。

## 第一次加入

先讀以下順序：

1. [`README.md`](README.md)：專案範圍與目前已實作功能。
2. [`DATA_CATALOG.md`](DATA_CATALOG.md)：資料來源、index visit、統計分母與資料邊界。
3. [`docs/00-overview.md`](docs/00-overview.md)：G0–G5 關卡與角色責任。
4. [`docs/01-prepare.md`](docs/01-prepare.md)：候選清單、完整性與患者分區。
5. [`docs/06-implementation-plan.md`](docs/06-implementation-plan.md)：工作包與建議開發順序。
6. [`docs/08-image-classification-experiments.md`](docs/08-image-classification-experiments.md)：CRC LST 影像分類的 endpoint、ROI、multimodal、aggregation 與評估規格。
7. [`schemas/records.md`](schemas/records.md)：CSV/JSONL 欄位和狀態契約。

建立自己的環境，不要修改系統 Python：

```bash
python3 --version                 # Python 3.11+
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHON=.venv/bin/python make verify
```

沒有 lake 存取權也可以完成本地驗證。未安裝 DuckDB 時，只有資料連線的 synthetic test 會 skip；安全測試和語法檢查仍應通過。

## 資料與隱私邊界

- 外部 lake 以 `--lake-root` 明確指定，exporter 只讀取 DuckDB 和影像，不修改 lake。
- 使用 `image_id` 和假名化 `patient_key`；不要在 issue、PR、commit、截圖或 log 放姓名、病歷號、原始路徑、診療日期或可回推身份的內容。
- `/data/`、`/outputs/`、`/masks/`、資料庫、影像與模型檔案都是本機產物。即使 Git ignore，也要在分享前檢查 `git status --short --ignored`。
- `.gitignore` 是最後一道防線，不是資料治理；任何不確定的檔案先停止分享並詢問專案負責人。

## 分支與單一 writer

每個 working tree 同一時間只能有一位寫入者。開始工作前：

```bash
git status --short --branch
git switch -c feat/<short-name>
./scripts/verify.sh
```

不要在別人持有 writer 時修改同一個 working tree；平行工作使用不同 branch/worktree。不要用 `git reset --hard`、`git checkout --` 或其他方式丟棄既有變更。除非負責人明確要求，不要建立 checkpoint commit。

## 建議工作循環

1. 在 [`HANDOVER.md`](HANDOVER.md) 確認目標、writer 狀態與已知風險。
2. 先用合成資料和小測試驗證資料契約，再連接外部 lake。
3. 以 `image_id`/`patient_key` join；不要用 CSV 行號、資料夾名稱或「最後一筆」猜結果。
4. `unknown`、`uncertain`、`pending` 和錯誤列保留原狀，不轉成 negative 或 usable。
5. 每次變更後執行 `PYTHON=.venv/bin/python make verify`，並檢查完整 diff。
6. 交接前更新 handoff 的 objective、完成項、驗證命令、已知問題、dirty files 和下一個確切動作，最後將 `Writer` 設為 `RELEASED`。

## 第一個資料連線 smoke test

只在取得核准的 lake 路徑後執行，且輸出放在 ignored runtime directory：

```bash
CLEAN_RUN=outputs/pilot-001
mkdir -p "$CLEAN_RUN"
test ! -e "$CLEAN_RUN/candidates.csv" && \
.venv/bin/python scripts/export_lake_manifest.py \
  --lake-root /path/to/clinical-image-lake \
  --source-id colon-esd-t1crc-cropped-v0.1.0 \
  --limit 3 --output "$CLEAN_RUN/candidates.csv"
```

這只是確認 metadata、影像路徑和 exporter 接線，不是隨機樣本、模型評估或訓練資料。exporter 會拒絕覆寫既有輸出；需要新結果時改用新的 `run_id`。

## Pull request / handoff checklist

- [ ] 變更沒有包含臨床影像、private lineage、mask、模型權重、資料庫或生成清單。
- [ ] `PYTHON=.venv/bin/python make verify` PASS，並記錄任何被 skip 的資料連線測試。
- [ ] 測試使用合成圖或假的 patient key，沒有把真實資料寫入 repo。
- [ ] schema、protocol、model、threshold 或資料選擇變更有版本與理由。
- [ ] 影像分類變更遵守 patient/lesion-level split，沒有把同一 lesion 的 frame 或 augmentation 分散到不同 split。
- [ ] 新增的 modality、ROI、device 或 lesion grouping metadata 有來源、版本與 unknown/pending 行為。
- [ ] README、相關操作章節和 `HANDOVER.md` 已同步。
- [ ] handoff 已列出最後成功階段、失敗/待處理項目、下一個確切命令，Writer 已 RELEASED。
