import { useEffect, useRef, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import ConfirmDialog from "@/components/ConfirmDialog";
import { ADMIN_NAV } from "@/lib/navConfig";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api, ApiError } from "@/lib/apiClient";
import { uploadWithProgress } from "@/lib/uploadWithProgress";
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
import { GraduationCap, Plus, Pencil, Trash2, Camera, UploadCloud } from "lucide-react";

const NONE = "none";
const ALLOWED_PHOTO_EXTENSIONS = ["jpg", "jpeg", "png"];
const MAX_PHOTO_SIZE_BYTES = 20 * 1024 * 1024;

function StatusBadge({ status }) {
  const styles = {
    active: "bg-lime text-ink border-0",
    inactive: "bg-surface-2 text-muted-foreground border-0",
    withdrawn: "bg-coral text-ink border-0",
  };
  return <Badge className={styles[status] || styles.inactive}>{status}</Badge>;
}

function validatePhotoFile(file) {
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (!ext || !ALLOWED_PHOTO_EXTENSIONS.includes(ext)) {
    return `File type .${ext || "?"} isn't allowed. Allowed: ${ALLOWED_PHOTO_EXTENSIONS.join(", ")}`;
  }
  if (file.size > MAX_PHOTO_SIZE_BYTES) {
    return `File exceeds the ${MAX_PHOTO_SIZE_BYTES / (1024 * 1024)}MB size limit`;
  }
  if (file.size === 0) {
    return "File is empty";
  }
  return null;
}

function StudentPhotoThumb({ student }) {
  const [url, setUrl] = useState(null);

  useEffect(() => {
    if (!student.profile_image) {
      setUrl(null);
      return;
    }
    api
      .get(`/api/students/${student.id}/profile-image`)
      .then((d) => setUrl(d.url))
      .catch(() => setUrl(null));
  }, [student.id, student.profile_image]);

  if (url) {
    return <img src={url} alt={student.full_name} className="w-9 h-9 rounded-full object-cover border border-soft" />;
  }

  return (
    <div className="w-9 h-9 rounded-full bg-surface-2 flex items-center justify-center text-xs font-semibold text-muted-foreground">
      {student.full_name?.[0] || "?"}
    </div>
  );
}

function emptyForm() {
  return {
    full_name: "",
    email: "",
    password: "",
    phone: "",
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
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => toast.error("Couldn't load the class list."));
    api.get("/api/parents?per_page=100").then((d) => setParents(d.items)).catch(() => toast.error("Couldn't load the parent list."));
  }, []);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null); // null = creating, object = editing
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const [photoTarget, setPhotoTarget] = useState(null);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoUploading, setPhotoUploading] = useState(false);
  const [photoProgress, setPhotoProgress] = useState(0);
  const [photoRemoving, setPhotoRemoving] = useState(false);
  const photoInputRef = useRef(null);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm());
    setDialogOpen(true);
  };

  const openEdit = (student) => {
    setEditing(student);
    setForm({
      ...emptyForm(),
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

  const openPhotoDialog = (student) => {
    setPhotoTarget(student);
    setPhotoFile(null);
    setPhotoPreview(null);
    setPhotoProgress(0);
  };

  const closePhotoDialog = () => {
    setPhotoTarget(null);
    setPhotoFile(null);
    setPhotoPreview(null);
    setPhotoProgress(0);
    if (photoInputRef.current) photoInputRef.current.value = "";
  };

  const onPhotoSelected = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const err = validatePhotoFile(file);
    if (err) {
      toast.error(err);
      e.target.value = "";
      return;
    }
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const uploadPhoto = async () => {
    if (!photoTarget || !photoFile) return toast.error("Choose a photo first");

    const formData = new FormData();
    formData.append("file", photoFile);

    setPhotoUploading(true);
    setPhotoProgress(0);
    try {
      await uploadWithProgress(`/api/students/${photoTarget.id}/profile-image`, formData, setPhotoProgress);
      toast.success("Profile photo uploaded");
      closePhotoDialog();
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Photo upload failed.");
    } finally {
      setPhotoUploading(false);
    }
  };

  const removePhoto = async () => {
    if (!photoTarget) return;
    setPhotoRemoving(true);
    try {
      await api.delete(`/api/students/${photoTarget.id}/profile-image`);
      toast.success("Profile photo removed");
      closePhotoDialog();
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't remove the photo.");
    } finally {
      setPhotoRemoving(false);
    }
  };

  return (
    <DashboardLayout title="Students" subtitle="Manage student records, class placement, and parent links." nav={ADMIN_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div className="flex items-center gap-3">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Roster</div>
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
              <Button data-testid="add-student-btn" onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
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
            <div className="text-sm text-coral py-6" data-testid="students-error">
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
                <Button onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
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
                    <TableHead>Photo</TableHead>
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
                        <div className="flex items-center gap-2">
                          <StudentPhotoThumb student={s} />
                          {s.has_face_embedding ? (
                            <Badge className="bg-lime text-ink border-0 text-[10px]">AI ready</Badge>
                          ) : (
                            <Badge variant="outline" className="text-[10px] border-soft">
                              No photo
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{s.full_name}</div>
                        <div className="text-xs text-muted-foreground">{s.email}</div>
                      </TableCell>
                      <TableCell>{s.admission_no}</TableCell>
                      <TableCell>{s.grade ? `Grade ${s.grade}` : <span className="text-muted-foreground">Unassigned</span>}</TableCell>
                      <TableCell>
                        {s.parent_id ? (
                          parents.find((p) => p.id === s.parent_id)?.full_name || `#${s.parent_id}`
                        ) : (
                          <span className="text-muted-foreground">None</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={s.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          data-testid={`photo-student-${s.id}`}
                          onClick={() => openPhotoDialog(s)}
                        >
                          <Camera className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" data-testid={`edit-student-${s.id}`} onClick={() => openEdit(s)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" data-testid={`delete-student-${s.id}`} onClick={() => setDeleteTarget(s)}>
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
                    <Input required type="password" minLength={6} title="At least 6 characters" placeholder="At least 6 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Phone</Label>
                    <Input placeholder="Optional" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                  </div>
                </div>
              </>
            )}
            {editing && (
              <div className="p-3 rounded-lg bg-surface-2 text-sm">
                <div className="font-medium">{editing.full_name}</div>
                <div className="text-xs text-muted-foreground">{editing.email}</div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
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
              <Button type="submit" disabled={submitting} className="bg-coral hover:bg-coral-deep text-ink">
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

      <Dialog open={!!photoTarget} onOpenChange={(open) => !open && closePhotoDialog()}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Student profile photo</DialogTitle>
          </DialogHeader>
          {photoTarget && (
            <div className="space-y-4" data-testid="student-photo-dialog">
              <div className="p-3 rounded-lg bg-surface-2 text-sm">
                <div className="font-medium">{photoTarget.full_name}</div>
                <div className="text-xs text-muted-foreground">{photoTarget.email}</div>
              </div>

              <label className="block cursor-pointer border-2 border-dashed border-soft rounded-2xl p-8 text-center hover:border-coral transition-colors bg-canvas">
                <input
                  ref={photoInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/jpg"
                  className="hidden"
                  data-testid="student-photo-input"
                  onChange={onPhotoSelected}
                />
                {photoPreview ? (
                  <img src={photoPreview} alt="Preview" className="mx-auto max-h-48 rounded-xl object-contain" />
                ) : (
                  <>
                    <UploadCloud className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                    <div className="text-sm font-medium">Click to choose a photo</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      JPG or PNG with exactly one clear face. Used for AI attendance matching.
                    </div>
                  </>
                )}
              </label>

              <DialogFooter className="gap-2 sm:justify-between">
                <div>
                  {photoTarget.profile_image && (
                    <Button
                      type="button"
                      variant="outline"
                      className="border-coral text-coral"
                      data-testid="remove-photo-btn"
                      disabled={photoRemoving || photoUploading}
                      onClick={removePhoto}
                    >
                      {photoRemoving ? "Removing…" : "Remove photo"}
                    </Button>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={closePhotoDialog}>
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    className="bg-coral hover:bg-coral-deep text-ink"
                    data-testid="upload-photo-btn"
                    disabled={!photoFile || photoUploading}
                    onClick={uploadPhoto}
                  >
                    {photoUploading ? `Uploading… ${photoProgress}%` : "Upload photo"}
                  </Button>
                </div>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
