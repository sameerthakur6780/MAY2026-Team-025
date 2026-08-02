import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Wallet, Users, TrendingUp, AlertCircle, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { MONTHLY_EARNINGS, BATCHES, ANNOUNCEMENTS } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const stats = [
  { key: "collected", label: "Collected this month", value: "₹68,900", icon: Wallet, delta: "+12.4%" },
  { key: "students", label: "Active students", value: "79", icon: Users, delta: "+3" },
  { key: "avg", label: "Avg. attendance", value: "92%", icon: TrendingUp, delta: "+2.1%" },
  { key: "overdue", label: "Overdue fees", value: "₹7,500", icon: AlertCircle, delta: "1 student" },
];

export default function AdminDashboard() {
  return (
    <DashboardLayout title="Good afternoon, Tutor" subtitle="Here's what's happening across your batches today." nav={ADMIN_NAV}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {stats.map((s, i) => (
          <Card key={s.key} data-testid={`stat-${s.key}`} className="border-soft shadow-none animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center">
                  <s.icon className="w-5 h-5 text-forest" />
                </div>
                <span className="text-xs font-semibold text-forest bg-sage/60 px-2 py-1 rounded-md">{s.delta}</span>
              </div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">{s.label}</div>
              <div className="text-3xl font-display font-bold text-forest mt-2">{s.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Monthly earnings</div>
                <div className="font-display text-xl font-semibold text-[#1C1C1C] mt-1">Last 6 months</div>
              </div>
              <Link to="/admin/finance" className="text-sm font-medium text-terracotta hover:underline inline-flex items-center gap-1" data-testid="link-view-finance">
                View all <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={MONTHLY_EARNINGS}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E3DC" />
                  <XAxis dataKey="month" stroke="#5C5C5C" fontSize={12} />
                  <YAxis stroke="#5C5C5C" fontSize={12} />
                  <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E5E3DC", borderRadius: 8 }} />
                  <Line type="monotone" dataKey="earnings" stroke="#1E3F33" strokeWidth={2.5} dot={{ fill: "#E07A5F", r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Recent announcements</div>
            <div className="mt-4 space-y-4">
              {ANNOUNCEMENTS.map((a) => (
                <div key={a.id} className="flex gap-3">
                  <div className={`w-1.5 rounded-full shrink-0 ${a.priority === "high" ? "bg-terracotta" : "bg-sage"}`} />
                  <div>
                    <div className="text-sm font-medium text-[#1C1C1C] leading-snug">{a.title}</div>
                    <div className="text-xs text-[#5C5C5C] mt-1">{a.batch} • {a.when}</div>
                  </div>
                </div>
              ))}
            </div>
            <Link to="/admin/alerts" className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-forest hover:text-terracotta" data-testid="link-view-alerts">
              Manage alerts <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Batches</div>
              <div className="font-display text-xl font-semibold text-[#1C1C1C] mt-1">Today's schedule</div>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {BATCHES.map((b) => (
              <div key={b.id} data-testid={`batch-card-${b.id}`} className="rounded-xl border border-soft p-4 hover:border-forest transition-colors">
                <div className="text-sm font-semibold text-[#1C1C1C]">{b.name}</div>
                <div className="text-xs text-[#5C5C5C] mt-1">{b.time}</div>
                <div className="mt-3 flex items-center justify-between">
                  <Badge variant="secondary" className="bg-sage/50 text-forest border-0">{b.students} students</Badge>
                  <span className="text-xs text-forest font-medium">{b.id}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
