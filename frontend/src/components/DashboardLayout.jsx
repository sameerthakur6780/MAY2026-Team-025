import { NavLink, useNavigate } from "react-router-dom";
import { LogOut, GraduationCap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ROLE_LABEL } from "@/lib/store";
import { useAuth } from "@/context/AuthContext";

export default function DashboardLayout({ title, subtitle, nav, children }) {
  const navigate = useNavigate();
  const { user, logout: logoutRequest } = useAuth();

  const logout = async () => {
    await logoutRequest();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex bg-canvas">
      {/* Sidebar */}
      <aside className="w-[280px] shrink-0 border-r border-soft bg-surface flex flex-col fixed h-screen">
        <div className="px-6 py-6 border-b border-soft">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-forest flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-white" strokeWidth={2} />
            </div>
            <div>
              <div className="font-display font-bold text-forest text-lg leading-none">EduCore</div>
              <div className="text-[10px] tracking-[0.2em] uppercase text-[#5C5C5C] mt-1">
                {ROLE_LABEL[user?.role] || "Portal"}
              </div>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              data-testid={`nav-${item.key}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-forest text-white"
                    : "text-[#1C1C1C] hover:bg-[#F0EEE8]"
                }`
              }
            >
              <item.icon className="w-4 h-4" strokeWidth={2} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-soft">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-sage flex items-center justify-center text-forest font-semibold text-sm">
              {(user?.full_name || "U").slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">{user?.full_name || "User"}</div>
              <div className="text-xs text-[#5C5C5C] truncate">{user?.email}</div>
            </div>
          </div>
          <Button
            data-testid="logout-btn"
            onClick={logout}
            variant="outline"
            className="w-full justify-start gap-2 border-soft"
          >
            <LogOut className="w-4 h-4" /> Sign out
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-[280px]">
        <div className="max-w-7xl mx-auto p-8">
          <header className="mb-8">
            <h1 className="font-display text-3xl sm:text-4xl font-bold text-forest tracking-tight">
              {title}
            </h1>
            {subtitle && (
              <p className="text-[#5C5C5C] mt-2 text-base">{subtitle}</p>
            )}
          </header>
          <div className="animate-fade-in-up">{children}</div>
        </div>
      </main>
    </div>
  );
}
