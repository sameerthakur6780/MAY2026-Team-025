import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { TEACHER_NAV } from "@/lib/navConfig";
import { api, ApiError } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ClipboardCheck, Download } from "lucide-react";
import { toast } from "sonner";

export default function TeacherGrading() {
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState([]);
  const [formByKey, setFormByKey] = useState({});
  const [savingKey, setSavingKey] = useState(null);
  const [downloadingKey, setDownloadingKey] = useState(null);

  const loadQueue = () => {
    setLoading(true);
    Promise.all([
      api.get("/api/homework-submissions?status=pending&per_page=100"),
      api.get("/api/test-submissions?status=pending&per_page=100"),
      api.get("/api/homework?per_page=100"),
      api.get("/api/tests?per_page=100"),
    ])
      .then(([hwSubs, testSubs, hwList, testList]) => {
        const hwById = Object.fromEntries(hwList.items.map((h) => [h.id, h]));
        const testById = Object.fromEntries(testList.items.map((t) => [t.id, t]));

        const hwItems = hwSubs.items.map((s) => ({
          key: `hw-${s.id}`,
          kind: "homework",
          submission: s,
          title: hwById[s.homework_id]?.title || `Homework #${s.homework_id}`,
          subjectName: hwById[s.homework_id]?.subject_name,
          maxMarks: hwById[s.homework_id]?.max_marks,
        }));
        const testItems = testSubs.items.map((s) => ({
          key: `test-${s.id}`,
          kind: "test",
          submission: s,
          title: testById[s.test_id]?.title || `Test #${s.test_id}`,
          subjectName: testById[s.test_id]?.subject_name,
          maxMarks: testById[s.test_id]?.max_marks,
        }));

        setQueue(
          [...hwItems, ...testItems].sort(
            (a, b) => new Date(a.submission.submitted_at) - new Date(b.submission.submitted_at)
          )
        );
      })
      .catch(() => toast.error("Couldn't load the grading queue."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const setField = (key, field, value) => {
    setFormByKey((prev) => ({ ...prev, [key]: { ...prev[key], [field]: value } }));
  };

  const handleDownload = async (item) => {
    const path = item.kind === "homework"
      ? `/api/homework-submissions/${item.submission.id}/download`
      : `/api/test-submissions/${item.submission.id}/download`;
    const tab = window.open("", "_blank");
    setDownloadingKey(item.key);
    try {
      const { url } = await api.get(path);
      if (tab) {
        tab.location.href = url;
      } else {
        window.open(url, "_blank");
      }
    } catch (err) {
      tab?.close();
      toast.error(err instanceof ApiError ? err.message : "Could not generate a download link.");
    } finally {
      setDownloadingKey(null);
    }
  };

  const handleSave = async (item) => {
    const values = formByKey[item.key] || {};
    const marks = Number(values.marks);
    if (values.marks === undefined || values.marks === "" || Number.isNaN(marks)) {
      return toast.error("Please enter marks");
    }
    if (item.maxMarks && marks > item.maxMarks) {
      return toast.error(`Marks can't exceed ${item.maxMarks}`);
    }
    const path = item.kind === "homework"
      ? `/api/homework-submissions/${item.submission.id}/grade`
      : `/api/test-submissions/${item.submission.id}/grade`;
    setSavingKey(item.key);
    try {
      await api.patch(path, { marks, feedback: values.feedback || null });
      toast.success(`${item.submission.student_name} graded`);
      setQueue((prev) => prev.filter((q) => q.key !== item.key));
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not save this grade.");
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <DashboardLayout title="Grading" subtitle="Review submitted homework and tests, then enter marks." nav={TEACHER_NAV}>
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : queue.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="Nothing to grade" description="Every submitted homework and test has been graded." />
      ) : (
        <div className="space-y-4">
          {queue.map((item) => {
            const values = formByKey[item.key] || {};
            return (
              <Card key={item.key} data-testid={`grade-${item.key}`} className="border-soft shadow-none">
                <CardContent className="p-5">
                  <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                    <div>
                      <Badge className="bg-surface-2 text-muted-foreground border-0 capitalize mb-1.5">{item.kind}</Badge>
                      <div className="font-medium text-foreground">{item.title}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">
                        {item.submission.student_name} &middot; {item.subjectName} &middot; submitted{" "}
                        {new Date(item.submission.submitted_at).toLocaleDateString()}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 border-soft"
                      disabled={downloadingKey === item.key}
                      onClick={() => handleDownload(item)}
                      data-testid={`download-${item.key}`}
                    >
                      <Download className="w-3.5 h-3.5" /> {downloadingKey === item.key ? "Opening…" : "View submission"}
                    </Button>
                  </div>
                  <div className="flex flex-wrap items-end gap-3">
                    <div className="w-28">
                      <Input
                        type="number"
                        min="0"
                        max={item.maxMarks || undefined}
                        placeholder={item.maxMarks ? `/ ${item.maxMarks}` : "Marks"}
                        value={values.marks ?? ""}
                        onChange={(e) => setField(item.key, "marks", e.target.value)}
                        data-testid={`marks-${item.key}`}
                      />
                    </div>
                    <div className="flex-1 min-w-[200px]">
                      <Input
                        placeholder="Feedback (optional)"
                        value={values.feedback ?? ""}
                        onChange={(e) => setField(item.key, "feedback", e.target.value)}
                        data-testid={`feedback-${item.key}`}
                      />
                    </div>
                    <Button
                      disabled={savingKey === item.key}
                      onClick={() => handleSave(item)}
                      className="bg-coral hover:bg-coral-deep text-ink"
                      data-testid={`save-grade-${item.key}`}
                    >
                      {savingKey === item.key ? "Saving…" : "Save grade"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </DashboardLayout>
  );
}
