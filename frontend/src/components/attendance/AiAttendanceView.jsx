import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/apiClient";
import { uploadWithProgress } from "@/lib/uploadWithProgress";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Camera, Sparkles, CheckCircle2, AlertTriangle, UserCheck } from "lucide-react";
import { toast } from "sonner";

const SKIP = "skip";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export default function AiAttendanceView() {
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const [date, setDate] = useState(todayIso());
  const [roster, setRoster] = useState([]);

  const [photo, setPhoto] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [reviewSelections, setReviewSelections] = useState([]);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    api
      .get("/api/classes?per_page=100")
      .then((d) => {
        setClasses(d.items);
        if (d.items.length > 0) setClassId(String(d.items[0].id));
      })
      .catch(() => toast.error("Couldn't load the class list."));
  }, []);

  useEffect(() => {
    if (!classId) return;
    api
      .get(`/api/students?class_id=${classId}&per_page=100`)
      .then((d) => setRoster(d.items))
      .catch(() => {});
  }, [classId]);

  useEffect(() => {
    if (!result?.needs_confirmation?.length) {
      setReviewSelections([]);
      return;
    }
    const marked = new Set([
      ...(result.auto_marked || []).map((m) => m.student_id),
      ...(result.skipped_student_ids || []),
    ]);
    setReviewSelections(
      result.needs_confirmation.map((item) => {
        const defaultId =
          item.best_match_student_id && !marked.has(item.best_match_student_id)
            ? String(item.best_match_student_id)
            : SKIP;
        return { faceIndex: item.face_index, studentId: defaultId };
      })
    );
  }, [result]);

  const nameFor = (studentId) => roster.find((s) => s.id === studentId)?.full_name || `#${studentId}`;

  const alreadyMarkedIds = useMemo(() => {
    if (!result) return new Set();
    return new Set([
      ...(result.auto_marked || []).map((m) => m.student_id),
      ...(result.skipped_student_ids || []),
    ]);
  }, [result]);

  const reviewOptions = useMemo(
    () => roster.filter((s) => !alreadyMarkedIds.has(s.id)),
    [roster, alreadyMarkedIds]
  );

  const onFile = (e) => {
    const f = e.target.files?.[0];
    setPhoto(f || null);
    setResult(null);
  };

  const runAI = async () => {
    if (!photo) return toast.error("Please upload a classroom photo first");
    if (!classId) return toast.error("Please select a class");

    const formData = new FormData();
    formData.append("class_id", classId);
    formData.append("date", date);
    formData.append("image", photo);

    setProcessing(true);
    setProgress(0);
    try {
      const data = await uploadWithProgress("/api/attendance/facial", formData, setProgress);
      setResult(data);
      toast.success(`AI matched ${data.auto_marked.length} of ${data.faces_detected} detected face(s)`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Facial attendance failed. Please try again.");
    } finally {
      setProcessing(false);
    }
  };

  const confirmReview = async () => {
    const entries = reviewSelections
      .filter((row) => row.studentId && row.studentId !== SKIP)
      .map((row) => ({ student_id: Number(row.studentId), status: "present" }));

    if (entries.length === 0) {
      return toast.error("Select at least one student to confirm, or skip unmatched faces.");
    }

    setConfirming(true);
    try {
      const bulk = await api.post("/api/attendance/bulk", {
        class_id: Number(classId),
        date,
        method: "facial",
        entries,
      });

      const confirmedFaceIndices = new Set(
        reviewSelections.filter((row) => row.studentId && row.studentId !== SKIP).map((row) => row.faceIndex)
      );
      const newlyMarked = bulk.created.map((r) => ({
        student_id: r.student_id,
        confidence: null,
      }));

      setResult((prev) => {
        if (!prev) return prev;
        const existingIds = new Set(prev.auto_marked.map((m) => m.student_id));
        const mergedMarked = [
          ...prev.auto_marked,
          ...newlyMarked.filter((m) => !existingIds.has(m.student_id)),
        ];
        return {
          ...prev,
          auto_marked: mergedMarked,
          skipped_student_ids: [...new Set([...prev.skipped_student_ids, ...bulk.skipped_student_ids])],
          needs_confirmation: prev.needs_confirmation.filter((item) => !confirmedFaceIndices.has(item.face_index)),
        };
      });

      toast.success(`Marked ${bulk.created.length} additional student(s) present`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't confirm attendance.");
    } finally {
      setConfirming(false);
    }
  };

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-soft shadow-none">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-5 gap-4 flex-wrap">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Step 1</div>
                <div className="font-display text-xl font-semibold mt-1">Upload classroom photo</div>
              </div>
              <div className="flex items-center gap-2">
                <Select value={classId} onValueChange={setClassId}>
                  <SelectTrigger data-testid="attendance-class-select" className="w-[150px] border-soft">
                    <SelectValue placeholder="Class" />
                  </SelectTrigger>
                  <SelectContent>
                    {classes.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        Grade {c.grade}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="date"
                  data-testid="attendance-date-input"
                  className="w-[150px] border-soft"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
            </div>

            <label
              htmlFor="photo-upload"
              data-testid="upload-label"
              className="block cursor-pointer border-2 border-dashed border-soft rounded-2xl p-10 text-center hover:border-coral transition-colors bg-canvas"
            >
              <input
                id="photo-upload"
                type="file"
                accept="image/*"
                onChange={onFile}
                className="hidden"
                data-testid="attendance-photo-input"
              />
              <div className="w-14 h-14 mx-auto rounded-2xl bg-sage flex items-center justify-center mb-4">
                <Camera className="w-6 h-6 text-ink" />
              </div>
              <div className="font-display text-lg font-semibold text-foreground">
                {photo ? photo.name : "Click to upload classroom photo"}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                JPG or PNG. AI face-recognition will identify present students.
              </div>
            </label>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button
                data-testid="run-ai-btn"
                onClick={runAI}
                disabled={processing}
                className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-pill px-6"
              >
                <Sparkles className="w-4 h-4" /> {processing ? `Analysing… ${progress}%` : "Run AI attendance"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-soft shadow-none">
          <CardContent className="p-6">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">How it works</div>
            <ol className="mt-4 space-y-4 text-sm text-foreground">
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-sage flex items-center justify-center text-ink font-bold text-xs shrink-0">
                  1
                </span>
                Snap a wide photo of your class.
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-sage flex items-center justify-center text-ink font-bold text-xs shrink-0">
                  2
                </span>
                AI matches faces to enrolled students&apos; profile photos.
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-sage flex items-center justify-center text-ink font-bold text-xs shrink-0">
                  3
                </span>
                High-confidence matches are marked present automatically; review uncertain faces below.
              </li>
            </ol>
          </CardContent>
        </Card>
      </div>

      {result && (
        <Card className="border-soft shadow-none mt-6 animate-fade-in-up">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
              <div>
                <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Step 2</div>
                <div className="font-display text-xl font-semibold mt-1">AI detection results</div>
              </div>
              <div className="text-sm text-lime font-medium inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> {result.auto_marked.length}/{result.faces_detected} face(s)
                auto-marked present
              </div>
            </div>

            {result.auto_marked.length > 0 && (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                {result.auto_marked.map((m) => (
                  <div
                    key={m.student_id}
                    data-testid={`detect-${m.student_id}`}
                    className="flex items-center justify-between p-3 rounded-lg border border-soft"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-sage flex items-center justify-center text-ink font-semibold text-sm">
                        {nameFor(m.student_id)[0]}
                      </div>
                      <div>
                        <div className="text-sm font-medium">{nameFor(m.student_id)}</div>
                        {m.confidence != null && (
                          <div className="text-xs text-muted-foreground">{Math.round(m.confidence * 100)}% confidence</div>
                        )}
                      </div>
                    </div>
                    <Badge className="bg-lime text-ink border-0">Present</Badge>
                  </div>
                ))}
              </div>
            )}

            {result.needs_confirmation.length > 0 && (
              <div className="mt-6 border-t border-soft pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-5 h-5 text-yellow" />
                  <div className="font-display text-lg font-semibold">Review unmatched faces</div>
                </div>
                <div className="space-y-3">
                  {result.needs_confirmation.map((item, idx) => (
                    <div
                      key={item.face_index}
                      data-testid={`review-face-${item.face_index}`}
                      className="flex flex-wrap items-center gap-4 p-3 rounded-lg border border-soft bg-canvas"
                    >
                      {item.thumbnail ? (
                        <img
                          src={item.thumbnail}
                          alt={`Face ${item.face_index + 1}`}
                          className="w-14 h-14 rounded-lg object-cover border border-soft"
                        />
                      ) : (
                        <div className="w-14 h-14 rounded-lg bg-surface-2 flex items-center justify-center text-xs text-muted-foreground">
                          Face {item.face_index + 1}
                        </div>
                      )}
                      <div className="flex-1 min-w-[200px]">
                        <div className="text-sm font-medium">Face {item.face_index + 1}</div>
                        {item.confidence != null && (
                          <div className="text-xs text-muted-foreground">
                            Best guess: {nameFor(item.best_match_student_id)} ({Math.round(item.confidence * 100)}%)
                          </div>
                        )}
                      </div>
                      <Select
                        value={reviewSelections[idx]?.studentId || SKIP}
                        onValueChange={(v) =>
                          setReviewSelections((prev) =>
                            prev.map((row, rowIdx) => (rowIdx === idx ? { ...row, studentId: v } : row))
                          )
                        }
                      >
                        <SelectTrigger className="w-[220px] border-soft" data-testid={`review-select-${item.face_index}`}>
                          <SelectValue placeholder="Select student" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value={SKIP}>Skip</SelectItem>
                          {reviewOptions.map((s) => (
                            <SelectItem key={s.id} value={String(s.id)}>
                              {s.full_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <Button
                    data-testid="confirm-review-btn"
                    onClick={confirmReview}
                    disabled={confirming}
                    className="bg-coral hover:bg-coral-deep text-ink gap-2 rounded-pill px-6"
                  >
                    <UserCheck className="w-4 h-4" />
                    {confirming ? "Confirming…" : "Confirm and mark present"}
                  </Button>
                </div>
              </div>
            )}

            {result.skipped_student_ids.length > 0 && (
              <div className="text-xs text-muted-foreground mt-4">
                {result.skipped_student_ids.length} student{result.skipped_student_ids.length !== 1 ? "s were" : " was"}{" "}
                already marked for {date}.
              </div>
            )}

            {result.students_without_profile_photo > 0 && (
              <div className="text-xs text-muted-foreground mt-1">
                {result.students_without_profile_photo} student
                {result.students_without_profile_photo !== 1 ? "s" : ""} in this class have no profile photo on file, so
                they can never be auto-matched.
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </>
  );
}
