# 3. 訓練影像品質篩選

## 3.1 品質是對任務的可用性判讀

輸入：已判病灶 yes 的影像；若也要建立分類/偵測陰性集，對 no 圖另外評同一品質流程，保留 `task_scope`。操作者：工程師產生指標，專家決定是否足以標邊界。

圖有局部反光不一定不能用；全圖很清楚也可能病灶邊界被器械挡住。全圖指標作篩選提示，專家需看病灶區域。`lesion_present=yes, quality_status=exclude` 是合法組合；不要為了排除品質差就把病灶改成 no。

## 3.2 建立共同判讀標準

先取 100–200 張 development 樣本，覆蓋指標高、中、低值與不同成像模式。專家判每種缺陷的 `severity=0,1,2,unknown`：0=無、1=有但不妨礙任務、2=妨礙可判讀/邊界定義。保存一組可教學的假名化例圖於 ignored outputs，完成 [校準表](../templates/annotation-protocol.md)。以下只是專家會議的起始規則。

| 原因碼 | 工程師可量測/提示 | 專家看什麼 | 處理 |
|---|---|---|---|
| `blur` | 現有 Walsh–Hadamard KS；必要時局部清晰度 | 病灶邊界/紋理是否可辨 | 邊界難辨為 exclude 或 uncertain |
| `dirty` | 污物/泡沫/黏液區域提案，初期人工 | 遮蔽是否落在病灶或邊界 | 不以「褐色面積」直接判污物 |
| `overexposed` | 臨床視野內接近飽和像素比例 | 是否丟失病灶組織資訊 | 小亮點和大片資訊損失分開 |
| `underexposed` | 過暗像素比例及局部細節 | 病灶區是否看得清楚 | 黑色外框先排除再算分數 |
| `glare` | 高亮低飽和候選連通區 | 反光是否覆蓋邊界 | 不自動 inpaint 再當原圖訓練 |
| `poor_view` | 病灶碰邊、器械/水流遮擋等提示 | 是否完整看見所有目標邊界 | 對完整病灶分割，截斷者排除或待裁決 |
| `out_of_scope` | 器械/標本/術後畫面等標籤 | 是否屬本次目標範圍 | 保留原因，不用 retrieval 猜測代替 |
| `privacy_suspect` | 燒錄文字或識別面板殘留 | 是否須交回去識別化流程 | 暫停此圖，回報 lake 管理者 |
| `corrupt` | 解碼、尺寸、雜湊檢查失敗 | 無法正常開啟 | 進錯誤佇列，不送模型 |

## 3.3 復用既有 blur 分數

`candidates.csv` 已帶 `blur_score/blur_is_usable/blur_qc_method`。本 repo 的 `blur_score` 是 KS statistic，**數字越小通常越模糊**；使用前先核對 method，其他算法方向可能相反。既有 0.089 是歷史目視校準值，不是所有 cohort 的合格線。未知 QC 保留未知，不能當通過。

只有分數缺失或前處理/方法版本不同時才重算。現有脚本是 directory 介面，不接受候選 manifest；以下可執行命令只做整個去識別化影像池中排序前 20 張的試算，**不是指定 cohort 校準抽樣**：

```bash
CLEAN_RUN=outputs/blur-smoke-001
mkdir -p "$CLEAN_RUN"
test ! -e "$CLEAN_RUN/blur.csv" && \
.venv/bin/python ../clinical-image-lake/scripts/blur_detection/detect_blur.py \
  --input-dir shared_image_lake/images --limit 20 --workers 2 \
  --output-csv "$CLEAN_RUN/blur.csv"
```

CSV 的 `relative_path` 要加上 `shared_image_lake/images/` 才能對回候選 `image_path`；join 後核對 matched/unmatched 數量，不能按行順序接。空值、NaN、Infinity、錯誤字串均是 `unknown`。對選定候選重算的 manifest adapter 列於 WP04，尚未實作。此子任務只保留自己的 QC 結果，不執行會改 lake DB 的 `apply_blur_qc.py`。

## 3.4 曝光、污物與視野指標設計（待開發）

1. 建立有效臨床視野 mask；必要時去除已確定的黑框，保留規則與範例。**不要把暗黏膜誤當黑框**；無法可靠估計視野時標 unknown。
2. 以有效視野像素為分母，計算 `bright_fraction`、`dark_fraction`、高亮連通區面积；強度界限如 8-bit 250/10 只能當待比較的起始參數。
3. 污物/泡沫不宜只依色彩硬規則；先收人工標籤再比較小型分類器/分割器。未開發前由人工完成 `dirty` 判讀。
4. 有病灶提示後再算病灶附近指標，記 `roi_source=expert_box` 或 `model_proposal`。沒有 ROI 時只報全圖值，不假裝已量到病灶品質。
5. 在 development 開發特徵/模型，在 calibration 選閾值；白光/NBI 分層查誤排比例，資料不足時保留人工判讀。
6. 同時報告「專家認為可用卻被排除」與「不可用卻通過」；只提高排除率不代表品質模型更好。

## 3.5 品質決策與記錄

人工覆核後，`quality_status` 為 `usable/exclude/uncertain`。`exclude` 必有原因，允許多重缺陷；`usable` 可以有 severity 1，需確定不影響本任務。severity 2 原則上不放行，專家例外需簽署且保存理由。關鍵項目 unknown 時保持 uncertain。

手冊預設完整邊界的 lesion segmentation；部分病灶、重度遮蔽、邊界无法裁決的圖保留在候選和研究統計中，但不進第一版定稿集。日後若改成可见区/遮蔽訓練，必須另定 ignore mask 與 loss 規範，不能默默把未知像素標背景。

驗收：所有進分割的圖均 `lesion_present=yes`、`quality_status=usable`，兩者有專家簽署；所有排除與 unknown 可追溯，原影像數量不因篩選而減少。
