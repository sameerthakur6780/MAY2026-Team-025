import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { HOMEWORK, BATCHES } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, BookOpen, Users } from "lucide-react";
import { toast } from "sonner";

export default function AdminHomework() {
  const [items, setItems] = useState(HOMEWORK);
  const [dialog, setDialog] = useState(false);
  const [form, setForm] = useState({ title: "", batch: "B01", due: "", desc: "" });

  const assign = () => {
    if (!form.title || !form.due) return toast.error("Please fill title and due date");
    const batch = BATCHES.find(b => b.id === form.batch);
    setItems([{ id: `H${Date.now()}`, title: form.title, batch: form.batch, due: form.due, assigned: batch?.students || 0, submitted: 0 }, ...items]);
    setForm({ title: "", batch: "B01", due: "", desc: "" });
    setDialog(false);
    toast.success("Homework assigned to batch");
  };

  return (
    <DashboardLayout title="Homework Assignment" subtitle="Assign daily tasks to batches or absentee students in one click." nav={ADMIN_NAV}>
      <div className="flex justify-end mb-6">
        <Dialog open={dialog} onOpenChange={setDialog}>
          <DialogTrigger asChild>
            <Button data-testid="assign-hw-btn" className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-full"><Plus className="w-4 h-4" /> Assign homework</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle className="font-display">New homework</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <div className="space-y-1.5"><Label>Title</Label><Input data-testid="hw-title-input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Ch 8 — Numerical set" /></div>
              <div className="space-y-1.5"><Label>Batch</Label>
                <Select value={form.batch} onValueChange={v => setForm({ ...form, batch: v })}>
                  <SelectTrigger data-testid="hw-batch-select" className="border-soft"><SelectValue /></SelectTrigger>
                  <SelectContent>{BATCHES.map(b => <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5"><Label>Due date</Label><Input data-testid="hw-due-input" type="date" value={form.due} onChange={e => setForm({ ...form, due: e.target.value })} /></div>
              <div className="space-y-1.5"><Label>Description (optional)</Label><Textarea data-testid="hw-desc-input" value={form.desc} onChange={e => setForm({ ...form, desc: e.target.value })} placeholder="Detailed instructions…" /></div>
              <Button data-testid="submit-hw-btn" onClick={assign} className="w-full bg-coral hover:bg-coral-deep text-ink">Assign to batch</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {items.map((h, i) => {
          const batch = BATCHES.find(b => b.id === h.batch);
          const pct = Math.round((h.submitted / h.assigned) * 100) || 0;
          return (
            <Card key={h.id} data-testid={`hw-${h.id}`} className="border-soft shadow-none animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <BookOpen className="w-3.5 h-3.5" /> {batch?.name}
                    </div>
                    <div className="font-display text-lg font-semibold text-foreground mt-1">{h.title}</div>
                    <div className="text-xs text-yellow mt-1 font-semibold">Due {h.due}</div>
                  </div>
                  <div className="text-xs text-coral inline-flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5" /> {h.assigned}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                  <span>{h.submitted} of {h.assigned} submitted</span>
                  <span className="font-semibold text-coral">{pct}%</span>
                </div>
                <Progress value={pct} className="h-2 bg-surface-2" />
              </CardContent>
            </Card>
          );
        })}
      </div>
    </DashboardLayout>
  );
}