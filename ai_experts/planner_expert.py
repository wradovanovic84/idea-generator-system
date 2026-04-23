import os
from anthropic import Anthropic
from dotenv import load_dotenv
from config import *

load_dotenv()

class PlannerExpert:
    """EXPERT za DETALJNO PLANIRANJE - Claude"""
    
    def __init__(self):
        self.client = Anthropic()
    
    def create_project_plan(self, idea_summary, brainstorm_data):
        """Kreira detaljni projekt plan"""
        
        print("\n📋 Kreiram detaljni projekt plan...")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_PLAN_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Kreiraj DETALJNI PROJECT PLAN za:
                    
                    IDEJA: {idea_summary}
                    
                    BRAINSTORM INSIGHTS:
                    {brainstorm_data}
                    
                    PLAN TREBAM SA:
                    
                    1. 📅 TIMELINE (Week by week)
                       - Week 1-2: MVP planning
                       - Week 3-4: Core development
                       - Week 5-6: Testing & refinement
                       - Week 7-8: Launch preparation
                    
                    2. 🎯 MILESTONES
                       - Specifični, measurable milestones
                       - Deadlines
                    
                    3. 👥 TEAM REQUIREMENTS
                       - Ko je potreban?
                       - Skills i iskustvo
                    
                    4. 💰 BUDGET ESTIMATE
                       - Development
                       - Infrastructure
                       - Marketing
                    
                    5. 📊 SUCCESS METRICS
                       - KPIs
                       - Kako meriti uspeh?
                    
                    6. ⚠️ RISK MANAGEMENT
                       - Mogući problemi
                       - Kako ih izbeći?
                    
                    Budi SPECIFIČNO! Kao za Startup pitch deck!
                    """
                }
            ]
        )
        
        return response.content[0].text
    
    def create_sprint_plan(self, project_overview, sprint_number=1):
        """Kreira sprint plan (2 nedelje)"""
        
        print(f"\n🏃 Kreiram sprint #{sprint_number} plan...")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Kreiraj SPRINT #{sprint_number} PLAN (2 nedelje):
                    
                    Project overview: {project_overview}
                    
                    TREBAM:
                    1. PRIORITIZED TASKS (šta raditi prvo?)
                    2. DAILY BREAKDOWN (šta svaki dan?)
                    3. BLOCKERS (šta može da nas zaustavi?)
                    4. SUCCESS CRITERIA (kako znamo da je OK?)
                    
                    Budi AKCIONO ORIJENTISAN!
                    """
                }
            ]
        )
        
        return response.content[0].text


# TEST
if __name__ == "__main__":
    expert = PlannerExpert()
    
    idea = "Mobilna app za finansije sa AI"
    brainstorm = "Market je veliki, trebam korisnici od 18-35, main feature je AI saveti"
    
    plan = expert.create_project_plan(idea, brainstorm)
    print(plan)
