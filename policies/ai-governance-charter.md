# AI Development Governance Charter｜教學版

Baseline：v1.0.0。這是 local-only lab 的教學 charter，不是法律、安全認證或 production policy。

## Purpose and use

- Scope：Task-board CLI 與本 repo artifact。
- Non-goals：真實使用者、客戶資料、外部服務、production。
- A0：讀本 lab tracked files。
- A1：隔離 worktree 內修改 allowed paths，附 diff／tests／checkpoint。
- A2：建立 PR、merge、push 均不授權給 Agent。
- A3：deploy、刪除、金流、restricted data、權限變更全部禁止。

## Data and vendor

- Data：synthetic-local。
- Model／vendor：不指定；任何 Agent 都受相同 Authority。
- Secret：不收。
- Trace：只留必要 command、exit、diff 與 test output；不收完整 environment。

## Authority

以 `agent-authority.yaml` 為機械可讀版本。Bootstrap 的 package network 是人明確啟動的環境準備，不延伸為 Agent 的任意 network 權限。Checker 對 tracked 與 durable artifact 是唯讀；執行 verifier 時，只例外允許 verifier-owned、gitignored、可丟棄的 cache、bytecode 與 coverage，不得把這個例外擴成 source、Spec、policy、task 或 Evidence 寫權。

## Evidence and rollout

- 缺 baseline、diff、verifier output 或 environment fingerprint 時不得宣告 pass。
- 只有本機與拋棄式環境；沒有 production rollout。
- Same failure 第二次出現就 escalate。

## Incident and retirement

- Kill switch：停止 loop process。
- Revoke：本 lab 不配置 token；若發現 credential，立即停止並移除 lab 外。
- Rollback：回 baseline commit，保留 failure Evidence。
- Retirement：停止新 run、保存必要決策、刪隔離 runtime；不涉及 vendor-side data。

## Exceptions

不得靜默 override。任何例外都要記 owner、理由、範圍、期限與補救；需要 production 或 restricted data 的例外在本 lab 一律拒絕。
