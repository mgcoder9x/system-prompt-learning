```yaml
eval_id: "similar_systems_landscape"
role: "prior_art_comparison"        # KHÁC fsrs.md (role=install_dependency); đây là đối chiếu tiền lệ/đối thủ
used_for: ["strategic_decision", "rebuild_vs_continue", "differentiation"]
method: "web_search_scan + 1 deep_fetch (vestige README lấy nguyên trang)"
honesty_caveat: >
  Trừ vestige (đã fetch nguyên README), các mục còn lại là SCAN BỀ MẶT theo mô tả repo/kết quả
  tìm kiếm — CHƯA audit mã nguồn từng cái. Đừng coi bảng năng lực là kết luận tuyệt đối; coi là
  bản đồ định hướng cần xác minh sâu khi ra quyết định lớn.
verified_at: 2026-07-09
verifier: "AI session (Kiro) — theo yêu cầu 'xem có repo nào tương tự'"
```

# Bản đồ hệ thống tương tự — đối chiếu tiền lệ (prior art)

> Mục đích: trả lời chính xác "có repo nào giống hệ này không" và cung cấp bằng chứng cho quyết
> định "đập đi xây lại hay không". Nguồn: web search 2026-07-09 + fetch README vestige.

## 0. Hệ của ta là gì (để so cho đúng trục)

Không phải "app FSRS". Là **substrate học-tập do-AI-vận-hành, lưu-trên-markdown**, gồm:
AI dạy Socratic • curriculum + blueprint có **cổng phủ bắt buộc** • **validator-là-chân-lý (Class A)**
• transaction (backup→validate→commit/rollback) • governance (change-request + nhật ký quyết định +
anti-drift) • **portable qua bất kỳ AI nào**. Khác biệt thật nằm ở **tầng toàn vẹn + governance**,
KHÔNG ở FSRS hay markdown-SR (những thứ này là commodity).

---

## 1. Tầng LỊCH ÔN (engine) — commodity, ta đã dùng lại đúng

```yaml
repo_id: "open-spaced-repetition / py-fsrs / fsrs4anki"
url: "https://github.com/open-spaced-repetition"
overlap: "Thuật toán FSRS-6 (21 weights) — đúng cái ta nhúng qua py-fsrs (xem fsrs.md)"
verdict: "KHÔNG rebuild. Đây là chuẩn ngành, dùng lại là đúng. Không phải nơi tạo khác biệt."
```

## 2. Tầng SR TRÊN MARKDOWN/PLAIN-TEXT — đông đúc, đã trưởng thành

```yaml
repos:
  - "eudoxia0/hashcards        (https://github.com/eudoxia0/hashcards)   # plain-text SR, CLI, 731 commits"
  - "Obsidian 'Decks'          (forum.obsidian.md, plugin)               # markdown thuần + FSRS + optimizer 21 weights client-side"
  - "st3v3nmw/obsidian-spaced-repetition                                 # FSRS/SM-2, ôn cả note lẫn flashcard"
  - "linanwx/aosr              (https://github.com/linanwx/aosr)"
  - "Syro (obsidian plugin)                                              # incremental reading + SR, UI hiện đại"
overlap: "Flashcard bằng markdown + lịch ôn FSRS; có UI ôn tập; local-first, git-friendly"
gap_vs_us: >
  Đây là 'THẺ để NGƯỜI tự ôn'. KHÔNG có AI dạy Socratic, KHÔNG có curriculum/blueprint bắt buộc,
  KHÔNG có validator-là-chân-lý/transaction. Chúng giải bài toán 'ôn để nhớ', không phải 'dạy để hiểu'.
verdict: "Tham khảo quy ước markdown-SR nếu muốn tương thích công cụ ngoài; KHÔNG cần tự viết lại phần ôn."
```

## 3. Tầng AI SINH HỌC LIỆU + SR — có sản phẩm người dùng

```yaml
repos:
  - "Il101/ExamAI              (https://github.com/Il101/ExamAI)         # Gemini 2.0 Flash + FSRS, FastAPI + Next.js (CÓ web app)"
  - "hivaze/adaptive_lang_study_bot                                      # Telegram, claude-agent-sdk, FSRS, nhắc học chủ động"
  - "Reqeique/SRS-AI-quiz-gen                                            # AI quiz -> flashcard SM-2"
  - "google/bespoke                                                      # SR cho học ngôn ngữ theo ngữ cảnh câu"
overlap: "AI tạo quiz/thẻ + lịch ôn; có UI/giao diện người dùng thật (web, Telegram)"
gap_vs_us: >
  Tập trung SINH NỘI DUNG + ÔN. KHÔNG có tầng toàn vẹn/transaction/governance, KHÔNG cam kết
  portability qua nhiều AI, KHÔNG có cổng-hiểu/blueprint coverage.
verdict: "Đây là hình mẫu 'lớp sản phẩm' (UI + backend) mà hệ ta đang THIẾU."
```

## 4. Tầng BỘ NHỚ AI-AGENT TRÊN FILE + PORTABLE — gần ta nhất về TINH THẦN

### 4a. vestige — ĐÃ FETCH SÂU (đối chiếu quan trọng nhất)

```yaml
repo_id: "samvallad33/vestige"
url: "https://github.com/samvallad33/vestige"
license: "AGPL-3.0"
traction: "579 stars, 58 forks, 28 releases, v2.2.1 (đang phát triển tích cực)"
size: "Rust 2024, ~86,000 dòng, 1 binary ~23MB, 1,550 test passing"
distribution: "MCP server (npm i -g vestige-mcp-server) — chạy với BẤT KỲ agent nào nói MCP"
clients_supported: "Cursor, VS Code (Copilot), Windsurf, Claude Code, Codex, Cline, Continue, Zed, Goose, JetBrains, Xcode"
storage: "SQLite + FTS5 + USearch HNSW (vector) + Nomic Embed v1.5; KHÔNG phải markdown thuần"
uses_fsrs: "CÓ — FSRS-6 (21 params) để 'quên' memory không dùng (decay), không phải để dạy"
ui: "Dashboard 3D (SvelteKit + Three.js), realtime WebSocket"
what_it_is: >
  BỘ NHỚ cho AI-agent: nhớ quyết định/kỹ thuật dự án giữa các phiên, truy hồi nguyên nhân gốc
  của lỗi (retroactive salience backfill), phát hiện MÂU THUẪN với điều đã lưu (claim_contradicts_memory).
overlap_with_us:
  - "Local-first, dữ liệu không rời máy, 'inspectable'"
  - "Dùng FSRS làm cơ chế quên/giữ"
  - "Portable qua NHIỀU AI (vestige làm điều này bằng MCP — bài học phân phối rất quan trọng)"
  - "Khái niệm 'phát hiện mâu thuẫn với trí nhớ' ~ tinh thần anti-drift/claim của ta"
gap_vs_us:
  - "vestige là MEMORY LAYER, KHÔNG phải hệ DẠY-HỌC: không curriculum, không blueprint, không cổng hiểu, không teaching rules"
  - "Nền lưu trữ = SQLite+vector, KHÔNG phải markdown-thuần-portable/human-diffable như ta"
  - "KHÔNG có mô hình 'validator-là-chân-lý (Class A)' + transaction all-or-nothing; nó dùng gating + test"
key_lessons_for_us:
  - "PHÂN PHỐI: 'portable qua mọi AI' NGÀY NAY ship dưới dạng MCP server + one-line install — KHÔNG phải 'mồi thủ công cho AI đọc START_HERE rồi chạy CLI'. Đây là bằng chứng trực tiếp giải đúng rủi ro kiến trúc gốc của ta (phụ thuộc AI có chịu chạy CLI)."
  - "CHUẨN THƯƠNG MẠI: 1 binary, cài 1 dòng, dashboard, 1550 test, 28 release — đây là 'bar' cho 'sản phẩm thương mại'."
  - "ĐỊNH VỊ: vestige đã chiếm ô 'bộ nhớ agent'. Ô 'DẠY-HỌC do-AI-vận-hành có cổng hiểu' vẫn TRỐNG — đó là chỗ khác biệt của ta."
verdict: "Không phải đối thủ trực tiếp (khác mục đích), nhưng là HÌNH MẪU cách productize + phân phối, và là bằng chứng thị trường cho 'portable AI cognition'."
```

### 4b. Nhóm bộ-nhớ-agent trên markdown (scan bề mặt)

```yaml
repos:
  - "zycaskevin/Vault-for-LLM   # markdown -> SQLite vault, sqlite-vec + ONNX, có migration + backup/restore verified"
  - "jzOcb/ai-agent-memory      # file-based, TTL tự động, nén bằng LLM, chia sẻ đa-agent"
  - "memweave (TDS article)     # markdown + SQLite, không cần vector DB"
  - "Nhiều gist 2026            # 'mọi state là file markdown đọc/ghi/prune được' — trùng triết lý file-based của ta"
overlap: "Triết lý 'state = file markdown, portable, human-readable'"
gap_vs_us: "Bộ nhớ, không phải dạy-học; đa số không có tầng toàn vẹn kiểu Class A."
```

### 4c. Nghiên cứu học thuật liên quan (CHƯA đọc được toàn văn — chỉ có abstract)

```yaml
paper: "A Protocol for Provenance-Verified Memory Transfer Across Heterogeneous LLM Agents"
url: "https://arxiv.org/abs/2605.11032"
status: "KHÔNG fetch được toàn văn (thử 2 lần, lỗi trích xuất). CHỈ có abstract từ search."
abstract_gist: >
  Nêu vấn đề trí nhớ agent bị khoá trong runtime của từng vendor -> mong manh, lock-in, mất kiến thức
  giữa các phiên; đề xuất protocol chuyển giao trí nhớ CÓ XÁC MINH NGUỒN GỐC (provenance) giữa các
  LLM khác loại.
relevance: >
  Trùng đúng luận đề 'portable + verifiable memory qua nhiều AI' của ta. Nếu đi hướng thương mại
  về portability/verifiability, NÊN đọc kỹ toàn văn (việc tương lai) để không phát minh lại protocol.
todo: "Fetch lại toàn văn khi cần; hiện KHÔNG được trích dẫn như đã đọc."
```

---

## 5. MA TRẬN NĂNG LỰC (× = có, — = không, ~ = một phần)

| Năng lực | Hệ của ta | markdown-SR (mục 2) | AI-tutor (mục 3) | vestige (4a) |
|---|:--:|:--:|:--:|:--:|
| Lịch ôn FSRS | × | × | × | × (để quên memory) |
| Lưu markdown thuần, human-diff | × | × | — | — (SQLite) |
| AI DẠY Socratic (hội thoại) | × | — | ~ | — |
| Curriculum + blueprint **cổng phủ bắt buộc** | × | — | — | — |
| **Validator-là-chân-lý (Class A)** + transaction | × | — | — | — |
| Governance: change-request + nhật ký + anti-drift | × | — | — | ~ (gating) |
| Portable qua nhiều AI | × (thủ công/CLI) | — | — | × (**MCP, tự động**) |
| Phát hiện mâu thuẫn/claim | ~ | — | — | × |
| **UI cho người dùng cuối** | — | × | × | × (dashboard) |
| **Phân phối 1-dòng / đóng gói** | — | × (plugin) | ~ | × (npm/binary) |
| Đảm bảo KHÔNG phụ thuộc "AI chịu chạy CLI" | — | n/a | × (là app) | × (là MCP tool) |

## 6. KẾT LUẬN (cho câu hỏi rebuild)

1. **Từng mảnh của ta đều đã có người làm tốt** (FSRS, markdown-SR, AI-tutor, agent-memory-portable).
2. **Tổ hợp của ta thì CHƯA ai phủ trọn** — đặc biệt "DẠY-HỌC do-AI-vận-hành + cổng hiểu + validator-là-chân-lý".
   Ô thị trường này còn trống; vestige ở ô kế bên (bộ nhớ) và đang có traction → thị trường "portable AI cognition" là thật.
3. **Khác biệt của ta = tầng toàn vẹn + governance**, KHÔNG phải FSRS/markdown. → Đừng rebuild phần đó; nó là moat.
4. **2 thứ ta THIẾU mà cả nhóm 3+4 đều có**: (a) lớp sản phẩm/UI, (b) phân phối không-phụ-thuộc-"AI-chịu-chạy-CLI".
   vestige chứng minh cách giải (b) = **MCP**. Đây là input thiết kế then chốt, không phải ý kiến.

→ Chi tiết quyết định: xem `../../../PRODUCT_THESIS.md` (thư mục gốc dự án).
