import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { STUDENT_NAV } from "@/lib/navConfig";
import { HOMEWORK } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Upload, BookOpen, CheckCircle2, Clock } from "lucide-react";
import { toast } from "sonner";

export default function StudentHomework() {
  const [items, setItems] = useState(HOMEWORK.map(h => ({ ...h, mySubmission: null })));
  const [dialog, setDialog] = useState(null);
  const [fileName, setFileName] = useState("");

  const submit = () => {
    if (!fileName) return toast.error("Please attach your homework file");
    setItems(items.map(i => i.id === dialog.id ? { ...i, mySubmission: fileName } : i));
    setDialog(null);
    setFileName("");
    toast.success("Homework submitted — AI will verify it shortly");
  };

  const pending = items.filter(i => !i.mySubmission);
  const submitted = items.filter(i => i.mySubmission);

  return (
    <DashboardLayout title="My Homework" subtitle="Submit your completed homework. AI will verify and your tutor reviews." nav={STUDENT_NAV}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
        <Card className="border-soft shadow-none bg-[#FDE8DC]/40">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-terracotta/20 flex items-center justify-center"><Clock className="w-5 h-5 text-terracotta" /></div>
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Pending</div>
              <div className="text-2xl font-display font-bold text-terracotta">{pending.length}</div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-soft shadow-none bg-sage/30">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-sage/70 flex items-center justify-center"><CheckCircle2 className="w-5 h-5 text-forest" /></div>
            <div>
              <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Submitted</div>
              <div className="text-2xl font-display font-bold text-forest">{submitted.length}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        {items.map(h => (
          <Card key={h.id} data-testid={`stud-hw-${h.id}`} className="border-soft shadow-none">
            <CardContent className="p-5 flex flex-wrap items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-sage/60 flex items-center justify-center shrink-0"><BookOpen className="w-5 h-5 text-forest" /></div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-[#1C1C1C]">{h.title}</div>
                <div className="text-xs text-[#5C5C5C] mt-0.5">Due {h.due}</div>
                {h.mySubmission && (
                  <div className="text-xs text-forest mt-1 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> {h.mySubmission}</div>
                )}
              </div>
              {h.mySubmission ? (
                <Badge className="bg-sage/60 text-forest border-0">AI-verified</Badge>
              ) : (
                <Button data-testid={`submit-hw-${h.id}`} onClick={() => setDialog(h)} className="bg-forest hover:bg-[#162D24] text-white gap-2 rounded-full">
                  <Upload className="w-4 h-4" /> Submit
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={!!dialog} onOpenChange={o => { if (!o) setDialog(null); }}>
        <DialogContent className="bg-white">
          <DialogHeader><DialogTitle className="font-display">Submit: {dialog?.title}</DialogTitle></DialogHeader>
          <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-8 text-center hover:border-forest bg-canvas mt-2">
            <input type="file" accept="image/*,.pdf,.doc,.docx" className="hidden" data-testid="hw-file-input" onChange={e => setFileName(e.target.files?.[0]?.name || "")} />
            <Upload className="w-8 h-8 mx-auto text-forest mb-3" />
            <div className="text-sm font-medium">{fileName || "Click to upload homework"}</div>
            <div className="text-xs text-[#5C5C5C] mt-1">Photo, PDF or DOC</div>
          </label>
          <Button data-testid="submit-hw-confirm" onClick={submit} className="w-full bg-forest hover:bg-[#162D24] text-white">Submit for verification</Button>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
