import os
from groq import Groq
import google.generativeai as genai
from dotenv import load_dotenv
from config import *

load_dotenv()

genai.configure(api_key=GEMINI_API_KEY)

class MarketingExpert:
    """EXPERT za MARKETING - Groq (brz) + Gemini (kreativnost)"""
    
    def __init__(self):
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.gemini = genai.GenerativeModel(GEMINI_MODEL)
    
    def create_gtm_strategy(self, product_info):
        """Go-to-Market strategija"""
        
        print("\n📢 Kreiram GTM strategiju...")
        
        # Groq - Brza strategija
        groq_response = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Kreiraj GO-TO-MARKET STRATEGIJU za:
                    {product_info}
                    
                    Trebam:
                    1. LAUNCH PLAN (Day 1-30)
                    2. CHANNELS (gde se oglašavati?)
                    3. MESSAGING (šta da kažem?)
                    4. PRICING (cena?)
                    5. PARTNERSHIPS (sa kime?)
                    
                    Budi AKCIONO!
                    """
                }
            ],
            temperature=MARKETING_TEMP,
            max_tokens=800
        )
        
        groq_strategy = groq_response.choices[0].message.content
        
        # Gemini - Dublja kreativnost
        gemini_prompt = f"""
        Kreiraj CREATIVE MESSAGING ANGLES za:
        {product_info}
        
        Groq je dao ovu strategiju:
        {groq_strategy[:500]}...
        
        Sada trebam 5 UNIQUE POSITIONING ANGLES:
        
        1. Za young professionals
        2. Za studente
        3. Za freelancere
        4. Za families
        5. Za investors
        
        Svaki angle trebam sa unique value proposition!
        """
        
        gemini_response = self.gemini.generate_content(gemini_prompt)
        gemini_angles = gemini_response.text
        
        return {
            "gtm_strategy": groq_strategy,
            "messaging_angles": gemini_angles
        }
    
    def create_marketing_content(self, angle, format_type="social"):
        """Generiši marketing content"""
        
        print(f"\n✍️ Kreiram {format_type} content...")
        
        response = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Napiši MARKETING {format_type.upper()} za:
                    
                    {angle}
                    
                    Trebam:
                    - Headline
                    - Body text
                    - Call to action
                    - Hashtags (ako je social)
                    
                    Budi PERSUASIVNA i KONVERTUJ!
                    """
                }
            ],
            temperature=MARKETING_TEMP,
            max_tokens=500
        )
        
        return response.choices[0].message.content


# TEST
if __name__ == "__main__":
    expert = MarketingExpert()
    
    product = "FinanceAI - Aplikacija za upravljanje finansijama sa AI savetima"
    
    strategy = expert.create_gtm_strategy(product)
    print(strategy["gtm_strategy"])
