import json
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from config import *

load_dotenv()

class CEOSession:
    """
    CEO interaktivna sesija - vodi CEO kroz ceo proces od ideje do finalnog odobrenja.
    Svaki 'sastanak' je checkpoint gde CEO kaze DA / NE / IZMENI.
    """

    def __init__(self):
        self.client = Anthropic()
        self.session_data = {
            "created_at": datetime.now().isoformat(),
            "idea_raw": "",
            "idea_refined": "",
            "brainstorm_approved": False,
            "plan_approved": False,
            "mid_review_approved": False,
            "final_approved": False,
            "ceo_decisions": [],
            "amendments": []
        }

    # ─────────────────────────────────────────────
    # KORAK 1 — CEO unosi ideju
    # ─────────────────────────────────────────────
    def capture_idea(self):
        print("\n" + "="*70)
        print("  DOBRODOŠAO, CEO.")
        print("  Ovde počinje sve. Unesite vašu ideju što jasnije možete.")
        print("="*70)
        print("\nOpišite ideju (završite sa ENTER dva puta):\n")

        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)

        idea = "\n".join(lines).strip()
        self.session_data["idea_raw"] = idea
        print("\n✅ Ideja zabeležena.")
        return idea

    # ─────────────────────────────────────────────
    # KORAK 2 — AI Brainstorm sa CEO-om (dialog)
    # ─────────────────────────────────────────────
    def brainstorm_with_ceo(self, idea):
        print("\n" + "="*70)
        print("  SASTANAK 1 — BRAINSTORM SESIJA")
        print("  AI Brainstormer razrađuje vašu ideju s vama.")
        print("="*70)

        conversation = [
            {
                "role": "user",
                "content": f"""
Ti si AI Brainstorm Partner koji pomaže CEO-u da razradi i definiše ideju.

Ideja CEO-a: {idea}

Postavi 4-6 ključnih pitanja koja će pomoći da se ideja precizira.
Budi koncizan, profesionalan, entuzijastičan.
Govori direktno CEO-u (ti formu).
"""
            }
        ]

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            messages=conversation
        )
        ai_message = response.content[0].text
        print(f"\n🤖 AI Brainstormer:\n{ai_message}\n")

        conversation.append({"role": "assistant", "content": ai_message})

        # CEO odgovara na pitanja
        print("Vaši odgovori (završite sa ENTER dva puta):\n")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        ceo_answers = "\n".join(lines).strip()

        conversation.append({"role": "user", "content": ceo_answers})

        # AI sintetiše finalnu verziju ideje
        conversation.append({
            "role": "user",
            "content": """
Na osnovu naše diskusije, napravi FINALNI SAŽETAK ideje u sledećem formatu:

NAZIV PROJEKTA: [ime]
ŠTA JE TO: [2-3 rečenice]
PROBLEM KOJI REŠAVA: [1-2 rečenice]
TARGET KORISNICI: [ko]
KLJUČNE FUNKCIONALNOSTI: [3-5 bullet points]
JEDINSTVENA VREDNOST: [šta ga razlikuje]

Budi precizan i koncizan.
"""
        })

        final_response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=conversation
        )
        refined_idea = final_response.content[0].text

        print(f"\n📋 FINALNA VERZIJA IDEJE:\n{refined_idea}\n")
        self.session_data["idea_refined"] = refined_idea

        return refined_idea

    # ─────────────────────────────────────────────
    # KORAK 3 — CEO ODOBRAVA finalnu verziju ideje
    # ─────────────────────────────────────────────
    def ceo_approve_idea(self, refined_idea):
        return self._meeting_checkpoint(
            meeting_name="ODOBRENJE IDEJE",
            content=refined_idea,
            context="Ovo je finalna verzija vaše ideje pre nego što tim krene na posao."
        )

    # ─────────────────────────────────────────────
    # KORAK 4 — CEO pregleda Plan realizacije
    # ─────────────────────────────────────────────
    def ceo_approve_plan(self, plan):
        return self._meeting_checkpoint(
            meeting_name="SASTANAK 2 — PREGLED PLANA",
            content=plan,
            context="COO i Planner su napravili detaljan plan realizacije."
        )

    # ─────────────────────────────────────────────
    # KORAK 5 — CEO mid-review (u toku realizacije)
    # ─────────────────────────────────────────────
    def ceo_mid_review(self, progress_report):
        return self._meeting_checkpoint(
            meeting_name="SASTANAK 3 — MID-REVIEW",
            content=progress_report,
            context="Project Manager podnosi izveštaj o napretku. Proverite da li je sve na pravom putu."
        )

    # ─────────────────────────────────────────────
    # KORAK 6 — CEO FINALNO 100% odobrenje
    # ─────────────────────────────────────────────
    def ceo_final_approval(self, final_deliverable):
        print("\n" + "="*70)
        print("  ⭐ FINALE — FINALNO ODOBRENJE CEO-a")
        print("  Ovo je krajnji proizvod. Jednom kada potvrdite, sistem je završen.")
        print("="*70)
        print(f"\n{final_deliverable}\n")

        while True:
            decision = input("Da li ste 100% zadovoljni ovim rezultatom? (DA/NE): ").strip().upper()
            if decision == "DA":
                self.session_data["final_approved"] = True
                self._log_decision("FINAL_APPROVAL", "DA", "")
                print("\n🎉 PROJEKAT ODOBREN! Čestitamo, CEO!")
                return True
            elif decision == "NE":
                feedback = input("Šta treba da se promeni? ").strip()
                self._log_decision("FINAL_APPROVAL", "NE", feedback)
                self.session_data["amendments"].append(feedback)
                print("\n🔄 Vraćamo se na reviziju...")
                return False
            else:
                print("Unesite DA ili NE.")

    # ─────────────────────────────────────────────
    # INTERNI: generički checkpoint za sastanke
    # ─────────────────────────────────────────────
    def _meeting_checkpoint(self, meeting_name, content, context=""):
        print("\n" + "="*70)
        print(f"  📋 {meeting_name}")
        if context:
            print(f"  {context}")
        print("="*70)
        print(f"\n{content}\n")
        print("-"*70)
        print("Opcije:  DA — odobravam i nastavljamo")
        print("         NE — odbijam, vraćamo na reviziju")
        print("         IZMENI — odobravam ali sa promenama")
        print("-"*70)

        while True:
            decision = input("\nVaša odluka (DA / NE / IZMENI): ").strip().upper()

            if decision == "DA":
                self._log_decision(meeting_name, "DA", "")
                print("\n✅ Odobreno. Nastavljamo.")
                return {"approved": True, "decision": "DA", "amendment": ""}

            elif decision == "NE":
                feedback = input("Razlog / šta treba drugačije? ").strip()
                self._log_decision(meeting_name, "NE", feedback)
                self.session_data["amendments"].append(feedback)
                print("\n🔄 Vraćamo se na reviziju...")
                return {"approved": False, "decision": "NE", "amendment": feedback}

            elif decision == "IZMENI":
                changes = input("Koje izmene? ").strip()
                self._log_decision(meeting_name, "IZMENI", changes)
                self.session_data["amendments"].append(changes)
                print("\n✅ Odobreno sa izmenama. Beležimo i nastavljamo.")
                return {"approved": True, "decision": "IZMENI", "amendment": changes}

            else:
                print("Unesite DA, NE ili IZMENI.")

    def _log_decision(self, meeting, decision, note):
        self.session_data["ceo_decisions"].append({
            "meeting": meeting,
            "decision": decision,
            "note": note,
            "timestamp": datetime.now().isoformat()
        })

    def save_session(self, path="storage/ceo_session.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 CEO sesija sačuvana u {path}")

    def get_session_data(self):
        return self.session_data
