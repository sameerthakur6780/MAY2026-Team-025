// Mock data used across the SmartBatch demo. No backend calls.
export const BATCHES = [
  { id: "B01", name: "Class 10 — Physics", students: 24, time: "5:00 PM – 6:30 PM" },
  { id: "B02", name: "Class 12 — Chemistry", students: 18, time: "6:45 PM – 8:15 PM" },
  { id: "B03", name: "Class 9 — Mathematics", students: 22, time: "4:00 PM – 5:00 PM" },
  { id: "B04", name: "JEE Foundation", students: 15, time: "8:30 PM – 10:00 PM" },
];

export const STUDENTS = [
  { id: "S01", name: "Aarav Sharma", batch: "B01", parent: "Rajesh Sharma", present: true, avg: 82 },
  { id: "S02", name: "Diya Kapoor", batch: "B01", parent: "Priya Kapoor", present: true, avg: 91 },
  { id: "S03", name: "Ishaan Verma", batch: "B02", parent: "Suresh Verma", present: false, avg: 74 },
  { id: "S04", name: "Meera Iyer", batch: "B02", parent: "Lakshmi Iyer", present: true, avg: 88 },
  { id: "S05", name: "Kabir Singh", batch: "B03", parent: "Harpreet Singh", present: true, avg: 79 },
  { id: "S06", name: "Ananya Rao", batch: "B04", parent: "Vikram Rao", present: false, avg: 85 },
  { id: "S07", name: "Rohan Mehta", batch: "B01", parent: "Amit Mehta", present: true, avg: 68 },
  { id: "S08", name: "Saanvi Patel", batch: "B03", parent: "Nikhil Patel", present: true, avg: 94 },
];

export const FEE_RECORDS = [
  { id: "F01", student: "Aarav Sharma", cycle: "Nov–Dec 2025", amount: 6000, due: "2026-02-28", status: "pending" },
  { id: "F02", student: "Diya Kapoor", cycle: "Nov–Dec 2025", amount: 6000, due: "2026-02-15", status: "paid" },
  { id: "F03", student: "Ishaan Verma", cycle: "Jan–Feb 2026", amount: 7500, due: "2026-03-10", status: "pending" },
  { id: "F04", student: "Meera Iyer", cycle: "Jan–Feb 2026", amount: 7500, due: "2026-02-05", status: "overdue" },
  { id: "F05", student: "Kabir Singh", cycle: "Jan–Feb 2026", amount: 5500, due: "2026-03-01", status: "paid" },
  { id: "F06", student: "Rohan Mehta", cycle: "Nov–Dec 2025", amount: 6000, due: "2026-02-20", status: "paid" },
];

export const MONTHLY_EARNINGS = [
  { month: "Sep", earnings: 42000 },
  { month: "Oct", earnings: 48500 },
  { month: "Nov", earnings: 51200 },
  { month: "Dec", earnings: 55700 },
  { month: "Jan", earnings: 61300 },
  { month: "Feb", earnings: 68900 },
];

export const RESOURCES = [
  { id: "R01", title: "Ch 8 — Gravitation Notes", batch: "B01", type: "PDF", uploaded: "2026-02-10", size: "2.4 MB" },
  { id: "R02", title: "Organic Chemistry Cheat Sheet", batch: "B02", type: "PDF", uploaded: "2026-02-08", size: "1.1 MB" },
  { id: "R03", title: "Blackboard photo — Trigonometry", batch: "B03", type: "IMG", uploaded: "2026-02-11", size: "3.7 MB" },
  { id: "R04", title: "Sample Paper — JEE Mock 3", batch: "B04", type: "PDF", uploaded: "2026-02-09", size: "5.9 MB" },
  { id: "R05", title: "Ch 8 — Practice Problems", batch: "B01", type: "PDF", uploaded: "2026-02-11", size: "820 KB" },
];

export const HOMEWORK = [
  { id: "H01", title: "Gravitation — Numerical Set", batch: "B01", due: "2026-02-14", assigned: 24, submitted: 18 },
  { id: "H02", title: "Alkanes reaction map", batch: "B02", due: "2026-02-13", assigned: 18, submitted: 15 },
  { id: "H03", title: "Trigonometry identities Q1–Q20", batch: "B03", due: "2026-02-15", assigned: 22, submitted: 20 },
  { id: "H04", title: "Mock Test 3 — Full paper", batch: "B04", due: "2026-02-16", assigned: 15, submitted: 9 },
];

export const ANNOUNCEMENTS = [
  { id: "A01", title: "Holiday declared for Feb 26 (Regional festival)", batch: "All", when: "2 hrs ago", priority: "high" },
  { id: "A02", title: "Extra revision class — JEE Foundation on Saturday", batch: "B04", when: "Yesterday", priority: "medium" },
  { id: "A03", title: "Fee window closes Feb 28 — reminder", batch: "All", when: "3 days ago", priority: "medium" },
];

export const TIMETABLE = [
  { day: "Today", slots: [
    { time: "5:00 PM", subject: "Physics — Gravitation part 3", room: "Room 2" },
    { time: "6:45 PM", subject: "Doubt clinic", room: "Room 1" },
  ]},
  { day: "Tomorrow", slots: [
    { time: "4:00 PM", subject: "Mathematics — Trigonometry", room: "Room 3" },
    { time: "5:00 PM", subject: "Physics — Practice test", room: "Room 2" },
  ]},
  { day: "Day after", slots: [
    { time: "6:45 PM", subject: "Chemistry — Alkenes intro", room: "Room 1" },
  ]},
];

export const UPCOMING_TESTS = [
  { id: "T01", subject: "Physics — Unit Test 4", date: "2026-02-18", topics: "Gravitation, Fluids" },
  { id: "T02", subject: "Mathematics — Trigonometry", date: "2026-02-22", topics: "Identities, Equations" },
  { id: "T03", subject: "Chemistry — Ch 10 & 11", date: "2026-02-25", topics: "Alkanes, Alkenes" },
];

export const STUDENT_PERFORMANCE = [
  { test: "Test 1", score: 72 },
  { test: "Test 2", score: 78 },
  { test: "Test 3", score: 85 },
  { test: "Test 4", score: 81 },
  { test: "Test 5", score: 89 },
];

export const SAFETY_FEED = [
  { id: "N01", type: "attendance", message: "Aarav marked present in Class 10 Physics", time: "5:04 PM today", ok: true },
  { id: "N02", type: "homework", message: "Homework 'Gravitation — Numerical Set' auto-verified", time: "Yesterday, 9:12 PM", ok: true },
  { id: "N03", type: "announcement", message: "Holiday declared for Feb 26 (Regional festival)", time: "2 hrs ago", ok: true },
  { id: "N04", type: "fee", message: "Fee reminder — cycle Nov–Dec 2025 due Feb 28", time: "3 days ago", ok: false },
];

export const CHAT_STARTERS = [
  "What's my homework for tonight?",
  "When is my next Physics test?",
  "Explain Newton's 3rd law simply",
  "Show tomorrow's timetable",
];

// Mock AI reply generator
export function mockAssistantReply(msg) {
  const m = msg.toLowerCase();
  if (m.includes("homework")) return "You have 2 pending: 'Gravitation — Numerical Set' (due Feb 14) and 'Trigonometry identities Q1–Q20' (due Feb 15).";
  if (m.includes("test") || m.includes("exam")) return "Your next test is Physics — Unit Test 4 on Feb 18. Topics: Gravitation & Fluids. Want a revision plan?";
  if (m.includes("timetable") || m.includes("schedule") || m.includes("tomorrow")) return "Tomorrow: Mathematics at 4:00 PM (Room 3), then Physics practice test at 5:00 PM (Room 2).";
  if (m.includes("newton")) return "Newton's 3rd law: For every action there is an equal and opposite reaction. When you push a wall, the wall pushes you back with the same force.";
  if (m.includes("hi") || m.includes("hello")) return "Hey! I'm your SmartBatch assistant. Ask me about homework, tests, or any concept you're stuck on.";
  return "Got it — I've noted your question. For deeper doubts your tutor will follow up in class. Meanwhile, try rephrasing or ask about homework, tests or timetable.";
}
