import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import ConfirmDialog from "@/components/ConfirmDialog";
import { ADMIN_NAV } from "@/lib/navConfig";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api, ApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { ClipboardList, Plus, Trash2 } from "lucide-react";

const ALL = "all";

function emptyForm() {
  return { class_id: "", subject_id: "", teacher_id: "" };
}

export default function AdminAssignments() {
  const [classFilter, setClassFilter] = useState(ALL);
  const [teacherFilter, setTeacherFilter] = useState(ALL);
  const filters = {
    ...(classFilter === ALL ? {} : { class_id: classFilter }),
    ...(teacherFilter === ALL ? {} : { teacher_id: teacherFilter }),
  };
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/assignments", filters);

  const [classes, setClasses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [subjects, setSubjects] = useState([]);

  const loadSubjects = () => api.get("/api/subjects?per_page=100").then((d) => setSubjects(d.items)).catch(() => toast.error("Couldn't load the subject list."));

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => toast.error("Couldn't load the class list."));
    api.get("/api/teachers?per_page=100").then((d) => setTeachers(d.items)).catch(() => toast.error("Couldn't load the teacher list."));
    loadSubjects();
  }, []);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [newSubjectOpen, setNewSubjectOpen] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [addingSubject, setAddingSubject] = useState(false);

  const openCreate = () => {
    setForm(emptyForm());
    setNewSubjectOpen(false);
    setNewSubjectName("");
    setDialogOpen(true);
  };

  const handleAddSubject = async () => {
    if (!newSubjectName.trim()) return;
    setAddingSubject(true);
    try {
      const created = await api.post("/api/subjects", { name: newSubjectName.trim() });
      toast.success("Subject added");
      await loadSubjects();
      setForm((f) => ({ ...f, subject_id: String(created.id) }));
      setNewSubjectOpen(false);
      setNewSubjectName("");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not add subject.");
    } finally {
      setAddingSubject(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/assignments", {
        class_id: Number(form.class_id),
        subject_id: Number(form.subject_id),
        teacher_id: Number(form.teacher_id),
      });
      toast.success("Assignment created");
      setDialogOpen(false);
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/api/assignments/${deleteTarget.id}`);
      toast.success("Assignment removed");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not remove this assignment.");
    }
  };

  const canSubmit = form.class_id && form.subject_id && form.teacher_id;

  return (
    <DashboardLayout
      title="Assignments"
      subtitle="Assign which teacher teaches which subject to which class."
      nav={ADMIN_NAV}
    >
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Timetable</div>
              <div className="font-display text-xl font-semibold mt-1">Class &middot; Subject &middot; Teacher</div>
            </div>
            <div className="flex items-center gap-2">
              <Select value={classFilter} onValueChange={setClassFilter}>
                <SelectTrigger className="w-[150px] border-soft">
                  <SelectValue placeholder="All classes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All classes</SelectItem>
                  {classes.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      Grade {c.grade}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={teacherFilter} onValueChange={setTeacherFilter}>
                <SelectTrigger className="w-[160px] border-soft">
                  <SelectValue placeholder="All teachers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All teachers</SelectItem>
                  {teachers.map((t) => (
                    <SelectItem key={t.id} value={String(t.id)}>
                      {t.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button data-testid="add-assignment-btn" onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
                <Plus className="w-4 h-4" /> New Assignment
              </Button>
            </div>
          </div>

          {loading && (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="text-sm text-coral py-6" data-testid="assignments-error">
              Couldn't load assignments: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <EmptyState
              icon={ClipboardList}
              title="No assignments yet"
              description="Assign a teacher to a class and subject to get started."
              action={
                <Button onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
                  <Plus className="w-4 h-4" /> New Assignment
                </Button>
              }
            />
          )}

          {!loading && !error && items.length > 0 && (
            <>
              <Table data-testid="assignments-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Class</TableHead>
                    <TableHead>Subject</TableHead>
                    <TableHead>Teacher</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((a) => (
                    <TableRow key={a.id} data-testid={`assignment-row-${a.id}`}>
                      <TableCell className="font-medium">Grade {a.grade}</TableCell>
                      <TableCell>{a.subject_name}</TableCell>
                      <TableCell>{a.teacher_name}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" data-testid={`delete-assignment-${a.id}`} onClick={() => setDeleteTarget(a)}>
                          <Trash2 className="w-4 h-4 text-coral" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
            </>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>New assignment</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="assignment-form">
            <div className="space-y-1.5">
              <Label>Class</Label>
              <Select value={form.class_id} onValueChange={(v) => setForm({ ...form, class_id: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a class" />
                </SelectTrigger>
                <SelectContent>
                  {classes.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      Grade {c.grade}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label>Subject</Label>
                <button
                  type="button"
                  data-testid="toggle-new-subject"
                  className="text-xs text-coral hover:underline font-semibold"
                  onClick={() => setNewSubjectOpen((v) => !v)}
                >
                  {newSubjectOpen ? "Cancel" : "+ New subject"}
                </button>
              </div>
              {newSubjectOpen ? (
                <div className="flex gap-2">
                  <Input
                    data-testid="new-subject-input"
                    placeholder="e.g. Mathematics"
                    value={newSubjectName}
                    onChange={(e) => setNewSubjectName(e.target.value)}
                  />
                  <Button type="button" onClick={handleAddSubject} disabled={addingSubject} className="bg-coral hover:bg-coral-deep text-ink shrink-0">
                    {addingSubject ? "Adding..." : "Add"}
                  </Button>
                </div>
              ) : (
                <Select value={form.subject_id} onValueChange={(v) => setForm({ ...form, subject_id: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder={subjects.length ? "Select a subject" : "No subjects yet -- add one"} />
                  </SelectTrigger>
                  <SelectContent>
                    {subjects.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Teacher</Label>
              <Select value={form.teacher_id} onValueChange={(v) => setForm({ ...form, teacher_id: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a teacher" />
                </SelectTrigger>
                <SelectContent>
                  {teachers.map((t) => (
                    <SelectItem key={t.id} value={String(t.id)}>
                      {t.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting || !canSubmit} className="bg-coral hover:bg-coral-deep text-ink">
                {submitting ? "Saving..." : "Create assignment"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Remove this assignment?"
        description={deleteTarget ? `${deleteTarget.teacher_name} will no longer teach ${deleteTarget.subject_name} to Grade ${deleteTarget.grade}.` : ""}
        onConfirm={handleDelete}
      />
    </DashboardLayout>
  );
}
