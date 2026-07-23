import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { FEE_RECORDS, MONTHLY_EARNINGS } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Plus, BellRing } from "lucide-react";
import { toast } from "sonner";

const statusColor = { paid: "bg-sage/60 text-forest", pending: "bg-[#FDE8DC] text-terracotta", overdue: "bg-[#FBD5D5] text-[#B23A48]" };

export default function AdminFinance() {
  const [records, setRecords] = useState(FEE_RECORDS);
  const [cycle, setCycle] = useState("2 months");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ student: "", amount: "", due: "" });

  const totalCollected = records.filter(r => r.status === "paid").reduce((a, b) => a + b.amount, 0);
  const totalPending = records.filter(r => r.status !== "paid").reduce((a, b) => a + b.amount, 0);

  const addRecord = () => {
    if (!form.student || !form.amount || !form.due) return toast.error("Please fill all fields");
    setRecords([{ id: `F${Date.now()}`, student: form.student, cycle: `Cycle (${cycle})`, amount: Number(form.amount), due: form.due, status: "pending" }, ...records]);
    setForm({ student: "", amount: "", due: "" });
    setDialogOpen(false);
    toast.success("Fee record added");
  };

  const sendReminder = (r) => toast.success(`Reminder sent to ${r.student}'s parent`);

  return (
    <DashboardLayout title="Financial Management" subtitle="Custom billing cycles, real-time collection status, and one-tap reminders." nav={ADMIN_NAV}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Collected</div>
          <div className="text-3xl font-display font-bold text-forest mt-2">₹{totalCollected.toLocaleString()}</div>
          <div className="text-xs text-forest/70 mt-2">Across {records.filter(r => r.status === "paid").length} students</div>
        </CardContent></Card>
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Outstanding</div>
          <div className="text-3xl font-display font-bold text-terracotta mt-2">₹{totalPending.toLocaleString()}</div>
          <div className="text-xs text-terracotta/70 mt-2">{records.filter(r => r.status !== "paid").length} pending payments</div>
        </CardContent></Card>
        <Card className="border-soft shadow-none"><CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Billing cycle</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {["Monthly", "2 months", "Quarterly"].map(c => (
              <button key={c} data-testid={`cycle-${c.replace(/\s+/g, "-")}`} onClick={() => { setCycle(c); toast.success(`Cycle set to ${c}`); }}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${cycle === c ? "bg-forest text-white border-forest" : "border-soft text-[#5C5C5C] hover:border-forest"}`}>
                {c}
              </button>
            ))}
          </div>
          <div className="text-xs text-[#5C5C5C] mt-3">Auto-generated fee reminders 3 days before due.</div>
        </CardContent></Card>
      </div>

      <Card className="border-soft shadow-none mb-6">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Earnings trend</div>
              <div className="font-display text-xl font-semibold mt-1">Last 6 months</div>
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MONTHLY_EARNINGS}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E3DC" />
                <XAxis dataKey="month" stroke="#5C5C5C" fontSize={12} />
                <YAxis stroke="#5C5C5C" fontSize={12} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E5E3DC", borderRadius: 8 }} />
                <Bar dataKey="earnings" fill="#1E3F33" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Fee ledger</div>
              <div className="font-display text-xl font-semibold mt-1">All records</div>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button data-testid="add-fee-btn" className="bg-forest hover:bg-[#162D24] text-white gap-2 rounded-full"><Plus className="w-4 h-4" /> Add fee</Button>
              </DialogTrigger>
              <DialogContent className="bg-white">
                <DialogHeader><DialogTitle className="font-display">New fee record</DialogTitle></DialogHeader>
                <div className="space-y-4 mt-2">
                  <div className="space-y-1.5"><Label>Student name</Label><Input data-testid="fee-student-input" value={form.student} onChange={e => setForm({ ...form, student: e.target.value })} placeholder="e.g. Aarav Sharma" /></div>
                  <div className="space-y-1.5"><Label>Amount (₹)</Label><Input data-testid="fee-amount-input" type="number" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} placeholder="6000" /></div>
                  <div className="space-y-1.5"><Label>Due date</Label><Input data-testid="fee-due-input" type="date" value={form.due} onChange={e => setForm({ ...form, due: e.target.value })} /></div>
                  <Button data-testid="submit-fee-btn" onClick={addRecord} className="w-full bg-forest hover:bg-[#162D24] text-white">Save record</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <Table>
            <TableHeader><TableRow className="border-soft">
              <TableHead className="text-[#5C5C5C]">Student</TableHead>
              <TableHead className="text-[#5C5C5C]">Cycle</TableHead>
              <TableHead className="text-[#5C5C5C]">Amount</TableHead>
              <TableHead className="text-[#5C5C5C]">Due</TableHead>
              <TableHead className="text-[#5C5C5C]">Status</TableHead>
              <TableHead className="text-right text-[#5C5C5C]">Action</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {records.map(r => (
                <TableRow key={r.id} className="border-soft" data-testid={`fee-row-${r.id}`}>
                  <TableCell className="font-medium">{r.student}</TableCell>
                  <TableCell className="text-[#5C5C5C]">{r.cycle}</TableCell>
                  <TableCell>₹{r.amount.toLocaleString()}</TableCell>
                  <TableCell className="text-[#5C5C5C]">{r.due}</TableCell>
                  <TableCell><Badge className={`${statusColor[r.status]} border-0 capitalize`}>{r.status}</Badge></TableCell>
                  <TableCell className="text-right">
                    {r.status !== "paid" && (
                      <Button data-testid={`remind-${r.id}`} onClick={() => sendReminder(r)} variant="outline" size="sm" className="gap-1.5 border-soft"><BellRing className="w-3.5 h-3.5" /> Remind</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
