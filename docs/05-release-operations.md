# 5. 批次驗收、訓練交付與異常處理

## 5.1 每張圖必須有去向

使用互斥的 image-level 終態：`released/negative_retained/quality_excluded/out_of_scope/pending_review/processing_error`。多個原因可放 details，但計總數時每張只能有一個終態；重跑要記新的 revision，舊紀錄不刪。

```text
候選總數 = released + negative_retained + quality_excluded
         + out_of_scope + pending_review + processing_error
```

病灶數與影像數分開計；10 張有 12 個病灶不是漏資料。生產批次尚有 pending 是允許的，但未完成列不能混入 release；報表要明示覆核完成率。

## 5.2 可進入第一版分割訓練集的聯合條件

按 `image_id` 與凍結的 review revision join，不靠資料列順序或任意「最後一筆」。同時滿足：

1. 完整性檢查通過，image SHA256 與候選快照一致。
2. 專家 `lesion_present=yes`、`quality_status=usable`，有 reviewer、時間及規範版本。
3. 所有目標病灶 instance 均 `accepted` 或 `corrected`，image-level `all_instances_reviewed=true`；無未裁決分歧。
4. final mask 可讀、W/H 正確、0/1、非空，hash 一致，完整患者分區可追溯。
5. 標註者/覆核者符合任務規範；不能僅因工具顯示 completed 就視為專家簽署。

陰性圖以獨立 manifest 保留。第一版 lesion-only segmentation 不自動產生背景負樣本；若日後要納入，須明確把 no+usable 且已覆核的圖轉成空 mask，另記政策版本。未審核或 unknown 不能拿來當負樣本。

## 5.3 分區與版本發布

在第 1 章已固定的患者角色上建立下游 split：development 可作 train，calibration 可作 val，獨立 test 維持 test；記錄映射與哪些模型使用過哪些組。若拿 test 做過範例/訓練/調閾值，此 test 已被污染，需另設全新患者組或如實降級成開發評估。

資料不平衡時報每組病人、影像、病灶、成像模式與品質組成，不直接移動個別影像讓數字好看。抽樣少量代表帧或限制每患者影像數時要在分區內做，保存抽样規則與完整候選去向。

預定布局（發布 CLI 待開發）：

```text
outputs/<run_id>/
  config.snapshot.yaml, candidates.csv, candidates.sha256
  partitions.csv, integrity.csv, errors.csv
  retrieval_predictions.csv, lesion_review.csv
  quality_metrics.csv, quality_review.csv
  prompts.jsonl, segmentation_proposals.csv, segmentation_review.csv
  image_finalization.csv, disposition.csv, review_events.csv
  proposal_masks/, final_masks/, tool_exports/, reports/
outputs/releases/<release_id>/
  train.csv, val.csv, test.csv, negative_retained.csv
  manifest.sha256, artifact_hashes.csv, dataset-card.md
  configuration/, validation-report.md
```

release manifest 的每列至少有 image_id、patient_key、image_path、image_sha256、semantic mask 路徑/hash、來源 review revision、split、release_id。主影像路徑是 repo 相對；mask 路徑是子專案相對，讀取器不可混用基準。定稿 mask 所在 run 必須與 release 一起保留；搬遷時把所有 referenced artifacts 一併移轉並重驗 hash，不能只交 CSV。

版本目錄一旦存在即拒絕覆寫。產物先寫暫存、完成驗收後原子化改名；更新產生新版本。匯出者需固定引用原 revision，不以最新審核內容靜默改變既有 release。這是後續 CLI 的工程契約，目前既有候選匯出程式並未實作。

## 5.4 發布檢查表

| 檢查 | 通過條件 | 未通過時 |
|---|---|---|
| 數量守恆 | 所有候選均有互斥終態 | 查 join 漏列/錯誤跳過 |
| 主鍵 | image_id 和 instance/review 複合鍵符合契約 | 停止匯出，不任取一列 |
| 患者分區 | train/val/test 的 patient_key 交集為空 | 回分區修正；已訓練結果重評 |
| 來源及雜湊 | 原圖、mask、候選與設定快照一致 | 不覆寫舊 hash，調查改檔 |
| 專家定稿 | 所有納入圖完整簽署、所有病灶完成 | 回待覆核 |
| Mask | 尺寸/方向/值域正確、非空 | 回 adapter 或標註工具 |
| 檢索及 QC 指標 | 使用凍結門檻，分層結果與區間列出 | 人工處理，不能聲稱自動達標 |
| 使用限制 | 資料卡說明選樣偏差、排除規則與適用來源 | 補文件後再交付 |

資料卡要列候選/各去向數、患者/病灶數、來源時間範圍（僅可取得者）、白光/NBI未知比例、expert 規範版本、模型來源/權重、性能与樣本大小、尚未處理的疑難類別。不要只報一個平均 Dice。

## 5.5 異常對照表

| 現象 | 優先檢查 | 下一步 |
|---|---|---|
| DB locked | 另一程序是否寫入 DB | 協調既有 writer，稍後唯讀重試；不要刪 lock 或強殺 |
| 找不到 source_id | 盤點查詢與大小寫 | 修正來源，不改成掃整個 data/ |
| 匯出路徑不存在 | 是否在主 repo、影像掛載是否正常 | 修復挂載；不得用空圖替代 |
| 缺少 patient_key | lake 來源 metadata | 暫停該圖，交管理者補正；不自造新 patient key |
| embedding NaN/零值 | 解碼、前處理、精度、版本 | 記錯誤，以小批 FP32 排查，重跑有版本 |
| cosine 全很高卻分不開 | 重複患者、錯誤 normalize、背景主導 | 查近鄰，先修接線再討論模型 |
| no 桶發現病灶 | 閾值、來源/模式偏移、範例不足 | 擴大人工覆核，新版本校準 |
| blur 分數空/NaN | 指標失效 | unknown，不轉成清楚 |
| GPU out of memory | 模型/batch/input 尺寸 | 降 batch；若換解析度/模型需新設定和比較 |
| mask 旋轉/錯位/拉伸 | EXIF、W/H、resize/pad 反向轉換 | 停止該批，在非方形合成圖驗證 |
| CVAT 匯出变彩色/255 | labelmap 和工具格式 | 明確映射值，不用所有非零像素當 lesion |
| 模型成功但無 mask | 空輸出或 prompt 不足 | 記 empty_prediction，交人工；不能直接列 no |
| 專家不同意 | 規範模糊或邊界真的不清楚 | 專家裁決；未解決保持 pending |

## 5.6 重跑及交接

逐圖處理以 input hash/模型/前處理/規範版本決定是否可復用。只重試失敗列，仍核對整批守恆。已 final 的 mask 不因模型重跑而覆寫；新模型另建 proposal，專家決定是否更新 final。

每次交接提供 [批次紀錄表](../templates/batch-record.md)、最後成功階段、失敗 image_id 清單、下一個確切操作、模型與設定位置、需專家回答的問題。不要把「程式沒拋錯」當作資料已可訓練。
