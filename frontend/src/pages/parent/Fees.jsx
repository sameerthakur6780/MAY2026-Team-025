import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import { PARENT_NAV } from "@/lib/navConfig";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Wallet } from "lucide-react";
import { toast } from "sonner";

const statusColor = { paid: "bg-lime text-ink", pending: "bg-yellow text-ink", overdue: "bg-coral text-ink" };

// Razorpay's Checkout widget is only ever needed on this page, so it's
// loaded on demand rather than added to index.html for every route.
function loadRazorpayScript() {
  if (window.Razorpay) return Promise.resolve(true);
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function ParentFees() {
  const { items, loading, error, refetch } = usePaginatedList("/api/fees");
  const [payingId, setPayingId] = useState(null);

  const upcoming = items.filter((f) => f.status !== "paid");
  const totalDue = upcoming.reduce((sum, f) => sum + f.amount, 0);

  async function handlePay(fee) {
    setPayingId(fee.id);
    try {
      const order = await api.post(`/api/fees/${fee.id}/create-order`);
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        toast.error("Couldn't load the payment gateway. Check your connection and try again.");
        return;
      }

      const rzp = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        order_id: order.order_id,
        name: "SmartBatch",
        description: `Fee — ${fee.cycle}`,
        theme: { color: "#FF6F59" },
        handler: () => {
          toast.success("Payment received — confirming with the bank, this updates in a few seconds.");
          setTimeout(refetch, 3000);
        },
        modal: {
          ondismiss: () => setPayingId(null),
        },
      });
      rzp.on("payment.failed", (resp) => {
        toast.error(resp.error?.description || "Payment failed. Please try again.");
      });
      rzp.open();
    } catch (err) {
      toast.error(err.message || "Could not start payment");
      setPayingId(null);
    }
  }

  return (
    <DashboardLayout title="Fees & Payments" subtitle="Pay a pending cycle securely via Razorpay." nav={PARENT_NAV}>
      <Card className="border-soft shadow-none mb-8">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Amount due</div>
              <div className="font-display text-4xl font-bold text-coral mt-2">₹{totalDue.toLocaleString()}</div>
            </div>
            <div className="w-12 h-12 rounded-xl bg-yellow/25 flex items-center justify-center">
              <Wallet className="w-6 h-6 text-yellow" />
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-3">
            {upcoming.length} pending cycle{upcoming.length !== 1 ? "s" : ""}. Pay each cycle below.
          </p>
        </CardContent>
      </Card>

      <Card className="border-soft shadow-none">
        <CardContent className="p-6">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">History</div>
          <div className="font-display text-xl font-semibold mt-1 mb-5">Payment records</div>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : error ? (
            <EmptyState title="Couldn't load your fees" description={error} />
          ) : items.length === 0 ? (
            <EmptyState
              icon={Wallet}
              title="No fee records yet"
              description="Your fee cycles will show up here once they're generated."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-soft">
                  <TableHead className="text-muted-foreground">Cycle</TableHead>
                  <TableHead className="text-muted-foreground">Amount</TableHead>
                  <TableHead className="text-muted-foreground">Due</TableHead>
                  <TableHead className="text-muted-foreground">Status</TableHead>
                  <TableHead className="text-muted-foreground text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((fee) => (
                  <TableRow key={fee.id} className="border-soft" data-testid={`parent-fee-${fee.id}`}>
                    <TableCell className="font-medium">{fee.cycle}</TableCell>
                    <TableCell>₹{fee.amount.toLocaleString()}</TableCell>
                    <TableCell className="text-muted-foreground">{fee.due_date}</TableCell>
                    <TableCell>
                      <Badge className={`${statusColor[fee.status]} border-0 capitalize`}>{fee.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {fee.status !== "paid" ? (
                        <Button
                          size="sm"
                          data-testid={`pay-now-btn-${fee.id}`}
                          disabled={payingId === fee.id}
                          onClick={() => handlePay(fee)}
                          className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-pill"
                        >
                          <Wallet className="w-3.5 h-3.5" /> {payingId === fee.id ? "Opening…" : "Pay now"}
                        </Button>
                      ) : (
                        <span className="text-xs text-muted-foreground">Paid</span>
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
