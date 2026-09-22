# 資料契約：候選 v0.1；新規劃審核產物 v0.2

本檔是後續工程實作的介面契約；目前只有 `candidates.csv` 由既有 exporter 實際產生。v0.2 其餘產物與驗證器尚待實作。原先 README 的審核 v0.1 是草案；若已有使用者自行製作的 v0.1 review，轉版必須明確映射、補齊簽署，不能只改版本字串。

## 共同規則

CSV 為 UTF-8，標準 quoting；缺值以空欄位表示，不用 `NaN`、`None`、字串 `null` 或 0 代替。小數必須有限。v0.2 bool 用小寫 `true/false`，時間用有時區的 ISO 8601 UTC（例如 `2026-09-17T08:00:00Z`）。JSON array/object 放在正確引號包住的 CSV 欄位或 JSONL，不用逗號拆字串。

v0.2 每份表均有 `schema_version,run_id`，逐圖表加 `image_id`；以下各表的「其他欄位」不重複列共通欄位。每個 run 有 `run-metadata.yaml`：source/候選hash、程式版本及差異hash、設定hash、模型/權重hash、前處理版本、環境、seed、操作者和開始/結束時間。含路徑的 provenance 指向任務內產物，不記原始病歷號/私有 lineage。

- `image_path` 基準為 clinical-image-lake repo 根目錄。
- prompt、mask、tool export 等 artifact 路徑基準為本 repo 根目錄。
- artifact 必須在批准的根目錄內，解析實體路徑後再次檢查；SHA256 是檔案 bytes 的 64 位小寫十六進位值。
- 同一批圖和 instance 的審核不覆寫，用不可變 `review_id` 和遞增 `revision`；以明確指定的 revision 發布，不從時間排序猜最後答案。
- 空 reviewer/時間代表未審核。模型 ID 或服務帳號不能代替專家身份。

## 1. 候選與資料角色

### `candidates.csv`（維持 v0.1，已實作）

精確欄位順序：

```text
schema_version,image_id,patient_key,image_path,source_id,content_sha256,width,height,blur_score,blur_is_usable,blur_qc_method
```

`schema_version=0.1`，主鍵 image_id。此既有 CLI 的 `blur_is_usable` 是 `True/False` 或空值，v0.2 讀取器必須明確解析，不能用 `bool('False')`。尺寸/hash/分數可能空白，需另經 integrity 檢查。資料按 image_id 排序，並未附 run_id；由 `run-metadata.yaml` 的相對路徑和候選 hash 對應 run。

### `integrity.csv` / `errors.csv`（v0.2）

Integrity 每個候選恰一列：`image_id,decode_status,actual_width,actual_height,actual_sha256,geometry_status,hash_status,path_status,error_code`。各 status 為 `ok/error/unknown`。Error 表可一圖多列：`error_id,stage,error_code,retryable,attempt,details,created_at`；details 不得含識別文字。

### `partitions.csv`（v0.2，患者層級）

無 image_id；欄位 `patient_key,role,partition_version,seed`。主鍵 `(partition_version,patient_key)`；role 為 `development/calibration/test`。抽樣另存 `sampling.csv`：`image_id,partition_version,sampling_kind,stratum,seed`；kind 為 `representative/enriched/smoke`。

## 2. 檢索與可見性

### `exemplars.csv`

`image_id,exemplar_set_id,label,lesion_review_id`。label 只能 yes/no，引用專家判讀；patient_key 由 candidates join 以排除同患者。主鍵 `(exemplar_set_id,image_id)`，只來自 development。

### `embedding_index.csv` / `retrieval_predictions.csv`

Embedding index：`image_id,row_index,encoder_id,checkpoint_sha256,preprocess_version,image_sha256,embedding_status`；embedding file/shape/dtype/hash 記 run metadata。embedding_status 為 `ok/error`，row_index 只對成功列分配。

Predictions：`image_id,encoder_id,exemplar_set_id,index_version,positive_score,negative_score,margin,neighbor_evidence_path,threshold_version,suggested_label,reason_code`。suggested_label 為 `yes/no/uncertain`。score 不存在必須 suggested_label=uncertain；無 threshold_version 只可排序，不自動建議 yes/no。

### `lesion_review.csv`

`image_id,review_id,revision,protocol_version,lesion_present,reviewer,reviewed_at,reason`。lesion_present 為 `yes/no/uncertain`。未審核不建立假 review。主鍵 review_id；重審保留舊列，新 row 由 review_events 指向前一版本。

舊 v0.1 把 prediction 與 review 混在 `retrieval_review.csv`，v0.2 拆開，避免 model suggested_label 被當作專家結果。

## 3. 品質

### `quality_metrics.csv`

`image_id,metrics_version,blur_score,blur_method,bright_fraction,dark_fraction,glare_fraction,valid_fov_fraction,roi_source,measurement_status`。fraction 为 [0,1]；method unknown 時不可比較不同 blur 值；roi_source 為 `full_fov/expert_box/model_proposal/unknown`，measurement_status 為 `ok/partial/error`。`partial` 時缺項保持空白。

### `quality_review.csv`

`image_id,review_id,revision,protocol_version,task_scope,blur,dirty,overexposed,underexposed,glare,poor_view,quality_status,reason_codes,reviewer,reviewed_at,reason`。

缺陷 severity 為 `0/1/2/unknown`，0=無、1=不影響任務、2=影響；quality_status 為 `usable/exclude/uncertain`。reason_codes 為 JSON array；可用碼見第 3 章。exclude 必有非空原因，關鍵 unknown 不得無理由放行。task_scope 例如 `lesion_segmentation`。

舊 v0.1 yes/no 缺陷欄位只能對應「存在與否」，不能自動推定 severity 1 或 2，需補審。

## 4. 提示、提案與定稿

### `prompts.jsonl`

每行一個物件：`schema_version,run_id,image_id,instance_id,prompt_id,revision,coordinate_space,width,height,box_xyxy,points_xy,point_labels,prompt_source,created_by,created_at`。

coordinate_space 固定 `original_image_pixels`；box 為 xyxy 半開框或 null，points 為 Nx2，point_labels 長度同 N（1=正點、0=負點）。至少框或點非空。prompt_source 為 `human/model`；模型生成提示要另記 model ID。instance_id 是此張圖的物件識別，不代表跨照片同一臨床病灶。

### `segmentation_proposals.csv`

`image_id,instance_id,proposal_id,prompt_id,proposal_origin,model_id,checkpoint_sha256,preprocess_version,proposal_mask_path,proposal_mask_sha256,model_score,status,error_code`。

proposal_origin 為 `model/manual`。model 起源必有完整模型與權重；manual 起源相關欄位空白，不用字串 manual 假造模型。status 為 `proposed/error`；error 列不必有 mask。model_score 只在有值時記錄，不能當 ground-truth 指標。

### `segmentation_review.csv`

`image_id,instance_id,review_id,revision,proposal_id,protocol_version,status,final_mask_path,final_mask_sha256,reviewer,reviewed_at,reason`。

status 為 `accepted/corrected/rejected`。accepted/corrected 必有專家身份、時間、合法 final mask 與 hash；rejected 不可有該 revision 的 final mask。accepted 可與 proposal 同像素但 final artifact 仍有固定版本。主鍵 review_id。

### `image_finalization.csv`

`image_id,finalization_id,revision,protocol_version,lesion_review_id,quality_review_id,expected_instance_count,approved_instance_ids,segmentation_review_ids,all_instances_reviewed,required_review_count,completed_review_ids,adjudication_status,finalizer,finalized_at`。

ID 清單是 JSON array；每個 approved instance 都須能找到對應 approved segmentation review。required_review_count 是**此圖**所需獨立專家人数，不是 CSV 列數；同人重審兩次只算一位；只有覆核範圍涵蓋此圖全部目標 instance 的專家才算完成，不能拿 A 審病灶一、B 審病灶二湊成全圖雙審。required=2 時至少兩位不同合格 reviewer，所有指定審核完成。adjudication_status 为 `not_required/pending/resolved`；pending 不放行。expected count 與 distinct approved count 一致，且所有可見目標已確認。

## 5. 標註工具與審核事件

`tool_mapping.csv`：`image_id,task_id,job_id,tool_image_name,image_sha256,width,height`。物件對照 `tool_object_mapping.csv` 加 `tool_object_id,instance_id,object_revision`。

`conversion_report.csv`：`image_id,instance_id,source_path,source_sha256,destination_path,destination_sha256,mapping_version,width,height,foreground_pixels,status,error_code`。status 為 `ok/error`；未轉換成功不可標 ok。

`review_events.csv`：`event_id,subject_type,subject_id,review_id,base_revision,new_revision,actor,actor_role,event_type,work_status,created_at,reason,related_review_ids`。subject_type 為 image/instance；subject_id 必須可解析回 image_id。work_status 为 `assigned/draft/submitted/pending_adjudication/finalized/superseded`；它不等於內容判斷 status。

review event 只追加。專家 A/B 各寫自己的 review；裁決引用雙方 ID；原 finalized 不因新提案被覆蓋。CSV 是第一版離線交換契約，線上多人協作需資料庫交易/樂觀鎖處理 base_revision，不允許多人直接編輯同一 CSV。

## 6. 去向及發布

`disposition.csv`：`image_id,revision,disposition,reason_codes,finalization_id`。disposition 為 `released/negative_retained/quality_excluded/out_of_scope/pending_review/processing_error`。每個凍結 snapshot 每張恰一列。released 指被此 release 納入，無 finalization 不可成立。

`train.csv/val.csv/test.csv`：`schema_version,run_id,release_id,image_id,patient_key,image_path,image_sha256,semantic_mask_path,semantic_mask_sha256,source_id,partition_version,split,finalization_id`。一張图一列，instance manifest 另保留；每個 release image_id 唯一。

`negative_retained.csv` 使用 image metadata 與 lesion/quality review IDs，不假造非空 lesion mask。所有发布來源 revision/hash 凍結，參考第 5 章與 release checklist。
