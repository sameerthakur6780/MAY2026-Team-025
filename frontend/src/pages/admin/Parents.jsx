import { useState } from "react";
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
import { Users, Plus, Pencil, Trash2 } from "lucide-react";

function emptyForm() {
  return { full_name: "", email: "", password: "", phone: "", occupation: "", address: "" };
}

export default function AdminParents() {
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/parents");

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm());
    setDialogOpen(true);
  };

  const openEdit = (parent) => {
    setEditing(parent);
    setForm({ ...emptyForm(), occupation: parent.occupation || "", address: parent.address || "" });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editing) {
        await api.patch(`/api/parents/${editing.id}`, {
          occupation: form.occupation || null,
          address: form.address || null,
        });
        toast.success("Parent updated");
      } else {
        await api.post("/api/parents", {
          full_name: form.full_name,
          email: form.email,
          password: form.password,
          phone: form.phone || null,
          occupation: form.occupation || null,
          address: form.address || null,
        });
        toast.success("Parent created");
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
      await api.delete(`/api/parents/${deleteTarget.id}`);
      toast.success("Parent deleted");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete this parent.");
    }
  };

  return (
    <DashboardLayout title="Parents" subtitle="Manage parent accounts and their linked students." nav={ADMIN_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Families</div>
              <div className="font-display text-xl font-semibold mt-1">All parents</div>
            </div>
            <Button data-testid="add-parent-btn" onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
              <Plus className="w-4 h-4" /> Add Parent
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
            <div className="text-sm text-coral py-6" data-testid="parents-error">
              Couldn't load parents: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <EmptyState
              icon={Users}
              title="No parents yet"
              description="Add a parent account, then link students to them from the Students page."
              action={
                <Button onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
                  <Plus className="w-4 h-4" /> Add Parent
                </Button>
              }
            />
          )}

          {!loading && !error && items.length > 0 && (
            <>
              <Table data-testid="parents-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Occupation</TableHead>
                    <TableHead>Linked students</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((p) => (
                    <TableRow key={p.id} data-testid={`parent-row-${p.id}`}>
                      <TableCell>
                        <div className="font-medium">{p.full_name}</div>
                        <div className="text-xs text-muted-foreground">{p.email}</div>
                      </TableCell>
                      <TableCell>{p.phone || <span className="text-muted-foreground">--</span>}</TableCell>
                      <TableCell>{p.occupation || <span className="text-muted-foreground">--</span>}</TableCell>
                      <TableCell>{p.student_ids?.length || 0}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" data-testid={`edit-parent-${p.id}`} onClick={() => openEdit(p)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" data-testid={`delete-parent-${p.id}`} onClick={() => setDeleteTarget(p)}>
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
            <DialogTitle>{editing ? "Edit parent" : "Add parent"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="parent-form">
            {!editing && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label>Full name</Label>
                    <Input required placeholder="e.g. Priya Nair" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Email</Label>
                    <Input required type="email" placeholder="parent@email.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
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
                <Label>Occupation</Label>
                <Input placeholder="Optional" value={form.occupation} onChange={(e) => setForm({ ...form, occupation: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>Address</Label>
                <Input placeholder="Optional" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-coral hover:bg-coral-deep text-ink">
                {submitting ? "Saving..." : editing ? "Save changes" : "Create parent"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete this parent?"
        description={deleteTarget ? `${deleteTarget.full_name}'s account will be permanently removed.` : ""}
        onConfirm={handleDelete}
      />
    </DashboardLayout>
  );
}
