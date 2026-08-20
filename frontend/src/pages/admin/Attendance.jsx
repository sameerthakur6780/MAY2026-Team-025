import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import AttendanceHistoryView from "@/components/attendance/AttendanceHistoryView";
import { ADMIN_NAV } from "@/lib/navConfig";
import { STUDENTS, BATCHES } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Camera, Sparkles, CheckCircle2, Bell } from "lucide-react";
import { toast } from "sonner";

export default function AdminAttendance() {
  const [view, setView] = useState("ai");
  const [batch, setBatch] = useState("B01");
  const [photoName, setPhotoName] = useState("");
  const [detected, setDetected] = useState([]);
  const [processing, setProcessing] = useState(false);

  const onFile = (e) => {
    const f = e.target.files?.[0];
    if (f) setPhotoName(f.name);
  };

  const runAI = () => {
    if (!photoName) return toast.error("Please upload a classroom photo first");
    setProcessing(true);
    setTimeout(() => {
      const list = STUDENTS.filter(s => s.batch === batch);
      // random present/absent split with majority present
      const detected = list.map(s => ({ ...s, present: Math.random() > 0.15 }));
      setDetected(detected);
      setProcessing(false);
      toast.success(`AI detected ${detected.filter(d => d.present).length} of ${detected.length} students`);
    }, 1500);
  };

  const notify = () => {
    if (!detected.length) return;
    toast.success(`Safety notifications sent to ${detected.filter(d => d.present).length} parents`);
  };

  return (
    <DashboardLayout title="Attendance" subtitle="AI photo attendance and manual attendance history." nav={ADMIN_NAV}>
      <div className="flex gap-2 mb-6">
        <Button
          data-testid="view-ai"
          variant={view === "ai" ? "default" : "outline"}
          className={view === "ai" ? "bg-coral hover:bg-coral-deep text-ink rounded-full px-5" : "border-soft rounded-full px-5"}
          onClick={() => setView("ai")}
        >
          AI photo attendance
        </Button>
        <Button
          data-testid="view-history"
          variant={view === "history" ? "default" : "outline"}
          className={view === "history" ? "bg-coral hover:bg-coral-deep text-ink rounded-full px-5" : "border-soft rounded-full px-5"}
          onClick={() => setView("history")}
        >
          History
        </Button>
      </div>

      {view === "history" ? (
        <AttendanceHistoryView />
      ) : (
      <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Step 1</div>
                <div className="font-display text-xl font-semibold mt-1">Upload classroom photo</div>
              </div>
              <div className="w-56">
                <Select value={batch} onValueChange={setBatch}>
                  <SelectTrigger data-testid="attendance-batch-select" className="border-soft"><SelectValue /></SelectTrigger>
                  <SelectContent>{BATCHES.map(b => <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>

            <label htmlFor="photo-upload" data-testid="upload-label" className="block cursor-pointer border-2 border-dashed border-soft rounded-2xl p-10 text-center hover:border-coral transition-colors bg-canvas">
              <input id="photo-upload" type="file" accept="image/*" onChange={onFile} className="hidden" data-testid="attendance-photo-input" />
              <div className="w-14 h-14 mx-auto rounded-2xl bg-sage flex items-center justify-center mb-4">
                <Camera className="w-6 h-6 text-ink" />
              </div>
              <div className="font-display text-lg font-semibold text-foreground">
                {photoName ? photoName : "Click to upload classroom photo"}
              </div>
              <div className="text-sm text-muted-foreground mt-1">JPG or PNG. AI face-recognition will identify present students.</div>
            </label>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button data-testid="run-ai-btn" onClick={runAI} disabled={processing} className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-pill px-6">
                <Sparkles className="w-4 h-4" /> {processing ? "Analysing…" : "Run AI attendance"}
              </Button>
              {detected.length > 0 && (
                <Button data-testid="notify-parents-btn" onClick={notify} variant="outline" className="gap-2 rounded-pill border-coral text-coral hover:bg-coral hover:text-ink">
                  <Bell className="w-4 h-4" /> Notify parents
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">How it works</div>
            <ol className="mt-4 space-y-4 text-sm text-foreground">
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-sage flex items-center justify-center text-ink font-bold text-xs shrink-0">1</span> Snap a wide photo of your batch.</li>
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-sage flex items-center justify-center text-ink font-bold text-xs shrink-0">2</span> AI matches faces to enrolled students.</li>
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-sage flex items-center justify-center text-ink font-bold text-xs shrink-0">3</span> Push safety notification to parents.</li>
            </ol>
          </CardContent>
        </Card>
      </div>

      {detected.length > 0 && (
        <Card className="border-soft shadow-none mt-6 animate-fade-in-up">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Step 2</div>
                <div className="font-display text-xl font-semibold mt-1">AI detection results</div>
              </div>
              <div className="text-sm text-lime font-medium inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> {detected.filter(d => d.present).length}/{detected.length} present
              </div>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {detected.map(s => (
                <div key={s.id} data-testid={`detect-${s.id}`} className="flex items-center justify-between p-3 rounded-lg border border-soft">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-sage flex items-center justify-center text-ink font-semibold text-sm">{s.name[0]}</div>
                    <div>
                      <div className="text-sm font-medium">{s.name}</div>
                      <div className="text-xs text-muted-foreground">{s.id}</div>
                    </div>
                  </div>
                  <Badge className={`border-0 ${s.present ? "bg-lime text-ink" : "bg-coral text-ink"}`}>
                    {s.present ? "Present" : "Absent"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      </>
      )}
    </DashboardLayout>
  );
}