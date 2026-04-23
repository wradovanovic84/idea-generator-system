from anthropic import Anthropic
from dotenv import load_dotenv
from config import *

load_dotenv()

class COOAgent:
    """
    COO Agent — prima odobreni plan i delegira konkretne zadatke
    svakom departmentu: Developer, Designer, Marketing, Finance.
    """

    def __init__(self):
        self.client = Anthropic()

    def delegate_tasks(self, refined_idea, approved_plan, ceo_amendments=""):
        print("\n" + "="*70)
        print("  COO — DELEGIRANJE ZADATAKA TIMU")
        print("="*70)
        print("\n📋 COO analizira plan i raspoređuje zadatke...\n")

        amendments_section = f"\nCEO IZMENE/NAPOMENE:\n{ceo_amendments}" if ceo_amendments else ""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1800,
            messages=[{
                "role": "user",
                "content": f"""
Ti si COO koji koordinira tim za realizaciju projekta.

IDEJA:
{refined_idea}

ODOBRENI PLAN:
{approved_plan}
{amendments_section}

Napravi TASK BRIEF za svaki departement u sledećem formatu:

---
🏗️ DEVELOPMENT TIM
Zadaci: [konkretni zadaci]
Prioritet: [High/Medium/Low]
Deadline: [okvirni]
Dependency: [šta im treba od drugih timova]

---
🎨 DESIGN TIM
Zadaci: [konkretni zadaci]
Prioritet: [High/Medium/Low]
Deadline: [okvirni]
Dependency: [šta im treba]

---
📢 MARKETING TIM
Zadaci: [konkretni zadaci]
Prioritet: [High/Medium/Low]
Deadline: [okvirni]
Dependency: [šta im treba]

---
💰 FINANCE
Zadaci: [budget breakdown, cost tracking]
Prioritet: [High/Medium/Low]
Deadline: [okvirni]

---
✅ QA TIM
Zadaci: [šta testiraju i kada]
Prioritet: [High/Medium/Low]
Dependency: [šta im treba od Dev/Design]

---
📊 SUMMARY ZA PROJECT MANAGER
Kritičan put: [šta mora da se završi prvo]
Blokeri: [potencijalni problemi]
Ključni milestones: [3-5 tačaka]

Budi specifičan i akcionabilan.
"""
            }]
        )

        task_brief = response.content[0].text
        print(task_brief)
        return task_brief

    def create_execution_summary(self, task_brief, department_outputs):
        """Sintetiše sve outpute departmana u jedan izveštaj za PM"""

        print("\n⚙️ COO sintetiše outpute departmana...\n")

        outputs_text = "\n\n".join([
            f"=== {dept.upper()} OUTPUT ===\n{output}"
            for dept, output in department_outputs.items()
        ])

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1200,
            messages=[{
                "role": "user",
                "content": f"""
Ti si COO koji proverava rad svih departmana.

ORIGINALNI TASK BRIEF:
{task_brief}

OUTPUTI DEPARTMANA:
{outputs_text}

Napravi COO IZVEŠTAJ koji sadrži:

1. ✅ ŠTA JE URAĐENO DOBRO
2. ⚠️ ŠTA NEDOSTAJE ILI JE NEPOTPUNO
3. 🔗 KAKO SE DELOVI UKLAPAJU
4. 📊 OCENA SPREMANOSTI (0-100%)
5. 🚀 PREPORUKA ZA PROJECT MANAGERA

Budi objektivan i koncizan.
"""
            }]
        )

        summary = response.content[0].text
        print(summary)
        return summary
