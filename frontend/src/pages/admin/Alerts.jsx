import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { ANNOUNCEMENTS, BATCHES } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Send, Megaphone, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export default function AdminAlerts() {
  const [items, setItems] = useState(ANNOUNCEMENTS);
  const [target, setTarget] = useState("All");
  const [priority, setPriority] = useState("medium");
  const [title, setTitle] = useState("");
  const [msg, setMsg] = useState("");

  const send = () => {
    if (!title) return toast.error("Please enter a title");
    const targetLabel = target === "All" ? "All" : BATCHES.find(b => b.id === target)?.name || target;
    setItems([{ id: `A${Date.now()}`, title, batch: targetLabel, when: "just now", priority }, ...items]);
    setTitle(""); setMsg("");
    toast.success(`Broadcast sent to ${targetLabel}`);
  };

  return (
    <DashboardLayout title="Reminders & Alerts" subtitle="Broadcast high-priority announcements to specific batches or your entire centre." nav={ADMIN_NAV}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">New broadcast</div>
            <div className="font-display text-xl font-semibold mt-1 mb-5">Compose announcement</div>
            <div className="space-y-4">
              <div className="space-y-1.5"><Label>Title</Label><Input data-testid="alert-title-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="Sudden holiday tomorrow — reschedule notice" /></div>
              <div className="space-y-1.5"><Label>Message</Label><Textarea data-testid="alert-msg-input" value={msg} onChange={e => setMsg(e.target.value)} placeholder="Full details…" rows={4} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5"><Label>Target</Label>
                  <Select value={target} onValueChange={setTarget}>
                    <SelectTrigger data-testid="alert-target-select" className="border-soft"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">Entire centre</SelectItem>
                      {BATCHES.map(b => <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>)}
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
              <Button data-testid="send-alert-btn" onClick={send} className="w-full bg-forest hover:bg-[#162D24] text-white gap-2"><Send className="w-4 h-4" /> Send broadcast</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Recent</div>
            <div className="font-display text-xl font-semibold mt-1 mb-5">Sent announcements</div>
            <div className="space-y-3">
              {items.map(a => (
                <div key={a.id} data-testid={`alert-${a.id}`} className="flex gap-3 p-4 rounded-xl border border-soft">
                  <div className={`w-10 h-10 shrink-0 rounded-lg flex items-center justify-center ${a.priority === "high" ? "bg-[#FBD5D5]" : "bg-sage/60"}`}>
                    {a.priority === "high" ? <AlertTriangle className="w-5 h-5 text-[#B23A48]" /> : <Megaphone className="w-5 h-5 text-forest" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-[#1C1C1C]">{a.title}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className="bg-sage/50 text-forest border-0 text-[10px]">{a.batch}</Badge>
                      <span className="text-xs text-[#5C5C5C]">{a.when}</span>
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
