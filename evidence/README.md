# Evidence

- `examples/not-run-manifest.json` 只示範 schema，刻意標為 `unknown`；
  它不是測試通過證明。
- `runs/` 由 `scripts/collect-evidence.sh` 每次建立新目錄，不覆寫舊 run。
- `loop-runs/` 保存每輪 verifier 的原始輸出與 failure signature。
- 每個 run 的 manifest schema version 2 記錄 OS、完整 Python identity、
  Git object format／commit、排除 generated runs 後的 source digest、
  dependency profile path／SHA-256、全部 exact pins 的 observed versions，
  以及 verifier exit／status。
- `dependency_profile.hash_locked_supply_chain` 固定為 `false`：constraints
  鎖定版本但沒有 artifact hashes，不得寫成 supply-chain 完整性證明。

可接受的狀態：

- `pass`：檢查執行且通過。
- `fail`：檢查執行但 acceptance 不通過。
- `environment-error`：環境、Git baseline、工具或必要資料不足。
- `unknown`：沒有證據可判斷。

Evidence bundle 可能含 diff 與 command output，但不得含 secret、credential、
customer data、完整 environment dump 或私人絕對路徑。
