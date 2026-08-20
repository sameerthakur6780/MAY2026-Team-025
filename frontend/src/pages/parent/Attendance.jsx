import DashboardLayout from "@/components/DashboardLayout";
import AttendanceHistoryView from "@/components/attendance/AttendanceHistoryView";
import { PARENT_NAV } from "@/lib/navConfig";

export default function ParentAttendance() {
  return (
    <DashboardLayout title="Attendance" subtitle="Your child's attendance history." nav={PARENT_NAV}>
      <AttendanceHistoryView />
    </DashboardLayout>
  );
}
