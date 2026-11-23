# Thiết kế

Claude Foundry hoạt động thế nào, và vì sao lại làm như vậy. Mã nguồn đủ nhỏ
để đọc hết trong một lần: một skill, tám agent, ba script, một file config và
một dashboard. Phần cho app Frappe nằm riêng trong `profiles/frappe/`.

Claude Foundry là bản fork của Software Factory for Claude Code v2 (ZazenCodes,
GPLv3). Ý tưởng và luồng chạy giữ nguyên; phần khác được liệt kê ở cuối file.

## Ý tưởng

Một "nhà máy phần mềm" biến hàng đợi yêu cầu thành code đã merge theo một dây
chuyền cố định. Script lo các bước chắc chắn: chạy kiểm tra, chuyển trạng thái,
merge. Agent lo phần cần phán đoán ở giữa: yêu cầu có đáng làm không, làm chính
xác cái gì, viết code, và code đó có tốt không. Mỗi bước để lại một file, nên
lúc nào cũng xem được chuyện gì đã xảy ra và vì sao.

Mỗi file mở đầu bằng mục `## Summary` gồm ba tới năm gạch đầu dòng, để người đọc
lướt một job trên dashboard và chỉ đọc kỹ chỗ cần.

## Các thành phần

| Thành phần | File | Vai trò |
|---|---|---|
| Hàng đợi | Issue trên GitHub có nhãn `factory` | Việc cần làm. Ai cũng tạo được issue, nhưng chỉ người có quyền triage hoặc write mới gắn được nhãn. |
| Điều phối | `.claude/skills/factory/SKILL.md` | Phiên Claude Code chạy `/factory`. Mở job, gọi agent, gọi script. Tự nó không viết gì. |
| Agent | `.claude/agents/*.md` | Mỗi vai một file. Mỗi agent đọc file, viết đúng một file, và trả lời bằng một dòng. |
| Trạng thái | `factory/jobs/<job-id>/` | `job.json` cùng file của mọi agent. Bị gitignore, chỉ nằm trên máy chạy factory. |
| Xương sống | `factory/bin/job`, `gate`, `route` | Chạy theo luật cố định. `job` là nơi duy nhất ghi `job.json` và từ chối mọi bước chuyển sai luật. |
| Kiểm tra | `factory/checks.sh` | Lệnh test, lint, typecheck, build của repo. Script duy nhất phải viết riêng cho từng repo. |
| Cấu hình | `factory/config.json` | Số job chạy cùng lúc, số vòng tối đa, nhánh gốc, ngôn ngữ, nhãn, bảng chọn reviewer, file bị khoá, cổng, bảng giá. |
| Dashboard | `factory/dashboard.html` | Bảng theo dõi job, giao diện Paper Pop (sáng và tối). |
| Đầu ra | PR | Mỗi job kết thúc bằng một PR đóng issue của nó. Merge PR là duyệt. |

## Dây chuyền

```
intake (opus, high)  → ACCEPT (có thể thu hẹp phạm vi) | NEEDS-INFO | REJECT, đăng thành comment trên issue
route (script)       → chọn reviewer và model từ risk/surfaces theo config.json
worktree             → nhánh factory/<job-id> tách từ origin/<base_branch>
spec-writer (opus)   → spec.md
builder (opus)       → commit; lần push đầu mở draft PR "Closes #<n>"
gate (script)        → checks.sh; FAIL → trả log cho builder, không gọi reviewer
reviewers (theo route) → chạy song song, ĐỢI ĐỦ; có CHANGES → builder → gate → reviewers (tối đa max_rounds vòng)
approver (opus)      → APPROVE: đồng bộ với origin/<base_branch>, gate lại, gh pr merge
                       ESCALATE: PR chuyển sang ready, quyết định đăng thành comment, gắn nhãn factory:needs-human
```

`stage` trong `job.json` là một trong `intake`, `needs-info`, `spec`, `build`,
`gate`, `review`, `approve`, `merging`, `needs-human`, `merged`, `rejected`.
Các bước chuyển hợp lệ nằm trong `TRANSITIONS` ở đầu `factory/bin/job`. Một job
ở bất kỳ stage nào cũng chuyển được sang `merged` khi PR của nó đã được merge
trên GitHub, kể cả khi người merge tay giữa chừng.

Dashboard xếp job thành bảy cột: Intake, Spec, Build, Review, Approve, Needs
human, Done.

## Model của từng agent

Chỉ dùng Sonnet và Opus, không dùng Haiku.

| Agent | Model | Khi nào chạy |
|---|---|---|
| intake | Opus, effort high | mỗi issue, một lần |
| spec-writer | Opus | mỗi job |
| builder | Opus | mỗi vòng |
| reviewer-code | Sonnet (risk `low`, `medium`), Opus (risk `high`) | mỗi vòng |
| reviewer-ux | Sonnet | khi intake gắn surface `ui` |
| reviewer-ui | Sonnet | khi intake gắn surface `ui` |
| reviewer-security | Opus | khi intake gắn surface `security` |
| approver | Opus | khi mọi reviewer PASS |

Model của intake, spec-writer, builder và approver nằm trong frontmatter của
agent. Model của reviewer do `factory/bin/route` chọn từ `routing` và
`surface_reviewers` trong `config.json`, nên đổi được mà không sửa prompt nào.

## Các quyết định

**Issue là hàng đợi; bạn là người bấm chạy.** `/factory run` lần lượt xử lý mọi
issue `factory` đang mở. Không có gì chạy trên GitHub Actions hay theo lịch:
factory chạy trên máy bạn, bằng gói Claude của bạn, khi bạn khởi động nó. Một
issue không tự mở được phiên Claude Code, và chạy tại máy thì worktree, phòng
thử và dashboard đều nằm ngay trước mặt.

**Một bộ điều phối cho mọi job.** Phiên chạy `/factory run` mở tối đa
`concurrency` job cùng lúc (mặc định 3, ví dụ candy_wiki là 1) và gọi mọi agent
dưới dạng subagent chạy nền. Không có bộ điều phối riêng cho từng job phải phối
hợp với nhau. Context của nó nhỏ vì agent và script chỉ trả về một dòng; chi
tiết nằm trong file mà agent sau sẽ đọc. Claude Code mặc định cho 20 subagent
chạy cùng lúc trong một phiên, đủ cho ba job, mỗi job bốn reviewer. Chính
`factory/bin/job queue` giữ giới hạn `concurrency`: job đang chạy giữ một chỗ,
`job create` từ chối khi hết chỗ.

**Xem kỹ ở cửa, một lần.** Intake chạy một lần cho mỗi job, bằng Opus với
effort high. Nó quyết định issue có đáng làm không, viết lại phạm vi khi issue
quá lớn hoặc quá mơ hồ, và hỏi tác giả khi chỉ họ mới trả lời được. Quyết định
được đăng thành comment trên issue; nội dung issue giữ nguyên. Câu hỏi đến tay
tác giả trước khi có spec, nên spec-writer không bao giờ bị kẹt vì thiếu thông
tin. Job hỏi lại thì nằm ở `needs-info`, không giữ chỗ, cho tới khi tác giả trả lời.

**Rủi ro quyết định việc kiểm tra, script làm việc chọn.** Intake chấm `risk`
(`low`, `medium`, `high`) và `surfaces` (`ui`, `security`). `factory/bin/route`
tra hai thứ đó trong `config.json` (xem bảng model ở trên). Một thay đổi rủi ro
thấp, không đụng giao diện chỉ chạy một reviewer code bằng Sonnet. Toàn bộ việc
chọn reviewer nằm trong một file và đọc được ngay.

**Script quyết định code có chạy không.** Gate chạy `checks.sh` trước khi gọi
bất kỳ reviewer nào, và chạy lại sau khi đồng bộ với nhánh gốc, ngay trước khi
merge. Build hỏng quay thẳng về builder kèm log. Gate chạy bản `checks.sh` của
checkout chính, nên một nhánh không sửa được bài kiểm tra dùng để chấm chính
nó. Gate cũng đánh trượt nhánh nào sửa hoặc xoá file khớp `protected_paths`:
kiểm tra và cấu hình của factory (ví dụ candy_wiki khoá thêm cấu hình lint,
semgrep và commitlint). Thêm file mới thì được. Test không bị khoá, vì tính năng
mới phải cập nhật test; reviewer-code đánh trượt test nào bị nới lỏng, bỏ qua
hay viết riêng cho trường hợp để qua. Builder còn có hook `Stop` gọi
`factory/bin/gate --hook`, chạy kiểm tra một lần trước khi builder kết thúc
như một lời nhắc; người quyết định vẫn là gate.

**Agent phán đoán phần script không làm được.** Reviewer không chạy lại bộ
test; họ đọc diff để xem tính đúng, phạm vi, bảo mật, UX và độ khớp giao diện.
Reviewer ux và ui mở trang thật để xem, mỗi agent một cổng riêng.

**Mỗi issue một PR, merge qua GitHub.** Bản v1 gốc merge ở máy, và hỏng khi
checkout chính đang bẩn hoặc đang bận. Ở đây merge bằng `gh pr merge`, nên
branch protection, required checks và lịch sử PR đều được áp dụng, còn checkout
chính của bạn không bao giờ bị đụng. Trước khi merge, nhánh được đồng bộ với
nhánh gốc và gate lại, vì có thể job khác vừa merge sau lần kiểm tra trước.
Cách merge lấy từ `merge_method`.

**Bạn duyệt bằng cách merge.** Approver tự merge những gì nó chắc chắn, còn lại
đẩy lên bạn kèm một câu hỏi cụ thể. PR bị đẩy lên thì chuyển sang ready for
review, issue gắn nhãn `factory:needs-human`. Merge để duyệt, hoặc bảo factory
sửa gì bằng `/factory <bất kỳ>`: lời của bạn được lưu nguyên văn thành
`feedback-<k>.md` cho builder, và job chạy thêm một vòng với số vòng được đặt
lại. Muốn bỏ một job đang chờ bạn hoặc chờ tác giả, bảo factory reject nó: lý
do được đăng lên issue, PR bị đóng, nhãn factory bị gỡ, job chuyển sang Done.

**Người đọc đọc bằng ngôn ngữ của mình.** `language` trong `config.json` (mặc
định `English`, ví dụ candy_wiki là `Vietnamese`) được truyền vào dòng đầu
prompt của mọi agent. Những gì người đọc để duyệt viết bằng ngôn ngữ đó: đánh
giá của intake, spec, báo cáo build, các bài review, quyết định, nội dung PR,
comment trên issue và tin nhắn của bộ điều phối. Code, commit, tiêu đề PR, tiêu
đề mục `##` và các dòng đầu mà script đọc (`DECISION:`, `VERDICT:`, `GATE:`,
`STATUS:`, `APPROVE`…) giữ tiếng Anh, vì script và dashboard dựa vào chúng.

**Trạng thái là file, nên chạy lại được.** Mọi thông tin bộ điều phối cần đều
nằm trong `factory/jobs/`. Phiên chết hay bị nén context thì một `/factory run`
mới đọc hàng đợi và chạy tiếp mọi job từ stage của nó.

**Chỗ đặt worktree và việc dọn dẹp cấu hình được.** Mặc định worktree của job
nằm ở `.worktrees/<job-id>`. `worktree_path` đổi được chỗ này; app Frappe đặt nó
trong một thư mục có dạng bench (`.../<job>/apps/<app>`), vì bước build giao
diện tìm `../../sites` như trong bench thật. Khi job kết thúc (merged hoặc
rejected), worktree và nhánh local bị xoá, rồi các lệnh trong `on_finish` chạy,
ví dụ xoá phòng thử. Lệnh `on_finish` lỗi chỉ được báo, không chặn job.

**Chi phí đo theo từng job.** Claude Code ghi transcript của từng subagent, kèm
model và số token mỗi tin nhắn, vào
`~/.claude/projects/<project>/<session>/subagents/`. Mọi prompt của factory mở
đầu bằng thư mục của job (`Job folder: <path>/`), nên `factory/bin/job` cộng các
transcript có chuỗi đó và tính tiền theo `prices_usd_per_mtok`. Con số là giá
tương đương API của các agent trong job; với gói subscription nó cho biết tiền
đi về đâu, không phải số bạn bị tính. Token của chính bộ điều phối không tính
vào job nào. Định dạng transcript không phải giao diện được công bố, nên bản
cập nhật Claude Code có thể làm phần này hỏng.

## Profile Frappe

App Frappe chỉ chạy được trong bench, nên `profiles/frappe/` bổ sung những gì
factory cần ở đó. Phần chung của factory không đổi; profile chỉ thêm script,
thêm đoạn hướng dẫn vào cuối từng agent, và cung cấp một cấu hình mẫu.

**Mỗi job một phòng thử.** `frappe-sandbox` tạo cho mỗi job một site tạm, chép
database từ `source_site` (với candy_wiki là `preview.localhost`) tại lúc tạo,
chạy code của nhánh job nhờ app được cài dạng editable và `PYTHONPATH` trỏ vào
worktree. Phòng thử có cổng riêng
(`http://job004-<app>.localhost:5145`), tắt email, tạm dừng scheduler, tắt
developer mode, và có hàng đợi Redis cùng worker riêng, nên tác vụ nền cũng
chạy code của nhánh. Site gốc không bị đụng tới. `up` build lại asset và chỉ
migrate khi nhánh đổi schema (DocType JSON, `hooks.py`, patch). Cấu hình nằm ở
`factory/frappe.json`: container, bench, site gốc, lệnh build, script
`setup`/`teardown` (candy_wiki dùng để tạo và xoá chỉ mục Qdrant riêng). Phòng
thử bị xoá qua `on_finish` khi job kết thúc.

**Chỉ chạy test liên quan.** `frappe-test` chọn test Python theo file nhánh đã
đổi (test bị đổi, `test_<name>.py` cạnh file bị đổi, test của DocType bị đổi,
cộng những gì `tests.select_cmd` in ra) rồi chạy trên phòng thử. `frappe-e2e`
làm tương tự với spec Playwright (spec bị đổi, spec trùng tên với file bị đổi,
`select_cmd`), cộng các spec `smoke` khi nhánh đổi nhiều hơn docs và thư mục
của factory, rồi chạy trên trình duyệt thật vào phòng thử. Lệnh chọn test luôn
lấy từ thư mục `factory/` của checkout chính, nên nhánh không đổi được cách chọn
test của chính nó.

**Nhánh chỉ chịu trách nhiệm cho cái nó làm hỏng.** App đang có sẵn lỗi cũ thì
không bắt job gánh. `ruff-new` so lỗi ruff của file bị đổi giữa nhánh và nhánh
gốc, chỉ đánh trượt lỗi mới. `frappe-e2e` giữ một **mốc** là danh sách bài e2e
đã hỏng sẵn trên nhánh gốc (`e2e-baseline.json` trong thư mục phòng thử, tạo
bằng `frappe-e2e baseline`); bài hỏng được chạy lại một lần trước khi kết luận,
và job chỉ trượt khi làm hỏng một bài đang chạy tốt.

**Agent dùng thử như người thật.** Builder và reviewer ux/ui đăng nhập phòng
thử bằng `agent-browser`, bấm thử luồng và lưu ảnh chụp vào
`round-<N>/shots/`. Approver đẩy lên người khi một thay đổi giao diện chưa có ai
xem trong phòng thử. Dashboard hiện ảnh chụp trong ngăn chi tiết của job và nút
**▶ try it** (đọc từ `sandbox.json`) để bạn tự mở phòng thử dùng thử trước khi
merge.

Cấu hình mẫu đầy đủ, đã chạy thử, nằm ở `profiles/frappe/examples/candy_wiki/`.
Hướng dẫn cài bằng tiếng Việt: `profiles/frappe/HUONG-DAN-CAI.md`.

## Rào chắn an toàn

- Chỉ issue có nhãn `factory` mới chạy. Gắn nhãn cần quyền triage hoặc write,
  nên nhãn chính là ranh giới tin cậy. `job create` từ chối issue không có nhãn.
- Nội dung issue đến tay agent dưới dạng dữ liệu được trích dẫn trong
  `issue.md`, chỉ kèm comment của tác giả issue và của người chạy factory. Nó
  không bao giờ là một phần của prompt. Intake, agent đọc nó đầu tiên, không
  có shell.
- Agent chỉ push nhánh `factory/*`. Chỉ `factory/bin/job merge` được merge, qua
  `gh pr merge`. Factory không bao giờ deploy.
- Mỗi issue một PR; mỗi job tối đa `max_rounds` vòng build trước khi hỏi người.
- Với Frappe: agent không migrate, ghi hay chạy test trên site nào ngoài phòng
  thử của job mình.

## Khác gì so với bản gốc

| Bản gốc (ZazenCodes v2) | Claude Foundry |
|---|---|
| Reviewer code rủi ro thấp chạy Haiku, reviewer ui chạy Haiku | Chỉ Sonnet và Opus; reviewer code rủi ro `high` lên Opus |
| Mọi nội dung viết bằng tiếng Anh | `language` trong config: người đọc duyệt bằng ngôn ngữ của mình, phần máy đọc giữ tiếng Anh |
| Worktree cố định ở `.worktrees/<job-id>` | `worktree_path` và `on_finish` cấu hình được |
| Dashboard giao diện riêng | Dashboard Paper Pop, sáng và tối, có ảnh chụp và nút ▶ try it |
| Chỉ có cấu hình chung | Thêm `profiles/frappe/`: phòng thử theo job, test Python và e2e liên quan, mốc lỗi có sẵn, hướng dẫn cài tiếng Việt |

Bản gốc v2 đã thay v1 ở các điểm: hàng đợi bằng issue thay vì một job mỗi
phiên, intake chấm rủi ro để chọn reviewer, `checks.sh` chặn trước khi review
và trước khi merge, merge qua PR thay vì `git merge` ở máy, intake hỏi tác giả
thay vì để spec-writer kẹt, và hiện chi phí theo từng job.
