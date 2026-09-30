# CRC LST 侵入深度影像分類：文獻導向的實驗規格

本章把相關研究整理成 `clinical-colon-image-clean` 可以逐步執行、重現和交接的實驗規格。它是研究計畫與資料契約補充，不代表目前 repo 已經完成 T1b 分類模型，也不把文獻中的 accuracy 當成本專案結果。

## 1. 先固定問題定義

開始模型比較前，先在 `run-metadata.yaml` 或實驗紀錄中固定：

- endpoint：例如 `Tis/T1a vs T1b`；不可把「可否接受內視鏡治療」或「superficial vs advanced CRC」直接混成同一個標籤。
- 統計單位：同時指定 image-level、lesion-level 或 patient-level；同一病灶的連續影像不可被當成互相獨立的病例。
- split：至少以 patient-level 分開 development、calibration、test；若要做 lesion-level aggregation，還要確認同一 `lesion_group_id` 不跨 split。
- 影像輸入：記錄 WLI、NBI、IEE、染色、放大倍率、設備與影像品質；未知就保留 `unknown`，不能從檔名或資料夾名稱猜。

## 2. accuracy 不可直接橫向比較

表中的 accuracy 不能直接排名，因為研究的 endpoint、資料分布、陽性比例、取樣方式，以及 image-level／lesion-level 統計方式不同。Tokunaga 的 endpoint 是可否接受內視鏡治療，Luo 在不同納入條件下的 AUROC 也不同；Ito 主要是內部 cross-validation，Nakajima 的測試集沒有 T1a，Nemoto 則使用偏向高 specificity 的 threshold。

系統性回顧與 meta-analysis 納入 10 篇研究、13,918 張影像與 1,472 個病灶，並指出研究間異質性很高：[systematic review and meta-analysis (2023)](https://pubmed.ncbi.nlm.nih.gov/37430125/)。因此本 repo 的比較應固定 endpoint、固定 patient split、固定 aggregation，再一起報告 sensitivity at fixed specificity、specificity、AUROC、NPV、calibration、lesion-level accuracy 和 patient-level accuracy。

## 3. 五個優先影像處理方向

### 3.1 病灶 ROI／背景處理

同時建立三種輸入作為第一組 ablation：

1. full frame；
2. tight lesion crop；
3. lesion crop 加固定比例的周邊 context。

ROI 目標是減少正常黏膜、邊框、器械或設備介面造成的 shortcut，但不能裁得太緊而失去邊界與表面結構。裁切要記錄座標、來源和版本，且 train、calibration、test 使用同一套規則。

### 3.2 WLI 與 NBI／IEE 多模態配對

若同一病灶有時間、位置或 acquisition id 可對齊的 WLI 與 NBI／IEE，先比較 WLI-only、IEE/NBI-only 和 paired fusion。沒有真實 NBI／IEE 時，不要用色彩轉換或其他 augmentation 假造另一種 modality；那不是多模態驗證。

### 3.3 Class imbalance

T1b 或深部侵犯病例可能是少數類別，應比較 focal loss、class-weight 和 patient／lesion-level oversampling。所有重採樣與 augmentation 僅可出現在 training；同一 lesion 的原圖、增強圖或近重複 frame 不可分散到 test。

### 3.4 同一病灶多張影像的 lesion-level aggregation

不要把每張 frame 當成獨立樣本。對同一 `lesion_group_id` 比較 weighted mean、top-k pooling、majority vote 和 attention aggregation；保存每張 frame 的 score，最後再產生 lesion-level 及 patient-level 結果。若沒有可靠的 lesion grouping，先只宣稱 patient-level 評估，並把 grouping 缺口列為限制。

### 3.5 影像品質與外部設備差異控制

保留 blur、曝光、反光、遮蔽、有效視野、放大倍率、設備／型號、modality 和 acquisition group。外部驗證至少要規劃一個設備、時間或來源 cohort holdout；否則模型可能只記住某台設備的色彩、壓縮或邊框特徵。

## 4. 研究比較表

下表是實際影像處理／模型策略與本專案可借用方式。每個研究仍須回到原始 endpoint 和資料集定義閱讀，不能只複製 accuracy。

| 研究 | 實際影像處理／模型策略 | 可借用方式 |
|---|---|---|
| [Ito 2019](https://pubmed.ncbi.nlm.nih.gov/30130758/) | WLI 固定為 520×520；fine-tuning、oversampling、3-fold CV。 | 作為 baseline 與 class balance 參考；但只有 41 cases，沒有外部驗證。 |
| [Nakajima 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7508661/) | 以腫瘤為中心裁切以減少正常黏膜背景；rotation、saturation、resize、exposure augmentation；同一 lesion 只要一張影像超過 threshold 即判定。square crop 的明確例子另見 Minami 2022。 | ROI crop、亮度／飽和度增強、lesion-level aggregation。 |
| [Tokunaga 2021](https://pubmed.ncbi.nlm.nih.gov/32735946/) | 非放大 WLI；SSD＋MobileNet，同時做 lesion localization 與分類。 | 先定位再分類；但 endpoint 是可否接受內視鏡治療，不完全等同 Tis／T1a vs T1b。 |
| [Luo 2021](https://pubmed.ncbi.nlm.nih.gov/33852902/) | GoogLeNet 加 tumor-localization branch，讓分類受到病灶位置引導；並使用 augmentation。 | 最接近 attention／ROI 引導的做法；早期病灶測試 AUROC .970，但加入 advanced CRC 後降到 .729，代表資料定義非常重要。 |
| [Lu 2022](https://pubmed.ncbi.nlm.nih.gov/34919941/) | 將 WL 與 IEE 組成 image pairs，比較 WLI-only、IEE-only 與 pair fusion；另測試 35 段影片。 | 多模態融合值得優先驗證；應保留配對品質與影片層級的外部驗證。 |
| [Nemoto 2023](https://www.giejournal.org/article/S0016-5107%2823%2900089-5/fulltext) | ResNet-50、ImageNet pretraining、focal loss、oversampling、augmentation；另用典型 T1b 影像做第二階段 fine-tuning。 | 對 T1b 少數類別與 threshold tuning 有參考價值；結果偏向高 specificity，sensitivity 只有 59.8%。 |
| [Lui 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6447402/) | WLI＋NBI，使用預訓練 ResNet；NBI 表現明顯優於 WLI。 | 若有 NBI／IEE，可做 paired 或 modality-specific model；但 endpoint 是可否完整內視鏡治療，不是完全相同的 T1b 分類。 |
| [Minami 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9656054/) | 使用 WLI、NBI、染色影像；明確裁切腫瘤與周邊區域，避免背景 shortcut。 | ROI＋context 很值得測試；但 specificity 偏低，不能只追求 sensitivity。 |
| [Yao 2023](https://pubmed.ncbi.nlm.nih.gov/36478234/) | WLI＋IEE＋臨床資料的 multimodal CCIC；image 與 video 都驗證。 | 若有合法且不洩漏 label 的年齡、部位、大小、Paris type、NICE／JNET 等 metadata，可做第二階段融合。 |

## 5. 對目前 repo 的實驗優先順序

1. 先固定 patient-level split；若有可靠 lesion grouping，再加上 lesion-level split 檢查，避免同一患者或同一 lesion 的連續影像分散到 train/test。
2. 在目前 WLI/full-frame baseline 外，增加 full frame、tight lesion crop、lesion crop＋周邊 context 三種輸入。
3. 使用 moderate rotation、resize/pad、brightness/exposure/saturation augmentation；不要先做過度 CLAHE、銳化或 super-resolution，因為可能製造不存在的血管與邊界。
4. 加入 focal loss 或 patient/lesion-level oversampling，但只在 training 使用；不得把同一 lesion 的增強圖放到 test。
5. 對同一 lesion 的多張圖做 weighted mean、top-k pooling 或 attention aggregation，而不是把每張 frame 當成獨立樣本。
6. 加入 tumor localization／attention branch，與同一 split 的 ROI baseline 比較。
7. 若有 WLI 與 NBI/IEE，做 paired fusion；若沒有，就不要用影像增強假造 NBI。
8. 以 sensitivity at fixed specificity、AUROC、NPV、lesion-level accuracy 和 patient-level accuracy 一起報告，不要只看 overall accuracy。

最可能帶來實際改善的組合是：**ROI＋context crop → focal loss／平衡取樣 → lesion-level aggregation → WLI／IEE fusion**。這只是實驗優先順序；必須在固定 endpoint、patient-level split 與獨立 holdout 下驗證，才能判定是真正的 generalization gain，而不是資料洩漏或背景 shortcut。

## 6. 資料契約補充：不要破壞現有 v0.1 exporter

目前 `scripts/export_lake_manifest.py` 產出的 `candidates.csv` 是 v0.1，欄位沒有 WLI/NBI、magnification、device、lesion ROI 或跨 frame 的 lesion grouping。為保持既有匯出相容性，不要直接改變 v0.1 欄位順序；模型實驗應先建立以 `image_id` join 的 v0.2 sidecar 或擴充 manifest。

建議的 classification metadata 欄位：

| 欄位 | 規則 |
|---|---|
| `patient_key` | 由既有 candidates join；只作患者分區，不在 repo 寫入姓名或病歷號。 |
| `lesion_group_id` | 由人工或可追溯的 protocol 建立，代表跨多張影像的同一臨床病灶；不可由資料夾名稱或連續檔名猜。 |
| `image_id` / `frame_group_id` | `image_id` 是影像主鍵；`frame_group_id` 用於同次 acquisition 或影片群組，未知保留空值。 |
| `modality` | `WLI/NBI/IEE/chromo/unknown`；未確認不推定。 |
| `magnification` | `non_magnified/magnified/unknown`。 |
| `device_id` | 經去識別化且穩定的設備代碼，不放 serial number 或私有 lineage。 |
| `roi_source` / `roi_box_xyxy` | `full_fov/expert_box/model_proposal/unknown`；座標以原圖像素、xyxy 半開區間記錄。 |
| `quality_status` / `quality_reason_codes` | 優先 join 既有 `quality_review.csv` 與 `quality_metrics.csv`，不重複創造互相矛盾的 blur 欄位。 |
| `depth_label` / `label_source` / `label_revision` | pathology 或專家標籤需帶來源與版本；`unknown/pending` 不得自動變成 negative。 |

詳細欄位契約見 [`schemas/records.md`](../schemas/records.md) 的「影像分類實驗延伸」；目前這些是 planned contract，尚未代表 exporter 已經能產生所有欄位。

## 7. 每次實驗的最低記錄

每一個 baseline 或 ablation 至少保存：source/cohort、endpoint、patient/lesion split version、sample counts、class balance、ROI/preprocess version、augmentation、loss、sampler、model/checkpoint、random seed、device holdout、metrics、confidence intervals、calibration、git commit 和資料 hash。任何影像、mask、模型權重、臨床資料與 generated manifest 都留在受控 runtime，不提交到這個公開 repo。

## 8. 驗收門檻

- train、calibration、test 沒有 patient intersection；有 `lesion_group_id` 時也沒有 lesion intersection。
- 同一 lesion 的原圖、連續 frame 和 augmentation 不跨 split。
- 每個比較都使用同一 endpoint、同一 split、同一 aggregation 規則。
- 結果同時有 frame-level、lesion-level 或 patient-level 的明確分母；若某層級無法計算，明確標記 unavailable。
- 至少一個外部設備、時間或來源 cohort holdout，或在報告中明確揭露尚未具備外部驗證。
- 研究結論只說「在本次設定下的差異」，不把內部 validation accuracy 寫成臨床 generalization。
