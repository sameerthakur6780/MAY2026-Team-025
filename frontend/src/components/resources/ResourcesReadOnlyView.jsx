import { useEffect, useState } from "react";
import ResourceCard from "@/components/resources/ResourceCard";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api, ApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { FolderOpen } from "lucide-react";

const ALL = "all";

export default function ResourcesReadOnlyView() {
  const [classFilter, setClassFilter] = useState(ALL);
  const [subjectFilter, setSubjectFilter] = useState(ALL);
  const filters = {
    ...(classFilter === ALL ? {} : { class_id: classFilter }),
    ...(subjectFilter === ALL ? {} : { subject_id: subjectFilter }),
  };
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/resources", filters);

  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => {});
    api.get("/api/subjects?per_page=100").then((d) => setSubjects(d.items)).catch(() => {});
  }, []);

  const handleDownload = async (resource) => {
    // Open the tab synchronously, in direct response to the click, then
    // point it at the signed url once we have it -- fetching the url first
    // and calling window.open() after the await breaks the "direct result
    // of a user gesture" chain browsers require, so popup blockers silently
    // swallow it. No window-feature flags here: verified against a live
    // Chromium that both `noopener` AND `noreferrer` (not just `noopener`,
    // despite that being the commonly-cited one) make window.open() return
    // null, which would break the redirect below. The destination is our
    // own backend-issued signed url, not arbitrary third-party content, so
    // skipping them here is a non-issue.
    const tab = window.open("", "_blank");
    setDownloadingId(resource.id);
    try {
      const { url } = await api.get(`/api/resources/${resource.id}/download`);
      if (tab) {
        tab.location.href = url;
      } else {
        window.open(url, "_blank");
      }
    } catch (err) {
      tab?.close();
      toast.error(err instanceof ApiError ? err.message : "Could not generate a download link.");
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div className="text-sm text-[#5C5C5C]">{total} resource{total === 1 ? "" : "s"} available to you</div>
        <div className="flex items-center gap-2">
          <Select value={classFilter} onValueChange={setClassFilter}>
            <SelectTrigger className="w-[150px] border-soft">
              <SelectValue placeholder="All classes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All classes</SelectItem>
              {classes.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  Grade {c.grade}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={subjectFilter} onValueChange={setSubjectFilter}>
            <SelectTrigger className="w-[150px] border-soft">
              <SelectValue placeholder="All subjects" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All subjects</SelectItem>
              {subjects.map((s) => (
                <SelectItem key={s.id} value={String(s.id)}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-xl" />
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="text-sm text-terracotta py-6" data-testid="resources-error">
          Couldn't load resources: {error}{" "}
          <button className="underline font-semibold" onClick={refetch}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState icon={FolderOpen} title="No resources yet" description="Nothing has been shared with your class yet -- check back soon." />
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="resources-grid">
            {items.map((r) => (
              <ResourceCard key={r.id} resource={r} onDownload={handleDownload} downloading={downloadingId === r.id} canDelete={false} />
            ))}
          </div>
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
