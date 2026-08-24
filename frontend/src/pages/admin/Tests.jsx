import DashboardLayout from "@/components/DashboardLayout";
import TestsManageView from "@/components/tests/TestsManageView";
import { ADMIN_NAV } from "@/lib/navConfig";

export default function AdminTests() {
  return (
    <DashboardLayout title="Tests" subtitle="Upload question papers and answer keys, then schedule AI auto-grading." nav={ADMIN_NAV}>
      <TestsManageView />
    </DashboardLayout>
  );
}
