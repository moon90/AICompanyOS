import React from "react";
import {
  Building2,
  CheckCircle2,
  Layers,
  Server,
  ShieldCheck,
  Terminal,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex flex-1 min-h-screen">
      {/* Sidebar Shell */}
      <aside className="w-64 border-r border-slate-800 bg-[#0d131f] flex flex-col justify-between p-4">
        <div>
          <div className="flex items-center gap-2 px-2 py-3 mb-6">
            <Building2 className="w-6 h-6 text-blue-500" />
            <span className="font-semibold text-lg tracking-tight">AI Company OS</span>
          </div>

          <nav className="space-y-1 text-sm">
            <div className="px-3 py-2 rounded-md bg-slate-800/60 text-white font-medium flex items-center justify-between">
              <span>Overview</span>
              <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/30">
                Phase 0
              </span>
            </div>
            <div className="px-3 py-2 rounded-md text-slate-500 flex items-center justify-between cursor-not-allowed">
              <span>Authentication</span>
              <span className="text-[10px] text-slate-600">Phase 1</span>
            </div>
            <div className="px-3 py-2 rounded-md text-slate-500 flex items-center justify-between cursor-not-allowed">
              <span>Dashboard</span>
              <span className="text-[10px] text-slate-600">Phase 2</span>
            </div>
            <div className="px-3 py-2 rounded-md text-slate-500 flex items-center justify-between cursor-not-allowed">
              <span>Organization</span>
              <span className="text-[10px] text-slate-600">Phase 3</span>
            </div>
            <div className="px-3 py-2 rounded-md text-slate-500 flex items-center justify-between cursor-not-allowed">
              <span>CEO Command</span>
              <span className="text-[10px] text-slate-600">Phase 5</span>
            </div>
            <div className="px-3 py-2 rounded-md text-slate-500 flex items-center justify-between cursor-not-allowed">
              <span>Projects & Tasks</span>
              <span className="text-[10px] text-slate-600">Phase 6</span>
            </div>
          </nav>
        </div>

        <div className="border-t border-slate-800 pt-3 text-xs text-slate-500 flex items-center justify-between">
          <span>Environment</span>
          <span className="font-mono text-slate-400">Foundation</span>
        </div>
      </aside>

      {/* Main Operational Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-[#0b0f17]">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-medium text-slate-200">System Foundation</h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Operational Baseline
            </span>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Modular Monolith Architecture
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-8 max-w-5xl">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold tracking-tight text-white mb-2">
              Phase 0 — Project Foundation
            </h2>
            <p className="text-sm text-slate-400">
              Core foundation established. All boundaries, packages, migrations, and quality checks
              verified in accordance with <code className="text-slate-300 font-mono">docs/Phases.md</code>.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">Backend API</h3>
                  <p className="text-xs text-slate-400">FastAPI, Pydantic, Uvicorn</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Deterministic <code className="text-slate-300 font-mono">GET /health</code> verified</span>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">Database & ORM</h3>
                  <p className="text-xs text-slate-400">SQLAlchemy 2.0, Alembic, PostgreSQL</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Migrations configured and baseline verified</span>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">Frontend Shell</h3>
                  <p className="text-xs text-slate-400">Next.js 14, React 18, Tailwind CSS</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Executive theme tokens and responsive layout initialized</span>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">Quality & Rules</h3>
                  <p className="text-xs text-slate-400">Pytest, Ruff, Mypy, ESLint</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Strict boundary compliance enforced per Rules.md</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
