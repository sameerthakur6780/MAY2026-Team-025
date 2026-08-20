import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { STUDENT_NAV } from "@/lib/navConfig";
import { api, ApiError } from "@/lib/apiClient";
import { uploadWithProgress } from "@/lib/uploadWithProgress";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Upload, BookOpen, CheckCircle2, Clock } from "lucide-react";
import { toast } from "sonner";

// Mirrors backend/config.py's ALLOWED_UPLOAD_EXTENSIONS / MAX_UPLOAD_SIZE_BYTES
// -- same convention as ResourcesManageView.jsx. Fast client-side check only;
// the server re-validates and is the real authority.
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

export default function StudentHomework() {
  const [loading, setLoading] = useState(true);
  const [homework, setHomework] = useState([]);
  const [submissionByHwId, setSubmissionByHwId] = useState({});

  const [dialogHw, setDialogHw] = useState(null);
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  const loadAll = () => {
    setLoading(true);
    Promise.all([api.get("/api/homework?per_page=100"), api.get("/api/homework-submissions?per_page=100")])
      .then(([hwRes, subRes]) => {
        setHomework(hwRes.items);
        const map = {};
        subRes.items.forEach((s) => {
          map[s.homework_id] = s;
        });
        setSubmissionByHwId(map);
      })
      .catch(() => toast.error("Couldn't load your homework."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAll();
  }, []);

  const pending = homework.filter((h) => !submissionByHwId[h.id]);
  const submitted = homework.filter((h) => submissionByHwId[h.id]);

  const openDialog = (hw) => {
    setDialogHw(hw);
    setFile(null);
    setFileError("");
  };

  const closeDialog = () => {
    setDialogHw(null);
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
    if (!file) return toast.error("Please attach your homework file");
    const formData = new FormData();
    formData.append("file", file);

    setSubmitting(true);
    setProgress(0);
    try {
      await uploadWithProgress(`/api/homework/${dialogHw.id}/submissions`, formData, setProgress);
      toast.success("Homework submitted");
      closeDialog();
      loadAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not submit homework.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="My Homework" subtitle="Submit your completed homework for your tutor to review." nav={STUDENT_NAV}>
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

          {homework.length === 0 ? (
            <EmptyState icon={BookOpen} title="No homework yet" description="Nothing has been assigned to your class yet." />
          ) : (
            <div className="space-y-4">
              {homework.map((h) => {
                const submission = submissionByHwId[h.id];
                return (
                  <Card key={h.id} data-testid={`stud-hw-${h.id}`} className="border-soft shadow-none">
                    <CardContent className="p-5 flex flex-wrap items-center gap-4">
                      <div className="w-11 h-11 rounded-xl bg-sage/60 flex items-center justify-center shrink-0">
                        <BookOpen className="w-5 h-5 text-ink" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-foreground">{h.title}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {h.subject_name} &middot; Due {h.due_date}
                        </div>
                        {submission && (
                          <div className="text-xs text-lime mt-1 inline-flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Submitted {new Date(submission.submitted_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      {submission ? (
                        <Badge className={submission.status === "graded" ? "bg-lime text-ink border-0" : "bg-surface-2 text-muted-foreground border-0"}>
                          {submission.status === "graded" ? `Graded: ${submission.marks}/${h.max_marks}` : "Awaiting review"}
                        </Badge>
                      ) : (
                        <Button
                          data-testid={`submit-hw-${h.id}`}
                          onClick={() => openDialog(h)}
                          className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-full"
                        >
                          <Upload className="w-4 h-4" /> Submit
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}

      <Dialog open={!!dialogHw} onOpenChange={(o) => !o && closeDialog()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-display">Submit: {dialogHw?.title}</DialogTitle>
          </DialogHeader>
          <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-8 text-center hover:border-coral bg-canvas mt-2">
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt"
              className="hidden"
              data-testid="hw-file-input"
              onChange={handleFileChange}
            />
            <Upload className="w-8 h-8 mx-auto text-coral mb-3" />
            <div className="text-sm font-medium">{file ? file.name : "Click to upload homework"}</div>
            <div className="text-xs text-muted-foreground mt-1">PDF, image, or Word doc, up to 20MB</div>
          </label>
          {fileError && <p className="text-xs text-coral mt-2">{fileError}</p>}
          {submitting && <div className="text-xs text-muted-foreground mt-2">Uploading… {progress}%</div>}
          <Button
            data-testid="submit-hw-confirm"
            disabled={submitting || !file}
            onClick={handleSubmit}
            className="w-full bg-coral hover:bg-coral-deep text-ink mt-2"
          >
            {submitting ? "Submitting…" : "Submit for review"}
          </Button>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
