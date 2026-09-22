# 批次紀錄表

複製到 `outputs/<run_id>/batch-record.md` 填寫；勿把臨床產物或患者清單寫回本模板。空白不是通過。

| 項目 | 填寫 |
|---|---|
| Run ID / 操作日期 / 工程師 | |
| 任務負責人 / 覆核專家 | |
| Source ID / 候選檔路徑與 SHA256 | |
| 程式 commit / 未提交差異檔與 hash | |
| 設定/環境快照路徑與 hash | |
| Protocol / partition / exemplar 版本 | |
| Encoder / preprocessing / checkpoint hash | |
| 檢索與 QC 閾值版本、核准者 | |
| 分割模型 / checkpoint hash | |
| 標註工具版本 / task / job mapping | |
| 起迄時間 / GPU 峰值 VRAM | |

## 數量與關卡

| 項目 | 影像數 | 患者數 | 病灶數/補充 |
|---|---:|---:|---|
| 全部候選 | | | |
| released | | | |
| negative_retained | | | |
| quality_excluded | | | |
| out_of_scope | | | |
| pending_review | | | |
| processing_error | | | |

- [ ] 候選數等於六種互斥去向總和。
- [ ] G0 資料完整性通過或錯誤已隔離。
- [ ] G1 規範與患者分區凍結。
- [ ] G2 檢索校準通過，或全人工替代並註明。
- [ ] G3 品質逐圖定稿。
- [ ] G4 所有目標病灶完成應有覆核。
- [ ] G5 發布清單驗收通過。

## 交接

最後成功階段：

待處理 artifact/錯誤清單路徑：

下一個確切操作（請附現有命令或人工步驟，不寫不存在的 CLI）：

專家待裁決事項及其 image/review ID：

本批次與上一批次改變的設定、模型或規範：
