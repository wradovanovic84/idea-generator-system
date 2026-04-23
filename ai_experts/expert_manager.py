import json
import sys
import os
from datetime import datetime

# Dodaj parent direktorijum u path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_experts.ceo_session import CEOSession
from ai_experts.coo_agent import COOAgent
from ai_experts.project_manager_agent import ProjectManagerAgent
from ai_experts.brainstormer_expert import BrainstormerExpert
from ai_experts.developer_expert import DeveloperExpert
from ai_experts.planner_expert import PlannerExpert
from ai_experts.designer_expert import DesignerExpert
from ai_experts.marketing_expert import MarketingExpert
from ai_experts.qa_expert import QAExpert
from config import *


class ExpertTeamManager:
    """
    ORCHESTRATOR — vodi kompletan CEO → Tim → Produkt workflow.

    Flow:
    1. CEO unosi ideju
    2. Brainstorm sesija s AI
    3. [SASTANAK 1] CEO odobrava finalnu ideju
    4. Planner pravi plan
    5. [SASTANAK 2] CEO odobrava plan
    6. COO delegira zadatke timu
    7. Tim radi (Dev, Design, Marketing, QA)
    8. COO sintetiše
    9. [SASTANAK 3] CEO mid-review
    10. PM priprema finalni deliverable
    11. [FINALE] CEO 100% odobrenje
    """

    def __init__(self):
        self.ceo = CEOSession()
        self.coo = COOAgent()
        self.pm = ProjectManagerAgent()
        self.brainstormer = BrainstormerExpert()
        self.planner = PlannerExpert()
        self.developer = DeveloperExpert()
        self.designer = DesignerExpert()
        self.marketing = MarketingExpert()
        self.qa = QAExpert()

        self.project_data = {}

    # ─────────────────────────────────────────────────────────
    # GLAVNI FLOW
    # ─────────────────────────────────────────────────────────
    def run(self):
        print("\n" + "█"*70)
        print("  IDEA INKUBATOR — SISTEM POKRENUT")
        print("  Od vaše ideje do gotovog proizvoda.")
        print("█"*70)

        # ── KORAK 1: CEO unosi ideju ──────────────────────────
        raw_idea = self.ceo.capture_idea()

        # ── KORAK 2: Brainstorm sa CEO-om ────────────────────
        refined_idea = self.ceo.brainstorm_with_ceo(raw_idea)
        self.project_data["refined_idea"] = refined_idea

        # ── KORAK 3: CEO odobrava ideju [SASTANAK 1] ─────────
        decision = self.ceo.ceo_approve_idea(refined_idea)
        while not decision["approved"]:
            # Revizija ideje na osnovu CEO feedbacka
            refined_idea = self._revise_idea(raw_idea, refined_idea, decision["amendment"])
            self.project_data["refined_idea"] = refined_idea
            decision = self.ceo.ceo_approve_idea(refined_idea)

        if decision["amendment"]:
            refined_idea = self._revise_idea(raw_idea, refined_idea, decision["amendment"])
            self.project_data["refined_idea"] = refined_idea

        # ── KORAK 4: Planner pravi plan ──────────────────────
        brainstorm_data = self.brainstormer.get_full_brainstorm(refined_idea)
        self.project_data["brainstorm"] = brainstorm_data

        plan = self.planner.create_project_plan(refined_idea, str(brainstorm_data))
        self.project_data["plan"] = plan

        # ── KORAK 5: CEO odobrava plan [SASTANAK 2] ──────────
        plan_decision = self.ceo.ceo_approve_plan(plan)
        while not plan_decision["approved"]:
            plan = self.planner.create_project_plan(
                refined_idea + f"\n\nCEO IZMENE: {plan_decision['amendment']}",
                str(brainstorm_data)
            )
            self.project_data["plan"] = plan
            plan_decision = self.ceo.ceo_approve_plan(plan)

        amendments_so_far = plan_decision.get("amendment", "")

        # ── KORAK 6: COO delegira zadatke ────────────────────
        task_brief = self.coo.delegate_tasks(refined_idea, plan, amendments_so_far)
        self.project_data["task_brief"] = task_brief

        # ── KORAK 7: Tim radi ────────────────────────────────
        print("\n\n" + "⚙️  "*20)
        print("TIM RADI — Svi departmani u akciji...")
        print("⚙️  "*20)

        department_outputs = self._run_all_departments(refined_idea)
        self.project_data["department_outputs"] = department_outputs

        # ── KORAK 8: COO sintetiše ───────────────────────────
        coo_summary = self.coo.create_execution_summary(task_brief, department_outputs)
        self.project_data["coo_summary"] = coo_summary

        # ── KORAK 9: CEO mid-review [SASTANAK 3] ─────────────
        progress_report = self.pm.create_progress_report(
            refined_idea, coo_summary, department_outputs
        )
        mid_decision = self.ceo.ceo_mid_review(progress_report)

        if not mid_decision["approved"]:
            # Ugradi izmene i ponovi deo rada
            for dept, output in department_outputs.items():
                department_outputs[dept] = self.pm.incorporate_amendments(
                    output, mid_decision["amendment"], dept
                )
            self.project_data["department_outputs"] = department_outputs
            coo_summary = self.coo.create_execution_summary(task_brief, department_outputs)
            self.project_data["coo_summary"] = coo_summary

        all_amendments = "\n".join(filter(None, [
            amendments_so_far,
            mid_decision.get("amendment", "")
        ]))

        # ── KORAK 10: PM priprema finalni deliverable ─────────
        final_deliverable = self.pm.prepare_final_deliverable(
            refined_idea, department_outputs, all_amendments
        )
        self.project_data["final_deliverable"] = final_deliverable

        # ── KORAK 11: CEO finalno odobrenje [FINALE] ──────────
        approved = self.ceo.ceo_final_approval(final_deliverable)
        while not approved:
            # CEO nije zadovoljan — još jedna iteracija
            for dept, output in department_outputs.items():
                department_outputs[dept] = self.pm.incorporate_amendments(
                    output,
                    "\n".join(self.ceo.session_data["amendments"]),
                    dept
                )
            final_deliverable = self.pm.prepare_final_deliverable(
                refined_idea, department_outputs,
                "\n".join(self.ceo.session_data["amendments"])
            )
            self.project_data["final_deliverable"] = final_deliverable
            approved = self.ceo.ceo_final_approval(final_deliverable)

        # ── ČUVAMO SVE ────────────────────────────────────────
        self._save_all()
        self.ceo.save_session()

        print("\n\n" + "█"*70)
        print("  ✅ PROJEKAT ZAVRŠEN I ODOBREN OD CEO-a!")
        print(f"  Sačuvano u: storage/")
        print("█"*70)

        return self.project_data

    # ─────────────────────────────────────────────────────────
    # POMOĆNE METODE
    # ─────────────────────────────────────────────────────────
    def _run_all_departments(self, refined_idea):
        outputs = {}

        print("\n🎨 Design tim radi...")
        outputs["design"] = self.designer.create_design_system(
            refined_idea.split("\n")[0][:50], refined_idea
        )

        print("\n📐 Development tim radi...")
        outputs["development"] = self.developer.generate_architecture(refined_idea)

        print("\n📢 Marketing tim radi...")
        outputs["marketing"] = self.marketing.create_gtm_strategy(refined_idea)

        print("\n✅ QA tim radi...")
        outputs["qa"] = self.qa.create_test_strategy(refined_idea)

        return outputs

    def _revise_idea(self, raw_idea, current_refined, amendments):
        from anthropic import Anthropic
        client = Anthropic()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": f"""
Revidirana verzija ideje na osnovu CEO feedbacka.

ORIGINALNA IDEJA CEO-a: {raw_idea}
TRENUTNA VERZIJA: {current_refined}
CEO IZMENE: {amendments}

Napravi novu FINALNU VERZIJU koja uključuje sve CEO izmene.
Koristi isti format kao originalna verzija.
"""
            }]
        )
        revised = response.content[0].text
        print(f"\n📝 Revidirana ideja:\n{revised}\n")
        return revised

    def _save_all(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"storage/project_{timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.project_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Projekat sačuvan: {path}")
