import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import AttendanceMarkView from "@/components/attendance/AttendanceMarkView";
import AttendanceHistoryView from "@/components/attendance/AttendanceHistoryView";
import { TEACHER_NAV } from "@/lib/navConfig";
import { Button } from "@/components/ui/button";

export default function TeacherAttendance() {
  const [view, setView] = useState("mark");

  return (
    <DashboardLayout
      title="Attendance"
      subtitle="Mark daily attendance for your classes and review past records."
      nav={TEACHER_NAV}
    >
      <div className="flex gap-2 mb-6">
        <Button
          data-testid="view-mark"
          variant={view === "mark" ? "default" : "outline"}
          className={view === "mark" ? "bg-forest hover:bg-[#162D24] text-white rounded-full px-5" : "border-soft rounded-full px-5"}
          onClick={() => setView("mark")}
        >
          Mark attendance
        </Button>
        <Button
          data-testid="view-history"
          variant={view === "history" ? "default" : "outline"}
          className={view === "history" ? "bg-forest hover:bg-[#162D24] text-white rounded-full px-5" : "border-soft rounded-full px-5"}
          onClick={() => setView("history")}
        >
          History
        </Button>
      </div>

      {view === "mark" ? <AttendanceMarkView /> : <AttendanceHistoryView />}
    </DashboardLayout>
  );
}
