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
          <div className="w-9 h-9 rounded-lg bg-forest flex items-center justify-center">
            <GraduationCap className="w-5 h-5 text-white" strokeWidth={2} />
          </div>
          <span className="font-display font-bold text-forest text-xl">SmartBatch</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" data-testid="nav-login-link">
            <Button variant="ghost" className="text-forest hover:bg-[#F0EEE8]">Sign in</Button>
          </Link>
          <Link to="/signup" data-testid="nav-signup-link">
            <Button className="bg-forest hover:bg-[#162D24] text-white rounded-full px-5">Get started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 pt-12 pb-20 grid lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sage text-forest text-xs font-semibold tracking-wider uppercase mb-6">
            <Sparkles className="w-3.5 h-3.5" /> Built for tutoring centres
          </div>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-forest tracking-tight leading-[1.05]">
            Less admin. <br />
            <span className="text-terracotta">More teaching.</span>
          </h1>
          <p className="mt-6 text-base sm:text-lg text-[#5C5C5C] max-w-xl leading-relaxed">
            SmartBatch turns messy WhatsApp groups, paper registers and manual fee chasing into one calm, AI-assisted platform for tutors, parents and students.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link to="/signup" data-testid="hero-cta-primary">
              <Button className="bg-forest hover:bg-[#162D24] text-white rounded-full px-7 py-6 text-base gap-2">
                Try the demo <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link to="/login" data-testid="hero-cta-secondary">
              <Button variant="outline" className="rounded-full px-7 py-6 text-base border-forest text-forest hover:bg-forest hover:text-white">
                Sign in
              </Button>
            </Link>
          </div>
          <div className="mt-10 flex items-center gap-6 text-sm text-[#5C5C5C]">
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-forest" /> No credit card</div>
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-forest" /> Instant access</div>
          </div>
        </div>

        <div className="lg:col-span-5 animate-fade-in-up" style={{ animationDelay: "0.15s" }}>
          <div className="relative">
            <div className="absolute -top-4 -left-4 w-24 h-24 rounded-full bg-terracotta/20 blur-2xl" />
            <div className="absolute -bottom-6 -right-6 w-32 h-32 rounded-full bg-sage/60 blur-2xl" />
            <div className="relative rounded-2xl overflow-hidden border border-soft shadow-sm">
              <img
                src="https://images.pexels.com/photos/9159042/pexels-photo-9159042.jpeg"
                alt="Students learning"
                className="w-full h-[440px] object-cover"
              />
            </div>
            <div className="absolute -bottom-6 -left-6 bg-white rounded-xl border border-soft p-4 shadow-sm w-56">
              <div className="text-[10px] tracking-[0.2em] uppercase text-[#5C5C5C] font-bold">Today</div>
              <div className="text-2xl font-display font-bold text-forest mt-1">₹68,900</div>
              <div className="text-xs text-forest/70 mt-1">Fees collected this month</div>
            </div>
          </div>
        </div>
      </section>

      {/* Role selection */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-16">
        <div className="mb-10 max-w-2xl">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-terracotta mb-3">Choose your portal</div>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-[#1C1C1C]">
            One platform. Three purpose-built experiences.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {ROLES.map((r) => (
            <Link key={r.key} to={`/login?role=${r.key}`} data-testid={`role-card-${r.key}`}
              className="group rounded-2xl border border-soft bg-white p-7 transition-all duration-200 hover:-translate-y-0.5 hover:border-forest">
              <div className="w-11 h-11 rounded-xl bg-sage flex items-center justify-center mb-5 group-hover:bg-forest transition-colors">
                <r.icon className="w-5 h-5 text-forest group-hover:text-white transition-colors" strokeWidth={2} />
              </div>
              <div className="font-display text-xl font-semibold text-[#1C1C1C]">{r.title}</div>
              <div className="text-sm text-[#5C5C5C] mt-2 leading-relaxed">{r.desc}</div>
              <div className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-forest group-hover:text-terracotta transition-colors">
                Continue <ArrowRight className="w-4 h-4" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20">
        <div className="mb-12 max-w-2xl">
          <div className="text-xs tracking-[0.2em] uppercase font-bold text-terracotta mb-3">What's inside</div>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-[#1C1C1C]">
            AI where it saves hours. Simple everywhere else.
          </h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((f, i) => (
            <div key={i} className="rounded-2xl border border-soft bg-white p-6 transition-all duration-200 hover:-translate-y-0.5">
              <div className="w-10 h-10 rounded-lg bg-forest flex items-center justify-center mb-4">
                <f.icon className="w-5 h-5 text-white" strokeWidth={2} />
              </div>
              <div className="font-display text-lg font-semibold text-[#1C1C1C]">{f.title}</div>
              <div className="text-sm text-[#5C5C5C] mt-2 leading-relaxed">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-16">
        <div className="rounded-3xl bg-forest p-10 lg:p-14 grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <h3 className="font-display text-3xl sm:text-4xl font-bold text-white leading-tight">
              Ready to see it working?
            </h3>
            <p className="text-white/80 mt-4 leading-relaxed">
              Sign up as any role — Admin, Parent or Student — and explore the full demo. All flows work end-to-end in this preview.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Link to="/signup?role=admin" data-testid="cta-signup-admin">
              <Button className="bg-terracotta hover:bg-[#D06950] text-white rounded-full px-6 py-6">I'm a Tutor</Button>
            </Link>
            <Link to="/signup?role=parent" data-testid="cta-signup-parent">
              <Button variant="outline" className="rounded-full px-6 py-6 border-white text-white bg-transparent hover:bg-white hover:text-forest">I'm a Parent</Button>
            </Link>
            <Link to="/signup?role=student" data-testid="cta-signup-student">
              <Button variant="outline" className="rounded-full px-6 py-6 border-white text-white bg-transparent hover:bg-white hover:text-forest">I'm a Student</Button>
            </Link>
          </div>
        </div>
      </section>

      <footer className="max-w-7xl mx-auto px-6 lg:px-8 py-10 flex items-center justify-between text-sm text-[#5C5C5C]">
        <div>© 2026 SmartBatch. Demo build.</div>
        <div>Made with care for tutoring centres.</div>
      </footer>
    </div>
  );
}
