import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { STUDENT_NAV } from "@/lib/navConfig";
import { RESOURCES, BATCHES } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FileText, Image as ImageIcon, Download, Search } from "lucide-react";
import { toast } from "sonner";

export default function StudentResources() {
  const [q, setQ] = useState("");
  const filtered = RESOURCES.filter(r => r.title.toLowerCase().includes(q.toLowerCase()));

  return (
    <DashboardLayout title="Study Resources" subtitle="All your notes and materials — clean and distraction-free." nav={STUDENT_NAV}>
      <div className="relative max-w-md mb-6">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#5C5C5C]" />
        <Input data-testid="resource-search" value={q} onChange={e => setQ(e.target.value)} placeholder="Search resources…" className="pl-9 border-soft" />
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((r, i) => {
          const batch = BATCHES.find(b => b.id === r.batch);
          const Icon = r.type === "PDF" ? FileText : ImageIcon;
          return (
            <Card key={r.id} data-testid={`student-resource-${r.id}`} className="border-soft shadow-none hover:-translate-y-0.5 transition-all animate-fade-in-up" style={{ animationDelay: `${i * 40}ms` }}>
              <CardContent className="p-5">
                <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center mb-3">
                  <Icon className="w-5 h-5 text-forest" />
                </div>
                <div className="font-display font-semibold text-[#1C1C1C] leading-tight">{r.title}</div>
                <div className="text-xs text-[#5C5C5C] mt-1">{batch?.name}</div>
                <div className="mt-4 flex items-center justify-between">
                  <Badge className="bg-sage/50 text-forest border-0">{r.type} • {r.size}</Badge>
                  <Button data-testid={`download-${r.id}`} onClick={() => toast.success(`Downloading ${r.title}…`)} size="sm" variant="outline" className="gap-1.5 border-soft">
                    <Download className="w-3.5 h-3.5" /> Get
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {filtered.length === 0 && (
          <div className="col-span-full text-center py-16 border-2 border-dashed border-soft rounded-2xl bg-canvas">
            <div className="text-sm text-[#5C5C5C]">No resources match "{q}".</div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
