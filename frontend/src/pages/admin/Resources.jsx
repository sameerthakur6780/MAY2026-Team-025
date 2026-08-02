import DashboardLayout from "@/components/DashboardLayout";
import ResourcesManageView from "@/components/resources/ResourcesManageView";
import { ADMIN_NAV } from "@/lib/navConfig";

export default function AdminResources() {
  return (
    <DashboardLayout title="Resources" subtitle="Upload and manage notes, question papers, and answer keys." nav={ADMIN_NAV}>
      <ResourcesManageView />
    </DashboardLayout>
  );
}
