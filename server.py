import os
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Dodaj root u path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config import *
from anthropic import Anthropic
from groq import Groq
from google import genai as google_genai

app = FastAPI(title="CEO Idea Incubator", docs_url=None, redoc_url=None)

# Samo localhost — nikakav pristup spolja
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ─────────────────────────────────────────
# In-memory storage za aktivne sesije
# ─────────────────────────────────────────
sessions: dict = {}

def new_session(session_id: str):
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "step": "idea_input",       # trenutni korak
        "idea_raw": "",
        "idea_refined": "",
        "plan": "",
        "task_brief": "",
        "department_outputs": {},
        "ceo_decisions": [],
        "amendments": [],
        "messages": [],             # CEO chat istorija
        "progress": {               # % po agentu
            "ceo": 0,
            "brainstorm": 0,
            "planner": 0,
            "coo": 0,
            "developer": 0,
            "designer": 0,
            "marketing": 0,
            "qa": 0,
            "project_manager": 0,
            "finale": 0
        },
        "status": {                 # status po agentu
            "ceo": "active",
            "brainstorm": "waiting",
            "planner": "waiting",
            "coo": "waiting",
            "developer": "waiting",
            "designer": "waiting",
            "marketing": "waiting",
            "qa": "waiting",
            "project_manager": "waiting",
            "finale": "waiting"
        }
    }
    return sessions[session_id]

def save_session_to_disk(session_id: str):
    os.makedirs("storage", exist_ok=True)
    path = f"storage/session_{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions[session_id], f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/sessions")
async def list_sessions():
    """Lista svih sesija za dashboard"""
    result = []
    storage = Path("storage")
    if storage.exists():
        for f in sorted(storage.glob("session_*.json"), reverse=True)[:10]:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
                result.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "step": data["step"],
                    "idea": data.get("idea_raw", "")[:80]
                })
    return result

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    if session_id in sessions:
        return sessions[session_id]
    # Pokušaj učitati sa diska
    path = f"storage/session_{session_id}.json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            sessions[session_id] = data
            return data
    return {"error": "Session not found"}

@app.post("/api/session/new")
async def create_session():
    session_id = str(uuid.uuid4())[:8]
    session = new_session(session_id)
    save_session_to_disk(session_id)
    return {"session_id": session_id}

@app.post("/api/session/{session_id}/decision")
async def ceo_decision(session_id: str, body: dict):
    """CEO donosi odluku: DA / NE / IZMENI"""
    if session_id not in sessions:
        return {"error": "Session not found"}

    decision = body.get("decision", "").upper()
    note = body.get("note", "")
    step = sessions[session_id]["step"]

    sessions[session_id]["ceo_decisions"].append({
        "step": step,
        "decision": decision,
        "note": note,
        "timestamp": datetime.now().isoformat()
    })

    if note:
        sessions[session_id]["amendments"].append(note)

    save_session_to_disk(session_id)
    return {"ok": True, "step": step, "decision": decision}

# ─────────────────────────────────────────
# WEBSOCKET — CEO Chat + Agent streaming
# ─────────────────────────────────────────
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if session_id not in sessions:
        new_session(session_id)

    session = sessions[session_id]

    try:
        async def send(msg_type: str, content: str, meta: dict = {}):
            await websocket.send_json({
                "type": msg_type,
                "content": content,
                "meta": meta,
                "timestamp": datetime.now().isoformat()
            })

        async def update_progress(agent: str, pct: int, status: str = "working"):
            session["progress"][agent] = pct
            session["status"][agent] = status
            await send("progress", "", {"agent": agent, "pct": pct, "status": status})

        # ── Dobrodošlica ──
        await send("system", "🏢 **CEO INKUBATOR IDEJA**\n\nDobrodošao! Opiši svoju ideju što jasnije možeš.\nNaš tim od 3 AI-a će je odmah analizirati i dati ti konkretnu preporuku.")
        await update_progress("ceo", 10, "active")

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")
            content = data.get("content", "")

            # ── KORAK 1: CEO unosi ideju → 3 AI diskusija ───
            if session["step"] == "idea_input" and msg_type == "message":
                session["idea_raw"] = content
                session["messages"].append({"role": "user", "content": content})
                await update_progress("ceo", 40, "active")
                await update_progress("brainstorm", 10, "working")

                groq_client  = Groq(api_key=GROQ_API_KEY)
                gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
                claude_client = Anthropic()

                # ── Groq: brza perspektiva ──────────────────
                await send("agent_start", "⚡ **Groq** analizira...", {"agent": "groq"})
                groq_resp = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{
                        "role": "system",
                        "content": "Ti si brzi AI strateg u timu. Daj KRATKU perspektivu na ideju: šta je dobro, šta nedostaje, koja je glavna šansa. Max 5 rečenica. Direktno i konkretno."
                    }, {
                        "role": "user",
                        "content": f"CEO ideja: {content}"
                    }],
                    temperature=0.75, max_tokens=350
                )
                groq_view = groq_resp.choices[0].message.content
                await send("groq", groq_view, {"agent": "groq"})
                await update_progress("brainstorm", 35, "working")

                # ── Gemini: market i korisnici ──────────────
                await send("agent_start", "🔷 **Gemini** analizira tržište...", {"agent": "gemini"})
                gemini_resp = gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=f"""Ti si AI market analyst u timu. Groq je rekao: "{groq_view}"

CEO ideja: {content}

Na osnovu Groq-ove perspektive, dodaj SAMO ono što on nije rekao:
- Ko su TAČNO target korisnici i koliko ih ima?
- Ko su 2-3 direktna konkurenta?
- Koja je 1 najveća pretnja ovoj ideji?

Max 5 rečenica. Direktno."""
                )
                gemini_view = gemini_resp.text
                await send("gemini", gemini_view, {"agent": "gemini"})
                await update_progress("brainstorm", 65, "working")

                # ── Claude: sinteza + konačna preporuka ─────
                await send("agent_start", "🟣 **Claude** sintetiše i daje preporuku...", {"agent": "claude"})
                claude_resp = claude_client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=700,
                    messages=[{"role": "user", "content": f"""Ti si AI koji sintetiše tim diskusiju i daje finalnu preporuku CEO-u.

CEO IDEJA: {content}

GROQ perspektiva: {groq_view}
GEMINI analiza: {gemini_view}

Na osnovu ove diskusije, daj CEO-u:

**🎯 NAŠA PREPORUKA:**
[1-2 rečenice — da li ići dalje i zašto]

**✅ 3 GLAVNE PREDNOSTI:**
- [prednost 1]
- [prednost 2]
- [prednost 3]

**⚠️ 2 STVARI KOJE TREBA REŠITI:**
- [stvar 1]
- [stvar 2]

**🔧 PREDLOG ALATA I TIMA:**
- Dizajn: [Canva / Figma / drugo — i zašto]
- Development: [šta preporučujemo]
- Ostalo: [šta još treba]

**📋 SLEDEĆI KORAK:**
[Jedna konkretna akcija]

Budi direktan — CEO treba odluku, ne esej."""}]
                )
                synthesis = claude_resp.content[0].text

                # Sačuvaj kompresovani summary sesije
                session["brainstorm_summary"] = _compress_summary(
                    content, groq_view, gemini_view, synthesis
                )
                session["idea_refined"] = synthesis
                await send("claude", synthesis, {"agent": "claude"})
                await update_progress("brainstorm", 100, "done")
                await update_progress("ceo", 70, "active")

                session["step"] = "idea_approval"
                session["messages"].append({"role": "assistant", "content": f"[BRAINSTORM SUMMARY]\n{session['brainstorm_summary']}"})
                save_session_to_disk(session_id)

                await send("approval_request",
                    "---\n**SASTANAK 1 — ODOBRENJE IDEJE**\n\nTim je dao preporuku gore. Kako nastavljamo?",
                    {"step": "idea_approval", "options": ["DA", "NE", "IZMENI"]}
                )

            # ── KORAK 2: CEO odobrava ideju ──────────────────
            elif session["step"] == "idea_approval" and msg_type == "decision":
                decision = content.upper()
                note = data.get("note", "")

                if decision == "NE":
                    session["step"] = "idea_input"
                    await update_progress("ceo", 10, "active")
                    await update_progress("brainstorm", 0, "waiting")
                    await send("system", f"🔄 OK. Opiši ideju ponovo ili izmenjenu verziju.\n*Tvoj komentar:* {note}")

                elif decision in ("DA", "IZMENI"):
                    if note:
                        session["amendments"].append(note)
                        await send("system", f"📝 Izmena zabeležena: *{note}*")

                    await update_progress("ceo", 100, "done")
                    await update_progress("planner", 20, "working")
                    session["step"] = "planning"

                    # Koristimo SUMMARY — ne celu diskusiju, da ne trošimo context
                    context = session.get("brainstorm_summary", session["idea_refined"])
                    if note:
                        context += f"\n\nCEO IZMENE: {note}"

                    await send("agent_start", "📋 **Planner** kreira plan realizacije...", {"agent": "planner"})
                    claude_client = Anthropic()
                    plan_resp = claude_client.messages.create(
                        model=CLAUDE_MODEL,
                        max_tokens=1200,
                        messages=[{"role": "user", "content": f"""Kreiraj koncizan PROJECT PLAN za:

{context}

**📅 TIMELINE** (8 nedelja)
- Nedelja 1-2: [šta]
- Nedelja 3-4: [šta]
- Nedelja 5-6: [šta]
- Nedelja 7-8: [šta]

**🎯 TOP 5 MILESTONES**
[milestone: datum]

**👥 TIM** (ko treba)

**💰 BUDGET** (okvirni breakdown)

**⚠️ TOP 3 RIZIKA + rešenja**

Budi koncizan — max 400 reči."""}]
                    )
                    plan = plan_resp.content[0].text
                    session["plan"] = plan
                    session["plan_summary"] = plan[:600]  # kompresovano za dalji context
                    await send("claude", plan, {"agent": "claude"})
                    await update_progress("planner", 100, "done")

                    session["step"] = "plan_approval"
                    save_session_to_disk(session_id)
                    await send("approval_request",
                        "---\n**SASTANAK 2 — ODOBRENJE PLANA**\n\nPreglej plan. Idemo li sa realizacijom?",
                        {"step": "plan_approval", "options": ["DA", "NE", "IZMENI"]}
                    )

            # ── KORAK 3: CEO odobrava plan ───────────────────
            elif session["step"] == "plan_approval" and msg_type == "decision":
                decision = content.upper()
                note = data.get("note", "")

                if decision == "NE":
                    session["step"] = "idea_approval"
                    await send("system", f"🔄 Revizija plana. Komentar: *{note}*\nPošalji DA kada si spreman da krenem sa novim planom.")

                elif decision in ("DA", "IZMENI"):
                    if note:
                        session["amendments"].append(note)

                    await update_progress("coo", 20, "working")
                    session["step"] = "execution"
                    await send("agent_start", "⚙️ **COO** delegira zadatke timu...", {"agent": "coo"})
                    await _run_execution(websocket, session, send, update_progress)
                save_session_to_disk(session_id)

            # ── Catch-all ────────────────────────────────────
            elif msg_type == "ping":
                await send("pong", "")

    except WebSocketDisconnect:
        save_session_to_disk(session_id)


def _compress_summary(idea: str, groq: str, gemini: str, claude: str) -> str:
    """
    Kompresuje brainstorm diskusiju u jedan kratak summary.
    Koristi se kao context za sve naredne agente — sprečava lutanje i bag sesije.
    """
    return f"""=== PROJEKAT SUMMARY ===
IDEJA: {idea[:200]}

TIM DISKUSIJA:
• Groq: {groq[:200]}
• Gemini: {gemini[:200]}
• Claude preporuka: {claude[:300]}

ODOBRENO: DA
========================"""


async def _run_execution(websocket, session, send, update_progress):
    """Pokretanje celog execution tima — koristi summary da ne trosi context"""
    claude_client = Anthropic()

    # Uvek koristimo kompresovani summary — ne celu diskusiju
    context = session.get("brainstorm_summary", session.get("idea_refined", ""))
    plan_ctx = session.get("plan_summary", session.get("plan", ""))[:500]
    amendments = ("\nCEO izmene: " + "; ".join(session["amendments"])) if session["amendments"] else ""

    # COO brief
    coo_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=800,
        messages=[{"role": "user", "content": f"Ti si COO. Napravi KRATAK task brief za timove.\n\nPROJEKAT:\n{context}\n\nPLAN:\n{plan_ctx}{amendments}\n\nBrief za: Dev, Design, Marketing, QA. Max 300 reči."}]
    )
    task_brief = coo_resp.content[0].text
    session["task_brief"] = task_brief
    await send("coo", task_brief, {"agent": "coo"})
    await update_progress("coo", 100, "done")

    # Developer
    await update_progress("developer", 20, "working")
    await send("agent_start", "🏗️ **Developer** kreira arhitekturu...", {"agent": "developer"})
    dev_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=900,
        messages=[{"role": "user", "content": f"Ti si Senior Developer. Na osnovu:\n{context}\n\nNapravi tehničku arhitekturu: tech stack, folder struktura, ključni moduli, API endpoints, baza. Max 300 reči."}]
    )
    session["department_outputs"]["development"] = dev_resp.content[0].text
    await send("developer", dev_resp.content[0].text, {"agent": "developer"})
    await update_progress("developer", 100, "done")

    # Designer
    await update_progress("designer", 20, "working")
    await send("agent_start", "🎨 **Designer** kreira design sistem...", {"agent": "designer"})
    design_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=700,
        messages=[{"role": "user", "content": f"Ti si UI/UX Designer. Na osnovu:\n{context}\n\nNapravi design sistem: color palette (hex kodovi), tipografija, 3 ključna ekrana, preporučeni alati (Canva/Figma/etc i zašto). Max 250 reči."}]
    )
    session["department_outputs"]["design"] = design_resp.content[0].text
    await send("designer", design_resp.content[0].text, {"agent": "designer"})
    await update_progress("designer", 100, "done")

    # Marketing
    await update_progress("marketing", 20, "working")
    await send("agent_start", "📢 **Marketing** kreira GTM strategiju...", {"agent": "marketing"})
    mkt_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=700,
        messages=[{"role": "user", "content": f"Ti si Marketing Direktor. Na osnovu:\n{context}\n\nNapravi GTM: glavna poruka, top 3 kanala, launch plan (3 faze), KPIs. Max 250 reči."}]
    )
    session["department_outputs"]["marketing"] = mkt_resp.content[0].text
    await send("marketing", mkt_resp.content[0].text, {"agent": "marketing"})
    await update_progress("marketing", 100, "done")

    # QA
    await update_progress("qa", 20, "working")
    await send("agent_start", "✅ **QA** kreira test strategiju...", {"agent": "qa"})
    qa_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=600,
        messages=[{"role": "user", "content": f"Ti si QA Lead. Na osnovu:\n{context}\n\nNapravi: top 5 test scenarija, acceptance criteria, šta mora proći pre launcha. Max 200 reči."}]
    )
    session["department_outputs"]["qa"] = qa_resp.content[0].text
    await send("qa", qa_resp.content[0].text, {"agent": "qa"})
    await update_progress("qa", 100, "done")

    # Project Manager — mid-review (koristi samo kratke excerpts)
    await update_progress("project_manager", 30, "working")
    await send("agent_start", "📊 **Project Manager** priprema mid-review za CEO...", {"agent": "project_manager"})
    pm_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=700,
        messages=[{"role": "user", "content": f"""Ti si Project Manager. Napravi KRATAK mid-review za CEO.

PROJEKAT: {context[:300]}

Tim je završio:
• Dev: {session['department_outputs']['development'][:200]}
• Design: {session['department_outputs']['design'][:150]}
• Marketing: {session['department_outputs']['marketing'][:150]}
• QA: {session['department_outputs']['qa'][:150]}

Format (max 250 reči):
**📊 STATUS:** [On Track / At Risk]
**Završenost:** [X%]
**✅ Top 3 urađene stvari:**
**⚠️ Top 2 rizika:**
**💡 Pitanja za CEO (odluke koje samo ti možeš doneti):**"""}]
    )
    pm_report = pm_resp.content[0].text
    await send("project_manager", pm_report, {"agent": "project_manager"})
    await update_progress("project_manager", 70, "working")

    session["step"] = "mid_review"
    await send("approval_request",
        "---\n✅ **SASTANAK 3 — MID-REVIEW**\n\nPreglej izveštaj iznad. Kako nastavljamo?",
        {"step": "mid_review", "options": ["DA", "NE", "IZMENI"]}
    )


# ─────────────────────────────────────────
# POKRETANJE
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "█"*50)
    print("  CEO IDEA INCUBATOR — POKRENUT")
    print("  Otvori: http://localhost:8000")
    print("  Samo lokalni pristup — bezbedno ✅")
    print("█"*50 + "\n")

    uvicorn.run(
        "server:app",
        host="127.0.0.1",   # SAMO localhost
        port=8000,
        reload=False
    )
