import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
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
import { School, Plus, Pencil } from "lucide-react";

export default function AdminClasses() {
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/classes");

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [grade, setGrade] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const openCreate = () => {
    setEditing(null);
    setGrade("");
    setDialogOpen(true);
  };

  const openEdit = (cls) => {
    setEditing(cls);
    setGrade(String(cls.grade));
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editing) {
        await api.patch(`/api/classes/${editing.id}`, { grade: Number(grade) });
        toast.success("Class updated");
      } else {
        await api.post("/api/classes", { grade: Number(grade) });
        toast.success("Class created");
      }
      setDialogOpen(false);
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="Classes" subtitle="Grades run from the tuition centre -- one batch per grade." nav={ADMIN_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Batches</div>
              <div className="font-display text-xl font-semibold mt-1">All classes</div>
            </div>
            <Button data-testid="add-class-btn" onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
              <Plus className="w-4 h-4" /> Add Class
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
            <div className="text-sm text-coral py-6" data-testid="classes-error">
              Couldn't load classes: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <EmptyState
              icon={School}
              title="No classes yet"
              description="Add a class for each grade you're running."
              action={
                <Button onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
                  <Plus className="w-4 h-4" /> Add Class
                </Button>
              }
            />
          )}

          {!loading && !error && items.length > 0 && (
            <>
              <Table data-testid="classes-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Grade</TableHead>
                    <TableHead>Students</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((c) => (
                    <TableRow key={c.id} data-testid={`class-row-${c.id}`}>
                      <TableCell className="font-medium">Grade {c.grade}</TableCell>
                      <TableCell>{c.student_count}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" data-testid={`edit-class-${c.id}`} onClick={() => openEdit(c)}>
                          <Pencil className="w-4 h-4" />
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
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit class" : "Add class"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="class-form">
            <div className="space-y-1.5">
              <Label>Grade (1-12)</Label>
              <Input required type="number" min="1" max="12" value={grade} onChange={(e) => setGrade(e.target.value)} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-coral hover:bg-coral-deep text-ink">
                {submitting ? "Saving..." : editing ? "Save changes" : "Create class"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
