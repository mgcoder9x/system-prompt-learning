# Requirements Document

## Introduction

Tính năng **Khung giáo trình bắt buộc** (mandatory-curriculum-framework) bổ sung một tầng **"khung sườn"** (blueprint) phía trên tính năng `curriculum-driven-learning` đã có. Khi người học yêu cầu học một chủ đề (ví dụ "học Docker"), hệ dựng một **Topic_Blueprint** — bản tuyên bố **các mảng kiến thức BẮT BUỘC phải dạy**, sắp theo lộ trình **zero → chuyên gia** (không cần chi tiết nội dung, chỉ cần khung + các mảng bắt buộc). Blueprint là **rào chắn (guardrail)**: mọi giáo trình (`curriculum.md`) và việc dạy sau đó PHẢI phủ đủ các mảng bắt buộc; thiếu mảng → máy chặn (không cho dạy).

**Động lực (nguyên văn ý người dùng):** Cần một cái **khung sườn** cố định để bất kỳ AI nào (giỏi hay dở) cũng phải bám theo khi dạy. Nếu "thả cửa", một AI kém sẽ dẫn học sai/bỏ sót mảng quan trọng. Có khung này thì: (1) AI nào cũng **mở đọc / kiểm tra được**; (2) AI **dạy bám khung**, không đi chệch; (3) AI giỏi hơn có thể **sửa/cải tiến khung** qua một quy trình có kiểm soát.

Quan hệ với tính năng sẵn có:
- `curriculum-driven-learning` (đã làm) cung cấp `curriculum.md` — danh sách điểm học có thứ tự + `teachable` gate + validator cấu trúc. Tính năng này **không thay thế** curriculum; nó thêm **Topic_Blueprint** làm **chuẩn bắt buộc mà curriculum phải phủ**.
- Điểm mới cốt lõi: hiện validator chỉ kiểm curriculum **đúng cấu trúc** (không trùng id, thứ tự liền, mục tiêu không rỗng). Nó **KHÔNG** kiểm "giáo trình có đủ các mảng bắt buộc zero→chuyên-gia" hay không. Tính năng này lấp đúng khoảng đó.

**Ranh giới bảo đảm (giữ nguyên triết lý hệ — không thương lượng):**
- **Máy đảm bảo (Class A — validator là chân lý):** blueprint tồn tại và đúng schema; curriculum **phủ đủ** mọi mảng bắt buộc đã khai báo (mỗi mảng bắt buộc được ánh xạ tới ≥1 điểm học); thứ tự/định danh mảng hợp lệ; tham chiếu nguyên vẹn (INV-03); portable không path tuyệt đối (INV-16); phân vùng code/dữ liệu (INV-17/18); chỉ cho dạy khi phủ đủ.
- **Người/AI đánh giá (Class D — máy KHÔNG tự nhận đảm bảo):** các mảng bắt buộc có **thật sự đủ để thành chuyên gia** không, nội dung mỗi mảng có **chính xác/đủ sâu** không. Máy chỉ ép **phủ đủ mảng đã khai báo**, KHÔNG tự bảo đảm "khung đúng tầm chuyên gia".

**Ràng buộc tương thích (không thương lượng):** Mọi lệnh mới / đổi registry / đổi schema / đổi spec PHẢI đi qua Change_Request_Process (§12) — không sửa nóng. Tài liệu này KHÔNG chốt tên lệnh; chỉ nêu năng lực. Mọi ghi vault qua Write_Transaction (backup → validate → commit/rollback). Mọi artifact mới có ràng-buộc-schema + drift-guard đồng nhất cơ chế hiện có.

## Glossary

- **AI_Learning_System**: Toàn hệ học tập do-AI-vận-hành hiện có.
- **Topic_Blueprint** (khung bắt buộc): Artifact MỚI, một-cho-mỗi-topic, máy-đọc-được, tuyên bố danh sách **Mandatory_Area** sắp theo lộ trình zero→chuyên-gia. Là dữ liệu học, thuộc `learning_vault/` (INV-18).
- **Mandatory_Area** (mảng bắt buộc): Một mảng kiến thức phải-được-dạy trong topic, có định danh ổn định, tiêu đề/mục tiêu không rỗng, vị trí thứ tự trong lộ trình, và cờ bắt buộc.
- **Blueprint_Status**: Trạng thái vòng đời của Topic_Blueprint thuộc tập {"draft" (nháp, được phép sửa), "approved" (đã duyệt, là chuẩn ràng buộc)}.
- **Curriculum**: Giáo trình đã có (`curriculum.md`) gồm các Curriculum_Point — nay phải **phủ đủ** các Mandatory_Area của Topic_Blueprint.
- **Coverage_Map** (ánh xạ phủ): Quan hệ mỗi Mandatory_Area được phủ bởi ≥1 Curriculum_Point.
- **Blueprint_Validator**: Phần mở rộng của validator hiện có, kiểm blueprint + kiểm curriculum phủ đủ blueprint (Class A).
- **Curriculum_Validator**: Bộ kiểm curriculum đã có (E-CURR-*).
- **Change_Request_Process**: Quy trình §12 (`_system/change_requests/`).
- **Write_Transaction**: Cơ chế ghi an toàn hiện có.

## Requirements

### Requirement 1: Topic_Blueprint là artifact khung bắt buộc, có cấu trúc, inspectable

**User Story:** Là người học, tôi muốn mỗi chủ đề có một khung bắt buộc rõ ràng liệt kê các mảng phải học từ zero đến chuyên gia, để tôi và bất kỳ AI nào cũng mở ra kiểm tra được.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL biểu diễn Topic_Blueprint của một topic dưới dạng artifact máy-đọc-được, mở-đọc-được dạng văn bản, gồm một danh sách Mandatory_Area được sắp theo một thứ tự lộ trình xác định, trong đó mỗi Mandatory_Area chiếm đúng một vị trí thứ tự riêng biệt, không trùng và không bỏ trống vị trí.
2. THE AI_Learning_System SHALL gán cho mỗi Mandatory_Area một định danh duy nhất trong phạm vi Topic_Blueprint và SHALL giữ định danh đó không đổi trong suốt vòng đời blueprint kể cả khi các Mandatory_Area khác được thêm, xóa hoặc sắp xếp lại.
3. THE AI_Learning_System SHALL ghi cho mỗi Mandatory_Area một tiêu đề học không rỗng (chứa ít nhất một ký tự không phải khoảng trắng) và một cờ bắt buộc cho biết mảng đó là bắt-buộc hay tùy-chọn.
4. THE AI_Learning_System SHALL lưu Topic_Blueprint bên trong `learning_vault/` cùng topic tương ứng (dữ liệu học, giữ INV-18) và SHALL đảm bảo artifact chỉ dùng đường dẫn tương đối, kiểm chứng được là không chứa đường dẫn tuyệt đối (giữ INV-16).
5. WHEN một Topic_Blueprint được tạo, THE AI_Learning_System SHALL khởi tạo Blueprint_Status là "draft".
6. IF một thao tác gán cho một Mandatory_Area một định danh trùng với định danh của một Mandatory_Area đã tồn tại trong cùng blueprint, THEN THE AI_Learning_System SHALL từ chối thao tác đó, báo lỗi mô tả rõ định danh trùng, và giữ nguyên blueprint không thay đổi.

### Requirement 2: Dựng khung bắt buộc khi bắt đầu một chủ đề

**User Story:** Là người học, khi tôi nói "học Docker", tôi muốn hệ dựng sẵn một khung bắt buộc zero→chuyên-gia, để việc học có lộ trình đầy đủ ngay từ đầu.

#### Acceptance Criteria

1. THE AI_Learning_System SHALL cung cấp một năng lực dựng Topic_Blueprint cho một topic, sinh một danh sách Mandatory_Area sắp theo lộ trình từ nền tảng đến nâng cao.
2. WHEN dựng Topic_Blueprint bám theo tài liệu tham chiếu (Reference_Store) hoặc nguồn ngoài, THE AI_Learning_System SHALL ghi cho mỗi Mandatory_Area ít nhất một liên kết truy vết tới nguồn/tài liệu đã dùng để dựng mảng đó.
3. WHEN dựng Topic_Blueprint, THE AI_Learning_System SHALL ghi blueprint qua Write_Transaction và SHALL chỉ commit khi validate PASS (ngược lại rollback, không để lại blueprint bộ phận).
4. IF đã tồn tại một Topic_Blueprint cho topic, THEN THE AI_Learning_System SHALL không ghi đè âm thầm mà SHALL từ chối lệnh dựng-mới kèm chỉ báo đã tồn tại (việc sửa đi qua Requirement 5).
5. IF năng lực dựng blueprint được gọi thiếu tham số bắt buộc hoặc không rõ ý định, THEN THE AI_Learning_System SHALL hỏi lại người dùng, không đoán ý định, và không ghi vault cho tới khi đủ thông tin.

### Requirement 3: Giáo trình phải phủ đủ mọi mảng bắt buộc (ép được — Class A)

**User Story:** Là người học, tôi muốn giáo trình chỉ được phép dạy khi đã phủ đủ mọi mảng bắt buộc của khung, để không bị bỏ sót phần quan trọng.

#### Acceptance Criteria

1. THE Blueprint_Validator SHALL xác minh mỗi Mandatory_Area có cờ bắt-buộc được ánh xạ bởi ít nhất một Curriculum_Point của Curriculum cùng topic (Coverage_Map đầy đủ).
2. IF một Mandatory_Area bắt-buộc không được ánh xạ bởi Curriculum_Point nào, THEN THE Blueprint_Validator SHALL trả về FAIL kèm một mã lỗi "mảng bắt buộc chưa được phủ" xác định và định danh Mandatory_Area liên quan.
3. WHILE tồn tại ít nhất một Mandatory_Area bắt-buộc chưa được phủ, THE AI_Learning_System SHALL giữ Curriculum ở trạng thái chưa-được-phép-dạy và SHALL không sinh Lesson mới từ Curriculum đó.
4. THE AI_Learning_System SHALL chỉ đặt Curriculum sang trạng thái được-phép-dạy khi đồng thời Curriculum_Validator PASS (cấu trúc curriculum) VÀ Blueprint_Validator PASS (phủ đủ mảng bắt buộc).
5. WHERE một Curriculum_Point ánh xạ tới một Mandatory_Area, THE Blueprint_Validator SHALL xác minh Mandatory_Area được ánh xạ là một mảng tồn tại trong Topic_Blueprint của topic (giữ toàn vẹn tham chiếu INV-03).
6. IF một Curriculum_Point ánh xạ tới một Mandatory_Area không tồn tại trong Topic_Blueprint, THEN THE Blueprint_Validator SHALL trả về FAIL kèm một mã lỗi tham chiếu-mảng-gãy xác định.
7. THE AI_Learning_System SHALL xác định việc "các mảng bắt buộc có đủ để đạt tầm chuyên gia hay không" và "nội dung mỗi mảng có chính xác/đủ sâu hay không" là đánh giá Class D do người/AI thực hiện, và Blueprint_Validator SHALL không tự tuyên bố các thuộc tính nội dung đó là đã đảm bảo.

### Requirement 4: Vòng đời duyệt khung — cho AI giỏi hơn sửa, khóa lại khi đã duyệt

**User Story:** Là người bảo trì việc học, tôi muốn khung nháp có thể được sửa/cải tiến, nhưng khi đã duyệt thì thành chuẩn ràng buộc không sửa tùy tiện, để một AI kém về sau không phá khung.

#### Acceptance Criteria

1. WHILE Blueprint_Status là "draft", THE AI_Learning_System SHALL cho phép sửa danh sách Mandatory_Area (thêm/xóa/sửa/sắp xếp lại) qua Write_Transaction.
2. THE AI_Learning_System SHALL cung cấp một năng lực chuyển Blueprint_Status từ "draft" sang "approved", và SHALL chỉ chuyển được khi Blueprint_Validator kiểm blueprint PASS.
3. WHILE Blueprint_Status là "approved", THE AI_Learning_System SHALL từ chối mọi thao tác sửa nội dung Mandatory_Area của blueprint đó trừ khi thao tác đi qua một bước sửa-có-kiểm-soát tường minh (yêu cầu xác nhận), và SHALL giữ nguyên blueprint nếu thao tác không đi qua bước đó.
4. WHEN một blueprint "approved" được sửa qua bước sửa-có-kiểm-soát, THE AI_Learning_System SHALL ghi thay đổi qua Write_Transaction, chạy lại Blueprint_Validator, và SHALL rollback nếu validate FAIL.
5. THE AI_Learning_System SHALL đảm bảo mọi thay đổi Blueprint_Status và mọi sửa đổi blueprint đều để lại vết kiểm-chứng-được (transaction log) — không đổi âm thầm.
6. IF một thao tác cố chuyển Blueprint_Status sang "approved" trong khi Blueprint_Validator FAIL, THEN THE AI_Learning_System SHALL từ chối chuyển trạng thái và giữ Blueprint_Status là "draft".

### Requirement 5: Ràng việc dạy bám khung — không đi chệch

**User Story:** Là người học, tôi muốn AI chỉ dạy theo các mảng trong khung, để việc dạy không lan man hay bỏ sót.

#### Acceptance Criteria

1. WHEN sinh một Lesson cho một Curriculum_Point, THE AI_Learning_System SHALL yêu cầu Curriculum_Point đó ánh xạ tới một Mandatory_Area tồn tại trong Topic_Blueprint đã "approved" của topic (nếu topic có blueprint approved).
2. IF một topic đã có Topic_Blueprint "approved" và một Curriculum_Point không ánh xạ tới bất kỳ Mandatory_Area nào, THEN THE Blueprint_Validator SHALL trả về FAIL kèm mã lỗi điểm-học-ngoài-khung xác định.
3. THE AI_Learning_System SHALL cho phép một Mandatory_Area được phủ bởi nhiều Curriculum_Point và một Curriculum_Point phủ nhiều Mandatory_Area, miễn là mọi ánh xạ đều trỏ tới Mandatory_Area tồn tại.
4. WHERE topic chưa có Topic_Blueprint (hoặc blueprint còn "draft"), THE AI_Learning_System SHALL giữ nguyên hành vi hiện có của curriculum-driven-learning (không bắt buộc ánh xạ khung), để tương thích ngược.

### Requirement 6: Tính kiểm-chứng-được và tất định (validator là chân lý)

**User Story:** Là người bảo trì hệ thống, tôi muốn khung và việc kiểm phủ đều kiểm chứng được bằng validator/test và tất định, để giữ validator là chân lý và tránh trôi dạt.

#### Acceptance Criteria

1. THE Blueprint_Validator SHALL gán cho mỗi loại vi phạm (định danh mảng trùng, tiêu đề rỗng, thứ tự sai, mảng bắt buộc chưa phủ, tham chiếu-mảng-gãy, điểm-học-ngoài-khung, con trỏ/trạng thái sai) đúng một mã lỗi phân biệt và ổn định, trong đó hai loại vi phạm khác nhau không dùng chung một mã và cùng một loại vi phạm luôn cho cùng một mã.
2. THE AI_Learning_System SHALL đảm bảo mỗi mã lỗi Blueprint_Validator phát ra có ít nhất một test tất định FAIL khi và chỉ khi vi phạm tương ứng hiện diện, và test đó ở trạng thái FAIL trước khi phần kiểm tương ứng được hiện thực (RED-first).
3. THE Blueprint_Validator SHALL trả về PASS khi và chỉ khi blueprint (và quan hệ phủ với curriculum) có 0 vi phạm, và trả về FAIL kèm danh sách vi phạm khi có ≥1 vi phạm.
4. THE AI_Learning_System SHALL đảm bảo mọi kiểm blueprint/phủ, với cùng một đầu vào, luôn cho cùng một tập mã lỗi và cùng một phán quyết đạt/không-đạt qua các lần chạy lặp lại, không phụ thuộc đồng hồ thật hay thứ tự duyệt file cụ thể (giữ tính tất định và portable).
5. WHEN Topic_Blueprint được định nghĩa như một artifact mới, THE AI_Learning_System SHALL đăng ký ràng-buộc-schema của nó vào cùng cơ chế schema + drift-guard hiện có và được validator kiểm trong cùng một lần chạy.

### Requirement 7: Tuân thủ change-request và bảo toàn bất biến nền (§12)

**User Story:** Là người bảo trì hệ thống, tôi muốn mọi thay đổi do tính năng này đều đi qua change-request và không phá bất biến hiện có, để hệ giữ kỷ luật và tính portable.

#### Acceptance Criteria

1. WHEN tính năng cần thêm/đổi lệnh, schema hoặc spec, THE AI_Learning_System SHALL chỉ áp dụng thay đổi sau khi có change-request được duyệt qua Change_Request_Process (§12), và SHALL không sửa nóng registry/schema/spec.
2. THE AI_Learning_System SHALL giữ validator là nguồn chân lý duy nhất (Class A) quyết định pass/fail cho mọi thuộc tính máy-đảm-bảo của Topic_Blueprint và quan hệ phủ; khi có mâu thuẫn giữa artifact và validator, kết quả validator SHALL là phân xử cuối cùng.
3. THE AI_Learning_System SHALL đảm bảo sau khi thêm tính năng, phép validate toàn repo vẫn PASS đối với INV-16 (portable), INV-17 (không code trong `learning_vault/`), INV-18 (không dữ liệu học trong `_system/`) và INV-25 (index topic khớp lesson thật).
4. IF một artifact blueprint mới chứa đường dẫn tuyệt đối, THEN phép validate SHALL FAIL (giữ INV-16).
5. IF một artifact blueprint mới thiếu ràng-buộc-schema hoặc drift-guard tương ứng, THEN phép validate SHALL FAIL.
6. IF một thay đổi lệnh/schema/spec được áp mà bỏ qua Change_Request_Process (§12), THEN THE AI_Learning_System SHALL coi đó là vi phạm kỷ luật, rollback thay đổi, và báo lỗi.
