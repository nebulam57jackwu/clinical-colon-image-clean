# 訓練集發布驗收表

Release ID：

Run IDs / protocol / partition / finalization snapshot：

驗收工程師 / 專家 / 任務負責人 / 日期：

| 必驗項目 | 結果 PASS/FAIL/不適用 | 證據路徑、計數或 hash |
|---|---|---|
| 候選與六類去向數量守恆 | | |
| image_id/instance/review 主鍵無重複或漏對照 | | |
| 原圖 decode/尺寸/方向/bytes hash 一致 | | |
| Train/val/test 患者交集皆空 | | |
| Test 未進 exemplar、訓練或門檻校準 | | |
| 每張都有已簽署 yes 與 usable | | |
| 所有目標病灶均有 accepted/corrected final | | |
| 每張 required review count 達成且身份合格 | | |
| 全部必要第二覆核與裁決完成 | | |
| 無 proposed/uncertain/pending/error 混入 | | |
| Mask 為原尺寸、0/1、非空、hash 正確 | | |
| Semantic union 包含全部 approved instances | | |
| Palette/RGB/void 的轉換都有明確映射 | | |
| 工具往返合成圖測試與真圖 overlay 已驗收 | | |
| 陰性資料獨立列出；未擅自產生負 mask | | |
| 所有引用路徑可讀，重定位規則有文件 | | |
| Release 拒覆寫，配置/程式/模型/review 版本凍結 | | |
| 分層效能、樣本量、區間、人工時間與限制已記錄 | | |
| Dataset card、artifact hashes 和驗收報告完整 | | |

只有所有必驗項目 PASS 才能發布。不適用要列理由與負責人核准，例如全人工版沒有模型校準數值，但不能將專家定稿或患者分區列成不適用。

失敗項目、修復責任人與重驗範圍：

專家同意標註用途及限制：

發布核准 / final manifest hash：
