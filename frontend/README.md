# SmartBatch — Frontend

A tutoring-centre management platform with three role-based portals (Admin/Tutor, Parent, Student), covering finance, AI-simulated attendance/grading, resources, homework and an AI assistant demo.

Built with React 19, Vite, Tailwind CSS and shadcn/ui. This is a frontend-only demo: all data lives in `src/lib/mockData.js` and sessions are stored in `localStorage` — there is no backend.

## Stack

- **Vite** — dev server and build
- **React 19** + **React Router 7** — SPA routing
- **Tailwind CSS 3** + **shadcn/ui** (Radix primitives) — UI components
- **Recharts** — dashboard charts
- **Sonner** — toast notifications
- **Bun** — package manager / dev runtime (npm/yarn/pnpm also work)

## Getting started

```bash
bun install
bun dev       # start the dev server (http://localhost:5173)
bun run build # production build to dist/
bun run preview  # preview the production build locally
```

Using npm instead:

```bash
npm install
npm run dev
npm run build
```

## Project structure

```
src/
├── main.jsx                 entry point
├── App.jsx                  routes + top-level layout
├── components/
│   ├── DashboardLayout.jsx  shared sidebar + header for all portal pages
│   └── ui/                  shadcn/ui components (button, dialog, select, table, ...)
├── lib/
│   ├── store.js             localStorage session helpers (login/logout/role routing)
│   ├── navConfig.js         per-role sidebar nav definitions
│   ├── mockData.js          all demo data + the mock AI assistant reply logic
│   └── utils.js             `cn()` class-merge helper (shadcn convention)
└── pages/
    ├── Landing.jsx, Login.jsx
    ├── admin/                Dashboard, Finance, Attendance, Resources, Homework, Grading, Alerts
    ├── parent/               Dashboard, Safety, Fees, Performance
    └── student/              Dashboard, Resources, Homework, Assistant
```

## Adding shadcn/ui components

```bash
bunx shadcn@latest add <component>
```

This project only includes the shadcn components actually used by the app (button, input, label, card, badge, table, select, textarea, progress, dialog) — add more as needed rather than bulk-generating the full set.
