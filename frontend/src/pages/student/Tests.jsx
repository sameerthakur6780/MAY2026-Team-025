import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { STUDENT_NAV } from "@/lib/navConfig";
import { api, ApiError } from "@/lib/apiClient";
import { formatDateTime } from "@/lib/utils";
import { uploadWithProgress } from "@/lib/uploadWithProgress";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Upload, ClipboardList, CheckCircle2, Clock, Download, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";

const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024;

function validateFile(file) {
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
    return `File type .${ext || "?"} isn't allowed. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
  }
  if (file.size > MAX_SIZE_BYTES) {
    return `File exceeds the ${MAX_SIZE_BYTES / (1024 * 1024)}MB size limit`;
  }
  if (file.size === 0) {
    return "File is empty";
  }
  return null;
}

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

export default function StudentTests() {
  const [loading, setLoading] = useState(true);
  const [tests, setTests] = useState([]);
  const [submissionByTestId, setSubmissionByTestId] = useState({});
  const [scoresBySubmissionId, setScoresBySubmissionId] = useState({});
  const [expandedId, setExpandedId] = useState(null);

  const [dialogTest, setDialogTest] = useState(null);
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  const loadAll = () => {
    setLoading(true);
    Promise.all([api.get("/api/tests?per_page=100"), api.get("/api/test-submissions?per_page=100")])
      .then(async ([testsRes, subRes]) => {
        setTests(testsRes.items);
        const map = {};
        subRes.items.forEach((s) => {
          map[s.test_id] = s;
        });
        setSubmissionByTestId(map);

        const scoreMap = {};
        await Promise.all(
          subRes.items
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
      .catch(() => toast.error("Couldn't load your tests."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAll();
  }, []);

  const pending = tests.filter((t) => !submissionByTestId[t.id]);
  const submitted = tests.filter((t) => submissionByTestId[t.id]);

  const openDialog = (test) => {
    setDialogTest(test);
    setFile(null);
    setFileError("");
  };

  const closeDialog = () => {
    setDialogTest(null);
    setFile(null);
    setFileError("");
  };

  const handleFileChange = (e) => {
    const picked = e.target.files?.[0];
    if (!picked) {
      setFile(null);
      setFileError("");
      return;
    }
    const err = validateFile(picked);
    setFileError(err || "");
    setFile(err ? null : picked);
  };

  const handleSubmit = async () => {
    if (!file) return toast.error("Please attach your response PDF");
    const formData = new FormData();
    formData.append("file", file);

    setSubmitting(true);
    setProgress(0);
    try {
      await uploadWithProgress(`/api/tests/${dialogTest.id}/submissions`, formData, setProgress);
      toast.success("Test response submitted");
      closeDialog();
      loadAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not submit response.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderTestCard = (t) => {
    const submission = submissionByTestId[t.id];
    const scores = submission ? scoresBySubmissionId[submission.id] : null;
    const isExpanded = expandedId === t.id;

    return (
      <Card key={t.id} data-testid={`stud-test-${t.id}`} className="border-soft shadow-none">
        <CardContent className="p-5 space-y-3">
          <div className="flex flex-wrap items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-sage/60 flex items-center justify-center shrink-0">
              <ClipboardList className="w-5 h-5 text-ink" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-foreground">{t.title}</div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {t.subject_name} &middot; Due {formatDateTime(t.due_date)} &middot; {t.max_marks} marks
              </div>
              {submission && (
                <div className="text-xs text-lime mt-1 inline-flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Submitted {new Date(submission.submitted_at).toLocaleDateString()}
                </div>
              )}
            </div>
            {submission ? (
              <Badge className={submission.status === "graded" ? "bg-lime text-ink border-0" : "bg-surface-2 text-muted-foreground border-0"}>
                {submission.status === "graded" ? `Graded: ${submission.marks}/${t.max_marks}` : "Awaiting evaluation"}
              </Badge>
            ) : new Date(t.due_date) < new Date() ? (
              <Badge className="bg-surface-2 text-muted-foreground border-0">Past due</Badge>
            ) : (
              <Button
                data-testid={`submit-test-${t.id}`}
                onClick={() => openDialog(t)}
                className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-full"
              >
                <Upload className="w-4 h-4" /> Upload response
              </Button>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            {t.question_paper_resource_id && (
              <Button size="sm" variant="outline" className="border-soft gap-1.5 rounded-full" onClick={() => downloadResource(t.question_paper_resource_id)}>
                <Download className="w-3.5 h-3.5" /> Question paper
              </Button>
            )}
            {t.evaluation_status === "completed" && t.answer_key_resource_id && (
              <Button size="sm" variant="outline" className="border-soft gap-1.5 rounded-full" onClick={() => downloadResource(t.answer_key_resource_id)}>
                <Download className="w-3.5 h-3.5" /> Answer key
              </Button>
            )}
          </div>

          {submission?.status === "graded" && scores?.scores?.length > 0 && (
            <div>
              <button
                type="button"
                className="text-xs font-semibold text-coral inline-flex items-center gap-1"
                onClick={() => setExpandedId(isExpanded ? null : t.id)}
              >
                {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {isExpanded ? "Hide" : "Show"} per-question feedback
              </button>
              {isExpanded && (
                <div className="mt-3 space-y-2 border-t border-soft pt-3">
                  {scores.scores.map((q) => (
                    <div key={q.question_no} className="text-xs rounded-lg bg-canvas p-3 border border-soft">
                      <div className="font-medium">Q{q.question_no}: {q.awarded_marks}/{q.max_marks}</div>
                      {q.feedback && <div className="text-muted-foreground mt-1">{q.feedback}</div>}
                    </div>
                  ))}
                  {submission.feedback && (
                    <div className="text-xs text-muted-foreground italic">{submission.feedback}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <DashboardLayout title="Tests" subtitle="Download question papers and upload your responses as PDF." nav={STUDENT_NAV}>
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
            <Card className="border-soft shadow-none bg-yellow/15">
              <CardContent className="p-5 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-yellow/30 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-yellow" />
                </div>
                <div>
                  <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Pending</div>
                  <div className="text-2xl font-display font-bold text-yellow">{pending.length}</div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-soft shadow-none bg-sage/30">
              <CardContent className="p-5 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-sage/70 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-ink" />
                </div>
                <div>
                  <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Submitted</div>
                  <div className="text-2xl font-display font-bold text-lime">{submitted.length}</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {tests.length === 0 ? (
            <EmptyState icon={ClipboardList} title="No tests yet" description="Nothing has been assigned to your class yet." />
          ) : (
            <div className="space-y-4">{tests.map(renderTestCard)}</div>
          )}
        </>
      )}

      <Dialog open={!!dialogTest} onOpenChange={(o) => !o && closeDialog()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-display">Submit: {dialogTest?.title}</DialogTitle>
          </DialogHeader>
          <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-8 text-center hover:border-coral bg-canvas mt-2">
            <input type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt" className="hidden" onChange={handleFileChange} />
            <Upload className="w-8 h-8 mx-auto text-coral mb-3" />
            <div className="text-sm font-medium">{file ? file.name : "Click to upload your response"}</div>
            <div className="text-xs text-muted-foreground mt-1">PDF recommended, up to 20MB</div>
          </label>
          {fileError && <p className="text-xs text-coral mt-2">{fileError}</p>}
          {submitting && <div className="text-xs text-muted-foreground mt-2">Uploading… {progress}%</div>}
          <Button disabled={submitting || !file} onClick={handleSubmit} className="w-full bg-coral hover:bg-coral-deep text-ink mt-2">
            {submitting ? "Submitting…" : "Submit response"}
          </Button>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
