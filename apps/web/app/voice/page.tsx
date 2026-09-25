"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  AudioWaveform,
  CheckCircle2,
  ChevronRight,
  Clock,
  ExternalLink,
  Flame,
  History,
  Layers,
  Loader2,
  Mic,
  MicOff,
  Plus,
  RefreshCw,
  Send,
  Sparkles,
  StopCircle,
  Volume2,
  VolumeX,
  Zap,
} from "lucide-react";
import {
  api,
  Company,
  VoiceCommandResponse,
  VoiceIntent,
  VoiceInteractionItem,
  VoiceSessionResponse,
  VoiceState,
  VoiceTelemetryResponse,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const STATE_CONFIG: Record<
  VoiceState,
  { label: string; bg: string; text: string; border: string; pulse: boolean }
> = {
  IDLE: {
    label: "IDLE",
    bg: "bg-slate-500/10",
    text: "text-slate-400",
    border: "border-slate-500/30",
    pulse: false,
  },
  LISTENING: {
    label: "LISTENING",
    bg: "bg-emerald-500/15",
    text: "text-emerald-400",
    border: "border-emerald-500/40",
    pulse: true,
  },
  PROCESSING: {
    label: "PROCESSING",
    bg: "bg-blue-500/15",
    text: "text-blue-400",
    border: "border-blue-500/40",
    pulse: true,
  },
  PLANNING: {
    label: "PLANNING",
    bg: "bg-amber-500/15",
    text: "text-amber-400",
    border: "border-amber-500/40",
    pulse: true,
  },
  EXECUTING: {
    label: "EXECUTING",
    bg: "bg-purple-500/15",
    text: "text-purple-400",
    border: "border-purple-500/40",
    pulse: true,
  },
  WAITING_FOR_APPROVAL: {
    label: "WAITING FOR APPROVAL",
    bg: "bg-rose-500/15",
    text: "text-rose-400",
    border: "border-rose-500/40",
    pulse: true,
  },
  SPEAKING: {
    label: "SPEAKING",
    bg: "bg-cyan-500/15",
    text: "text-cyan-400",
    border: "border-cyan-500/40",
    pulse: true,
  },
};

const INTENT_BADGES: Record<VoiceIntent, { label: string; color: string }> = {
  STATUS_QUERY: { label: "Status Query", color: "text-blue-400 bg-blue-500/10 border-blue-500/30" },
  TASK_CREATE: { label: "Task Creation", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" },
  TASK_CONTROL: { label: "Task Control", color: "text-amber-400 bg-amber-500/10 border-amber-500/30" },
  APPROVAL_DECISION: { label: "Approval", color: "text-purple-400 bg-purple-500/10 border-purple-500/30" },
  DELEGATION_COMMAND: { label: "Delegation", color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/30" },
  GENERAL_INQUIRY: { label: "General", color: "text-slate-400 bg-slate-500/10 border-slate-500/30" },
};

const CANONICAL_PROMPTS = [
  { label: "CEO Briefing", query: "CEO, what's happening?" },
  { label: "Enterprise Pipeline", query: "Show enterprise opportunities" },
  { label: "Blocked Items", query: "Which need attention?" },
  { label: "Delegate Marketing", query: "Ask marketing to draft launch announcement" },
  { label: "Approve Request", query: "Approve that" },
  { label: "Stop Active Task", query: "Stop the task" },
];

export default function VoiceConsolePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Voice Session State
  const [sessions, setSessions] = useState<VoiceSessionResponse[]>([]);
  const [currentSession, setCurrentSession] = useState<VoiceSessionResponse | null>(null);
  const [currentState, setCurrentState] = useState<VoiceState>("IDLE");
  const [telemetry, setTelemetry] = useState<VoiceTelemetryResponse | null>(null);

  // Command & Audio Interaction State
  const [inputTranscript, setInputTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [speechRecognitionSupported, setSpeechRecognitionSupported] = useState(false);

  // Audio Recognition ref
  const recognitionRef = useRef<any>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of conversation
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentSession?.interactions, isProcessing]);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        setSpeechRecognitionSupported(true);
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onstart = () => {
          setIsListening(true);
          setCurrentState("LISTENING");
        };

        recognition.onresult = (event: any) => {
          let currentText = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            currentText += event.results[i][0].transcript;
          }
          setInputTranscript(currentText);
        };

        recognition.onerror = (event: any) => {
          console.warn("Speech recognition error:", event.error);
          setIsListening(false);
          setCurrentState("IDLE");
        };

        recognition.onend = () => {
          setIsListening(false);
          if (currentState === "LISTENING") {
            setCurrentState("IDLE");
          }
        };

        recognitionRef.current = recognition;
      }
    }
  }, [currentState]);

  // Load Companies & Initial Voice Session
  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const comps = await api.getCompanies();
      setCompanies(comps);

      if (comps.length > 0) {
        const compId = comps[0].id;
        setSelectedCompanyId(compId);
        await refreshSessionsAndTelemetry(compId);
      }
    } catch (err: any) {
      setError(err?.detail || err?.message || "Failed to load voice interface data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Refresh Sessions & Telemetry
  const refreshSessionsAndTelemetry = async (compId: string) => {
    try {
      const [sessList, telem] = await Promise.all([
        api.listVoiceSessions(compId, 20),
        api.getVoiceTelemetry(compId).catch(() => null),
      ]);
      setSessions(sessList.items);
      setTelemetry(telem);

      if (sessList.items.length > 0) {
        // Load latest session detail
        const latest = await api.getVoiceSession(compId, sessList.items[0].id);
        setCurrentSession(latest);
        setCurrentState(latest.state);
      } else {
        // Automatically create a new session
        const newSess = await api.createVoiceSession(compId, {
          title: "Executive Voice Session",
        });
        setSessions([newSess]);
        setCurrentSession(newSess);
        setCurrentState(newSess.state);
      }
    } catch (err: any) {
      console.error("Error refreshing voice data:", err);
    }
  };

  const handleSelectCompany = async (compId: string) => {
    setSelectedCompanyId(compId);
    await refreshSessionsAndTelemetry(compId);
  };

  const handleCreateNewSession = async () => {
    if (!selectedCompanyId) return;
    try {
      setLoading(true);
      const newSess = await api.createVoiceSession(selectedCompanyId, {
        title: `Session ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`,
      });
      setSessions((prev) => [newSess, ...prev]);
      setCurrentSession(newSess);
      setCurrentState("IDLE");
    } catch (err: any) {
      setError(err?.detail || "Failed to create new voice session.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    if (!selectedCompanyId) return;
    try {
      const sess = await api.getVoiceSession(selectedCompanyId, sessionId);
      setCurrentSession(sess);
      setCurrentState(sess.state);
    } catch (err: any) {
      console.error("Failed to load session:", err);
    }
  };

  // Toggle Speech Recognition
  const toggleListening = () => {
    if (!speechRecognitionSupported) {
      alert("Speech recognition is not natively supported in this browser. You can type commands directly.");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      setCurrentState("IDLE");
    } else {
      setInputTranscript("");
      try {
        recognitionRef.current?.start();
      } catch (err) {
        console.warn("Recognition already active", err);
      }
    }
  };

  // Text-To-Speech Synthesis
  const speakText = (text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setCurrentState("SPEAKING");
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setCurrentState("IDLE");
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setCurrentState("IDLE");
    };

    window.speechSynthesis.speak(utterance);
  };

  // Submit Spoken or Typed Command
  const handleSubmitCommand = async (customTranscript?: string) => {
    const textToSend = (customTranscript || inputTranscript).trim();
    if (!textToSend || !selectedCompanyId) return;

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }

    setIsProcessing(true);
    setCurrentState("PROCESSING");
    setInputTranscript("");

    try {
      const response: VoiceCommandResponse = await api.sendVoiceCommand(selectedCompanyId, {
        transcript: textToSend,
        session_id: currentSession?.id,
      });

      // Construct optimistic interaction item
      const newInteraction: VoiceInteractionItem = {
        id: `vci-${Date.now()}`,
        session_id: response.session_id,
        company_id: selectedCompanyId,
        user_id: "",
        transcript: response.transcript,
        intent: response.intent,
        action_taken: response.action_taken,
        action_entity_id: response.action_entity_id,
        action_success: response.action_success,
        spoken_response: response.spoken_response,
        detailed_response: response.detailed_response,
        execution_time_ms: response.execution_time_ms,
        created_at: response.timestamp,
      };

      setCurrentSession((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          state: response.state,
          interactions: [...prev.interactions, newInteraction],
        };
      });

      setCurrentState(response.state);

      // Trigger text-to-speech if enabled
      if (autoSpeak && response.spoken_response) {
        speakText(response.spoken_response);
      } else {
        setTimeout(() => setCurrentState("IDLE"), 1200);
      }

      // Refresh telemetry in background
      api.getVoiceTelemetry(selectedCompanyId).then(setTelemetry).catch(() => null);
    } catch (err: any) {
      setError(err?.detail || err?.message || "Failed to process voice command.");
      setCurrentState("IDLE");
    } finally {
      setIsProcessing(false);
    }
  };

  const stateStyle = STATE_CONFIG[currentState] || STATE_CONFIG.IDLE;

  return (
    <ShellLayout pageTitle="Voice Interface" breadcrumb="Executive & Strategy">
      <div className="space-y-6">
        {/* Top Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1e2738]">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 via-purple-500/20 to-pink-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-lg shadow-indigo-500/10">
                <Mic className="w-5 h-5 text-indigo-300" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                  Voice Interface Console
                  <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    Phase 21
                  </span>
                </h1>
                <p className="text-xs text-slate-400">
                  Real-time bidirectional speech orchestration over core company execution systems (§ 25).
                </p>
              </div>
            </div>
          </div>

          {/* Controls & Company Selector */}
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedCompanyId}
              onChange={(e) => handleSelectCompany(e.target.value)}
              className="bg-[#111724] border border-[#1e2738] text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 font-mono transition"
            >
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <button
              onClick={handleCreateNewSession}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow-md shadow-indigo-600/20 disabled:opacity-50"
            >
              <Plus className="w-3.5 h-3.5" />
              New Session
            </button>

            <button
              onClick={() => selectedCompanyId && refreshSessionsAndTelemetry(selectedCompanyId)}
              disabled={loading}
              className="p-2 rounded-lg border border-[#1e2738] bg-[#111724] hover:bg-[#161f30] text-slate-400 hover:text-white transition"
              title="Refresh Voice State"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-white font-mono text-xs ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Telemetry Stats Bar */}
        {telemetry && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl border border-[#1e2738] bg-[#111724] flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[11px] text-slate-400">Total Sessions</p>
                <p className="text-base font-bold text-white font-mono">{telemetry.total_sessions}</p>
              </div>
            </div>

            <div className="p-3 rounded-xl border border-[#1e2738] bg-[#111724] flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <AudioWaveform className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[11px] text-slate-400">Interactions</p>
                <p className="text-base font-bold text-white font-mono">{telemetry.total_interactions}</p>
              </div>
            </div>

            <div className="p-3 rounded-xl border border-[#1e2738] bg-[#111724] flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[11px] text-slate-400">Avg Latency</p>
                <p className="text-base font-bold text-white font-mono">{telemetry.avg_execution_time_ms.toFixed(1)}ms</p>
              </div>
            </div>

            <div className="p-3 rounded-xl border border-[#1e2738] bg-[#111724] flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[11px] text-slate-400">Top Intent</p>
                <p className="text-xs font-bold text-white font-mono truncate">
                  {Object.keys(telemetry.intent_distribution)[0] || "READY"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Console Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Interactive Dialogue Feed & Live Voice Hub (8 cols) */}
          <div className="lg:col-span-8 space-y-4">
            {/* Live Voice State Indicator Card */}
            <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724] relative overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-mono font-semibold border flex items-center gap-2 ${stateStyle.bg} ${stateStyle.text} ${stateStyle.border}`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        currentState === "LISTENING"
                          ? "bg-emerald-400 animate-ping"
                          : currentState === "SPEAKING"
                          ? "bg-cyan-400 animate-pulse"
                          : currentState === "PROCESSING" || currentState === "PLANNING"
                          ? "bg-blue-400 animate-spin"
                          : "bg-slate-400"
                      }`}
                    />
                    STATE: {stateStyle.label}
                  </div>

                  <span className="text-xs text-slate-400 font-mono">
                    Session: {currentSession?.title || "Active"}
                  </span>
                </div>

                {/* Auto Speak Toggle */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setAutoSpeak(!autoSpeak)}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono border transition ${
                      autoSpeak
                        ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-400"
                        : "bg-slate-800/40 border-slate-700/50 text-slate-400"
                    }`}
                    title="Toggle automatic speech playback for responses"
                  >
                    {autoSpeak ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                    {autoSpeak ? "Auto Speak ON" : "Auto Speak OFF"}
                  </button>
                </div>
              </div>

              {/* Dynamic Soundwave Equalizer (Visible when Listening or Speaking) */}
              {(isListening || isSpeaking || isProcessing) && (
                <div className="mt-4 pt-4 border-t border-[#1e2738]/60 flex items-center justify-center gap-1.5 h-8">
                  {[40, 75, 100, 60, 90, 45, 80, 100, 70, 50, 85, 30].map((h, i) => (
                    <span
                      key={i}
                      className={`w-1 rounded-full transition-all duration-300 ${
                        isListening
                          ? "bg-emerald-400 animate-pulse"
                          : isSpeaking
                          ? "bg-cyan-400 animate-bounce"
                          : "bg-blue-400 animate-pulse"
                      }`}
                      style={{
                        height: `${h}%`,
                        animationDelay: `${i * 75}ms`,
                      }}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Conversation Stream */}
            <div className="rounded-xl border border-[#1e2738] bg-[#0d121c] p-4 min-h-[380px] max-h-[480px] overflow-y-auto space-y-4">
              {currentSession && currentSession.interactions.length === 0 && (
                <div className="h-64 flex flex-col items-center justify-center text-center p-6 space-y-3">
                  <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                    <AudioWaveform className="w-6 h-6 animate-pulse" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">Voice Interface Ready</h3>
                    <p className="text-xs text-slate-400 max-w-sm mt-1">
                      Speak directly into your microphone or choose a canonical prompt below to query company status, delegate tasks, or approve requests.
                    </p>
                  </div>
                </div>
              )}

              {currentSession?.interactions.map((item) => {
                const intentConfig = INTENT_BADGES[item.intent] || INTENT_BADGES.GENERAL_INQUIRY;

                return (
                  <div key={item.id} className="space-y-3">
                    {/* User Command Bubble */}
                    <div className="flex items-start justify-end gap-2.5">
                      <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-indigo-600/20 border border-indigo-500/30 p-3 text-white shadow-sm">
                        <div className="flex items-center justify-between gap-3 mb-1">
                          <span
                            className={`text-[10px] font-mono px-2 py-0.5 rounded border ${intentConfig.color}`}
                          >
                            {intentConfig.label}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {new Date(item.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-slate-100 flex items-center gap-2">
                          <Mic className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                          &ldquo;{item.transcript}&rdquo;
                        </p>
                      </div>
                    </div>

                    {/* CEO / System Spoken & Detailed Response Bubble */}
                    <div className="flex items-start gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 mt-1">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <div className="max-w-[88%] rounded-2xl rounded-tl-sm bg-[#111724] border border-[#1e2738] p-4 text-slate-200 shadow-sm space-y-3">
                        {/* Spoken Response Header */}
                        <div className="flex items-center justify-between gap-2 border-b border-[#1e2738]/60 pb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-cyan-400">CEO Response</span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              {item.execution_time_ms.toFixed(1)}ms
                            </span>
                          </div>

                          <button
                            onClick={() => speakText(item.spoken_response)}
                            className="p-1 rounded text-slate-400 hover:text-cyan-300 transition"
                            title="Replay Spoken Audio"
                          >
                            <Volume2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        {/* Spoken Audio Transcript */}
                        <p className="text-sm text-slate-100 italic bg-cyan-950/20 border border-cyan-800/20 p-2.5 rounded-lg">
                          &ldquo;{item.spoken_response}&rdquo;
                        </p>

                        {/* Detailed Markdown Breakdown */}
                        {item.detailed_response && (
                          <div className="text-xs text-slate-300 leading-relaxed space-y-1 font-mono bg-[#090d14] p-3 rounded-lg border border-[#1e2738]/60 whitespace-pre-wrap">
                            {item.detailed_response}
                          </div>
                        )}

                        {/* Action Taken Metadata Tag */}
                        {item.action_taken && (
                          <div className="flex items-center gap-2 pt-1">
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              Action: {item.action_taken}
                            </span>
                            {item.action_entity_id && (
                              <span className="text-[10px] font-mono text-slate-400">
                                Entity: <code className="text-slate-300">{item.action_entity_id}</code>
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {isProcessing && (
                <div className="flex items-center gap-3 p-3 rounded-xl bg-[#111724] border border-[#1e2738] text-slate-300 text-xs">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                  <span>CEO routing voice intent to underlying company systems...</span>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Canonical Prompt Chips */}
            <div className="space-y-1.5">
              <p className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-400" /> Canonical Section 25 Prompts:
              </p>
              <div className="flex flex-wrap gap-2">
                {CANONICAL_PROMPTS.map((prompt) => (
                  <button
                    key={prompt.label}
                    onClick={() => handleSubmitCommand(prompt.query)}
                    disabled={isProcessing}
                    className="text-xs px-2.5 py-1.5 rounded-lg bg-[#111724] border border-[#1e2738] hover:border-indigo-500/50 hover:bg-[#161f30] text-slate-300 hover:text-white transition flex items-center gap-1.5 font-mono disabled:opacity-50"
                  >
                    <span>{prompt.query}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Input Bar & Microphone Control */}
            <div className="p-3 rounded-xl border border-[#1e2738] bg-[#111724] flex items-center gap-2">
              <button
                onClick={toggleListening}
                disabled={isProcessing}
                className={`p-3 rounded-xl transition shadow-lg shrink-0 flex items-center justify-center ${
                  isListening
                    ? "bg-rose-600 text-white animate-pulse shadow-rose-600/30"
                    : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30"
                }`}
                title={isListening ? "Stop listening" : "Click to speak"}
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <input
                type="text"
                value={inputTranscript}
                onChange={(e) => setInputTranscript(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmitCommand();
                  }
                }}
                placeholder={
                  isListening
                    ? "Listening... Speak your command now..."
                    : "Type a command or speak into your microphone..."
                }
                className="flex-1 bg-[#0d121c] border border-[#1e2738] rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-sans transition"
              />

              <button
                onClick={() => handleSubmitCommand()}
                disabled={!inputTranscript.trim() || isProcessing}
                className="p-3 rounded-xl bg-[#1a2333] hover:bg-indigo-600 text-slate-300 hover:text-white transition disabled:opacity-40 disabled:hover:bg-[#1a2333]"
                title="Send Command"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Right Column: Sessions Drawer & Architectural Overview (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Architectural Foundation Card per docs/Phases.md § 25 */}
            <div className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/10 space-y-3">
              <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                Section 25 Voice Principle
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                &ldquo;Voice is a control interface over the same underlying company system. It should not create a separate execution architecture.&rdquo;
              </p>
              <div className="text-[11px] font-mono text-slate-400 space-y-1 border-t border-indigo-500/20 pt-2">
                <div className="flex items-center justify-between">
                  <span>Microphone:</span>
                  <span className="text-emerald-400">Web Speech API</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Intent Router:</span>
                  <span className="text-indigo-400">CEO Core Engine</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>State Tracking:</span>
                  <span className="text-cyan-400">6 Canonical States</span>
                </div>
              </div>
            </div>

            {/* Session History Drawer */}
            <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724] space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <History className="w-3.5 h-3.5 text-slate-400" />
                  Voice Sessions
                </h3>
                <span className="text-[10px] font-mono text-slate-400">
                  {sessions.length} total
                </span>
              </div>

              <div className="space-y-2 max-h-[320px] overflow-y-auto">
                {sessions.map((sess) => {
                  const isCurrent = currentSession?.id === sess.id;
                  const sessState = STATE_CONFIG[sess.state] || STATE_CONFIG.IDLE;

                  return (
                    <button
                      key={sess.id}
                      onClick={() => handleSelectSession(sess.id)}
                      className={`w-full text-left p-3 rounded-lg border transition text-xs flex items-center justify-between ${
                        isCurrent
                          ? "bg-indigo-600/15 border-indigo-500/40 text-white"
                          : "bg-[#0d121c] border-[#1e2738] hover:border-slate-700 text-slate-300 hover:text-white"
                      }`}
                    >
                      <div className="space-y-1 min-w-0 pr-2">
                        <p className="font-semibold truncate">{sess.title}</p>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(sess.created_at).toLocaleDateString([], {
                              month: "short",
                              day: "numeric",
                            })}
                          </span>
                          <span>•</span>
                          <span>{sess.interactions?.length || 0} turns</span>
                        </div>
                      </div>

                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0 ${sessState.bg} ${sessState.text} ${sessState.border}`}
                      >
                        {sess.state}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Intent Analytics Card */}
            {telemetry && Object.keys(telemetry.intent_distribution).length > 0 && (
              <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724] space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Intent Distribution
                </h3>
                <div className="space-y-2">
                  {Object.entries(telemetry.intent_distribution).map(([intent, count]) => {
                    const pct = Math.round((count / telemetry.total_interactions) * 100);
                    return (
                      <div key={intent} className="space-y-1">
                        <div className="flex items-center justify-between text-[11px] font-mono">
                          <span className="text-slate-300">{intent}</span>
                          <span className="text-slate-400">{count} ({pct}%)</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-[#1e2738] overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ShellLayout>
  );
}
