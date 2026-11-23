# Hướng dẫn cài Claude Foundry vào candy_wiki

Làm theo từng bước dưới đây, mỗi bước là một khối lệnh để chép rồi dán vào terminal (WSL).
Cả quá trình mất khoảng 15 phút, chưa kể thời gian chờ duyệt PR.

Bạn sẽ không đụng tới branch đang làm: mọi thứ được cài trong một bản checkout tạm, rồi đưa lên
GitHub bằng một PR.

## Factory sẽ làm gì cho candy_wiki

- Bạn tạo issue trên GitHub, gắn nhãn `factory`, rồi gõ `/factory run` trong Claude Code.
- Mỗi issue thành một **job**. Mỗi job có một **phòng thử**: một site tạm chép từ
  `preview.localhost` (dữ liệu thật mới nhất), chạy code của branch đó, mở ở địa chỉ dạng
  `http://job004-candy-wiki.localhost:5145`.
- Agent viết code, chạy kiểm tra, rồi đăng nhập phòng thử để bấm thử và chụp màn hình.
- Bước kiểm tra tự động có chạy cả **test e2e** (Playwright) của candy_wiki trên phòng thử:
  những bài liên quan tới phần bị sửa, cộng một bài "smoke" xem trang chủ Guidelines còn chạy.
  Nhờ vậy tính năng cũ bị hỏng thì job bị chặn lại, kể cả khi agent không nghĩ tới việc thử nó.
- Trên dashboard có nút **▶ try it** để bạn tự mở phòng thử và dùng thử trước khi merge.
- Phòng thử tắt email, tạm dừng tác vụ nền theo lịch, và có bản chỉ mục tìm kiếm Qdrant riêng.
  Candy AI vẫn chạy bình thường. `preview.localhost` không bị đụng tới.
- Job xong (merge hoặc bỏ) thì phòng thử tự được xoá.
- Những gì bạn đọc để duyệt đều bằng tiếng Việt: đánh giá của intake (đăng lên issue), spec, báo
  cáo của builder, các bài review, quyết định của approver, nội dung PR, và tin nhắn của factory
  trong terminal. Code, commit, tiêu đề PR và các tiêu đề mục (`## Summary`…) giữ tiếng Anh, vì
  repo quy định vậy và dashboard dựa vào chúng.

## Bước 0. Kiểm tra máy

```bash
claude --version          # cần 2.1.257 trở lên
gh auth status            # đã đăng nhập GitHub
agent-browser --version   # trình duyệt cho agent (đã cài)
uvx --version             # dùng để chạy ruff
ls ~/.cache/ms-playwright | grep chromium   # trình duyệt cho test e2e
docker ps --format '{{.Names}}' | grep frappe_docker_devcontainer-frappe-1   # bench đang chạy
```

Dòng nào báo lỗi thì xử lý dòng đó trước. Nếu dòng `ms-playwright` không in ra `chromium-…` thì
cài trình duyệt cho Playwright:

```bash
cd ~/frappe_docker/development/frappe-bench-preview/apps/candy_wiki && node_modules/.bin/playwright install chromium
```

## Bước 1. Tạo bản checkout tạm từ `version-16`

```bash
APP=~/frappe_docker/development/frappe-bench-preview/apps/candy_wiki
INSTALL=~/frappe_docker/development/.factory-sandboxes/install-candy_wiki
F=~/claude-foundry

cd $APP
git fetch origin
git worktree add $INSTALL -b chore/install-factory origin/version-16
cd $INSTALL
```

Bản tạm phải nằm trong `~/frappe_docker`, để container của bench thấy được nó khi chạy kiểm tra.

## Bước 2. Chép các file của factory

```bash
mkdir -p .claude/skills/factory .claude/agents factory/bin
cp $F/.claude/skills/factory/SKILL.md .claude/skills/factory/
cp $F/.claude/agents/*.md .claude/agents/
cp $F/factory/bin/job $F/factory/bin/gate $F/factory/bin/route factory/bin/
cp $F/factory/dashboard.html factory/
cp $F/profiles/frappe/bin/* factory/bin/
cp $F/profiles/frappe/examples/candy_wiki/factory/* factory/
chmod +x factory/bin/* factory/checks.sh
```

Các file vừa chép, theo vai trò:

| File | Để làm gì |
|---|---|
| `.claude/skills/factory/`, `.claude/agents/` | lệnh `/factory` và các agent |
| `factory/bin/job`, `gate`, `route` | quản lý job, chạy kiểm tra, chọn reviewer |
| `factory/bin/frappe-sandbox` | tạo, chạy và xoá phòng thử |
| `factory/bin/frappe-test` | chọn và chạy test Python liên quan trên phòng thử |
| `factory/bin/frappe-e2e` | chọn và chạy test e2e Playwright liên quan trên phòng thử |
| `factory/bin/ruff-new` | chỉ đánh trượt lỗi ruff mà branch mới tạo ra |
| `factory/config.json` | base `version-16`, mỗi lần 1 job, các file bị khoá, ngôn ngữ báo cáo (`Vietnamese`) |
| `factory/frappe.json` | container, site gốc, lệnh build của candy_wiki |
| `factory/checks.sh` | các bước kiểm tra trước khi reviewer đọc |
| `factory/sandbox_setup.py`, `sandbox_teardown.py` | tạo và xoá bản chỉ mục Qdrant riêng |
| `factory/select_tests.py` | chọn test Python và e2e theo `FEATURE_MAP` (khi branch đã có file này) |
| `factory/dashboard.html` | dashboard Paper Pop |

## Bước 3. Thêm hướng dẫn Frappe cho các agent

```bash
for a in builder reviewer-ux reviewer-ui reviewer-code reviewer-security approver spec-writer; do
  printf '\n' >> .claude/agents/$a.md
  cat $F/profiles/frappe/agents/$a.md >> .claude/agents/$a.md
done
```

Sau đó mở `.claude/agents/intake.md`, tìm dòng `## Decide`, và dán dòng sau ngay bên dưới (cách
một dòng trống):

```markdown
Candy Wiki is GLAC's guideline and knowledge hub (Frappe + Vue): guidelines, reviews, change management, tags and permissions, Candy AI and the public reader belong here; anything else doesn't.
```

## Bước 4. Bổ sung AGENTS.md và .gitignore

```bash
printf '\n' >> AGENTS.md
cat $F/profiles/frappe/examples/candy_wiki/AGENTS-section.md >> AGENTS.md
printf '\n/factory/jobs/\n/.worktrees/\n' >> .gitignore
```

Đoạn thêm vào AGENTS.md nói cho agent của factory biết:
- được push branch `factory/<job>` và mở PR (ngoại lệ của luật "chỉ push khi được yêu cầu");
- dùng phòng thử thay cho `preview.localhost`;
- không chạy `scripts/preview.sh`, `verify.py`, `test-parallel.sh`.

## Bước 5. Chạy thử các bước kiểm tra

```bash
ln -sr $APP/node_modules node_modules
ln -sr $APP/frontend/node_modules frontend/node_modules
bash factory/checks.sh
python3 -m json.tool factory/config.json > /dev/null && echo "config OK"
factory/bin/job queue
```

Kết quả đúng là:
- `checks.sh` in ra `✔ All checks passed.`. Bước e2e báo "nothing to run" vì branch cài đặt chỉ
  đổi file của factory;
- `config OK`;
- `job queue` chạy mà không báo lỗi. Danh sách có thể trống.

Hai symlink `node_modules` đã bị git bỏ qua, nên không lọt vào commit. Mỗi job thật cũng tự tạo
hai symlink này.

## Bước 6. Tạo nhãn trên GitHub

```bash
R=Global-Link-Asia-Consulting/candy-wiki
gh label create factory --repo $R --color 5319E7 --description "Build this with the software factory"
gh label create factory:needs-info --repo $R --color FBCA04 --description "The factory asked the author a question"
gh label create factory:needs-human --repo $R --color D93F0B --description "The factory needs a human decision on the PR"
```

## Bước 7. Commit, mở PR, merge

```bash
git add .claude factory AGENTS.md .gitignore
git status --short     # xem lại: chỉ có file của factory, AGENTS.md và .gitignore
git commit -m "chore: install Claude Foundry software factory"
git push -u origin chore/install-factory
gh pr create --repo Global-Link-Asia-Consulting/candy-wiki --base version-16 \
  --title "chore: install Claude Foundry software factory" \
  --body "## Why?
Run GitHub issues through the factory, each job in its own sandbox site.

## What?
Factory skill, agents, scripts and dashboard, with candy_wiki's checks and sandbox config.

## How?
See factory/frappe.json and factory/checks.sh."
```

Mở link PR, xem diff, rồi merge trên GitHub.

## Bước 8. Đưa factory vào bản checkout chính

Lệnh `/factory` chạy từ bản checkout chính (`$APP`), nên bản đó phải có thư mục `factory/`.
Chọn một trong hai cách:

```bash
cd $APP
# Cách A: chuyển sang version-16
git switch version-16 && git pull
# Cách B: giữ branch đang làm, merge version-16 vào
git fetch origin && git merge origin/version-16
```

Lưu ý: preview chạy đúng code của bản checkout chính, nên sau bước này preview chạy code của
branch bạn vừa chọn.

Xoá bản checkout tạm:

```bash
git worktree remove --force $INSTALL
```

## Bước 9. Chạy job đầu tiên

1. Tạo một issue nhỏ trên GitHub, ví dụ "Đổi chữ nút X thành Y", rồi gắn nhãn `factory`.
2. Mở Claude Code trong thư mục app:
   ```bash
   cd $APP && claude
   ```
   rồi gõ `/factory run <số issue>`.
3. Mở dashboard ở một terminal khác:
   ```bash
   cd $APP/factory && python3 -m http.server
   ```
   Truy cập http://localhost:8000/dashboard.html.
4. Khi thẻ job có nút **▶ try it**, bấm vào rồi đăng nhập `Administrator` / `admin` để tự dùng
   thử. Ảnh chụp của agent nằm trong ngăn chi tiết của job (bấm vào thẻ).
5. Thấy ổn thì merge PR trên GitHub. Muốn sửa thì gõ `/factory <góp ý của bạn>`.

## Lệnh hay dùng với phòng thử

```bash
cd $APP
factory/bin/frappe-sandbox status          # các phòng thử đang có
factory/bin/frappe-sandbox up <job>        # bật lại, in địa chỉ
factory/bin/frappe-sandbox down <job>      # tắt (giữ dữ liệu)
factory/bin/frappe-sandbox drop <job>      # xoá hẳn
```

Muốn biết một job sẽ chạy những bài e2e nào, đứng trong thư mục worktree của job đó rồi chạy
`python3 $APP/factory/bin/frappe-e2e --dry-run`.

## Cần biết

- Lần đầu tạo phòng thử mất khoảng 2–4 phút: chép database khoảng 270 MB, build giao diện, migrate.
  Những lần sau chỉ build lại phần đã đổi.
- Bước e2e chạy trên trình duyệt thật nên chậm: mỗi file test mất khoảng 1–2 phút. Một job bình
  thường chạy 1–4 file. Kết quả đầy đủ nằm ở `logs/e2e.log` trong thư mục phòng thử, ảnh chụp và
  trace của bài hỏng nằm ở `e2e-results/`.
- Bộ e2e của candy_wiki đang có nhiều bài hỏng sẵn trên `version-16`: lần đo ngày 2026-11-23 là
  138/346 bài, phần lớn vì bài test còn tìm giao diện "Spaces" cũ. Factory không bắt branch chịu
  trách nhiệm cho những bài đó. Nó giữ một **mốc** là danh sách bài hỏng sẵn, nằm ở
  `~/frappe_docker/development/.factory-sandboxes/candy_wiki/e2e-baseline.json` (đã tạo sẵn,
  không nằm trong repo). Job chỉ bị trượt khi làm hỏng một bài **đang chạy tốt**. Mỗi bài hỏng
  được chạy lại một lần trước khi kết luận, để lỗi chập chờn không làm trượt job oan.
- Mốc cũ dần khi `version-16` thay đổi. Sau khi sửa được một nhóm bài test, làm mới mốc cho đúng
  các file đó, mỗi file mất vài phút:
  ```bash
  cd $APP && factory/bin/frappe-sandbox down main 2>/dev/null; factory/bin/frappe-e2e baseline e2e/tests/sidebar.spec.ts
  ```
  Bỏ tên file thì nó chạy lại cả bộ, mất hơn một tiếng. Xong thì chạy lệnh dọn dẹp mà nó in ra.
- Phòng thử chép dữ liệu tại thời điểm tạo. Muốn dữ liệu mới hơn thì `drop` rồi `up` lại.
- Mỗi phòng thử tốn thêm một database và khoảng 34 MB file (dùng hard link nên gần như không tốn
  thêm). Nên chạy mỗi lần 1 job (`concurrency: 1` trong `factory/config.json`) cho tới khi bạn
  tin tưởng factory.
- Khi branch `chore/state-tests` (có `ci.sh`, semgrep gate, `FEATURE_MAP`) được merge vào
  `version-16`, `checks.sh` tự chạy thêm semgrep gate và kiểm tra bản đồ tính năng, và chọn test
  Python lẫn e2e theo `FEATURE_MAP`. Bạn không cần sửa gì.
