"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Clock, Shield } from "lucide-react";

interface PhaseBoundaryCardProps {
  title: string;
  phaseNumber: number;
  phaseName: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  plannedFeatures: string[];
  docSection?: string;
}

export function PhaseBoundaryCard({
  title,
  phaseNumber,
  phaseName,
  icon: Icon,
  description,
  plannedFeatures,
  docSection,
}: PhaseBoundaryCardProps) {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 pb-4 border-b border-[#1e2738]">
        <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400">
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-white">{title}</h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Phase {phaseNumber}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400">{phaseName}</p>
        </div>
      </div>

      {/* Main Roadmap Notice Card */}
      <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 sm:p-8 space-y-6">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0 mt-1">
            <Clock className="w-5 h-5" />
          </div>
          <div className="space-y-2">
            <h2 className="text-base font-semibold text-white">
              Scheduled Roadmap Section
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {description}
            </p>
          </div>
        </div>

        {/* Planned Capabilities */}
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Planned Capabilities for Phase {phaseNumber}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {plannedFeatures.map((feature) => (
              <div
                key={feature}
                className="p-3 rounded-lg bg-[#0c1017] border border-[#1e2738] flex items-center gap-2.5 text-xs text-slate-300"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Phase Integrity Guarantee */}
        <div className="p-4 rounded-lg bg-[#0c1017]/60 border border-[#1e2738] flex items-start gap-3">
          <Shield className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-semibold text-slate-200">
              Zero Mock Data Policy (docs/Rules.md § 2.3)
            </span>
            <p className="text-slate-400 leading-relaxed">
              Per project specifications, no simulated entities or fabricated states are introduced.
              Authoritative database tables, domain services, and APIs will be established upon authorization of Phase {phaseNumber}.
            </p>
          </div>
        </div>

        {/* Actions & Documentation reference */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-4 border-t border-[#1e2738]">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <BookOpen className="w-4 h-4 text-indigo-400" />
            <span>
              Specification:{" "}
              <code className="text-slate-300 font-mono">
                docs/Phases.md {docSection ? `§ ${docSection}` : ""}
              </code>
            </span>
          </div>

          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition shadow-sm self-start sm:self-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Executive Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
