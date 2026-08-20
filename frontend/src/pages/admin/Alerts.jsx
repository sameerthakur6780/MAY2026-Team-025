import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { api, ApiError } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Send, Megaphone, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

const ALL = "all";

export default function AdminAlerts() {
  const [classes, setClasses] = useState([]);
  const [sent, setSent] = useState([]);
  const [target, setTarget] = useState(ALL);
  const [priority, setPriority] = useState("medium");
  const [title, setTitle] = useState("");
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => toast.error("Couldn't load the class list."));
  }, []);

  const send = async () => {
    if (!title) return toast.error("Please enter a title");
    setSending(true);
    const targetLabel = target === ALL ? "Entire centre" : `Grade ${classes.find((c) => String(c.id) === target)?.grade}`;
    try {
      const result = await api.post("/api/announcements/broadcast", {
        title,
        message: msg,
        class_id: target === ALL ? null : Number(target),
        priority,
      });
      setSent([{ id: `A${Date.now()}`, title, batch: targetLabel, when: "just now", priority, recipients: result.recipient_count }, ...sent]);
      setTitle("");
      setMsg("");
      toast.success(`Sent to ${result.recipient_count} recipient${result.recipient_count !== 1 ? "s" : ""} (${targetLabel})`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Broadcast failed. Please try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <DashboardLayout title="Reminders & Alerts" subtitle="Broadcast real emails to specific classes or your entire centre." nav={ADMIN_NAV}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">New broadcast</div>
            <div className="font-display text-xl font-semibold mt-1 mb-5">Compose announcement</div>
            <div className="space-y-4">
              <div className="space-y-1.5"><Label>Title</Label><Input data-testid="alert-title-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="Sudden holiday tomorrow — reschedule notice" /></div>
              <div className="space-y-1.5"><Label>Message</Label><Textarea data-testid="alert-msg-input" value={msg} onChange={e => setMsg(e.target.value)} placeholder="Full details…" rows={4} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5"><Label>Target</Label>
                  <Select value={target} onValueChange={setTarget}>
                    <SelectTrigger data-testid="alert-target-select" className="border-soft"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value={ALL}>Entire centre</SelectItem>
                      {classes.map(c => <SelectItem key={c.id} value={String(c.id)}>Grade {c.grade}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5"><Label>Priority</Label>
                  <Select value={priority} onValueChange={setPriority}>
                    <SelectTrigger data-testid="alert-priority-select" className="border-soft"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="high">High</SelectItem><SelectItem value="medium">Medium</SelectItem><SelectItem value="low">Low</SelectItem></SelectContent>
                  </Select>
                </div>
              </div>
              <Button data-testid="send-alert-btn" disabled={sending} onClick={send} className="w-full bg-coral hover:bg-coral-deep text-ink gap-2">
                <Send className="w-4 h-4" /> {sending ? "Sending…" : "Send broadcast"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">This session</div>
            <div className="font-display text-xl font-semibold mt-1 mb-5">Sent announcements</div>
            <div className="space-y-3">
              {sent.length === 0 && (
                <p className="text-sm text-muted-foreground">Nothing sent yet this session.</p>
              )}
              {sent.map(a => (
                <div key={a.id} data-testid={`alert-${a.id}`} className="flex gap-3 p-4 rounded-xl border border-soft">
                  <div className={`w-10 h-10 shrink-0 rounded-lg flex items-center justify-center ${a.priority === "high" ? "bg-coral" : "bg-sage/60"}`}>
                    {a.priority === "high" ? <AlertTriangle className="w-5 h-5 text-ink" /> : <Megaphone className="w-5 h-5 text-ink" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-foreground">{a.title}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className="bg-sage/50 text-ink border-0 text-[10px]">{a.batch}</Badge>
                      <span className="text-xs text-muted-foreground">{a.recipients} recipient{a.recipients !== 1 ? "s" : ""} · {a.when}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
