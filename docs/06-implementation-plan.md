# 6. 工程開發清單、依賴與驗收

本章是工程規格，不是已提供的命令列工具。除候選匯出及主 repo 的 blur 腳本外，下表所列模組尚待開發。`configs/pipeline.yaml` 是待實作的設定契約；現有 exporter 只讀 CLI 參數。

## 6.1 開發順序與最小可用版本

```text
WP00 判讀規範 ───────────────────────────────────────┐
WP01 候選/完整性 → WP02 患者分區 → WP03 檢索           │
                                      ↓              │
                                 WP04 品質           │
                                      ↓              │
                                 WP05 模型提案       │
                                      ↓              │
WP06 標註往返/覆核 ←──────────────────────────────────┘
                  ↓
WP07 訓練交付/驗收 → WP08 批次恢復/監控
```

**人工可用版本**先完成 WP00、01、02、06、07：人工判讀可見性、品質和畫 mask，先交付一個可追溯小批次。再加 WP03、04、05 減少工時。不要等模型全接好才發現 ID 對不上或工具匯出不了正確遮罩。

## 6.2 工作包

| 工作包 | 要實作的功能 | 輸入 → 輸出 | 完成證據 |
|---|---|---|---|
| WP00 規範定版 | 醫師定目標病灶、邊界、品質級別；工程師建列舉/表單 | 分層例圖 → `protocol_version`、共識例圖、簽署紀錄 | 30–50 張共識試標，分歧有裁決；例圖存 ignored outputs |
| WP01 候選完整性 | 擴充既有 exporter：拒絕覆寫、原子寫檔、實體路徑限制、decode/尺寸/hash 檢查、錯誤帳本 | lake/來源 → candidates v0.1、integrity、errors、run metadata | 不可讀圖、變更 hash、symlink 逃逸均被記錄；正常列數守恆；DB 唯讀 |
| WP02 患者分區 | 固定 seed 按 patient 分角色；跨來源同患者綁定；代表性/難例抽樣分開 | candidates → partitions、sampling manifest | 重跑一致、分區無患者交集、追加來源不移動已凍結患者、未知 metadata 保留 |
| WP03 檢索 | Encoder adapter、可恢復 embedding、精確 cosine、排除同患者、三態分流、校準報告 | exemplars/partitions → embeddings/index、predictions、threshold report | 小矩陣已知近鄰排序正確；自我/同患者排除；NaN/零向量與不足範例不判 no |
| WP04 品質 | 接既有 KS 及 manifest adapter；有效視野、亮/暗/反光指標；人工缺陷表單 | candidates/lesion review → quality metrics/review | 真/假/未知區分；不同 method 分數不混用；全圖與 ROI 分母明確；髒污模型未有前走人工 |
| WP05 分割 | 可替換 SAM adapter、固定 prompt 座標、還原原圖、逐病灶 proposal | yes+usable+prompts → proposals/masks | 非方形/圖緣/多病灶幾何正確；空 mask 是錯誤提案；模型/權重/提示可重建 |
| WP06 標註覆核 | 標註工具 mapping、PNG/工具格式轉換、雙人指派、裁決、不可變 review event | proposals 或人工 → review events/final masks/image finalization | 合成圖往返像素相等；彩色/調色盤解碼正確；缺失/重複 ID 阻擋；審核衝突不能靜默覆寫 |
| WP07 Release | 固定 revision join、semantic union、train/val/test、hash 和資料卡、聯合閘門 | final masks/approved reviews → release | 任一未核准/跨患者洩漏/非法 mask 拒絕；凍結版本不能覆寫；100% 列可追溯 |
| WP08 批次運維 | idempotent cache、resume、失敗重試、統計、來源漂移報告 | run artifacts → resume plan/report | 中斷後無漏列/重複 final；重跑不改專家定稿；數量守恆 |

## 6.3 各工作包應提供的介面

以下是**預定 Python 介面**，不是可直接執行的现有函式：

```text
validate_candidates(manifest, repo_root) -> integrity, errors
assign_patient_partitions(candidates, seed, previous_partitions=None) -> partitions
encode_images(manifest, encoder_config) -> embeddings, embedding_index, errors
retrieve(query_embeddings, exemplar_embeddings, patient_keys, config) -> predictions
calibrate(predictions, expert_labels, calibration_patients, targets) -> thresholds, report
score_quality(manifest, methods, config) -> metrics, errors
propose_masks(approved_images, prompts, model_config) -> proposals, errors
import_tool_export(archive, mapping, labelmap, config) -> draft_masks, conversion_report
finalize_review(review_events, chosen_revisions, protocol) -> finalization
validate_release(release_manifest, artifacts, partitions) -> report
```

共通要求：按主鍵 join；錯誤逐列回傳；寫檔先暫存後原子化；預設拒絕覆寫；cache 必須涵蓋來源 hash、模型與前處理；`null` 閾值拒絕自動分流。支援 dry-run 的寫入工具先列輸入/輸出/既有產物，不把 dry-run 當成功發布。

## 6.4 有意義的測試清單

測試使用合成圖與假的患者 key，不提交真實病人圖。每個工作包完成時加入與風險相符的測試：

- 資料層：少一張原圖、同 ID 多列、unknown QC、來源空集、同患者跨來源、路徑穿越、同輸出不可覆寫。
- 檢索：自我近鄰、同患者排除、正負範例不足、ties 固定排序、向量行序錯置、非有限向量、校準患者混進範例庫。
- 品質：全黑/全白/局部亮點、真實視野未知、blur 值方向、0 與 missing 不混淆；合成圖只驗指標運算，不宣稱臨床校準。
- Mask：640×480 非方形、點在角落、兩病灶、洞、uint8 {0,1}、0/255 mapping、P-mode palette、RGB labelmap、未知色、重複檔名、旋轉/縮放、空/全圖 mask。
- 覆核：兩位覆核者相同帳號、未完成第二覆核、裁決未簽、舊 revision 被改、圖有一個病灶漏審、PNG hash 變更。
- 發布：把 proposed/uncertain/error 混進來必須失敗；同患者跨 split 失敗；取 approved instances union 正確；重跑 hash 一致；固定版本拒覆寫。

模型整合另跑 20 張專家已確認的小樣本做可視化檢查。單元測試過關證明接線與契約，不證明病灶判讀或邊界正確。

## 6.5 里程碑與工時估算

以下是假設一位熟悉 Python 的工程師、既有伺服器可用、專家每週有兩次校準會議的起始估算，取得權重/標註人力可能改變時程。

| 里程碑 | 建議投入 | 可交付內容 |
|---|---|---|
| M1 人工流程閉環 | 工程約 3–5 工作天，另排專家時間 | WP00/01/02/06 最小實作，20 張完整往返與人工定稿 |
| M2 首份可追溯資料 | 工程約 3–5 工作天 | WP07、100–200 張試標，分類/品質/分割一致與首份驗收 |
| M3 模型輔助版本 | 工程約 1–2 週，依環境調整 | WP03/04/05、一組凍結設定和校準報告，與人工工時比較 |
| M4 正式批次 | 依資料量與專家可用時間估算 | WP08、分層監控、完整審核與發布 |

先實測每張專家秒數，再估算：`總人工小時 ≈ (初審圖數×初審秒 + mask數×修正秒 + 雙審圖數×雙審秒 + 裁決圖數×裁決秒)/3600`。另加準備/會議/返工時間。不要用 GPU 每秒幾張推算專家工作量。

## 6.6 接手第一天的具體任務

讀第 0、1、7 章；確認候選匯出與已存在的 runtime 目錄；複製批次紀錄表；跑索引小批次；用兩張合成圖驗標註格式；安排 30–50 張共識會議。當天交付工程/專家各一份未解決事項清單；模型安裝可以往後排，但每個欄位的 ID、狀態與責任人要先定好。
