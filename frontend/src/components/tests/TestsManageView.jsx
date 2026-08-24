import { useEffect, useRef, useState } from "react";
import EmptyState from "@/components/EmptyState";
import { api, ApiError } from "@/lib/apiClient";
import { uploadWithProgress } from "@/lib/uploadWithProgress";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, ClipboardList, Upload, Play, CalendarClock } from "lucide-react";

const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024;

const STATUS_LABELS = {
  not_scheduled: { label: "Not scheduled", className: "bg-surface-2 text-muted-foreground border-0" },
  scheduled: { label: "Scheduled", className: "bg-yellow/20 text-yellow border-0" },
  running: { label: "Running", className: "bg-coral/20 text-coral border-0" },
  completed: { label: "Completed", className: "bg-lime text-ink border-0" },
  failed: { label: "Failed", className: "bg-coral text-ink border-0" },
};

function emptyForm() {
  return {
    class_id: "",
    subject_id: "",
    title: "",
    due_date: "",
    description: "",
    max_marks: "100",
  };
}

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

function toLocalDatetimeValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

async function uploadResource(file, type, classId, subjectId) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", type);
  formData.append("class_id", String(classId));
  formData.append("subject_id", String(subjectId));
  return uploadWithProgress("/api/resources", formData, () => {});
}

export default function TestsManageView() {
  const [loading, setLoading] = useState(true);
  const [tests, setTests] = useState([]);
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [submissionCountByTestId, setSubmissionCountByTestId] = useState({});
  const [evalByTestId, setEvalByTestId] = useState({});

  const [dialog, setDialog] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [questionPaper, setQuestionPaper] = useState(null);
  const [answerKey, setAnswerKey] = useState(null);
  const [qpError, setQpError] = useState("");
  const [akError, setAkError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [scheduleTestId, setScheduleTestId] = useState(null);
  const [scheduleAt, setScheduleAt] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [runningId, setRunningId] = useState(null);

  const qpRef = useRef(null);
  const akRef = useRef(null);

  const loadAll = () => {
    setLoading(true);
    Promise.all([
      api.get("/api/tests?per_page=100"),
      api.get("/api/classes?per_page=100"),
      api.get("/api/subjects?per_page=100"),
      api.get("/api/test-submissions?per_page=100"),
    ])
      .then(async ([testsRes, classesRes, subjectsRes, subsRes]) => {
        setTests(testsRes.items);
        setClasses(classesRes.items);
        setSubjects(subjectsRes.items);
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

  const resetCreateDialog = () => {
    setForm(emptyForm());
    setQuestionPaper(null);
    setAnswerKey(null);
    setQpError("");
    setAkError("");
  };

  const handleFilePick = (setter, setError) => (e) => {
    const picked = e.target.files?.[0];
    if (!picked) {
      setter(null);
      setError("");
      return;
    }
    const err = validateFile(picked);
    setError(err || "");
    setter(err ? null : picked);
  };

  const createTest = async () => {
    if (!form.class_id || !form.subject_id || !form.title || !form.due_date || !form.max_marks) {
      return toast.error("Please fill all required fields");
    }
    if (!questionPaper) return toast.error("Please upload the question paper");
    if (!answerKey) return toast.error("Please upload the answer key");

    setSubmitting(true);
    try {
      const classId = Number(form.class_id);
      const subjectId = Number(form.subject_id);
      const qpResource = await uploadResource(questionPaper, "question_paper", classId, subjectId);
      const akResource = await uploadResource(answerKey, "answer_key", classId, subjectId);

      await api.post("/api/tests", {
        class_id: classId,
        subject_id: subjectId,
        title: form.title,
        description: form.description || null,
        due_date: form.due_date,
        max_marks: Number(form.max_marks),
        question_paper_resource_id: qpResource.id,
        answer_key_resource_id: akResource.id,
      });

      toast.success("Test created with question paper and answer key");
      resetCreateDialog();
      setDialog(false);
      loadAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not create test.");
    } finally {
      setSubmitting(false);
    }
  };

  const scheduleEvaluation = async () => {
    if (!scheduleAt) return toast.error("Pick a date and time");
    setScheduling(true);
    try {
      const scheduledAt = new Date(scheduleAt).toISOString();
      await api.post(`/api/tests/${scheduleTestId}/evaluation`, { scheduled_at: scheduledAt });
      toast.success("AI evaluation scheduled");
      setScheduleTestId(null);
      setScheduleAt("");
      loadAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not schedule evaluation.");
    } finally {
      setScheduling(false);
    }
  };

  const runNow = async (testId) => {
    setRunningId(testId);
    try {
      await api.post(`/api/tests/${testId}/evaluation/run`);
      toast.success("AI evaluation started");
      loadAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not start evaluation.");
    } finally {
      setRunningId(null);
    }
  };

  const openSchedule = (testId) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    setScheduleAt(toLocalDatetimeValue(tomorrow));
    setScheduleTestId(testId);
  };

  return (
    <>
      <div className="flex justify-end mb-6">
        <Dialog open={dialog} onOpenChange={(o) => { setDialog(o); if (!o) resetCreateDialog(); }}>
          <DialogTrigger asChild>
            <Button data-testid="create-test-btn" className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-full">
              <Plus className="w-4 h-4" /> Create test
            </Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle className="font-display">New test</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <div className="space-y-1.5">
                <Label>Title</Label>
                <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Unit test — Algebra" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Class</Label>
                  <Select value={form.class_id} onValueChange={(v) => setForm({ ...form, class_id: v })}>
                    <SelectTrigger className="border-soft"><SelectValue placeholder="Select class" /></SelectTrigger>
                    <SelectContent>
                      {classes.map((c) => <SelectItem key={c.id} value={String(c.id)}>Grade {c.grade}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Subject</Label>
                  <Select value={form.subject_id} onValueChange={(v) => setForm({ ...form, subject_id: v })}>
                    <SelectTrigger className="border-soft"><SelectValue placeholder="Select subject" /></SelectTrigger>
                    <SelectContent>
                      {subjects.map((s) => <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Due date</Label>
                  <Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <Label>Max marks</Label>
                  <Input type="number" min="1" value={form.max_marks} onChange={(e) => setForm({ ...form, max_marks: e.target.value })} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Description (optional)</Label>
                <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Instructions for students…" />
              </div>
              <div className="space-y-1.5">
                <Label>Question paper (PDF)</Label>
                <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-4 text-center hover:border-coral bg-canvas">
                  <input ref={qpRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt" className="hidden" onChange={handleFilePick(setQuestionPaper, setQpError)} />
                  <Upload className="w-5 h-5 mx-auto text-coral mb-1" />
                  <div className="text-xs">{questionPaper ? questionPaper.name : "Upload question paper"}</div>
                </label>
                {qpError && <p className="text-xs text-coral">{qpError}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Answer key (PDF)</Label>
                <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-4 text-center hover:border-coral bg-canvas">
                  <input ref={akRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt" className="hidden" onChange={handleFilePick(setAnswerKey, setAkError)} />
                  <Upload className="w-5 h-5 mx-auto text-coral mb-1" />
                  <div className="text-xs">{answerKey ? answerKey.name : "Upload answer key"}</div>
                </label>
                {akError && <p className="text-xs text-coral">{akError}</p>}
              </div>
              <Button disabled={submitting} onClick={createTest} className="w-full bg-coral hover:bg-coral-deep text-ink">
                {submitting ? "Creating…" : "Publish test"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-36 w-full rounded-xl" />)}
        </div>
      ) : tests.length === 0 ? (
        <EmptyState icon={ClipboardList} title="No tests yet" description="Create a test with a question paper and answer key to get started." />
      ) : (
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
                    </div>
                    <Badge className={status.className}>{status.label}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {submissionCountByTestId[t.id] || 0} submission(s)
                    {evalInfo ? ` · ${evalInfo.graded_count}/${evalInfo.total_students} graded` : ""}
                  </div>
                  {t.evaluation_error && (
                    <p className="text-xs text-coral">{t.evaluation_error}</p>
                  )}
                  {t.evaluation_status !== "running" && t.evaluation_status !== "completed" && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-soft gap-1.5 rounded-full"
                        onClick={() => openSchedule(t.id)}
                        disabled={!t.answer_key_resource_id}
                      >
                        <CalendarClock className="w-3.5 h-3.5" /> Schedule
                      </Button>
                      <Button
                        size="sm"
                        className="bg-coral hover:bg-coral-deep text-ink gap-1.5 rounded-full"
                        onClick={() => runNow(t.id)}
                        disabled={!t.answer_key_resource_id || runningId === t.id}
                      >
                        <Play className="w-3.5 h-3.5" /> {runningId === t.id ? "Starting…" : "Run now"}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Dialog open={scheduleTestId !== null} onOpenChange={(o) => !o && setScheduleTestId(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle className="font-display">Schedule AI evaluation</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-2">
            <div className="space-y-1.5">
              <Label>Evaluation date & time</Label>
              <Input type="datetime-local" value={scheduleAt} onChange={(e) => setScheduleAt(e.target.value)} />
            </div>
            <Button disabled={scheduling} onClick={scheduleEvaluation} className="w-full bg-coral hover:bg-coral-deep text-ink">
              {scheduling ? "Scheduling…" : "Schedule evaluation"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
