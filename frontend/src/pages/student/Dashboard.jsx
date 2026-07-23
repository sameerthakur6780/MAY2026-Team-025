import { Link } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { STUDENT_NAV } from "@/lib/navConfig";
import { TIMETABLE, UPCOMING_TESTS, HOMEWORK } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, BookOpen, CalendarCheck, ArrowRight, Sparkles } from "lucide-react";

export default function StudentDashboard() {
  return (
    <DashboardLayout title="Hey Aarav 👋" subtitle="Here's your plan for today and what's coming up." nav={STUDENT_NAV}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Your day</div>
                <div className="font-display text-xl font-semibold mt-1">Timetable</div>
              </div>
              <Badge className="bg-sage/60 text-forest border-0">Live</Badge>
            </div>
            <div className="space-y-6">
              {TIMETABLE.map((d, i) => (
                <div key={i}>
                  <div className="text-xs tracking-[0.2em] uppercase font-bold text-terracotta mb-2">{d.day}</div>
                  <div className="space-y-2">
                    {d.slots.map((s, j) => (
                      <div key={j} className="flex items-center gap-4 p-3 rounded-lg border border-soft">
                        <div className="w-14 shrink-0 text-sm font-semibold text-forest">{s.time}</div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium">{s.subject}</div>
                          <div className="text-xs text-[#5C5C5C]">{s.room}</div>
                        </div>
                        <Clock className="w-4 h-4 text-[#5C5C5C]" />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-soft shadow-none bg-forest text-white">
            <CardContent className="p-6">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center mb-4">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="font-display text-xl font-semibold leading-snug">Stuck on a concept?</div>
              <div className="text-sm text-white/70 mt-2">Chat with your EduCore AI assistant — 24/7, no waiting.</div>
              <Link to="/student/assistant" data-testid="link-ai-assistant" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-terracotta hover:gap-2 transition-all">
                Open AI chat <ArrowRight className="w-4 h-4" />
              </Link>
            </CardContent>
          </Card>

          <Card className="border-soft shadow-none">
            <CardContent className="p-6">
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Upcoming tests</div>
              <div className="font-display text-lg font-semibold mt-1 mb-4">This month</div>
              <div className="space-y-3">
                {UPCOMING_TESTS.slice(0, 3).map(t => (
                  <div key={t.id} className="flex gap-3">
                    <div className="w-9 h-9 shrink-0 rounded-lg bg-sage/60 flex items-center justify-center">
                      <CalendarCheck className="w-4 h-4 text-forest" />
                    </div>
                    <div>
                      <div className="text-sm font-medium leading-tight">{t.subject}</div>
                      <div className="text-xs text-[#5C5C5C] mt-0.5">{t.date}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Pending</div>
              <div className="font-display text-xl font-semibold mt-1">Homework due soon</div>
            </div>
            <Link to="/student/homework" className="text-sm font-medium text-terracotta hover:underline inline-flex items-center gap-1" data-testid="link-view-homework">
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {HOMEWORK.slice(0, 4).map(h => (
              <div key={h.id} className="p-4 rounded-xl border border-soft flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-sage/60 flex items-center justify-center shrink-0">
                  <BookOpen className="w-5 h-5 text-forest" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{h.title}</div>
                  <div className="text-xs text-terracotta font-semibold mt-0.5">Due {h.due}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
