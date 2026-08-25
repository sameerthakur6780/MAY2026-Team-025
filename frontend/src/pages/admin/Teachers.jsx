import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import ConfirmDialog from "@/components/ConfirmDialog";
import MultiSelect from "@/components/ui/multi-select";
import { ADMIN_NAV } from "@/lib/navConfig";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api, ApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Presentation, Plus, Pencil, Trash2 } from "lucide-react";

const NONE = "none";

function emptyForm() {
  return { full_name: "", email: "", password: "", phone: "", subject_id: NONE, class_ids: [] };
}

export default function AdminTeachers() {
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/teachers");
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [teacherAssignments, setTeacherAssignments] = useState([]);

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => toast.error("Couldn't load the class list."));
    api.get("/api/subjects?per_page=100").then((d) => setSubjects(d.items)).catch(() => toast.error("Couldn't load the subject list."));
  }, []);

  const gradeFor = (classId) => classes.find((c) => c.id === classId)?.grade;
  const classOptions = classes.map((c) => ({ value: c.id, label: `Grade ${c.grade}` }));

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const openCreate = () => {
    setEditing(null);
    setTeacherAssignments([]);
    setForm(emptyForm());
    setDialogOpen(true);
  };

  const openEdit = async (teacher) => {
    setEditing(teacher);
    setForm({
      full_name: teacher.full_name,
      email: teacher.email,
      password: "",
      phone: teacher.phone || "",
      subject_id: NONE,
      class_ids: [],
    });
    setDialogOpen(true);

    try {
      const data = await api.get(`/api/assignments?teacher_id=${teacher.id}&per_page=100`);
      setTeacherAssignments(data.items);
      const subjectIds = [...new Set(data.items.map((a) => a.subject_id))];
      if (subjectIds.length === 1) {
        const subjectId = String(subjectIds[0]);
        const classIds = data.items.filter((a) => a.subject_id === subjectIds[0]).map((a) => a.class_id);
        setForm((current) => ({ ...current, subject_id: subjectId, class_ids: classIds }));
      }
    } catch {
      setTeacherAssignments([]);
      toast.error("Couldn't load this teacher's class assignments.");
    }
  };

  const handleSubjectChange = (subjectId) => {
    const classIds =
      subjectId === NONE
        ? []
        : teacherAssignments.filter((a) => String(a.subject_id) === subjectId).map((a) => a.class_id);
    setForm((current) => ({ ...current, subject_id: subjectId, class_ids: classIds }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editing) {
        const payload = {
          full_name: form.full_name,
          email: form.email,
          phone: form.phone || null,
        };
        if (form.subject_id !== NONE) {
          payload.subject_id = Number(form.subject_id);
          payload.class_ids = form.class_ids;
        }
        await api.patch(`/api/teachers/${editing.id}`, payload);
        toast.success("Teacher updated");
      } else {
        await api.post("/api/teachers", {
          full_name: form.full_name,
          email: form.email,
          password: form.password,
          phone: form.phone || null,
        });
        toast.success("Teacher created");
      }
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
      await api.delete(`/api/teachers/${deleteTarget.id}`);
      toast.success("Teacher deleted");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete this teacher.");
    }
  };

  return (
    <DashboardLayout title="Teachers" subtitle="Manage teacher accounts and assign classes by subject." nav={ADMIN_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Staff</div>
              <div className="font-display text-xl font-semibold mt-1">All teachers</div>
            </div>
            <Button data-testid="add-teacher-btn" onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
              <Plus className="w-4 h-4" /> Add Teacher
            </Button>
          </div>

          {loading && (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="text-sm text-coral py-6" data-testid="teachers-error">
              Couldn't load teachers: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <EmptyState
              icon={Presentation}
              title="No teachers yet"
              description="Add your first teacher, then assign them to classes from here or the Assignments page."
              action={
                <Button onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
                  <Plus className="w-4 h-4" /> Add Teacher
                </Button>
              }
            />
          )}

          {!loading && !error && items.length > 0 && (
            <>
              <Table data-testid="teachers-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Assigned classes</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((t) => (
                    <TableRow key={t.id} data-testid={`teacher-row-${t.id}`}>
                      <TableCell>
                        <div className="font-medium">{t.full_name}</div>
                        <div className="text-xs text-muted-foreground">{t.email}</div>
                      </TableCell>
                      <TableCell>{t.phone || <span className="text-muted-foreground">--</span>}</TableCell>
                      <TableCell>
                        {t.assigned_class_ids && t.assigned_class_ids.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {t.assigned_class_ids.map((cid) => (
                              <Badge key={cid} className="bg-sage/60 text-ink border-0">
                                Grade {gradeFor(cid) ?? cid}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">None yet</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" data-testid={`edit-teacher-${t.id}`} onClick={() => openEdit(t)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" data-testid={`delete-teacher-${t.id}`} onClick={() => setDeleteTarget(t)}>
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
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit teacher" : "Add teacher"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="teacher-form">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Full name</Label>
                <Input required placeholder="e.g. Tara Iyer" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>Email</Label>
                <Input required type="email" placeholder="teacher@email.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {!editing && (
                <div className="space-y-1.5">
                  <Label>Password</Label>
                  <Input required type="password" minLength={6} title="At least 6 characters" placeholder="At least 6 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
                </div>
              )}
              <div className="space-y-1.5">
                <Label>Phone</Label>
                <Input placeholder="Optional" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
            </div>

            {editing && (
              <>
                <div className="space-y-1.5">
                  <Label>Subject</Label>
                  <Select value={form.subject_id} onValueChange={handleSubjectChange}>
                    <SelectTrigger className="border-soft">
                      <SelectValue placeholder="Select subject to manage classes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>No class assignment changes</SelectItem>
                      {subjects.map((s) => (
                        <SelectItem key={s.id} value={String(s.id)}>
                          {s.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {form.subject_id !== NONE && (
                  <div className="space-y-1.5">
                    <Label>Classes for this subject</Label>
                    <MultiSelect options={classOptions} value={form.class_ids} onChange={(class_ids) => setForm({ ...form, class_ids })} />
                  </div>
                )}
              </>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-coral hover:bg-coral-deep text-ink">
                {submitting ? "Saving..." : editing ? "Save changes" : "Create teacher"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete this teacher?"
        description={deleteTarget ? `${deleteTarget.full_name}'s account and class assignments will be permanently removed.` : ""}
        onConfirm={handleDelete}
      />
    </DashboardLayout>
  );
}
