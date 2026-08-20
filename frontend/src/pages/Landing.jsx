import { Link } from "react-router-dom";
import { ArrowRight, Users, GraduationCap, ShieldCheck, Sparkles, CheckCircle2, LineChart, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

const FEATURES = [
  { icon: Sparkles, title: "AI Photo Attendance", desc: "One classroom photo. Everyone marked. Parents notified in seconds." },
  { icon: CheckCircle2, title: "Auto Grading", desc: "Upload an answer key and let AI grade papers, homework and worksheets." },
  { icon: LineChart, title: "Financial Command", desc: "Custom billing cycles, real-time earnings and one-tap reminders." },
  { icon: BookOpen, title: "Distraction-free Resources", desc: "Batch-secured notes, PDFs and photos — no WhatsApp chaos." },
];

const ROLES = [
  { key: "admin", title: "Admin / Tutor", desc: "Run finance, attendance, grading & resources.", icon: ShieldCheck },
  { key: "parent", title: "Parent", desc: "Safety pings, fee QR pay & real progress reports.", icon: Users },
  { key: "student", title: "Student", desc: "Timetable, homework, resources & AI tutor.", icon: GraduationCap },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-canvas grain-bg">
      {/* Nav */}
      <nav className="max-w-7xl mx-auto px-6 lg:px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-coral flex items-center justify-center">
            <GraduationCap className="w-5 h-5 text-ink" strokeWidth={2} />
          </div>
          <span className="font-display font-bold text-foreground text-xl">SmartBatch</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" data-testid="nav-login-link">
            <Button variant="ghost" className="text-foreground hover:bg-surface-2 rounded-pill">Sign in</Button>
          </Link>
          <Link to="/login" data-testid="nav-login-cta-link">
            <Button className="bg-coral hover:bg-coral-deep text-ink rounded-pill px-5">Get started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 pt-12 pb-20 grid lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 animate-fade-in-up">
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground tracking-tight leading-[1.05]">
            Less admin. <br />
            <span className="marker">More teaching.</span>
          </h1>
          <p className="mt-6 text-base sm:text-lg text-muted-foreground max-w-xl leading-relaxed">
            SmartBatch turns messy WhatsApp groups, paper registers and manual fee chasing into one calm, AI-assisted platform for tutors, parents and students.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link to="/login" data-testid="hero-cta-primary">
              <Button className="bg-coral hover:bg-coral-deep text-ink rounded-pill px-7 py-6 text-base gap-2">
                Sign in <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
          <div className="mt-10 flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-coral" /> No credit card</div>
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-coral" /> Instant access</div>
          </div>
        </div>

        <div className="lg:col-span-5 animate-fade-in-up" style={{ animationDelay: "0.15s" }}>
          <div className="relative">
            <div className="absolute -top-4 -left-4 w-24 h-24 rounded-full bg-coral/20 blur-2xl" />
            <div className="absolute -bottom-6 -right-6 w-32 h-32 rounded-full bg-sage/60 blur-2xl" />
            <div className="relative rounded-2xl overflow-hidden border border-soft shadow-sm">
              <img
                src="https://images.pexels.com/photos/9159042/pexels-photo-9159042.jpeg"
                alt="Students learning"
                className="w-full h-[440px] object-cover"
              />
            </div>
            <div className="absolute -bottom-6 -left-6 bg-surface rounded-xl border border-soft p-4 shadow-md w-56">
              <div className="text-[10px] tracking-[0.2em] uppercase text-muted-foreground font-bold">Today</div>
              <div className="text-2xl font-display font-bold text-coral mt-1">₹68,900</div>
              <div className="text-xs text-muted-foreground mt-1">Fees collected this month</div>
            </div>
          </div>
        </div>
      </section>

      {/* Role selection */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-16">
        <div className="mb-10 max-w-2xl">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-yellow mb-3">Choose your portal</div>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-foreground">
            One platform. Three purpose-built experiences.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {ROLES.map((r) => (
            <Link key={r.key} to={`/login?role=${r.key}`} data-testid={`role-card-${r.key}`}
              className="group rounded-2xl border border-soft bg-surface p-7 transition-all duration-200 hover:-translate-y-0.5 hover:border-coral">
              <div className="w-11 h-11 rounded-xl bg-sage flex items-center justify-center mb-5 group-hover:bg-coral transition-colors">
                <r.icon className="w-5 h-5 text-ink transition-colors" strokeWidth={2} />
              </div>
              <div className="font-display text-xl font-semibold text-foreground">{r.title}</div>
              <div className="text-sm text-muted-foreground mt-2 leading-relaxed">{r.desc}</div>
              <div className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-coral group-hover:gap-2.5 transition-all">
                Continue <ArrowRight className="w-4 h-4" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20">
        <div className="mb-12 max-w-2xl">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-yellow mb-3">What's inside</div>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-foreground">
            AI where it saves hours. Simple everywhere else.
          </h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((f, i) => (
            <div key={i} className="rounded-2xl border border-soft bg-surface p-6 transition-all duration-200 hover:-translate-y-0.5">
              <div className="w-10 h-10 rounded-xl bg-coral flex items-center justify-center mb-4">
                <f.icon className="w-5 h-5 text-ink" strokeWidth={2} />
              </div>
              <div className="font-display text-lg font-semibold text-foreground">{f.title}</div>
              <div className="text-sm text-muted-foreground mt-2 leading-relaxed">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-16">
        <div className="rounded-3xl bg-deep p-10 lg:p-14 grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <h3 className="font-display text-3xl sm:text-4xl font-bold text-foreground leading-tight">
              Ready to see it working?
            </h3>
            <p className="text-muted-foreground mt-4 leading-relaxed">
              Sign in as any role — Admin, Parent or Student — and explore the full demo. All flows work end-to-end in this preview.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Link to="/login?role=admin" data-testid="cta-login-admin">
              <Button className="bg-coral hover:bg-coral-deep text-ink rounded-pill px-6 py-6">I'm a Tutor</Button>
            </Link>
            <Link to="/login?role=parent" data-testid="cta-login-parent">
              <Button variant="outline" className="rounded-pill px-6 py-6 border-white text-foreground bg-transparent hover:bg-white hover:text-ink">I'm a Parent</Button>
            </Link>
            <Link to="/login?role=student" data-testid="cta-login-student">
              <Button variant="outline" className="rounded-pill px-6 py-6 border-white text-foreground bg-transparent hover:bg-white hover:text-ink">I'm a Student</Button>
            </Link>
          </div>
        </div>
      </section>

      <footer className="max-w-7xl mx-auto px-6 lg:px-8 py-10 flex items-center justify-between text-sm text-muted-foreground">
        <div>© 2026 SmartBatch.</div>
        <div>Made with care for tutoring centres.</div>
      </footer>
    </div>
  );
}
