import { Link } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { PARENT_NAV } from "@/lib/navConfig";
import { SAFETY_FEED, FEE_RECORDS, STUDENT_PERFORMANCE } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, TrendingUp, Wallet, ArrowRight } from "lucide-react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function ParentDashboard() {
  const pending = FEE_RECORDS.filter(f => f.status !== "paid").reduce((a, b) => a + b.amount, 0);
  const avgScore = Math.round(STUDENT_PERFORMANCE.reduce((a, b) => a + b.score, 0) / STUDENT_PERFORMANCE.length);
  const recent = SAFETY_FEED.slice(0, 3);

  return (
    <DashboardLayout title="Aarav's overview" subtitle="A calm, at-a-glance view of your child's day." nav={PARENT_NAV}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center mb-4"><CheckCircle2 className="w-5 h-5 text-ink" /></div>
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Today's attendance</div>
          <div className="text-2xl font-display font-bold text-lime mt-1">Present at 5:04 PM</div>
          <div className="text-xs text-muted-foreground mt-1">Confirmed via AI face detection</div>
        </CardContent></Card>
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center mb-4"><TrendingUp className="w-5 h-5 text-ink" /></div>
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Avg. score</div>
          <div className="text-3xl font-display font-bold text-coral mt-1">{avgScore}%</div>
          <div className="text-xs text-muted-foreground mt-1">Across last 5 tests</div>
        </CardContent></Card>
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="w-10 h-10 rounded-lg bg-yellow/25 flex items-center justify-center mb-4"><Wallet className="w-5 h-5 text-yellow" /></div>
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Pending fees</div>
          <div className="text-3xl font-display font-bold text-yellow mt-1">₹{pending.toLocaleString()}</div>
          <Link to="/parent/fees" className="text-xs text-yellow font-semibold mt-2 inline-flex items-center gap-1 hover:underline" data-testid="link-pay-fees">Pay now <ArrowRight className="w-3 h-3" /></Link>
        </CardContent></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Performance trend</div>
            <div className="font-display text-xl font-semibold mt-1 mb-4">Recent tests</div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={STUDENT_PERFORMANCE}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3F3F3F" />
                  <XAxis dataKey="test" stroke="#9A9A9A" fontSize={12} />
                  <YAxis stroke="#9A9A9A" fontSize={12} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: "#2C2C2C", border: "1px solid #3F3F3F", borderRadius: 12, color: "#FFFFFF" }} labelStyle={{ color: "#FFFFFF" }} />
                  <Line type="monotone" dataKey="score" stroke="#F65E4B" strokeWidth={2.5} dot={{ fill: "#F65E4B", r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Latest updates</div>
            <div className="font-display text-xl font-semibold mt-1 mb-4">Safety & alerts</div>
            <div className="space-y-4">
              {recent.map(n => (
                <div key={n.id} className="flex gap-3">
                  <div className={`w-1.5 rounded-full shrink-0 ${n.ok ? "bg-sage" : "bg-coral"}`} />
                  <div>
                    <div className="text-sm text-foreground leading-snug">{n.message}</div>
                    <div className="text-xs text-muted-foreground mt-1">{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
            <Link to="/parent/safety" className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-coral hover:text-coral-deep" data-testid="link-safety-feed">
              Full feed <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
