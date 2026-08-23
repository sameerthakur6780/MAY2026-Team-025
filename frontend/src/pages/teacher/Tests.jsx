import DashboardLayout from "@/components/DashboardLayout";
import TestsManageView from "@/components/tests/TestsManageView";
import { TEACHER_NAV } from "@/lib/navConfig";

export default function TeacherTests() {
  return (
    <DashboardLayout title="Tests" subtitle="Upload question papers and answer keys, then schedule AI auto-grading." nav={TEACHER_NAV}>
      <TestsManageView />
    </DashboardLayout>
  );
}
