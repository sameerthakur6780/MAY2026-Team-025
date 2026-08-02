import { LayoutDashboard, Wallet, Camera, FolderOpen, BookOpen, ClipboardCheck, Megaphone, Bell, LineChart, CalendarDays, MessageCircle } from "lucide-react";

export const ADMIN_NAV = [
  { to: "/admin/dashboard", key: "admin-dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/finance", key: "admin-finance", label: "Finance", icon: Wallet },
  { to: "/admin/attendance", key: "admin-attendance", label: "Attendance", icon: Camera },
  { to: "/admin/resources", key: "admin-resources", label: "Resources", icon: FolderOpen },
  { to: "/admin/homework", key: "admin-homework", label: "Homework", icon: BookOpen },
  { to: "/admin/grading", key: "admin-grading", label: "AI Grading", icon: ClipboardCheck },
  { to: "/admin/alerts", key: "admin-alerts", label: "Alerts", icon: Megaphone },
];

export const PARENT_NAV = [
  { to: "/parent/dashboard", key: "parent-dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/parent/safety", key: "parent-safety", label: "Safety Feed", icon: Bell },
  { to: "/parent/fees", key: "parent-fees", label: "Fees & Pay", icon: Wallet },
  { to: "/parent/performance", key: "parent-performance", label: "Performance", icon: LineChart },
];

export const STUDENT_NAV = [
  { to: "/student/dashboard", key: "student-dashboard", label: "My Plan", icon: CalendarDays },
  { to: "/student/resources", key: "student-resources", label: "Resources", icon: FolderOpen },
  { to: "/student/homework", key: "student-homework", label: "Homework", icon: BookOpen },
  { to: "/student/assistant", key: "student-assistant", label: "AI Assistant", icon: MessageCircle },
];
