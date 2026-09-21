"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, User } from "@/lib/api";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface ShellLayoutProps {
  pageTitle: string;
  breadcrumb?: string;
  children: React.ReactNode;
}

export function ShellLayout({ pageTitle, breadcrumb = "Company OS", children }: ShellLayoutProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function verifyAuth() {
      try {
        const profile = await api.getMe();
        if (mounted) {
          setUser(profile);
          setLoading(false);
        }
      } catch {
        if (mounted) {
          router.push("/login");
        }
      }
    }

    verifyAuth();

    return () => {
      mounted = false;
    };
  }, [router]);

  async function handleLogout() {
    try {
      await api.logout();
    } catch {
      // Proceed with redirect regardless of logout response
    }
    router.push("/login");
    router.refresh();
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center text-slate-400">
        <div className="w-10 h-10 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-4"></div>
        <p className="text-xs font-mono uppercase tracking-widest text-slate-400">
          Verifying Authoritative Session…
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#09090b] text-slate-100">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <Sidebar user={user} onLogout={handleLogout} />
      </div>

      {/* Mobile Sidebar Overlay / Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-[#0c1017] shadow-2xl">
            <Sidebar
              user={user}
              onLogout={handleLogout}
              onCloseMobile={() => setMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar
          user={user}
          pageTitle={pageTitle}
          breadcrumb={breadcrumb}
          onLogout={handleLogout}
          onToggleMobileMenu={() => setMobileMenuOpen(true)}
        />

        <main className="flex-1 overflow-y-auto bg-[#09090b]">
          <div className="max-w-[1600px] mx-auto p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
