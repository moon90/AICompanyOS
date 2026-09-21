"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Edit3,
  Globe,
  Plus,
  Save,
  Shield,
  Sparkles,
  Users,
  Layers,
} from "lucide-react";
import { api, Company, Department, CompanyMember } from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function CompanyPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [members, setMembers] = useState<CompanyMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "departments" | "chart" | "members" | "settings">("overview");

  // Creation form state
  const [createName, setCreateName] = useState("");
  const [createIndustry, setCreateIndustry] = useState("");
  const [createMission, setCreateMission] = useState("");
  const [createDescription, setCreateDescription] = useState("");
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Department creation state
  const [showAddDept, setShowAddDept] = useState(false);
  const [deptName, setDeptName] = useState("");
  const [deptCode, setDeptCode] = useState("");
  const [deptLeadRole, setDeptLeadRole] = useState("");
  const [deptDescription, setDeptDescription] = useState("");
  const [deptSubmitting, setDeptSubmitting] = useState(false);
  const [deptError, setDeptError] = useState<string | null>(null);

  // Company settings edit state
  const [editName, setEditName] = useState("");
  const [editIndustry, setEditIndustry] = useState("");
  const [editMission, setEditMission] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editSuccess, setEditSuccess] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  async function loadCompanyData() {
    setLoading(true);
    try {
      const compList = await api.getCompanies();
      setCompanies(compList);
      if (compList.length > 0) {
        const current = compList[0];
        setSelectedCompany(current);
        setEditName(current.name);
        setEditIndustry(current.industry || "");
        setEditMission(current.mission || "");
        setEditDescription(current.description || "");

        const [depts, mems] = await Promise.all([
          api.getDepartments(current.id),
          api.getCompanyMembers(current.id),
        ]);
        setDepartments(depts);
        setMembers(mems);
      }
    } catch {
      // Handled gracefully in UI
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCompanyData();
  }, []);

  async function handleCreateCompany(e: React.FormEvent) {
    e.preventDefault();
    setCreateSubmitting(true);
    setCreateError(null);

    try {
      const company = await api.createCompany({
        name: createName,
        industry: createIndustry || undefined,
        mission: createMission || undefined,
        description: createDescription || undefined,
      });
      setSelectedCompany(company);
      await loadCompanyData();
    } catch (err: unknown) {
      const errorMsg = err && typeof err === "object" && "detail" in err
        ? String((err as { detail: string }).detail)
        : "Failed to create company.";
      setCreateError(errorMsg);
    } finally {
      setCreateSubmitting(false);
    }
  }

  async function handleCreateDepartment(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCompany) return;
    setDeptSubmitting(true);
    setDeptError(null);

    try {
      await api.createDepartment(selectedCompany.id, {
        name: deptName,
        code: deptCode,
        lead_role: deptLeadRole || undefined,
        description: deptDescription || undefined,
      });
      setDeptName("");
      setDeptCode("");
      setDeptLeadRole("");
      setDeptDescription("");
      setShowAddDept(false);

      const refreshed = await api.getDepartments(selectedCompany.id);
      setDepartments(refreshed);
    } catch (err: unknown) {
      const errorMsg = err && typeof err === "object" && "detail" in err
        ? String((err as { detail: string }).detail)
        : "Failed to create department.";
      setDeptError(errorMsg);
    } finally {
      setDeptSubmitting(false);
    }
  }

  async function handleUpdateCompany(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCompany) return;
    setEditSubmitting(true);
    setEditError(null);
    setEditSuccess(false);

    try {
      const updated = await api.updateCompany(selectedCompany.id, {
        name: editName,
        industry: editIndustry || undefined,
        mission: editMission || undefined,
        description: editDescription || undefined,
      });
      setSelectedCompany(updated);
      setEditSuccess(true);
      await loadCompanyData();
    } catch (err: unknown) {
      const errorMsg = err && typeof err === "object" && "detail" in err
        ? String((err as { detail: string }).detail)
        : "Failed to update company settings.";
      setEditError(errorMsg);
    } finally {
      setEditSubmitting(false);
    }
  }

  if (loading) {
    return (
      <ShellLayout pageTitle="Company" breadcrumb="Organization">
        <div className="flex flex-col items-center justify-center py-24 text-slate-400">
          <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mb-3"></div>
          <span className="text-xs font-mono uppercase tracking-wider">Loading Company Profile…</span>
        </div>
      </ShellLayout>
    );
  }

  // State 1: No company exists yet
  if (!selectedCompany) {
    return (
      <ShellLayout pageTitle="Company" breadcrumb="Organization">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="text-center pb-2">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 mx-auto mb-3">
              <Building2 className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white mb-1">
              Initialize Your AI Company
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
              Create your primary company organization. Standard departmental structures (CTO, CMO, Sales, Finance, Operations)
              will be provisioned automatically per <code className="text-slate-300 font-mono">docs/Phases.md</code> § 7.
            </p>
          </div>

          <form
            onSubmit={handleCreateCompany}
            className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 sm:p-8 space-y-5"
          >
            {createError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{createError}</span>
              </div>
            )}

            <div>
              <label htmlFor="company-name" className="block text-xs font-medium text-slate-300 mb-1.5">
                Company Name <span className="text-rose-400">*</span>
              </label>
              <input
                id="company-name"
                type="text"
                required
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="e.g. Apex Autonomous Technologies"
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              />
            </div>

            <div>
              <label htmlFor="industry" className="block text-xs font-medium text-slate-300 mb-1.5">
                Industry Sector
              </label>
              <input
                id="industry"
                type="text"
                value={createIndustry}
                onChange={(e) => setCreateIndustry(e.target.value)}
                placeholder="e.g. Artificial Intelligence, FinTech, Enterprise Software"
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              />
            </div>

            <div>
              <label htmlFor="mission" className="block text-xs font-medium text-slate-300 mb-1.5">
                Mission Statement
              </label>
              <textarea
                id="mission"
                rows={3}
                value={createMission}
                onChange={(e) => setCreateMission(e.target.value)}
                placeholder="Core purpose and primary objective of the company"
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition resize-none"
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-xs font-medium text-slate-300 mb-1.5">
                Company Description
              </label>
              <textarea
                id="description"
                rows={3}
                value={createDescription}
                onChange={(e) => setCreateDescription(e.target.value)}
                placeholder="Detailed summary of business activities and strategy"
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={createSubmitting || !createName.trim()}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-medium text-white transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
            >
              {createSubmitting ? (
                <span>Establishing Company…</span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Establish Company Profile</span>
                </>
              )}
            </button>
          </form>
        </div>
      </ShellLayout>
    );
  }

  // State 2: Company exists
  return (
    <ShellLayout pageTitle="Company" breadcrumb="Organization">
      <div className="space-y-6">
        {/* Company Header Banner */}
        <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 mb-1 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {selectedCompany.name}
                </h1>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  {selectedCompany.status.toUpperCase()}
                </span>
                {selectedCompany.user_role && (
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/60">
                    Role: {selectedCompany.user_role.toUpperCase()}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-3">
                <span>Industry: {selectedCompany.industry || "General Enterprise"}</span>
                <span>•</span>
                <span>Established: {new Date(selectedCompany.created_at).toLocaleDateString()}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <span className="text-xs font-mono text-slate-400 bg-[#0c1017] px-3 py-1.5 rounded-lg border border-[#1e2738]">
              ID: {selectedCompany.id.slice(0, 8)}…
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-[#1e2738] flex gap-2 overflow-x-auto select-none">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "overview"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Overview & Mission
          </button>
          <button
            onClick={() => setActiveTab("departments")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap flex items-center gap-2 ${
              activeTab === "departments"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>Departments</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
              {departments.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("chart")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "chart"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Organizational Structure
          </button>
          <button
            onClick={() => setActiveTab("members")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap flex items-center gap-2 ${
              activeTab === "members"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>Members & Governance</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
              {members.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("settings")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "settings"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Settings
          </button>
        </div>

        {/* Tab 1: Overview & Mission */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Mission Statement Card */}
            <div className="rounded-xl border border-indigo-500/30 bg-gradient-to-br from-[#111724] to-[#0d131f] p-6">
              <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-2">
                <Sparkles className="w-4 h-4" />
                <span>Company Mission</span>
              </div>
              <p className="text-base sm:text-lg text-slate-100 font-medium leading-relaxed italic">
                &ldquo;{selectedCompany.mission || "No mission statement established yet."}&rdquo;
              </p>
            </div>

            {/* Description & Metadata Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 rounded-xl border border-[#1e2738] bg-[#111724] p-6 space-y-4">
                <h3 className="text-sm font-semibold text-white">Company Narrative & Description</h3>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                  {selectedCompany.description || "No company description provided."}
                </p>
              </div>

              <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 space-y-4">
                <h3 className="text-sm font-semibold text-white">Operational Summary</h3>
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-[#1e2738]">
                    <span className="text-slate-400">Industry Sector</span>
                    <span className="text-white font-medium">{selectedCompany.industry || "Unassigned"}</span>
                  </div>
                  <div className="flex items-center justify-between pb-2 border-b border-[#1e2738]">
                    <span className="text-slate-400">Total Departments</span>
                    <span className="text-white font-mono font-medium">{departments.length}</span>
                  </div>
                  <div className="flex items-center justify-between pb-2 border-b border-[#1e2738]">
                    <span className="text-slate-400">Governance Members</span>
                    <span className="text-white font-mono font-medium">{members.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Tenant Authority</span>
                    <span className="text-emerald-400 font-mono text-[11px]">PostgreSQL Scoped</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Departments */}
        {activeTab === "departments" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white">Organizational Departments</h2>
                <p className="text-xs text-slate-400">
                  Standard departments provisioned per <code className="text-slate-300 font-mono">docs/Phases.md</code> § 7.
                </p>
              </div>

              <button
                onClick={() => setShowAddDept(!showAddDept)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Department</span>
              </button>
            </div>

            {/* Add Department Drawer */}
            {showAddDept && (
              <form
                onSubmit={handleCreateDepartment}
                className="rounded-xl border border-indigo-500/30 bg-[#0e1420] p-5 space-y-4"
              >
                <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                  <h3 className="text-xs font-semibold text-white uppercase tracking-wide">
                    New Department Configuration
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowAddDept(false)}
                    className="text-slate-400 hover:text-white text-xs"
                  >
                    Cancel
                  </button>
                </div>

                {deptError && (
                  <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{deptError}</span>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label htmlFor="new-dept-name" className="block text-xs font-medium text-slate-300 mb-1">
                      Department Name *
                    </label>
                    <input
                      id="new-dept-name"
                      type="text"
                      required
                      value={deptName}
                      onChange={(e) => setDeptName(e.target.value)}
                      placeholder="e.g. Legal & Compliance"
                      className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="new-dept-code" className="block text-xs font-medium text-slate-300 mb-1">
                      Department Code *
                    </label>
                    <input
                      id="new-dept-code"
                      type="text"
                      required
                      value={deptCode}
                      onChange={(e) => setDeptCode(e.target.value)}
                      placeholder="e.g. legal"
                      className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="new-dept-lead" className="block text-xs font-medium text-slate-300 mb-1">
                      Lead Role Title
                    </label>
                    <input
                      id="new-dept-lead"
                      type="text"
                      value={deptLeadRole}
                      onChange={(e) => setDeptLeadRole(e.target.value)}
                      placeholder="e.g. General Counsel"
                      className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="new-dept-desc" className="block text-xs font-medium text-slate-300 mb-1">
                    Department Mission / Responsibilities
                  </label>
                  <input
                    id="new-dept-desc"
                    type="text"
                    value={deptDescription}
                    onChange={(e) => setDeptDescription(e.target.value)}
                    placeholder="Short description of department objective"
                    className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={deptSubmitting || !deptName.trim() || !deptCode.trim()}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition disabled:opacity-50"
                >
                  {deptSubmitting ? "Saving Department…" : "Save Department"}
                </button>
              </form>
            )}

            {/* Department Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {departments.map((dept) => (
                <div
                  key={dept.id}
                  className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 flex flex-col justify-between space-y-4 hover:border-slate-700 transition"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-white">{dept.name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {dept.code}
                      </span>
                    </div>

                    <div className="text-xs font-medium text-indigo-400 mb-2">
                      {dept.lead_role || "Department Head"}
                    </div>

                    <p className="text-xs text-slate-400 leading-relaxed">
                      {dept.description || "No specific mission defined."}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[#1e2738] flex items-center justify-between text-[11px] text-slate-400">
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      {dept.status}
                    </span>
                    <span className="font-mono text-[10px]">
                      Phase 4 Runtime Slot
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Organizational Hierarchy Chart */}
        {activeTab === "chart" && (
          <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 sm:p-8 space-y-8">
            <div>
              <h2 className="text-base font-semibold text-white mb-1">
                Company Organizational Structure
              </h2>
              <p className="text-xs text-slate-400">
                Authoritative hierarchy per <code className="text-slate-300 font-mono">docs/Phases.md</code> § 7.
                Execution runtime agents belong to Phase 4.
              </p>
            </div>

            {/* Org Tree Visualization */}
            <div className="flex flex-col items-center max-w-2xl mx-auto space-y-4 py-4">
              {/* Level 1: Founder / Owner */}
              <div className="w-64 rounded-xl border border-indigo-500/40 bg-indigo-950/20 p-4 text-center shadow-lg">
                <div className="text-[10px] font-mono uppercase text-indigo-400 mb-0.5">
                  Human Authority (docs/Rules.md § 3)
                </div>
                <div className="text-sm font-bold text-white">
                  Founder & Owner
                </div>
                <div className="text-xs text-slate-400 mt-1 font-mono">
                  {members[0]?.user_name || "Authorized Operator"}
                </div>
              </div>

              {/* Vertical Connector */}
              <div className="w-0.5 h-6 bg-indigo-500/40"></div>

              {/* Level 2: CEO Orchestrator */}
              <div className="w-64 rounded-xl border border-slate-700 bg-[#0c1017] p-4 text-center relative">
                <div className="text-[10px] font-mono uppercase text-amber-400 mb-0.5 flex items-center justify-center gap-1">
                  <span>Executive Orchestrator</span>
                </div>
                <div className="text-sm font-bold text-white">
                  CEO Agent Loop
                </div>
                <div className="text-[10px] text-slate-400 mt-1 font-mono">
                  Scheduled for Phase 5
                </div>
              </div>

              {/* Vertical Connector */}
              <div className="w-0.5 h-6 bg-slate-700"></div>

              {/* Level 3: Department Heads Grid */}
              <div className="w-full">
                <div className="text-center text-[11px] uppercase tracking-wider text-slate-400 font-mono mb-3">
                  Department Leadership Layer
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {departments.map((dept) => (
                    <div
                      key={dept.id}
                      className="rounded-lg border border-[#1e2738] bg-[#0c1017] p-3 text-center space-y-1 hover:border-indigo-500/40 transition"
                    >
                      <div className="text-xs font-bold text-white">
                        {dept.name}
                      </div>
                      <div className="text-[11px] text-indigo-300 font-medium">
                        {dept.lead_role || "Lead"}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {dept.code.toUpperCase()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Members & Governance */}
        {activeTab === "members" && (
          <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
              <div>
                <h2 className="text-sm font-semibold text-white">Company Governance Members</h2>
                <p className="text-xs text-slate-400">
                  Explicit user-to-company memberships defined in <code className="text-slate-300 font-mono">company_members</code>.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Total Members: {members.length}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1e2738] text-slate-400 font-medium">
                    <th className="py-2.5 px-3">Name</th>
                    <th className="py-2.5 px-3">Email</th>
                    <th className="py-2.5 px-3">Company Role</th>
                    <th className="py-2.5 px-3">Membership Status</th>
                    <th className="py-2.5 px-3">Member Since</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2738] text-slate-200">
                  {members.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-3 font-medium text-white flex items-center gap-2">
                        <Users className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{m.user_name}</span>
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-400">{m.user_email}</td>
                      <td className="py-3 px-3">
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/60">
                          {m.role.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-emerald-400 flex items-center gap-1 font-mono text-[11px]">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          {m.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-400">
                        {new Date(m.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 5: Settings */}
        {activeTab === "settings" && (
          <form
            onSubmit={handleUpdateCompany}
            className="max-w-2xl rounded-xl border border-[#1e2738] bg-[#111724] p-6 sm:p-8 space-y-5"
          >
            <div className="border-b border-[#1e2738] pb-3">
              <h2 className="text-sm font-semibold text-white">Company Profile Settings</h2>
              <p className="text-xs text-slate-400">
                Update operational details for this company entity. Requires administrative role.
              </p>
            </div>

            {editError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{editError}</span>
              </div>
            )}

            {editSuccess && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Company profile updated successfully.</span>
              </div>
            )}

            <div>
              <label htmlFor="edit-name" className="block text-xs font-medium text-slate-300 mb-1.5">
                Company Name
              </label>
              <input
                id="edit-name"
                type="text"
                required
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label htmlFor="edit-industry" className="block text-xs font-medium text-slate-300 mb-1.5">
                Industry
              </label>
              <input
                id="edit-industry"
                type="text"
                value={editIndustry}
                onChange={(e) => setEditIndustry(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label htmlFor="edit-mission" className="block text-xs font-medium text-slate-300 mb-1.5">
                Mission Statement
              </label>
              <textarea
                id="edit-mission"
                rows={3}
                value={editMission}
                onChange={(e) => setEditMission(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"
              />
            </div>

            <div>
              <label htmlFor="edit-desc" className="block text-xs font-medium text-slate-300 mb-1.5">
                Description
              </label>
              <textarea
                id="edit-desc"
                rows={3}
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={editSubmitting || !editName.trim()}
              className="py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition disabled:opacity-50 flex items-center gap-2"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{editSubmitting ? "Saving…" : "Save Changes"}</span>
            </button>
          </form>
        )}
      </div>
    </ShellLayout>
  );
}
