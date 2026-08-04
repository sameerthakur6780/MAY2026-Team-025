import DashboardLayout from "@/components/DashboardLayout";
import AttendanceHistoryView from "@/components/attendance/AttendanceHistoryView";
import { STUDENT_NAV } from "@/lib/navConfig";

export default function StudentAttendance() {
  return (
    <DashboardLayout title="Attendance" subtitle="Your attendance history." nav={STUDENT_NAV}>
      <AttendanceHistoryView />
    </DashboardLayout>
  );
}
