import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";

import TeacherDashboard from "@/pages/teacher/Dashboard";
import TeacherResources from "@/pages/teacher/Resources";
import TeacherAttendance from "@/pages/teacher/Attendance";

import AdminDashboard from "@/pages/admin/Dashboard";
import AdminStudents from "@/pages/admin/Students";
import AdminClasses from "@/pages/admin/Classes";
import AdminTeachers from "@/pages/admin/Teachers";
import AdminParents from "@/pages/admin/Parents";
import AdminAssignments from "@/pages/admin/Assignments";
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
import ParentResources from "@/pages/parent/Resources";
import ParentAttendance from "@/pages/parent/Attendance";

import StudentDashboard from "@/pages/student/Dashboard";
import StudentResources from "@/pages/student/Resources";
import StudentAttendance from "@/pages/student/Attendance";
import StudentHomework from "@/pages/student/Homework";
import StudentAssistant from "@/pages/student/Assistant";

function App() {
  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            <Route path="/admin/dashboard" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
            <Route path="/admin/students" element={<ProtectedRoute role="admin"><AdminStudents /></ProtectedRoute>} />
            <Route path="/admin/classes" element={<ProtectedRoute role="admin"><AdminClasses /></ProtectedRoute>} />
            <Route path="/admin/teachers" element={<ProtectedRoute role="admin"><AdminTeachers /></ProtectedRoute>} />
            <Route path="/admin/parents" element={<ProtectedRoute role="admin"><AdminParents /></ProtectedRoute>} />
            <Route path="/admin/assignments" element={<ProtectedRoute role="admin"><AdminAssignments /></ProtectedRoute>} />
            <Route path="/admin/finance" element={<ProtectedRoute role="admin"><AdminFinance /></ProtectedRoute>} />
            <Route path="/admin/attendance" element={<ProtectedRoute role="admin"><AdminAttendance /></ProtectedRoute>} />
            <Route path="/admin/resources" element={<ProtectedRoute role="admin"><AdminResources /></ProtectedRoute>} />
            <Route path="/admin/homework" element={<ProtectedRoute role="admin"><AdminHomework /></ProtectedRoute>} />
            <Route path="/admin/grading" element={<ProtectedRoute role="admin"><AdminGrading /></ProtectedRoute>} />
            <Route path="/admin/alerts" element={<ProtectedRoute role="admin"><AdminAlerts /></ProtectedRoute>} />

            <Route path="/teacher/dashboard" element={<ProtectedRoute role="teacher"><TeacherDashboard /></ProtectedRoute>} />
            <Route path="/teacher/attendance" element={<ProtectedRoute role="teacher"><TeacherAttendance /></ProtectedRoute>} />
            <Route path="/teacher/resources" element={<ProtectedRoute role="teacher"><TeacherResources /></ProtectedRoute>} />

            <Route path="/parent/dashboard" element={<ProtectedRoute role="parent"><ParentDashboard /></ProtectedRoute>} />
            <Route path="/parent/safety" element={<ProtectedRoute role="parent"><ParentSafety /></ProtectedRoute>} />
            <Route path="/parent/fees" element={<ProtectedRoute role="parent"><ParentFees /></ProtectedRoute>} />
            <Route path="/parent/performance" element={<ProtectedRoute role="parent"><ParentPerformance /></ProtectedRoute>} />
            <Route path="/parent/resources" element={<ProtectedRoute role="parent"><ParentResources /></ProtectedRoute>} />
            <Route path="/parent/attendance" element={<ProtectedRoute role="parent"><ParentAttendance /></ProtectedRoute>} />

            <Route path="/student/dashboard" element={<ProtectedRoute role="student"><StudentDashboard /></ProtectedRoute>} />
            <Route path="/student/attendance" element={<ProtectedRoute role="student"><StudentAttendance /></ProtectedRoute>} />
            <Route path="/student/resources" element={<ProtectedRoute role="student"><StudentResources /></ProtectedRoute>} />
            <Route path="/student/homework" element={<ProtectedRoute role="student"><StudentHomework /></ProtectedRoute>} />
            <Route path="/student/assistant" element={<ProtectedRoute role="student"><StudentAssistant /></ProtectedRoute>} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
