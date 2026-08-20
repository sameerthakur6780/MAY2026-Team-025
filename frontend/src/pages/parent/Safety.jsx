import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import { PARENT_NAV } from "@/lib/navConfig";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Bell, CalendarClock, BookOpen, Megaphone, Wallet } from "lucide-react";

const ICON_BY_TYPE = {
  attendance_absent: CalendarClock,
  homework_assigned: BookOpen,
  marks_published: BookOpen,
  fee_due_reminder: Wallet,
  payment_received: Wallet,
  announcement: Megaphone,
};

// Which notification types represent something that needs the parent's
// attention (styled amber) vs. routine/good-news updates (styled sage) --
// there's no such flag from the backend, it's derived from the type itself.
const NEEDS_ATTENTION = new Set(["attendance_absent", "fee_due_reminder"]);

function formatWhen(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function ParentSafety() {
  const { items, loading, error, page, pages, total, setPage, refetch } = usePaginatedList("/api/notifications");

  return (
    <DashboardLayout title="Safety & Notifications" subtitle="Real-time updates from your child's tutoring centre." nav={PARENT_NAV}>
      <div className="max-w-3xl space-y-3">
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-xl" />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="text-sm text-coral py-6" data-testid="safety-feed-error">
            Couldn't load notifications: {error}{" "}
            <button className="underline font-semibold" onClick={refetch}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <EmptyState
            icon={Bell}
            title="No notifications yet"
            description="Updates about attendance, fees, homework, and announcements will show up here."
          />
        )}

        {!loading && !error && items.map((n, i) => {
          const Icon = ICON_BY_TYPE[n.type] || Bell;
          const attention = NEEDS_ATTENTION.has(n.type);
          return (
            <Card
              key={n.id}
              data-testid={`feed-${n.id}`}
              className="border-soft shadow-none animate-fade-in-up"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <CardContent className="p-5 flex items-start gap-4">
                <div className={`w-11 h-11 shrink-0 rounded-xl flex items-center justify-center ${attention ? "bg-yellow/25" : "bg-sage/60"}`}>
                  <Icon className={`w-5 h-5 ${attention ? "text-yellow" : "text-ink"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-foreground">{n.subject}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge className="bg-surface-2 text-muted-foreground border-0 capitalize text-[10px]">
                      {n.type.replace(/_/g, " ")}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{formatWhen(n.sent_at || n.created_at)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}

        {!loading && !error && items.length > 0 && (
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        )}
      </div>
    </DashboardLayout>
  );
}
