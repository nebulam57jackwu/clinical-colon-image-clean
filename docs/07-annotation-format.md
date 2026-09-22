# 7. 標註操作、格式轉換與多人覆核細則

本章供工程師製作標註匯入匯出 adapter，並供初審/覆核者依同一規則操作。**目前尚無自動轉換或覆核 CLI**；以下規格與合成例子必須先做往返驗證，才可用於正式批次。

## 7.1 一次標註工作如何開始與結束

| 步驟 | 操作者 | 具體操作與完成依據 |
|---|---|---|
| 1. 派工 | 工程師 | 固定 run/protocol，從核准清單選 50–100 張；建立 task/job → image_id 對照，不以排序當 ID |
| 2. 初審 | 初審者 | 先看原圖，再判 yes/no/uncertain 和品質；缺資訊保留 unknown，不為完成率而猜測 |
| 3. 提示/草稿 | 初審者 | 每個目標病灶建立 instance ID，畫框/點或人工 mask；記提案来源與提示版本 |
| 4. 第一位專家 | 專家 A | 核對目標及所有邊界；accepted/corrected/rejected；填 reviewer、時間、理由與 mask hash |
| 5. 第二位專家 | 專家 B | 對預先抽中的圖及所有疑難例獨立覆核；與 A 不同帳號，暫不展示 A 的判斷與模型分數 |
| 6. 分歧裁決 | 裁決專家 | 看雙方結果，選定/修訂 final；保存裁決原因和來源 review IDs，不刪其中一方 |
| 7. 圖層定稿 | 專家+工程師 | 確認所有病灶完成、圖層品質與可見性一致，凍結 finalization revision |
| 8. 交回 | 工程師 | 匯出原始工具檔、轉換 mask、review metadata，做 hash/幾何/數量核對後進 G5 |

工具的 job completed 僅是工作進度，專家定稿需有本資料契約中的簽署。第一版所有 mask 至少一位合格專家定稿；第二覆核比例的起始設定為 20%，再加全部疑難列，由負責人在批次開始前簽署。

## 7.2 先建 ID 對照，再匯入檔案

`tool_mapping.csv` 每列含 run_id、task_id、job_id、tool_image_name、image_id、image_sha256、width、height。instance 對照另含 tool_object_id、instance_id、object_revision。工具新增加的第二個病灶也必須分配新 instance ID，不能覆用原 ID。

推薦工具檔名為 `<image_id>.<原副檔名>`；同 stem 不得有兩張不同圖，不能把 `IMG_1.jpg` 和 `IMG_1.png` 只靠 stem 當同一筆。以對照表精確 join，拒絕重複、多對一及不存在的 ID。zip 裡的排序與原始 candidate 的排序沒有關係。

任何影像內容、尺寸或方向變動都需要新的 transformation 紀錄與重驗；mask 不可在匯出時被默默旋轉來「看起來差不多」。工具端避免有損匯出，至少確認解码尺寸/方向與來源一致。

## 7.3 Canonical mask 與工具格式

本子專案 canonical instance mask：原圖 W×H、單通道 uint8 PNG、數值只有 0/1、每檔一個病灶。semantic mask 是已定稿 instance 的逐像素 OR；instance ID 只在對照表，不把任意的 17、42 直接當訓練類別值。

CVAT Segmentation Mask ZIP 使用 `SegmentationClass/` 及 `SegmentationObject/`，可含 palette/RGB，且 attributes 不隨此格式保存。因此工具 ZIP 和本子專案 review metadata 必須成對保存。[官方格式說明](https://docs.cvat.ai/docs/manual/advanced/formats/format-smask/)

| 輸入格式 | 轉換方式 | 阻擋條件 |
|---|---|---|
| L-mode 0/1 PNG | 明確宣告 0=背景、1=lesion 後逐像素檢查 | 出現其他值、尺寸錯誤 |
| L-mode 0/255 PNG | 只有 labelmap 確認 255=lesion 才做 255→1 | 255 若是 ignore/void，不能當 lesion |
| P-mode palette PNG | 先讀 index 与 palette，依 labelmap 的 class index 映射 | 不可 `convert('L')` 後把亮度當類別 |
| RGB 類別 PNG | 以 labelmap 的精確 RGB 三元組轉 class；背景和 lesion 分開 | 不明色、抗鋸齒混色；不採最近顏色猜測 |
| 工具 instance mask | 讀 object-ID mapping，依每個目標 instance 拆 binary | 缺 object 對照；不能把連通區數當病灶數 |
| Polygon | 固定座標系與 rasterization 版本，holes/多區域明確記錄 | 自交、邊界不明、holes 遺失；不得無記錄地修補 |
| Probability/logit map | 記 sigmoid/softmax 與閾值，在正確座標還原後二值化 | 將 0–1 浮點直接轉 uint8 造成全部歸零 |

遇到 ignore/void 第一版就阻擋該張，交專家處理。日後要接受必須新增 ignore mask 與訓練 loss 契約，不能把 void 當背景。

## 7.4 轉換順序與小例子

1. 先檢查 ZIP 成員路徑；拒絕絕對路徑、`..`、symlink 及不合理解壓大小，解到全新的批次暫存目錄。
2. 讀 mapping/labelmap；鎖定 image_id、object ID、W/H 和來源 hash。
3. 判斷圖檔模式與 dtype，保留原始數值，不先做一般照片灰階轉換。
4. 按明確映射產生每個 instance 的 0/1 mask。未知色/類別記錯誤；不以 `mask > 0` 一網打盡。
5. 檢查形狀、值域、非空、方向與 image overlay。lossless PNG 寫出後重新讀取，應像素完全一致。
6. 產出 `conversion_report.csv`：每檔 source hash、destination hash、mapping version、尺寸、前景面積、狀態與錯誤碼。
7. 只在專家定稿後，對所有已確認 instance 做聯集產生 semantic mask；聯集不能用來復原原本 instance ID。

以下為**純示範**：已知來源單通道 mask，映射中 255 確認代表病灶。實際 adapter 還要處理路徑、ID 與版本。

```python
import numpy as np

source = np.array([[0, 0, 255], [0, 255, 255]], dtype=np.uint8)
assert set(np.unique(source)).issubset({0, 255})
canonical = np.where(source == 255, 1, 0).astype(np.uint8)
assert canonical.shape == (2, 3)
assert int(canonical.sum()) == 3
```

不要把此範例套在任意 255 圖；醫療/其他資料集中 255 也常被定為未知類別。實際意義由本批次 labelmap 決定。

## 7.5 兩張合成圖的往返驗收

建立 640×480 的非方形彩色背景圖：第一張有兩個分離、不同 instance 的矩形目標；第二張有環形目標（含洞）與靠近右下角的目標。保存已知 0/1 mask、instance ID 和 W/H。

1. 匯入工具，**不修改**即匯出。轉回 canonical 後，各 instance XOR 不同像素數應為 0，ID 一一對應、holes 不消失；semantic union 也一致。
2. 在副本人工加一塊明確區域再匯出；差異只能發生在修改區域，另一個 instance 不受影響。
3. 測試 palette/RGB/0–255 各一種工具支持的往返。若工具強制 polygon 導致 rasterization 不完全一致，記錄差異與規格，優先改用 lossless mask 路徑；不能直接放寬為「肉眼看起來對」。
4. 故意加入未知色、尺寸對調、重複 basename、缺 mask、錯 image ID，必須報錯。未匯出的物件不當空背景。
5. 往返通過後才用 20 張真實已審核影像做 overlay 人工驗收，含多病灶、邊緣及反光難例。

## 7.6 多人覆核狀態與並行衝突

review event 的工作狀態為 `assigned/draft/submitted/pending_adjudication/finalized/superseded`；它與模型的 `proposed`、內容判斷的 `accepted/corrected/rejected` 是不同欄位。

- A、B 各自建立不可變的 `review_id`，都指向同一 input revision。不得一起寫同一張 final PNG。
- 第二覆核清單在開始前按患者/難度抽样固定；若後來發現疑難，可增加項目並保留理由。已被指派第二覆核的圖，B 未完成不得发布。
- 即使兩人 mask 高度重疊，仍需核對病灶數、可見性、品質與語義範圍；Dice 不直接自動解決分歧。
- 專家裁決建立新 review，引用 A/B；選擇 A/B 或重畫均記理由、reviewer 和時間。單人團隊無法做獨立雙審時記實際限制，不用同一帳號模擬第二人。
- 每次更新使用 `base_revision`。若伺服器已有較新 revision，拒絕舊版覆蓋並要求合併/裁決。
- 若更改了 mask 或標註規範，原 finalized 版本仍保留；新版本需重新取得受影響的簽署。release 固定舊版直到新 release 明確發布。

## 7.7 每张圖的定稿檢查

全圖看一次、逐病灶邊界放大一次、關閉 overlay 再看一次。檢查：目標數量相符；沒有將腸腔、器械或皺褶算入；不明處沒有猜填；多個 instance 不誤合併；mask 与图對齊；品質足以支援本任務。

填 `expected_instance_count`、`approved_instance_ids`、`all_instances_reviewed`、`required_review_count`、`completed_review_ids`、`adjudication_status`、`protocol_version` 與 finalization 時間。確認通過後才交 [訓練集驗收表](../templates/release-checklist.md)。
