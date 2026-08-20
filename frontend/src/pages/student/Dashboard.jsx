import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { STUDENT_NAV } from "@/lib/navConfig";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CalendarCheck, BookOpen, ArrowRight, Sparkles, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

const ATTENDANCE_STATUS_COLOR = { present: "text-lime", absent: "text-coral", late: "text-yellow" };

export default function StudentDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [upcomingTests, setUpcomingTests] = useState([]);
  const [pendingHomework, setPendingHomework] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState(null);

  useEffect(() => {
    const today = todayIso();
    Promise.all([
      api.get("/api/tests?per_page=100"),
      api.get("/api/homework?per_page=100"),
      api.get("/api/homework-submissions?per_page=100"),
      api.get(`/api/attendance?date_from=${today}&date_to=${today}&per_page=1`),
    ])
      .then(([testsRes, hwRes, subRes, attendanceRes]) => {
        const submittedIds = new Set(subRes.items.map((s) => s.homework_id));

        setUpcomingTests(
          testsRes.items
            .filter((t) => t.due_date >= today)
            .sort((a, b) => a.due_date.localeCompare(b.due_date))
            .slice(0, 5)
        );
        setPendingHomework(
          hwRes.items
            .filter((h) => !submittedIds.has(h.id))
            .sort((a, b) => a.due_date.localeCompare(b.due_date))
            .slice(0, 4)
        );
        setTodayAttendance(attendanceRes.items[0] || null);
      })
      .catch(() => toast.error("Couldn't load your dashboard. Please refresh."))
      .finally(() => setLoading(false));
  }, []);

  const firstName = user?.full_name?.split(" ")[0] || "there";

  return (
    <DashboardLayout title={`Hey ${firstName} 👋`} subtitle="Here's your plan for today and what's coming up." nav={STUDENT_NAV}>
      {loading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="lg:col-span-2 h-72 w-full rounded-xl" />
            <Skeleton className="h-72 w-full rounded-xl" />
          </div>
          <Skeleton className="h-40 w-full rounded-xl" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <Card className="lg:col-span-2 border-soft shadow-none">
              <CardContent className="p-6">
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">This month</div>
                <div className="font-display text-xl font-semibold mt-1 mb-5">Upcoming tests</div>
                {upcomingTests.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">No upcoming tests scheduled.</p>
                ) : (
                  <div className="space-y-3">
                    {upcomingTests.map((t) => (
                      <div key={t.id} className="flex items-center gap-4 p-3 rounded-lg border border-soft">
                        <div className="w-9 h-9 shrink-0 rounded-lg bg-sage/60 flex items-center justify-center">
                          <CalendarCheck className="w-4 h-4 text-ink" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium">{t.title}</div>
                          <div className="text-xs text-muted-foreground">{t.subject_name}</div>
                        </div>
                        <div className="text-xs font-semibold text-coral shrink-0">Due {t.due_date}</div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="border-soft shadow-none bg-coral text-ink">
                <CardContent className="p-6">
                  <div className="w-10 h-10 rounded-lg bg-ink/10 flex items-center justify-center mb-4">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div className="font-display text-xl font-semibold leading-snug">Stuck on a concept?</div>
                  <div className="text-sm text-ink/70 mt-2">Chat with your SmartBatch AI assistant</div>
                  <Link
                    to="/student/assistant"
                    data-testid="link-ai-assistant"
                    className="mt-5 inline-flex items-center gap-1.5 text-sm font-bold hover:gap-2 transition-all"
                  >
                    Open AI chat <ArrowRight className="w-4 h-4" />
                  </Link>
                </CardContent>
              </Card>

              <Card className="border-soft shadow-none">
                <CardContent className="p-6">
                  <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Today</div>
                  <div className="font-display text-lg font-semibold mt-1 mb-4">Attendance</div>
                  {todayAttendance ? (
                    <>
                      <div className={`text-2xl font-display font-bold capitalize ${ATTENDANCE_STATUS_COLOR[todayAttendance.status] || "text-foreground"}`}>
                        {todayAttendance.status}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {todayAttendance.method === "facial" ? "Confirmed via AI face detection" : `Marked by ${todayAttendance.marked_by_name}`}
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="text-xl font-display font-bold text-muted-foreground">Not marked yet</div>
                      <div className="text-xs text-muted-foreground mt-1">Check back later today</div>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          <Card className="border-soft shadow-none">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Pending</div>
                  <div className="font-display text-xl font-semibold mt-1">Homework due soon</div>
                </div>
                <Link
                  to="/student/homework"
                  className="text-sm font-medium text-coral hover:underline inline-flex items-center gap-1"
                  data-testid="link-view-homework"
                >
                  View all <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              {pendingHomework.length === 0 ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
                  <CheckCircle2 className="w-4 h-4 text-lime" /> You're all caught up -- nothing pending.
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 gap-4">
                  {pendingHomework.map((h) => (
                    <div key={h.id} className="p-4 rounded-xl border border-soft flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-sage/60 flex items-center justify-center shrink-0">
                        <BookOpen className="w-5 h-5 text-ink" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{h.title}</div>
                        <div className="text-xs text-yellow font-semibold mt-0.5">Due {h.due_date}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </DashboardLayout>
  );
}
