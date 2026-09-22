# 4. 病灶分割提案、專家修正與定稿

## 4.1 先選定「要標什麼」

操作者：專家定義範圍，工程師完成 adapter 與工具。輸入：經專家判 yes 且 quality usable 的影像。輸出：逐病灶 prompt、proposal mask、review event、final mask。

首次專家會議簽署：目標包含哪些病灶；有蒂病灶是否包含蒂；染色/燒灼/術後傷口是否屬目標；邊界模糊、碰到圖緣、反光遮蔽如何處理。工程師不以影像分割模型猜病理侵襲範圍。第一版只收能明確畫出目標可見邊界的影像，不能確定者回 uncertain。

同一張有兩個目標病灶，就記兩個 `instance_id`。每個病灶各一份 binary mask；訓練 semantic mask 是所有已確認目標病灶的聯集。漏標第二個病灶會讓它被當背景，必須在 image-level finalization 再查一次。

## 4.2 模型比較與環境

查核日期 2026-09-17。下表是候選和實驗設計，沒有任何一個已在本院資料證明是 SOTA。

| 候選 | 這裡怎麼試 | 選用限制 |
|---|---|---|
| SAM 2.1 | 靜態圖用點/框互動分割，先建立能運行的 baseline | 必須提供/產生病灶提示；自動分割所有物件不等於識別病灶 |
| SAM 3 image | 同一批圖、同一套點/框提示評估；文字提示可另做探索組 | image API 和 checkpoint 要配對，不混用其他模型权重 |
| MedSAM / MedSAM2 | 檢查目標 checkpoint 的訓練域與 2D RGB 輸入支援後再試 | 「醫療」名稱不證明適用大腸鏡；MedSAM2 主打 3D/影片 |
| 任務專用分割模型 | 有足夠專家 mask 後，另建监督式 baseline | 病人分區、外部訓練資料和授權需可追溯 |

SAM 2.1 的官方 image predictor 接受提示；SAM 3 支援 image segmentation。SAM 3.1 的 Object Multiplex 主要改進多物件**影片追蹤**；本專案暫以靜態图为主，因此不把 `sam3.1` 固定為預設 image checkpoint。[SAM 2 官方實作](https://github.com/facebookresearch/sam2)、[SAM 3 官方實作](https://github.com/facebookresearch/sam3)、[SAM 3.1 release notes](https://github.com/facebookresearch/sam3/blob/main/RELEASE_SAM3p1.md)、[MedSAM2](https://github.com/bowang-lab/MedSAM2)

環境按選定官方 commit 安裝，保存 lock/pip freeze、checkpoint SHA256、GPU 峰值記憶體和每圖耗時。SAM 3 官方 README 當前列 Python 3.12+、PyTorch 2.7+、CUDA 12.6+；實際以鎖定版本的需求為準。權重下載可能須取得存取權，未取得就用可合法取得的 baseline，不把尚未下載寫成可運行。

公平比較先在 development 的人工 mask 比較模型；相同圖、相同提示預算、相同評估方式。專家框是人力輸入，報告總工時時要計入，不可稱全自動。若用 ground-truth mask 算出理想框，那是 oracle 實驗，另列，不能與實際人工框混報。

## 4.3 從畫框到原圖 mask 的具體步驟（adapter 待開發）

1. 打開候選原圖，工程師核對 `image_id`、尺寸、SHA256。標註畫面不再壓縮/調色後覆寫圖。
2. 初審者對每個可見病灶畫緊貼但涵蓋完整目標的框，或一個確定在病灶內的正點；框不足以區分時加負點排除鄰近皺褶。每次提示保留 revision。
3. 統一保存原圖像素座標：左上原點，x 向右、y 向下，點 `(x,y)`，框 `[x_min,y_min,x_max,y_max)` 半開区间。框限 `0 <= x_min < x_max <= W`；點限 `0 <= x < W`。adapter 負責轉成各模型需要的 normalized/xywh/xyxy 格式。
4. 記錄 image-to-model resize/padding/crop 轉換；模型輸出還原到原始 W×H。硬標籤 resize 只能 nearest-neighbor；若先 resize logits，再 threshold，需記錄方法與閾值。
5. 先跑 20 張（含非方形圖、邊緣病灶、多病灶），檢查提示與 mask overlay，確認 x/y 沒對調、H/W 沒對調、沒有重複套用座標縮放。
6. 模型若產生多個候選 mask，保留各自分數和選擇原因。模型自評 IoU 不是真實 Dice，也不能取代專家審核。
7. 產出 `proposal_masks/<image_id>/<instance_id>/<proposal_id>.png`，記 `status=proposed`。提案和模型分數不得直接填入 final 欄位。
8. 工程檢查空遮罩、全圖遮罩、邊界相交、异常面積、mask 含 NaN/非法像素、多碎片與重疊。這些是警示，不直接自動填洞或刪除小病灶；修改也要另存版本。

所有 mask 是單通道 uint8 PNG，0 背景、1 目標病灶。人眼看幾乎全黑是正常的：檢查用 overlay 或顯示乘 255，儲存值仍是 0/1。檢視用彩色 overlay 不能當訓練 mask。

## 4.4 標註工具操作 SOP

轉換映射、合成圖往返及並行覆核細節另見 [第 7 章](07-annotation-format.md)。

建議在伺服器部署院內/受控的 CVAT；不依賴外部公開標註服務。部署由工程師按 [CVAT 官方安裝文件](https://docs.cvat.ai/docs/administration/community/basics/installation/) 建置並記版本。本 repo 尚未部署 CVAT 或自動匯入匯出介面。

1. 建立專案 `clinical-colon-image-clean`，以 `run_id` 建 task，每個 job 建議 50–100 張以便追蹤；這是操作起始大小。
2. 輸入圖只用假名檔名；優先以唯讀共享路徑存取。若工具需產生工作副本，記載來源/hash、用途與回收時間，不將它註冊為新的主影像。
3. label 定 `lesion`，metadata 保存 image_id/instance_id 對照表。先用 2 張**合成圖**完成 mask 匯入→修改→匯出的往返測試，再用 20 張已審核樣本確認幾何。
4. 接入 adapter 後匯入模型 proposal；未接好前可直接人工畫 mask，這時 `proposal_origin=manual`，不要假造模型名稱。
5. 專家用 30–50% 透明 overlay 看全圖，再放大邊界。逐一看是否少一個病灶、誤包含皺褶/器械、反光處邊界是否可判讀、像素是否對齊。
6. 不需修正：`accepted`；有修正且完成：`corrected`；錯圖/不可判讀/需重新提示：`rejected`，記理由並返回適當隊列。專家資格與 reviewer ID 保存在院內對照表。
7. final mask 另存新路徑，accepted 也要固定 final artifact 的 hash。不得覆寫 proposal，以便量測修正幅度和追溯。
8. 匯出工具原始格式與轉換後 0/1 PNG；按 image_id/instance_id join，核對是否遺失空 mask、漏圖或改檔名。

CVAT Segmentation Mask 格式可能是單通道或彩色 label mask，且**不保存 attributes**。轉換時讀 `labelmap.txt`，用明確的 lesion 類別映射成 0/1；reviewer、時間、狀態另存本子專案 review CSV，不能期待 PNG/工具 ZIP 自帶完整覆核資訊。[CVAT Segmentation Mask 格式](https://docs.cvat.ai/docs/manual/advanced/formats/format-smask/)

## 4.5 專家覆核與分歧處理

每張訓練 mask 都需要明確專家定稿。起始規劃再對 10–20% 隨機定稿與全部疑難例雙人覆核，獨立看圖後再討論；影像難度不同應分層抽樣。兩人不同意時留 `pending_adjudication`，由資深專家裁決，保留兩份初始結果。不能用平均兩個 mask 代替裁決。

獨立模型測試集的參考 mask 應先由看不到模型提案的專家完成，避免參考答案受模型影響。以另一份操作樣本量測使用模型提案後的修正時間，與人工從零標註相比；安排相同難度/分層與交叉順序，報告提示時間、修正時間及總時間。

## 4.6 指標與放行

`Dice = 2|P∩G|/(|P|+|G|)`、`IoU = |P∩G|/|P∪G|`。本任務只評已確認陽性，空預測對非空真值記 0；不得用「雙空=1」灌高成績。報逐圖/逐患者分布、最差案例、分層結果、完全漏掉病灶比例及專家修正時間。

分開報 **分割階段条件效能**（已正確篩進來的陽性）與 **全流程漏失**（檢索漏掉、品質誤排及分割漏掉）。前者很高不能掩蓋上游丟圖。除 Dice/IoU 外，本專案選型重視減少專家總時間並維持邊界可靠性。

放行：每個已知目標 instance 都有 final、專家狀態和 hash；尺寸等於原圖、像素集合為 {0,1}、非空；圖層整體確認 `all_instances_reviewed=true`。任何 uncertain 或 pending_adjudication 均不進第一版 release。
