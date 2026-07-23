import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { GraduationCap, Users, ShieldCheck, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { setSession, roleHome, ROLE_LABEL } from "@/lib/store";

const ROLES = [
  { key: "admin", label: "Admin / Tutor", icon: ShieldCheck },
  { key: "parent", label: "Parent", icon: Users },
  { key: "student", label: "Student", icon: GraduationCap },
];

export default function Login() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [role, setRole] = useState(params.get("role") || "admin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    const r = params.get("role");
    if (r) setRole(r);
  }, [params]);

  const handleLogin = (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please enter email and password");
      return;
    }
    if (password.length < 4) {
      toast.error("Password too short (min 4 chars for demo)");
      return;
    }
    const name = email.split("@")[0].replace(/\./g, " ");
    setSession({ role, email, name: name.charAt(0).toUpperCase() + name.slice(1) });
    toast.success(`Welcome back, ${ROLE_LABEL[role]}`);
    navigate(roleHome(role));
  };

  const useDemoAccount = () => {
    const demo = { admin: "tutor@educore.demo", parent: "parent@educore.demo", student: "student@educore.demo" };
    setEmail(demo[role]);
    setPassword("demo1234");
  };

  return (
    <div className="min-h-screen bg-canvas flex">
      {/* Left side visual */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-forest">
        <div className="absolute inset-0 opacity-30">
          <img
            src="https://images.unsplash.com/photo-1577896851231-70ef18881754?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjbGFzc3Jvb20lMjBzdHVkZW50c3xlbnwwfHx8fDE3ODM0MzAyNjN8MA&ixlib=rb-4.1.0&q=85"
            alt="Classroom"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative z-10 p-12 flex flex-col justify-between text-white">
          <Link to="/" className="flex items-center gap-2.5" data-testid="brand-link">
            <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-forest" />
            </div>
            <span className="font-display font-bold text-xl">EduCore</span>
          </Link>
          <div className="max-w-md">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-sage mb-3">Welcome back</div>
            <h2 className="font-display text-4xl font-bold leading-tight">
              A calmer tutoring day is one login away.
            </h2>
            <p className="mt-4 text-white/70 leading-relaxed">
              Attendance in a photo, fees on autopilot, homework verified by AI — everything you left on WhatsApp lives here now.
            </p>
          </div>
          <div className="text-xs text-white/50">© 2026 EduCore</div>
        </div>
      </div>

      {/* Right side form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md animate-fade-in-up">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-[#5C5C5C] hover:text-forest mb-8" data-testid="back-home-link">
            <ArrowLeft className="w-4 h-4" /> Back to home
          </Link>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-forest tracking-tight">Sign in</h1>
          <p className="text-[#5C5C5C] mt-2">Continue to your EduCore portal</p>

          {/* Role tabs */}
          <div className="mt-8 grid grid-cols-3 gap-2 p-1 bg-[#F0EEE8] rounded-xl">
            {ROLES.map((r) => (
              <button
                key={r.key}
                data-testid={`role-tab-${r.key}`}
                onClick={() => setRole(r.key)}
                className={`flex flex-col items-center gap-1.5 py-3 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  role === r.key ? "bg-white text-forest shadow-sm" : "text-[#5C5C5C] hover:text-forest"
                }`}
              >
                <r.icon className="w-4 h-4" />
                {r.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleLogin} className="mt-6 space-y-4" data-testid="login-form">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                data-testid="login-email-input"
                type="email"
                placeholder="you@school.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="border-soft focus:border-forest focus:ring-sage"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                data-testid="login-password-input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="border-soft focus:border-forest focus:ring-sage"
              />
            </div>
            <button
              type="button"
              data-testid="use-demo-btn"
              onClick={useDemoAccount}
              className="text-xs text-terracotta hover:underline font-semibold"
            >
              Use demo credentials →
            </button>
            <Button type="submit" data-testid="login-submit-btn" className="w-full bg-forest hover:bg-[#162D24] text-white py-6 rounded-lg font-semibold">
              Sign in as {ROLE_LABEL[role]}
            </Button>
          </form>

          <div className="mt-6 text-sm text-center text-[#5C5C5C]">
            Don't have an account?{" "}
            <Link to={`/signup?role=${role}`} className="text-forest font-semibold hover:underline" data-testid="goto-signup-link">
              Create one
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
