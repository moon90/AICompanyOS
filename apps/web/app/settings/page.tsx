"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Key, Lock, Settings, Shield, ShieldAlert, Sparkles, Terminal } from "lucide-react";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function SettingsPage() {
  return (
    <ShellLayout pageTitle="Settings" breadcrumb="System & Governance">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Security Hardening Spotlight Card */}
        <div className="bg-gradient-to-r from-indigo-950/40 via-[#111724] to-[#111724] border border-indigo-500/30 rounded-xl p-6 relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <Shield className="w-3.5 h-3.5" />
                Phase 23 Active
              </div>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Security Hardening &amp; Agent Policy Governance
              </h2>
              <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
                Configure Rule 185 Default-DENY capability matrices, inspect immutable audit logs, test PromptGuard injection defenses, and manage agent quarantine state.
              </p>
            </div>

            <Link
              href="/security"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500 transition shadow-lg shadow-indigo-600/20 shrink-0 self-start md:self-center"
            >
              <span>Launch Security Console</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Configuration Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[#111724] border border-[#1e2738] rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Lock className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Default-DENY Posture</h3>
                <p className="text-xs text-slate-400">Rule 185 capability boundaries</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every newly registered AI agent runs in restricted isolation. Capabilities such as tool execution, state changes, and memory access must be explicitly authorized.
            </p>
            <Link
              href="/security"
              className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              Configure Agent Capabilities &rarr;
            </Link>
          </div>

          <div className="bg-[#111724] border border-[#1e2738] rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-rose-600/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">PromptGuard &amp; Secret Redaction</h3>
                <p className="text-xs text-slate-400">Rule 169 untrusted input isolation</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Sanitizes untrusted prompt inputs, detects jailbreak attempts, and prevents credential leakage across company tenant boundaries.
            </p>
            <Link
              href="/security"
              className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              Open PromptGuard Testbench &rarr;
            </Link>
          </div>
        </div>
      </div>
    </ShellLayout>
  );
}
