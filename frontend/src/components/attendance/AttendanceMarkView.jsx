import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { CheckCircle2, SkipForward, Users } from "lucide-react";

const STATUS_OPTIONS = ["present", "absent", "late"];

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendanceMarkView() {
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const [date, setDate] = useState(todayIso());

  const [roster, setRoster] = useState([]);
  const [existingByStudent, setExistingByStudent] = useState({});
  const [pendingStatus, setPendingStatus] = useState({});
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [rosterError, setRosterError] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [correctingId, setCorrectingId] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  useEffect(() => {
    // Already scoped server-side to this teacher's assigned classes.
    api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => {});
  }, []);

  const loadRosterAndAttendance = async () => {
    if (!classId || !date) return;
    setLoadingRoster(true);
    setRosterError(null);
    try {
      const [studentsRes, attendanceRes] = await Promise.all([
        api.get(`/api/students?class_id=${classId}&per_page=100`),
        api.get(`/api/attendance?class_id=${classId}&date_from=${date}&date_to=${date}&per_page=100`),
      ]);
      setRoster(studentsRes.items);
      const byStudent = {};
      attendanceRes.items.forEach((rec) => {
        byStudent[rec.student_id] = rec;
      });
      setExistingByStudent(byStudent);
      setPendingStatus((prev) => {
        const next = {};
        studentsRes.items.forEach((s) => {
          if (!byStudent[s.id]) next[s.id] = prev[s.id] || "present";
        });
        return next;
      });
    } catch (err) {
      setRosterError(err instanceof ApiError ? err.message : "Could not load the class roster.");
    } finally {
      setLoadingRoster(false);
    }
  };

  useEffect(() => {
    setLastResult(null);
    loadRosterAndAttendance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [classId, date]);

  const handleStatusChange = (student, newStatus) => {
    const existing = existingByStudent[student.id];
    if (existing) {
      handleCorrect(existing.id, newStatus);
    } else {
      setPendingStatus((prev) => ({ ...prev, [student.id]: newStatus }));
    }
  };

  const handleCorrect = async (recordId, newStatus) => {
    setCorrectingId(recordId);
    try {
      const updated = await api.patch(`/api/attendance/${recordId}`, { status: newStatus });
      setExistingByStudent((prev) => ({ ...prev, [updated.student_id]: updated }));
      toast.success("Attendance corrected");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not correct this record.");
    } finally {
      setCorrectingId(null);
    }
  };

  const handleSubmit = async () => {
    if (!roster.length) return;
    const entries = roster.map((s) => ({
      student_id: s.id,
      status: existingByStudent[s.id]?.status || pendingStatus[s.id] || "present",
    }));

    setSubmitting(true);
    try {
      const result = await api.post("/api/attendance/bulk", { class_id: Number(classId), date, entries });
      const nameFor = (id) => roster.find((s) => s.id === id)?.full_name || `#${id}`;
      const createdNames = result.created.map((c) => nameFor(c.student_id));
      const skippedNames = result.skipped_student_ids.map((id) => nameFor(id));
      setLastResult({ createdNames, skippedNames });
      toast.success(`${createdNames.length} newly marked, ${skippedNames.length} already marked`);
      loadRosterAndAttendance();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not submit attendance.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-soft shadow-none">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
          <div>
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-[#5C5C5C]">Roll call</div>
            <div className="font-display text-xl font-semibold mt-1">Mark attendance</div>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <Label className="text-xs text-[#5C5C5C]">Class</Label>
              <Select value={classId} onValueChange={setClassId}>
                <SelectTrigger data-testid="mark-class-select" className="w-[150px] border-soft">
                  <SelectValue placeholder="Select class" />
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
            <div className="space-y-1">
              <Label className="text-xs text-[#5C5C5C]">Date</Label>
              <Input
                type="date"
                data-testid="mark-date-input"
                className="border-soft w-[150px]"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
          </div>
        </div>

        {!classId && (
          <div className="text-sm text-[#5C5C5C] py-10 text-center" data-testid="mark-no-class">
            Pick a class to load its roster.
          </div>
        )}

        {classId && loadingRoster && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-lg" />
            ))}
          </div>
        )}

        {classId && !loadingRoster && rosterError && (
          <div className="text-sm text-terracotta py-6" data-testid="mark-roster-error">
            {rosterError}{" "}
            <button className="underline font-semibold" onClick={loadRosterAndAttendance}>
              Retry
            </button>
          </div>
        )}

        {classId && !loadingRoster && !rosterError && roster.length === 0 && (
          <div className="text-sm text-[#5C5C5C] py-10 text-center" data-testid="mark-empty-roster">
            No students are enrolled in this class yet.
          </div>
        )}

        {classId && !loadingRoster && !rosterError && roster.length > 0 && (
          <>
            <Table data-testid="mark-roster-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Student</TableHead>
                  <TableHead>Admission No</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>State</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roster.map((s) => {
                  const existing = existingByStudent[s.id];
                  const value = existing ? existing.status : pendingStatus[s.id] || "present";
                  return (
                    <TableRow key={s.id} data-testid={`mark-row-${s.id}`}>
                      <TableCell className="font-medium">{s.full_name}</TableCell>
                      <TableCell>{s.admission_no}</TableCell>
                      <TableCell>
                        <Select
                          value={value}
                          disabled={correctingId === existing?.id}
                          onValueChange={(v) => handleStatusChange(s, v)}
                        >
                          <SelectTrigger className="w-[110px] h-8 border-soft" data-testid={`status-select-${s.id}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {STATUS_OPTIONS.map((opt) => (
                              <SelectItem key={opt} value={opt}>
                                {opt}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        {existing ? (
                          <Badge className="bg-[#F0EEE8] text-[#5C5C5C] border-0">Already marked</Badge>
                        ) : (
                          <Badge className="bg-sage/60 text-forest border-0">Not yet marked</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>

            <div className="mt-5 flex items-center justify-between">
              <div className="text-xs text-[#5C5C5C] flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5" /> {roster.length} student{roster.length === 1 ? "" : "s"} in this class
              </div>
              <Button
                data-testid="submit-attendance-btn"
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-forest hover:bg-[#162D24] text-white rounded-full px-6"
              >
                {submitting ? "Submitting..." : `Submit attendance for ${date}`}
              </Button>
            </div>

            {lastResult && (
              <div className="mt-5 p-4 rounded-xl border border-soft bg-canvas space-y-3" data-testid="mark-result">
                <div className="flex items-center gap-2 text-sm font-medium text-forest">
                  <CheckCircle2 className="w-4 h-4" /> {lastResult.createdNames.length} newly marked
                </div>
                {lastResult.createdNames.length > 0 && (
                  <div className="text-xs text-[#5C5C5C] pl-6">{lastResult.createdNames.join(", ")}</div>
                )}
                {lastResult.skippedNames.length > 0 && (
                  <>
                    <div className="flex items-center gap-2 text-sm font-medium text-[#8A6A1E]">
                      <SkipForward className="w-4 h-4" /> {lastResult.skippedNames.length} already marked for{" "}
                      {date} (unchanged -- use the Status column above to correct one)
                    </div>
                    <div className="text-xs text-[#5C5C5C] pl-6">{lastResult.skippedNames.join(", ")}</div>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
