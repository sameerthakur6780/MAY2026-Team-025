import { LayoutDashboard, Wallet, Camera, FolderOpen, BookOpen, ClipboardCheck, Megaphone, Bell, CalendarDays, CalendarClock, MessageCircle, GraduationCap, School, Presentation, Users, ClipboardList } from "lucide-react";

export const ADMIN_NAV = [
  { to: "/admin/dashboard", key: "admin-dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/students", key: "admin-students", label: "Students", icon: GraduationCap },
  { to: "/admin/classes", key: "admin-classes", label: "Classes", icon: School },
  { to: "/admin/teachers", key: "admin-teachers", label: "Teachers", icon: Presentation },
  { to: "/admin/parents", key: "admin-parents", label: "Parents", icon: Users },
  { to: "/admin/assignments", key: "admin-assignments", label: "Assignments", icon: ClipboardList },
  { to: "/admin/attendance", key: "admin-attendance", label: "Attendance", icon: Camera },
  { to: "/admin/resources", key: "admin-resources", label: "Resources", icon: FolderOpen },
  { to: "/admin/alerts", key: "admin-alerts", label: "Alerts", icon: Megaphone },
];

export const TEACHER_NAV = [
  { to: "/teacher/dashboard", key: "teacher-dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/teacher/attendance", key: "teacher-attendance", label: "Attendance", icon: CalendarClock },
  { to: "/teacher/resources", key: "teacher-resources", label: "Resources", icon: FolderOpen },
  { to: "/teacher/homework", key: "teacher-homework", label: "Homework", icon: BookOpen },
  { to: "/teacher/grading", key: "teacher-grading", label: "AI Grading", icon: ClipboardCheck },
];

export const PARENT_NAV = [
  { to: "/parent/dashboard", key: "parent-dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/parent/attendance", key: "parent-attendance", label: "Attendance", icon: CalendarClock },
  { to: "/parent/safety", key: "parent-safety", label: "Safety Feed", icon: Bell },
  { to: "/parent/fees", key: "parent-fees", label: "Fees & Pay", icon: Wallet },
  { to: "/parent/resources", key: "parent-resources", label: "Resources", icon: FolderOpen },
];

export const STUDENT_NAV = [
  { to: "/student/dashboard", key: "student-dashboard", label: "My Plan", icon: CalendarDays },
  { to: "/student/attendance", key: "student-attendance", label: "Attendance", icon: CalendarClock },
  { to: "/student/resources", key: "student-resources", label: "Resources", icon: FolderOpen },
  { to: "/student/homework", key: "student-homework", label: "Homework", icon: BookOpen },
  { to: "/student/assistant", key: "student-assistant", label: "AI Assistant", icon: MessageCircle },
];
