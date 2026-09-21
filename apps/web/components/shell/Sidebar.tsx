"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bot,
  Building2,
  CheckSquare,
  FolderGit2,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldAlert,
  User as UserIcon,
  Users,
  X,
} from "lucide-react";
import { User } from "@/lib/api";

interface SidebarProps {
  user: User | null;
  onLogout: () => void;
  onCloseMobile?: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  phaseBadge?: string;
  isCurrent?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

export function Sidebar({ user, onLogout, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();

  const navGroups: NavGroup[] = [
    {
      label: "Overview",
      items: [
        {
          name: "Dashboard",
          href: "/",
          icon: LayoutDashboard,
          isCurrent: pathname === "/",
        },
      ],
    },
    {
      label: "Organization & Leadership",
      items: [
        {
          name: "Company",
          href: "/company",
          icon: Building2,
          phaseBadge: "Phase 3",
          isCurrent: pathname === "/company",
        },
        {
          name: "CEO Orchestrator",
          href: "/ceo",
          icon: Bot,
          phaseBadge: "Phase 5",
          isCurrent: pathname === "/ceo",
        },
        {
          name: "Agent Registry",
          href: "/agents",
          icon: Users,
          phaseBadge: "Phase 4",
          isCurrent: pathname === "/agents",
        },
      ],
    },
    {
      label: "Work Management",
      items: [
        {
          name: "Projects",
          href: "/projects",
          icon: FolderGit2,
          phaseBadge: "Phase 6",
          isCurrent: pathname === "/projects",
        },
        {
          name: "Tasks",
          href: "/tasks",
          icon: CheckSquare,
          phaseBadge: "Phase 6",
          isCurrent: pathname === "/tasks",
        },
        {
          name: "Approvals",
          href: "/approvals",
          icon: ShieldAlert,
          phaseBadge: "Phase 10",
          isCurrent: pathname === "/approvals",
        },
      ],
    },
    {
      label: "System & Governance",
      items: [
        {
          name: "Activity",
          href: "/activity",
          icon: Activity,
          phaseBadge: "Phase 13",
          isCurrent: pathname === "/activity",
        },
        {
          name: "Settings",
          href: "/settings",
          icon: Settings,
          phaseBadge: "Phase 23",
          isCurrent: pathname === "/settings",
        },
      ],
    },
  ];

  return (
    <aside className="w-72 bg-[#0c1017] border-r border-[#1e2738] flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="h-16 border-b border-[#1e2738] px-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <span className="font-semibold text-sm tracking-tight text-white block">
              AI COMPANY OS
            </span>
            <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">
              Executive Shell
            </span>
          </div>
        </div>

        {/* Mobile close button */}
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800/60"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1">
            <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              {group.label}
            </div>

            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={`group flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    item.isCurrent
                      ? "bg-indigo-600/20 text-white border border-indigo-500/40 shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/50 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={`w-4 h-4 transition-colors ${
                        item.isCurrent
                          ? "text-indigo-400"
                          : "text-slate-400 group-hover:text-slate-200"
                      }`}
                    />
                    <span>{item.name}</span>
                  </div>

                  {item.phaseBadge && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/60">
                      {item.phaseBadge}
                    </span>
                  )}
                  {item.isCurrent && !item.phaseBadge && (
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* CEO Status / Phase Boundary Widget per UI.md § 21 */}
      <div className="p-3 mx-3 mb-3 rounded-lg border border-[#1e2738] bg-[#111724]">
        <div className="flex items-center justify-between text-[11px] mb-1.5">
          <span className="text-slate-400 font-medium">CEO Orchestrator</span>
          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
            Inactive
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Autonomous orchestration activates in <strong className="text-slate-300">Phase 5</strong>.
        </p>
      </div>

      {/* Authenticated Operator Footer per UI.md */}
      <div className="border-t border-[#1e2738] p-3 bg-[#0a0e14]">
        <div className="flex items-center justify-between gap-2 p-1.5 rounded-lg">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0">
              <UserIcon className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white truncate">
                {user?.name || "Authorized Operator"}
              </p>
              <p className="text-[11px] text-slate-400 font-mono truncate">
                {user?.email || "operator@session"}
              </p>
            </div>
          </div>

          <button
            onClick={onLogout}
            title="Sign out of operator session"
            className="p-1.5 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition shrink-0"
            aria-label="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
