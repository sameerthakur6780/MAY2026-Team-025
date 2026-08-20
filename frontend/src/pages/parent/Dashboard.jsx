import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { PARENT_NAV } from "@/lib/navConfig";
import { api } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, TrendingUp, Wallet, ArrowRight } from "lucide-react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { toast } from "sonner";

// Which notification types get the "needs attention" (coral) dot vs routine
// (sage) -- mirrors the same distinction on the full Safety & Notifications
// feed (see parent/Safety.jsx).
const NEEDS_ATTENTION = new Set(["attendance_absent", "fee_due_reminder"]);

const ATTENDANCE_STATUS_COLOR = { present: "text-lime", absent: "text-coral", late: "text-yellow" };

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function monthLabel(ym) {
  const [year, month] = ym.split("-").map(Number);
  return `${MONTH_LABELS[month - 1]} ${year}`;
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function formatWhen(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function ParentDashboard() {
  const [loading, setLoading] = useState(true);
  const [children, setChildren] = useState([]);
  const [fees, setFees] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState([]);
  const [marksTrend, setMarksTrend] = useState([]);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const today = todayIso();
    Promise.all([
      api.get("/api/students?per_page=100"),
      api.get("/api/fees?per_page=100"),
      api.get(`/api/attendance?date_from=${today}&date_to=${today}&per_page=100`),
      api.get("/api/analytics/marks-trend"),
      api.get("/api/notifications?per_page=3"),
    ])
      .then(([studentsRes, feesRes, attendanceRes, marksRes, notificationsRes]) => {
        setChildren(studentsRes.items);
        setFees(feesRes.items);
        setTodayAttendance(attendanceRes.items);
        setMarksTrend(marksRes);
        setNotifications(notificationsRes.items);
      })
      .catch(() => toast.error("Couldn't load your dashboard. Please refresh."))
      .finally(() => setLoading(false));
  }, []);

  const pending = fees.filter((f) => f.status !== "paid").reduce((a, b) => a + b.amount, 0);
  const presentCount = todayAttendance.filter((a) => a.status === "present").length;
  const avgScore = marksTrend.length
    ? Math.round(marksTrend.reduce((a, b) => a + b.value, 0) / marksTrend.length)
    : null;
  const title = children.length === 1 ? `${children[0].full_name.split(" ")[0]}'s overview` : "Your children's overview";

  return (
    <DashboardLayout
      title={loading ? "Overview" : title}
      subtitle="A calm, at-a-glance view of your child's day."
      nav={PARENT_NAV}
    >
      {loading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
            <Card className="border-soft shadow-none">
              <CardContent className="p-6">
                <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-5 h-5 text-ink" />
                </div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Today's attendance</div>
                {todayAttendance.length === 0 ? (
                  <>
                    <div className="text-xl font-display font-bold text-muted-foreground mt-1">Not marked yet</div>
                    <div className="text-xs text-muted-foreground mt-1">Check back later today</div>
                  </>
                ) : (
                  <>
                    {todayAttendance.length === 1 ? (
                      <div className={`text-2xl font-display font-bold mt-1 capitalize ${ATTENDANCE_STATUS_COLOR[todayAttendance[0].status] || "text-foreground"}`}>
                        {todayAttendance[0].status}
                      </div>
                    ) : (
                      <div className={`text-2xl font-display font-bold mt-1 ${presentCount === todayAttendance.length ? "text-lime" : "text-coral"}`}>
                        {presentCount}/{todayAttendance.length} present
                      </div>
                    )}
                    <div className="text-xs text-muted-foreground mt-1">
                      {todayAttendance[0].method === "facial"
                        ? "Confirmed via AI face detection"
                        : `Marked by ${todayAttendance[0].marked_by_name}`}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
            <Card className="border-soft shadow-none">
              <CardContent className="p-6">
                <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center mb-4">
                  <TrendingUp className="w-5 h-5 text-ink" />
                </div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Avg. score</div>
                <div className="text-3xl font-display font-bold text-coral mt-1">{avgScore !== null ? `${avgScore}%` : "--"}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {avgScore !== null ? "Monthly average, graded work" : "No graded work yet"}
                </div>
              </CardContent>
            </Card>
            <Card className="border-soft shadow-none">
              <CardContent className="p-6">
                <div className="w-10 h-10 rounded-lg bg-yellow/25 flex items-center justify-center mb-4">
                  <Wallet className="w-5 h-5 text-yellow" />
                </div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Pending fees</div>
                <div className="text-3xl font-display font-bold text-yellow mt-1">₹{pending.toLocaleString()}</div>
                <Link
                  to="/parent/fees"
                  className="text-xs text-yellow font-semibold mt-2 inline-flex items-center gap-1 hover:underline"
                  data-testid="link-pay-fees"
                >
                  Pay now <ArrowRight className="w-3 h-3" />
                </Link>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2 border-soft shadow-none">
              <CardContent className="p-6">
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Performance trend</div>
                <div className="font-display text-xl font-semibold mt-1 mb-4">Monthly average</div>
                {marksTrend.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-10 text-center">No graded homework or tests yet.</p>
                ) : (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={marksTrend.map((m) => ({ month: monthLabel(m.date), score: m.value }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#3F3F3F" />
                        <XAxis dataKey="month" stroke="#9A9A9A" fontSize={12} />
                        <YAxis stroke="#9A9A9A" fontSize={12} domain={[0, 100]} />
                        <Tooltip
                          contentStyle={{ background: "#2C2C2C", border: "1px solid #3F3F3F", borderRadius: 12, color: "#FFFFFF" }}
                          labelStyle={{ color: "#FFFFFF" }}
                        />
                        <Line type="monotone" dataKey="score" stroke="#F65E4B" strokeWidth={2.5} dot={{ fill: "#F65E4B", r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border-soft shadow-none">
              <CardContent className="p-6">
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Latest updates</div>
                <div className="font-display text-xl font-semibold mt-1 mb-4">Safety & alerts</div>
                {notifications.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nothing yet.</p>
                ) : (
                  <div className="space-y-4">
                    {notifications.map((n) => (
                      <div key={n.id} className="flex gap-3">
                        <div className={`w-1.5 rounded-full shrink-0 ${NEEDS_ATTENTION.has(n.type) ? "bg-coral" : "bg-sage"}`} />
                        <div>
                          <div className="text-sm text-foreground leading-snug">{n.subject}</div>
                          <div className="text-xs text-muted-foreground mt-1">{formatWhen(n.sent_at || n.created_at)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <Link
                  to="/parent/safety"
                  className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-coral hover:text-coral-deep"
                  data-testid="link-safety-feed"
                >
                  Full feed <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
