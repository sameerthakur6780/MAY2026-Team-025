import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import AttendanceHistoryView from "@/components/attendance/AttendanceHistoryView";
import AiAttendanceView from "@/components/attendance/AiAttendanceView";
import { ADMIN_NAV } from "@/lib/navConfig";
import { Button } from "@/components/ui/button";

export default function AdminAttendance() {
  const [view, setView] = useState("ai");

  return (
    <DashboardLayout title="Attendance" subtitle="AI photo attendance and manual attendance history." nav={ADMIN_NAV}>
      <div className="flex gap-2 mb-6">
        <Button
          data-testid="view-ai"
          variant={view === "ai" ? "default" : "outline"}
          className={view === "ai" ? "bg-coral hover:bg-coral-deep text-ink rounded-full px-5" : "border-soft rounded-full px-5"}
          onClick={() => setView("ai")}
        >
          AI photo attendance
        </Button>
        <Button
          data-testid="view-history"
          variant={view === "history" ? "default" : "outline"}
          className={view === "history" ? "bg-coral hover:bg-coral-deep text-ink rounded-full px-5" : "border-soft rounded-full px-5"}
          onClick={() => setView("history")}
        >
          History
        </Button>
      </div>

      {view === "history" ? <AttendanceHistoryView /> : <AiAttendanceView />}
    </DashboardLayout>
  );
}
