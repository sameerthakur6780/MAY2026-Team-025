import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { PARENT_NAV } from "@/lib/navConfig";
import { api, ApiError } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ClipboardList, Download, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";

async function downloadResource(resourceId) {
  const tab = window.open("", "_blank");
  try {
    const { url } = await api.get(`/api/resources/${resourceId}/download`);
    if (tab) tab.location.href = url;
    else window.open(url, "_blank");
  } catch (err) {
    tab?.close();
    toast.error(err instanceof ApiError ? err.message : "Could not download file.");
  }
}

async function downloadSubmission(submissionId) {
  const tab = window.open("", "_blank");
  try {
    const { url } = await api.get(`/api/test-submissions/${submissionId}/download`);
    if (tab) tab.location.href = url;
    else window.open(url, "_blank");
  } catch (err) {
    tab?.close();
    toast.error(err instanceof ApiError ? err.message : "Could not download response.");
  }
}

export default function ParentTests() {
  const [loading, setLoading] = useState(true);
  const [tests, setTests] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [scoresBySubmissionId, setScoresBySubmissionId] = useState({});
  const [expandedKey, setExpandedKey] = useState(null);

  useEffect(() => {
    Promise.all([api.get("/api/tests?per_page=100"), api.get("/api/test-submissions?per_page=100")])
      .then(async ([testsRes, subsRes]) => {
        setTests(testsRes.items);
        setSubmissions(subsRes.items);

        const scoreMap = {};
        await Promise.all(
          subsRes.items
            .filter((s) => s.status === "graded")
            .map(async (s) => {
              try {
                scoreMap[s.id] = await api.get(`/api/test-submissions/${s.id}/scores`);
              } catch {
                scoreMap[s.id] = null;
              }
            })
        );
        setScoresBySubmissionId(scoreMap);
      })
      .catch(() => toast.error("Couldn't load test results."))
      .finally(() => setLoading(false));
  }, []);

  const submissionByTestAndStudent = {};
  submissions.forEach((s) => {
    submissionByTestAndStudent[`${s.test_id}-${s.student_id}`] = s;
  });

  const gradedTests = tests.filter((t) => t.evaluation_status === "completed");

  return (
    <DashboardLayout title="Test Results" subtitle="View your child's test results, question papers, and submitted responses." nav={PARENT_NAV}>
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : gradedTests.length === 0 ? (
        <EmptyState icon={ClipboardList} title="No graded tests yet" description="Results will appear here after AI evaluation completes." />
      ) : (
        <div className="space-y-4">
          {gradedTests.map((t) => {
            const childSubs = submissions.filter((s) => s.test_id === t.id);
            if (childSubs.length === 0) {
              return (
                <Card key={t.id} className="border-soft shadow-none">
                  <CardContent className="p-5">
                    <div className="font-medium">{t.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">{t.subject_name} · Grade {t.grade}</div>
                    <p className="text-xs text-muted-foreground mt-2">No submission from your child.</p>
                  </CardContent>
                </Card>
              );
            }

            return childSubs.map((sub) => {
              const scores = scoresBySubmissionId[sub.id];
              const expandKey = `${t.id}-${sub.id}`;
              const isExpanded = expandedKey === expandKey;

              return (
                <Card key={expandKey} data-testid={`parent-test-${t.id}-${sub.student_id}`} className="border-soft shadow-none">
                  <CardContent className="p-5 space-y-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="font-medium text-foreground">{t.title}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {sub.student_name} · {t.subject_name} · Grade {t.grade}
                        </div>
                      </div>
                      <Badge className="bg-lime text-ink border-0">
                        {sub.marks ?? 0}/{t.max_marks}
                      </Badge>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {t.question_paper_resource_id && (
                        <Button size="sm" variant="outline" className="border-soft gap-1.5 rounded-full" onClick={() => downloadResource(t.question_paper_resource_id)}>
                          <Download className="w-3.5 h-3.5" /> Question paper
                        </Button>
                      )}
                      {sub.file_url && !sub.file_url.includes("no-response") && (
                        <Button size="sm" variant="outline" className="border-soft gap-1.5 rounded-full" onClick={() => downloadSubmission(sub.id)}>
                          <Download className="w-3.5 h-3.5" /> Student response
                        </Button>
                      )}
                      {t.answer_key_resource_id && (
                        <Button size="sm" variant="outline" className="border-soft gap-1.5 rounded-full" onClick={() => downloadResource(t.answer_key_resource_id)}>
                          <Download className="w-3.5 h-3.5" /> Answer key
                        </Button>
                      )}
                    </div>

                    {sub.feedback && (
                      <p className="text-xs text-muted-foreground">{sub.feedback}</p>
                    )}

                    {scores?.scores?.length > 0 && (
                      <div>
                        <button
                          type="button"
                          className="text-xs font-semibold text-coral inline-flex items-center gap-1"
                          onClick={() => setExpandedKey(isExpanded ? null : expandKey)}
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          {isExpanded ? "Hide" : "Show"} per-question breakdown
                        </button>
                        {isExpanded && (
                          <div className="mt-3 space-y-2 border-t border-soft pt-3">
                            {scores.scores.map((q) => (
                              <div key={q.question_no} className="text-xs rounded-lg bg-canvas p-3 border border-soft">
                                <div className="font-medium">Q{q.question_no}: {q.awarded_marks}/{q.max_marks}</div>
                                <div className="text-muted-foreground mt-0.5">{q.question_text}</div>
                                {q.feedback && <div className="text-muted-foreground mt-1">{q.feedback}</div>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            });
          })}
        </div>
      )}
    </DashboardLayout>
  );
}
