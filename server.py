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
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)

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
        await send("system", "🏢 **CEO INKUBATOR IDEJA** — Dobrodošao!\n\nOpiši svoju ideju što jasnije možeš. Nema loših ideja — samo počni.")
        await update_progress("ceo", 10, "active")

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")
            content = data.get("content", "")

            # ── CEO unosi ideju ──────────────────────────────
            if session["step"] == "idea_input" and msg_type == "message":
                session["idea_raw"] = content
                session["messages"].append({"role": "user", "content": content})
                await update_progress("ceo", 30, "active")

                # Groq — brza brainstorm pitanja
                await send("agent_start", "🔥 **GROQ** analizira ideju...", {"agent": "groq"})
                groq_client = Groq(api_key=GROQ_API_KEY)
                groq_resp = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "Ti si AI Brainstorm Partner. Postavi 4-5 preciznih pitanja koja će pomoći CEO-u da razradi ideju. Budi koncizan i entuzijastičan."},
                        {"role": "user", "content": f"CEO ideja: {content}"}
                    ],
                    temperature=0.8, max_tokens=600
                )
                groq_questions = groq_resp.choices[0].message.content
                await send("groq", groq_questions, {"agent": "groq"})

                session["step"] = "brainstorm_dialog"
                session["messages"].append({"role": "assistant", "content": groq_questions})
                await update_progress("ceo", 50, "active")
                await update_progress("brainstorm", 30, "working")
                save_session_to_disk(session_id)

            # ── CEO odgovara na pitanja ──────────────────────
            elif session["step"] == "brainstorm_dialog" and msg_type == "message":
                session["messages"].append({"role": "user", "content": content})
                await update_progress("brainstorm", 60, "working")

                # Gemini — duboka analiza
                await send("agent_start", "🎯 **GEMINI** radi duboku analizu...", {"agent": "gemini"})
                gemini_model = genai.GenerativeModel(GEMINI_MODEL)
                gemini_prompt = f"""
CEO ideja: {session['idea_raw']}
CEO odgovori: {content}

Napravi FINALNU DEFINICIJU ideje:

**NAZIV PROJEKTA:** [ime]
**ŠTA JE TO:** [2-3 rečenice]
**PROBLEM KOJI REŠAVA:** [konkretno]
**TARGET KORISNICI:** [ko tačno]
**KLJUČNE FUNKCIONALNOSTI:**
- [feature 1]
- [feature 2]
- [feature 3]
**JEDINSTVENA VREDNOST:** [šta ga razlikuje]
**PROCENA TRŽIŠTA:** [potencijal]
"""
                gemini_resp = gemini_model.generate_content(gemini_prompt)
                refined = gemini_resp.text
                session["idea_refined"] = refined
                await send("gemini", refined, {"agent": "gemini"})

                session["step"] = "idea_approval"
                await update_progress("brainstorm", 100, "done")
                await update_progress("ceo", 70, "active")

                await send("approval_request",
                    "---\n✅ **SASTANAK 1 — ODOBRENJE IDEJE**\n\nPregledaj finalnu verziju ideje gore. Da li nastavljamo?",
                    {"step": "idea_approval", "options": ["DA", "NE", "IZMENI"]}
                )
                save_session_to_disk(session_id)

            # ── CEO odobrava ideju ───────────────────────────
            elif session["step"] == "idea_approval" and msg_type == "decision":
                decision = content.upper()
                note = data.get("note", "")

                if decision == "NE":
                    session["step"] = "idea_input"
                    await update_progress("ceo", 10, "active")
                    await send("system", f"🔄 Vraćamo se. Recite nam šta treba drugačije?\n*Razlog:* {note}")

                elif decision in ("DA", "IZMENI"):
                    if note:
                        session["amendments"].append(note)
                        await send("system", f"📝 Izmene zabeležene: *{note}*")

                    await update_progress("ceo", 100, "done")
                    await update_progress("planner", 20, "working")
                    session["step"] = "planning"
                    await send("agent_start", "📋 **PLANNER** kreira detaljni plan realizacije...", {"agent": "planner"})

                    # Claude — planning
                    claude_client = Anthropic()
                    amendments_txt = f"\nCEO izmene: {note}" if note else ""
                    plan_resp = claude_client.messages.create(
                        model=CLAUDE_MODEL,
                        max_tokens=1500,
                        messages=[{"role": "user", "content": f"""
Kreiraj DETALJNI PROJECT PLAN za:

{session['idea_refined']}
{amendments_txt}

Format:
**📅 TIMELINE**
- Nedelja 1-2: [šta]
- Nedelja 3-4: [šta]
- Nedelja 5-6: [šta]
- Nedelja 7-8: [šta]

**🎯 MILESTONES**
[5 konkretnih milestone-a sa datumima]

**👥 TIM**
[Ko je potreban]

**💰 BUDGET PROCENA**
[Breakdown]

**⚠️ RIZICI**
[Top 3 rizika + rešenja]
"""}]
                    )
                    plan = plan_resp.content[0].text
                    session["plan"] = plan
                    await send("claude", plan, {"agent": "claude"})
                    await update_progress("planner", 100, "done")

                    session["step"] = "plan_approval"
                    await send("approval_request",
                        "---\n✅ **SASTANAK 2 — ODOBRENJE PLANA**\n\nPreglej plan iznad. Da li nastavljamo sa realizacijom?",
                        {"step": "plan_approval", "options": ["DA", "NE", "IZMENI"]}
                    )
                save_session_to_disk(session_id)

            # ── CEO odobrava plan ────────────────────────────
            elif session["step"] == "plan_approval" and msg_type == "decision":
                decision = content.upper()
                note = data.get("note", "")

                if decision == "NE":
                    session["step"] = "planning"
                    await send("system", f"🔄 Revizija plana. Razlog: {note}")
                    # Ponovi planning
                    session["step"] = "idea_approval"
                    await send("system", "Pošalji DA ponovo kada si spreman da krenem sa novim planom.")

                elif decision in ("DA", "IZMENI"):
                    if note:
                        session["amendments"].append(note)

                    await update_progress("coo", 20, "working")
                    session["step"] = "execution"
                    await send("agent_start", "⚙️ **COO** delegira zadatke timu...", {"agent": "coo"})

                    # Pokreni sve agente paralelno
                    await _run_execution(websocket, session, send, update_progress)
                save_session_to_disk(session_id)

            # ── Catch-all ────────────────────────────────────
            elif msg_type == "ping":
                await send("pong", "")

    except WebSocketDisconnect:
        save_session_to_disk(session_id)


async def _run_execution(websocket, session, send, update_progress):
    """Pokretanje celog execution tima"""
    claude_client = Anthropic()
    idea = session["idea_refined"]
    plan = session["plan"]
    amendments = "\n".join(session["amendments"]) if session["amendments"] else ""

    # COO brief
    coo_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": f"Ti si COO. Delegiraj zadatke timu za projekat:\n{idea}\nPlan:\n{plan}\n{f'CEO izmene: {amendments}' if amendments else ''}\n\nNapravi kratki task brief za: Dev, Design, Marketing, QA tim."}]
    )
    task_brief = coo_resp.content[0].text
    session["task_brief"] = task_brief
    await send("coo", task_brief, {"agent": "coo"})
    await update_progress("coo", 100, "done")

    # Developer
    await update_progress("developer", 20, "working")
    await send("agent_start", "🏗️ **DEVELOPER** kreira arhitekturu...", {"agent": "developer"})
    dev_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=1200,
        messages=[{"role": "user", "content": f"Ti si Senior Developer. Napravi tehničku arhitekturu za:\n{idea}\n\nUključi: stack, struktura foldera, ključni moduli, API endpoints, baza podataka."}]
    )
    session["department_outputs"]["development"] = dev_resp.content[0].text
    await send("developer", dev_resp.content[0].text, {"agent": "developer"})
    await update_progress("developer", 100, "done")

    # Designer
    await update_progress("designer", 20, "working")
    await send("agent_start", "🎨 **DESIGNER** kreira design system...", {"agent": "designer"})
    design_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=800,
        messages=[{"role": "user", "content": f"Ti si UI/UX Designer. Napravi design sistem za:\n{idea}\n\nUključi: color palette (hex), tipografiju, ključne ekrane, UX tok."}]
    )
    session["department_outputs"]["design"] = design_resp.content[0].text
    await send("designer", design_resp.content[0].text, {"agent": "designer"})
    await update_progress("designer", 100, "done")

    # Marketing
    await update_progress("marketing", 20, "working")
    await send("agent_start", "📢 **MARKETING** kreira GTM strategiju...", {"agent": "marketing"})
    mkt_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=800,
        messages=[{"role": "user", "content": f"Ti si Marketing Direktor. Napravi go-to-market strategiju za:\n{idea}\n\nUključi: messaging, kanali, launch plan, KPIs."}]
    )
    session["department_outputs"]["marketing"] = mkt_resp.content[0].text
    await send("marketing", mkt_resp.content[0].text, {"agent": "marketing"})
    await update_progress("marketing", 100, "done")

    # QA
    await update_progress("qa", 20, "working")
    await send("agent_start", "✅ **QA** kreira test strategiju...", {"agent": "qa"})
    qa_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=700,
        messages=[{"role": "user", "content": f"Ti si QA Lead. Napravi test strategiju za:\n{idea}\n\nUključi: unit, integration, E2E testove i acceptance criteria."}]
    )
    session["department_outputs"]["qa"] = qa_resp.content[0].text
    await send("qa", qa_resp.content[0].text, {"agent": "qa"})
    await update_progress("qa", 100, "done")

    # Project Manager — mid-review
    await update_progress("project_manager", 30, "working")
    await send("agent_start", "📊 **PROJECT MANAGER** priprema mid-review...", {"agent": "project_manager"})
    pm_resp = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=900,
        messages=[{"role": "user", "content": f"""Ti si Project Manager. Napravi CEO mid-review izveštaj.

Projekat: {idea}

Dev output: {session['department_outputs']['development'][:400]}
Design output: {session['department_outputs']['design'][:300]}
Marketing output: {session['department_outputs']['marketing'][:300]}
QA output: {session['department_outputs']['qa'][:300]}

Format:
**📊 STATUS:** [On Track / At Risk]
**Završenost:** [X%]
**✅ Urađeno:** [lista]
**⚠️ Rizici:** [lista]
**💡 Odluke za CEO:** [2-3 pitanja]
"""}]
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
