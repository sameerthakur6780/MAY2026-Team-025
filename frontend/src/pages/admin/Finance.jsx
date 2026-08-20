import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { ADMIN_NAV } from "@/lib/navConfig";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api, ApiError } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Wallet, Plus, BellRing } from "lucide-react";
import { toast } from "sonner";

const statusColor = { paid: "bg-lime text-ink", pending: "bg-yellow text-ink", overdue: "bg-coral text-ink" };
const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function cycleLabel(cycle) {
  const [year, month] = cycle.split("-").map(Number);
  return `${MONTH_LABELS[month - 1]} ${year}`;
}

function emptyForm() {
  return { student_id: "", monthly_amount: "", start_date: "" };
}

export default function AdminFinance() {
  // per_page=100 covers this centre's whole fee history in one request --
  // matches the "give me everything" convention used elsewhere (e.g.
  // /api/classes?per_page=100) rather than paginating totals that need to
  // reflect every record.
  const { items, loading, error, refetch } = usePaginatedList("/api/fees", { per_page: 100 });
  const [students, setStudents] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [remindingId, setRemindingId] = useState(null);

  useEffect(() => {
    api.get("/api/students?per_page=100").then((d) => setStudents(d.items)).catch(() => toast.error("Couldn't load the student list."));
  }, []);

  const paid = items.filter((f) => f.status === "paid");
  const unpaid = items.filter((f) => f.status !== "paid");
  const totalCollected = paid.reduce((a, b) => a + b.amount, 0);
  const totalPending = unpaid.reduce((a, b) => a + b.amount, 0);

  const earningsByCycle = {};
  for (const fee of paid) {
    earningsByCycle[fee.cycle] = (earningsByCycle[fee.cycle] || 0) + fee.amount;
  }
  const earningsTrend = Object.keys(earningsByCycle)
    .sort()
    .slice(-6)
    .map((cycle) => ({ month: cycleLabel(cycle), earnings: earningsByCycle[cycle] }));

  const handleDialogChange = (open) => {
    setDialogOpen(open);
    if (open) setForm(emptyForm());
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/fee-plans", {
        student_id: Number(form.student_id),
        monthly_amount: Number(form.monthly_amount),
        start_date: form.start_date,
      });
      toast.success("Fee plan created — first invoice generated");
      setDialogOpen(false);
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const sendReminder = async (fee) => {
    setRemindingId(fee.id);
    try {
      await api.post(`/api/fees/${fee.id}/remind`);
      toast.success(`Reminder sent to ${fee.student_name}'s parent`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not send reminder.");
    } finally {
      setRemindingId(null);
    }
  };

  return (
    <DashboardLayout title="Financial Management" subtitle="Real-time collection status and one-tap reminders." nav={ADMIN_NAV}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Collected</div>
            <div className="text-3xl font-display font-bold text-lime mt-2">₹{totalCollected.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground mt-2">Across {paid.length} invoice{paid.length !== 1 ? "s" : ""}</div>
          </CardContent>
        </Card>
        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Outstanding</div>
            <div className="text-3xl font-display font-bold text-coral mt-2">₹{totalPending.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground mt-2">{unpaid.length} pending invoice{unpaid.length !== 1 ? "s" : ""}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-soft shadow-none mb-6">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Earnings trend</div>
              <div className="font-display text-xl font-semibold mt-1">Paid invoices by cycle</div>
            </div>
          </div>
          {earningsTrend.length === 0 ? (
            <p className="text-sm text-muted-foreground">No paid invoices yet.</p>
          ) : (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={earningsTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3F3F3F" />
                  <XAxis dataKey="month" stroke="#9A9A9A" fontSize={12} />
                  <YAxis stroke="#9A9A9A" fontSize={12} />
                  <Tooltip contentStyle={{ background: "#2C2C2C", border: "1px solid #3F3F3F", borderRadius: 12, color: "#FFFFFF" }} labelStyle={{ color: "#FFFFFF" }} />
                  <Bar dataKey="earnings" fill="#F65E4B" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Fee ledger</div>
              <div className="font-display text-xl font-semibold mt-1">All records</div>
            </div>
            <Dialog open={dialogOpen} onOpenChange={handleDialogChange}>
              <DialogTrigger asChild>
                <Button data-testid="add-fee-plan-btn" className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-pill">
                  <Plus className="w-4 h-4" /> New fee plan
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle className="font-display">New fee plan</DialogTitle></DialogHeader>
                <form onSubmit={handleCreate} className="space-y-4 mt-2" data-testid="fee-plan-form">
                  <div className="space-y-1.5">
                    <Label>Student</Label>
                    <Select value={form.student_id} onValueChange={(v) => setForm({ ...form, student_id: v })}>
                      <SelectTrigger data-testid="fee-plan-student-select"><SelectValue placeholder="Select a student" /></SelectTrigger>
                      <SelectContent>
                        {students.map((s) => (
                          <SelectItem key={s.id} value={String(s.id)}>{s.full_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Monthly amount (₹)</Label>
                    <Input required type="number" min="1" data-testid="fee-plan-amount-input" value={form.monthly_amount} onChange={(e) => setForm({ ...form, monthly_amount: e.target.value })} placeholder="6000" />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Starting cycle</Label>
                    <Input required type="date" data-testid="fee-plan-start-input" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
                  </div>
                  <Button type="submit" disabled={submitting || !form.student_id} data-testid="submit-fee-plan-btn" className="w-full bg-coral hover:bg-coral-deep text-ink">
                    {submitting ? "Creating…" : "Create plan"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : error ? (
            <div className="text-sm text-coral py-6" data-testid="fees-error">
              Couldn't load fees: {error}{" "}
              <button className="underline font-semibold" onClick={refetch}>Retry</button>
            </div>
          ) : items.length === 0 ? (
            <EmptyState
              icon={Wallet}
              title="No fee records yet"
              description="Create a fee plan for a student to generate their first invoice."
            />
          ) : (
            <Table>
              <TableHeader><TableRow className="border-soft">
                <TableHead className="text-muted-foreground">Student</TableHead>
                <TableHead className="text-muted-foreground">Cycle</TableHead>
                <TableHead className="text-muted-foreground">Amount</TableHead>
                <TableHead className="text-muted-foreground">Due</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
                <TableHead className="text-right text-muted-foreground">Action</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {items.map((r) => (
                  <TableRow key={r.id} className="border-soft" data-testid={`fee-row-${r.id}`}>
                    <TableCell className="font-medium">{r.student_name}</TableCell>
                    <TableCell className="text-muted-foreground">{r.cycle}</TableCell>
                    <TableCell>₹{r.amount.toLocaleString()}</TableCell>
                    <TableCell className="text-muted-foreground">{r.due_date}</TableCell>
                    <TableCell><Badge className={`${statusColor[r.status]} border-0 capitalize`}>{r.status}</Badge></TableCell>
                    <TableCell className="text-right">
                      {r.status !== "paid" && (
                        <Button
                          data-testid={`remind-${r.id}`}
                          disabled={remindingId === r.id}
                          onClick={() => sendReminder(r)}
                          variant="outline"
                          size="sm"
                          className="gap-1.5 border-soft"
                        >
                          <BellRing className="w-3.5 h-3.5" /> {remindingId === r.id ? "Sending…" : "Remind"}
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
