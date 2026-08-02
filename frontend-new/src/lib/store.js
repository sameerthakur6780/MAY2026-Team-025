
export function roleHome(role) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "parent") return "/parent/dashboard";
  if (role === "student") return "/student/dashboard";
  return "/";
}

export const ROLE_LABEL = {
  admin: "Admin / Tutor",
  parent: "Parent",
  student: "Student",
};
