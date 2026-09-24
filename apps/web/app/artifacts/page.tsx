"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Bot,
  Calendar,
  Check,
  Code2,
  Copy,
  Download,
  Eye,
  FileCode,
  FileSpreadsheet,
  FileText,
  Filter,
  GitBranch,
  History,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Tag,
  Trash2,
  User as UserIcon,
  X,
} from "lucide-react";
import {
  api,
  Artifact,
  ArtifactCreatePayload,
  ArtifactType,
  ArtifactVersionCreatePayload,
  ArtifactVersionItem,
  Company,
  Project,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const TYPE_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  MARKDOWN: {
    label: "Markdown",
    bg: "bg-indigo-500/10",
    text: "text-indigo-400",
    border: "border-indigo-500/25",
    icon: FileText,
  },
  CODE: {
    label: "Code",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/25",
    icon: Code2,
  },
  JSON: {
    label: "JSON",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/25",
    icon: FileCode,
  },
  CSV: {
    label: "CSV / Table",
    bg: "bg-sky-500/10",
    text: "text-sky-400",
    border: "border-sky-500/25",
    icon: FileSpreadsheet,
  },
  REPORT: {
    label: "Executive Report",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/25",
    icon: Layers,
  },
  PDF: {
    label: "PDF Doc",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/25",
    icon: FileText,
  },
  TEXT: {
    label: "Plain Text",
    bg: "bg-slate-500/10",
    text: "text-slate-300",
    border: "border-slate-500/25",
    icon: FileText,
  },
  IMAGE: {
    label: "Image / Asset",
    bg: "bg-pink-500/10",
    text: "text-pink-400",
    border: "border-pink-500/25",
    icon: Layers,
  },
  DOCUMENT: {
    label: "Document",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/25",
    icon: FileText,
  },
};

function formatBytes(bytes: number): string {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function ArtifactsPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedProjectId, setSelectedProjectId] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Drawer & Selection
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [lineageVersions, setLineageVersions] = useState<ArtifactVersionItem[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [copied, setCopied] = useState(false);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Create Form State
  const [createForm, setCreateForm] = useState({
    name: "",
    artifact_type: "MARKDOWN" as ArtifactType,
    project_id: "",
    location: "",
    content: "",
    change_summary: "Initial draft",
    tags: "",
  });

  // Version Form State
  const [versionForm, setVersionForm] = useState({
    content: "",
    change_summary: "",
    creator_name: "",
  });

  // Load Companies
  const loadCompanies = useCallback(async () => {
    try {
      const items = await api.getCompanies();
      setCompanies(items || []);
      if (items && items.length > 0 && !selectedCompanyId) {
        setSelectedCompanyId(items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load companies");
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    loadCompanies();
  }, [loadCompanies]);

  // Load Artifacts and Projects
  const loadData = useCallback(async () => {
    if (!selectedCompanyId) return;
    try {
      setRefreshing(true);
      setError(null);

      const [artRes, projRes] = await Promise.all([
        api.getCompanyArtifacts(selectedCompanyId, {
          artifact_type: selectedType !== "ALL" ? selectedType : undefined,
          project_id: selectedProjectId !== "ALL" ? selectedProjectId : undefined,
          search: searchQuery || undefined,
          page_size: 100,
        }),
        api.getProjects(selectedCompanyId).catch(() => ({ items: [] })),
      ]);

      setArtifacts(artRes.items || []);
      setProjects(projRes.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load artifacts");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedCompanyId, selectedType, selectedProjectId, searchQuery]);

  useEffect(() => {
    if (selectedCompanyId) {
      loadData();
    }
  }, [selectedCompanyId, loadData]);

  // Handle Artifact Selection & Version Lineage Fetching
  const handleSelectArtifact = async (artifact: Artifact) => {
    setSelectedArtifact(artifact);
    setLoadingVersions(true);
    try {
      const versions = await api.getArtifactVersions(selectedCompanyId, artifact.id);
      setLineageVersions(versions);
    } catch {
      setLineageVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  };

  // Switch to a specific version within lineage
  const handleSwitchVersion = async (versionItemId: string) => {
    if (!selectedCompanyId) return;
    try {
      const art = await api.getArtifact(selectedCompanyId, versionItemId);
      setSelectedArtifact(art);
    } catch (err) {
      console.error("Failed to fetch version item:", err);
    }
  };

  // Create Root Artifact
  const handleCreateArtifact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompanyId || !createForm.name) return;
    setSubmitting(true);
    try {
      const tagsList = createForm.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      const payload: ArtifactCreatePayload = {
        name: createForm.name,
        artifact_type: createForm.artifact_type,
        project_id: createForm.project_id || undefined,
        location: createForm.location || undefined,
        content: createForm.content || undefined,
        change_summary: createForm.change_summary || "Initial version",
        metadata: tagsList.length > 0 ? { tags: tagsList } : {},
      };

      const created = await api.createArtifact(selectedCompanyId, payload);
      setShowCreateModal(false);
      setCreateForm({
        name: "",
        artifact_type: "MARKDOWN",
        project_id: "",
        location: "",
        content: "",
        change_summary: "Initial draft",
        tags: "",
      });
      await loadData();
      setSelectedArtifact(created);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create artifact");
    } finally {
      setSubmitting(false);
    }
  };

  // Create Version
  const handleCreateVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompanyId || !selectedArtifact || !versionForm.change_summary) return;
    setSubmitting(true);
    try {
      const payload: ArtifactVersionCreatePayload = {
        content: versionForm.content || selectedArtifact.content,
        change_summary: versionForm.change_summary,
        creator_name: versionForm.creator_name || undefined,
      };

      const updated = await api.createArtifactVersion(
        selectedCompanyId,
        selectedArtifact.id,
        payload
      );
      setShowVersionModal(false);
      setVersionForm({ content: "", change_summary: "", creator_name: "" });
      await loadData();
      await handleSelectArtifact(updated);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create new version");
    } finally {
      setSubmitting(false);
    }
  };

  // Delete Artifact
  const handleDeleteArtifact = async (artifact: Artifact) => {
    if (!selectedCompanyId) return;
    if (
      !confirm(
        `Are you sure you want to delete artifact '${artifact.name}' (v${artifact.version})?`
      )
    )
      return;

    try {
      await api.deleteArtifact(selectedCompanyId, artifact.id);
      if (selectedArtifact?.id === artifact.id) {
        setSelectedArtifact(null);
      }
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete artifact");
    }
  };

  const copyContent = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadContent = (filename: string, text: string) => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  // KPI Calculations
  const totalArtifacts = artifacts.length;
  const docCount = artifacts.filter((a) =>
    ["MARKDOWN", "TEXT", "DOCUMENT", "REPORT", "PDF"].includes(a.artifact_type.toUpperCase())
  ).length;
  const codeJsonCount = artifacts.filter((a) =>
    ["CODE", "JSON"].includes(a.artifact_type.toUpperCase())
  ).length;
  const tableDataCount = artifacts.filter((a) =>
    ["CSV", "IMAGE"].includes(a.artifact_type.toUpperCase())
  ).length;

  return (
    <ShellLayout pageTitle="Documents & Artifacts" breadcrumb="Work Management">
      <div className="space-y-6">
        {/* Executive Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1e2738] pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight">
                  Documents &amp; Artifacts
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Authoritative multi-tenant repository of deliverables, specs, code, and versioned assets
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Company Selector */}
            {companies.length > 1 && (
              <select
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
                className="bg-[#111724] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={() => loadData()}
              disabled={refreshing}
              className="p-2 rounded-lg bg-[#111724] border border-[#1e2738] text-slate-400 hover:text-white transition disabled:opacity-50"
              title="Refresh artifacts"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
            </button>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
            >
              <Plus className="w-4 h-4" />
              <span>New Artifact</span>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/25 flex items-center gap-3 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Executive KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0c1017] flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Total Artifacts
              </p>
              <p className="text-2xl font-bold text-white mt-1">{totalArtifacts}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0c1017] flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Specs &amp; Documents
              </p>
              <p className="text-2xl font-bold text-indigo-400 mt-1">{docCount}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0c1017] flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Code &amp; JSON
              </p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{codeJsonCount}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Code2 className="w-5 h-5" />
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0c1017] flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Datasets &amp; Assets
              </p>
              <p className="text-2xl font-bold text-sky-400 mt-1">{tableDataCount}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3 rounded-xl bg-[#0c1017] border border-[#1e2738]">
          <div className="flex items-center gap-2 flex-1 max-w-md bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-1.5 focus-within:border-indigo-500 transition">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <input
              type="text"
              placeholder="Search by title, author, path, or summary..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-xs text-white placeholder-slate-400 outline-none w-full"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
            {/* Project Filter */}
            {projects.length > 0 && (
              <div className="flex items-center gap-1.5 bg-[#111724] border border-[#1e2738] px-2.5 py-1.5 rounded-lg text-xs shrink-0">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="bg-transparent text-xs text-slate-300 outline-none cursor-pointer"
                >
                  <option value="ALL">All Projects</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Type Filters */}
            <div className="flex items-center gap-1 bg-[#111724] p-1 rounded-lg border border-[#1e2738] shrink-0">
              {["ALL", "MARKDOWN", "CODE", "JSON", "CSV", "REPORT"].map((type) => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition ${
                    selectedType === type
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {type === "ALL" ? "All Types" : type}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Artifacts Grid / Empty State */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            <p className="text-xs">Loading artifacts and documents...</p>
          </div>
        ) : artifacts.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3 border border-dashed border-[#1e2738] rounded-xl bg-[#0c1017]">
            <div className="w-12 h-12 rounded-xl bg-slate-800/50 flex items-center justify-center text-slate-500">
              <FileText className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-300">No artifacts found</p>
            <p className="text-xs text-slate-400 text-center max-w-sm">
              No documents, reports, or deliverables match your active search and filter criteria.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 text-xs font-semibold px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition"
            >
              Create First Artifact
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {artifacts.map((art) => {
              const typeCfg = TYPE_CONFIG[art.artifact_type.toUpperCase()] || TYPE_CONFIG.DOCUMENT;
              const TypeIcon = typeCfg.icon;
              const proj = projects.find((p) => p.id === art.project_id);

              return (
                <div
                  key={art.id}
                  className={`p-4 rounded-xl border transition flex flex-col justify-between group hover:border-indigo-500/40 ${
                    selectedArtifact?.id === art.id
                      ? "bg-indigo-950/20 border-indigo-500/50 shadow-md"
                      : "bg-[#0c1017] border-[#1e2738]"
                  }`}
                >
                  <div className="space-y-3">
                    {/* Top Row: Type & Version */}
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${typeCfg.bg} ${typeCfg.text} ${typeCfg.border}`}
                      >
                        <TypeIcon className="w-3.5 h-3.5" />
                        {typeCfg.label}
                      </span>

                      <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-[#111724] border border-[#1e2738] text-indigo-400">
                        v{art.version}
                      </span>
                    </div>

                    {/* Title */}
                    <div>
                      <h3 className="font-semibold text-sm text-white group-hover:text-indigo-300 transition line-clamp-1">
                        {art.name}
                      </h3>
                      {art.location && (
                        <p className="text-[11px] font-mono text-slate-400 truncate mt-0.5">
                          {art.location}
                        </p>
                      )}
                    </div>

                    {/* Change Summary */}
                    {art.change_summary && (
                      <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed bg-[#111724]/60 p-2 rounded-lg border border-[#1e2738]/60">
                        {art.change_summary}
                      </p>
                    )}
                  </div>

                  {/* Bottom Meta & Actions */}
                  <div className="mt-4 pt-3 border-t border-[#1e2738] space-y-2.5">
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <div className="flex items-center gap-1.5 truncate">
                        {art.created_by_agent_id ? (
                          <Bot className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        ) : (
                          <UserIcon className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        )}
                        <span className="truncate">{art.creator_name}</span>
                      </div>
                      <span className="font-mono text-slate-400">{formatBytes(art.file_size_bytes)}</span>
                    </div>

                    {proj && (
                      <div className="flex items-center gap-1 text-[10px] text-slate-400 truncate">
                        <Tag className="w-3 h-3 text-slate-500" />
                        <span className="truncate">{proj.name}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-1 gap-2">
                      <button
                        onClick={() => handleSelectArtifact(art)}
                        className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Preview</span>
                      </button>

                      <button
                        onClick={() => {
                          setSelectedArtifact(art);
                          setVersionForm({
                            content: art.content || "",
                            change_summary: "",
                            creator_name: "",
                          });
                          setShowVersionModal(true);
                        }}
                        className="p-1.5 rounded-lg bg-[#111724] border border-[#1e2738] text-slate-400 hover:text-white transition"
                        title="New Version"
                      >
                        <GitBranch className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleDeleteArtifact(art)}
                        className="p-1.5 rounded-lg bg-[#111724] border border-[#1e2738] text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Document Preview Drawer */}
        {selectedArtifact && (
          <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-[#0c1017] border-l border-[#1e2738] shadow-2xl z-50 flex flex-col">
            {/* Drawer Header */}
            <div className="p-5 border-b border-[#1e2738] flex items-center justify-between bg-[#0a0e14]">
              <div className="space-y-1 min-w-0 pr-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-600/20 text-indigo-400 border border-indigo-500/40">
                    v{selectedArtifact.version}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    {formatBytes(selectedArtifact.file_size_bytes)}
                  </span>
                </div>
                <h2 className="text-base font-bold text-white truncate">
                  {selectedArtifact.name}
                </h2>
                {selectedArtifact.location && (
                  <p className="text-xs font-mono text-slate-400 truncate">
                    {selectedArtifact.location}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {selectedArtifact.content && (
                  <>
                    <button
                      onClick={() => copyContent(selectedArtifact.content || "")}
                      className="p-2 rounded-lg bg-[#111724] border border-[#1e2738] text-slate-400 hover:text-white transition"
                      title="Copy content"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() =>
                        downloadContent(
                          selectedArtifact.name,
                          selectedArtifact.content || ""
                        )
                      }
                      className="p-2 rounded-lg bg-[#111724] border border-[#1e2738] text-slate-400 hover:text-white transition"
                      title="Download file"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </>
                )}

                <button
                  onClick={() => setSelectedArtifact(null)}
                  className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition"
                  title="Close preview"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Version Lineage Bar */}
            {lineageVersions.length > 1 && (
              <div className="px-5 py-2.5 bg-[#111724]/70 border-b border-[#1e2738] flex items-center gap-2 overflow-x-auto">
                <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 shrink-0">
                  <History className="w-3.5 h-3.5" />
                  Lineage:
                </span>
                {lineageVersions.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => handleSwitchVersion(v.id)}
                    className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition shrink-0 ${
                      selectedArtifact.id === v.id
                        ? "bg-indigo-600 text-white shadow-xs"
                        : "bg-[#0c1017] border border-[#1e2738] text-slate-400 hover:text-white"
                    }`}
                    title={v.change_summary || undefined}
                  >
                    v{v.version} ({v.creator_name})
                  </button>
                ))}
              </div>
            )}

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              {/* Attribution and Change Notes */}
              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-[#111724] border border-[#1e2738] text-xs">
                <div>
                  <span className="text-[11px] text-slate-400 block font-medium">Created By</span>
                  <span className="text-white font-semibold flex items-center gap-1.5 mt-0.5">
                    {selectedArtifact.created_by_agent_id ? (
                      <Bot className="w-3.5 h-3.5 text-indigo-400" />
                    ) : (
                      <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                    )}
                    {selectedArtifact.creator_name}
                  </span>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400 block font-medium">Recorded Date</span>
                  <span className="text-slate-300 font-mono text-[11px] mt-0.5 block">
                    {new Date(selectedArtifact.created_at).toLocaleString()}
                  </span>
                </div>
                {selectedArtifact.change_summary && (
                  <div className="col-span-2 pt-2 border-t border-[#1e2738]/60">
                    <span className="text-[11px] text-slate-400 block font-medium">Change Summary</span>
                    <span className="text-slate-200 text-xs mt-0.5 block leading-relaxed">
                      {selectedArtifact.change_summary}
                    </span>
                  </div>
                )}
              </div>

              {/* Content Preview */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Content Viewer ({selectedArtifact.artifact_type})
                  </h4>
                </div>

                {selectedArtifact.content ? (
                  <div className="p-4 rounded-xl bg-[#090d14] border border-[#1e2738] font-mono text-xs text-slate-200 leading-relaxed overflow-x-auto whitespace-pre-wrap select-text max-h-[500px]">
                    {selectedArtifact.content}
                  </div>
                ) : (
                  <div className="py-12 flex flex-col items-center justify-center text-slate-500 border border-dashed border-[#1e2738] rounded-xl">
                    <FileText className="w-8 h-8 mb-2 opacity-50" />
                    <p className="text-xs">No direct text content stored.</p>
                    {selectedArtifact.location && (
                      <p className="text-[11px] font-mono text-slate-400 mt-1">
                        Located at: {selectedArtifact.location}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Metadata Inspector */}
              {selectedArtifact.metadata && Object.keys(selectedArtifact.metadata).length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Metadata Attributes
                  </h4>
                  <pre className="p-3.5 rounded-xl bg-[#090d14] border border-[#1e2738] font-mono text-xs text-indigo-300 overflow-x-auto">
                    {JSON.stringify(selectedArtifact.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Drawer Footer Actions */}
            <div className="p-4 border-t border-[#1e2738] bg-[#0a0e14] flex items-center justify-between">
              <button
                onClick={() => {
                  setVersionForm({
                    content: selectedArtifact.content || "",
                    change_summary: "",
                    creator_name: "",
                  });
                  setShowVersionModal(true);
                }}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-xs transition"
              >
                <GitBranch className="w-4 h-4" />
                <span>Create New Version (v{selectedArtifact.version + 1})</span>
              </button>

              <button
                onClick={() => handleDeleteArtifact(selectedArtifact)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-xs font-medium transition"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete</span>
              </button>
            </div>
          </div>
        )}

        {/* Create Root Artifact Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="w-full max-w-lg bg-[#0c1017] border border-[#1e2738] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
              <div className="p-5 border-b border-[#1e2738] flex items-center justify-between bg-[#0a0e14]">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-indigo-600/15 border border-indigo-500/30 text-indigo-400">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white">Create New Artifact</h3>
                    <p className="text-[11px] text-slate-400">
                      Author and store a persistent document or deliverable
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-md"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateArtifact} className="p-5 overflow-y-auto space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Artifact Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Architecture RFC, System Schema v1"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Artifact Type
                    </label>
                    <select
                      value={createForm.artifact_type}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          artifact_type: e.target.value as ArtifactType,
                        })
                      }
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                    >
                      <option value="MARKDOWN">Markdown Document</option>
                      <option value="CODE">Code Snippet</option>
                      <option value="JSON">JSON Data</option>
                      <option value="CSV">CSV Table</option>
                      <option value="REPORT">Executive Report</option>
                      <option value="TEXT">Plain Text</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Project Association
                    </label>
                    <select
                      value={createForm.project_id}
                      onChange={(e) => setCreateForm({ ...createForm, project_id: e.target.value })}
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                    >
                      <option value="">None (Company Global)</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Storage Location / Virtual Path
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. docs/architecture/rfc-001.md"
                    value={createForm.location}
                    onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500 font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Document Content
                  </label>
                  <textarea
                    rows={8}
                    placeholder="Write content or paste markdown, code, or structured text..."
                    value={createForm.content}
                    onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg p-3 outline-none focus:border-indigo-500 font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. spec, architecture, backend"
                    value={createForm.tags}
                    onChange={(e) => setCreateForm({ ...createForm, tags: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="pt-3 border-t border-[#1e2738] flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-[#1e2738] text-slate-300 hover:text-white text-xs transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Save Artifact</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Create Version Modal */}
        {showVersionModal && selectedArtifact && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="w-full max-w-lg bg-[#0c1017] border border-[#1e2738] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
              <div className="p-5 border-b border-[#1e2738] flex items-center justify-between bg-[#0a0e14]">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-indigo-600/15 border border-indigo-500/30 text-indigo-400">
                    <GitBranch className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white">
                      Create Version v{selectedArtifact.version + 1}
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Lineage linked to root &apos;{selectedArtifact.name}&apos;
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowVersionModal(false)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-md"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateVersion} className="p-5 overflow-y-auto space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Change Summary *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Updated Section 3 following architecture review"
                    value={versionForm.change_summary}
                    onChange={(e) =>
                      setVersionForm({ ...versionForm, change_summary: e.target.value })
                    }
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Author / Creator Attribution
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Lead Architect or Dev Agent"
                    value={versionForm.creator_name}
                    onChange={(e) =>
                      setVersionForm({ ...versionForm, creator_name: e.target.value })
                    }
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Updated Content
                  </label>
                  <textarea
                    rows={8}
                    value={versionForm.content}
                    onChange={(e) =>
                      setVersionForm({ ...versionForm, content: e.target.value })
                    }
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg p-3 outline-none focus:border-indigo-500 font-mono"
                  />
                </div>

                <div className="pt-3 border-t border-[#1e2738] flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowVersionModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-[#1e2738] text-slate-300 hover:text-white text-xs transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Publish Version</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}
