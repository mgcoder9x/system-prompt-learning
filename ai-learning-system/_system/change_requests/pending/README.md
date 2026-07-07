# change_requests/pending/

Change request **đang chờ duyệt** (spec §12 bước 1). Mỗi CR một file `cr-<id>-<slug>.md` theo mẫu ở
`approved/cr-0001-*.md`. AI (lệnh `/system` / intent `system_change`) chỉ được **ghi vào đây**, KHÔNG áp ngay.
Sau khi người dùng xác nhận (§12 bước 6–7): move sang `../approved/`, áp dụng, ghi `../changelog.md`.
