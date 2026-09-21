"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Bell,
  CheckCircle2,
  ChevronDown,
  Command,
  LogOut,
  Menu,
  ShieldCheck,
  User as UserIcon,
} from "lucide-react";
import { User } from "@/lib/api";

interface TopBarProps {
  user: User | null;
  pageTitle: string;
  breadcrumb?: string;
  onLogout: () => void;
  onToggleMobileMenu: () => void;
}

export function TopBar({
  user,
  pageTitle,
  breadcrumb = "Company OS",
  onLogout,
  onToggleMobileMenu,
}: TopBarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="h-16 border-b border-[#1e2738] bg-[#0c1017]/95 backdrop-blur px-4 sm:px-6 flex items-center justify-between z-10 sticky top-0">
      {/* Left: Mobile hamburger & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/60"
          aria-label="Toggle navigation drawer"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>{breadcrumb}</span>
            <span>/</span>
            <span className="text-slate-200 font-medium">{pageTitle}</span>
          </div>
        </div>
      </div>

      {/* Center: System Status Indicator */}
      <div className="hidden md:flex items-center gap-2">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>System Foundation: Operational</span>
        </span>
      </div>

      {/* Right: Search, Notifications & User Menu */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Command Search Shortcut Button */}
        <button
          onClick={() => {
            // Accessible command palette trigger placeholder
          }}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-700 transition"
          aria-label="Command search"
        >
          <Command className="w-3.5 h-3.5 text-slate-400" />
          <span>Quick Find</span>
          <kbd className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
            ⌘K
          </kbd>
        </button>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/60 relative"
            aria-label="Notifications"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-lg border border-[#1e2738] bg-[#111724] shadow-xl p-4 text-xs z-50">
              <div className="font-semibold text-white mb-2 flex items-center justify-between">
                <span>Notifications</span>
                <span className="text-[10px] font-mono text-slate-400">0 unread</span>
              </div>
              <div className="py-4 text-center text-slate-400">
                <p>No operational notifications</p>
                <p className="text-[10px] text-slate-500 mt-1">
                  Alerting & event feeds activate in Phase 13
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Operator Profile Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-800/60 transition border border-transparent hover:border-slate-700/60"
            aria-label="User menu"
          >
            <div className="w-7 h-7 rounded-full bg-indigo-600/25 border border-indigo-500/40 text-indigo-300 flex items-center justify-center text-xs font-semibold">
              {user?.name ? user.name[0].toUpperCase() : "O"}
            </div>
            <div className="hidden xl:block text-left">
              <span className="block text-xs font-semibold text-white leading-tight">
                {user?.name || "Operator"}
              </span>
              <span className="block text-[10px] text-slate-400 font-mono leading-tight">
                Admin
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl border border-[#1e2738] bg-[#111724] shadow-2xl p-2 z-50">
              <div className="px-3 py-2 border-b border-[#1e2738] mb-1">
                <p className="text-xs font-semibold text-white">{user?.name || "Operator"}</p>
                <p className="text-[11px] text-slate-400 font-mono truncate">{user?.email}</p>
                <div className="mt-2 flex items-center gap-1.5 text-[10px] text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-800/40">
                  <ShieldCheck className="w-3 h-3" />
                  <span>Session: PostgreSQL Active</span>
                </div>
              </div>

              <div className="py-1 text-xs text-slate-300 space-y-0.5">
                <Link
                  href="/settings"
                  className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-slate-800/60 text-slate-300 hover:text-white"
                >
                  <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                  <span>Account & Preferences</span>
                </Link>
              </div>

              <div className="border-t border-[#1e2738] pt-1 mt-1">
                <button
                  onClick={onLogout}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-md text-xs text-rose-400 hover:bg-rose-500/10 transition"
                >
                  <span>Sign Out</span>
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
