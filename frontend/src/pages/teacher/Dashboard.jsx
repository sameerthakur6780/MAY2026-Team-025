import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { TEACHER_NAV } from "@/lib/navConfig";
import { useAuth } from "@/context/AuthContext";
import { api, ApiError } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Users, GraduationCap } from "lucide-react";

export default function TeacherDashboard() {
  const { user } = useAuth();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        // Already scoped server-side to this teacher's assigned classes.
        const data = await api.get("/api/classes");
        if (!cancelled) setClasses(data.items || []);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load your classes.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

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

          {loading && <div className="text-sm text-muted-foreground" data-testid="teacher-classes-loading">Loading your classes...</div>}

          {!loading && error && (
            <div className="text-sm text-coral" data-testid="teacher-classes-error">
              {error}
            </div>
          )}

          {!loading && !error && classes.length === 0 && (
            <div className="text-sm text-muted-foreground" data-testid="teacher-classes-empty">
              You don't have any classes assigned yet.
            </div>
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
