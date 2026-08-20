import { useEffect, useRef, useState } from "react";
import ResourceCard from "@/components/resources/ResourceCard";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import ConfirmDialog from "@/components/ConfirmDialog";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { api, ApiError } from "@/lib/apiClient";
import { uploadWithProgress } from "@/lib/uploadWithProgress";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { FolderOpen, Plus, UploadCloud } from "lucide-react";

const ALL = "all";

// Mirrors backend/config.py's ALLOWED_UPLOAD_EXTENSIONS / MAX_UPLOAD_SIZE_BYTES.
// Keep these two in sync -- this is only a fast client-side check so a user
// doesn't wait on a slow upload just to get rejected; the server still
// re-validates and is the real authority.
const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024;

const RESOURCE_TYPES = [
  { value: "note", label: "Note" },
  { value: "pdf", label: "PDF" },
  { value: "image", label: "Image" },
  { value: "question_paper", label: "Question Paper" },
  { value: "answer_key", label: "Answer Key" },
];

function validateFile(file) {
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
    return `File type .${ext || "?"} isn't allowed. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
  }
  if (file.size > MAX_SIZE_BYTES) {
    return `File exceeds the ${MAX_SIZE_BYTES / (1024 * 1024)}MB size limit`;
  }
  if (file.size === 0) {
    return "File is empty";
  }
  return null;
}

export default function ResourcesManageView() {
  const { user } = useAuth();
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
  const [deleteTarget, setDeleteTarget] = useState(null);

  useEffect(() => {
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => toast.error("Couldn't load the class list."));
    api.get("/api/subjects?per_page=100").then((d) => setSubjects(d.items)).catch(() => toast.error("Couldn't load the subject list."));
  }, []);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [type, setType] = useState("note");
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);

  const openCreate = () => {
    setType("note");
    setClassId("");
    setSubjectId("");
    setFile(null);
    setFileError(null);
    setProgress(0);
    setDialogOpen(true);
  };

  const handleFileChange = (e) => {
    const picked = e.target.files?.[0] || null;
    if (!picked) {
      setFile(null);
      setFileError(null);
      return;
    }
    const err = validateFile(picked);
    setFile(err ? null : picked);
    setFileError(err);
  };

  const handleDownload = async (resource) => {
    // See ResourcesReadOnlyView's handleDownload for why the tab opens
    // synchronously before the await instead of after, and why no
    // noopener/noreferrer flags (both null the window reference).
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

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !classId || !subjectId) {
      toast.error("Please pick a class, subject, and file.");
      return;
    }

    const formData = new FormData();
    formData.append("type", type);
    formData.append("class_id", classId);
    formData.append("subject_id", subjectId);
    formData.append("file", file);

    setUploading(true);
    setProgress(0);
    try {
      await uploadWithProgress("/api/resources", formData, setProgress);
      toast.success("Resource uploaded");
      setDialogOpen(false);
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/api/resources/${deleteTarget.id}`);
      toast.success("Resource deleted");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete this resource.");
    }
  };

  return (
    <Card className="border-soft shadow-none">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Library</div>
            <div className="font-display text-xl font-semibold mt-1">Shared resources</div>
          </div>
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
            <Button data-testid="upload-resource-btn" onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
              <Plus className="w-4 h-4" /> Upload
            </Button>
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
          <div className="text-sm text-coral py-6" data-testid="resources-error">
            Couldn't load resources: {error}{" "}
            <button className="underline font-semibold" onClick={refetch}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <EmptyState
            icon={FolderOpen}
            title="No resources yet"
            description="Upload notes, question papers, or answer keys for your classes."
            action={
              <Button onClick={openCreate} className="bg-coral hover:bg-coral-deep text-ink">
                <Plus className="w-4 h-4" /> Upload
              </Button>
            }
          />
        )}

        {!loading && !error && items.length > 0 && (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="resources-grid">
              {items.map((r) => (
                <ResourceCard
                  key={r.id}
                  resource={r}
                  onDownload={handleDownload}
                  downloading={downloadingId === r.id}
                  canDelete={user?.role === "admin" || r.uploaded_by === user?.id}
                  onDelete={setDeleteTarget}
                />
              ))}
            </div>
            <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
          </>
        )}
      </CardContent>

      <Dialog open={dialogOpen} onOpenChange={(open) => !uploading && setDialogOpen(open)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Upload resource</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpload} className="space-y-4" data-testid="resource-upload-form">
            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select value={type} onValueChange={setType} disabled={uploading}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RESOURCE_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Class</Label>
                <Select value={classId} onValueChange={setClassId} disabled={uploading}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {classes.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        Grade {c.grade}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Subject</Label>
                <Select value={subjectId} onValueChange={setSubjectId} disabled={uploading}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {subjects.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>File</Label>
              <label
                className={`block cursor-pointer border-2 border-dashed rounded-xl p-6 text-center bg-canvas ${
                  fileError ? "border-coral" : "border-soft hover:border-coral"
                } ${uploading ? "pointer-events-none opacity-60" : ""}`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  data-testid="resource-file-input"
                  disabled={uploading}
                  onChange={handleFileChange}
                  accept={ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(",")}
                />
                <UploadCloud className="w-5 h-5 mx-auto text-coral mb-2" />
                <div className="text-sm text-muted-foreground">
                  {file ? file.name : `Click to attach a file (max ${MAX_SIZE_BYTES / (1024 * 1024)}MB)`}
                </div>
              </label>
              {fileError && (
                <div className="text-xs text-coral" data-testid="file-validation-error">
                  {fileError}
                </div>
              )}
            </div>

            {uploading && (
              <div className="space-y-1.5" data-testid="upload-progress">
                <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                  {progress < 100 ? (
                    <div className="h-full bg-coral transition-all duration-150" style={{ width: `${progress}%` }} />
                  ) : (
                    // The client has sent every byte, but the server still has to write it
                    // to Supabase and commit the row -- that can take a while on its own,
                    // independent of upload speed. A static "100%" bar would look stuck,
                    // so this pulses instead of pretending we know how much longer it'll take.
                    <div className="h-full w-full bg-coral animate-pulse" />
                  )}
                </div>
                <div className="text-xs text-muted-foreground text-center">
                  {progress < 100 ? `Uploading... ${progress}%` : "Finishing up..."}
                </div>
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" disabled={uploading} onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                data-testid="submit-upload-btn"
                disabled={uploading || !file || !classId || !subjectId}
                className="bg-coral hover:bg-coral-deep text-ink"
              >
                {uploading ? (progress < 100 ? `Uploading... ${progress}%` : "Finishing up...") : "Upload"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete this resource?"
        description={deleteTarget ? `"${deleteTarget.filename}" will be permanently removed from storage.` : ""}
        onConfirm={handleDelete}
      />
    </Card>
  );
}
