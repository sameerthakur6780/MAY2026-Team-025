import DashboardLayout from "@/components/DashboardLayout";
import ResourcesManageView from "@/components/resources/ResourcesManageView";
import { TEACHER_NAV } from "@/lib/navConfig";

export default function TeacherResources() {
  return (
    <DashboardLayout title="Resources" subtitle="Upload and manage notes, question papers, and answer keys for your classes." nav={TEACHER_NAV}>
      <ResourcesManageView />
    </DashboardLayout>
  );
}
