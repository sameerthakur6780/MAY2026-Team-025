import DashboardLayout from "@/components/DashboardLayout";
import { PARENT_NAV } from "@/lib/navConfig";
import { FEE_RECORDS } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { QrCode, Wallet } from "lucide-react";
import { toast } from "sonner";

const statusColor = { paid: "bg-lime text-ink", pending: "bg-yellow text-ink", overdue: "bg-coral text-ink" };

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
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Amount due</div>
                <div className="font-display text-4xl font-bold text-coral mt-2">₹{totalDue.toLocaleString()}</div>
              </div>
              <div className="w-12 h-12 rounded-xl bg-yellow/25 flex items-center justify-center">
                <Wallet className="w-6 h-6 text-yellow" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              {upcoming.length} pending cycle{upcoming.length !== 1 ? "s" : ""}. Pay before Feb 28 to avoid a late fee.
            </p>
            <div className="mt-6 flex gap-3">
              <Button data-testid="pay-now-btn" onClick={() => toast.success("Redirecting to your UPI app… (demo)")} className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-pill">
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
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground mb-3">Scan to pay</div>
            <div className="inline-block p-4 bg-white rounded-2xl border border-soft">
              <div className="w-40 h-40 bg-ink rounded-lg relative overflow-hidden" data-testid="fake-qr">
                <div className="absolute inset-2 bg-white rounded"></div>
                <div className="absolute inset-4 grid grid-cols-8 gap-0.5">
                  {Array.from({ length: 64 }).map((_, i) => (
                    <div key={i} className={`aspect-square ${Math.random() > 0.5 ? "bg-ink" : "bg-white"}`} />
                  ))}
                </div>
                <div className="absolute top-3 left-3 w-6 h-6 bg-white border-2 border-ink"></div>
                <div className="absolute top-3 right-3 w-6 h-6 bg-white border-2 border-ink"></div>
                <div className="absolute bottom-3 left-3 w-6 h-6 bg-white border-2 border-ink"></div>
              </div>
            </div>
            <div className="text-xs text-muted-foreground mt-3">SmartBatch@ybl</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">History</div>
          <div className="font-display text-xl font-semibold mt-1 mb-5">Payment records</div>
          <Table>
            <TableHeader><TableRow className="border-soft">
              <TableHead className="text-muted-foreground">Cycle</TableHead>
              <TableHead className="text-muted-foreground">Amount</TableHead>
              <TableHead className="text-muted-foreground">Due</TableHead>
              <TableHead className="text-muted-foreground">Status</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {FEE_RECORDS.map(r => (
                <TableRow key={r.id} className="border-soft" data-testid={`parent-fee-${r.id}`}>
                  <TableCell className="font-medium">{r.cycle}</TableCell>
                  <TableCell>₹{r.amount.toLocaleString()}</TableCell>
                  <TableCell className="text-muted-foreground">{r.due}</TableCell>
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
