# Requirements Document

## Introduction

Tính năng **Học theo giáo trình** (curriculum-driven learning) mở rộng hệ `ai-learning-system` từ mô hình "một topic chỉ có lesson-001" sang mô hình **một topic có một giáo trình nhiều bài, dạy-và-hỏi bám theo giáo trình, tự tiến qua từng bài khi người học đã qua cổng "đã hiểu"**.

Động lực: lệnh `/learn` hiện tại CHỈ tạo được lesson-001 cho một topic; không có cơ chế tạo lesson-002+ và không có cơ chế "giáo trình nhiều bài + tự tiến qua từng bài". Spec gốc đã hình dung một topic có nhiều lesson (ví dụ Docker 5 lesson) nhưng chưa được xây.

Tính năng bổ sung ba năng lực mới:
1. Một vùng đầu vào `reference/` để người dùng đặt tài liệu học; AI dựng giáo trình bám theo tài liệu đó nếu có, hoặc tự dựng từ nguồn đáng tin nếu rỗng.
2. Một artifact **giáo trình (curriculum)** trung tâm, có cấu trúc, nhiều điểm/nhiều bài; là chuẩn để sinh lesson và đánh giá; được kiểm rất chặt (sâu – rộng – chính xác) trước khi cho dạy.
3. Một vùng `exam/` để người dùng nộp bài thực hành (ví dụ code); AI kiểm tra/chấm — đây là đánh giá thực hành Class D, phân biệt rõ với cổng rubric `learned_gate` hiện có.

**Ranh giới bảo đảm xuyên suốt (theo triết lý hệ thống):**
- **Máy đảm bảo (Class A – validator là chân lý):** cấu trúc giáo trình đúng schema, index bài khớp lesson có thật trên đĩa (INV-25), tính toàn vẹn tham chiếu (INV-03), tiến độ nhảy bài chỉ xảy ra sau khi cổng "đã hiểu" đạt (INV-07), portable không đường dẫn tuyệt đối (INV-16), phân vùng code/dữ liệu (INV-17/18).
- **Người/AI đánh giá (Class B/C/D – audit được, KHÔNG phải chân lý):** chất lượng và độ chính xác nội dung giáo trình, mức độ "đủ sâu/đủ rộng" về mặt tri thức, và việc chấm bài thực hành trong `exam/`.

**Ràng buộc tương thích (không thương lượng):** Mọi lệnh mới, đổi registry lệnh, đổi schema, hay đổi spec PHẢI đi qua quy trình change-request §12 (không sửa nóng). Tài liệu này KHÔNG chốt tên lệnh; chỉ nêu năng lực cần có. Tên lệnh và đăng ký registry sẽ được quyết ở pha design/impl thông qua change-request.

## Glossary

- **AI_Learning_System**: Toàn hệ học tập do-AI-vận-hành hiện có (validator INV-01..26, Write Transaction, FSRS, driver CLI `session.py`, rubric 5 trục + cổng `learned_gate`).
- **Reference_Store**: Vùng đầu vào mới `reference/` nơi người dùng đặt tài liệu học gốc (đầu vào của AI, không phải dữ liệu học sinh ra). Vị trí đĩa và phân loại INV được quyết ở design (xem Requirement 2 và Requirement 11).
- **Curriculum** (giáo trình): Artifact trung tâm, có cấu trúc máy-đọc-được, mô tả một topic gồm nhiều **Curriculum_Point** (điểm cần học) và ánh xạ tới nhiều **Lesson**; là chuẩn để sinh lesson và đánh giá. Là dữ liệu học, thuộc `learning_vault/` (INV-18).
- **Curriculum_Point**: Một điểm/mục học trong Curriculum, có định danh ổn định, mục tiêu học, và trạng thái tiến độ.
- **Lesson**: Bài học dạy-và-hỏi hiện có (lesson.md + lesson_state.md), nay được sinh bám theo một hoặc nhiều Curriculum_Point.
- **Curriculum_Validator**: Bộ kiểm giáo trình (mở rộng của validator hiện có) kiểm cấu trúc, index, tham chiếu và tiêu chí "đạt" của Curriculum.
- **Learned_Gate**: Cổng "đã hiểu" hiện có — `status: learned` chỉ khi mọi trục rubric đạt ngưỡng và mỗi trục đạt ngưỡng có ≥1 evidence verbatim (INV-07/22/22b).
- **Exam_Store**: Vùng mới `exam/` nơi người dùng nộp bài thực hành (ví dụ code); AI kiểm tra/chấm. Đánh giá thực hành Class D.
- **Exam_Submission**: Một bài nộp trong Exam_Store gắn với một topic/curriculum/lesson.
- **Change_Request_Process**: Quy trình §12 (`_system/change_requests/`) để thêm/đổi lệnh, schema, spec — không sửa nóng.
- **Write_Transaction**: Cơ chế ghi an toàn hiện có (backup → validate → commit/rollback).

## Requirements

### Requirement 1: Vùng đầu vào tài liệu tham chiếu (Reference_Store)

**User Story:** Là người học, tôi muốn đặt tài liệu học của mình vào một vùng `reference/` cố định, để AI dựng giáo trình bám theo đúng tài liệu tôi cung cấp.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL cung cấp cho mỗi topic một vùng đầu vào Reference_Store để người dùng đặt tài liệu học gốc của topic đó.
2. WHEN người dùng khởi tạo dựng giáo trình cho một topic mà Reference_Store của topic đó chứa ít nhất một tài liệu tham chiếu hợp lệ (tài liệu đọc-được và có nội dung khác rỗng), THE AI_Learning_System SHALL dựng Curriculum bám theo nội dung các tài liệu tham chiếu hợp lệ trong Reference_Store của topic đó.
3. WHEN người dùng khởi tạo dựng giáo trình cho một topic mà Reference_Store của topic đó không chứa tài liệu tham chiếu hợp lệ nào, THE AI_Learning_System SHALL dựng Curriculum từ nguồn ngoài và SHALL ghi mỗi nguồn đã dùng thành một mục trong `sources.md` với `status: raw`.
4. WHERE Curriculum được dựng bám theo Reference_Store, THE AI_Learning_System SHALL ghi cho mỗi Curriculum_Point ít nhất một liên kết truy vết tới tài liệu tham chiếu hợp lệ đã dùng để dựng điểm đó.
5. IF người dùng yêu cầu dựng giáo trình cho một topic mà Reference_Store không chứa tài liệu tham chiếu hợp lệ nào và không có nguồn ngoài khả dụng, THEN THE AI_Learning_System SHALL trả về một thông báo lỗi cho biết thiếu nguồn đầu vào và SHALL không tạo Curriculum lẫn không ghi mục mới vào `sources.md`.
6. IF một tài liệu trong Reference_Store của topic không đọc được hoặc có nội dung rỗng, THEN THE AI_Learning_System SHALL bỏ qua tài liệu đó khi dựng Curriculum và SHALL phát một cảnh báo cho biết tài liệu đã bị bỏ qua.

### Requirement 2: Phân loại và phân vùng của Reference_Store (INV-17/18)

**User Story:** Là người bảo trì hệ thống, tôi muốn vị trí và phân loại của Reference_Store được nêu rõ, để không phá vỡ ranh giới code/dữ liệu của hệ (INV-17/18) và giữ hệ portable.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL đặt Reference_Store tại một vị trí xác định duy nhất, tham chiếu bằng đường dẫn tương đối so với thư mục gốc và không dùng đường dẫn tuyệt đối (giữ INV-16).
2. THE AI_Learning_System SHALL không đặt mã nguồn, dependency, hay repository bên trong `learning_vault/` (giữ INV-17).
3. THE AI_Learning_System SHALL không đặt dữ liệu học bên trong `_system/` (giữ INV-18).
4. WHERE Reference_Store chứa tài liệu tham chiếu, THE AI_Learning_System SHALL phân loại các tài liệu đó là dữ liệu học đầu vào (không phải mã nguồn), và tài liệu design SHALL nêu rõ tiêu chí phân loại và lý do thỏa INV-17.
5. IF một thao tác cố đặt mã nguồn/dependency vào vùng dữ liệu học vi phạm INV-17, THEN THE AI_Learning_System SHALL từ chối thao tác đó, giữ nguyên trạng thái (không ghi một phần), và phát tín hiệu lỗi cho biết loại vi phạm.
6. IF một thao tác cố đặt dữ liệu học vào `_system/` vi phạm INV-18, THEN THE AI_Learning_System SHALL từ chối thao tác đó và phát tín hiệu lỗi cho biết loại vi phạm.
7. THE AI_Learning_System SHALL đảm bảo mọi artifact tham chiếu Reference_Store chỉ dùng đường dẫn tương đối và kiểm chứng được là không chứa đường dẫn tuyệt đối (giữ INV-16).

### Requirement 3: Giáo trình là artifact có cấu trúc, nhiều điểm/nhiều bài

**User Story:** Là người học, tôi muốn giáo trình là một artifact trung tâm có cấu trúc rõ ràng, để mỗi bài học và mỗi đánh giá đều có chuẩn tham chiếu.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL biểu diễn Curriculum của một topic dưới dạng artifact máy-đọc-được có cấu trúc gồm danh sách các Curriculum_Point được sắp theo một thứ tự học xác định, trong đó mỗi Curriculum_Point chiếm đúng một vị trí thứ tự riêng biệt, không trùng vị trí và không bỏ trống vị trí.
2. THE AI_Learning_System SHALL gán cho mỗi Curriculum_Point một định danh duy nhất trong phạm vi Curriculum, và SHALL giữ định danh đó không đổi trong suốt vòng đời của Curriculum kể cả khi các Curriculum_Point khác được thêm, xóa hoặc sắp xếp lại.
3. THE AI_Learning_System SHALL ghi cho mỗi Curriculum_Point một mục tiêu học không rỗng (chứa ít nhất một ký tự không phải khoảng trắng).
4. THE AI_Learning_System SHALL ánh xạ mỗi Lesson tới một hoặc nhiều Curriculum_Point mà Lesson đó dạy, và mỗi Curriculum_Point được ánh xạ SHALL là một điểm tồn tại trong Curriculum (giữ toàn vẹn tham chiếu INV-03).
5. THE AI_Learning_System SHALL lưu Curriculum bên trong `learning_vault/` cùng topic tương ứng (dữ liệu học, giữ INV-18).
6. WHEN một Curriculum_Point được tạo, THE AI_Learning_System SHALL đặt trạng thái tiến độ của điểm đó nhận đúng một giá trị thuộc tập hợp lệ {"chưa bắt đầu", "đang học", "hoàn thành"} và khởi tạo trạng thái là "chưa bắt đầu".
7. IF một thao tác gán cho một Curriculum_Point một định danh trùng với định danh của một Curriculum_Point đã tồn tại trong cùng Curriculum, THEN THE AI_Learning_System SHALL từ chối thao tác đó, trả về thông báo lỗi mô tả rõ định danh bị trùng, và SHALL giữ nguyên Curriculum không thay đổi.

### Requirement 4: Năng lực dựng giáo trình và thu thập dữ liệu (lệnh mới qua change-request)

**User Story:** Là người học, tôi muốn có lệnh để dựng giáo trình và lệnh để thu thập dữ liệu đầu vào, để bắt đầu một topic học nhiều bài mà không phải thao tác thủ công.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL cung cấp một năng lực dựng Curriculum cho một topic từ Reference_Store hoặc từ nguồn ngoài.
2. THE AI_Learning_System SHALL cung cấp một năng lực thu thập dữ liệu đầu vào để nạp tài liệu vào Reference_Store hoặc ghi nguồn vào `sources.md`.
3. WHEN một lệnh mới hiện thực năng lực dựng giáo trình hoặc thu thập dữ liệu được thêm vào hệ, THE AI_Learning_System SHALL không cho lệnh đó có hiệu lực cho tới khi lệnh được đăng ký qua Change_Request_Process (§12) và change-request được duyệt (không sửa nóng).
4. WHEN một lệnh mới thực hiện ghi vào vault, THE AI_Learning_System SHALL thực hiện ghi đó qua Write_Transaction và SHALL chỉ commit khi validate PASS (ngược lại rollback).
5. IF một lệnh mới được gọi thiếu tham số bắt buộc hoặc không rõ ý định, THEN THE AI_Learning_System SHALL hỏi lại người dùng, SHALL không đoán ý định, và SHALL không ghi vào vault cho tới khi đủ thông tin.
6. IF một lệnh chưa được đăng ký/duyệt qua Change_Request_Process được gọi, THEN THE AI_Learning_System SHALL từ chối thực thi, báo lỗi, và không thay đổi vault.
7. IF một Write_Transaction của lệnh mới validate FAIL, THEN THE AI_Learning_System SHALL rollback về trạng thái trước ghi, SHALL không commit một phần, và SHALL báo lỗi.

### Requirement 5: Kiểm giáo trình chặt trước khi cho dạy (Curriculum_Validator)

**User Story:** Là người học, tôi muốn giáo trình được kiểm rất chặt về độ sâu, độ rộng và độ chính xác trước khi được dùng để dạy, để không học theo một giáo trình lỗi.

#### Acceptance Criteria

1. THE Curriculum_Validator SHALL trả về PASS khi và chỉ khi Curriculum có 0 vi phạm, và trả về FAIL kèm danh sách vi phạm khi có ≥1 vi phạm; mỗi vi phạm SHALL gắn một mã lỗi xác định và định danh Curriculum_Point liên quan (nếu có).
2. IF một Curriculum không đạt ít nhất một tiêu chí "đạt", THEN THE AI_Learning_System SHALL đánh dấu Curriculum đó là chưa-được-phép-dạy và SHALL không sinh Lesson mới từ Curriculum đó.
3. THE Curriculum_Validator SHALL xác minh mỗi Curriculum_Point có định danh duy nhất trong phạm vi Curriculum, có mục tiêu học không rỗng (ít nhất một ký tự không phải khoảng trắng), và có trạng thái tiến độ thuộc tập giá trị hợp lệ định nghĩa trong schema (kiểm chứng cấu trúc — Class A).
4. WHERE Curriculum được dựng bám theo Reference_Store, THE Curriculum_Validator SHALL xác minh mỗi liên kết truy vết từ Curriculum_Point tới tài liệu tham chiếu trỏ tới một tài liệu tồn tại trên đĩa.
5. THE AI_Learning_System SHALL xác định "đủ sâu" và "đủ rộng và chính xác về nội dung" của Curriculum là đánh giá Class B/C/D do người/AI thực hiện, và Curriculum_Validator SHALL không tự tuyên bố các thuộc tính nội dung đó là đã đảm bảo tuyệt đối.
6. IF một liên kết truy vết của Curriculum_Point trỏ tới một tài liệu tham chiếu không tồn tại trên đĩa, THEN THE Curriculum_Validator SHALL trả về FAIL kèm một mã lỗi tham chiếu gãy xác định.

### Requirement 6: Sinh nhiều lesson bám theo giáo trình

**User Story:** Là người học, tôi muốn mỗi bài học được sinh bám theo giáo trình, để nội dung dạy và chuẩn đánh giá đều nhất quán với giáo trình.

#### Acceptance Criteria

1. WHILE một Curriculum đã ở trạng thái được-phép-dạy (đã PASS Curriculum_Validator theo Requirement 5), THE AI_Learning_System SHALL cho phép sinh Lesson cho các Curriculum_Point của Curriculum đó.
2. WHEN sinh một Lesson cho một Curriculum_Point, THE AI_Learning_System SHALL đặt mục tiêu học và chuẩn đánh giá của Lesson bám theo Curriculum_Point tương ứng và ghi ánh xạ Lesson ↔ Curriculum_Point (giữ INV-03).
3. THE AI_Learning_System SHALL cho phép một topic có từ 2 Lesson trở lên với định danh tuần tự duy nhất theo dạng lesson-NNN.
4. WHEN sinh một Lesson mới, THE AI_Learning_System SHALL ghi Lesson qua Write_Transaction.
5. WHEN một Write_Transaction sinh Lesson commit thành công, THE AI_Learning_System SHALL cập nhật index lesson của topic khớp đúng tập Lesson thật trên đĩa (giữ INV-25).
6. IF một Write_Transaction sinh Lesson thất bại, THEN THE AI_Learning_System SHALL rollback, SHALL không để lại Lesson bộ phận, và SHALL giữ index lesson không đổi.
7. IF yêu cầu sinh Lesson trỏ tới một Curriculum_Point không tồn tại trong Curriculum, THEN THE AI_Learning_System SHALL trả về lỗi, SHALL không tạo Lesson, và SHALL giữ nguyên index/dữ liệu topic.
8. IF yêu cầu sinh Lesson nhắm tới một Curriculum chưa-được-phép-dạy, THEN THE AI_Learning_System SHALL từ chối sinh Lesson kèm chỉ báo lỗi.

### Requirement 7: Tự tiến qua bài kế khi đã qua cổng "đã hiểu"

**User Story:** Là người học, tôi muốn hệ tự chuyển sang bài kế sau khi tôi đã qua cổng "đã hiểu" của bài hiện tại, để mạch học liền lạc mà không phải tự điều hướng.

#### Acceptance Criteria

1. WHEN một Lesson đạt Learned_Gate (`status: learned` thoả đủ điều kiện INV-07/22/22b), THE AI_Learning_System SHALL đánh dấu mọi Curriculum_Point mà Lesson đó ánh xạ tới (theo Requirement 5) là hoàn thành và ghi thay đổi này qua Write_Transaction (backup → validate → commit/rollback).
2. WHEN một Curriculum_Point được đánh dấu hoàn thành và trong Curriculum còn ít nhất một Curriculum_Point chưa hoàn thành, THE AI_Learning_System SHALL đặt Curriculum_Point chưa hoàn thành đầu tiên theo thứ tự học làm điểm học hiện tại và cập nhật con trỏ tiến độ qua Write_Transaction, trong cùng một giao dịch với việc đánh dấu hoàn thành.
3. IF một Lesson chưa đạt Learned_Gate, THEN THE AI_Learning_System SHALL giữ nguyên con trỏ tiến độ hiện tại và SHALL không đặt Curriculum_Point kế làm điểm học hiện tại.
4. WHEN toàn bộ Curriculum_Point của một Curriculum đã ở trạng thái hoàn thành, THE AI_Learning_System SHALL đánh dấu Curriculum đó là đã hoàn tất qua Write_Transaction và SHALL giữ con trỏ tiến độ tại Curriculum_Point cuối cùng theo thứ tự học.
5. THE AI_Learning_System SHALL đảm bảo con trỏ tiến độ Curriculum luôn trỏ tới một Curriculum_Point tồn tại trong Curriculum (giữ toàn vẹn tham chiếu INV-03).
6. IF một giao dịch Write_Transaction cập nhật trạng thái hoàn thành hoặc con trỏ tiến độ không validate được, THEN THE AI_Learning_System SHALL rollback về trạng thái trước giao dịch, giữ nguyên con trỏ tiến độ và trạng thái các Curriculum_Point, và SHALL trả về một thông báo lỗi cho biết việc tự tiến qua bài kế đã thất bại.

### Requirement 8: Yêu cầu bổ sung giáo trình giữa chừng

**User Story:** Là người học, khi thấy giáo trình còn thiếu, tôi muốn yêu cầu bổ sung điểm học giữa chừng, để lấp khoảng trống mà không phải dựng lại từ đầu.

#### Acceptance Criteria

1. WHEN người học yêu cầu bổ sung một Curriculum_Point vào một vị trí xác định trong thứ tự học của một Curriculum đang học, THE AI_Learning_System SHALL chèn Curriculum_Point mới vào đúng vị trí đó qua Write_Transaction, giữ nguyên thứ tự và định danh của các Curriculum_Point hiện có.
2. WHEN một Curriculum_Point được bổ sung, THE Curriculum_Validator SHALL kiểm lại toàn bộ Curriculum theo tập tiêu chí "đạt" và trả về báo cáo PASS hoặc FAIL với danh sách vi phạm trước khi cho sinh Lesson từ điểm mới.
3. THE AI_Learning_System SHALL giữ nguyên trạng thái tiến độ của các Curriculum_Point đã hoàn thành và giữ nguyên con trỏ tiến độ Curriculum hiện tại khi bổ sung điểm mới.
4. WHEN một Curriculum_Point được bổ sung, THE AI_Learning_System SHALL gán cho điểm mới một định danh duy nhất, ổn định, không trùng với bất kỳ định danh nào hiện có trong Curriculum.
5. IF việc bổ sung Curriculum_Point không hoàn tất được qua Write_Transaction, THEN THE AI_Learning_System SHALL rollback Curriculum về trạng thái trước khi bổ sung và SHALL trả về một thông báo lỗi mô tả rõ việc bổ sung thất bại.
6. IF việc kiểm lại Curriculum sau khi bổ sung trả về FAIL, THEN THE AI_Learning_System SHALL đánh dấu Curriculum là chưa-được-phép-dạy và SHALL không sinh Lesson từ Curriculum_Point mới.
7. IF yêu cầu bổ sung chỉ định một vị trí không hợp lệ hoặc một định danh trùng với định danh hiện có trong Curriculum, THEN THE AI_Learning_System SHALL từ chối yêu cầu và SHALL không thay đổi Curriculum.

### Requirement 9: Vùng bài thực hành và chấm bài (Exam_Store)

**User Story:** Là người học, tôi muốn nộp bài thực hành (ví dụ code) vào một vùng `exam/` và được AI kiểm tra/chấm, để đánh giá năng lực áp dụng thực tế.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL cung cấp Exam_Store để người dùng nộp Exam_Submission, mỗi Exam_Submission có định danh duy nhất và tham chiếu đúng một topic hoặc một Curriculum_Point tồn tại.
2. WHEN người dùng yêu cầu chấm một Exam_Submission đang tồn tại, THE AI_Learning_System SHALL tạo đúng một bản ghi kết quả chấm gắn Exam_Submission với topic/Curriculum_Point tương ứng qua Write_Transaction.
3. THE AI_Learning_System SHALL xác định việc đánh giá chất lượng thực chất của Exam_Submission là đánh giá Class D do người/AI thực hiện, tách biệt với Learned_Gate của rubric hiện có, và SHALL không tự tuyên bố kết quả chấm là đảm bảo tuyệt đối.
4. THE AI_Learning_System SHALL kiểm chứng bằng máy (Class A) rằng mỗi bản ghi kết quả chấm trỏ tới một Exam_Submission tồn tại và một topic/Curriculum_Point tồn tại.
5. WHERE Exam_Store chứa mã nguồn do người học nộp, THE AI_Learning_System SHALL đảm bảo việc chứa mã nguồn đó không làm phép kiểm INV-17 trên `learning_vault/` chuyển từ PASS sang FAIL, và tài liệu design SHALL nêu rõ cách Exam_Store thỏa ranh giới INV-17.
6. IF một yêu cầu chấm trỏ tới một Exam_Submission hoặc topic/Curriculum_Point không tồn tại, THEN THE AI_Learning_System SHALL từ chối yêu cầu và SHALL không tạo bản ghi kết quả chấm.
7. IF một Write_Transaction tạo bản ghi kết quả chấm thất bại, THEN THE AI_Learning_System SHALL rollback và SHALL không để lại bản ghi bộ phận.

### Requirement 10: Tính kiểm-chứng-được của giáo trình và tiến độ nhảy bài

**User Story:** Là người bảo trì hệ thống, tôi muốn cấu trúc giáo trình và logic nhảy bài đều kiểm chứng được bằng validator/test, để giữ validator là chân lý và tránh trôi dạt.

#### Acceptance Criteria

1. THE Curriculum_Validator SHALL gán cho mỗi loại vi phạm cấu trúc Curriculum (định danh trùng, mục tiêu rỗng, tham chiếu gãy, index lệch) đúng một mã lỗi phân biệt và ổn định, trong đó hai loại vi phạm khác nhau không dùng chung một mã và cùng một loại vi phạm luôn cho cùng một mã.
2. THE AI_Learning_System SHALL đảm bảo mỗi mã lỗi Curriculum_Validator phát ra có ít nhất một test tất định FAIL khi và chỉ khi vi phạm tương ứng hiện diện, và test đó ở trạng thái FAIL trước khi phần kiểm tương ứng của validator được hiện thực (RED-first).
3. IF index lesson của topic không khớp tập Lesson thật trên đĩa (index trỏ tới lesson không tồn tại, hoặc lesson trên đĩa không được index), THEN THE Curriculum_Validator SHALL báo lỗi lệch index (giữ INV-25) và giữ nguyên trạng thái.
4. WHEN Learned_Gate của Lesson hiện tại đạt, THE AI_Learning_System SHALL cho phép tiến qua Curriculum_Point kế; và tính chất "chỉ tiến sau khi Learned_Gate đạt" SHALL kiểm chứng được bằng test tất định.
5. IF một Lesson chưa đạt Learned_Gate mà có yêu cầu tiến bài, THEN THE AI_Learning_System SHALL từ chối tiến bài, giữ nguyên Curriculum_Point hiện tại, và phát chỉ báo lỗi.
6. THE AI_Learning_System SHALL đảm bảo mọi kiểm giáo trình và tiến độ, với cùng một đầu vào, luôn cho cùng một tập mã lỗi và cùng một phán quyết đạt/không-đạt qua các lần chạy lặp lại, không phụ thuộc đồng hồ thật hay thứ tự duyệt file cụ thể (giữ tính tất định và portable).

### Requirement 11: Tuân thủ change-request và bảo toàn bất biến (§12, validator là chân lý)

**User Story:** Là người bảo trì hệ thống, tôi muốn mọi thay đổi do tính năng này mang lại đều đi qua change-request và không phá bất biến hiện có, để hệ giữ được kỷ luật và tính portable.

#### Acceptance Criteria

1. WHEN tính năng cần thêm/đổi lệnh, schema, hoặc spec, THE AI_Learning_System SHALL chỉ áp dụng thay đổi đó sau khi có change-request được duyệt qua Change_Request_Process (§12), và SHALL không sửa nóng registry/schema/spec.
2. THE AI_Learning_System SHALL giữ validator là nguồn chân lý duy nhất (Class A) quyết định pass/fail cho mọi thuộc tính máy-đảm-bảo của Curriculum, Lesson, index và tiến độ; khi có mâu thuẫn giữa artifact và validator, kết quả validator SHALL là phân xử cuối cùng.
3. THE AI_Learning_System SHALL giữ mọi artifact mới chỉ dùng đường dẫn tương đối và kiểm chứng được là không chứa đường dẫn tuyệt đối, có thể kiểm ở gốc bất kỳ (giữ INV-16, portable).
4. THE AI_Learning_System SHALL đảm bảo sau khi thêm tính năng, phép validate toàn repo vẫn PASS đối với INV-25 (index topic khớp lesson có thật), INV-17 (không code trong `learning_vault/`) và INV-18 (không dữ liệu học trong `_system/`).
5. WHEN một artifact mới (Curriculum, bản ghi kết quả chấm) được định nghĩa, THE AI_Learning_System SHALL đăng ký ràng-buộc-schema của artifact đó vào cùng cơ chế schema + drift-guard hiện có và được validator kiểm trong cùng một lần chạy.
6. IF một thay đổi lệnh/schema/spec được áp mà bỏ qua Change_Request_Process (§12), THEN THE AI_Learning_System SHALL coi đó là vi phạm kỷ luật, rollback thay đổi, và báo lỗi.
7. IF một artifact mới chứa đường dẫn tuyệt đối, THEN phép validate SHALL FAIL (giữ INV-16).
8. IF một artifact mới thiếu ràng-buộc-schema hoặc drift-guard tương ứng, THEN phép validate SHALL FAIL.
