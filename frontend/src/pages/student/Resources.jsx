import DashboardLayout from "@/components/DashboardLayout";
import ResourcesReadOnlyView from "@/components/resources/ResourcesReadOnlyView";
import { STUDENT_NAV } from "@/lib/navConfig";

export default function StudentResources() {
  return (
    <DashboardLayout title="Study Resources" subtitle="All your notes and materials -- clean and distraction-free." nav={STUDENT_NAV}>
      <ResourcesReadOnlyView />
    </DashboardLayout>
  );
}
