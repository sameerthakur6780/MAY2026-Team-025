import DashboardLayout from "@/components/DashboardLayout";
import ResourcesReadOnlyView from "@/components/resources/ResourcesReadOnlyView";
import { ADMIN_NAV } from "@/lib/navConfig";

export default function AdminResources() {
  return (
    <DashboardLayout title="Resources" subtitle="Notes, question papers, and answer keys uploaded by teachers." nav={ADMIN_NAV}>
      <ResourcesReadOnlyView />
    </DashboardLayout>
  );
}
