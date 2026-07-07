---
schema: lesson_state
schema_version: 1
lesson_id: <<LESSON_ID>>
title: <<LESSON_TITLE>>
status: not_started
created: <<CREATED>>
updated: <<CREATED>>
objective: <<OBJECTIVE>>
prerequisites: []
sections_done: []
sections_pending: []
mastery:
  concept: {score: 0, evidence: []}
  explain: {score: 0, evidence: []}
  apply: {score: 0, evidence: []}
  critique: {score: 0, evidence: []}
  teachback: {score: 0, evidence: []}
open_gaps: []
review_items: []
next_action: ""
last_session: null
---

# Trạng thái lesson (máy-kiểm)

Lesson mới: `status: not_started`, chưa có `review_items`, mastery 5 trục = 0. Khi dạy/ôn, transaction
cập nhật `review_items`/`mastery`/`status` (qua cổng learned_gate, INV-07). `updated ≥ created` (INV-05).
