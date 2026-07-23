import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ADMIN_NAV } from "@/lib/navConfig";
import { RESOURCES, BATCHES } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Upload, FileText, Image as ImageIcon, Folder, Plus } from "lucide-react";
import { toast } from "sonner";

export default function AdminResources() {
  const [items, setItems] = useState(RESOURCES);
  const [batchFilter, setBatchFilter] = useState("all");
  const [dialog, setDialog] = useState(false);
  const [form, setForm] = useState({ title: "", batch: "B01", type: "PDF" });

  const filtered = batchFilter === "all" ? items : items.filter(i => i.batch === batchFilter);

  const add = () => {
    if (!form.title) return toast.error("Please enter a title");
    setItems([{ id: `R${Date.now()}`, title: form.title, batch: form.batch, type: form.type, uploaded: new Date().toISOString().slice(0, 10), size: "1.8 MB" }, ...items]);
    setForm({ title: "", batch: "B01", type: "PDF" });
    setDialog(false);
    toast.success("Resource uploaded");
  };

  return (
    <DashboardLayout title="Resource Distribution" subtitle="Batch-secured notes, PDFs and blackboard photos — no WhatsApp chaos." nav={ADMIN_NAV}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2 flex-wrap">
          <button data-testid="filter-all" onClick={() => setBatchFilter("all")} className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${batchFilter === "all" ? "bg-forest text-white border-forest" : "border-soft text-[#5C5C5C] hover:border-forest"}`}>All batches</button>
          {BATCHES.map(b => (
            <button key={b.id} data-testid={`filter-${b.id}`} onClick={() => setBatchFilter(b.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${batchFilter === b.id ? "bg-forest text-white border-forest" : "border-soft text-[#5C5C5C] hover:border-forest"}`}>
              {b.name}
            </button>
          ))}
        </div>

        <Dialog open={dialog} onOpenChange={setDialog}>
          <DialogTrigger asChild>
            <Button data-testid="upload-resource-btn" className="bg-forest hover:bg-[#162D24] text-white gap-2 rounded-full"><Plus className="w-4 h-4" /> Upload resource</Button>
          </DialogTrigger>
          <DialogContent className="bg-white">
            <DialogHeader><DialogTitle className="font-display">Upload new resource</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <div className="space-y-1.5"><Label>Title</Label><Input data-testid="res-title-input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Ch 8 — Practice Set" /></div>
              <div className="space-y-1.5"><Label>Batch</Label>
                <Select value={form.batch} onValueChange={v => setForm({ ...form, batch: v })}>
                  <SelectTrigger data-testid="res-batch-select" className="border-soft"><SelectValue /></SelectTrigger>
                  <SelectContent>{BATCHES.map(b => <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5"><Label>Type</Label>
                <Select value={form.type} onValueChange={v => setForm({ ...form, type: v })}>
                  <SelectTrigger data-testid="res-type-select" className="border-soft"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="PDF">PDF</SelectItem><SelectItem value="IMG">Image (notes)</SelectItem></SelectContent>
                </Select>
              </div>
              <label className="block cursor-pointer border-2 border-dashed border-soft rounded-xl p-6 text-center hover:border-forest bg-canvas">
                <input type="file" className="hidden" data-testid="res-file-input" />
                <Upload className="w-5 h-5 mx-auto text-forest mb-2" />
                <div className="text-sm text-[#5C5C5C]">Click to attach file (demo)</div>
              </label>
              <Button data-testid="submit-resource-btn" onClick={add} className="w-full bg-forest hover:bg-[#162D24] text-white">Publish to batch</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((r, i) => {
          const batch = BATCHES.find(b => b.id === r.batch);
          const Icon = r.type === "PDF" ? FileText : ImageIcon;
          return (
            <Card key={r.id} data-testid={`resource-${r.id}`} className="border-soft shadow-none hover:-translate-y-0.5 transition-all animate-fade-in-up" style={{ animationDelay: `${i * 40}ms` }}>
              <CardContent className="p-5">
                <div className="w-10 h-10 rounded-lg bg-sage flex items-center justify-center mb-3">
                  <Icon className="w-5 h-5 text-forest" />
                </div>
                <div className="font-display font-semibold text-[#1C1C1C] leading-tight">{r.title}</div>
                <div className="flex items-center gap-2 mt-2 text-xs text-[#5C5C5C]">
                  <Folder className="w-3.5 h-3.5" /> {batch?.name}
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <Badge className="bg-sage/50 text-forest border-0">{r.type} • {r.size}</Badge>
                  <span className="text-xs text-[#5C5C5C]">{r.uploaded}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {filtered.length === 0 && (
          <div className="col-span-full text-center py-12 border-2 border-dashed border-soft rounded-2xl bg-canvas">
            <div className="text-sm text-[#5C5C5C]">No resources uploaded for this batch yet.</div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
