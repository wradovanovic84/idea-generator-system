import os
from anthropic import Anthropic
from dotenv import load_dotenv
from config import *

load_dotenv()

class QAExpert:
    """EXPERT za QA/Testing - Claude"""
    
    def __init__(self):
        self.client = Anthropic()
    
    def create_test_strategy(self, requirements):
        """Kreira test strategiju"""
        
        print("\n✅ Kreiram test strategiju...")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Kreiraj COMPREHENSIVE TEST STRATEGY za:
                    
                    {requirements}
                    
                    TREBAM:
                    1. UNIT TESTS (individualne funkcije)
                    2. INTEGRATION TESTS (kako delovi rade zajedno)
                    3. E2E TESTS (čitav workflow)
                    4. SECURITY TESTS (sigurnost)
                    5. PERFORMANCE TESTS (brzina)
                    6. USABILITY TESTS (user experience)
                    
                    Za svaki tip daj primere testova!
                    """
                }
            ]
        )
        
        return response.content[0].text
    
    def find_potential_bugs(self, code):
        """Pronalazi potencijalne bugove"""
        
        print("\n🐛 Tragam za bugovima...")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    PRONAĐI SVE POTENCIJALNE BUGOVE U KODU:
                    
                    {code}
                    
                    Za svaki bug daj:
                    - Lokacija (gde je problem?)
                    - Ozbiljnost (Critical/High/Medium/Low)
                    - Uticaj (šta se dešava?)
                    - Rešenje (kako popraviti?)
                    
                    Budi PARANOIČAN - kao da se u produkciji grešica može koštati miliona!
                    """
                }
            ]
        )
        
        return response.content[0].text


# TEST
if __name__ == "__main__":
    expert = QAExpert()
    
    requirements = "Finansijska aplikacija sa user auth, expense tracking, AI advice"
    
    strategy = expert.create_test_strategy(requirements)
    print(strategy)
