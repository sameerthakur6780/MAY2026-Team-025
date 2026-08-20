import DashboardLayout from "@/components/DashboardLayout";
import { PARENT_NAV } from "@/lib/navConfig";
import { SAFETY_FEED } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, BookOpen, Megaphone, Wallet } from "lucide-react";

const iconMap = { attendance: CheckCircle2, homework: BookOpen, announcement: Megaphone, fee: Wallet };

export default function ParentSafety() {
  return (
    <DashboardLayout title="Safety & Notifications" subtitle="Real-time updates from your child's tutoring centre." nav={PARENT_NAV}>
      <div className="max-w-3xl space-y-3">
        {SAFETY_FEED.map((n, i) => {
          const Icon = iconMap[n.type] || CheckCircle2;
          return (
            <Card key={n.id} data-testid={`feed-${n.id}`} className="border-soft shadow-none animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
              <CardContent className="p-5 flex items-start gap-4">
                <div className={`w-11 h-11 shrink-0 rounded-xl flex items-center justify-center ${n.ok ? "bg-sage/60" : "bg-yellow/25"}`}>
                  <Icon className={`w-5 h-5 ${n.ok ? "text-ink" : "text-yellow"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-foreground">{n.message}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge className="bg-surface-2 text-muted-foreground border-0 capitalize text-[10px]">{n.type}</Badge>
                    <span className="text-xs text-muted-foreground">{n.time}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </DashboardLayout>
  );
}
