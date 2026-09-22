# 多人覆核與裁決表

填写在 outputs，對应不可變 review records；此表可當會議摘要，不能取代精確的 mask hash 與 metadata。

| 項目 | 填寫 |
|---|---|
| Run / image_id / instance_id(s) | |
| Protocol / input revision / proposal ID | |
| 專家 A / review ID / mask 路徑及 hash | |
| 專家 B / review ID / mask 路徑及 hash | |
| A/B 是否不同合格 reviewer；是否獨立判讀 | |
| 分歧：病灶存在 / 品質 / 數量 / 邊界 / 其他 | |
| 兩方判斷與理由 | |
| 裁決專家 / 時間 / 新 review ID | |
| 裁決：採 A / 採 B / 另畫 / 無法裁決 | |
| 定稿或 pending 的理由 | |
| Final mask 路徑 / hash / revision | |
| 圖層所有病灶是否都完成 | |
| 舊 release 是否受影響及處理方式 | |

- [ ] 保留 A/B 原始結果，未覆寫。
- [ ] 需要的所有覆核已完成；同一人多次審核不重複計人數。
- [ ] 新裁決引用原 review IDs；若無法裁決，保持 pending，未進 release。
