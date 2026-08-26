import { useEffect, useState } from "react";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/apiClient";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ClipboardList } from "lucide-react";

const STATUS_LABELS = {
  not_scheduled: { label: "Not scheduled", className: "bg-surface-2 text-muted-foreground border-0" },
  scheduled: { label: "Scheduled", className: "bg-yellow/20 text-yellow border-0" },
  running: { label: "Running", className: "bg-coral/20 text-coral border-0" },
  completed: { label: "Completed", className: "bg-lime text-ink border-0" },
  failed: { label: "Failed", className: "bg-coral text-ink border-0" },
};

export default function TestsReadOnlyView() {
  const [loading, setLoading] = useState(true);
  const [tests, setTests] = useState([]);
  const [submissionCountByTestId, setSubmissionCountByTestId] = useState({});
  const [evalByTestId, setEvalByTestId] = useState({});

  const loadAll = () => {
    setLoading(true);
    Promise.all([api.get("/api/tests?per_page=100"), api.get("/api/test-submissions?per_page=100")])
      .then(async ([testsRes, subsRes]) => {
        setTests(testsRes.items);
        const counts = {};
        subsRes.items.forEach((s) => {
          counts[s.test_id] = (counts[s.test_id] || 0) + 1;
        });
        setSubmissionCountByTestId(counts);

        const evalMap = {};
        await Promise.all(
          testsRes.items.map(async (t) => {
            try {
              evalMap[t.id] = await api.get(`/api/tests/${t.id}/evaluation`);
            } catch {
              evalMap[t.id] = null;
            }
          })
        );
        setEvalByTestId(evalMap);
      })
      .catch(() => toast.error("Couldn't load tests."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    const running = tests.some((t) => t.evaluation_status === "running");
    if (!running) return undefined;
    const timer = setInterval(loadAll, 5000);
    return () => clearInterval(timer);
  }, [tests]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-36 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (tests.length === 0) {
    return <EmptyState icon={ClipboardList} title="No tests yet" description="Tests created by teachers will show up here." />;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {tests.map((t) => {
        const status = STATUS_LABELS[t.evaluation_status] || STATUS_LABELS.not_scheduled;
        const evalInfo = evalByTestId[t.id];
        return (
          <Card key={t.id} data-testid={`test-card-${t.id}`} className="border-soft shadow-none">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium text-foreground">{t.title}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Grade {t.grade} &middot; {t.subject_name} &middot; Due {t.due_date}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">By {t.creator_name}</div>
                </div>
                <Badge className={status.className}>{status.label}</Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                {submissionCountByTestId[t.id] || 0} submission(s)
                {evalInfo ? ` · ${evalInfo.graded_count}/${evalInfo.total_students} graded` : ""}
              </div>
              {t.evaluation_error && <p className="text-xs text-coral">{t.evaluation_error}</p>}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
