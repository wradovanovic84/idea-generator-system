import os
from anthropic import Anthropic
from dotenv import load_dotenv
from config import *

load_dotenv()

class DeveloperExpert:
    """EXPERT za pisanje PROFESIONALNOG koda - Claude"""
    
    def __init__(self):
        self.client = Anthropic()
        self.conversation_history = []
    
    def generate_architecture(self, requirements):
        """Generiši arhitekturu aplikacije"""
        
        print("\n📐 Generisem arhitekturu...")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_CODE_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Kreiraj PROFESIONALNU ARHITEKTURU za:
                    
                    {requirements}
                    
                    Trebam:
                    1. FOLDER STRUKTURA (kako organizovati kod)
                    2. TECHNOLOGY STACK (Python, JS, baza, itd)
                    3. DATA MODELS (kako je data organizovana)
                    4. API ENDPOINTS (koje rute trebaju)
                    5. AUTHENTICATION (kako štititi)
                    6. DEPLOYMENT (kako staviti u produkciju)
                    
                    Budi DETALJNO PROFESIONALNO!
                    """
                }
            ]
        )
        
        return response.content[0].text
    
    def generate_code(self, module_name, requirements):
        """Generiši kod za specifičan modul"""
        
        print(f"\n💻 Generisem kod za: {module_name}")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_CODE_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Napiši PRODUCTION-READY Python kod za: {module_name}
                    
                    Zahtevi: {requirements}
                    
                    STANDARDS:
                    ✅ PEP 8 format
                    ✅ Type hints
                    ✅ Docstrings za sve funkcije
                    ✅ Error handling
                    ✅ Logging
                    ✅ Unit test template
                    
                    Piši kao za Google/Meta!
                    """
                }
            ]
        )
        
        return response.content[0].text
    
    def review_and_improve(self, code):
        """Pregleda kod i predlaže poboljšanja"""
        
        print(f"\n🔍 Pregledavam kod...")
        
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    EXPERT CODE REVIEW:
                    
                    {code}
                    
                    Daj:
                    1. Критични problemi (MUST FIX)
                    2. Security issues
                    3. Performance optimizations
                    4. Best practices sugestije
                    5. Improved verzija koda
                    
                    Budi DETALJNO KRITIČAN!
                    """
                }
            ]
        )
        
        return response.content[0].text


# TEST
if __name__ == "__main__":
    expert = DeveloperExpert()
    
    requirements = """
    Aplikacija za upravljanje finansijama:
    - User authentication
    - Dodavanje troškova/prihoda
    - AI saveti
    - Dashboard
    """
    
    architecture = expert.generate_architecture(requirements)
    print(architecture)
