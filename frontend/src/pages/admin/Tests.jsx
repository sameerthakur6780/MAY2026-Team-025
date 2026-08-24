import DashboardLayout from "@/components/DashboardLayout";
import TestsReadOnlyView from "@/components/tests/TestsReadOnlyView";
import { ADMIN_NAV } from "@/lib/navConfig";

export default function AdminTests() {
  return (
    <DashboardLayout title="Tests" subtitle="Tests, question papers, and grading status across every teacher." nav={ADMIN_NAV}>
      <TestsReadOnlyView />
    </DashboardLayout>
  );
}
