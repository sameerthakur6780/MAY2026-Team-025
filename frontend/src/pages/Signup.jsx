import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { GraduationCap, Users, ShieldCheck, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ROLE_LABEL } from "@/lib/store";

const ROLES = [
  { key: "admin", label: "Admin", icon: ShieldCheck },
  { key: "parent", label: "Parent", icon: Users },
  { key: "student", label: "Student", icon: GraduationCap },
];

export default function Signup() {
  const [params] = useSearchParams();
  const [role, setRole] = useState(params.get("role") || "admin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // There's no public self-signup on the real backend -- accounts are
  // created by an admin (POST /api/auth/signup requires an admin session).
  // This form is left in place for the visual, but it can't actually create
  // an account, so it says so rather than pretending to.
  const handleSignup = (e) => {
    e.preventDefault();
    if (!name || !email || !password) return toast.error("Please fill all fields");
    toast.error("Self-signup isn't available. Ask your center admin to create your account.");
  };

  return (
    <div className="min-h-screen bg-canvas flex">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-deep">
        <div className="absolute inset-0 opacity-25">
          <img
            src="https://images.pexels.com/photos/8423012/pexels-photo-8423012.jpeg"
            alt="Students"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative z-10 p-12 flex flex-col justify-between text-foreground">
          <Link to="/" className="flex items-center gap-2.5" data-testid="brand-link">
            <div className="w-9 h-9 rounded-xl bg-coral flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-ink" />
            </div>
            <span className="font-display font-bold text-xl">SmartBatch</span>
          </Link>
          <div className="max-w-md">
            <div className="text-xs tracking-[0.2em] uppercase font-bold text-sage mb-3">Get started</div>
            <h2 className="font-display text-4xl font-bold leading-tight">
              Set up your centre in the time it takes to make chai.
            </h2>
            <p className="mt-4 text-muted-foreground leading-relaxed">
              No card. No setup fee. Explore every dashboard end-to-end.
            </p>
          </div>
          <div className="text-xs text-muted-foreground">© 2026 SmartBatch</div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md animate-fade-in-up">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-coral mb-8" data-testid="back-home-link">
            <ArrowLeft className="w-4 h-4" /> Back to home
          </Link>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-foreground tracking-tight">Create account</h1>
          <p className="text-muted-foreground mt-2">Pick your role and start exploring.</p>

          <div className="mt-8 grid grid-cols-3 gap-2 p-1 bg-deep rounded-pill">
            {ROLES.map((r) => (
              <button
                key={r.key}
                data-testid={`signup-role-tab-${r.key}`}
                onClick={() => setRole(r.key)}
                className={`flex flex-col items-center gap-1.5 py-3 rounded-pill text-xs font-semibold transition-all duration-200 ${
                  role === r.key ? "bg-white text-ink" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <r.icon className="w-4 h-4" />
                {r.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSignup} className="mt-6 space-y-4" data-testid="signup-form">
            <div className="space-y-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" data-testid="signup-name-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" className="border-soft focus:border-coral focus:ring-sage" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" data-testid="signup-email-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@school.com" className="border-soft focus:border-coral focus:ring-sage" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" data-testid="signup-password-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" className="border-soft focus:border-coral focus:ring-sage" />
            </div>
            <Button type="submit" data-testid="signup-submit-btn" className="w-full bg-coral hover:bg-coral-deep text-ink py-6 rounded-pill font-semibold">
              Create {ROLE_LABEL[role]} account
            </Button>
          </form>

          <div className="mt-6 text-sm text-center text-muted-foreground">
            Already have an account?{" "}
            <Link to={`/login?role=${role}`} className="text-coral font-semibold hover:underline" data-testid="goto-login-link">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
