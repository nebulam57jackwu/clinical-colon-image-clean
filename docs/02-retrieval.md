# 2. Image retrieval 病灶初篩與校準

## 2.1 先定義標籤，再建立範例庫

操作者：工程師建工具，專家定標籤。輸入：G0 候選與 development 患者。輸出：`exemplars.csv`、逐圖審核與判讀規範版本。

| `lesion_present` | 判讀定義 | 常見例子 |
|---|---|---|
| `yes` | 此張圖可見規範內的目標病灶；病灶邊界是否完整另由品質階段判定 | 可見息肉或目標腫瘤；即使只見部分仍可能 yes |
| `no` | 專家在可判讀視野內未見目標病灶 | 正常黏膜、皺褶；傷口是否為 no 依目標範圍規範 |
| `uncertain` | 可見性不足或專家無法確定 | 重度遮蔽、全圖失焦、病灶/皺褶難分、目標類型未定 |

先由專家一起看 30–50 張建立共識，再將起始標註池分開判讀。起始規劃：至少 20% 雙人獨立判讀，加上所有不確定/分歧列交專家裁決；比例可調整但須記錄。第一輪盡量不顯示模型建議，以降低跟著模型判讀的偏差。

從 development 挑選數十至數百張陽性和陰性 exemplar，優先覆蓋患者與外觀多樣性；同一患者連續十張幾乎一樣的圖不要佔滿近鄰。保存人工標籤、審核者、來源 `image_id`、`exemplar_set_id`、排除/加入理由。陰性範例要含皺褶、反光、器械和傷口等難例，但前提是專家能確定它們為 no。

## 2.2 Encoder 選型（待開發）

先做一個固定 encoder 的 baseline，再比較另一個候選；不先 fine-tune。建議比較 DINOv3 ViT-B 與 DINOv2 或已取得授權的內視鏡 encoder。DINOv3 官方提供全圖與密集視覺特徵及多種尺寸模型，因此是本專案的候選；本地病灶辨識效能仍須實測。[DINOv3 官方實作](https://github.com/facebookresearch/dinov3)

每次運行固定 `encoder_id`、來源 commit、checkpoint SHA256、input size、resize/pad/normalize 規則、global token 或 pooling 方法、數值精度。不能只寫 `DINO`。使用官方前處理做 baseline，另測保留完整視野的 resize/pad；若中心裁切會丟掉邊缘病灶，記錄並評估，不直接套通用分類預設。

實作步驟：

1. 用 development 的 20 張確認影像正常、embedding 维度固定、無 NaN/Inf/零向量。
2. `eval()` 和推論模式分批抽特徵，batch size 從 1 增加；相同前處理保證 exemplar 與 query 一致。
3. L2 normalize：`z = feature / ||feature||`；零向量記錯誤，不能加一個常數後當正常樣本。
4. 存 `embeddings.npy` 和相同行序的 `embedding_index.csv`。cache key 包含 `image_id + content_sha256 + encoder + preprocessing`；任一改變就失效。
5. 先用精確 cosine 檢索，規模增大後再測近似索引的召回損失。44k × 768 × float32 約 135 MB，只是向量本體估算，不含索引、模型與影像。

## 2.3 一個可重現的檢索 baseline

以下是演算法規格，尚未提供 CLI：

```text
對每個 query：
  排除同 image_id、同 content hash，以及同 patient_key 的 exemplar
  陽性 exemplar 的 cosine similarity 由高到低排序
  陰性 exemplar 的 cosine similarity 由高到低排序
  每類取最多 k=5 個不同患者的最近範例
  s_pos = 陽性 top-k 的平均相似度
  s_neg = 陰性 top-k 的平均相似度
  margin = s_pos - s_neg
```

`k=5` 是 baseline 設計值，存進設定；某類找不到足夠不同患者（初始要求 5）就標 `insufficient_reference` → `uncertain`。每張記錄近鄰 ID、類別、相似度、患者排除規則與索引版本。cosine 和 margin 不是機率。

兩個閾值 `t_low < t_high`：`margin >= t_high` 建議 yes，`margin <= t_low` 建議 no，中間 uncertain。即使 margin 很高，若正負範例絕對相似度都很低、影像解碼失敗、嚴重品質問題或近鄰分歧，仍改送 uncertain。絕對相似度最低值也須校準；沒校準時這個模型只能排序，不能自動放行。

小病灶可能在全圖 embedding 被背景淹沒。若錯誤分析顯示這是主要漏判，增加重疊多尺度區塊檢索，保留每塊的原圖座標，評估是否真的改善召回。區塊最高分不能直接當病灶定位框，更不能當真實 mask。

## 2.4 閾值怎麼選

1. 在 development 選好 encoder、k 和前處理後凍結模型。
2. 在 calibration 按患者獨立取得專家標籤，掃描 `t_low/t_high`；選到負向桶漏掉的陽性最少、人工審核量仍可負擔的組合。
3. 同時報告 `yes/no/uncertain` 的數量、混淆矩陣、各亞組及患者層級結果。不要把 uncertain 當 no 計算一般二元 accuracy。
4. **分流保留召回率** = 真實陽性中被送到 yes 或 uncertain 的比例；**直接陽性召回率** = 真實陽性中建議 yes 的比例，兩者都報。
5. **負向桶漏病灶比例** = 專家判 yes 且被建議 no 的張數 / 全部建議 no 張數；它與 `1 − recall` 分母不同，不能混用。
6. 在代表性抽樣報審核分鐘數/百張與每個患者權重，使用患者 bootstrap 的 95% 區間。難例富集資料另列。
7. 目標由負責人在看 test 前簽署，例如要求「分流保留召回率至少 98%」只能寫成**待核准設計目標**；小樣本即使觀察零漏判也不能證明達標。
8. 閾值與設定凍結後評 test；若不達標，回 development 開新版本，維持人工審核。

## 2.5 審核畫面與正式批次

畫面一次顯示原圖、放大、前幾個正/負近鄰、三態按鈕和理由欄。近鄰屬參考證據，不把病理診斷或相似度當病灶存在真值。第一版將所有供訓練的影像由人確認；模型只是排序，優先處理 uncertain、近閾值及相似度離群者。

每批另外抽查建議 no 的隨機樣本和高風險亞組，避免只看 yes。發現漏病灶，標明來自哪個來源/設備/模式，擴大該亞組人工檢查並重新校準。更改 exemplar 後要建立新 `exemplar_set_id` 和重新驗證，不能偷偷把 test 錯例加入範例庫後重報 test 成績。

驗收：每張 query 都有結果或錯誤；每個建議可重建近鄰；所有專家結果有 reviewer/時間；未判定仍是空白或 uncertain，不能被 CSV 空值填補成 no。
