import os
import json
from groq import Groq
from google import genai as google_genai
from dotenv import load_dotenv
from config import *

load_dotenv()

class BrainstormerExpert:
    """EXPERT za brainstorming - Groq (brz) + Gemini Pro (duboko)"""
    
    def __init__(self):
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.conversation_history = []
    
    def phase1_quick_brainstorm_groq(self, idea):
        """FAZA 1: Groq - Brza, energična brainstorm pitanja"""
        
        print("\n🔥 FASE 1: Groq - Brza brainstorm pitanja...")
        
        system = """
        EXPERT BRAINSTORMER - Groq (Brz, energičan, kreativna pitanja)
        
        Tvoj je posao da postaviš ODLIČNU, ENERGIČNA pitanja koja će:
        1. Rasčistiti ideju
        2. Otkriti nove mogućnosti
        3. Naći potencijal
        
        Pitanja trebaju biti:
        ✅ Specifična (ne opšta)
        ✅ Tražeće (koji problem? zašto? kako?)
        ✅ Kreativna (nešto novo)
        ✅ Broja (5-7 pitanja)
        
        Budi ENTUZIJASTIČAN! Kao coach koji veruje u ideju!
        """
        
        response = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Moja ideja: {idea}"}
            ],
            temperature=BRAINSTORM_TEMP,
            max_tokens=MAX_BRAINSTORM_TOKENS
        )
        
        groq_response = response.choices[0].message.content
        print(f"\n🔥 GROQ:\n{groq_response}")
        
        return groq_response
    
    def phase2_deep_analysis_gemini(self, idea, groq_insights):
        """FAZA 2: Gemini Pro - Duboka, analitička analiza"""
        
        print("\n\n🎯 FASE 2: Gemini Pro - Duboka analiza...")
        
        gemini = google_genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
        EXPERT ANALIZIRAJUĆI STRATEGIJU - Gemini Pro (Detaljan, analitičan)
        
        Ideja: {idea}
        
        Groq je dao ova pitanja i uvide:
        {groq_insights}
        
        Sada trebam DUBOKU ANALIZU sa:
        
        1. 📊 MARKET ANALYSIS
           - Koliki je tržišni potencijal?
           - Ko su direktni konkurenti?
           - Šta nedostaje na tržištu?
        
        2. 👥 TARGET AUDIENCE
           - Tačan demografski profil
           - Leurs pain points
           - Gde se nalaze?
        
        3. 💪 STRENGTHS & WEAKNESSES
           - Čime je ovo bolje od konkurencije?
           - Gde su rizici i slabosti?
        
        4. 🚀 GO-TO-MARKET STRATEGY
           - Kako lansirati?
           - Kako doći do prvog miliona korisnika?
        
        5. 💰 MONETIZATION
           - Kako zaraditi?
           - Koju cenu postaviti?
        
        6. 📈 METRICS ZA USPEH
           - KPIs za praćenje
           - Šta znači uspeh?
        
        Budi PROFESIONALAN I DUBOKO ANALITIZAN!
        """
        
        response = gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        gemini_response = response.text

        print(f"\n🎯 GEMINI PRO:\n{gemini_response}")
        
        return gemini_response
    
    def get_full_brainstorm(self, idea):
        """Kompletna brainstorm sesija"""
        
        print("="*70)
        print("🧠 BRAINSTORMER EXPERT - KOMPLETAN WORKFLOW")
        print("="*70)
        
        # FAZA 1: Groq - Brze pitanja
        groq_result = self.phase1_quick_brainstorm_groq(idea)
        
        # FAZA 2: Gemini Pro - Duboka analiza
        gemini_result = self.phase2_deep_analysis_gemini(idea, groq_result)
        
        # FINALNA SINTEZA
        final_summary = self._create_summary(idea, groq_result, gemini_result)
        
        print("\n\n📋 FINALNA SINTEZA:")
        print(final_summary)
        
        return {
            "idea": idea,
            "quick_brainstorm": groq_result,
            "deep_analysis": gemini_result,
            "summary": final_summary
        }
    
    def _create_summary(self, idea, groq, gemini):
        """Napravi sintezi od oba analize"""
        
        gemini = google_genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
        Napravi KRATKU SINTERZU (do 300 karaktera) koja kombinuje:
        
        Groq uvide (pitanja/ideje):
        {groq[:500]}...
        
        Gemini analizu:
        {gemini[:500]}...
        
        Sintezu napravi sa KEY TAKEAWAYS - šta je najvažnije?
        """
        
        response = gemini.models.generate_content(model=GEMINI_FLASH_MODEL, contents=prompt)
        return response.text


# TEST
if __name__ == "__main__":
    expert = BrainstormerExpert()
    
    idea = "Mobilna app za upravljanje finansijama sa AI savetima za mlade do 35 godina u Srbiji"
    
    result = expert.get_full_brainstorm(idea)
    
    # Sačuvaj rezultat
    with open("storage/brainstorm_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Rezultat sačuvan u storage/brainstorm_result.json")
