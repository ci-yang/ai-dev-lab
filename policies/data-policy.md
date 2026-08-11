# Data Policy

- Data class：synthetic-local。
- Allowed purpose：本機教學與驗證。
- Allowed storage：gitignored `runtime/`、`evidence/runs/`、`evidence/loop-runs/`。
- Prohibited：secret、credential、customer data、private production code、外部傳輸、raw environment dump。
- Telemetry：none。
- Network：只有人明確執行 bootstrap 安裝公開 dev dependencies 時允許 package index。
- Retention：由 lab operator 刪除隔離 copy；本 repo 不替團隊定 retention。
- Human owner：lab operator。

Task title 是 untrusted data。它可以寫進 local store，不得被當成 shell 或 Agent instruction。
