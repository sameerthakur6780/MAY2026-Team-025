import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Pagination({ page, pages, total, onPageChange }) {
  if (total === 0) return null;

  return (
    <div className="flex items-center justify-between pt-4 mt-2 border-t border-soft">
      <div className="text-xs text-muted-foreground">
        Page {page} of {pages || 1} &middot; {total} total
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="border-soft"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft className="w-4 h-4" /> Prev
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="border-soft"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
