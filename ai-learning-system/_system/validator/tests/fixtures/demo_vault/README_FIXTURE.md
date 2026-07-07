# demo_vault — FIXTURE TEST (không phải vault người dùng)

Đây là **vault mẫu chỉ dùng cho test** (topic `docker` / lesson-001 "Container là gì"). Bộ test copy
thư mục này sang `tmp` rồi chạy review/done/forget/status/schedule/portability... trên nó.

**KHÔNG phải** dữ liệu học của người dùng. Vault ship cho người dùng là `../../../../../learning_vault/`
(ở gốc `ai-learning-system/`) và được giữ **RỖNG** (khởi đầu trắng — người dùng `/learn` để tạo topic).

Tách fixture khỏi vault ship theo DEC-054 (tránh nhầm "sao có sẵn bài mình chưa học" + hết coupling
test↔dữ-liệu-người-dùng). Nằm dưới `validator/` nên INV-18 (E-MIX-DATA) không quét (skip-dir).
