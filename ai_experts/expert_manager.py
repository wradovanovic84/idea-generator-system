import json
from datetime import datetime
from brainstormer_expert import BrainstormerExpert
from developer_expert import DeveloperExpert
from planner_expert import PlannerExpert
from designer_expert import DesignerExpert
from marketing_expert import MarketingExpert
from qa_expert import QAExpert
from config import *

class ExpertTeamManager:
    """ORCHESTRATOR - Koordinira sve EXPERT-e"""
    
    def __init__(self):
        self.brainstormer = BrainstormerExpert()
        self.developer = DeveloperExpert()
        self.planner = PlannerExpert()
        self.designer = DesignerExpert()
        self.marketing = MarketingExpert()
        self.qa = QAExpert()
        
        self.project_result = {}
    
    def execute_full_workflow(self, idea):
        """KOMPLETAN WORKFLOW - od ideje do gotovog projekta!"""
        
        print("="*80)
        print("🚀 EXPERT TEAM - KOMPLETAN WORKFLOW POKRENUT")
        print("="*80)
        
        # FAZA 1: BRAINSTORMING
        print("\n\n" + "🧠 "*20)
        print("FAZA 1: BRAINSTORMING")
        print("🧠 "*20)
        brainstorm_result = self.brainstormer.get_full_brainstorm(idea)
        self.project_result["brainstorm"] = brainstorm_result
        
        # FAZA 2: PLANNING
        print("\n\n" + "📋 "*20)
        print("FAZA 2: DETALJNO PLANIRANJE")
        print("📋 "*20)
        plan = self.planner.create_project_plan(idea, str(brainstorm_result))
        self.project_result["plan"] = plan
        
        # FAZA 3: DESIGN
        print("\n\n" + "🎨 "*20)
        print("FAZA 3: DESIGN SYSTEM")
        print("🎨 "*20)
        design_system = self.designer.create_design_system(idea.split()[0], idea)
        self.project_result["design"] = design_system
        
        # FAZA 4: ARCHITECTURE
        print("\n\n" + "📐 "*20)
        print("FAZA 4: TEHNIČKA ARHITEKTURA")
        print("📐 "*20)
        architecture = self.developer.generate_architecture(idea)
        self.project_result["architecture"] = architecture
        
        # FAZA 5: MARKETING
        print("\n\n" + "📢 "*20)
        print("FAZA 5: MARKETING STRATEGIJA")
        print("📢 "*20)
        marketing = self.marketing.create_gtm_strategy(idea)
        self.project_result["marketing"] = marketing
        
        # FAZA 6: QA PLAN
        print("\n\n" + "✅ "*20)
        print("FAZA 6: QA / TESTING PLAN")
        print("✅ "*20)
        qa_strategy = self.qa.create_test_strategy(idea)
        self.project_result["qa"] = qa_strategy
        
        # SAČUVAJ SVE
        self._save_results()
        
        print("\n\n" + "="*80)
        print("✅ EXPERT TEAM - KOMPLETAN WORKFLOW ZAVRŠEN!")
        print("="*80)
        
        return self.project_result
    
    def _save_results(self):
        """Čuva sve rezultate"""
        
        # JSON sa svim rezultatima
        with open(f"storage/project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                  "w", encoding="utf-8") as f:
            json.dump(self.project_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Svi rezultati sačuvani u storage/ folder")


# RUN
if __name__ == "__main__":
    manager = ExpertTeamManager()
    
    idea = """
    Mobilna aplikacija za upravljanje finansijama sa AI savetima.
    Target: Mladi do 35 godina u Srbiji.
    Main features: Tracking troškova, AI saveti za uštedu, budgeting, reports.
    """
    
    results = manager.execute_full_workflow(idea)
