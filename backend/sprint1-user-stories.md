# sprint 1 — user stories (scope: auth through manual attendance)

facial recognition, rag, grading, notifications, analytics, and payments are out of scope for this sprint — deferred to sprint 2+.

| id | user story | endpoint(s) |
|----|------------|-------------|
| US-01 | as an admin, i want to log in with email/password so i can access the platform securely | POST /api/auth/login |
| US-02 | as any authenticated user, i want to log out so my session ends securely | POST /api/auth/logout |
| US-03 | as any authenticated user, i want my session to persist across requests via cookies so i don't have to re-login constantly | GET /api/auth/me, apiClient refresh-on-401 |
| US-04 | as an admin, i want to create teacher/parent/student accounts so only authorized people can access the system | POST /api/auth/signup, POST /api/students, /api/teachers, /api/parents |
| US-05 | as an admin, i want to manage student records (create/edit/delete) so i can maintain accurate enrollment data | /api/students CRUD |
| US-06 | as an admin, i want to manage teacher records so i can maintain staff data | /api/teachers (list/create/delete) |
| US-07 | as an admin, i want to manage parent records so i can maintain guardian contact/data | /api/parents CRUD |
| US-08 | as an admin, i want to manage classes (grade 1-12) so i can organize students correctly | /api/classes (list/create/edit) |
| US-09 | as an admin, i want to assign teachers to specific classes and subjects so teaching responsibilities are tracked | /api/assignments CRUD |
| US-10 | as a teacher, i want to see only the classes/students i'm assigned to so i don't access unrelated data | GET /api/students, /api/classes (role-scoped) |
| US-11 | as a parent, i want to see only my own child's data so i can't access other students' information | GET /api/students, /api/classes (role-scoped) |
| US-12 | as a teacher/admin, i want to upload notes/pdfs/question papers for a class+subject so students can access study material | POST /api/resources |
| US-13 | as a student/parent, i want to view and download resources for my class so i can study/support learning | GET /api/resources, signed download url |
| US-14 | as a teacher, i want to mark attendance for my whole class at once so daily attendance is efficient | POST /api/attendance (bulk) |
| US-15 | as a teacher, i want to correct a single student's attendance entry so mistakes can be fixed without redoing the whole day | PATCH /api/attendance/<id> |
| US-16 | as any role, i want to view attendance history scoped to what i'm authorized to see | GET /api/attendance (role-scoped, filterable) |

