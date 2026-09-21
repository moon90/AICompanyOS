"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Building2,
  CheckCircle2,
  KeyRound,
  Layers,
  LogOut,
  Server,
  ShieldCheck,
  Terminal,
  User as UserIcon,
} from "lucide-react";
import { api, User } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      try {
        const profile = await api.getMe();
        setUser(profile);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [router]);

  async function handleLogout() {
    try {
      await api.logout();
    } catch {
      // Proceed with redirect regardless of network error on logout
    }
    router.push("/login");
    router.refresh();
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0b0f17] text-slate-400 font-mono text-sm">
        Verifying authorization session...
      </div>
    );
  }

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
              <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30">
                Phase 1 Active
              </span>
            </div>
            <div className="px-3 py-2 rounded-md text-emerald-400/80 bg-emerald-950/20 border border-emerald-800/30 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <KeyRound className="w-3.5 h-3.5 text-emerald-400" />
                <span>Authentication</span>
              </span>
              <span className="text-[10px] text-emerald-400 font-mono">Verified</span>
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

        {/* User Card & Logout */}
        <div className="border-t border-slate-800 pt-3">
          <div className="px-2 py-2 mb-2 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center shrink-0">
              <UserIcon className="w-4 h-4" />
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-medium text-white truncate">{user?.name || "Operator"}</p>
              <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full text-xs text-slate-400 hover:text-white px-3 py-2 rounded-md hover:bg-slate-800/60 flex items-center justify-between transition cursor-pointer"
          >
            <span>Sign Out</span>
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </aside>

      {/* Main Operational Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-[#0b0f17]">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-medium text-slate-200">System Foundation</h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Session Authenticated (PostgreSQL)
            </span>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Operator: {user?.email}
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-8 max-w-5xl">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold tracking-tight text-white mb-2">
              Phase 1 — Authentication Verified
            </h2>
            <p className="text-sm text-slate-400">
              Secure user registration, bcrypt password hashing, and authoritative PostgreSQL session management
              are operational in accordance with <code className="text-slate-300 font-mono">docs/Phases.md</code> § 5.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">PostgreSQL Session Authority</h3>
                  <p className="text-xs text-slate-400">Table <code className="font-mono">user_sessions</code></p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Active session validated for user ID: <code className="text-slate-300 font-mono">{user?.id}</code></span>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">Security & Password Policy</h3>
                  <p className="text-xs text-slate-400">Bcrypt, sliding rate limits, HttpOnly cookies</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Brute-force protection & session revocation active</span>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">API Authentication Routes</h3>
                  <p className="text-xs text-slate-400">/api/v1/auth/[register, login, logout, me]</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Deterministic endpoints decoupled via AuthService</span>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-800 bg-[#111827]">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white">Route Protection</h3>
                  <p className="text-xs text-slate-400">Next.js Edge Middleware</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Unauthenticated requests redirected automatically to /login</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
