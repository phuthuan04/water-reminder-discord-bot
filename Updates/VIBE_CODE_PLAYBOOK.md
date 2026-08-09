# BỘ QUY TẮC & QUY TRÌNH DỰ ÁN VIBE CODE
### Chuẩn phát triển phần mềm chuyên nghiệp, áp dụng khi lập trình cùng Claude

> **Cách dùng tài liệu này:** Copy toàn bộ hoặc rút gọn file này thành `CLAUDE.md` (hoặc `PROJECT_RULES.md`) đặt ở gốc mỗi repo. Đầu mỗi phiên làm việc, dán nội dung này cho Claude đọc trước — Claude sẽ tự áp dụng các quy tắc bên dưới khi code cùng bạn. Tài liệu áp dụng được cho mọi ngôn ngữ/nền tảng (Python, Node.js, web, mobile, bot, API...).

---

## 0. Nguyên tắc cốt lõi

1. **Spec trước, code sau** — Không viết code khi chưa rõ mình đang xây cái gì và tại sao.
2. **Từng bước nhỏ, kiểm tra liên tục** — Mỗi thay đổi phải nhỏ, chạy được, test được, rồi mới đi tiếp.
3. **Mọi thứ đều có version control** — Không có "code sống ngoài Git".
4. **Document song song với code, không làm sau cùng** — README/comment lỗi thời còn tệ hơn không có.
5. **Hiểu trước khi chấp nhận** — Không paste nguyên khối code AI sinh ra mà không hiểu nó làm gì.
6. **Fail an toàn, log rõ ràng** — Lỗi phải được bắt, ghi log, không âm thầm biến mất.
7. **Một nguồn sự thật (single source of truth)** — Config, secret, docs không bị trùng lặp/mâu thuẫn ở nhiều nơi.

---

## 1. Cấu trúc thư mục chuẩn

```
ten-du-an/
├── README.md                 # Giới thiệu, cài đặt, cách chạy
├── CHANGELOG.md               # Lịch sử thay đổi theo version
├── CLAUDE.md                  # Bối cảnh dự án cho Claude đọc (xem mục 8)
├── .env.example                # Mẫu biến môi trường (KHÔNG chứa giá trị thật)
├── .gitignore
├── LICENSE
├── docs/
│   ├── architecture.md         # Sơ đồ kiến trúc, luồng dữ liệu
│   ├── api.md                  # Danh sách API/command, tham số
│   └── decisions/               # ADR - Architecture Decision Records
├── src/                        # Mã nguồn chính
├── tests/                      # Unit test, integration test
├── scripts/                     # Script tiện ích (migrate, seed, deploy)
└── .github/workflows/           # CI/CD pipelines
```

---

## 2. Vòng đời dự án — 8 giai đoạn

### Giai đoạn 1 — Khởi tạo & Lập kế hoạch
- Viết **1 đoạn spec ngắn**: dự án làm gì, cho ai dùng, phạm vi MVP là gì, cái gì KHÔNG làm ở bản đầu.
- Chọn tech stack và **ghi lại lý do chọn** (1-2 dòng là đủ).
- Liệt kê rủi ro/điểm chưa chắc chắn cần hỏi Claude làm rõ trước khi code.
- **Output:** `docs/spec.md` hoặc phần "Mục tiêu" trong README.

### Giai đoạn 2 — Thiết kế
- Vẽ sơ đồ kiến trúc đơn giản (có thể nhờ Claude tạo diagram).
- Thiết kế data model / schema database trước khi viết code truy vấn.
- Với API/bot command: liệt kê input – output – lỗi có thể xảy ra cho từng chức năng.
- **Output:** `docs/architecture.md`.

### Giai đoạn 3 — Coding
- Mỗi lần chỉ làm **một tính năng/module nhỏ**, commit ngay khi chạy được.
- Tuân thủ convention đặt tên và format của ngôn ngữ đang dùng (xem bảng mục 4).
- Không tự ý thay đổi phần code không liên quan đến task đang làm.

### Giai đoạn 4 — Testing
- Viết ít nhất test cơ bản cho phần logic quan trọng (không cần 100% coverage với dự án cá nhân).
- Test thủ công theo checklist trước khi coi là xong (xem mục 6).

### Giai đoạn 5 — Documentation
- Cập nhật README, docstring/comment, CHANGELOG **ngay trong cùng commit** với code.
- Quyết định kỹ thuật quan trọng → ghi 1 ADR ngắn (xem mẫu mục 5).

### Giai đoạn 6 — Review & Debug
- Tự review lại diff trước khi merge (xem checklist mục 6).
- Theo quy trình debug 5 bước (mục 6).

### Giai đoạn 7 — Deploy
- Deploy qua pipeline tự động (CI/CD), không deploy tay khi đã có pipeline.
- Có kế hoạch rollback rõ ràng trước khi deploy tính năng lớn.

### Giai đoạn 8 — Vận hành & Update
- Theo dõi log/lỗi sau khi deploy.
- Cập nhật dependency định kỳ, kiểm tra breaking change trước khi update.
- Backup dữ liệu định kỳ (đặc biệt nếu dùng volume/DB như SQLite).

---

## 3. Quy tắc code & convention theo ngôn ngữ

| Ngôn ngữ | Style guide | Formatter | Linter | Test framework |
|---|---|---|---|---|
| Python | PEP 8 | `black` | `ruff` / `flake8` | `pytest` |
| JavaScript/TypeScript | Airbnb / Standard | `prettier` | `eslint` | `jest` / `vitest` |
| Go | Effective Go | `gofmt` | `golangci-lint` | `go test` |
| Java | Google Java Style | `google-java-format` | `checkstyle` | `JUnit` |

**Quy tắc chung mọi ngôn ngữ:**
- Tên biến/hàm rõ nghĩa, không viết tắt khó hiểu.
- Hàm nên làm **một việc**, không quá ~50 dòng nếu tránh được.
- Không hard-code secret/API key trong code — luôn dùng biến môi trường (`.env`).
- Bắt lỗi (try/except, try/catch) ở mọi điểm giao tiếp bên ngoài (API call, DB, file I/O).

---

## 4. Git workflow

**Branch naming:** `feature/ten-tinh-nang`, `fix/mo-ta-loi`, `docs/cap-nhat-readme`

**Commit message — theo chuẩn Conventional Commits:**

| Prefix | Ý nghĩa | Ví dụ |
|---|---|---|
| `feat:` | Thêm tính năng mới | `feat: thêm lệnh /thongke xuất biểu đồ tuần` |
| `fix:` | Sửa lỗi | `fix: sửa lỗi streak reset sai múi giờ` |
| `docs:` | Sửa tài liệu | `docs: cập nhật hướng dẫn cài đặt` |
| `refactor:` | Tái cấu trúc, không đổi hành vi | `refactor: tách logic nhắc nhở ra module riêng` |
| `test:` | Thêm/sửa test | `test: thêm test cho lệnh /dangky` |
| `chore:` | Việc vặt (update dependency...) | `chore: nâng cấp discord.py lên 2.4` |

**Trước khi merge vào `main`:**
- [ ] Code chạy được, không lỗi khi khởi động
- [ ] Đã test thủ công tính năng vừa thêm
- [ ] Không còn `print()`/`console.log()` debug thừa
- [ ] README/CHANGELOG đã cập nhật nếu cần

---

## 5. Documentation chuẩn

**README tối thiểu cần có:**
1. Mô tả dự án (1-2 câu)
2. Cách cài đặt (bước cụ thể, copy-paste chạy được)
3. Cách chạy/sử dụng
4. Biến môi trường cần thiết
5. Cấu trúc thư mục ngắn gọn

**Mẫu ADR (Architecture Decision Record) — 5 dòng là đủ:**
```
## Quyết định: Dùng SQLite thay vì PostgreSQL
Ngày: 2026-07-31
Lý do: Dự án nhỏ, deploy trên Railway với volume, không cần server DB riêng.
Đánh đổi: Khó scale multi-instance sau này, nhưng chấp nhận được ở quy mô hiện tại.
```

**Docstring/comment:** giải thích **tại sao**, không lặp lại **cái gì** mà code đã tự nói rõ.

---

## 6. Testing & quy trình Debug

**Testing pyramid (ưu tiên từ dưới lên):**
- Unit test (nhiều nhất) → test từng hàm logic riêng lẻ
- Integration test (vừa phải) → test luồng ghép nhiều thành phần (VD: lệnh bot → DB)
- Test thủ công (ít nhất, cho UI/UX)

**Checklist trước khi coi 1 tính năng là "xong":**
- [ ] Chạy thử case đúng (happy path)
- [ ] Chạy thử case lỗi (input sai, mất mạng, DB rỗng...)
- [ ] Kiểm tra log có rõ ràng, đủ thông tin để debug sau này không
- [ ] Không crash toàn bộ app khi 1 phần lỗi

**Quy trình debug 5 bước:**
1. **Tái hiện lỗi** — xác định bước chính xác gây lỗi
2. **Đọc log/traceback đầy đủ** — không đoán, đọc dòng lỗi cụ thể
3. **Cô lập nguyên nhân** — thu hẹp bằng cách tắt bớt phần code/print biến trung gian
4. **Sửa từng điểm một** — không sửa nhiều chỗ cùng lúc
5. **Verify lại** — chạy lại đúng bước ban đầu để chắc chắn đã hết lỗi, không tạo lỗi mới

---

## 7. CI/CD & Update tự động

- **CI cơ bản (GitHub Actions):** tự chạy lint + test mỗi khi push/PR, chặn merge nếu fail.
- **CD:** auto-deploy khi merge vào `main` (VD: Railway/Vercel/Render tự deploy từ GitHub).
- **Dependency update tự động:** bật Dependabot (GitHub) hoặc Renovate để tự tạo PR khi có bản cập nhật thư viện — luôn đọc changelog trước khi merge, tránh breaking change.
- **Versioning:** dùng Semantic Versioning `MAJOR.MINOR.PATCH` (VD: `1.2.0`), cập nhật `CHANGELOG.md` mỗi lần release.

Mẫu workflow tối giản:
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install & test
        run: |
          pip install -r requirements.txt
          pytest
```

---

## 8. Quy tắc riêng khi vibe code cùng Claude

- **Luôn giữ file `CLAUDE.md`** ở gốc dự án mô tả: dự án làm gì, stack đang dùng, quy ước đặt tên, các quyết định quan trọng — để mỗi phiên chat mới Claude nắm bối cảnh ngay, không phải giải thích lại từ đầu.
- **Yêu cầu giải thích trước khi áp dụng** với đoạn code lạ/phức tạp — hỏi "đoạn này làm gì, tại sao làm vậy" trước khi copy vào dự án.
- **Đưa từng phần nhỏ**, không yêu cầu "viết toàn bộ app" trong 1 lần — dễ kiểm soát, dễ debug khi có lỗi.
- **Commit/backup trước khi thử nghiệm lớn** — để luôn có điểm quay lại an toàn.
- **Không tin tuyệt đối output đầu tiên** — luôn tự chạy thử, đọc lại logic thay vì mặc định code AI sinh ra là đúng.
- **Ghi lại câu hỏi hay** — Nếu Claude giải thích một khái niệm hay (VD: async/await, ORM, webhook...), lưu lại vào ghi chú cá nhân để học dần, không chỉ để phục vụ 1 dự án.

---

## 9. Checklist tổng hợp — Definition of Done

Một tính năng/dự án được coi là hoàn thành khi:
- [ ] Code chạy đúng, đã test cả case đúng lẫn case lỗi
- [ ] Đã commit với message rõ ràng theo convention
- [ ] README/CHANGELOG/docstring đã cập nhật
- [ ] Không có secret/API key lộ trong code hoặc lịch sử Git
- [ ] Log đủ rõ để debug nếu có sự cố sau này
- [ ] Đã deploy (nếu cần) và kiểm tra chạy ổn trên môi trường thật

---

*Tài liệu này là khung áp dụng chung — có thể rút gọn tuỳ quy mô dự án. Với dự án cá nhân nhỏ, không cần làm đủ 100% mọi mục, nhưng nên giữ tối thiểu: spec ngắn, Git + commit convention, README, và quy trình debug 5 bước.*
