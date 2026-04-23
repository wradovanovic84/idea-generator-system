from anthropic import Anthropic
from dotenv import load_dotenv
from config import *

load_dotenv()

class ProjectManagerAgent:
    """
    GM / Project Manager Agent — prati realizaciju, unapređuje,
    organizuje mid-review izveštaj za CEO i priprema finalni deliverable.
    """

    def __init__(self):
        self.client = Anthropic()

    def create_progress_report(self, refined_idea, coo_summary, department_outputs):
        """Kreira mid-review izveštaj za CEO sastanak"""

        print("\n" + "="*70)
        print("  PROJECT MANAGER — MID-REVIEW IZVEŠTAJ")
        print("="*70)
        print("\n📊 PM priprema izveštaj za CEO...\n")

        outputs_text = "\n\n".join([
            f"=== {dept.upper()} ===\n{output}"
            for dept, output in department_outputs.items()
        ])

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1400,
            messages=[{
                "role": "user",
                "content": f"""
Ti si iskusan Project Manager koji priprema mid-review za CEO.

PROJEKAT:
{refined_idea}

COO IZVEŠTAJ:
{coo_summary}

OUTPUTI TIMOVA:
{outputs_text}

Napravi CEO MID-REVIEW u sledećem formatu:

📊 STATUS PROJEKTA
Opšti status: [On Track / At Risk / Behind]
Završenost: [X%]

✅ ŠTA JE GOTOVO
[bullet lista konkretnih deliverables]

🔄 U TOKU
[šta se trenutno radi]

⚠️ PROBLEMI I RIZICI
[konkretni problemi sa predlozima rešenja]

💡 PREPORUKE ZA CEO
[2-3 konkretne odluke koje CEO treba da donese]

📅 SLEDEĆI KORACI
[šta sledi nakon CEO odobrenja]

Budi jasan, koncizan — CEO nema vremena za detalje, treba mu slika i odluke.
"""
            }]
        )

        report = response.content[0].text
        print(report)
        return report

    def prepare_final_deliverable(self, refined_idea, all_outputs, ceo_amendments):
        """Pakuje sve u finalni deliverable za CEO odobrenje"""

        print("\n" + "="*70)
        print("  PROJECT MANAGER — PRIPREMA FINALNOG DELIVERABLE-a")
        print("="*70)
        print("\n📦 PM pakuje finalni proizvod...\n")

        outputs_text = "\n\n".join([
            f"=== {dept.upper()} ===\n{output}"
            for dept, output in all_outputs.items()
        ])

        amendments_section = f"\nCEO IZMENE TOKOM PROCESA:\n{ceo_amendments}" if ceo_amendments else ""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""
Ti si Project Manager koji priprema FINALNI DELIVERABLE za CEO odobrenje.

PROJEKAT:
{refined_idea}
{amendments_section}

SVI OUTPUTI TIMOVA:
{outputs_text}

Napravi FINALNI DELIVERABLE dokument sa sledećom strukturom:

═══════════════════════════════════════
        FINALNI DELIVERABLE — [Naziv projekta]
═══════════════════════════════════════

📌 EXECUTIVE SUMMARY
[3-4 rečenice — šta je ovo i zašto je važno]

🎯 ŠTA SMO NAPRAVILI
[Jasno i konkretno — šta tačno postoji]

🏗️ TEHNIČKO REŠENJE
[Arhitektura, tehnologije, kod koji postoji]

🎨 DIZAJN
[Design sistem, UI/UX odluke]

📢 MARKETING PLAN
[Go-to-market, poruka, kanali]

💰 FINANSIJE
[Budget, troškovi, prihod projekcija]

✅ QA STATUS
[Šta je testirano, šta je OK]

🚀 KAKO POKRENUTI
[Konkretni koraci za launch]

📊 METRIKE USPEHA
[Kako ćemo znati da je uspelo]

Budi konkretan, profesionalan, spreman za CEO finalnu potvrdu.
"""
            }]
        )

        deliverable = response.content[0].text
        print(deliverable)
        return deliverable

    def incorporate_amendments(self, original_output, amendments, context):
        """Ugrađuje CEO izmene u postojeći output"""

        print(f"\n🔄 PM ugrađuje CEO izmene u {context}...\n")

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": f"""
Revidiraj sledeći output na osnovu CEO izmena.

KONTEKST: {context}

ORIGINALNI OUTPUT:
{original_output}

CEO IZMENE/ZAHTEVI:
{amendments}

Napravi REVIDIRANU VERZIJU koja potpuno uključuje CEO zahteve.
Označi šta je izmenjeno sa [IZMENJENO].
"""
            }]
        )

        revised = response.content[0].text
        print(revised)
        return revised
