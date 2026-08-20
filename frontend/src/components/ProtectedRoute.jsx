import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function ProtectedRoute({ role, children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-canvas text-muted-foreground">
        Loading...
      </div>
    );
  }

  if (!user || (role && user.role !== role)) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
