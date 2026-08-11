# Task TB-LAB-001｜建立可驗證的本機 Task Board

## Goal

在本機 JSON store 新增、列出、查看與完成 task；任何人能以同一命令重跑驗證。

## Context pointers

- `AGENTS.md`
- `specs/task-board.md`
- `context/context-manifest.md`
- `policies/agent-authority.yaml`

## Scope

- Allowed: `src/task_board/`、`tests/`、本 task 的 Evidence。
- Forbidden: 網路功能、資料庫、GUI、登入、雲端同步、production integration。

## Constraints

- Python 3.12+；exact tool profile 由
  `constraints/runtime-profile.txt` 定義。
- Runtime 只用標準庫。
- Task 為 frozen dataclass。
- JSON 寫入採 atomic replace。
- 不吞錯誤；預期的 input／環境錯誤回 exit 2。
- 不讀取或保存 secret。

## Acceptance and Evidence

- TAC-01：第一筆 task ID 是 `TB-001`，後續單調遞增。
- TAC-02：list 可分辨 todo 與 done。
- TAC-03：complete 不改寫 task ID、title、priority。
- TAC-04：空白 title、未知 task、壞 JSON 不得被當成成功。
- TAC-05：重跑 init 不覆寫現有資料。
- TAC-06：`scripts/verify.sh full` 通過並達 80% coverage。

`TAC-*` 是這張 task 的驗收編號；`SAC-*` 是
`specs/task-board.md` 的產品行為編號。兩者不能只靠尾碼推定對應：

| Task acceptance | Spec／gate 對應 |
|---|---|
| TAC-01 | SAC-02 |
| TAC-02 | SAC-03 |
| TAC-03 | SAC-04 |
| TAC-04 | SAC-04、SAC-05 |
| TAC-05 | SAC-01 |
| TAC-06 | Task-only verification gate；對應 Spec 的 Evidence plan，不是產品行為 SAC |

Evidence：pytest output、coverage、diff、commit、exit code 與 known gaps。

## Authority

- Agent read/write scope：本 lab 的 task／policy 指定路徑。
- Execute：`scripts/verify.sh` 與 allowlist guard。
- Production／remote service side effects：不在授權 scope。
- 邊界說明：上述是 task policy，不是 OS sandbox 證明。CLI 的 `--store`
  接受使用者指定的本機路徑；官方範例固定使用 `runtime/`。

## Stop and escalate

- Acceptance 需要改動 `specs/task-board.md`。
- 需要 runtime dependency、network、credential 或 production data。
- Baseline 先失敗或 full verifier 是 environment error。

## Return

回報 status、changed files、TAC／SAC 對應、commands／exit codes、Evidence path、risks／gaps。
