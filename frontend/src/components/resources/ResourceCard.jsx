import { FileText, Image as ImageIcon, FileQuestion, FileCheck2, Download, Trash2, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const TYPE_ICON = {
  note: FileText,
  pdf: FileText,
  image: ImageIcon,
  question_paper: FileQuestion,
  answer_key: FileCheck2,
};

const TYPE_LABEL = {
  note: "Note",
  pdf: "PDF",
  image: "Image",
  question_paper: "Question Paper",
  answer_key: "Answer Key",
};

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ResourceCard({ resource, onDownload, downloading, canDelete, onDelete, deleting }) {
  const Icon = TYPE_ICON[resource.type] || FileText;

  return (
    <Card data-testid={`resource-${resource.id}`} className="border-soft shadow-none hover:-translate-y-0.5 transition-all">
      <CardContent className="p-5">
        <div className="w-10 h-10 rounded-lg bg-sage/60 flex items-center justify-center mb-3">
          <Icon className="w-5 h-5 text-forest" />
        </div>
        <div className="font-display font-semibold text-[#1C1C1C] leading-tight truncate" title={resource.filename}>
          {resource.filename}
        </div>
        <div className="text-xs text-[#5C5C5C] mt-1">
          Grade {resource.grade} &middot; {resource.subject_name}
        </div>
        <div className="mt-3 flex items-center justify-between">
          <Badge className="bg-sage/50 text-forest border-0">
            {TYPE_LABEL[resource.type] || resource.type} &middot; {formatSize(resource.size)}
          </Badge>
          <span className="text-xs text-[#5C5C5C]">{resource.uploader_name}</span>
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Button
            data-testid={`download-resource-${resource.id}`}
            onClick={() => onDownload(resource)}
            disabled={downloading}
            size="sm"
            variant="outline"
            className="gap-1.5 border-soft flex-1"
          >
            {downloading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            {downloading ? "Preparing..." : "Download"}
          </Button>
          {canDelete && (
            <Button
              data-testid={`delete-resource-${resource.id}`}
              onClick={() => onDelete(resource)}
              disabled={deleting}
              size="sm"
              variant="ghost"
            >
              <Trash2 className="w-4 h-4 text-terracotta" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
