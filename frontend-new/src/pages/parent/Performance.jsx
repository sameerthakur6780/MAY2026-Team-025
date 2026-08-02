import DashboardLayout from "@/components/DashboardLayout";
import { PARENT_NAV } from "@/lib/navConfig";
import { STUDENT_PERFORMANCE, HOMEWORK, UPCOMING_TESTS } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { CheckCircle2, BookOpen, CalendarCheck } from "lucide-react";

export default function ParentPerformance() {
  const avg = Math.round(STUDENT_PERFORMANCE.reduce((a, b) => a + b.score, 0) / STUDENT_PERFORMANCE.length);
  return (
    <DashboardLayout title="Performance Tracking" subtitle="Aarav's academic progress at a glance." nav={PARENT_NAV}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Average score</div>
          <div className="text-3xl font-display font-bold text-forest mt-2">{avg}%</div>
          <div className="text-xs text-forest mt-1">+7% vs last month</div>
        </CardContent></Card>
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Homework completion</div>
          <div className="text-3xl font-display font-bold text-forest mt-2">86%</div>
          <div className="text-xs text-[#5C5C5C] mt-1">AI-verified last 30 days</div>
        </CardContent></Card>
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Attendance</div>
          <div className="text-3xl font-display font-bold text-forest mt-2">94%</div>
          <div className="text-xs text-[#5C5C5C] mt-1">18 of 19 classes</div>
        </CardContent></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Test scores</div>
            <div className="font-display text-xl font-semibold mt-1 mb-4">Trend</div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={STUDENT_PERFORMANCE}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E3DC" />
                  <XAxis dataKey="test" stroke="#5C5C5C" fontSize={12} />
                  <YAxis stroke="#5C5C5C" fontSize={12} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E5E3DC", borderRadius: 8 }} />
                  <Bar dataKey="score" fill="#1E3F33" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Upcoming tests</div>
            <div className="font-display text-xl font-semibold mt-1 mb-4">This month</div>
            <div className="space-y-4">
              {UPCOMING_TESTS.map(t => (
                <div key={t.id} className="flex gap-3">
                  <div className="w-10 h-10 shrink-0 rounded-lg bg-sage/60 flex items-center justify-center">
                    <CalendarCheck className="w-5 h-5 text-forest" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">{t.subject}</div>
                    <div className="text-xs text-[#5C5C5C]">{t.date} • {t.topics}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Homework status</div>
          <div className="font-display text-xl font-semibold mt-1 mb-5">AI-verified submissions</div>
          <div className="space-y-4">
            {HOMEWORK.map(h => (
              <div key={h.id} className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-sage/60 flex items-center justify-center shrink-0"><BookOpen className="w-5 h-5 text-forest" /></div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{h.title}</div>
                  <div className="text-xs text-[#5C5C5C]">Due {h.due}</div>
                </div>
                <Badge className="bg-sage/60 text-forest border-0 gap-1"><CheckCircle2 className="w-3 h-3" /> Verified</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
