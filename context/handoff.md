# Handoff

- Task／Spec：`TB-LAB-001`／`specs/task-board.md`
- Current step：依 `evidence/` 中最新 run 判斷；聊天摘要不具權威。
- Canonical baseline：`scripts/verify.sh fast`
- Full gate：`scripts/verify.sh full`
- Authority：`policies/agent-authority.yaml`
- Durable Loop state：`.ai-loop/state.yaml`
- Append-only events：`.ai-loop/events.jsonl`
- Next safe action：先跑 fast baseline；若 exit 2，修環境而非修改 acceptance。
- Human decision：任何 Scope、Spec、network 或外部副作用變更。
- Recovery：回到已知 commit；runtime store 可刪除，production recovery 不適用。

這份 handoff 不宣告目前 checks 已通過。真實結果只能從該次 Evidence bundle 取得。
