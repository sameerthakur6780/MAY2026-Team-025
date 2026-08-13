import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { TEACHER_NAV } from "@/lib/navConfig";
import { useAuth } from "@/context/AuthContext";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, GraduationCap, School } from "lucide-react";

const PER_PAGE_100 = { per_page: 100 };

export default function TeacherDashboard() {
  const { user } = useAuth();
  // Already scoped server-side to this teacher's assigned classes.
  const { items: classes, loading, error, refetch } = usePaginatedList("/api/classes", PER_PAGE_100);

  return (
    <DashboardLayout
      title={`Welcome, ${user?.full_name || "Teacher"}`}
      subtitle="Here's a quick look at the classes assigned to you."
      nav={TEACHER_NAV}
    >
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Your batches</div>
              <div className="font-display text-xl font-semibold mt-1">Assigned classes</div>
            </div>
          </div>

          {loading && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="teacher-classes-loading">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-[72px] w-full rounded-xl" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="text-sm text-coral py-6" data-testid="teacher-classes-error">
              Couldn't load your classes: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && classes.length === 0 && (
            <EmptyState
              icon={School}
              title="No classes yet"
              description="You don't have any classes assigned yet."
              data-testid="teacher-classes-empty"
            />
          )}

          {!loading && !error && classes.length > 0 && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="teacher-classes-list">
              {classes.map((c) => (
                <div key={c.id} className="p-4 rounded-xl border border-soft flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-sage/60 flex items-center justify-center shrink-0">
                    <GraduationCap className="w-5 h-5 text-ink" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">Grade {c.grade}</div>
                    <div className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                      <Users className="w-3 h-3" /> {c.student_count} student{c.student_count === 1 ? "" : "s"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}