"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  ArrowLeft,
  Sparkles,
  Bot,
  Activity,
  History,
  Layers,
  Send,
  Globe,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Radio,
  ChevronRight,
  Shield,
  Zap,
  Info,
  Clock,
  Sparkle,
  X,
  Sliders,
} from "lucide-react";
import {
  apiClient,
  type Company,
  type VoiceCommandResponse,
  type VoiceInteractionItem,
  type VoiceIntent,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Supported Languages & Presets
// ---------------------------------------------------------------------------
interface SupportedLanguage {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
  samplePrompt: string;
}

const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  {
    code: "en-US",
    name: "English (US)",
    nativeName: "English",
    flag: "🇺🇸",
    samplePrompt: "CEO, give me an executive briefing on company status.",
  },
  {
    code: "bn-BD",
    name: "Bengali",
    nativeName: "বাংলা",
    flag: "🇧🇩",
    samplePrompt: "সিইও, আমাদের কোম্পানির সার্বিক কাজের অবস্থা কী?",
  },
  {
    code: "es-ES",
    name: "Spanish",
    nativeName: "Español",
    flag: "🇪🇸",
    samplePrompt: "¿Cuál es el estado actual de los proyectos y tareas?",
  },
  {
    code: "fr-FR",
    name: "French",
    nativeName: "Français",
    flag: "🇫🇷",
    samplePrompt: "Donnez-moi un point exécutif sur la santé de l'entreprise.",
  },
  {
    code: "de-DE",
    name: "German",
    nativeName: "Deutsch",
    flag: "🇩🇪",
    samplePrompt: "Wie ist der aktuelle Status unserer Unternehmensprojekte?",
  },
  {
    code: "ar-SA",
    name: "Arabic",
    nativeName: "العربية",
    flag: "🇸🇦",
    samplePrompt: "أعطني ملخصاً تنفيذياً عن حالة المشاريع والمهام.",
  },
  {
    code: "hi-IN",
    name: "Hindi",
    nativeName: "हिन्दी",
    flag: "🇮🇳",
    samplePrompt: "कंपनी के मौजूदा कार्यों और स्थिति का संक्षिप्त विवरण दें।",
  },
  {
    code: "zh-CN",
    name: "Mandarin Chinese",
    nativeName: "中文 (普通话)",
    flag: "🇨🇳",
    samplePrompt: "请汇报目前公司活跃项目及执行中任务的整体情况。",
  },
  {
    code: "ja-JP",
    name: "Japanese",
    nativeName: "日本語",
    flag: "🇯🇵",
    samplePrompt: "現在の会社ステータスと進行中タスクの状況を教えてください。",
  },
  {
    code: "pt-BR",
    name: "Portuguese",
    nativeName: "Português",
    flag: "🇧🇷",
    samplePrompt: "Qual é o status atual dos projetos e aprovações?",
  },
  {
    code: "it-IT",
    name: "Italian",
    nativeName: "Italiano",
    flag: "🇮🇹",
    samplePrompt: "Qual è lo stato esecutivo dei nostri progetti aziendali?",
  },
  {
    code: "ru-RU",
    name: "Russian",
    nativeName: "Русский",
    flag: "🇷🇺",
    samplePrompt: "Предоставьте исполнительный отчет о состоянии компании.",
  },
  {
    code: "ko-KR",
    name: "Korean",
    nativeName: "한국어",
    flag: "🇰🇷",
    samplePrompt: "현재 회사 프로젝트와 주요 업무 진행 현황을 보고해주세요.",
  },
  {
    code: "tr-TR",
    name: "Turkish",
    nativeName: "Türkçe",
    flag: "🇹🇷",
    samplePrompt: "Şirketin genel durumu ve aktif görevler hakkında brifing verin.",
  },
  {
    code: "nl-NL",
    name: "Dutch",
    nativeName: "Nederlands",
    flag: "🇳🇱",
    samplePrompt: "Wat is de huidige stand van zaken van de bedrijfsprojecten?",
  },
  {
    code: "sv-SE",
    name: "Swedish",
    nativeName: "Svenska",
    flag: "🇸🇪",
    samplePrompt: "Ge mig en verkställande sammanfattning av bolagets status.",
  },
  {
    code: "pl-PL",
    name: "Polish",
    nativeName: "Polski",
    flag: "🇵🇱",
    samplePrompt: "Jaki jest aktualny stan projektów i zadań w firmie?",
  },
  {
    code: "vi-VN",
    name: "Vietnamese",
    nativeName: "Tiếng Việt",
    flag: "🇻🇳",
    samplePrompt: "Báo cáo tình hình hoạt động và tiến độ các dự án hiện tại.",
  },
  {
    code: "id-ID",
    name: "Indonesian",
    nativeName: "Bahasa Indonesia",
    flag: "🇮🇩",
    samplePrompt: "Berikan ringkasan eksekutif tentang status proyek perusahaan.",
  },
];

type VoiceCoreState = "IDLE" | "LISTENING" | "THINKING" | "SPEAKING";

export default function CeoExecutiveVoiceRoomPage() {
  // Navigation & Company context
  const [company, setCompany] = useState<Company | null>(null);
  const [companyId, setCompanyId] = useState<string>("");
  const [ceoName, setCeoName] = useState<string>("Autonomous CEO");
  const [ceoRole, setCeoRole] = useState<string>("Executive Agent");

  // Room core states
  const [coreState, setCoreState] = useState<VoiceCoreState>("IDLE");
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(false);
  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState<boolean>(false);
  const [selectedLanguage, setSelectedLanguage] = useState<SupportedLanguage>(
    SUPPORTED_LANGUAGES[0]
  );

  // Drawers
  const [showHistoryDrawer, setShowHistoryDrawer] = useState<boolean>(false);
  const [showMetricsDrawer, setShowMetricsDrawer] = useState<boolean>(false);

  // Transcripts & Teleprompter
  const [interimTranscript, setInterimTranscript] = useState<string>("");
  const [activeUserPrompt, setActiveUserPrompt] = useState<string>("");
  const [activeCeoSpoken, setActiveCeoSpoken] = useState<string>(
    "Welcome to the Executive Suite. I am your autonomous CEO. Speak to me in any language, or select from strategic inquiries below."
  );
  const [activeCeoDetailed, setActiveCeoDetailed] = useState<string>("");
  const [activeIntent, setActiveIntent] = useState<VoiceIntent | "">("");
  const [executionTimeMs, setExecutionTimeMs] = useState<number | null>(null);

  // History & Session
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [interactionHistory, setInteractionHistory] = useState<VoiceInteractionItem[]>([]);
  const [companyStats, setCompanyStats] = useState<{
    projects: number;
    tasks: number;
    approvals: number;
  }>({ projects: 0, tasks: 0, approvals: 0 });

  // Text input fallback
  const [textInput, setTextInput] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Audio frequency animation state
  const [audioFreqLevel, setAudioFreqLevel] = useState<number>(0);

  // References
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const particleCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneStreamRef = useRef<MediaStream | null>(null);
  const animationFrameIdRef = useRef<number | null>(null);
  const isSpeechSupportedRef = useRef<boolean>(true);
  const isSynthesizingRef = useRef<boolean>(false);

  // ---------------------------------------------------------------------------
  // Initialize Company & CEO Context
  // ---------------------------------------------------------------------------
  useEffect(() => {
    async function loadCompanyContext() {
      try {
        const companies = await apiClient.getCompanies();
        if (companies && companies.length > 0) {
          const active = companies[0];
          setCompany(active);
          setCompanyId(active.id);

          // Fetch CEO info & company briefing
          try {
            const ceoContext = await apiClient.getCeoContext(active.id);
            if (ceoContext?.ceo_agent?.name) {
              setCeoName(ceoContext.ceo_agent.name);
            }
            if (ceoContext?.ceo_agent?.role) {
              setCeoRole(ceoContext.ceo_agent.role);
            }
          } catch (e) {
            // fallback gracefully
          }

          // Fetch active stats
          try {
            const [projs, tasks, approvals] = await Promise.allSettled([
              apiClient.getProjects(active.id),
              apiClient.getTasks(active.id),
              apiClient.getApprovals(active.id),
            ]);
            setCompanyStats({
              projects:
                projs.status === "fulfilled"
                  ? projs.value.total ?? projs.value.items?.length ?? 0
                  : 0,
              tasks:
                tasks.status === "fulfilled"
                  ? tasks.value.total ?? tasks.value.items?.length ?? 0
                  : 0,
              approvals:
                approvals.status === "fulfilled"
                  ? approvals.value.total ?? approvals.value.items?.length ?? 0
                  : 0,
            });
          } catch (e) {
            // fallback
          }

          // Create initial voice session
          try {
            const session = await apiClient.createVoiceSession(active.id, {
              title: "Executive CEO Suite Session",
            });
            if (session?.id) {
              setSessionId(session.id);
            }
          } catch (e) {
            // non-fatal
          }
        }
      } catch (err) {
        console.error("Error loading company context:", err);
      }
    }

    loadCompanyContext();
  }, []);

  // ---------------------------------------------------------------------------
  // Background Starfield & Neural Particle Canvas
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const canvas = particleCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    // Particle nodes
    const particleCount = 75;
    const particles = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: Math.random() * 1.8 + 0.6,
      alpha: Math.random() * 0.5 + 0.2,
    }));

    function renderParticles() {
      if (!ctx) return;
      ctx.clearRect(0, 0, width, height);

      // Draw faint connections
      for (let i = 0; i < particleCount; i++) {
        const p1 = particles[i];
        p1.x += p1.vx;
        p1.y += p1.vy;
        if (p1.x < 0) p1.x = width;
        if (p1.x > width) p1.x = 0;
        if (p1.y < 0) p1.y = height;
        if (p1.y > height) p1.y = 0;

        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(147, 197, 253, ${p1.alpha})`;
        ctx.fill();

        for (let j = i + 1; j < particleCount; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            const lineAlpha = (1 - dist / 110) * 0.12;
            ctx.strokeStyle = `rgba(59, 130, 246, ${lineAlpha})`;
            ctx.lineWidth = 0.7;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(renderParticles);
    }

    renderParticles();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animId);
    };
  }, []);

  // ---------------------------------------------------------------------------
  // 3D Gyroscopic Holographic Neural Core Canvas
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let angleX = 0;
    let angleY = 0;
    let angleZ = 0;

    const baseRadius = 140;

    function renderCore() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Color palette based on Core State
      let primaryColor = "rgba(6, 182, 212, "; // Cyan (IDLE)
      let secondaryColor = "rgba(139, 92, 246, "; // Violet
      let speedMult = 0.012;

      if (coreState === "LISTENING") {
        primaryColor = "rgba(16, 185, 129, "; // Emerald
        secondaryColor = "rgba(6, 182, 212, "; // Cyan
        speedMult = 0.024;
      } else if (coreState === "THINKING") {
        primaryColor = "rgba(245, 158, 11, "; // Amber
        secondaryColor = "rgba(168, 85, 247, "; // Purple
        speedMult = 0.045;
      } else if (coreState === "SPEAKING") {
        primaryColor = "rgba(236, 72, 153, "; // Pink
        secondaryColor = "rgba(99, 102, 241, "; // Indigo
        speedMult = 0.018;
      }

      angleX += speedMult;
      angleY += speedMult * 0.8;
      angleZ += speedMult * 0.5;

      // Dynamic reactive radius multiplier
      const pulse =
        coreState === "LISTENING" || coreState === "SPEAKING"
          ? 1 + (audioFreqLevel / 255) * 0.35 + Math.sin(angleX * 4) * 0.04
          : 1 + Math.sin(angleX * 2) * 0.05;

      const currentRadius = baseRadius * pulse;

      // 1. Central Ambient Glow
      const radGlow = ctx.createRadialGradient(
        centerX,
        centerY,
        10,
        centerX,
        centerY,
        currentRadius * 1.6
      );
      radGlow.addColorStop(0, primaryColor + "0.35)");
      radGlow.addColorStop(0.4, secondaryColor + "0.15)");
      radGlow.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = radGlow;
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentRadius * 1.6, 0, Math.PI * 2);
      ctx.fill();

      // 2. Concentric Gyroscopic Rings (3D perspective)
      const ringConfigs = [
        { rotX: angleX, rotY: angleY, rotZ: 0, rMult: 1.0, width: 2.2, color: primaryColor },
        { rotX: -angleX * 0.7, rotY: angleZ, rotZ: angleY, rMult: 0.85, width: 1.8, color: secondaryColor },
        { rotX: angleY, rotY: -angleZ * 0.9, rotZ: angleX * 0.6, rMult: 0.7, width: 1.5, color: primaryColor },
        { rotX: angleZ, rotY: angleX * 1.1, rotZ: -angleY * 0.8, rMult: 0.55, width: 1.2, color: secondaryColor },
      ];

      ringConfigs.forEach((ring) => {
        const segments = 64;
        ctx.beginPath();
        for (let i = 0; i <= segments; i++) {
          const theta = (i / segments) * Math.PI * 2;
          const r = currentRadius * ring.rMult;

          // 3D coordinates on circle plane
          let x = r * Math.cos(theta);
          let y = r * Math.sin(theta);
          let z = 0;

          // Rotation around X
          let y1 = y * Math.cos(ring.rotX) - z * Math.sin(ring.rotX);
          let z1 = y * Math.sin(ring.rotX) + z * Math.cos(ring.rotX);

          // Rotation around Y
          let x2 = x * Math.cos(ring.rotY) + z1 * Math.sin(ring.rotY);
          let z2 = -x * Math.sin(ring.rotY) + z1 * Math.cos(ring.rotY);

          // Rotation around Z
          let x3 = x2 * Math.cos(ring.rotZ) - y1 * Math.sin(ring.rotZ);
          let y3 = x2 * Math.sin(ring.rotZ) + y1 * Math.cos(ring.rotZ);

          // Project to 2D
          const fov = 400;
          const scale = fov / (fov + z2 + 200);
          const px = centerX + x3 * scale;
          const py = centerY + y3 * scale;

          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.strokeStyle = ring.color + "0.75)";
        ctx.lineWidth = ring.width;
        ctx.stroke();

        // Node beacons on the ring
        const nodeCount = 4;
        for (let k = 0; k < nodeCount; k++) {
          const nodeTheta = ring.rotZ * 2 + (k * Math.PI * 2) / nodeCount;
          const r = currentRadius * ring.rMult;
          let x = r * Math.cos(nodeTheta);
          let y = r * Math.sin(nodeTheta);
          let z = 0;

          let y1 = y * Math.cos(ring.rotX) - z * Math.sin(ring.rotX);
          let z1 = y * Math.sin(ring.rotX) + z * Math.cos(ring.rotX);
          let x2 = x * Math.cos(ring.rotY) + z1 * Math.sin(ring.rotY);
          let z2 = -x * Math.sin(ring.rotY) + z1 * Math.cos(ring.rotY);
          let x3 = x2 * Math.cos(ring.rotZ) - y1 * Math.sin(ring.rotZ);
          let y3 = x2 * Math.sin(ring.rotZ) + y1 * Math.cos(ring.rotZ);

          const scale = 400 / (400 + z2 + 200);
          const px = centerX + x3 * scale;
          const py = centerY + y3 * scale;

          ctx.beginPath();
          ctx.arc(px, py, 3.5 * scale, 0, Math.PI * 2);
          ctx.fillStyle = ring.color + "0.95)";
          ctx.shadowColor = ring.color + "1)";
          ctx.shadowBlur = 8;
          ctx.fill();
          ctx.shadowBlur = 0; // reset
        }
      });

      // 3. Central Core Nucleus
      const nucleusRadius = currentRadius * 0.28;
      const nuclGlow = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        centerX,
        centerY,
        nucleusRadius
      );
      nuclGlow.addColorStop(0, "rgba(255, 255, 255, 0.95)");
      nuclGlow.addColorStop(0.3, primaryColor + "0.8)");
      nuclGlow.addColorStop(0.7, secondaryColor + "0.4)");
      nuclGlow.addColorStop(1, "rgba(0, 0, 0, 0)");

      ctx.beginPath();
      ctx.arc(centerX, centerY, nucleusRadius, 0, Math.PI * 2);
      ctx.fillStyle = nuclGlow;
      ctx.fill();

      // Outer ripple ring on speaking/listening
      if (coreState === "LISTENING" || coreState === "SPEAKING") {
        const rippleR = currentRadius * (1.1 + Math.sin(angleX * 8) * 0.08);
        ctx.beginPath();
        ctx.arc(centerX, centerY, rippleR, 0, Math.PI * 2);
        ctx.strokeStyle = primaryColor + "0.4)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 6]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      animId = requestAnimationFrame(renderCore);
    }

    renderCore();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [coreState, audioFreqLevel]);

  // ---------------------------------------------------------------------------
  // Web Audio API Frequency Analyser for Live Mic Visualization
  // ---------------------------------------------------------------------------
  const startAudioVisualizer = useCallback(async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) return;
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      microphoneStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateFreq = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        // Calculate average volume level
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setAudioFreqLevel(avg);
        animationFrameIdRef.current = requestAnimationFrame(updateFreq);
      };

      updateFreq();
    } catch (e) {
      console.warn("AudioContext / mic stream could not be initialized:", e);
    }
  }, []);

  const stopAudioVisualizer = useCallback(() => {
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
    }
    if (microphoneStreamRef.current) {
      microphoneStreamRef.current.getTracks().forEach((track) => track.stop());
      microphoneStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAudioFreqLevel(0);
  }, []);

  // ---------------------------------------------------------------------------
  // Web Speech API: Text-to-Speech (Multilingual CEO Voice)
  // ---------------------------------------------------------------------------
  const speakText = useCallback(
    (text: string, langCode: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      if (isAudioMuted || !text) return;

      window.speechSynthesis.cancel(); // Cancel any existing speech

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = langCode;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      // Select voice matching language if available
      const voices = window.speechSynthesis.getVoices();
      const codePrefix = langCode.split("-")[0].toLowerCase();
      const matchedVoice =
        voices.find((v) => v.lang.toLowerCase() === langCode.toLowerCase()) ||
        voices.find((v) => v.lang.toLowerCase().startsWith(codePrefix));

      if (matchedVoice) {
        utterance.voice = matchedVoice;
      }

      utterance.onstart = () => {
        isSynthesizingRef.current = true;
        setCoreState("SPEAKING");
      };

      utterance.onend = () => {
        isSynthesizingRef.current = false;
        setCoreState("IDLE");
      };

      utterance.onerror = () => {
        isSynthesizingRef.current = false;
        setCoreState("IDLE");
      };

      window.speechSynthesis.speak(utterance);
    },
    [isAudioMuted]
  );

  // ---------------------------------------------------------------------------
  // Voice Command Processing & Execution
  // ---------------------------------------------------------------------------
  const handleExecuteVoiceCommand = useCallback(
    async (transcriptText: string) => {
      const trimmed = transcriptText.trim();
      if (!trimmed || isProcessing || !companyId) return;

      setIsProcessing(true);
      setCoreState("THINKING");
      setActiveUserPrompt(trimmed);
      setInterimTranscript("");

      try {
        const response: VoiceCommandResponse = await apiClient.sendVoiceCommand(
          companyId,
          {
            transcript: trimmed,
            session_id: sessionId,
            language: selectedLanguage.code,
          }
        );

        setActiveCeoSpoken(response.spoken_response);
        setActiveCeoDetailed(response.detailed_response);
        setActiveIntent(response.intent);
        setExecutionTimeMs(response.execution_time_ms);

        // Update history drawer item
        const historyItem: VoiceInteractionItem = {
          id: `vci-${Date.now()}`,
          session_id: response.session_id,
          company_id: companyId,
          user_id: "",
          transcript: trimmed,
          intent: response.intent,
          action_taken: response.action_taken || null,
          action_entity_id: response.action_entity_id || null,
          action_success: response.action_success,
          spoken_response: response.spoken_response,
          detailed_response: response.detailed_response,
          execution_time_ms: response.execution_time_ms,
          created_at: response.timestamp,
        };
        setInteractionHistory((prev) => [historyItem, ...prev]);

        // Speak response in target language
        speakText(response.spoken_response, selectedLanguage.code);
      } catch (err: any) {
        console.error("Voice command execution error:", err);
        const errorMsg =
          "I encountered an error processing your executive command. Please verify your connection or restate your request.";
        setActiveCeoSpoken(errorMsg);
        setActiveCeoDetailed(err?.message || "Internal command dispatch error.");
        setCoreState("IDLE");
        speakText(errorMsg, "en-US");
      } finally {
        setIsProcessing(false);
      }
    },
    [companyId, sessionId, selectedLanguage, isProcessing, speakText]
  );

  // ---------------------------------------------------------------------------
  // Web Speech API: Speech-to-Text Recognition
  // ---------------------------------------------------------------------------
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }
    stopAudioVisualizer();
    if (coreState === "LISTENING") {
      setCoreState("IDLE");
    }
  }, [stopAudioVisualizer, coreState]);

  const startListening = useCallback(async () => {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      isSpeechSupportedRef.current = false;
      alert(
        "Web Speech Recognition API is not supported in this browser. You can still use the modern keyboard input dock."
      );
      return;
    }

    // Cancel speech output before listening
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = selectedLanguage.code;
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setCoreState("LISTENING");
        setInterimTranscript("");
        startAudioVisualizer();
      };

      recognition.onresult = (event: any) => {
        let currentInterim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          if (item.isFinal) {
            const finalTranscript = item[0].transcript;
            stopListening();
            handleExecuteVoiceCommand(finalTranscript);
            return;
          } else {
            currentInterim += item[0].transcript;
          }
        }
        setInterimTranscript(currentInterim);
      };

      recognition.onerror = (event: any) => {
        console.warn("Speech recognition error:", event.error);
        stopListening();
      };

      recognition.onend = () => {
        stopAudioVisualizer();
        if (coreState === "LISTENING") {
          setCoreState("IDLE");
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      console.error("Failed to start speech recognition:", e);
      stopListening();
    }
  }, [selectedLanguage, startAudioVisualizer, stopAudioVisualizer, stopListening, handleExecuteVoiceCommand, coreState]);

  const toggleListening = useCallback(() => {
    if (coreState === "LISTENING") {
      stopListening();
    } else {
      startListening();
    }
  }, [coreState, stopListening, startListening]);

  // ---------------------------------------------------------------------------
  // Fullscreen Handler
  // ---------------------------------------------------------------------------
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(() => {});
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      }).catch(() => {});
    }
  };

  // ---------------------------------------------------------------------------
  // Keyboard Shortcuts: Spacebar (Push-to-Talk) & F (Fullscreen) & Esc
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Avoid hotkeys when typing in text input
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        toggleListening();
      } else if (e.key === "f" || e.key === "F") {
        toggleFullscreen();
      } else if (e.key === "Escape") {
        if (isLanguageModalOpen) setIsLanguageModalOpen(false);
        else if (showHistoryDrawer) setShowHistoryDrawer(false);
        else if (showMetricsDrawer) setShowMetricsDrawer(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [coreState, isLanguageModalOpen, showHistoryDrawer, showMetricsDrawer, toggleListening]);

  // ---------------------------------------------------------------------------
  // UI Render
  // ---------------------------------------------------------------------------
  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#030712] text-slate-100 select-none font-sans">
      {/* 1. Deep Space Starfield & Interconnected Neural Mesh */}
      <canvas
        ref={particleCanvasRef}
        className="absolute inset-0 pointer-events-none z-0 opacity-80"
      />

      {/* 2. Radial Atmospheric Glow Backdrops */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-tr from-cyan-600/10 via-indigo-600/15 to-purple-600/10 rounded-full blur-[140px] pointer-events-none z-0" />

      {/* 3. Top Executive HUD Bar */}
      <header className="absolute top-0 left-0 right-0 h-16 px-6 flex items-center justify-between z-30 border-b border-cyan-500/10 backdrop-blur-md bg-slate-950/40">
        {/* Left: Exit Room & Executive Identity */}
        <div className="flex items-center space-x-4">
          <Link
            href="/ceo"
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-slate-700/60 bg-slate-900/50 hover:bg-slate-800/80 hover:border-cyan-500/40 text-slate-300 hover:text-white transition-all text-xs font-medium group"
            title="Return to CEO Management Dashboard (Esc)"
          >
            <ArrowLeft className="w-4 h-4 text-cyan-400 group-hover:-translate-x-0.5 transition-transform" />
            <span>Exit Suite</span>
          </Link>

          <div className="h-4 w-px bg-slate-800" />

          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/30 border border-cyan-500/40 flex items-center justify-center">
                <Bot className="w-4 h-4 text-cyan-400" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-slate-950 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-sm font-semibold tracking-wide text-white">
                  {ceoName}
                </h1>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-cyan-950/70 border border-cyan-500/40 text-cyan-300">
                  {ceoRole}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                {company?.name || "Company OS"} &bull; Real-Time Voice Synthesis
              </p>
            </div>
          </div>
        </div>

        {/* Center: Live Connection State Pill */}
        <div className="hidden md:flex items-center space-x-3 px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800 backdrop-blur-md text-xs">
          <div className="flex items-center space-x-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                coreState === "LISTENING"
                  ? "bg-emerald-400 animate-ping"
                  : coreState === "THINKING"
                  ? "bg-amber-400 animate-spin"
                  : coreState === "SPEAKING"
                  ? "bg-pink-400 animate-pulse"
                  : "bg-cyan-400"
              }`}
            />
            <span className="font-semibold text-slate-300 tracking-wide text-[11px]">
              {coreState === "LISTENING"
                ? "LISTENING (MIC ACTIVE)"
                : coreState === "THINKING"
                ? "EXECUTIVE REASONING..."
                : coreState === "SPEAKING"
                ? "VOCALIZING RESPONSE"
                : "AWAITING INQUIRY"}
            </span>
          </div>
          {executionTimeMs !== null && (
            <>
              <div className="h-3 w-px bg-slate-800" />
              <span className="text-[10px] text-slate-400">
                {executionTimeMs.toFixed(0)}ms latency
              </span>
            </>
          )}
        </div>

        {/* Right: Controls (Language, Mute, Metrics, History, Fullscreen) */}
        <div className="flex items-center space-x-2">
          {/* Language Selector Button */}
          <button
            onClick={() => setIsLanguageModalOpen(true)}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/20 hover:bg-cyan-900/30 text-cyan-300 transition-all text-xs font-medium"
            title="Change Meeting Language"
          >
            <span className="text-sm">{selectedLanguage.flag}</span>
            <span className="font-semibold">{selectedLanguage.name}</span>
            <Globe className="w-3.5 h-3.5 opacity-70" />
          </button>

          {/* Audio Mute Toggle */}
          <button
            onClick={() => {
              setIsAudioMuted(!isAudioMuted);
              if (!isAudioMuted && window.speechSynthesis) {
                window.speechSynthesis.cancel();
              }
            }}
            className={`p-2 rounded-lg border text-xs transition-all ${
              isAudioMuted
                ? "border-amber-500/40 bg-amber-950/30 text-amber-300"
                : "border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300"
            }`}
            title={isAudioMuted ? "Unmute CEO Vocalizer" : "Mute CEO Vocalizer"}
          >
            {isAudioMuted ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4 text-cyan-400" />
            )}
          </button>

          {/* Company Live Metrics Drawer Toggle */}
          <button
            onClick={() => setShowMetricsDrawer(!showMetricsDrawer)}
            className={`p-2 rounded-lg border text-xs transition-all ${
              showMetricsDrawer
                ? "border-cyan-500/50 bg-cyan-950/40 text-cyan-300"
                : "border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300"
            }`}
            title="Company Intelligence HUD"
          >
            <Layers className="w-4 h-4" />
          </button>

          {/* Transcript History Drawer Toggle */}
          <button
            onClick={() => setShowHistoryDrawer(!showHistoryDrawer)}
            className={`p-2 rounded-lg border text-xs transition-all relative ${
              showHistoryDrawer
                ? "border-cyan-500/50 bg-cyan-950/40 text-cyan-300"
                : "border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300"
            }`}
            title="Executive Meeting Transcript & Audit"
          >
            <History className="w-4 h-4" />
            {interactionHistory.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-cyan-500 text-black text-[9px] font-bold flex items-center justify-center">
                {interactionHistory.length}
              </span>
            )}
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg border border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300 text-xs transition-all"
            title="Toggle True Fullscreen (F)"
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4 text-cyan-400" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </header>

      {/* 4. Centerpiece: Holographic 3D Gyroscopic Neural Core & Subtitle Teleprompter */}
      <main className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none pb-28 pt-16">
        {/* Holographic Gyroscopic 3D Canvas */}
        <div
          className="relative pointer-events-auto cursor-pointer flex items-center justify-center"
          onClick={toggleListening}
          title="Click Holographic Core to Start/Stop Speaking (or press Spacebar)"
        >
          <canvas
            ref={canvasRef}
            width={480}
            height={480}
            className="transition-transform duration-700 hover:scale-105 active:scale-95"
          />

          {/* Interactive Core Center Status Badge */}
          <div className="absolute pointer-events-none flex flex-col items-center justify-center text-center">
            <Radio
              className={`w-6 h-6 mb-1 ${
                coreState === "LISTENING"
                  ? "text-emerald-400 animate-ping"
                  : coreState === "THINKING"
                  ? "text-amber-400 animate-spin"
                  : coreState === "SPEAKING"
                  ? "text-pink-400 animate-bounce"
                  : "text-cyan-400 opacity-60"
              }`}
            />
            <span className="text-[11px] font-mono tracking-widest uppercase text-slate-300 font-bold bg-slate-950/60 px-2 py-0.5 rounded-full border border-slate-700/40">
              {coreState}
            </span>
          </div>
        </div>

        {/* Live Audio Frequency Spectrum Bar (Active during Speaking/Listening) */}
        <div className="flex items-center space-x-1.5 mt-2 pointer-events-none h-6">
          {Array.from({ length: 16 }).map((_, i) => {
            const h =
              coreState === "LISTENING" || coreState === "SPEAKING"
                ? Math.max(
                    4,
                    Math.min(
                      24,
                      Math.sin((i / 16) * Math.PI) * (audioFreqLevel / 8) +
                        Math.random() * 6
                    )
                  )
                : 3;
            return (
              <div
                key={i}
                style={{ height: `${h}px` }}
                className={`w-1 rounded-full transition-all duration-75 ${
                  coreState === "LISTENING"
                    ? "bg-emerald-400"
                    : coreState === "SPEAKING"
                    ? "bg-pink-400"
                    : "bg-slate-700/60"
                }`}
              />
            );
          })}
        </div>

        {/* Subtitle Teleprompter & Live Dialogue HUD */}
        <div className="w-full max-w-3xl px-6 mt-4 pointer-events-auto">
          <div className="relative rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/70 backdrop-blur-xl shadow-[0_0_60px_rgba(6,182,212,0.1)] transition-all">
            {/* Interim / Live User Speech Preview */}
            {(coreState === "LISTENING" || interimTranscript) && (
              <div className="mb-3 flex items-start space-x-3 pb-3 border-b border-slate-800/80">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping mt-1.5 shrink-0" />
                <div className="flex-1">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400">
                    Live Input ({selectedLanguage.name})
                  </span>
                  <p className="text-base text-slate-100 italic mt-0.5 leading-relaxed font-medium">
                    {interimTranscript || "Listening... Speak naturally in your language."}
                  </p>
                </div>
              </div>
            )}

            {/* Recent User Prompt if not actively speaking */}
            {!interimTranscript && activeUserPrompt && (
              <div className="mb-2 text-xs text-slate-400 flex items-center space-x-2">
                <span className="font-semibold text-cyan-400">You:</span>
                <span className="italic truncate">&ldquo;{activeUserPrompt}&rdquo;</span>
              </div>
            )}

            {/* CEO Spoken Response Teleprompter */}
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="w-7 h-7 rounded-lg bg-cyan-950/60 border border-cyan-500/40 flex items-center justify-center shrink-0 mt-0.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-cyan-300 tracking-wide uppercase">
                      {ceoName}
                    </span>
                    {activeIntent && (
                      <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-950/80 border border-indigo-500/40 text-indigo-300">
                        {activeIntent}
                      </span>
                    )}
                  </div>
                  <p className="text-slate-100 text-sm md:text-base font-normal mt-1 leading-relaxed">
                    {activeCeoSpoken}
                  </p>
                </div>
              </div>

              {/* Replay audio button */}
              <button
                onClick={() => speakText(activeCeoSpoken, selectedLanguage.code)}
                className="ml-3 p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition-colors shrink-0"
                title="Replay Spoken Response"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* 5. Bottom Executive Control Dock */}
      <footer className="absolute bottom-6 left-0 right-0 flex flex-col items-center justify-center z-30 pointer-events-none px-6">
        {/* Quick Strategic Inquiry Chips */}
        <div className="flex items-center space-x-2 mb-3 pointer-events-auto overflow-x-auto max-w-full pb-1 no-scrollbar">
          {[
            selectedLanguage.samplePrompt,
            "Any blocked tasks?",
            "Show enterprise opportunities",
            "Create task for marketing",
          ].map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleExecuteVoiceCommand(prompt)}
              disabled={isProcessing || coreState === "LISTENING"}
              className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-900/70 hover:bg-cyan-950/60 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-200 transition-all backdrop-blur-md shadow-sm whitespace-nowrap active:scale-95 disabled:opacity-50"
            >
              <span className="mr-1 text-cyan-400 font-bold">&bull;</span>
              {prompt}
            </button>
          ))}
        </div>

        {/* Central Floating Glass Dock */}
        <div className="pointer-events-auto flex items-center space-x-3 p-2 rounded-2xl border border-cyan-500/20 bg-slate-950/80 backdrop-blur-2xl shadow-[0_0_50px_rgba(6,182,212,0.15)] max-w-xl w-full">
          {/* Main Push-to-Talk Orb Button */}
          <button
            onClick={toggleListening}
            disabled={isProcessing}
            className={`relative flex items-center justify-center w-12 h-12 rounded-xl transition-all duration-300 shrink-0 ${
              coreState === "LISTENING"
                ? "bg-emerald-500 text-black shadow-[0_0_25px_rgba(16,185,129,0.7)] scale-105"
                : "bg-gradient-to-tr from-cyan-500 to-indigo-600 text-white shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] hover:scale-105 active:scale-95"
            }`}
            title="Press Spacebar or Click to Speak"
          >
            {coreState === "LISTENING" ? (
              <MicOff className="w-5 h-5 animate-pulse" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
            {coreState === "LISTENING" && (
              <span className="absolute -inset-1 rounded-xl border border-emerald-400 animate-ping opacity-60 pointer-events-none" />
            )}
          </button>

          {/* Hybrid Keyboard Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (textInput.trim()) {
                handleExecuteVoiceCommand(textInput);
                setTextInput("");
              }
            }}
            className="flex-1 flex items-center space-x-2 bg-slate-900/60 rounded-xl px-3 py-2 border border-slate-800/80 focus-within:border-cyan-500/50 transition-all"
          >
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={`Ask CEO anything in ${selectedLanguage.name}... (or hold Spacebar)`}
              disabled={isProcessing || coreState === "LISTENING"}
              className="bg-transparent flex-1 text-sm text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!textInput.trim() || isProcessing}
              className="p-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-black disabled:opacity-30 transition-all"
              title="Submit command"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Hotkey Spacebar Badge */}
          <div className="hidden sm:flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-400">
            <span>Space</span>
          </div>
        </div>
      </footer>

      {/* 6. Language Selection Modal */}
      {isLanguageModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xl animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl max-h-[85vh] rounded-2xl border border-cyan-500/30 bg-slate-900/90 shadow-2xl p-6 flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/40 text-cyan-400">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">
                    Select Meeting Language
                  </h2>
                  <p className="text-xs text-slate-400">
                    The CEO speaks, recognizes, and formulates strategic answers in your preferred tongue.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsLanguageModalOpen(false)}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 py-4 overflow-y-auto max-h-[55vh] pr-1">
              {SUPPORTED_LANGUAGES.map((lang) => {
                const isSelected = selectedLanguage.code === lang.code;
                return (
                  <button
                    key={lang.code}
                    onClick={() => {
                      setSelectedLanguage(lang);
                      setIsLanguageModalOpen(false);
                      // Announce switch
                      speakText(
                        `Switched executive meeting language to ${lang.name}.`,
                        lang.code
                      );
                    }}
                    className={`flex items-center justify-between p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "border-cyan-500 bg-cyan-950/40 text-white shadow-[0_0_15px_rgba(6,182,212,0.2)]"
                        : "border-slate-800/80 bg-slate-950/40 hover:bg-slate-800/60 hover:border-slate-700 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{lang.flag}</span>
                      <div>
                        <div className="text-sm font-semibold">{lang.name}</div>
                        <div className="text-xs text-slate-400 font-mono">
                          {lang.nativeName} ({lang.code})
                        </div>
                      </div>
                    </div>
                    {isSelected && (
                      <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    )}
                  </button>
                );
              })}
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
              <span>Automatic BCP 47 Speech Recognition & Synthesis configured</span>
              <button
                onClick={() => setIsLanguageModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-black font-semibold text-xs"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. Right Drawer: Executive Meeting Audit & Conversation History */}
      <aside
        className={`fixed top-0 right-0 bottom-0 w-96 z-40 bg-slate-950/95 border-l border-cyan-500/20 backdrop-blur-2xl p-6 flex flex-col transition-transform duration-300 ease-in-out shadow-2xl ${
          showHistoryDrawer ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">
              Meeting Audit & History
            </h3>
          </div>
          <button
            onClick={() => setShowHistoryDrawer(false)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
          {interactionHistory.length === 0 ? (
            <div className="text-center py-16 text-slate-500 text-xs">
              <History className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p>No voice interactions logged yet in this session.</p>
              <p className="mt-1">Speak into the core to record strategic decisions.</p>
            </div>
          ) : (
            interactionHistory.map((item) => (
              <div
                key={item.id}
                className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 text-xs space-y-2 hover:border-cyan-500/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-cyan-400">
                    You: &ldquo;{item.transcript}&rdquo;
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    {item.intent}
                  </span>
                </div>

                <div className="text-slate-300 border-l-2 border-cyan-500/50 pl-2 text-[11px] leading-relaxed">
                  {item.spoken_response}
                </div>

                {item.action_taken && (
                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60">
                    <span className="text-emerald-400 font-mono">
                      Action: {item.action_taken}
                    </span>
                    <span>{item.execution_time_ms.toFixed(0)}ms</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-500">
          <span>Session: {sessionId || "Active"}</span>
          <button
            onClick={() => setInteractionHistory([])}
            className="text-slate-400 hover:text-red-400 transition-colors"
          >
            Clear History
          </button>
        </div>
      </aside>

      {/* 8. Left Drawer: Company Intelligence HUD */}
      <aside
        className={`fixed top-0 left-0 bottom-0 w-80 z-40 bg-slate-950/95 border-r border-cyan-500/20 backdrop-blur-2xl p-6 flex flex-col transition-transform duration-300 ease-in-out shadow-2xl ${
          showMetricsDrawer ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">
              Company Intelligence
            </h3>
          </div>
          <button
            onClick={() => setShowMetricsDrawer(false)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          {/* Company Brief Card */}
          <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/50">
            <h4 className="text-xs font-bold text-white mb-1">
              {company?.name || "AI Company OS"}
            </h4>
            <p className="text-[11px] text-slate-400 line-clamp-2">
              {company?.description || "Autonomous multi-agent enterprise."}
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-2">
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/40 text-center">
              <span className="text-lg font-bold text-cyan-400">
                {companyStats.projects}
              </span>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">
                Projects
              </p>
            </div>
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/40 text-center">
              <span className="text-lg font-bold text-indigo-400">
                {companyStats.tasks}
              </span>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">
                Tasks
              </p>
            </div>
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/40 text-center">
              <span className="text-lg font-bold text-amber-400">
                {companyStats.approvals}
              </span>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">
                Approvals
              </p>
            </div>
          </div>

          {/* CEO Operational Authority Level */}
          <div className="p-3.5 rounded-xl border border-cyan-500/20 bg-cyan-950/20 text-xs">
            <div className="flex items-center space-x-2 text-cyan-300 font-bold mb-1">
              <Shield className="w-4 h-4" />
              <span>Full Autonomous Authority</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              The CEO agent has delegated jurisdiction over task dispatch, project alignment, and company-wide strategic briefings.
            </p>
          </div>

          {/* Detailed Response Breakdown if available */}
          {activeCeoDetailed && (
            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/40 text-xs">
              <h5 className="font-bold text-slate-200 mb-1 flex items-center space-x-1.5">
                <Info className="w-3.5 h-3.5 text-cyan-400" />
                <span>Executive Context</span>
              </h5>
              <div className="text-[11px] text-slate-300 whitespace-pre-wrap font-mono leading-relaxed mt-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                {activeCeoDetailed}
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500">
          <span>Target Language: {selectedLanguage.name}</span>
        </div>
      </aside>
    </div>
  );
}
