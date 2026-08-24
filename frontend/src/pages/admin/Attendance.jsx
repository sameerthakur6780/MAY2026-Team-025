import DashboardLayout from "@/components/DashboardLayout";
import AttendanceHistoryView from "@/components/attendance/AttendanceHistoryView";
import { ADMIN_NAV } from "@/lib/navConfig";

export default function AdminAttendance() {
  return (
    <DashboardLayout title="Attendance" subtitle="Attendance history across all classes." nav={ADMIN_NAV}>
      <AttendanceHistoryView />
    </DashboardLayout>
  );
}
