import DashboardLayout from "@/components/DashboardLayout";
import { PARENT_NAV } from "@/lib/navConfig";
import { FEE_RECORDS } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { QrCode, Wallet } from "lucide-react";
import { toast } from "sonner";

const statusColor = { paid: "bg-sage/60 text-forest", pending: "bg-[#FDE8DC] text-terracotta", overdue: "bg-[#FBD5D5] text-[#B23A48]" };

export default function ParentFees() {
  const upcoming = FEE_RECORDS.filter(f => f.status !== "paid");
  const totalDue = upcoming.reduce((a, b) => a + b.amount, 0);

  return (
    <DashboardLayout title="Fees & Payments" subtitle="Scan the QR to pay, or review your history." nav={PARENT_NAV}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Amount due</div>
                <div className="font-display text-4xl font-bold text-forest mt-2">₹{totalDue.toLocaleString()}</div>
              </div>
              <div className="w-12 h-12 rounded-xl bg-[#FDE8DC] flex items-center justify-center">
                <Wallet className="w-6 h-6 text-terracotta" />
              </div>
            </div>
            <p className="text-sm text-[#5C5C5C]">
              {upcoming.length} pending cycle{upcoming.length !== 1 ? "s" : ""}. Pay before Feb 28 to avoid a late fee.
            </p>
            <div className="mt-6 flex gap-3">
              <Button data-testid="pay-now-btn" onClick={() => toast.success("Redirecting to your UPI app… (demo)")} className="bg-forest hover:bg-[#162D24] text-white gap-2 rounded-full">
                <QrCode className="w-4 h-4" /> Pay via UPI
              </Button>
              <Button variant="outline" data-testid="pay-cash-btn" onClick={() => toast.success("Cash payment noted — please pay at centre")} className="rounded-full border-soft">
                Mark cash pay
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6 text-center">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C] mb-3">Scan to pay</div>
            <div className="inline-block p-4 bg-white rounded-2xl border border-soft">
              <div className="w-40 h-40 bg-[#1E3F33] rounded-lg relative overflow-hidden" data-testid="fake-qr">
                <div className="absolute inset-2 bg-white rounded"></div>
                <div className="absolute inset-4 grid grid-cols-8 gap-0.5">
                  {Array.from({ length: 64 }).map((_, i) => (
                    <div key={i} className={`aspect-square ${Math.random() > 0.5 ? "bg-[#1E3F33]" : "bg-white"}`} />
                  ))}
                </div>
                <div className="absolute top-3 left-3 w-6 h-6 bg-white border-2 border-[#1E3F33]"></div>
                <div className="absolute top-3 right-3 w-6 h-6 bg-white border-2 border-[#1E3F33]"></div>
                <div className="absolute bottom-3 left-3 w-6 h-6 bg-white border-2 border-[#1E3F33]"></div>
              </div>
            </div>
            <div className="text-xs text-[#5C5C5C] mt-3">SmartBatch@ybl</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">History</div>
          <div className="font-display text-xl font-semibold mt-1 mb-5">Payment records</div>
          <Table>
            <TableHeader><TableRow className="border-soft">
              <TableHead className="text-[#5C5C5C]">Cycle</TableHead>
              <TableHead className="text-[#5C5C5C]">Amount</TableHead>
              <TableHead className="text-[#5C5C5C]">Due</TableHead>
              <TableHead className="text-[#5C5C5C]">Status</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {FEE_RECORDS.map(r => (
                <TableRow key={r.id} className="border-soft" data-testid={`parent-fee-${r.id}`}>
                  <TableCell className="font-medium">{r.cycle}</TableCell>
                  <TableCell>₹{r.amount.toLocaleString()}</TableCell>
                  <TableCell className="text-[#5C5C5C]">{r.due}</TableCell>
                  <TableCell><Badge className={`${statusColor[r.status]} border-0 capitalize`}>{r.status}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
