# Sprint 1 API Test Cases

Generated from live executions against the real Flask app (in-memory SQLite, no network calls) using the same fixtures/helpers as `backend/tests/` (pytest suite, 164/164 passing -- see `backend/test_output.txt`). Every "Actual output" value below was captured from a genuine HTTP response produced during this run, not written by hand.

**Total cases: 194**

Rows 196-202 below are a separate live run: real photos (`backend/tests/fixtures/`), the real DeepFace/OpenCV pipeline (VGG-Face, 4096-d embeddings, cosine similarity), and the real Flask routes -- nothing about face detection/embedding/matching is mocked (only Supabase Storage is faked, same substitution the rest of this suite uses). Script: `backend/tests/manual_facial_recognition_check.py`.

| API being tested | Inputs | Expected output | Actual output | Result |
|---|---|---|---|---|
| POST /api/auth/login | {"email": "loginok@test.com", "password": "Password123"} | 200; body = {"id", "full_name", "email", "role": "admin", "phone"}; sets access_token_cookie, csrf_access_token, refresh_token_cookie, csrf_refresh_token | 200; body={'email': 'loginok@test.com', 'full_name': 'Test Admin', 'id': 1, 'phone': None, 'role': 'admin'}; cookies_set=['access_token_cookie', 'csrf_access_token', 'refresh_token_cookie', 'csrf_refresh_token'] | Success |
| POST /api/auth/login | {"email": "loginok@test.com", "password": "wrong-password"} | 401; error="invalid_credentials" | 401; {'error': 'invalid_credentials', 'message': 'Invalid email or password'} | Success |
| POST /api/auth/login | {"email": "nobody@test.com", "password": "Password123"} | 401; error="invalid_credentials" (same error as wrong password -- doesn't leak whether the email exists) | 401; {'error': 'invalid_credentials', 'message': 'Invalid email or password'} | Success |
| POST /api/auth/login | {"email": "not-an-email", "password": "Password123"} | 400; error="validation_error"; message.email present | 400; {'error': 'validation_error', 'message': {'email': ['Not a valid email address.']}} | Success |
| POST /api/auth/login | {"email": "someone@test.com"}  (password omitted) | 400; error="validation_error"; message.password present | 400; {'error': 'validation_error', 'message': {'password': ['Missing data for required field.']}} | Success |
| POST /api/auth/login | 5 consecutive requests with wrong password, same client, within 60s | 401 invalid_credentials on each of the 5 attempts (under the 5/min limit) | status codes = [401, 401, 401, 401, 401] | Success |
| POST /api/auth/login | 6th request within the same 60s window, same client | 429; error="rate_limited" | 429; {'error': 'rate_limited', 'message': '5 per 1 minute'} | Success |
| GET /api/auth/me | valid session cookie | 200; role=admin | 200; {'email': 'logout@test.com', 'full_name': 'Test Admin', 'id': 1, 'phone': None, 'role': 'admin'} | Success |
| POST /api/auth/logout | (none, valid session) | 200; body.message present | 200; {'message': 'Logged out'} | Success |
| GET /api/auth/me | same client, after logout | 401; error="authentication_required" | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| POST /api/auth/logout | no session at all | 200 (always succeeds, no auth required) | 200; {'message': 'Logged out'} | Success |
| GET /api/auth/me | no session cookie | 401; error="authentication_required" | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| POST /api/auth/refresh | no refresh cookie | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "refresh_token_cookie"'} | Success |
| POST /api/auth/refresh | valid refresh_token_cookie + matching X-CSRF-TOKEN (from csrf_refresh_token) | 200; sets a new access_token_cookie | 200; {'message': 'Access token refreshed'}; new access cookie set=True | Success |
| GET /api/auth/me | using the refreshed access cookie | 200 | 200; {'email': 'refresh@test.com', 'full_name': 'Test Admin', 'id': 1, 'phone': None, 'role': 'admin'} | Success |
| POST /api/auth/refresh | valid refresh_token_cookie, but X-CSRF-TOKEN taken from an access-token's csrf_access_token value | 401 (refresh CSRF must be bound to the refresh token's own csrf claim, not the access token's) | 401; {'error': 'authentication_required', 'message': 'CSRF double submit tokens do not match'} | Success |
| POST /api/auth/signup | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| POST /api/auth/signup | logged in as a teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/auth/signup | {"role": "teacher", "full_name": "New Teacher", "email": "newteacher@test.com", "password": "Password123"} | 201; body.role="teacher" | 201; {'email': 'newteacher@test.com', 'full_name': 'New Teacher', 'id': 3, 'phone': None, 'role': 'teacher'} | Success |
| POST /api/auth/signup | {"role": "parent", "full_name": "New Parent", "email": "newparent@test.com", "password": "Password123", "occupation": "Engineer"} | 201; body.role="parent" | 201; {'email': 'newparent@test.com', 'full_name': 'New Parent', 'id': 4, 'phone': None, 'role': 'parent'} | Success |
| POST /api/auth/signup | {"role": "student", ..., "admission_no": "ADM-1001"} | 201; body.role="student" | 201; {'email': 'newstudent@test.com', 'full_name': 'New Student', 'id': 5, 'phone': None, 'role': 'student'} | Success |
| POST /api/auth/signup | {"role": "student", "full_name": "No Admission", "email": "noadm@test.com", "password": "Password123"}  (admission_no omitted) | 400; error="validation_error"; message.admission_no present | 400; {'error': 'validation_error', 'message': {'admission_no': ['admission_no is required for student accounts']}} | Success |
| POST /api/auth/signup | {"role": "admin", ...}  (admin accounts can't be created via this endpoint) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'role': ['Must be one of: teacher, parent, student.']}} | Success |
| POST /api/auth/signup | {"role": "teacher", ..., "password": "abc"} | 400; error="validation_error"; message.password present | 400; {'error': 'validation_error', 'message': {'password': ['Shorter than minimum length 6.']}} | Success |
| POST /api/auth/signup | {"role": "teacher"}  (full_name/email/password omitted) | 400; message has full_name, email, password | 400; {'error': 'validation_error', 'message': {'email': ['Missing data for required field.'], 'full_name': ['Missing data for required field.'], 'password': ['Missing data for required field.']}} | Success |
| POST /api/auth/signup | email "dupe@test.com" already registered to another account | 409; error="email_taken" | 409; {'error': 'email_taken', 'message': 'An account with this email already exists'} | Success |
| GET /api/students | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/students | logged in as student (role not permitted on this route at all) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| GET /api/students | logged in as admin, 2 students exist | 200; total=2 | 200; total=2 | Success |
| GET /api/students | response shape check | body keys = {"items","page","per_page","total","pages"} | keys=['items', 'page', 'pages', 'per_page', 'total'] | Success |
| GET /api/students | logged in as teacher assigned only to class grade=1 (2 students exist total, 1 in their class) | 200; items = [student 1] only | 200; ids=[1] | Success |
| GET /api/students | logged in as a teacher with zero class assignments | 200; items=[] | 200; items=[] | Success |
| GET /api/students | logged in as parent with 1 of 2 total students as their child | 200; items = [student 1] only | 200; ids=[1] | Success |
| GET /api/students?class_id={id} | class_id=1 (2 students exist, 1 in this class) | 200; items=[student 1] | 200; ids=[1] | Success |
| GET /api/students?grade={n} | grade=5 | 200; items=[student 3] | 200; ids=[3] | Success |
| GET /api/students?class_id={bad} | class_id=not-a-number | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'class_id': ['class_id must be an integer']}} | Success |
| GET /api/students/{id} | id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Student not found'} | Success |
| GET /api/students/{id} | logged in as an unrelated parent, requesting another parent's child | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'You do not have access to this resource'} | Success |
| GET /api/students/{id} | id=2, logged in as admin | 200; full_name="Detail Student", has_face_embedding=false, status="active" | 200; {'full_name': 'Detail Student', 'has_face_embedding': False, 'status': 'active'} | Success |
| POST /api/students | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/students | {"full_name": "Brand New Student", "email": "bns@test.com", "password": "Password123", "admission_no": "ADM-500", "class_id": <grade 6 class>} | 201; admission_no="ADM-500", grade=6, status="active" | 201; {'admission_no': 'ADM-500', 'grade': 6, 'status': 'active'} | Success |
| POST /api/students | admission_no omitted | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'admission_no': ['admission_no is required for student accounts']}} | Success |
| POST /api/students | email "taken@test.com" already in use | 409; error="email_taken" | 409; {'error': 'email_taken', 'message': 'An account with this email already exists'} | Success |
| POST /api/students | admission_no "DUPADM" already in use by another student | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'A record with conflicting unique fields already exists'} | Success |
| PATCH /api/students/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| PATCH /api/students/{id} | {"status": "inactive", "gender": "female"} | 200; status="inactive", gender="female" | 200; {'status': 'inactive', 'gender': 'female'} | Success |
| PATCH /api/students/{id} | {"status": "graduated"}  (not one of active/inactive/withdrawn) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'status': ['Must be one of: active, inactive, withdrawn.']}} | Success |
| PATCH /api/students/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Student not found'} | Success |
| PATCH /api/students/{id} | admission_no changed to "EXIST-1" which another student already has | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'A record with conflicting unique fields already exists (e.g. admission_no)'} | Success |
| DELETE /api/students/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/students/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Student not found'} | Success |
| GET /api/teachers | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/teachers | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| GET /api/teachers | 2 teachers exist | 200; total=2, names=[Alice Teach, Bob Teach] | 200; total=2, names=['Alice Teach', 'Bob Teach'] | Success |
| GET /api/teachers/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Teacher not found'} | Success |
| GET /api/teachers/{id} | id=3 | 200; full_name="Detail Teacher", assigned_class_ids=[] | 200; {'full_name': 'Detail Teacher', 'assigned_class_ids': []} | Success |
| POST /api/teachers | logged in as parent (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/teachers | {"full_name": "New Teacher", "email": "newteach@test.com", "password": "Password123", "phone": "12345"} | 201; full_name="New Teacher", phone="12345", assigned_class_ids=[] | 201; {'full_name': 'New Teacher', 'phone': '12345', 'assigned_class_ids': []} | Success |
| POST /api/teachers | {"email": "onlyemail@test.com"}  (full_name/password omitted) | 400; message has full_name and password | 400; {'error': 'validation_error', 'message': {'full_name': ['Missing data for required field.'], 'password': ['Missing data for required field.']}} | Success |
| POST /api/teachers | email "dupteach@test.com" already in use | 409; error="email_taken" | 409; {'error': 'email_taken', 'message': 'An account with this email already exists'} | Success |
| PATCH /api/teachers/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| PATCH /api/teachers/{id} | {} (empty body -- teachers table has no editable fields) | 200; full_name unchanged ("No Op Teacher") | 200; full_name=No Op Teacher | Success |
| PATCH /api/teachers/{id} | {"full_name": "Should Not Work"}  (any field at all is rejected) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'full_name': ['Unknown field.']}} | Success |
| PATCH /api/teachers/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Teacher not found'} | Success |
| DELETE /api/teachers/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/teachers/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Teacher not found'} | Success |
| GET /api/parents | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/parents | logged in as parent (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| GET /api/parents | 2 parents exist | 200; total=2 | 200; total=2 | Success |
| GET /api/parents/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Parent not found'} | Success |
| GET /api/parents/{id} | id=3, has 1 linked child | 200; full_name="Detail Parent", student_ids=[1] | 200; {'full_name': 'Detail Parent', 'student_ids': [1]} | Success |
| POST /api/parents | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/parents | {"full_name": "New Parent", ..., "occupation": "Doctor", "address": "123 Main St"} | 201; occupation="Doctor", student_ids=[] | 201; {'occupation': 'Doctor', 'student_ids': []} | Success |
| POST /api/parents | {} (all required fields omitted) | 400; message has full_name, email, password | 400; {'error': 'validation_error', 'message': {'email': ['Missing data for required field.'], 'full_name': ['Missing data for required field.'], 'password': ['Missing data for required field.']}} | Success |
| POST /api/parents | email "dupparent@test.com" already in use | 409; error="email_taken" | 409; {'error': 'email_taken', 'message': 'An account with this email already exists'} | Success |
| PATCH /api/parents/{id} | logged in as parent (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| PATCH /api/parents/{id} | {"occupation": "Pilot", "address": "New Address"} | 200; occupation="Pilot", address="New Address" | 200; {'occupation': 'Pilot', 'address': 'New Address'} | Success |
| PATCH /api/parents/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Parent not found'} | Success |
| DELETE /api/parents/{id} | logged in as parent (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/parents/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Parent not found'} | Success |
| DELETE /api/parents/{id} | parent still has 1 linked student | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'Cannot delete: 1 student(s) are still linked to this parent'} | Success |
| GET /api/classes | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/classes | 2 classes exist, logged in as admin | 200; total=2 | 200; total=2 | Success |
| GET /api/classes | logged in as teacher assigned only to grade=1 (2 classes exist) | 200; items=[grade 1] only | 200; grades=[1] | Success |
| GET /api/classes | logged in as parent whose child is in grade=1 (2 classes exist) | 200; items=[grade 1] only | 200; grades=[1] | Success |
| GET /api/classes/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| GET /api/classes/{id} | logged in as a teacher not assigned to this class | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'You do not have access to this resource'} | Success |
| GET /api/classes/{id} | class has 2 students enrolled | 200; student_count=2 | 200; student_count=2 | Success |
| POST /api/classes | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/classes | {"grade": 9} | 201; grade=9, student_count=0 | 201; {'grade': 9, 'student_count': 0} | Success |
| POST /api/classes | {"grade": 13}  (above max of 12) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'grade': ['Must be greater than or equal to 1 and less than or equal to 12.']}} | Success |
| POST /api/classes | {"grade": 0}  (below min of 1) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'grade': ['Must be greater than or equal to 1 and less than or equal to 12.']}} | Success |
| POST /api/classes | {} (grade omitted) | 400; message.grade present | 400; {'error': 'validation_error', 'message': {'grade': ['Missing data for required field.']}} | Success |
| POST /api/classes | grade=10 already exists (one batch per grade) | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'A class for this grade already exists'} | Success |
| PATCH /api/classes/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| PATCH /api/classes/{id} | {"grade": 2} | 200; grade=2 | 200; grade=2 | Success |
| PATCH /api/classes/{id} | grade changed to 3, which already exists | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'A class for this grade already exists'} | Success |
| PATCH /api/classes/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| DELETE /api/classes/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/classes/{id} | id=1, no students enrolled | 204, empty body | 204; body=b'' | Success |
| GET /api/classes/{id} | same id, immediately after delete | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| DELETE /api/classes/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| DELETE /api/classes/{id} | class still has 1 student assigned | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'Cannot delete: 1 student(s) are still assigned to this class'} | Success |
| GET /api/assignments | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/assignments | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| GET /api/assignments | 1 assignment exists (grade 1 / English) | 200; total=1, items[0].grade=1, subject_name="English" | 200; total=1, item={'grade': 1, 'subject_name': 'English'} | Success |
| GET /api/assignments?class_id={id} | class_id=2 (2 assignments exist across 2 classes) | 200; total=1 | 200; total=1 | Success |
| GET /api/assignments?teacher_id={id} | teacher_id belongs to a teacher with 0 assignments | 200; total=0 | 200; total=0 | Success |
| POST /api/assignments | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/assignments | {class_id: 1, subject_id: 1, teacher_id: 1} | 201; matches the ids sent | 201; {'class_id': 1, 'subject_id': 1, 'teacher_id': 1} | Success |
| POST /api/assignments | {} (all fields omitted) | 400; message has class_id, subject_id, teacher_id | 400; {'error': 'validation_error', 'message': {'class_id': ['Missing data for required field.'], 'subject_id': ['Missing data for required field.'], 'teacher_id': ['Missing data for required field.']}} | Success |
| POST /api/assignments | class_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| POST /api/assignments | subject_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Subject not found'} | Success |
| POST /api/assignments | teacher_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Teacher not found'} | Success |
| POST /api/assignments | same class_id+subject_id already assigned to a different teacher | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'This class/subject combination is already assigned to a teacher'} | Success |
| DELETE /api/assignments/{id} | logged in as teacher (non-admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/assignments/{id} | id=1 | 204, empty body | 204; body=b'' | Success |
| DELETE /api/assignments/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Assignment not found'} | Success |
| POST /api/resources | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| POST /api/resources | logged in as parent (non-admin/teacher) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/resources | logged in as student (non-admin/teacher) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/resources | multipart: type=note, subject_id, class_id, file=notes.pdf (25 bytes), logged in as admin | 201; type="note", subject_name="Maths", grade=1, filename="notes.pdf", size=25 | 201; {'type': 'note', 'subject_name': 'Maths', 'grade': 1, 'filename': 'notes.pdf', 'size': 25} | Success |
| POST /api/resources | logged in as teacher | 201 | 201; type=note | Success |
| POST /api/resources | file field omitted | 400; error="missing_file" | 400; {'error': 'missing_file', 'message': 'No file was uploaded'} | Success |
| POST /api/resources | file=virus.exe (.exe not in the allowed-extensions list) | 400; error="invalid_file_type" | 400; {'error': 'invalid_file_type', 'message': "File type .exe isn't allowed. Allowed types: doc, docx, jpeg, jpg, pdf, png, txt"} | Success |
| POST /api/resources | file content is 0 bytes | 400; error="empty_file" | 400; {'error': 'empty_file', 'message': 'Uploaded file is empty'} | Success |
| POST /api/resources | type/subject_id/class_id all omitted | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'class_id': ['Missing data for required field.'], 'subject_id': ['Missing data for required field.'], 'type': ['Missing data for required field.']}} | Success |
| POST /api/resources | type="not_a_real_type" (not one of note/pdf/image/question_paper/answer_key) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'type': ['Must be one of: note, pdf, image, question_paper, answer_key.']}} | Success |
| POST /api/resources | class_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| POST /api/resources | subject_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Subject not found'} | Success |
| GET /api/resources | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/resources | 2 resources exist across 2 classes, logged in as admin | 200; total=2 | 200; total=2 | Success |
| GET /api/resources | logged in as a student in grade=1; 1 resource exists in each of grade 1/2 | 200; items=[visible.pdf] only | 200; filenames=['visible.pdf'] | Success |
| GET /api/resources | logged in as a parent whose child is in grade=1 | 200; items=[visible.pdf] only | 200; filenames=['visible.pdf'] | Success |
| GET /api/resources | logged in as a teacher assigned only to grade=1 | 200; items=[visible.pdf] only | 200; filenames=['visible.pdf'] | Success |
| GET /api/resources/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Resource not found'} | Success |
| GET /api/resources/{id} | logged in as student in grade=2, resource belongs to grade=1 | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'You do not have access to this resource'} | Success |
| GET /api/resources/{id}/download | id=1 | 200; filename="dl.pdf", expires_in=300, url starts with the fake storage host | 200; {'expires_in': 300, 'filename': 'dl.pdf', 'url': 'https://fake-storage.test/note/1/f0a85187-b1ef-41ef-854b-1d6b272a7ea2_dl.pdf?expires_in=300'} | Success |
| GET /api/resources/{id}/download | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Resource not found'} | Success |
| GET /api/resources/{id}/download | logged in as a teacher not assigned to this resource's class | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'You do not have access to this resource'} | Success |
| DELETE /api/resources/{id} | logged in as parent (role_required rejects before any lookup) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/resources/{id} | logged in as student (role_required rejects before any lookup) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| DELETE /api/resources/{id} | id=1, logged in as admin (not the uploader) | 204, empty body | 204; body=b'' | Success |
| GET /api/resources/{id} | same id, immediately after delete | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Resource not found'} | Success |
| DELETE /api/resources/{id} | logged in as the teacher who uploaded this resource | 204, empty body | 204; body=b'' | Success |
| DELETE /api/resources/{id} | logged in as a different teacher (not the uploader, not admin) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Only the uploader or an admin can delete this resource'} | Success |
| DELETE /api/resources/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Resource not found'} | Success |
| DELETE /api/resources/{id} | resource is referenced by 1 homework record | 409; error="conflict" | 409; {'error': 'conflict', 'message': 'Cannot delete: referenced by 1 homework and 0 test record(s)'} | Success |
| POST /api/attendance/bulk | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| POST /api/attendance/bulk | logged in as parent (non-admin/teacher) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/attendance/bulk | logged in as student (non-admin/teacher) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| POST /api/attendance/bulk | class_id=1, date=2026-01-15, entries=[{s1: present}, {s2: absent}] | 201; both created, none skipped, method=manual | 201; created=2, skipped=[], statuses={1: 'present', 2: 'absent'} | Success |
| POST /api/attendance/bulk | logged in as the teacher assigned to this class | 201; created[0].status=late | 201; status=late | Success |
| POST /api/attendance/bulk | first call: mark s1 present for 2026-01-15 | 201; created=[s1] | 201; created_ids=[1] | Success |
| POST /api/attendance/bulk | second call, same class/date: re-mark s1 (already marked) + new s2 | 201; created=[s2] only, skipped_student_ids=[s1]  -- re-marking is skipped, not rejected, so a future facial auto-marking pass can coexist with manual marking | 201; created_ids=[2], skipped=[1] | Success |
| POST /api/attendance/bulk | entries lists student 1 twice | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'entries': ['entries contains the same student_id more than once']}} | Success |
| POST /api/attendance/bulk | entries=[] (empty) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'entries': ['Shorter than minimum length 1.']}} | Success |
| POST /api/attendance/bulk | status="on_vacation" (not one of present/absent/late) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'entries': {'0': {'status': ['Must be one of: present, absent, late.']}}}} | Success |
| POST /api/attendance/bulk | class_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Class not found'} | Success |
| POST /api/attendance/bulk | student_id=999999 (does not exist) | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Unknown student_id(s): [999999]'} | Success |
| POST /api/attendance/bulk | student belongs to grade=2 but class_id targets grade=1 | 400; error="invalid_student_class" | 400; {'error': 'invalid_student_class', 'message': 'student_id(s) not enrolled in class 1: [2]'} | Success |
| GET /api/attendance | no session | 401 | 401; {'error': 'authentication_required', 'message': 'Missing cookie "access_token_cookie"'} | Success |
| GET /api/attendance | 1 record exists, logged in as admin | 200; total=1 | 200; total=1 | Success |
| GET /api/attendance | logged in as teacher assigned only to grade=1; 1 record exists per class | 200; total=1, items[0].student_id=1 | 200; total=1, student_id=1 | Success |
| GET /api/attendance | logged in as parent; both their child and a classmate have records in the SAME class | 200; total=1 (only the parent's own child, scoped by identity not class_id), student_id=1 | 200; total=1, student_id=1 | Success |
| GET /api/attendance | logged in as student; a classmate also has a record for the same class/date | 200; total=1, student_id=1 | 200; total=1, student_id=1 | Success |
| GET /api/attendance?date_from={bad} | date_from=not-a-date | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'date_from': ['date_from must be an ISO date (YYYY-MM-DD)']}} | Success |
| GET /api/attendance?date_from={date} | record exists on 2026-01-01; filter date_from=2026-02-01 | 200; total=0 | 200; total=0 | Success |
| GET /api/attendance?date_from&date_to | filter range 2026-01-01..2026-01-31 (record is inside range) | 200; total=1 | 200; total=1 | Success |
| PATCH /api/attendance/{id} | logged in as parent (non-admin/teacher) | 403; error="forbidden" | 403; {'error': 'forbidden', 'message': 'Insufficient permissions'} | Success |
| PATCH /api/attendance/{id} | id=1, {"status": "present"}  (correcting absent -> present) | 200; status=present | 200; status=present | Success |
| PATCH /api/attendance/{id} | {"status": "sleeping"}  (not a valid status) | 400; error="validation_error" | 400; {'error': 'validation_error', 'message': {'status': ['Must be one of: present, absent, late.']}} | Success |
| PATCH /api/attendance/{id} | id=999999 | 404; error="not_found" | 404; {'error': 'not_found', 'message': 'Attendance record not found'} | Success |
| Direct DB query: SELECT * FROM users WHERE id=2  (before deleting the student) | user_id=2 belonging to the student created above | 1 row returned (the user exists) | User.query.get(2) = <User 2 student193@test.com (student)>, email=student193@test.com | Success |
| DELETE /api/students/{id} | id=1 (student) | 204, empty body | 204; body=b'' | Success |
| Direct DB query: SELECT * FROM users WHERE id=2  (after deleting the student) | same user_id=2, queried immediately after the DELETE call returned 204 | 0 rows returned (User.query.get returns None) -- the FK cascade (cascade="all, delete-orphan" on the User side) removed the user row too, not just the profile row | User.query.get(2) = None | Success |
| Direct DB query: SELECT * FROM users WHERE id=2  (before deleting the teacher) | user_id=2 belonging to the teacher created above | 1 row returned (the user exists) | User.query.get(2) = <User 2 teacher196@test.com (teacher)>, email=teacher196@test.com | Success |
| DELETE /api/teachers/{id} | id=1 (teacher) | 204, empty body | 204; body=b'' | Success |
| Direct DB query: SELECT * FROM users WHERE id=2  (after deleting the teacher) | same user_id=2, queried immediately after the DELETE call returned 204 | 0 rows returned (User.query.get returns None) -- the FK cascade (cascade="all, delete-orphan" on the User side) removed the user row too, not just the profile row | User.query.get(2) = None | Success |
| Direct DB query: SELECT * FROM users WHERE id=2  (before deleting the parent) | user_id=2 belonging to the parent created above | 1 row returned (the user exists) | User.query.get(2) = <User 2 parent198@test.com (parent)>, email=parent198@test.com | Success |
| DELETE /api/parents/{id} | id=1 (parent) | 204, empty body | 204; body=b'' | Success |
| Direct DB query: SELECT * FROM users WHERE id=2  (after deleting the parent) | same user_id=2, queried immediately after the DELETE call returned 204 | 0 rows returned (User.query.get returns None) -- the FK cascade (cascade="all, delete-orphan" on the User side) removed the user row too, not just the profile row | User.query.get(2) = None | Success |
| POST /api/classes | {} (grade omitted) -- used as the real backend payload for the frontend bug repro below | 400; error="validation_error"; message is an OBJECT, e.g. {"grade": ["Missing data for required field."]} | 400; {'error': 'validation_error', 'message': {'grade': ['Missing data for required field.']}} | Success |
| Frontend: apiClient.js error handling for a validation_error response (ORIGINAL buggy code) | Real backend body from the request above: {'error': 'validation_error', 'message': {'grade': ['Missing data for required field.']}} | A readable message the UI can show in a toast, e.g. "grade: Missing data for required field." | err.message = "[object Object]"  (captured by running the original code — `new ApiError((data && data.message) \|\| response.statusText, ...)` — through Node with this exact response body) | Fail |
| Frontend: apiClient.js error handling for a validation_error response (FIXED code, current file) | Same real backend body: {'error': 'validation_error', 'message': {'grade': ['Missing data for required field.']}} | A readable message, e.g. "grade: Missing data for required field." | err.message = "grade: Missing data for required field."  (captured by running the current formatErrorMessage() + ApiError construction through Node with this exact response body) | Success |
| POST /api/students/{id}/profile-image | Real photo `person1.jpg`, student enrolled in grade 7 | 200; has_face_embedding=true, real embedding computed (not mocked) | 200; has_face_embedding=True, face_embedding stored, dims=4096 (VGG-Face) | Success |
| POST /api/students/{id}/profile-image | Real photo `person2.jpg` | 200; has_face_embedding=true | 200; has_face_embedding=True, dims=4096 | Success |
| POST /api/students/{id}/profile-image | Real photo `person3.jpg` | 200; has_face_embedding=true | 200; has_face_embedding=True, dims=4096 | Success |
| POST /api/attendance/facial | Real photo `group.png` (all 3 enrolled students together), class_id=grade-7 class, date=2026-08-14 | 200; faces_detected=3; all 3 auto-marked present (confidence >= HIGH=0.60); needs_confirmation=[] | 200; faces_detected=3; auto_marked=[{student 1, confidence=0.650}, {student 2, confidence=0.755}, {student 3, confidence=0.803}]; needs_confirmation=[]. Raw cosine-similarity matrix (face vs every candidate) confirms correct assignment with no ambiguity: face0 vs {s1:0.650, s2:0.036, s3:0.179}; face1 vs {s1:0.028, s2:0.755, s3:0.058}; face2 vs {s1:0.102, s2:0.074, s3:0.803} | Success |
| POST /api/attendance/facial | Real photo `person4.jpg` ALONE (4th person, not in the group photo/not enrolled), same class, date=2026-08-15 | 200; faces_detected=1; auto_marked=[] (must NOT match student 1/2/3); needs_confirmation has 1 entry | 200; faces_detected=1; auto_marked=[]; needs_confirmation=[{face_index:0, best_match_student_id:null, confidence:null}] (raw best-match score below LOW threshold so the API reports it as unmatched). Direct engine call for the real underlying number: best_match=student 2, raw confidence=0.147 -- correctly far below both LOW (0.40) and HIGH (0.60) | Success |
| POST /api/attendance/facial | Composite of `group.png` + `person4.jpg` side-by-side (4 real faces in one image: 3 enrolled + 1 unknown), date=2026-08-16 | 200; faces_detected=4; exactly students 1/2/3 auto-marked; person4's face isolated in needs_confirmation, not folded into any of the 3 real matches | 200; faces_detected=4; auto_marked=[{student 1, confidence=0.655}, {student 2, confidence=0.780}, {student 3, confidence=0.798}] (consistent with the standalone group.png run); needs_confirmation=[{face_index:0, best_match_student_id:null, confidence:null}] -- person4 correctly isolated | Success |
| Direct DB query: SELECT * FROM attendance WHERE class_id=1 AND method='facial' AND date='2026-08-14' | Rows created by the group.png facial run above | 3 rows, student_ids={1,2,3}, method=facial, status=present | 3 rows returned: Attendance(student_id=1, method=facial, status=present), Attendance(student_id=2, method=facial, status=present), Attendance(student_id=3, method=facial, status=present) -- student_ids match exactly, no extra/missing rows, none for person4 | Success |

## Threshold gap analysis (from the real run above)

- Correct-match confidences, group.png (3 real students): 0.650, 0.755, 0.803
- Lowest correct-match confidence: **0.650** (student 1)
- Highest incorrect-match confidence (person4, not enrolled): **0.147**
- Threshold gap (lowest correct minus highest incorrect): **0.503**

Both configured thresholds landed on the right side of every real score in this run: the weakest genuine match (0.650) cleared FACE_HIGH_CONFIDENCE_THRESHOLD (0.60) and every incorrect match (0.147) fell far short of FACE_LOW_CONFIDENCE_THRESHOLD (0.40). FACE_LOW_CONFIDENCE_THRESHOLD=0.40 has a wide margin (0.253) below it and needs no change. FACE_HIGH_CONFIDENCE_THRESHOLD=0.60 passed, but only by a 0.05 margin on the weakest genuine match -- thin for a threshold that has to hold up across real classroom lighting/angles, not just controlled headshots. Recommendation: lower FACE_HIGH_CONFIDENCE_THRESHOLD to **0.55**. That gives auto-marking more headroom for borderline-but-genuine matches, and costs nothing on the false-positive side since even 0.55 still sits 0.403 above the highest incorrect score observed (0.147). Applied in backend/config.py with this reasoning as a comment; n=3 subjects / n=1 negative, so re-validate if a larger real photo set becomes available.
