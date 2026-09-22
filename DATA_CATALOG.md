# 資料目錄與分類 Menu

這一頁回答「有哪些資料、怎麼挑出來、現在在哪裡、下一步能不能拿去訓練」。數字都要連同統計單位一起讀：patient root、exam 子資料夾、影像檔、去重後登記影像是四種不同東西。

## 目錄

| Menu | 內容 | 主要位置 |
|---|---|---|
| A. 資料來源 | ESD 與 T1CRC 原始 cohort 的來源和用途 | lake repo `data/` |
| B. Index visit 篩選 | 日期欄位、容差、保留與 quarantine 規則 | lake repo `data/colon-cohort-reports/` |
| C. 影像處理沿革 | raw → crop/OCR → 去重 → lake 登記 | lake repo `artifacts/`、`shared_image_lake/` |
| D. 品質分類 | blur、解碼、污物/曝光和人工品質狀態 | lake QC + 本 repo review records |
| E. 任務分類 | retrieval、segmentation、expert final 的狀態 | 本 repo `schemas/records.md` |
| F. 目前統計 | 已核對的數字和分母 | 本頁；新批次重查 lake |
| G. 工程入口 | 要再跑什麼、哪些仍待開發 | `docs/01-prepare.md`、`docs/06-implementation-plan.md` |

## A. 資料來源

### `colon-esd-cohort`

ESD 來源的 raw colonoscopy tree。index date 取自 `COHORT_MASTER.index_exam_date`（必要時依人工 chart review 修正），影像經日期比對後才進入 index-visit pool。這個資料夾仍是 raw/clinical data，禁止直接放進 Git 或交給標註工具。

### `colon-t1crc-cohort`

T1CRC 來源的 raw colonoscopy tree。index date 依 `T1_CRC_CODED` 中 `Cancer or Not = 1` 的日期判定，再與病人 exam 子資料夾日期比對。它和 ESD 使用相同的後續去識別化、blur QC 和登記流程，但來源欄位規則不同。

### `colon-esd-t1crc-cropped-v0.1.0`

兩個 cohort 的 index-visit 影像經裝置版面裁切、OCR fail-closed 驗證、HMAC 假名化後形成的標準 release。它是下游任務的影像來源，不是病灶標籤資料集；病灶存在與否、品質 review 和 segmentation mask 在本 repo 管理。

### `crc_lst_pathology_classification`

這是歷史上曾登記過的另一個資料來源。其 31,363 筆 rendition 已從目前 lake 退休，以避免同一 source frame 有兩份不同裁切版本；它保留在原本的下游專案，不應再從目前 lake 查到。若看到舊文件提到它，先確認文件日期和資料庫實際 `source_id`。

## B. Index visit 篩選規則

這次整理的概念是「每位病人保留 index 訪視」，不是把所有檢查日期混在一起。

| Cohort | index date 來源 | 與 local exam date 比對 | 目的 |
|---|---|---|---|
| ESD | `COHORT_MASTER.index_exam_date` | `+0/+1/+2` 天容差 | 處理系統性日期偏移；只留對應 index exam |
| T1CRC | `T1_CRC_CODED` 的 `Cancer or Not = 1` 日期 | 同一套日期比對原則 | 以 coded cancer visit 對應影像 exam |

日期容差不是影像品質條件，也不是病灶標籤。當時觀察到約 45% 的 ESD 病人有一致的 +1/+2 日偏移，因此採用已確認的容差。沒有任何 local date match 的個案經人工 chart review；不能把未判定資料自動當成 negative。

保留的 exam 子資料夾留在 active cohort tree；非 index exam 子資料夾是搬移，不是刪除，位於：

```text
/home/a01949/projects/clinical-image-lake/data/.non-index-quarantine/<cohort>/<patient_root>/<exam_folder>/
```

完整回復對照表：`data/colon-cohort-reports/non_index_quarantine_manifest.csv`。每列記錄原始 `src` 和 quarantine `dst`；要復原時先人工確認，再依 manifest 還原，禁止用模糊 glob 批次搬動。

## C. 已核對的資料處理沿革

```text
raw active cohort
  ├─ index-date match (+0/+1/+2 days)
  ├─ non-index quarantine (recoverable)
  └─ blur score / index image manifest
          43,994 raw images
             ↓ device-label × resolution crop measurement + OCR verification
          43,872 cropped/de-identified frames
             ↓ exact-content duplicate exclusion (41 frames)
          43,831 images registered in shared_image_lake
```

| 階段 | ESD | T1CRC | 合計 | 統計單位/說明 |
|---|---:|---:|---:|---|
| active raw patient roots | 575 | 68 | 643 | root folders；不是 image count |
| active raw exam subfolders | 584 | 68 | 652 | 目前 tree 的 exam directories；可能包含無影像子資料夾 |
| index image manifest | 40,455 | 3,539 | 43,994 | 有列入 manifest 的 raw image files |
| crop/OCR 成功 | 40,443 | 3,429 | 43,872 | 122 張因 7 個版面群組量測失敗而排除 |
| registered after exact dedup | — | — | 43,831 | 41 exact duplicate-content frames 未登記 |
| lake distinct patients | — | — | 571 | `source_id=colon-esd-t1crc-cropped-v0.1.0` |

ESD/T1CRC 的分列影像數來自現有 index manifest；去識別化 output 的 cohort 分布有其自己的 manifest 统计。工程師每次新批次都要重新查詢，不能把本表當成永遠不變的資料庫快照。

非 index quarantine 目前有 767 筆子資料夾、18,627 張影像，仍可還原。它們不是「刪除資料」，也不是 negative training set。

## D. 影像品質分類

品質和病灶存在是兩個軸：一張圖可以 `lesion_present=yes` 但 `quality_status=exclude`，也可以沒有病灶但影像品質很好。

| 層級 | 狀態 | 意義 | 是否可直接進 segmentation training |
|---|---|---|---|
| Lake blur QC | `blur_is_usable=true` | 既有 KS blur method 未標記為模糊 | 否；仍需任務品質 review |
| Lake blur QC | `false` | 可能模糊；KS 分數越低通常越模糊 | 否，除非專家另有明確政策 |
| Lake blur QC | 空值/unknown | 沒有可用 blur 判定 | 否；補測或人工審核 |
| Task quality review | `usable` | 對指定任務足夠清楚 | 可進下一階段，但仍需 mask 定稿 |
| Task quality review | `exclude` | blur、污物、過曝、反光、視野或其他缺陷妨礙任務 | 否；保留原因 |
| Task quality review | `uncertain` | 專家無法安全判定 | 否；送覆核 |

blur 只是提示，不會自動判定污物、過曝或病灶邊界。這些原因在 [品質手冊](docs/03-quality.md) 中分別記錄；未知不能轉成通過或 negative。

## E. 任務分類與挑選順序

下游 image-level 的狀態依序建立：

1. `lesion_present=yes/no/uncertain`：專家判影像內是否看得到本任務目標病灶。retrieval 分數只能產生排序或建議。
2. `quality_status=usable/exclude/uncertain`：判斷影像是否適合指定訓練用途；病灶存在判定不因品質差而改成 no。
3. `segmentation_review=accepted/corrected/rejected`：模型 proposal 或人工 mask 經專家審核的結果。
4. `image_finalization`：確認該張所有可見目標 instance 都已處理，沒有 pending adjudication。
5. `disposition=released/negative_retained/quality_excluded/out_of_scope/pending_review/processing_error`：每張候選在某一個 frozen revision 恰有一個去向。

第一版 lesion segmentation training 的聯合條件是：影像完整性通過、專家 `lesion_present=yes`、品質 `usable`、所有病灶 instance 為 `accepted/corrected`、mask 尺寸和值域合法、患者分區已凍結。no/uncertain、品質排除、尚未裁決資料都保留紀錄但不進該 release。

## F. 你可以用哪個數字

| 想回答的問題 | 應查的來源 | 使用的分母 |
|---|---|---|
| raw tree 有多少病人資料夾？ | `find data/<cohort> -mindepth 1 -maxdepth 1 -type d` | root folder |
| 有多少 exam 子資料夾？ | `find data/<cohort> -mindepth 2 -maxdepth 2 -type d` | exam directory |
| 有多少 index raw images？ | `index_visit_images_manifest.csv` | manifest rows |
| 有多少可用標準影像在 lake？ | DuckDB `images_master` 按 `source_id` | registered image rows |
| 有多少病人？ | `count(distinct patient_key)` | pseudonymous patient key |
| 有多少被排除的非 index 圖？ | `non_index_quarantine_manifest.csv` 的 `image_count` 總和 | quarantined image files |

推薦查詢（在 lake repo 執行，DuckDB 位於主 repo）：

```bash
/home/a01949/projects/clinical-image-lake/.venv/bin/python - <<'PY'
import duckdb
con = duckdb.connect('/home/a01949/projects/clinical-image-lake/shared_image_lake/metadata/dataset_metadata.duckdb', read_only=True)
print(con.execute('''
SELECT source_id, count(*) AS images, count(DISTINCT patient_key) AS patients
FROM images_master GROUP BY source_id ORDER BY source_id
''').fetchdf().to_string(index=False))
con.close()
PY
```

## G. 變更規則

這頁的數字是一次整理的可核對 snapshot；新 cohort、新日期規則、新 crop box、新 QC threshold 或新 dedup policy 都要新增 `run_id`/decision entry，不能直接改舊數字。若報告中使用「保留 652 個資料夾」，必須寫成「652 個 exam 子資料夾（ESD 584 + T1CRC 68）」並另列 raw patient roots 和有影像 manifest rows。

資料目錄不包含病歷號、姓名或 private lineage；它只描述假名化 lake 和 raw tree 的結構。標註資料、mask 和 train/val/test split 仍由本 repo 的 task records 管理。
