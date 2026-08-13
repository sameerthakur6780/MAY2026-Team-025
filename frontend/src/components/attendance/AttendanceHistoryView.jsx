import { useEffect, useState } from "react";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { useAuth } from "@/context/AuthContext";
import { api, ApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { CalendarClock } from "lucide-react";

const ALL = "all";

const STATUS_STYLES = {
  present: "bg-lime text-ink border-0",
  absent: "bg-coral text-ink border-0",
  late: "bg-yellow text-ink border-0",
};

const STATUS_OPTIONS = ["present", "absent", "late"];

function StatusBadge({ status }) {
  return <Badge className={STATUS_STYLES[status] || "bg-surface-2 text-muted-foreground border-0"}>{status}</Badge>;
}

export default function AttendanceHistoryView() {
  const { user } = useAuth();
  const canCorrect = user?.role === "admin" || user?.role === "teacher";

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [classFilter, setClassFilter] = useState(ALL);
  const [studentFilter, setStudentFilter] = useState(ALL);
  const [classes, setClasses] = useState([]);
  const [children, setChildren] = useState([]);
  const [correctingId, setCorrectingId] = useState(null);

  const filters = {
    ...(dateFrom ? { date_from: dateFrom } : {}),
    ...(dateTo ? { date_to: dateTo } : {}),
    ...(classFilter === ALL ? {} : { class_id: classFilter }),
    ...(studentFilter === ALL ? {} : { student_id: studentFilter }),
  };
  const { items, page, pages, total, loading, error, setPage, refetch } = usePaginatedList("/api/attendance", filters);

  useEffect(() => {
    if (user?.role === "admin" || user?.role === "teacher") {
      api.get("/api/classes?per_page=100").then((d) => setClasses(d.items)).catch(() => {});
    }
    if (user?.role === "parent") {
      // Already scoped server-side to this parent's own children.
      api.get("/api/students?per_page=100").then((d) => setChildren(d.items)).catch(() => {});
    }
  }, [user?.role]);

  const handleCorrect = async (recordId, newStatus) => {
    setCorrectingId(recordId);
    try {
      await api.patch(`/api/attendance/${recordId}`, { status: newStatus });
      toast.success("Attendance record corrected");
      refetch();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not update this record.");
    } finally {
      setCorrectingId(null);
    }
  };

  return (
    <Card className="border-soft shadow-none">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
          <div>
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-muted-foreground">Records</div>
            <div className="font-display text-xl font-semibold mt-1">Attendance history</div>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">From</Label>
              <Input
                type="date"
                data-testid="history-date-from"
                className="border-soft w-[150px]"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">To</Label>
              <Input
                type="date"
                data-testid="history-date-to"
                className="border-soft w-[150px]"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
            {(user?.role === "admin" || user?.role === "teacher") && (
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
            )}
            {user?.role === "parent" && children.length > 1 && (
              <Select value={studentFilter} onValueChange={setStudentFilter}>
                <SelectTrigger className="w-[170px] border-soft">
                  <SelectValue placeholder="All children" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All children</SelectItem>
                  {children.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        {loading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-lg" />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="text-sm text-coral py-6" data-testid="attendance-history-error">
            Couldn't load attendance: {error}{" "}
            <button className="underline font-semibold" onClick={refetch}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <EmptyState
            icon={CalendarClock}
            title="No attendance records"
            description="Nothing matches these filters yet."
          />
        )}

        {!loading && !error && items.length > 0 && (
          <>
            <Table data-testid="attendance-history-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  {user?.role !== "student" && <TableHead>Student</TableHead>}
                  <TableHead>Class</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Marked By</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((rec) => (
                  <TableRow key={rec.id} data-testid={`attendance-row-${rec.id}`}>
                    <TableCell>{rec.date}</TableCell>
                    {user?.role !== "student" && <TableCell>{rec.student_name}</TableCell>}
                    <TableCell>Grade {rec.grade}</TableCell>
                    <TableCell>
                      {canCorrect ? (
                        <Select
                          value={rec.status}
                          disabled={correctingId === rec.id}
                          onValueChange={(value) => value !== rec.status && handleCorrect(rec.id, value)}
                        >
                          <SelectTrigger className="w-[110px] h-8 border-soft" data-testid={`correct-status-${rec.id}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {STATUS_OPTIONS.map((s) => (
                              <SelectItem key={s} value={s}>
                                {s}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <StatusBadge status={rec.status} />
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className="bg-surface-2 text-muted-foreground border-0">{rec.method}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{rec.marked_by_name}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
          </>
        )}
      </CardContent>
    </Card>
  );
}
