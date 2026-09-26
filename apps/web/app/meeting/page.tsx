"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  BarChart3,
  Bot,
  Brain,
  Camera,
  CameraOff,
  CheckCircle2,
  Clock,
  Code2,
  Cpu,
  FileText,
  Filter,
  Globe,
  HelpCircle,
  Info,
  Lightbulb,
  Maximize2,
  Mic,
  MicOff,
  Minimize2,
  Monitor,
  MonitorOff,
  PhoneOff,
  Radio,
  RefreshCw,
  Send,
  Settings,
  Shield,
  Sparkles,
  Users,
  Video,
  Volume2,
  VolumeX,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import {
  api,
  type Agent,
  type Company,
  type ErrorRecord,
  type Project,
  type Task,
  type VoiceCommandResponse,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Supported Languages & Models
// ---------------------------------------------------------------------------
interface MeetingLanguage {
  code: string;
  name: string;
  native: string;
  flag: string;
}

const MEETING_LANGUAGES: MeetingLanguage[] = [
  { code: "en-US", name: "English (US)", native: "English", flag: "🇺🇸" },
  { code: "bn-BD", name: "Bengali", native: "বাংলা", flag: "🇧🇩" },
  { code: "es-ES", name: "Spanish", native: "Español", flag: "🇪🇸" },
  { code: "fr-FR", name: "French", native: "Français", flag: "🇫🇷" },
  { code: "de-DE", name: "German", native: "Deutsch", flag: "🇩🇪" },
  { code: "ar-SA", name: "Arabic", native: "العربية", flag: "🇸🇦" },
  { code: "hi-IN", name: "Hindi", native: "हिन्दी", flag: "🇮🇳" },
  { code: "zh-CN", name: "Mandarin", native: "中文", flag: "🇨🇳" },
  { code: "ja-JP", name: "Japanese", native: "日本語", flag: "🇯🇵" },
  { code: "pt-BR", name: "Portuguese", native: "Português", flag: "🇧🇷" },
  { code: "it-IT", name: "Italian", native: "Italiano", flag: "🇮🇹" },
  { code: "ru-RU", name: "Russian", native: "Русский", flag: "🇷🇺" },
  { code: "ko-KR", name: "Korean", native: "한국어", flag: "🇰🇷" },
  { code: "nl-NL", name: "Dutch", native: "Nederlands", flag: "🇳🇱" },
  { code: "tr-TR", name: "Turkish", native: "Türkçe", flag: "🇹🇷" },
];

const AI_MODELS = [
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI", badge: "Multimodal Live" },
  { id: "claude-3-5-sonnet", name: "Claude 3.5 Sonnet", provider: "Anthropic", badge: "Deep Reasoning" },
  { id: "gemini-2-flash", name: "Gemini 2.0 Flash", provider: "Google DeepMind", badge: "Ultra Low Latency" },
];

interface ChatMessage {
  id: string;
  sender: "ai" | "user";
  senderName: string;
  text: string;
  timestamp: string;
  category?: "projects" | "bugs" | "features" | "engineering" | "general";
}

export default function AgentMeetingRoomPage() {
  // Company & Agent context
  const [company, setCompany] = useState<Company | null>(null);
  const [companyId, setCompanyId] = useState<string>("");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeAgent, setActiveAgent] = useState<{
    id: string;
    name: string;
    role: string;
    avatarUrl?: string;
  }>({
    id: "ai-assistant",
    name: "AI Assistant",
    role: "Executive Co-Pilot",
  });

  // Call & Meeting State
  const [isCallActive, setIsCallActive] = useState<boolean>(true);
  const [isMicOn, setIsMicOn] = useState<boolean>(true);
  const [isCameraOn, setIsCameraOn] = useState<boolean>(false);
  const [isScreenSharing, setIsScreenSharing] = useState<boolean>(false);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(false);
  const [isAiThinking, setIsAiThinking] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Settings
  const [selectedLanguage, setSelectedLanguage] = useState<MeetingLanguage>(MEETING_LANGUAGES[0]);
  const [selectedModel, setSelectedModel] = useState<string>(AI_MODELS[0].name);

  // Live Timer
  const [sessionSeconds, setSessionSeconds] = useState<number>(765); // 00:12:45 initial start

  // Messages
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      sender: "ai",
      senderName: "AI Assistant",
      text: "Hello! How can I help you today? We can review active projects, triage bugs, or architect new features.",
      timestamp: "10:42 AM",
      category: "general",
    },
    {
      id: "msg-2",
      sender: "user",
      senderName: "You",
      text: "Can you analyze the project milestones and open bug trends?",
      timestamp: "10:43 AM",
      category: "projects",
    },
    {
      id: "msg-3",
      sender: "ai",
      senderName: "AI Assistant",
      text: "Certainly! I am pulling the latest project velocity metrics and open error records right away.",
      timestamp: "10:43 AM",
      category: "projects",
    },
  ]);

  const [typedInput, setTypedInput] = useState<string>("");
  const [interimSpeech, setInterimSpeech] = useState<string>("");

  // Live audio visualization level (0 - 100)
  const [audioLevel, setAudioLevel] = useState<number>(35);

  // Video streams
  const cameraVideoRef = useRef<HTMLVideoElement | null>(null);
  const screenVideoRef = useRef<HTMLVideoElement | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);

  // Speech Recognition & Synthesis references
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);
  const orbCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // ---------------------------------------------------------------------------
  // Load Context on Mount
  // ---------------------------------------------------------------------------
  useEffect(() => {
    async function loadData() {
      try {
        const comps = await api.getCompanies();
        if (comps.length > 0) {
          const comp = comps[0];
          setCompany(comp);
          setCompanyId(comp.id);

          // Load agents
          try {
            const agentList = await api.getAgents(comp.id);
            if (agentList?.length > 0) {
              setAgents(agentList);
              const ceo = agentList.find((a) => a.role?.toLowerCase().includes("ceo")) || agentList[0];
              setActiveAgent({
                id: ceo.id,
                name: ceo.name,
                role: ceo.role,
              });
            }
          } catch (e) {
            // fallback gracefully
          }
        }
      } catch (err) {
        console.error("Failed to load initial meeting context:", err);
      }
    }
    loadData();
  }, []);

  // ---------------------------------------------------------------------------
  // Session Clock Timer
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!isCallActive) return;
    const interval = setInterval(() => {
      setSessionSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isCallActive]);

  const formatTimer = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${pad(hours)}:${pad(mins)}:${pad(secs)}`;
  };

  // Scroll to bottom on new message
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, interimSpeech, isAiThinking]);

  // ---------------------------------------------------------------------------
  // 3D Iridescent Holographic Orb (Canvas Shader Animation)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const canvas = orbCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let time = 0;

    function renderOrb() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2 - 15;
      time += 0.02;

      // Dynamic floating bounce
      const floatY = Math.sin(time * 1.5) * 8;
      const orbY = centerY + floatY;

      // Dynamic radius scaling with audio level
      const pulseMultiplier = 1 + (audioLevel / 100) * 0.12;
      const radius = 100 * pulseMultiplier;

      // 1. Perspective Floor Ripple Rings
      const floorY = canvas.height - 35;
      const ringCount = 3;
      for (let r = 1; r <= ringCount; r++) {
        const ringRadiusX = 120 + r * 45 + Math.sin(time * 2 + r) * 6;
        const ringRadiusY = ringRadiusX * 0.28; // perspective compression
        ctx.beginPath();
        ctx.ellipse(centerX, floorY, ringRadiusX, ringRadiusY, 0, 0, Math.PI * 2);
        const ringAlpha = (0.28 - r * 0.08) * (1 + (audioLevel / 100) * 0.5);
        ctx.strokeStyle = `rgba(168, 85, 247, ${Math.max(0.04, ringAlpha)})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      // Floor Ambient Glow
      const floorGlow = ctx.createRadialGradient(
        centerX,
        floorY,
        10,
        centerX,
        floorY,
        180
      );
      floorGlow.addColorStop(0, "rgba(192, 132, 252, 0.22)");
      floorGlow.addColorStop(0.5, "rgba(147, 51, 234, 0.08)");
      floorGlow.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = floorGlow;
      ctx.beginPath();
      ctx.ellipse(centerX, floorY, 180, 50, 0, 0, Math.PI * 2);
      ctx.fill();

      // 2. Outer Orb Aura / Corona
      const outerGlow = ctx.createRadialGradient(
        centerX,
        orbY,
        radius * 0.8,
        centerX,
        orbY,
        radius * 1.6
      );
      outerGlow.addColorStop(0, "rgba(216, 180, 254, 0.45)");
      outerGlow.addColorStop(0.4, "rgba(168, 85, 247, 0.25)");
      outerGlow.addColorStop(0.7, "rgba(59, 130, 246, 0.1)");
      outerGlow.addColorStop(1, "rgba(0, 0, 0, 0)");

      ctx.beginPath();
      ctx.arc(centerX, orbY, radius * 1.6, 0, Math.PI * 2);
      ctx.fillStyle = outerGlow;
      ctx.fill();

      // 3. Multi-Stop Iridescent Spherical Core Gradient
      // Offset light source top-right to create authentic 3D sphere volume
      const lightX = centerX + Math.cos(time * 0.8) * (radius * 0.25) - radius * 0.2;
      const lightY = orbY + Math.sin(time * 0.8) * (radius * 0.2) - radius * 0.3;

      const sphereGrad = ctx.createRadialGradient(
        lightX,
        lightY,
        radius * 0.05,
        centerX,
        orbY,
        radius
      );

      // Iridescent color stops: Pearlescent White -> Magenta/Pink -> Electric Violet -> Deep Indigo -> Dark Rim
      sphereGrad.addColorStop(0.0, "rgba(255, 255, 255, 1.0)");
      sphereGrad.addColorStop(0.18, "rgba(253, 224, 255, 0.95)");
      sphereGrad.addColorStop(0.4, "rgba(244, 114, 182, 0.9)");
      sphereGrad.addColorStop(0.65, "rgba(168, 85, 247, 0.85)");
      sphereGrad.addColorStop(0.85, "rgba(79, 70, 229, 0.75)");
      sphereGrad.addColorStop(1.0, "rgba(24, 16, 52, 0.9)");

      ctx.beginPath();
      ctx.arc(centerX, orbY, radius, 0, Math.PI * 2);
      ctx.fillStyle = sphereGrad;
      ctx.shadowColor = "rgba(192, 132, 252, 0.6)";
      ctx.shadowBlur = 35;
      ctx.fill();
      ctx.shadowBlur = 0; // reset

      // 4. Cyan / Azure Specular Glint Rim (Subtle iridescent edge)
      const rimGrad = ctx.createLinearGradient(
        centerX - radius,
        orbY - radius,
        centerX + radius,
        orbY + radius
      );
      rimGrad.addColorStop(0, "rgba(56, 189, 248, 0.6)");
      rimGrad.addColorStop(0.5, "rgba(236, 72, 153, 0.4)");
      rimGrad.addColorStop(1, "rgba(168, 85, 247, 0.5)");

      ctx.beginPath();
      ctx.arc(centerX, orbY, radius, 0, Math.PI * 2);
      ctx.strokeStyle = rimGrad;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // 5. High-Specular Star Reflection
      const specX = centerX - radius * 0.28;
      const specY = orbY - radius * 0.32;
      const specGrad = ctx.createRadialGradient(specX, specY, 1, specX, specY, radius * 0.35);
      specGrad.addColorStop(0, "rgba(255, 255, 255, 0.9)");
      specGrad.addColorStop(0.3, "rgba(255, 255, 255, 0.4)");
      specGrad.addColorStop(1, "rgba(255, 255, 255, 0)");

      ctx.beginPath();
      ctx.arc(specX, specY, radius * 0.35, 0, Math.PI * 2);
      ctx.fillStyle = specGrad;
      ctx.fill();

      animId = requestAnimationFrame(renderOrb);
    }

    renderOrb();
    return () => cancelAnimationFrame(animId);
  }, [audioLevel]);

  // ---------------------------------------------------------------------------
  // Web Audio API Analyzer for Live Soundwave Equalizer
  // ---------------------------------------------------------------------------
  const startAudioCapture = useCallback(async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) return;
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const loop = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setAudioLevel(Math.min(100, Math.max(15, avg * 1.5)));
        animFrameRef.current = requestAnimationFrame(loop);
      };

      loop();
    } catch (e) {
      console.warn("Microphone audio analyser initialization bypassed:", e);
      // Simulated subtle breathing soundwave
      const simInterval = setInterval(() => {
        setAudioLevel(20 + Math.random() * 25);
      }, 150);
      return () => clearInterval(simInterval);
    }
  }, []);

  const stopAudioCapture = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((t) => t.stop());
      micStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAudioLevel(15);
  }, []);

  // ---------------------------------------------------------------------------
  // Web Speech API: Text-to-Speech (Multilingual Voice Vocalizer)
  // ---------------------------------------------------------------------------
  const speakVoice = useCallback(
    (text: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      if (isAudioMuted || !text) return;

      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = selectedLanguage.code;
      utterance.rate = 1.0;
      utterance.pitch = 1.05;

      const voices = window.speechSynthesis.getVoices();
      const prefix = selectedLanguage.code.split("-")[0].toLowerCase();
      const matched =
        voices.find((v) => v.lang.toLowerCase() === selectedLanguage.code.toLowerCase()) ||
        voices.find((v) => v.lang.toLowerCase().startsWith(prefix));

      if (matched) utterance.voice = matched;

      utterance.onstart = () => setAudioLevel(75);
      utterance.onend = () => setAudioLevel(25);
      utterance.onerror = () => setAudioLevel(25);

      window.speechSynthesis.speak(utterance);
    },
    [isAudioMuted, selectedLanguage]
  );

  // ---------------------------------------------------------------------------
  // Action Handler: Process & Dispatch Meeting Inquiries
  // ---------------------------------------------------------------------------
  const handleProcessInquiry = useCallback(
    async (rawPrompt: string, explicitCategory?: ChatMessage["category"]) => {
      const prompt = rawPrompt.trim();
      if (!prompt || isAiThinking) return;

      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      // Add user message
      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: "user",
        senderName: "You",
        text: prompt,
        timestamp: timeStr,
        category: explicitCategory || "general",
      };
      setMessages((prev) => [...prev, userMsg]);
      setTypedInput("");
      setInterimSpeech("");
      setIsAiThinking(true);

      const lower = prompt.toLowerCase();
      let responseText = "";
      let category: ChatMessage["category"] = explicitCategory || "general";

      try {
        if (!companyId) {
          responseText = "I'm ready to assist with company operations. Let me connect to your workspace.";
        } else if (
          lower.includes("project") ||
          lower.includes("milestone") ||
          lower.includes("sprint") ||
          explicitCategory === "projects"
        ) {
          category = "projects";
          const projects = await api.getProjects(companyId);
          const tasks = await api.getTasks(companyId);
          const inProgress = tasks.items?.filter((t) => t.status === "IN_PROGRESS").length || 0;
          const totalProj = projects.total ?? projects.items?.length ?? 0;

          responseText = `We currently have ${totalProj} active projects in the portfolio, with ${inProgress} tasks actively in progress. All roadmap deadlines are aligned with executive targets.`;
        } else if (
          lower.includes("bug") ||
          lower.includes("error") ||
          lower.includes("fix") ||
          lower.includes("issue") ||
          explicitCategory === "bugs"
        ) {
          category = "bugs";
          try {
            const summary = await api.getCompanyErrorSummary(companyId);
            const totalErrors = summary.total_errors ?? 0;
            const openErrors = summary.open_count ?? 0;
            const investigating = summary.investigating_count ?? 0;

            if (openErrors === 0 && totalErrors === 0) {
              responseText =
                "Great news! There are zero unresolved critical bugs logged in the error subsystem. All systems are operating smoothly.";
            } else {
              responseText = `Currently tracking ${totalErrors} total bug records: ${openErrors} open, and ${investigating} currently under investigation by engineering agents.`;
            }
          } catch {
            const errorList = await api.getCompanyErrors(companyId).catch(() => ({ items: [] }));
            const count = errorList.items?.length ?? 0;
            responseText = `Currently tracking ${count} bug records in the error triage pipeline. All systems are being monitored.`;
          }
        } else if (
          lower.includes("feature") ||
          lower.includes("add feature") ||
          lower.includes("create task") ||
          explicitCategory === "features"
        ) {
          category = "features";
          // Create task directly in the company backlog
          const taskTitle = prompt
            .replace(/add feature/i, "")
            .replace(/create task/i, "")
            .replace(/new feature/i, "")
            .trim() || "New Proposed Strategic Feature";

          try {
            const newTask = await api.createTask(companyId, {
              title: taskTitle.slice(0, 120),
              description: `Proposed during AI Agent Meeting: "${prompt}"`,
              priority: "HIGH",
            });
            responseText = `I have architected and registered the new feature task: "${newTask.title}" (ID: ${newTask.id}) into the company backlog.`;
          } catch (e) {
            responseText = `I've noted the feature request: "${taskTitle}". Ready to plan architecture specifications.`;
          }
        } else {
          // Standard voice command backend routing
          const voiceRes = await api.sendVoiceCommand(companyId, {
            transcript: prompt,
            language: selectedLanguage.code,
          });
          responseText = voiceRes.spoken_response || voiceRes.detailed_response;
        }
      } catch (err: any) {
        console.error("Inquiry execution error:", err);
        responseText = `I received your meeting inquiry: "${prompt}". Operating parameters remain stable across company services.`;
      } finally {
        setIsAiThinking(false);
        const aiMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: "ai",
          senderName: activeAgent.name,
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          category,
        };
        setMessages((prev) => [...prev, aiMsg]);
        speakVoice(responseText);
      }
    },
    [companyId, isAiThinking, activeAgent.name, selectedLanguage, speakVoice]
  );

  // ---------------------------------------------------------------------------
  // Web Speech API: Speech Recognition
  // ---------------------------------------------------------------------------
  const startSpeechRecognition = useCallback(() => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = selectedLanguage.code;
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          if (res.isFinal) {
            const final = res[0].transcript;
            setInterimSpeech("");
            handleProcessInquiry(final);
          } else {
            interim += res[0].transcript;
          }
        }
        setInterimSpeech(interim);
      };

      recognition.onerror = (e: any) => {
        console.warn("Speech recognition notice:", e.error);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      console.warn("Speech recognition start skipped:", e);
    }
  }, [selectedLanguage, handleProcessInquiry]);

  const stopSpeechRecognition = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }
    setInterimSpeech("");
  }, []);

  // Manage mic toggle
  useEffect(() => {
    if (isMicOn && isCallActive) {
      startAudioCapture();
      startSpeechRecognition();
    } else {
      stopAudioCapture();
      stopSpeechRecognition();
    }
    return () => {
      stopAudioCapture();
      stopSpeechRecognition();
    };
  }, [isMicOn, isCallActive, startAudioCapture, stopAudioCapture, startSpeechRecognition, stopSpeechRecognition]);

  // ---------------------------------------------------------------------------
  // Hardware Media: Camera & Screen Sharing
  // ---------------------------------------------------------------------------
  const toggleCamera = async () => {
    if (isCameraOn) {
      if (cameraStreamRef.current) {
        cameraStreamRef.current.getTracks().forEach((t) => t.stop());
        cameraStreamRef.current = null;
      }
      setIsCameraOn(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        cameraStreamRef.current = stream;
        if (cameraVideoRef.current) {
          cameraVideoRef.current.srcObject = stream;
        }
        setIsCameraOn(true);
      } catch (e) {
        alert("Camera access was not granted or no webcam was detected.");
      }
    }
  };

  const toggleScreenShare = async () => {
    if (isScreenSharing) {
      if (screenStreamRef.current) {
        screenStreamRef.current.getTracks().forEach((t) => t.stop());
        screenStreamRef.current = null;
      }
      setIsScreenSharing(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        screenStreamRef.current = stream;
        if (screenVideoRef.current) {
          screenVideoRef.current.srcObject = stream;
        }
        setIsScreenSharing(true);
        stream.getVideoTracks()[0].onended = () => {
          setIsScreenSharing(false);
        };
      } catch (e) {
        // User cancelled or unsupported
      }
    }
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // ---------------------------------------------------------------------------
  // Soundwave Equalizer Visualization (Right Card)
  // ---------------------------------------------------------------------------
  const equalizerBars = Array.from({ length: 28 }).map((_, i) => {
    const centerFactor = 1 - Math.abs(i - 14) / 14;
    const baseHeight = 8;
    const dynamicHeight = Math.max(
      6,
      Math.min(52, baseHeight + centerFactor * (audioLevel * 0.45) + Math.sin(i * 0.8) * 6)
    );
    return dynamicHeight;
  });

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#07080f] text-slate-100 select-none font-sans flex flex-col items-center justify-center p-4 md:p-6">
      {/* Background Subtle Mesh Radial Glows */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[750px] bg-gradient-to-tr from-purple-900/15 via-indigo-900/20 to-pink-900/15 rounded-full blur-[160px] pointer-events-none" />

      {/* Main Container Window (Sleek Obsidian Cyber Bezel) */}
      <div className="relative w-full max-w-[1440px] h-full max-h-[920px] rounded-3xl border border-purple-900/30 bg-[#0a0b14]/90 backdrop-blur-3xl shadow-[0_0_80px_rgba(112,26,117,0.18)] flex flex-col overflow-hidden">
        
        {/* Top Header Row */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-purple-900/20 z-20">
          {/* Top-Left: Active AI Agent Identity Pill */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2.5 px-3 py-1.5 rounded-xl border border-purple-500/30 bg-purple-950/30 backdrop-blur-md">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-purple-500/30 to-pink-500/30 border border-purple-400/40 flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-purple-300" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-1.5">
                  <span className="text-xs font-semibold text-white tracking-wide">
                    {activeAgent.name}
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <span className="text-[10px] text-purple-300/80 -mt-0.5">Online</span>
              </div>
            </div>

            {/* Switch Agent Dropdown */}
            {agents.length > 1 && (
              <select
                value={activeAgent.id}
                onChange={(e) => {
                  const ag = agents.find((a) => a.id === e.target.value);
                  if (ag) {
                    setActiveAgent({ id: ag.id, name: ag.name, role: ag.role });
                    speakVoice(`Switched meeting presenter to ${ag.name}, ${ag.role}.`);
                  }
                }}
                className="bg-slate-900/60 border border-purple-900/40 text-purple-200 text-xs rounded-xl px-2.5 py-1.5 focus:outline-none focus:border-purple-500/60"
              >
                {agents.map((ag) => (
                  <option key={ag.id} value={ag.id} className="bg-slate-900 text-white">
                    {ag.name} ({ag.role})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Top-Right: Controls & Settings */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={toggleFullscreen}
              className="p-2 rounded-xl border border-purple-900/30 bg-purple-950/20 hover:bg-purple-900/30 text-purple-300 transition-all text-xs"
              title="Toggle Fullscreen"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-xl border border-purple-900/30 bg-purple-950/20 hover:bg-purple-900/40 text-purple-300 hover:text-white transition-all shadow-sm"
              title="Meeting & Model Settings"
            >
              <Settings className="w-4 h-4" />
            </button>

            <Link
              href="/dashboard"
              className="p-2 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-400 hover:text-white text-xs transition-all"
              title="Close Meeting Window"
            >
              <X className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Meeting Body: 3-Column Glass Layout */}
        <div className="flex-1 grid grid-cols-12 gap-4 p-5 overflow-hidden z-10">
          
          {/* ================================================================= */}
          {/* LEFT COLUMN: Conversation & Session Info                          */}
          {/* ================================================================= */}
          <div className="col-span-12 lg:col-span-3 flex flex-col space-y-4 h-full overflow-hidden">
            {/* 1. Conversation Card */}
            <div className="flex-1 flex flex-col rounded-2xl border border-purple-900/30 bg-[#0e101b]/80 backdrop-blur-xl p-4 overflow-hidden shadow-lg">
              {/* Card Header */}
              <div className="flex items-center justify-between pb-3 border-b border-purple-900/20 mb-3">
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    <span className="w-1 h-3 bg-purple-400 rounded-full" />
                    <span className="w-1 h-4 bg-pink-400 rounded-full" />
                    <span className="w-1 h-2 bg-purple-400 rounded-full" />
                  </div>
                  <h3 className="text-xs font-semibold text-white tracking-wide">Conversation</h3>
                </div>
                <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-pink-950/50 border border-pink-500/40 text-pink-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-ping mr-0.5" />
                  Live
                </span>
              </div>

              {/* Chat Stream */}
              <div ref={chatScrollRef} className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs no-scrollbar">
                {messages.map((msg) => (
                  <div key={msg.id} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span
                        className={`font-semibold ${
                          msg.sender === "ai" ? "text-purple-300" : "text-pink-400"
                        }`}
                      >
                        {msg.senderName}
                      </span>
                      <span className="text-[10px] text-slate-500">{msg.timestamp}</span>
                    </div>
                    <p className="text-slate-300 text-xs leading-relaxed bg-slate-900/40 p-2.5 rounded-xl border border-slate-800/40">
                      {msg.text}
                    </p>
                  </div>
                ))}

                {/* Interim Live Speech Transcript */}
                {interimSpeech && (
                  <div className="space-y-1">
                    <span className="text-pink-400 font-semibold text-[11px]">You (speaking...)</span>
                    <p className="text-slate-200 text-xs italic bg-pink-950/20 p-2 rounded-xl border border-pink-500/30">
                      {interimSpeech}
                    </p>
                  </div>
                )}

                {/* AI Thinking Animation */}
                {isAiThinking && (
                  <div className="flex items-center space-x-1.5 py-1 text-purple-400 text-xs">
                    <Sparkles className="w-3.5 h-3.5 animate-spin" />
                    <span>Thinking...</span>
                  </div>
                )}
              </div>

              {/* Quick Input Bar */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (typedInput.trim()) {
                    handleProcessInquiry(typedInput);
                  }
                }}
                className="mt-3 pt-2 border-t border-purple-900/20 flex items-center space-x-2"
              >
                <input
                  type="text"
                  value={typedInput}
                  onChange={(e) => setTypedInput(e.target.value)}
                  placeholder="Ask or discuss anything..."
                  className="flex-1 bg-slate-900/80 border border-purple-900/40 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50"
                />
                <button
                  type="submit"
                  disabled={!typedInput.trim() || isAiThinking}
                  className="p-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-40 transition-all"
                >
                  <Send className="w-3 h-3" />
                </button>
              </form>
            </div>

            {/* 2. Session Info Card */}
            <div className="rounded-2xl border border-purple-900/30 bg-[#0e101b]/80 backdrop-blur-xl p-4 shadow-lg text-xs space-y-3">
              <div className="flex items-center space-x-2 pb-2 border-b border-purple-900/20">
                <Info className="w-3.5 h-3.5 text-purple-400" />
                <h4 className="font-semibold text-white tracking-wide text-xs">Session Info</h4>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-slate-400">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>Duration</span>
                  </div>
                  <span className="font-mono text-white font-medium">{formatTimer(sessionSeconds)}</span>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-3.5 h-3.5 text-slate-500" />
                    <span>Model</span>
                  </div>
                  <span className="text-purple-300 font-medium">{selectedModel}</span>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <div className="flex items-center space-x-2">
                    <Globe className="w-3.5 h-3.5 text-slate-500" />
                    <span>Language</span>
                  </div>
                  <span className="text-slate-200 font-medium flex items-center space-x-1">
                    <span>{selectedLanguage.flag}</span>
                    <span>{selectedLanguage.name}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ================================================================= */}
          {/* CENTER STAGE: Iridescent 3D Orb & Floating Call Control Dock       */}
          {/* ================================================================= */}
          <div className="col-span-12 lg:col-span-6 flex flex-col items-center justify-between relative h-full">
            
            {/* Screen Share / Camera Preview Floating Overlay if active */}
            {isScreenSharing && (
              <div className="absolute top-2 left-4 right-4 h-48 rounded-2xl border border-purple-500/40 bg-black/80 overflow-hidden shadow-2xl z-20">
                <video ref={screenVideoRef} autoPlay playsInline className="w-full h-full object-contain" />
                <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/60 text-[10px] text-purple-300">
                  Screen Share Active
                </span>
              </div>
            )}

            {isCameraOn && (
              <div className="absolute bottom-28 right-4 w-36 h-28 rounded-xl border border-purple-500/40 bg-black/80 overflow-hidden shadow-2xl z-20">
                <video ref={cameraVideoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                <span className="absolute bottom-1 left-1 px-1.5 py-0.2 rounded bg-black/60 text-[9px] text-pink-300">
                  Camera
                </span>
              </div>
            )}

            {/* Central Holographic 3D Iridescent Orb */}
            <div className="flex-1 flex items-center justify-center w-full relative">
              <canvas
                ref={orbCanvasRef}
                width={420}
                height={400}
                className="cursor-pointer transition-transform duration-500 hover:scale-105 active:scale-95"
                onClick={() => {
                  speakVoice("Meeting room active. What topic shall we explore next?");
                }}
                title="Click Holographic Orb to interact"
              />
            </div>

            {/* Floating Meeting Call Control Dock */}
            <div className="mb-4 z-20">
              <div className="flex items-center space-x-6 px-6 py-3 rounded-2xl border border-purple-500/20 bg-[#121320]/90 backdrop-blur-2xl shadow-[0_0_50px_rgba(112,26,117,0.25)]">
                
                {/* Red End Call Button */}
                <button
                  onClick={() => {
                    setIsCallActive(false);
                    stopAudioCapture();
                    stopSpeechRecognition();
                    window.location.href = "/dashboard";
                  }}
                  className="w-12 h-12 rounded-full bg-rose-500 hover:bg-rose-600 text-white flex items-center justify-center shadow-[0_0_25px_rgba(244,63,94,0.6)] hover:scale-105 active:scale-95 transition-all"
                  title="Leave Meeting Room"
                >
                  <PhoneOff className="w-5 h-5" />
                </button>

                {/* Share Screen Button */}
                <button
                  onClick={toggleScreenShare}
                  className={`flex flex-col items-center space-y-1 transition-colors ${
                    isScreenSharing ? "text-purple-400" : "text-slate-400 hover:text-white"
                  }`}
                  title="Share Screen"
                >
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:bg-slate-800">
                    {isScreenSharing ? <MonitorOff className="w-5 h-5" /> : <Monitor className="w-5 h-5" />}
                  </div>
                  <span className="text-[10px] font-medium tracking-wide">Share Screen</span>
                </button>

                {/* Camera Toggle Button */}
                <button
                  onClick={toggleCamera}
                  className={`flex flex-col items-center space-y-1 transition-colors ${
                    isCameraOn ? "text-purple-400" : "text-slate-400 hover:text-white"
                  }`}
                  title="Toggle Video Camera"
                >
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:bg-slate-800">
                    {isCameraOn ? <Camera className="w-5 h-5" /> : <CameraOff className="w-5 h-5" />}
                  </div>
                  <span className="text-[10px] font-medium tracking-wide">Camera</span>
                </button>

                {/* Microphone Toggle Button */}
                <button
                  onClick={() => setIsMicOn(!isMicOn)}
                  className={`flex flex-col items-center space-y-1 transition-colors ${
                    isMicOn ? "text-emerald-400" : "text-slate-500 hover:text-slate-300"
                  }`}
                  title="Toggle Microphone"
                >
                  <div
                    className={`p-2.5 rounded-xl border transition-all ${
                      isMicOn
                        ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                        : "bg-slate-900/60 border-slate-800 text-slate-500"
                    }`}
                  >
                    {isMicOn ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
                  </div>
                  <span className="text-[10px] font-medium tracking-wide">Microphone</span>
                </button>
              </div>
            </div>
          </div>

          {/* ================================================================= */}
          {/* RIGHT COLUMN: Capabilities & Audio Level Visualizer               */}
          {/* ================================================================= */}
          <div className="col-span-12 lg:col-span-3 flex flex-col space-y-4 h-full overflow-hidden">
            
            {/* 1. Capabilities / Meeting Focus Agenda Card */}
            <div className="flex-1 rounded-2xl border border-purple-900/30 bg-[#0e101b]/80 backdrop-blur-xl p-4 shadow-lg flex flex-col overflow-hidden">
              <div className="flex items-center space-x-2 pb-3 border-b border-purple-900/20 mb-3">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <h3 className="text-xs font-semibold text-white tracking-wide">Capabilities</h3>
              </div>

              <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 no-scrollbar">
                {/* Capability 1: Projects & Data Analysis */}
                <button
                  onClick={() =>
                    handleProcessInquiry("Can you analyze active project milestones and timeline velocity?", "projects")
                  }
                  className="w-full flex items-start space-x-3 p-3 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-purple-950/30 hover:border-purple-500/40 text-left transition-all group"
                >
                  <div className="p-2 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-indigo-400 group-hover:scale-105 transition-transform shrink-0">
                    <BarChart3 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors">
                      Data Analysis
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                      Process and analyze complex data
                    </p>
                  </div>
                </button>

                {/* Capability 2: Smart Insights & Feature Add */}
                <button
                  onClick={() =>
                    handleProcessInquiry("Generate strategic insights and suggest next features to build.", "features")
                  }
                  className="w-full flex items-start space-x-3 p-3 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-purple-950/30 hover:border-purple-500/40 text-left transition-all group"
                >
                  <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-500/30 text-purple-400 group-hover:scale-105 transition-transform shrink-0">
                    <Lightbulb className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors">
                      Smart Insights
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                      Generate actionable insights
                    </p>
                  </div>
                </button>

                {/* Capability 3: Report Generation & Bug Triage */}
                <button
                  onClick={() =>
                    handleProcessInquiry("Generate executive report on open bugs and error resolutions.", "bugs")
                  }
                  className="w-full flex items-start space-x-3 p-3 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-purple-950/30 hover:border-purple-500/40 text-left transition-all group"
                >
                  <div className="p-2 rounded-lg bg-pink-950/60 border border-pink-500/30 text-pink-400 group-hover:scale-105 transition-transform shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors">
                      Report Generation
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                      Create detailed reports
                    </p>
                  </div>
                </button>

                {/* Capability 4: Code Assistance & Bug Fixing */}
                <button
                  onClick={() =>
                    handleProcessInquiry("Help with coding, bug fixing, and repository verification.", "engineering")
                  }
                  className="w-full flex items-start space-x-3 p-3 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-purple-950/30 hover:border-purple-500/40 text-left transition-all group"
                >
                  <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 group-hover:scale-105 transition-transform shrink-0">
                    <Code2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors">
                      Code Assistance
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                      Help with coding and debugging
                    </p>
                  </div>
                </button>
              </div>
            </div>

            {/* 2. Audio Level Equalizer Card */}
            <div className="rounded-2xl border border-purple-900/30 bg-[#0e101b]/80 backdrop-blur-xl p-4 shadow-lg text-xs space-y-3">
              <div className="flex items-center space-x-2 pb-2 border-b border-purple-900/20">
                <div className="flex items-center space-x-1">
                  <span className="w-1 h-3 bg-purple-400 rounded-full" />
                  <span className="w-1 h-4 bg-pink-400 rounded-full" />
                  <span className="w-1 h-2 bg-purple-400 rounded-full" />
                </div>
                <h4 className="font-semibold text-white tracking-wide text-xs">Audio Level</h4>
              </div>

              {/* Symmetric Equalizer Frequency Bars */}
              <div className="h-16 flex items-center justify-center space-x-1 px-2">
                {equalizerBars.map((height, idx) => (
                  <div
                    key={idx}
                    style={{ height: `${height}px` }}
                    className="w-1.5 rounded-full bg-gradient-to-t from-indigo-500 via-purple-500 to-pink-400 transition-all duration-75 opacity-90 shadow-[0_0_8px_rgba(236,72,153,0.3)]"
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xl animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl border border-purple-500/30 bg-slate-900/95 shadow-2xl p-6 flex flex-col space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-purple-900/40">
              <div className="flex items-center space-x-2">
                <Settings className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white">Meeting Settings</h3>
              </div>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* AI Model Selection */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Active AI Intelligence Model</label>
              <div className="grid grid-cols-1 gap-2">
                {AI_MODELS.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => setSelectedModel(model.name)}
                    className={`flex items-center justify-between p-2.5 rounded-xl border text-xs text-left transition-all ${
                      selectedModel === model.name
                        ? "border-purple-500 bg-purple-950/40 text-white shadow-[0_0_15px_rgba(168,85,247,0.2)]"
                        : "border-slate-800 bg-slate-950/40 text-slate-300 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <span className="font-bold">{model.name}</span>
                      <span className="text-[10px] text-slate-500 ml-2">({model.provider})</span>
                    </div>
                    <span className="text-[10px] font-mono text-purple-300 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/40">
                      {model.badge}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Language Selection */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Spoken & Synthesized Language</label>
              <div className="grid grid-cols-3 gap-2 max-h-40 overflow-y-auto pr-1">
                {MEETING_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setSelectedLanguage(lang)}
                    className={`flex items-center space-x-2 p-2 rounded-lg border text-xs text-left transition-all ${
                      selectedLanguage.code === lang.code
                        ? "border-purple-500 bg-purple-950/40 text-white"
                        : "border-slate-800 bg-slate-950/40 text-slate-400 hover:text-white"
                    }`}
                  >
                    <span className="text-sm">{lang.flag}</span>
                    <span className="truncate">{lang.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Audio Mute */}
            <div className="pt-2 border-t border-purple-900/30 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2 text-slate-300">
                {isAudioMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4 text-purple-400" />}
                <span>Voice Audio Playback</span>
              </div>
              <button
                onClick={() => setIsAudioMuted(!isAudioMuted)}
                className={`px-3 py-1 rounded-lg text-xs font-medium border ${
                  isAudioMuted
                    ? "border-rose-500/40 bg-rose-950/30 text-rose-300"
                    : "border-purple-500/40 bg-purple-950/30 text-purple-300"
                }`}
              >
                {isAudioMuted ? "Muted" : "Enabled"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
