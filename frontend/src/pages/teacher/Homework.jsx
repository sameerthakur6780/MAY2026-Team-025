import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { TEACHER_NAV } from "@/lib/navConfig";
import { api, ApiError } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, BookOpen, Users } from "lucide-react";
import { toast } from "sonner";

function emptyForm() {
  return { class_id: "", subject_id: "", title: "", due_date: "", description: "", max_marks: "100" };
}

export default function TeacherHomework() {
  const [loading, setLoading] = useState(true);
  const [homework, setHomework] = useState([]);
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [submissionCountByHwId, setSubmissionCountByHwId] = useState({});

  const [dialog, setDialog] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);

  const loadAll = () => {
    setLoading(true);
    Promise.all([
      api.get("/api/homework?per_page=100"),
      api.get("/api/classes?per_page=100"),
      api.get("/api/subjects?per_page=100"),
      api.get("/api/homework-submissions?per_page=100"),
    ])
      .then(([hwRes, classesRes, subjectsRes, subsRes]) => {
        setHomework(hwRes.items);
        setClasses(classesRes.items);
        setSubjects(subjectsRes.items);
        const counts = {};
        subsRes.items.forEach((s) => {
          counts[s.homework_id] = (counts[s.homework_id] || 0) + 1;
        });
        setSubmissionCountByHwId(counts);
      })
      .catch(() => toast.error("Couldn't load homework."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAll();
  }, []);

  const classById = (id) => classes.find((c) => c.id === id);

  const assign = async () => {
    if (!form.class_id || !form.subject_id || !form.title || !form.due_date || !form.max_marks) {
      return toast.error("Please fill all required fields");
    }
    setSubmitting(true);
    try {
      await api.post("/api/homework", {
        class_id: Number(form.class_id),
        subject_id: Number(form.subject_id),
        title: form.title,
        description: form.description || null,
        due_date: form.due_date,
        max_marks: Number(form.max_marks),
      });
      toast.success("Homework assigned to class");
      setForm(emptyForm());
      setDialog(false);
      loadAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not assign homework.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="Homework Assignment" subtitle="Assign homework to a class and track submissions." nav={TEACHER_NAV}>
      <div className="flex justify-end mb-6">
        <Dialog open={dialog} onOpenChange={setDialog}>
          <DialogTrigger asChild>
            <Button data-testid="assign-hw-btn" className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-full">
              <Plus className="w-4 h-4" /> Assign homework
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle className="font-display">New homework</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <div className="space-y-1.5">
                <Label>Title</Label>
                <Input data-testid="hw-title-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Ch 8 — Numerical set" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Class</Label>
                  <Select value={form.class_id} onValueChange={(v) => setForm({ ...form, class_id: v })}>
                    <SelectTrigger data-testid="hw-class-select" className="border-soft"><SelectValue placeholder="Select class" /></SelectTrigger>
                    <SelectContent>
                      {classes.map((c) => <SelectItem key={c.id} value={String(c.id)}>Grade {c.grade}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Subject</Label>
                  <Select value={form.subject_id} onValueChange={(v) => setForm({ ...form, subject_id: v })}>
                    <SelectTrigger data-testid="hw-subject-select" className="border-soft"><SelectValue placeholder="Select subject" /></SelectTrigger>
                    <SelectContent>
                      {subjects.map((s) => <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Due date</Label>
                  <Input data-testid="hw-due-input" type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <Label>Max marks</Label>
                  <Input data-testid="hw-max-marks-input" type="number" min="1" value={form.max_marks} onChange={(e) => setForm({ ...form, max_marks: e.target.value })} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Description (optional)</Label>
                <Textarea data-testid="hw-desc-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Detailed instructions…" />
              </div>
              <Button data-testid="submit-hw-btn" disabled={submitting} onClick={assign} className="w-full bg-coral hover:bg-coral-deep text-ink">
                {submitting ? "Assigning…" : "Assign to class"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-36 w-full rounded-xl" />)}
        </div>
      ) : homework.length === 0 ? (
        <EmptyState icon={BookOpen} title="No homework assigned yet" description="Assign your first homework to a class to get started." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {homework.map((h, i) => {
            const school_class = classById(h.class_id);
            const assigned = school_class?.student_count || 0;
            const submitted = submissionCountByHwId[h.id] || 0;
            const pct = assigned ? Math.round((submitted / assigned) * 100) : 0;
            return (
              <Card key={h.id} data-testid={`hw-${h.id}`} className="border-soft shadow-none animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <BookOpen className="w-3.5 h-3.5" /> Grade {h.grade} &middot; {h.subject_name}
                      </div>
                      <div className="font-display text-lg font-semibold text-foreground mt-1">{h.title}</div>
                      <div className="text-xs text-yellow mt-1 font-semibold">Due {h.due_date}</div>
                    </div>
                    <div className="text-xs text-coral inline-flex items-center gap-1.5 shrink-0">
                      <Users className="w-3.5 h-3.5" /> {assigned}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                    <span>{submitted} of {assigned} submitted</span>
                    <span className="font-semibold text-coral">{pct}%</span>
                  </div>
                  <Progress value={pct} className="h-2 bg-surface-2" />
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </DashboardLayout>
  );
}
