# ai-dev-lab：可驗證的 AI 驅動開發教學環境

> 狀態：v1.0.0 教學基線。這不是 production starter kit。

這是一個刻意縮小的 Python task-board CLI，用來示範如何把 task
contract、Context、Spec、Harness、Evidence、delegation 與 bounded
loop 接成一條能重跑、能驗收的工程流程。它是合成教學案例，**不是
真實產品、公司事故或 production 系統**。

Task Board runtime 沒有 network client、帳號、credential、客戶資料、
部署或 production integration；官方範例只操作本機合成資料。

## 取得固定版本

建議從 GitHub Release 下載與教學內容對應的固定版本：

<https://github.com/ci-yang/ai-dev-lab/releases/tag/v1.0.0>

Release 頁面提供原始碼壓縮檔、SHA-256 checksum 與驗證摘要。日後
`main` 可繼續更新，但 `v1.0.0` tag 不會跟著移動。

## 快速開始

需求：

- Python 3.12+
- Git
- macOS 或 Linux 的 Bash 環境

最省步驟的方式是直接 clone 固定 tag：

```bash
git clone --branch v1.0.0 --depth 1 \
  https://github.com/ci-yang/ai-dev-lab.git
cd ai-dev-lab
scripts/bootstrap.sh
scripts/verify.sh full
```

若從 Release 下載 `ai-dev-lab-v1.0.0.zip`，解壓後先在該副本建立
Git baseline，再執行 bootstrap 與 verifier：

```bash
cd ai-dev-lab-v1.0.0
git init -b main
git add .
git commit -m "chore: create lab baseline"
scripts/bootstrap.sh
scripts/verify.sh full
```

若 Git identity 尚未設定，先依 Git 顯示的指引設定再 commit。後續練習
會修改 runtime store、Evidence 與 loop state，請保留原始壓縮檔不動。

`bootstrap.sh` 預設使用 `constraints/runtime-profile.txt` 的 exact
pins 建立 Python 3.12+ 環境並安裝開發依賴。這是 version-locked
教學 profile，沒有 artifact hashes，不是 hash-locked supply-chain
保證。Fresh bootstrap 預設需要存取 Python package index。

Scripts 會依序使用明示的 `PYTHON_BIN`、本 lab 的
`.venv/bin/python`、系統 `python3`，因此 bootstrap 後不必依賴
`activate` 造成的隱形 shell state。要互動使用 venv，仍可執行：

```bash
source .venv/bin/activate
```

## 已驗證基線

在隔離副本與 Python 3.12 環境執行 `scripts/verify.sh full`：

- Ruff、Black、isort 全部通過。
- `47 passed`。
- Coverage `83.18%`，高於 contract 的 80%。
- macOS 本機驗證通過；GitHub Actions 會另跑 Linux gate。
- Windows PowerShell bootstrap 尚未驗證。

這些結果只適用於對應 commit 與 dependency profile；不要外推成
所有作業系統或未來版本都會通過。實際結果以 Release 的驗證摘要與
使用者自己重跑的 verifier 為準。

## 會練到什麼

- 用 Task contract 把「新增、列出、完成任務」寫成可驗收行為。
- 用 Context manifest 指向當次需要的 source of truth。
- 用 Spec 的 SAC 編號連接 tests 與 Evidence。
- 用 `scripts/verify.sh` 取得唯一 fast／full 驗證入口。
- 用 allowlist guard 拒絕未授權命令。
- 用 Evidence bundle 區分 pass、fail 與 environment error。
- 用 maker-checker delegation 練習 tracked artifact 唯讀驗收。
- 用最多三輪的 bounded loop 練習 stop、escalate、resume。
- 用 Authority policy 把 Agent scope 限定在 local teaching workflow。

## Task Board 範例

```bash
scripts/guard-command.sh task-board --store runtime/tasks.json init
scripts/guard-command.sh task-board --store runtime/tasks.json \
  add "建立第一份 Evidence" --priority high
scripts/guard-command.sh task-board --store runtime/tasks.json list
scripts/guard-command.sh task-board --store runtime/tasks.json complete TB-001
```

官方命令把 runtime 資料放在 gitignored 的 `runtime/`。重跑 `init`
不會覆寫既有資料；不存在的 task、空白標題與壞掉的 JSON 會回 exit 2。
CLI 的 `--store` 接受使用者指定的本機路徑，也會建立缺少的 parent
directory；它沒有提供作業系統層的 path confinement。

## 安全邊界

- Runtime 沒有 network client，也不需要 credential；這是功能範圍，
  不是 network isolation 證明。
- 官方範例只讀寫 lab 的 `runtime/`；`--store` 仍可寫入執行者有
  權限的其他本機路徑，沒有 OS filesystem sandbox。
- `bootstrap.sh` 是明示例外：預設會連 Python package index 安裝依賴。
- 不需要也不允許 production credential。
- 不執行任意 shell；教學命令走 `guard-command.sh` allowlist。
- `demo-repeated-failure` 是明確標示的教學 failure，不是真實事故。
- Approval、merge、push、deploy、刪除與對外訊息都不在教學 Agent
  Authority 內；這是 repo policy，不代表底層程序有 OS sandbox。

## Artifact 地圖

```text
AGENTS.md                     repo map、命令、stop rules
tasks/                        task 與 delegation contracts
context/                      context manifest 與 handoff
specs/                        行為、acceptance、non-goals
src/ + tests/                 implementation 與 executable evidence
scripts/                      verify、guard、evidence、bounded loop
evidence/                     schema example 與每次 run
policies/                     Authority、資料與治理
.ai-loop/                     contract、state、events、checkpoints
```

## Exit code

- `0`：指定檢查完成且通過。
- `1`：檢查真的執行，但 acceptance 不通過。
- `2`：命令、環境、資料格式、必要 Evidence 或 Authority 有問題。

Loop 因 repeated failure 進入 `escalated`／`blocked` 終止狀態時也會
回 `2`；此時要連同 state 與 terminal reason 判讀。不要把 exit 2
一律當成測試失敗，也不要把沒有執行的檢查寫成 pass。

## License

MIT
