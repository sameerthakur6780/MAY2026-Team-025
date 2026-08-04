
export function roleHome(role) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "teacher") return "/teacher/dashboard";
  if (role === "parent") return "/parent/dashboard";
  if (role === "student") return "/student/dashboard";
  return "/";
}

export const ROLE_LABEL = {
  admin: "Admin",
  teacher: "Teacher",
  parent: "Parent",
  student: "Student",
};
