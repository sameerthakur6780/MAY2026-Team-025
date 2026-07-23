import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { getSession } from "@/lib/store";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";

import AdminDashboard from "@/pages/admin/Dashboard";
import AdminFinance from "@/pages/admin/Finance";
import AdminAttendance from "@/pages/admin/Attendance";
import AdminResources from "@/pages/admin/Resources";
import AdminHomework from "@/pages/admin/Homework";
import AdminGrading from "@/pages/admin/Grading";
import AdminAlerts from "@/pages/admin/Alerts";

import ParentDashboard from "@/pages/parent/Dashboard";
import ParentSafety from "@/pages/parent/Safety";
import ParentFees from "@/pages/parent/Fees";
import ParentPerformance from "@/pages/parent/Performance";

import StudentDashboard from "@/pages/student/Dashboard";
import StudentResources from "@/pages/student/Resources";
import StudentHomework from "@/pages/student/Homework";
import StudentAssistant from "@/pages/student/Assistant";

function Protected({ role, children }) {
  const s = getSession();
  if (!s) return <Navigate to="/login" replace />;
  if (role && s.role !== role) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route path="/admin/dashboard" element={<Protected role="admin"><AdminDashboard /></Protected>} />
          <Route path="/admin/finance" element={<Protected role="admin"><AdminFinance /></Protected>} />
          <Route path="/admin/attendance" element={<Protected role="admin"><AdminAttendance /></Protected>} />
          <Route path="/admin/resources" element={<Protected role="admin"><AdminResources /></Protected>} />
          <Route path="/admin/homework" element={<Protected role="admin"><AdminHomework /></Protected>} />
          <Route path="/admin/grading" element={<Protected role="admin"><AdminGrading /></Protected>} />
          <Route path="/admin/alerts" element={<Protected role="admin"><AdminAlerts /></Protected>} />

          <Route path="/parent/dashboard" element={<Protected role="parent"><ParentDashboard /></Protected>} />
          <Route path="/parent/safety" element={<Protected role="parent"><ParentSafety /></Protected>} />
          <Route path="/parent/fees" element={<Protected role="parent"><ParentFees /></Protected>} />
          <Route path="/parent/performance" element={<Protected role="parent"><ParentPerformance /></Protected>} />

          <Route path="/student/dashboard" element={<Protected role="student"><StudentDashboard /></Protected>} />
          <Route path="/student/resources" element={<Protected role="student"><StudentResources /></Protected>} />
          <Route path="/student/homework" element={<Protected role="student"><StudentHomework /></Protected>} />
          <Route path="/student/assistant" element={<Protected role="student"><StudentAssistant /></Protected>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
