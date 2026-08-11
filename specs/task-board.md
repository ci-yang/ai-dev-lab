# SPEC-TB-001｜Local-only Task Board

## Problem and desired outcome

讀者需要一個足夠小、能直接看懂，又能真實展示 task contract、Context、Harness、Evidence、delegation 與 bounded Loop 的程式。結果是本機 CLI，不是 production 產品。

## Users and stakeholders

- User：具備基本 Python 與 Git 的讀者。
- Outcome owner：執行 lab 的人。
- Maintainer：lab 維護者。

## Current behavior and baseline

Reference implementation 以 JSON array 保存 task。可觀察行為由下列 `SAC-*` 與 tests 定義；沒有 Evidence 的環境不得宣告 baseline pass。

## Scope

- Init、add、list、show、complete。
- Local JSON store。
- Stable text output 與 exit 0／2。

## Non-goals

- GUI、帳號、多使用者、同步、網路、資料庫、排程、通知。
- Production deploy、migration、billing、auth。
- Autonomous merge 或 production／remote service 寫入。

## Acceptance criteria

- SAC-01：init 在 store 不存在時建立空 array；存在時不覆寫。
- SAC-02：add trim title，分配 `TB-NNN`，priority 只能 low／medium／high。
- SAC-03：list 依 ID 排序，並能篩選 todo／done。
- SAC-04：complete 只把既有 task 轉為 done；未知 ID 回 exit 2。
- SAC-05：空白 title、未知欄位、非法 status／priority、非 array store 都拒絕。
- SAC-06：save 在同一目錄寫 temporary file，flush／fsync 後 atomic replace。
- SAC-07：輸入中的 shell syntax 只當文字，不被 guard 展開。
- SAC-08：runtime 不含 network client、不要求 credential；官方範例只用
  gitignored 的 `runtime/`。
- SAC-09：`--store` 接受使用者指定的本機路徑並可建立 parent directory；
  CLI 不提供 OS path confinement。

## Examples and edge cases

- 第一筆：`TB-001 [todo] high | 建立第一份 Evidence`。
- 空白 title：拒絕，store 不得被建立。
- Corrupt store：拒絕，不得以空 array 覆蓋。
- `Keep $(commands) as plain text`：保留原文，不執行 command substitution。

## Constraints and compatibility

- Python 3.12+；exact tool profile 見
  `constraints/runtime-profile.txt`。
- Runtime standard library only。
- UTF-8 JSON。
- macOS／Linux 的 Bash scripts；Windows 未驗證。

## Open questions

- Windows PowerShell bootstrap：目前未驗證；不阻擋 macOS／Linux lab，owner 為 lab 維護者。
- Concurrent writers：不在 V3 lab scope；若加入，先建立 locking／transaction Spec。

## Evidence plan

- Unit／CLI／script／contract tests。
- fast 與 full verifier。
- 隔離 copy 的 bootstrap、guard、evidence、loop 成功與失敗路徑。
- Scoped secret／private-path scan。

## Rollback or exit

Code 回到 baseline commit。官方範例的 Runtime store、Evidence runs 與
Loop checkpoints 在隔離 lab 內可丟棄。產品不含 production／remote
service integration；若使用者自行把 `--store` 指到 lab 外，該本機檔案
不會由 rollback 自動處理。
