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
import { Presentation, Plus, Trash2 } from "lucide-react";

function emptyForm() {
  return { full_name: "", email: "", password: "", phone: "" };
}

export default function AdminTeachers() {
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/teachers");
  const [classes, setClasses] = useState([]);

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => {});
  }, []);

  const gradeFor = (classId) => classes.find((c) => c.id === classId)?.grade;

  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const openCreate = () => {
    setForm(emptyForm());
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/teachers", {
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        phone: form.phone || null,
      });
      toast.success("Teacher created");
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
    <DashboardLayout title="Teachers" subtitle="Manage teacher accounts. Class/subject assignment happens on the Assignments page." nav={ADMIN_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Staff</div>
              <div className="font-display text-xl font-semibold mt-1">All teachers</div>
            </div>
            <Button data-testid="add-teacher-btn" onClick={openCreate} className="bg-forest hover:bg-[#162D24] text-white">
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
            <div className="text-sm text-terracotta py-6" data-testid="teachers-error">
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
              description="Add your first teacher, then assign them to classes from the Assignments page."
              action={
                <Button onClick={openCreate} className="bg-forest hover:bg-[#162D24] text-white">
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
                        <div className="text-xs text-[#5C5C5C]">{t.email}</div>
                      </TableCell>
                      <TableCell>{t.phone || <span className="text-[#5C5C5C]">--</span>}</TableCell>
                      <TableCell>
                        {t.assigned_class_ids && t.assigned_class_ids.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {t.assigned_class_ids.map((cid) => (
                              <Badge key={cid} className="bg-sage/60 text-forest border-0">
                                Grade {gradeFor(cid) ?? cid}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-[#5C5C5C]">None yet</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" data-testid={`delete-teacher-${t.id}`} onClick={() => setDeleteTarget(t)}>
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
            <DialogTitle>Add teacher</DialogTitle>
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
              <div className="space-y-1.5">
                <Label>Password</Label>
                <Input required type="password" placeholder="At least 6 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>Phone</Label>
                <Input placeholder="Optional" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-forest hover:bg-[#162D24] text-white">
                {submitting ? "Saving..." : "Create teacher"}
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
