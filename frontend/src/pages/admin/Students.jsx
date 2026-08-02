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
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { GraduationCap, Plus, Pencil, Trash2 } from "lucide-react";

const NONE = "none";

function StatusBadge({ status }) {
  const styles = {
    active: "bg-sage/60 text-forest border-0",
    inactive: "bg-[#F0EEE8] text-[#5C5C5C] border-0",
    withdrawn: "bg-terracotta/10 text-terracotta border-0",
  };
  return <Badge className={styles[status] || styles.inactive}>{status}</Badge>;
}

function emptyForm() {
  return {
    full_name: "",
    email: "",
    password: "",
    phone: "",
    admission_no: "",
    dob: "",
    gender: "",
    class_id: NONE,
    parent_id: NONE,
    status: "active",
  };
}

export default function AdminStudents() {
  const [classFilter, setClassFilter] = useState(NONE);
  const filters = classFilter === NONE ? {} : { class_id: classFilter };
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/students", filters);

  const [classes, setClasses] = useState([]);
  const [parents, setParents] = useState([]);

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => {});
    api.get("/api/parents?per_page=100").then((d) => setParents(d.items)).catch(() => {});
  }, []);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null); // null = creating, object = editing
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm());
    setDialogOpen(true);
  };

  const openEdit = (student) => {
    setEditing(student);
    setForm({
      ...emptyForm(),
      admission_no: student.admission_no || "",
      dob: student.dob || "",
      gender: student.gender || "",
      class_id: student.class_id ? String(student.class_id) : NONE,
      parent_id: student.parent_id ? String(student.parent_id) : NONE,
      status: student.status || "active",
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editing) {
        await api.patch(`/api/students/${editing.id}`, {
          admission_no: form.admission_no,
          dob: form.dob || null,
          gender: form.gender || null,
          class_id: form.class_id === NONE ? null : Number(form.class_id),
          parent_id: form.parent_id === NONE ? null : Number(form.parent_id),
          status: form.status,
        });
        toast.success("Student updated");
      } else {
        await api.post("/api/students", {
          full_name: form.full_name,
          email: form.email,
          password: form.password,
          phone: form.phone || null,
          admission_no: form.admission_no,
          dob: form.dob || null,
          gender: form.gender || null,
          class_id: form.class_id === NONE ? null : Number(form.class_id),
          parent_id: form.parent_id === NONE ? null : Number(form.parent_id),
        });
        toast.success("Student created");
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
      await api.delete(`/api/students/${deleteTarget.id}`);
      toast.success("Student deleted");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete this student.");
    }
  };

  return (
    <DashboardLayout title="Students" subtitle="Manage student records, class placement, and parent links." nav={ADMIN_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div className="flex items-center gap-3">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Roster</div>
                <div className="font-display text-xl font-semibold mt-1">All students</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Select value={classFilter} onValueChange={setClassFilter}>
                <SelectTrigger className="w-[160px] border-soft">
                  <SelectValue placeholder="All classes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>All classes</SelectItem>
                  {classes.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      Grade {c.grade}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button data-testid="add-student-btn" onClick={openCreate} className="bg-forest hover:bg-[#162D24] text-white">
                <Plus className="w-4 h-4" /> Add Student
              </Button>
            </div>
          </div>

          {loading && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="text-sm text-terracotta py-6" data-testid="students-error">
              Couldn't load students: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <EmptyState
              icon={GraduationCap}
              title="No students yet"
              description="Add your first student to get started."
              action={
                <Button onClick={openCreate} className="bg-forest hover:bg-[#162D24] text-white">
                  <Plus className="w-4 h-4" /> Add Student
                </Button>
              }
            />
          )}

          {!loading && !error && items.length > 0 && (
            <>
              <Table data-testid="students-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Admission No</TableHead>
                    <TableHead>Class</TableHead>
                    <TableHead>Parent</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((s) => (
                    <TableRow key={s.id} data-testid={`student-row-${s.id}`}>
                      <TableCell>
                        <div className="font-medium">{s.full_name}</div>
                        <div className="text-xs text-[#5C5C5C]">{s.email}</div>
                      </TableCell>
                      <TableCell>{s.admission_no}</TableCell>
                      <TableCell>{s.grade ? `Grade ${s.grade}` : <span className="text-[#5C5C5C]">Unassigned</span>}</TableCell>
                      <TableCell>
                        {s.parent_id ? (
                          parents.find((p) => p.id === s.parent_id)?.full_name || `#${s.parent_id}`
                        ) : (
                          <span className="text-[#5C5C5C]">None</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={s.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" data-testid={`edit-student-${s.id}`} onClick={() => openEdit(s)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" data-testid={`delete-student-${s.id}`} onClick={() => setDeleteTarget(s)}>
                          <Trash2 className="w-4 h-4 text-terracotta" />
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
            <DialogTitle>{editing ? "Edit student" : "Add student"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="student-form">
            {!editing && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label>Full name</Label>
                    <Input required placeholder="e.g. Sam Sharma" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Email</Label>
                    <Input required type="email" placeholder="student@email.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label>Password</Label>
                    <Input required type="password" placeholder="At least 6 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Phone</Label>
                    <Input placeholder="Optional" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                  </div>
                </div>
              </>
            )}
            {editing && (
              <div className="p-3 rounded-lg bg-[#F7F5F0] text-sm">
                <div className="font-medium">{editing.full_name}</div>
                <div className="text-xs text-[#5C5C5C]">{editing.email}</div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Admission No</Label>
                <Input required placeholder="e.g. ADM2026001" value={form.admission_no} onChange={(e) => setForm({ ...form, admission_no: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>Date of birth</Label>
                <Input type="date" value={form.dob} onChange={(e) => setForm({ ...form, dob: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Gender</Label>
                <Input placeholder="Optional" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>Class</Label>
                <Select value={form.class_id} onValueChange={(v) => setForm({ ...form, class_id: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>Unassigned</SelectItem>
                    {classes.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        Grade {c.grade}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Parent</Label>
                <Select value={form.parent_id} onValueChange={(v) => setForm({ ...form, parent_id: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>None</SelectItem>
                    {parents.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        {p.full_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {editing && (
                <div className="space-y-1.5">
                  <Label>Status</Label>
                  <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                      <SelectItem value="withdrawn">Withdrawn</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-forest hover:bg-[#162D24] text-white">
                {submitting ? "Saving..." : editing ? "Save changes" : "Create student"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete this student?"
        description={deleteTarget ? `${deleteTarget.full_name}'s account and records will be permanently removed. This can't be undone.` : ""}
        onConfirm={handleDelete}
      />
    </DashboardLayout>
  );
}
