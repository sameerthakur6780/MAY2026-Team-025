import DashboardLayout from "@/components/DashboardLayout";
import ResourcesReadOnlyView from "@/components/resources/ResourcesReadOnlyView";
import { PARENT_NAV } from "@/lib/navConfig";

export default function ParentResources() {
  return (
    <DashboardLayout title="Resources" subtitle="Notes and materials shared for your child's class." nav={PARENT_NAV}>
      <ResourcesReadOnlyView />
    </DashboardLayout>
  );
}
