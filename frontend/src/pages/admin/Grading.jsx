import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { STUDENTS } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ClipboardCheck, Sparkles, FileText, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

export default function AdminGrading() {
  const [answerKey, setAnswerKey] = useState("");
  const [sheet, setSheet] = useState("");
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState([]);

  const runGrading = () => {
    if (!answerKey || !sheet) return toast.error("Please upload both answer key and student sheets");
    setProcessing(true);
    setTimeout(() => {
      const list = STUDENTS.slice(0, 6).map(s => {
        const score = Math.floor(Math.random() * 40 + 55);
        return { ...s, score, correct: Math.floor(score / 5), total: 20 };
      });
      setResults(list);
      setProcessing(false);
      toast.success(`Graded ${list.length} papers`);
    }, 1600);
  };

  return (
    <DashboardLayout title="AI Grading & Verification" subtitle="Upload an answer key. AI scans student sheets and homework, then grades them for you." nav={ADMIN_NAV}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Step 1</div>
            <div className="font-display text-lg font-semibold mt-1 mb-4">Upload answer key</div>
            <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-8 text-center hover:border-forest bg-canvas">
              <input type="file" className="hidden" data-testid="key-input" onChange={e => setAnswerKey(e.target.files?.[0]?.name || "")} />
              <FileText className="w-8 h-8 mx-auto text-forest mb-3" />
              <div className="text-sm font-medium">{answerKey || "Click to upload answer key"}</div>
              <div className="text-xs text-[#5C5C5C] mt-1">PDF or image</div>
            </label>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Step 2</div>
            <div className="font-display text-lg font-semibold mt-1 mb-4">Upload student sheets</div>
            <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-8 text-center hover:border-forest bg-canvas">
              <input type="file" multiple className="hidden" data-testid="sheet-input" onChange={e => setSheet(e.target.files?.[0]?.name || "6 files")} />
              <ClipboardCheck className="w-8 h-8 mx-auto text-forest mb-3" />
              <div className="text-sm font-medium">{sheet || "Click to upload student sheets"}</div>
              <div className="text-xs text-[#5C5C5C] mt-1">Batch upload supported</div>
            </label>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-center mb-8">
        <Button data-testid="grade-btn" onClick={runGrading} disabled={processing} className="bg-forest hover:bg-[#162D24] text-white gap-2 rounded-full px-8 py-6">
          <Sparkles className="w-4 h-4" /> {processing ? "Grading with AI…" : "Grade with AI"}
        </Button>
      </div>

      {results.length > 0 && (
        <Card className="border-soft shadow-none animate-fade-in-up">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Results</div>
                <div className="font-display text-xl font-semibold mt-1">AI-verified scores</div>
              </div>
              <div className="text-sm text-forest inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Avg: {Math.round(results.reduce((a, b) => a + b.score, 0) / results.length)}%
              </div>
            </div>
            <div className="space-y-3">
              {results.map(r => (
                <div key={r.id} data-testid={`grade-${r.id}`} className="flex items-center gap-4 p-4 rounded-xl border border-soft">
                  <div className="w-10 h-10 rounded-full bg-sage flex items-center justify-center text-forest font-semibold text-sm">{r.name[0]}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">{r.name}</div>
                    <div className="text-xs text-[#5C5C5C]">{r.correct}/{r.total} correct</div>
                  </div>
                  <div className="w-40">
                    <Progress value={r.score} className="h-2 bg-[#F0EEE8]" />
                  </div>
                  <Badge className={`border-0 ${r.score >= 80 ? "bg-sage/60 text-forest" : r.score >= 60 ? "bg-[#FDE8DC] text-terracotta" : "bg-[#FBD5D5] text-[#B23A48]"}`}>
                    {r.score}%
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </DashboardLayout>
  );
}