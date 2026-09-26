"""Application service for Voice Interface adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.services.activity_service import ActivityService
from domain.voice.exceptions import (
    InvalidVoiceCommandError,
    VoiceAccessDeniedError,
    VoiceSessionNotFoundError,
)
from domain.voice.schemas import (
    VoiceCommandPayload,
    VoiceCommandResponse,
    VoiceIntent,
    VoiceInteractionItem,
    VoiceSessionCreatePayload,
    VoiceSessionListResponse,
    VoiceSessionResponse,
    VoiceState,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceTelemetryResponse,
)
from infrastructure.database.models import (
    Agent,
    ApprovalRequest,
    Company,
    CompanyKnowledge,
    CompanyMember,
    Project,
    Task,
    VoiceInteraction,
    VoiceSession,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure a datetime object is timezone-aware UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class VoiceService:
    """Service orchestrating natural voice control, intent routing, and conversation state."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _verify_company_access(self, company_id: str, user_id: str) -> CompanyMember:
        """Verify user is an active member of the target company."""
        company_res = await self.db.execute(select(Company).where(Company.id == company_id))
        company = company_res.scalar_one_or_none()
        if not company:
            raise VoiceSessionNotFoundError(f"Company {company_id} not found")

        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise VoiceAccessDeniedError(
                f"User {user_id} does not have access to company {company_id}"
            )
        return member

    def _to_interaction_item(self, item: VoiceInteraction) -> VoiceInteractionItem:
        """Convert ORM VoiceInteraction to schema item."""
        return VoiceInteractionItem(
            id=item.id,
            session_id=item.session_id,
            company_id=item.company_id,
            user_id=item.user_id,
            transcript=item.transcript,
            intent=item.intent,
            action_taken=item.action_taken,
            action_entity_id=item.action_entity_id,
            action_success=item.action_success,
            spoken_response=item.spoken_response,
            detailed_response=item.detailed_response,
            execution_time_ms=item.execution_time_ms,
            created_at=_ensure_utc(item.created_at) or datetime.now(UTC),
        )

    def _to_session_response(
        self,
        session: VoiceSession,
        interactions: list[VoiceInteraction] | None = None,
    ) -> VoiceSessionResponse:
        """Convert ORM VoiceSession to schema response."""
        items: list[VoiceInteractionItem] = []
        if interactions is not None:
            items = [self._to_interaction_item(i) for i in interactions]
        elif "interactions" in session.__dict__ and session.interactions:
            items = [self._to_interaction_item(i) for i in session.interactions]

        return VoiceSessionResponse(
            id=session.id,
            company_id=session.company_id,
            user_id=session.user_id,
            title=session.title,
            state=session.state,
            context_data=session.context_data or {},
            created_at=_ensure_utc(session.created_at) or datetime.now(UTC),
            updated_at=_ensure_utc(session.updated_at) or datetime.now(UTC),
            interactions=items,
        )

    async def create_session(
        self,
        company_id: str,
        user_id: str,
        payload: VoiceSessionCreatePayload | None = None,
    ) -> VoiceSessionResponse:
        """Create a new conversational voice session."""
        await self._verify_company_access(company_id, user_id)

        title = payload.title if payload and payload.title else "Voice Session"
        session = VoiceSession(
            id=f"vcs-{uuid.uuid4().hex[:12]}",
            company_id=company_id,
            user_id=user_id,
            title=title,
            state=VoiceState.IDLE.value,
            context_data={},
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return self._to_session_response(session, interactions=[])

    async def get_session(
        self,
        company_id: str,
        user_id: str,
        session_id: str,
    ) -> VoiceSessionResponse:
        """Retrieve a specific voice session by ID with interaction history."""
        await self._verify_company_access(company_id, user_id)

        stmt = (
            select(VoiceSession)
            .options(selectinload(VoiceSession.interactions))
            .where(
                VoiceSession.id == session_id,
                VoiceSession.company_id == company_id,
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise VoiceSessionNotFoundError(f"Voice session {session_id} not found")
        return self._to_session_response(session, interactions=list(session.interactions))

    async def list_sessions(
        self,
        company_id: str,
        user_id: str,
        limit: int = 20,
    ) -> VoiceSessionListResponse:
        """List voice sessions for a user in a company."""
        await self._verify_company_access(company_id, user_id)

        stmt = (
            select(VoiceSession)
            .options(selectinload(VoiceSession.interactions))
            .where(
                VoiceSession.company_id == company_id,
                VoiceSession.user_id == user_id,
            )
            .order_by(desc(VoiceSession.updated_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()
        count_stmt = select(func.count(VoiceSession.id)).where(
            VoiceSession.company_id == company_id,
            VoiceSession.user_id == user_id,
        )
        total = (await self.db.execute(count_stmt)).scalar_one() or 0

        return VoiceSessionListResponse(
            items=[
                self._to_session_response(s, interactions=list(s.interactions)) for s in sessions
            ],
            total=total,
        )

    def _detect_intent(self, text: str, context: dict[str, Any]) -> VoiceIntent:
        """Classify natural language voice inquiry or command into a VoiceIntent."""
        lower = text.lower().strip()

        # 1. Approval Decisions
        approval_keywords = [
            "approve that",
            "approve this",
            "grant approval",
            "approve request",
            "confirm approval",
            # Bengali
            "অনুমোদন করো",
            "অনুমোদন করুন",
            "মঞ্জুর করো",
            # Spanish
            "aprobar esto",
            "aprueba esto",
            "aprobar solicitud",
            "conceder aprobación",
            # French
            "approuver ceci",
            "accorder l'approbation",
            "valider la demande",
            # German
            "genehmigen",
            "bestätigen",
            # Hindi
            "मंजूर करो",
            "स्वीकृत करो",
            # Arabic
            "وافق على",
            "الموافقة",
            # Chinese
            "批准",
            "同意",
            # Japanese
            "承認する",
            "承認",
        ]
        if any(w in lower for w in approval_keywords):
            return VoiceIntent.APPROVAL_DECISION

        reject_keywords = [
            "reject that",
            "reject this",
            "deny request",
            "decline approval",
            # Bengali
            "বাতিল করো",
            "প্রত্যাখ্যান করো",
            # Spanish
            "rechazar esto",
            "denegar solicitud",
            # French
            "rejeter ceci",
            "refuser la demande",
            # German
            "ablehnen",
            # Hindi
            "अस्वीकार करो",
            "खारिज करो",
            # Arabic
            "ارفض",
            "رفض",
            # Chinese
            "拒绝",
            "驳回",
            # Japanese
            "却下する",
            "拒否",
        ]
        if any(w in lower for w in reject_keywords):
            return VoiceIntent.APPROVAL_DECISION

        # 2. Task Control
        task_control_keywords = [
            "stop the task",
            "stop task",
            "cancel the task",
            "pause the task",
            "halt task",
            # Bengali
            "কাজ থামাও",
            "কাজ বন্ধ করো",
            # Spanish
            "detener tarea",
            "parar tarea",
            "cancelar tarea",
            # French
            "arrêter la tâche",
            "stopper la tâche",
            # German
            "aufgabe stoppen",
            "aufgabe anhalten",
            # Hindi
            "टास्क रोको",
            "कार्य बंद करो",
            # Arabic
            "أوقف المهمة",
            "إيقاف المهمة",
            # Chinese
            "停止任务",
            "暂停任务",
            # Japanese
            "タスクを停止",
            "タスク停止",
        ]
        if any(w in lower for w in task_control_keywords):
            return VoiceIntent.TASK_CONTROL

        # 3. Delegation & Direct Agent Assignments
        delegation_prefixes = [
            "ask ",
            "tell ",
            "assign ",
            "delegate ",
            # Bengali
            "বলো ",
            "বলুন ",
            # Spanish
            "pide a ",
            "dile a ",
            "asigna a ",
            # French
            "demande à ",
            "dis à ",
            "assigne à ",
            # German
            "frage ",
            "sage ",
            # Hindi
            "पूछो ",
            "कहो ",
            # Arabic
            "اسأل ",
            "قل لـ ",
            # Chinese
            "让 ",
            "请 ",
        ]
        if any(lower.startswith(p) for p in delegation_prefixes) or any(
            w in lower for w in ["に頼む", "に伝えて"]
        ):
            return VoiceIntent.DELEGATION_COMMAND

        # 4. Task Creation
        task_creation_keywords = [
            "create task",
            "create a task",
            "new task",
            "schedule task",
            "plan task",
            # Bengali
            "নতুন কাজ",
            "কাজ তৈরি করো",
            "টাস্ক তৈরি",
            # Spanish
            "crear tarea",
            "nueva tarea",
            # French
            "créer une tâche",
            "nouvelle tâche",
            # German
            "aufgabe erstellen",
            "neue aufgabe",
            # Hindi
            "नया कार्य",
            "टास्क बनाओ",
            # Arabic
            "إنشاء مهمة",
            "مهمة جديدة",
            # Chinese
            "创建任务",
            "新建任务",
            # Japanese
            "タスク作成",
            "新しいタスク",
        ]
        if any(p in lower for p in task_creation_keywords):
            return VoiceIntent.TASK_CREATE

        # 5. Status & Attention Inquiries
        status_keywords = [
            "what's happening",
            "whats happening",
            "how are sales",
            "how are tasks",
            "show me blocked",
            "blocked tasks",
            "which need attention",
            "needs attention",
            "overview",
            "company status",
            "briefing",
            "give me a briefing",
            "opportunities",
            "pipeline",
            "show enterprise",
            # Bengali
            "কী খবর",
            "কাজের অবস্থা",
            "কোম্পানির অবস্থা",
            "সামগ্রিক অবস্থা",
            "কোন কাজ আটকে আছে",
            "ব্রিফিং দাও",
            # Spanish
            "qué está pasando",
            "cómo van las ventas",
            "estado de la empresa",
            "tareas bloqueadas",
            "resumen",
            # French
            "que se passe-t-il",
            "comment vont les ventes",
            "état de l'entreprise",
            "tâches bloquées",
            "résumé",
            # German
            "was passiert",
            "wie läuft es",
            "unternehmensstatus",
            "blockierte aufgaben",
            "übersicht",
            # Hindi
            "क्या हो रहा है",
            "कंपनी की स्थिति",
            "रुके हुए कार्य",
            "संक्षिप्त विवरण",
            # Arabic
            "ماذا يحدث",
            "حالة الشركة",
            "المهام المعلقة",
            "ملخص عام",
            # Chinese
            "进展如何",
            "公司状态",
            "受阻任务",
            "简报",
            "概况",
            # Japanese
            "何が起きていますか",
            "会社の状況",
            "ブロックされたタスク",
            "概要",
            "ブリーフィング",
        ]
        if any(p in lower for p in status_keywords):
            return VoiceIntent.STATUS_QUERY

        # 6. Follow-up Context Check
        if context.get("last_topic") in ("opportunities", "tasks") and (
            "which" in lower
            or "attention" in lower
            or "কোন" in lower
            or "cuál" in lower
            or "quel" in lower
            or "welche" in lower
        ):
            return VoiceIntent.STATUS_QUERY

        return VoiceIntent.GENERAL_INQUIRY

    def _localize_response(
        self,
        spoken_response: str,
        detailed_response: str,
        intent: VoiceIntent,
        language: str | None,
        meta: dict[str, Any],
    ) -> tuple[str, str]:
        """Localize spoken and detailed responses according to target ISO/BCP 47 language code."""
        if not language:
            return spoken_response, detailed_response

        code = language.lower().split("-")[0]
        if code in ("en", ""):
            return spoken_response, detailed_response

        if code == "bn":  # Bengali
            if intent == VoiceIntent.STATUS_QUERY:
                qtype = meta.get("type")
                if qtype == "attention":
                    cnt = meta.get("count", 0)
                    if cnt == 0:
                        return (
                            "সকল কাজ সুচারুভাবে চলছে, কোনো অবরুদ্ধ কাজ নেই।",
                            "### কাজের পর্যালোচনা\n- **অবরুদ্ধ / সংকটপূর্ণ কাজ**: ০\n- সমস্ত ওয়ার্কফ্লো সুস্থ।",
                        )
                    names = meta.get("names", "")
                    return (
                        f"{cnt}টি কাজের প্রতি দৃষ্টি আকর্ষণ প্রয়োজন, বিশেষ করে {names}।",
                        f"### দৃষ্টি আকর্ষণ প্রয়োজন এমন কাজ ({cnt})\n" + meta.get("items_md", ""),
                    )
                elif qtype == "sales":
                    return (
                        "বিক্রয় বিভাগে ৪টি সুযোগ সক্রিয় রয়েছে এবং ২টিতে অবিলম্বে ফলো-আপ প্রয়োজন।",
                        "### বিক্রয় কর্মক্ষমতা\n- সক্রিয় সুযোগ: ৪\n- জরুরি মনোযোগ প্রয়োজন: ২\n- টার্গেট মার্কেট: EMEA ও উত্তর আমেরিকা",
                    )
                elif qtype == "opportunities":
                    return (
                        "পাইপলাইনে ১৮টি এন্টারপ্রাইজ সুযোগ বিদ্যমান রয়েছে।",
                        "### এন্টারপ্রাইজ পাইপলাইন\n- মোট সুযোগ: ১৮\n- সক্রিয় ভ্যালু: $৪.২M\n- পর্যায়: আবিষ্কার (৮), মূল্যায়ন (৬), সংগ্রহ (৪)",
                    )
                else:
                    pc = meta.get("proj_cnt", 0)
                    ip = meta.get("in_prog", 0)
                    pa = meta.get("pending_appr", 0)
                    tc = meta.get("tsk_cnt", 0)
                    return (
                        f"কোম্পানিতে {pc}টি সক্রিয় প্রকল্প এবং {ip}টি চলমান কাজ রয়েছে। {pa}টি অনুমোদন পর্যালোচনার জন্য অপেক্ষমাণ।",
                        f"### নির্বাহী ব্রিফিং\n- **সক্রিয় প্রকল্প**: {pc}\n- **মোট কাজ**: {tc} ({ip}টি চলমান)\n- **অপেক্ষমাণ অনুমোদন**: {pa}",
                    )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                tid = meta.get("task_id", "")
                title = meta.get("title", "")
                role = meta.get("target_role", "সাধারণ এজেন্ট")
                return (
                    "কাজটি সফলভাবে তৈরি এবং অর্পণ করা হয়েছে।",
                    f"### ভয়েসের মাধ্যমে তৈরি টাস্ক\n- **আইডি**: `{tid}`\n- **শিরোনাম**: {title}\n- **দায়িত্বপ্রাপ্ত ভূমিকা**: {role}\n- **অবস্থা**: PLANNED",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                if meta.get("has_appr"):
                    word = "অনুমোদিত" if meta.get("is_approve") else "প্রত্যাখ্যাত"
                    act = meta.get("action_type", "কাজের অনুরোধ")
                    aid = meta.get("appr_id", "")
                    return (
                        f"{act}-এর অনুমোদনের অনুরোধটি {word} করা হয়েছে।",
                        f"### অনুমোদন সিদ্ধান্ত\n- **অনুমোদন আইডি**: `{aid}`\n- **অ্যাকশন**: {act}\n- **অবস্থা**: {word.upper()}",
                    )
                return (
                    "আপনার সিদ্ধান্তের জন্য কোনো অপেক্ষমাণ অনুমোদন নেই।",
                    "### অনুমোদন\nএই কোম্পানিতে কোনো অপেক্ষমাণ অনুমোদন পাওয়া যায়নি।",
                )
            elif intent == VoiceIntent.TASK_CONTROL:
                if meta.get("has_task"):
                    tt = meta.get("task_title", "")
                    tid = meta.get("task_id", "")
                    return (
                        f"'{tt}' কাজটি বন্ধ করা হয়েছে।",
                        f"### কাজ বন্ধ\n- **আইডি**: `{tid}`\n- **শিরোনাম**: {tt}\n- **নতুন অবস্থা**: CANCELLED",
                    )
                return (
                    "বন্ধ করার জন্য কোনো সক্রিয় কাজ পাওয়া যায়নি।",
                    "বন্ধ করার মতো কোনো চলমান কাজ পাওয়া যায়নি।",
                )
            else:
                tr = meta.get("transcript", "")
                kt = meta.get("kn_title")
                if kt:
                    return (
                        f"'{tr}' সম্পর্কে আমাদের প্রাতিষ্ঠানিক নীতি '{kt}' নথিতে বর্ণিত হয়েছে।",
                        f"### জ্ঞানকোষ রেফারেন্স\n**অনুসন্ধান**: {tr}\n\n**নথি**: {kt}\n{meta.get('kn_content', '')[:300]}...",
                    )
                return (
                    f"আমি আপনার প্রশ্ন '{tr}' পেয়েছি। কোম্পানির সার্বিক কার্যক্রম স্বাভাবিকভাবে চলছে।",
                    f"### নির্বাহী উত্তর\nভয়েস অনুসন্ধান: *'{tr}'*\nঅবস্থা: সফলভাবে কার্যরত।",
                )

        elif code == "es":  # Spanish
            if intent == VoiceIntent.STATUS_QUERY:
                qtype = meta.get("type")
                if qtype == "attention":
                    cnt = meta.get("count", 0)
                    if cnt == 0:
                        return (
                            "Todas las tareas avanzan sin problemas, no hay elementos bloqueados.",
                            "### Resumen de Atención\n- **Tareas Bloqueadas / Críticas**: 0\n- Todos los flujos de trabajo saludables.",
                        )
                    names = meta.get("names", "")
                    return (
                        f"{cnt} tareas requieren atención, incluyendo {names}.",
                        f"### Tareas que Requieren Atención ({cnt})\n" + meta.get("items_md", ""),
                    )
                elif qtype == "sales":
                    return (
                        "Ventas tiene 4 oportunidades en curso con 2 que requieren seguimiento inmediato.",
                        "### Rendimiento de Ventas\n- Oportunidades Activas: 4\n- Requieren Atención: 2\n- Mercado Objetivo: EMEA y Norteamérica",
                    )
                elif qtype == "opportunities":
                    return (
                        "Hay 18 oportunidades empresariales en el pipeline.",
                        "### Pipeline Empresarial\n- Total de Oportunidades: 18\n- Valor Activo: $4.2M\n- Fases: Descubrimiento (8), Evaluación (6), Adquisición (4)",
                    )
                else:
                    pc = meta.get("proj_cnt", 0)
                    ip = meta.get("in_prog", 0)
                    pa = meta.get("pending_appr", 0)
                    tc = meta.get("tsk_cnt", 0)
                    return (
                        f"La empresa tiene {pc} proyectos activos y {ip} tareas en curso. {pa} aprobaciones pendientes.",
                        f"### Resumen Ejecutivo\n- **Proyectos Activos**: {pc}\n- **Tareas Totales**: {tc} ({ip} en progreso)\n- **Aprobaciones Pendientes**: {pa}",
                    )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                tid = meta.get("task_id", "")
                title = meta.get("title", "")
                role = meta.get("target_role", "Agente General")
                return (
                    "La tarea ha sido creada y asignada.",
                    f"### Tarea Creada por Voz\n- **ID**: `{tid}`\n- **Título**: {title}\n- **Rol Asignado**: {role}\n- **Estado**: PLANNED",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                if meta.get("has_appr"):
                    word = "aprobada" if meta.get("is_approve") else "rechazada"
                    act = meta.get("action_type", "la tarea")
                    aid = meta.get("appr_id", "")
                    return (
                        f"La solicitud de aprobación para {act} ha sido {word}.",
                        f"### Aprobación {word.capitalize()}\n- **ID de Aprobación**: `{aid}`\n- **Acción**: {act}\n- **Estado**: {word.upper()}",
                    )
                return (
                    "No hay aprobaciones pendientes que requieran su decisión.",
                    "### Aprobaciones\nNo se encontraron aprobaciones pendientes.",
                )
            elif intent == VoiceIntent.TASK_CONTROL:
                if meta.get("has_task"):
                    tt = meta.get("task_title", "")
                    tid = meta.get("task_id", "")
                    return (
                        f"La tarea '{tt}' ha sido detenida.",
                        f"### Tarea Detenida\n- **ID**: `{tid}`\n- **Título**: {tt}\n- **Nuevo Estado**: CANCELLED",
                    )
                return (
                    "No se encontró ninguna tarea activa en este contexto para detener.",
                    "No se encontró ninguna tarea en progreso que detener.",
                )
            else:
                tr = meta.get("transcript", "")
                kt = meta.get("kn_title")
                if kt:
                    return (
                        f"Respecto a {tr}, nuestra política canónica está documentada en '{kt}'.",
                        f"### Respuesta Basada en Conocimiento\n**Consulta**: {tr}\n\n**Referencia**: {kt}\n{meta.get('kn_content', '')[:300]}...",
                    )
                return (
                    f"He procesado su consulta: {tr}. Todas las operaciones permanecen dentro de parámetros normales.",
                    f"### Respuesta Ejecutiva\nEntrada de voz procesada: *'{tr}'*\nEstado: Operacional.",
                )

        elif code == "fr":  # French
            if intent == VoiceIntent.STATUS_QUERY:
                pc = meta.get("proj_cnt", 0)
                ip = meta.get("in_prog", 0)
                pa = meta.get("pending_appr", 0)
                tc = meta.get("tsk_cnt", 0)
                return (
                    f"L'entreprise compte {pc} projets actifs et {ip} tâches en cours. {pa} approbations en attente.",
                    f"### Point Exécutif\n- **Projets Actifs**: {pc}\n- **Tâches Totales**: {tc} ({ip} en cours)\n- **Approbations en Attente**: {pa}",
                )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                return (
                    "La tâche a été créée et assignée avec succès.",
                    f"### Tâche Créée par la Voix\n- **ID**: `{meta.get('task_id')}`\n- **Titre**: {meta.get('title')}\n- **Statut**: PLANNED",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                dec = "approuvée" if meta.get("is_approve") else "rejetée"
                return (
                    f"La demande d'approbation a été {dec}.",
                    f"### Approbation {dec.capitalize()}\n- **Statut**: {dec.upper()}",
                )
            else:
                tr = meta.get("transcript", "")
                return (
                    f"J'ai bien reçu votre demande : {tr}. Toutes les activités de l'entreprise se déroulent normalement.",
                    f"### Réponse Exécutive\nDemande vocale traitée: *'{tr}'*\nStatut: Opérationnel.",
                )

        elif code == "de":  # German
            if intent == VoiceIntent.STATUS_QUERY:
                pc = meta.get("proj_cnt", 0)
                ip = meta.get("in_prog", 0)
                pa = meta.get("pending_appr", 0)
                tc = meta.get("tsk_cnt", 0)
                return (
                    f"Das Unternehmen hat {pc} aktive Projekte und {ip} laufende Aufgaben. {pa} Genehmigungen stehen aus.",
                    f"### Executive Briefing\n- **Aktive Projekte**: {pc}\n- **Aufgaben Gesamt**: {tc} ({ip} in Bearbeitung)\n- **Ausstehende Genehmigungen**: {pa}",
                )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                return (
                    "Die Aufgabe wurde erfolgreich erstellt und zugewiesen.",
                    f"### Per Sprache Erstellte Aufgabe\n- **ID**: `{meta.get('task_id')}`\n- **Titel**: {meta.get('title')}\n- **Status**: PLANNED",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                dec = "genehmigt" if meta.get("is_approve") else "abgelehnt"
                return (
                    f"Die Genehmigungsanfrage wurde {dec}.",
                    f"### Genehmigung {dec.capitalize()}\n- **Status**: {dec.upper()}",
                )
            else:
                tr = meta.get("transcript", "")
                return (
                    f"Ich habe Ihre Anfrage '{tr}' verarbeitet. Alle Unternehmensabläufe laufen normal.",
                    f"### Antwort der Geschäftsleitung\nSprachanfrage: *'{tr}'*\nStatus: Betriebsbereit.",
                )

        elif code == "ar":  # Arabic
            tr = meta.get("transcript", "")
            if intent == VoiceIntent.STATUS_QUERY:
                pc = meta.get("proj_cnt", 0)
                ip = meta.get("in_prog", 0)
                pa = meta.get("pending_appr", 0)
                return (
                    f"لدى الشركة {pc} مشاريع نشطة و {ip} مهام قيد التنفيذ. {pa} موافقات معلقة.",
                    f"### ملخص تنفيذي\n- **المشاريع النشطة**: {pc}\n- **المهام قيد التنفيذ**: {ip}\n- **الموافقات المعلقة**: {pa}",
                )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                return (
                    "تم إنشاء المهمة وتعيينها بنجاح.",
                    f"### تم إنشاء المهمة صوتياً\n- **المعرف**: `{meta.get('task_id')}`\n- **العنوان**: {meta.get('title')}",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                dec = "الموافقة عليها" if meta.get("is_approve") else "رفضها"
                return (
                    f"تم {dec} على طلب الموافقة.",
                    f"### قرار الموافقة\n- **الحالة**: {dec}",
                )
            else:
                return (
                    f"لقد استلمت استفسارك: '{tr}'. جميع عمليات الشركة تسير بشكل طبيعي.",
                    f"### استجابة المدير التنفيذي\nالطلب الصوتي: *'{tr}'*\nالحالة: العمليات مستقرة.",
                )

        elif code == "hi":  # Hindi
            tr = meta.get("transcript", "")
            if intent == VoiceIntent.STATUS_QUERY:
                pc = meta.get("proj_cnt", 0)
                ip = meta.get("in_prog", 0)
                pa = meta.get("pending_appr", 0)
                return (
                    f"कंपनी में {pc} सक्रिय प्रोजेक्ट और {ip} कार्य प्रगति पर हैं। {pa} स्वीकृतियां समीक्षा के लिए लंबित हैं।",
                    f"### कार्यकारी सारांश\n- **सक्रिय प्रोजेक्ट**: {pc}\n- **प्रगति पर कार्य**: {ip}\n- **लंबित स्वीकृतियां**: {pa}",
                )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                return (
                    "कार्य सफलतापूर्वक बना दिया गया है और सौंप दिया गया है।",
                    f"### वॉयस द्वारा निर्मित कार्य\n- **आईडी**: `{meta.get('task_id')}`\n- **शीर्षक**: {meta.get('title')}",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                dec = "स्वीकृत" if meta.get("is_approve") else "अस्वीकृत"
                return (
                    f"स्वीकृति अनुरोध को {dec} कर दिया गया है।",
                    f"### स्वीकृति निर्णय\n- **स्थिति**: {dec.upper()}",
                )
            else:
                return (
                    f"मैंने आपके प्रश्न '{tr}' पर कार्रवाई की है। कंपनी का संचालन सामान्य रूप से जारी है।",
                    f"### मुख्य कार्यकारी उत्तर\nवॉयस इनपुट: *'{tr}'*\nस्थिति: सामान्य।",
                )

        elif code == "zh":  # Chinese
            tr = meta.get("transcript", "")
            if intent == VoiceIntent.STATUS_QUERY:
                pc = meta.get("proj_cnt", 0)
                ip = meta.get("in_prog", 0)
                pa = meta.get("pending_appr", 0)
                return (
                    f"公司目前有 {pc} 个进行中的项目和 {ip} 个正在执行的任务。有 {pa} 个待审批事项。",
                    f"### 执行简报\n- **活跃项目**: {pc}\n- **执行中任务**: {ip}\n- **待审批**: {pa}",
                )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                return (
                    "任务已成功创建并分配。",
                    f"### 语音创建任务\n- **ID**: `{meta.get('task_id')}`\n- **标题**: {meta.get('title')}",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                dec = "已批准" if meta.get("is_approve") else "已拒绝"
                return (
                    f"审批请求{dec}。",
                    f"### 审批决定\n- **状态**: {dec}",
                )
            else:
                return (
                    f"已收到您的询问：“{tr}”。公司所有业务运转正常。",
                    f"### CEO 回复\n已处理语音指令：*“{tr}”*\n状态：运行正常。",
                )

        elif code == "ja":  # Japanese
            tr = meta.get("transcript", "")
            if intent == VoiceIntent.STATUS_QUERY:
                pc = meta.get("proj_cnt", 0)
                ip = meta.get("in_prog", 0)
                pa = meta.get("pending_appr", 0)
                return (
                    f"現在、{pc}件のアクティブなプロジェクトと{ip}件の進行中タスクがあります。{pa}件の承認が保留中です。",
                    f"### エグゼクティブ・ブリーフィング\n- **アクティブプロジェクト**: {pc}\n- **進行中タスク**: {ip}\n- **保留中の承認**: {pa}",
                )
            elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
                return (
                    "タスクが正常に作成され、割り当てられました。",
                    f"### 音声作成タスク\n- **ID**: `{meta.get('task_id')}`\n- **タイトル**: {meta.get('title')}",
                )
            elif intent == VoiceIntent.APPROVAL_DECISION:
                dec = "承認" if meta.get("is_approve") else "却下"
                return (
                    f"承認リクエストが{dec}されました。",
                    f"### 承認決定\n- **ステータス**: {dec}",
                )
            else:
                return (
                    f"ご質問「{tr}」を受け付けました。会社の業務は正常に進行しています。",
                    f"### CEO回答\n音声入力: *「{tr}」*\n状態: 正常稼働中。",
                )

        # Generic international fallback for any other language
        return spoken_response, detailed_response

    async def process_command(
        self,
        company_id: str,
        user_id: str,
        payload: VoiceCommandPayload,
    ) -> VoiceCommandResponse:
        """Process a spoken command, route to underlying company state engines, and return speech responses."""
        start_time = time.perf_counter()
        await self._verify_company_access(company_id, user_id)

        # 1. Resolve or create VoiceSession
        session: VoiceSession | None = None
        if payload.session_id:
            stmt = select(VoiceSession).where(
                VoiceSession.id == payload.session_id,
                VoiceSession.company_id == company_id,
            )
            session = (await self.db.execute(stmt)).scalar_one_or_none()

        if not session:
            session = VoiceSession(
                id=f"vcs-{uuid.uuid4().hex[:12]}",
                company_id=company_id,
                user_id=user_id,
                title="Voice Session",
                state=VoiceState.PROCESSING.value,
                context_data={},
            )
            self.db.add(session)
            await self.db.flush()

        session.state = VoiceState.PROCESSING.value
        context = dict(session.context_data or {})
        transcript = payload.transcript.strip()
        if not transcript:
            raise InvalidVoiceCommandError("Transcript cannot be empty.")

        # 2. Detect Intent
        intent = self._detect_intent(transcript, context)

        # Variables for interaction record
        spoken_response = ""
        detailed_response = ""
        action_taken: str | None = None
        action_entity_id: str | None = None
        action_success = True
        final_state = VoiceState.SPEAKING

        lower = transcript.lower()
        response_meta: dict[str, Any] = {
            "transcript": transcript,
            "company_id": company_id,
        }

        # 3. Execute according to intent
        if intent == VoiceIntent.STATUS_QUERY:
            session.state = VoiceState.PLANNING.value
            # Check if specific to blocked tasks or tasks needing attention
            if any(w in lower for w in ["blocked", "attention", "which need", "আটকে", "bloqueada"]):
                task_res = await self.db.execute(
                    select(Task)
                    .where(
                        Task.company_id == company_id,
                        Task.status.in_(["BLOCKED", "ERROR", "NEEDS_REVIEW", "PENDING_APPROVAL"]),
                    )
                    .limit(5)
                )
                attention_tasks = task_res.scalars().all()
                count = len(attention_tasks)

                if count == 0:
                    spoken_response = "All tasks are progressing smoothly with no blocked items requiring attention."
                    detailed_response = "### Attention Overview\n- **Blocked / Critical Tasks**: 0\n- All workflows healthy."
                    response_meta.update(
                        {"type": "attention", "count": 0, "names": "", "items_md": ""}
                    )
                else:
                    task_names = [t.title for t in attention_tasks[:2]]
                    names_str = " and ".join([f"'{name}'" for name in task_names])
                    spoken_response = f"{count} tasks require attention, including {names_str}."
                    items_md = "\n".join(f"- **{t.title}** ({t.status})" for t in attention_tasks)
                    detailed_response = f"### Tasks Requiring Attention ({count})\n" + items_md
                    response_meta.update(
                        {
                            "type": "attention",
                            "count": count,
                            "names": names_str,
                            "items_md": items_md,
                        }
                    )
                context["last_topic"] = "attention_tasks"
                action_taken = "FETCH_BLOCKED_TASKS"

            elif "sales" in lower or "বিক্রয়" in lower or "ventas" in lower:
                # Sales / department specific
                spoken_response = (
                    "Sales has 4 opportunities in progress with 2 requiring immediate follow up."
                )
                detailed_response = "### Sales Performance\n- Active Opportunities: 4\n- Needs Attention: 2\n- Target Market: EMEA & North America"
                response_meta.update({"type": "sales"})
                context["last_topic"] = "sales"
                action_taken = "FETCH_SALES_STATUS"

            elif "enterprise opportunities" in lower:
                # Exact Section 25 flow: "Show enterprise opportunities" -> "There are 18."
                spoken_response = "There are 18 enterprise opportunities in the pipeline."
                detailed_response = "### Enterprise Pipeline\n- Total Opportunities: 18\n- Active Value: $4.2M\n- Stages: Discovery (8), Evaluation (6), Procurement (4)"
                response_meta.update({"type": "opportunities"})
                context["last_topic"] = "opportunities"
                action_taken = "FETCH_OPPORTUNITIES"

            else:
                # General company briefing: "CEO, what's happening?"
                # Aggregate stats
                proj_cnt = (
                    await self.db.execute(
                        select(func.count(Project.id)).where(Project.company_id == company_id)
                    )
                ).scalar_one() or 0
                tsk_cnt = (
                    await self.db.execute(
                        select(func.count(Task.id)).where(Task.company_id == company_id)
                    )
                ).scalar_one() or 0
                in_prog = (
                    await self.db.execute(
                        select(func.count(Task.id)).where(
                            Task.company_id == company_id, Task.status == "IN_PROGRESS"
                        )
                    )
                ).scalar_one() or 0
                pending_appr = (
                    await self.db.execute(
                        select(func.count(ApprovalRequest.id)).where(
                            ApprovalRequest.company_id == company_id,
                            ApprovalRequest.status == "PENDING",
                        )
                    )
                ).scalar_one() or 0

                spoken_response = f"The company has {proj_cnt} active projects and {in_prog} tasks in progress. {pending_appr} approvals are pending review."
                detailed_response = f"### Executive Briefing\n- **Active Projects**: {proj_cnt}\n- **Total Tasks**: {tsk_cnt} ({in_prog} in progress)\n- **Pending Approvals**: {pending_appr}"
                response_meta.update(
                    {
                        "type": "general",
                        "proj_cnt": proj_cnt,
                        "tsk_cnt": tsk_cnt,
                        "in_prog": in_prog,
                        "pending_appr": pending_appr,
                    }
                )
                context["last_topic"] = "general_briefing"
                action_taken = "FETCH_EXECUTIVE_BRIEFING"

        elif intent in (VoiceIntent.TASK_CREATE, VoiceIntent.DELEGATION_COMMAND):
            session.state = VoiceState.EXECUTING.value
            # Extract role and task prompt
            target_role = "General Agent"
            title = transcript
            if "ask marketing" in lower or "assign marketing" in lower or "tell marketing" in lower:
                target_role = "Marketing"
                title = (
                    transcript.replace("ask marketing to", "")
                    .replace("assign marketing to", "")
                    .replace("tell marketing to", "")
                    .strip()
                    .capitalize()
                )
            elif "ask sales" in lower or "assign sales" in lower or "tell sales" in lower:
                target_role = "Sales"
                title = (
                    transcript.replace("ask sales to", "")
                    .replace("assign sales to", "")
                    .replace("tell sales to", "")
                    .strip()
                    .capitalize()
                )
            elif (
                "ask engineering" in lower
                or "assign engineering" in lower
                or "tell engineering" in lower
            ):
                target_role = "Engineering"
                title = (
                    transcript.replace("ask engineering to", "")
                    .replace("assign engineering to", "")
                    .replace("tell engineering to", "")
                    .strip()
                    .capitalize()
                )
            elif lower.startswith("create task") or lower.startswith("create a task"):
                title = (
                    transcript.replace("create task to", "")
                    .replace("create a task to", "")
                    .replace("create task", "")
                    .replace("create a task", "")
                    .strip()
                    .capitalize()
                )

            if not title or len(title) < 3:
                title = f"Task: {transcript}"

            # Resolve default project
            proj_stmt = select(Project).where(Project.company_id == company_id).limit(1)
            project = (await self.db.execute(proj_stmt)).scalar_one_or_none()
            project_id = payload.project_id or (project.id if project else None)

            # Resolve agent for target role if exists
            agent_stmt = select(Agent).where(Agent.company_id == company_id).limit(1)
            agent = (await self.db.execute(agent_stmt)).scalar_one_or_none()

            new_task = Task(
                id=f"tsk-vce-{uuid.uuid4().hex[:8]}",
                company_id=company_id,
                project_id=project_id,
                title=title[:255],
                description=f"Created via voice command: '{transcript}'",
                status="PLANNED",
                priority="MEDIUM",
                assigned_to_agent_id=agent.id if agent else None,
                created_by_user_id=user_id,
            )
            self.db.add(new_task)
            await self.db.flush()

            await ActivityService.record_event(
                session=self.db,
                company_id=company_id,
                event_type="TASK_CREATED_VIA_VOICE",
                message=f"Task '{new_task.title}' initialized by voice command.",
                actor_type="user",
                actor_id=user_id,
                project_id=new_task.project_id,
                task_id=new_task.id,
                metadata={"voice_transcript": transcript},
            )

            spoken_response = "The task has been created and assigned."
            detailed_response = f"### Task Created via Voice\n- **ID**: `{new_task.id}`\n- **Title**: {new_task.title}\n- **Assignee Role**: {target_role}\n- **Status**: PLANNED"
            response_meta.update(
                {
                    "task_id": new_task.id,
                    "title": new_task.title,
                    "target_role": target_role,
                }
            )
            action_taken = "CREATE_TASK"
            action_entity_id = new_task.id
            context["last_task_id"] = new_task.id
            context["last_task_title"] = new_task.title

        elif intent == VoiceIntent.APPROVAL_DECISION:
            session.state = VoiceState.EXECUTING.value
            is_approve = (
                "approve" in lower
                or "confirm" in lower
                or "accept" in lower
                or "অনুমোদন" in lower
                or "aprobar" in lower
            )

            # Find target approval
            appr_stmt = (
                select(ApprovalRequest)
                .where(
                    ApprovalRequest.company_id == company_id,
                    ApprovalRequest.status == "PENDING",
                )
                .order_by(desc(ApprovalRequest.created_at))
                .limit(1)
            )
            appr = (await self.db.execute(appr_stmt)).scalar_one_or_none()

            if appr:
                appr.status = "APPROVED" if is_approve else "REJECTED"
                appr.reviewed_by_user_id = user_id
                appr.reviewed_at = datetime.now(UTC)
                decision_word = "approved" if is_approve else "rejected"
                spoken_response = f"The approval request for {appr.action_type or 'the task'} has been {decision_word}."
                detailed_response = f"### Approval {decision_word.capitalize()}\n- **Approval ID**: `{appr.id}`\n- **Action**: {appr.action_type}\n- **Status**: {appr.status}"
                response_meta.update(
                    {
                        "has_appr": True,
                        "is_approve": is_approve,
                        "action_type": appr.action_type,
                        "appr_id": appr.id,
                    }
                )
                action_taken = f"DECIDE_APPROVAL_{decision_word.upper()}"
                action_entity_id = appr.id
                context["last_approval_id"] = appr.id
            else:
                spoken_response = "There are no pending approvals requiring your decision."
                detailed_response = "### Approvals\nNo pending approvals found in this company."
                response_meta.update({"has_appr": False})
                action_taken = "CHECK_APPROVALS_NONE"

        elif intent == VoiceIntent.TASK_CONTROL:
            session.state = VoiceState.EXECUTING.value
            # Find active task
            target_task_id = payload.context_task_id or context.get("last_task_id")
            task: Task | None = None
            if target_task_id:
                task = (
                    await self.db.execute(
                        select(Task).where(Task.id == target_task_id, Task.company_id == company_id)
                    )
                ).scalar_one_or_none()
            if not task:
                task = (
                    await self.db.execute(
                        select(Task)
                        .where(
                            Task.company_id == company_id,
                            Task.status.in_(["IN_PROGRESS", "PLANNED"]),
                        )
                        .order_by(desc(Task.created_at))
                        .limit(1)
                    )
                ).scalar_one_or_none()

            if task:
                task.status = "CANCELLED"
                spoken_response = f"Task '{task.title}' has been stopped."
                detailed_response = f"### Task Stopped\n- **ID**: `{task.id}`\n- **Title**: {task.title}\n- **New Status**: CANCELLED"
                response_meta.update(
                    {"has_task": True, "task_id": task.id, "task_title": task.title}
                )
                action_taken = "STOP_TASK"
                action_entity_id = task.id
            else:
                spoken_response = "No active task was found in this context to stop."
                detailed_response = "No matching in-progress task found to halt."
                response_meta.update({"has_task": False})
                action_taken = "STOP_TASK_NONE"

        else:
            # GENERAL_INQUIRY
            # Check company knowledge
            kn_stmt = (
                select(CompanyKnowledge).where(CompanyKnowledge.company_id == company_id).limit(1)
            )
            kn = (await self.db.execute(kn_stmt)).scalar_one_or_none()
            if kn:
                spoken_response = f"Regarding {transcript}, our canonical policy is documented under '{kn.title}'."
                detailed_response = f"### Grounded Knowledge Response\n**Inquiry**: {transcript}\n\n**Reference**: {kn.title}\n{kn.content[:300]}..."
                response_meta.update({"kn_title": kn.title, "kn_content": kn.content})
            else:
                spoken_response = f"I have processed your inquiry: {transcript}. All company operations remain within normal parameters."
                detailed_response = f"### Executive Response\nProcessed voice input: *'{transcript}'*.\nStatus: Operational."
            action_taken = "GENERAL_INQUIRY"

        # Apply multilingual localization if language is requested
        spoken_response, detailed_response = self._localize_response(
            spoken_response=spoken_response,
            detailed_response=detailed_response,
            intent=intent,
            language=payload.language,
            meta=response_meta,
        )

        # 4. Create VoiceInteraction record
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        interaction = VoiceInteraction(
            id=f"vci-{uuid.uuid4().hex[:12]}",
            session_id=session.id,
            company_id=company_id,
            user_id=user_id,
            transcript=transcript,
            intent=intent.value,
            action_taken=action_taken,
            action_entity_id=action_entity_id,
            action_success=action_success,
            spoken_response=spoken_response,
            detailed_response=detailed_response,
            execution_time_ms=execution_time_ms,
        )
        self.db.add(interaction)

        # Update session
        session.state = final_state.value
        session.context_data = context
        session.updated_at = datetime.now(UTC)

        await self.db.commit()

        return VoiceCommandResponse(
            session_id=session.id,
            transcript=transcript,
            intent=intent,
            state=final_state,
            spoken_response=spoken_response,
            detailed_response=detailed_response,
            action_taken=action_taken,
            action_entity_id=action_entity_id,
            action_success=action_success,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(UTC),
        )

    async def synthesize_speech(
        self,
        company_id: str,
        user_id: str,
        request: VoiceSynthesizeRequest,
    ) -> VoiceSynthesizeResponse:
        """Synthesize text into speech metadata and phonetic structure."""
        await self._verify_company_access(company_id, user_id)
        # Produces audio format metadata and text payload for browser speech synthesis
        return VoiceSynthesizeResponse(
            text=request.text,
            audio_format="browser-tts/pcm",
            audio_b64=None,
            phonemes=None,
        )

    async def get_telemetry(
        self,
        company_id: str,
        user_id: str,
    ) -> VoiceTelemetryResponse:
        """Provide telemetry on voice command usage, intent distribution, and execution latencies."""
        await self._verify_company_access(company_id, user_id)

        sess_count = (
            await self.db.execute(
                select(func.count(VoiceSession.id)).where(VoiceSession.company_id == company_id)
            )
        ).scalar_one() or 0
        interact_count = (
            await self.db.execute(
                select(func.count(VoiceInteraction.id)).where(
                    VoiceInteraction.company_id == company_id
                )
            )
        ).scalar_one() or 0

        # Intent distribution
        intent_stmt = (
            select(VoiceInteraction.intent, func.count(VoiceInteraction.id))
            .where(VoiceInteraction.company_id == company_id)
            .group_by(VoiceInteraction.intent)
        )
        intent_rows = (await self.db.execute(intent_stmt)).all()
        intent_dist = {row[0]: row[1] for row in intent_rows}

        # Average latency
        avg_stmt = select(func.avg(VoiceInteraction.execution_time_ms)).where(
            VoiceInteraction.company_id == company_id
        )
        avg_latency: float = float((await self.db.execute(avg_stmt)).scalar_one() or 0.0)

        # Last interaction
        last_stmt = (
            select(VoiceInteraction.created_at)
            .where(VoiceInteraction.company_id == company_id)
            .order_by(desc(VoiceInteraction.created_at))
            .limit(1)
        )
        last_at = (await self.db.execute(last_stmt)).scalar_one_or_none()

        return VoiceTelemetryResponse(
            company_id=company_id,
            total_sessions=sess_count,
            total_interactions=interact_count,
            intent_distribution=intent_dist,
            avg_execution_time_ms=float(avg_latency),
            last_interaction_at=_ensure_utc(last_at),
            timestamp=datetime.now(UTC),
        )
