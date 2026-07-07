---
schema: topic_state
schema_version: 1
topic_id: <<TOPIC_ID>>
title: <<TOPIC_TITLE>>
current_lesson: null
has_draft_knowledge: false
lessons: []
created: <<CREATED>>
updated: <<CREATED>>
review_schedule:
  generated_from_hash: "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
  items: []
assessment:
  generated_from_hash: "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
  concept_avg: 0.0
  explain_avg: 0.0
  apply_avg: 0.0
  critique_avg: 0.0
  teachback_avg: 0.0
---

# Topic: <<TOPIC_TITLE>>

Topic mới, chưa có lesson. Hai view (`review_schedule`, `assessment`) đang ở trạng thái RỖNG với
`generated_from_hash` = hash canonical của danh sách rỗng (INV-09). Khi `/learn` thêm lesson/review item
đầu tiên, transaction-FULL sẽ **REGEN** hai view này bằng `views.py` — KHÔNG sửa hash bằng tay.
