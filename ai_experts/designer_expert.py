import os
from google import genai as google_genai
from dotenv import load_dotenv
from config import *

load_dotenv()

class DesignerExpert:
    """EXPERT za UI/UX DIZAJN - Gemini Pro"""

    def __init__(self):
        self.gemini = google_genai.Client(api_key=GEMINI_API_KEY)
    
    def create_design_system(self, app_name, app_description):
        """Kreira kompletan design system"""
        
        print("\n🎨 Kreiram design system...")
        
        prompt = f"""
        Kreiraj KOMPLETAN DESIGN SYSTEM za: {app_name}
        
        Opis: {app_description}
        
        TREBAM:
        
        1. 🎨 COLOR PALETTE
           - Primary, secondary, accent boje
           - Hex kodovi
           - Kako se koriste?
        
        2. 📝 TYPOGRAPHY
           - Font familije (preporuka)
           - Sizes (heading, body, small)
           - Line heights
        
        3. 📦 COMPONENT LIBRARY
           - Button styles
           - Input fields
           - Cards
           - Modals
           - Navigation
        
        4. 🎯 SPACING SYSTEM
           - Grid (8px, 16px, itd)
           - Padding/margin rules
        
        5. ♿ ACCESSIBILITY
           - Color contrast
           - Font sizes za čitljivost
           - Touch target sizes
        
        6. 📱 RESPONSIVE BREAKPOINTS
           - Mobile: 320px
           - Tablet: 768px
           - Desktop: 1024px
        
        7. 🎬 ANIMATIONS
           - Transitions (duration, easing)
           - Micro-interactions
        
        Budi DETALJNO! Kao za Big Tech design system!
        """
        
        response = self.gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return response.text
    
    def create_wireframes_description(self, screens_list):
        """Generiši detaljan opis wireframe-a"""
        
        print("\n📐 Kreiram wireframe deskripcije...")
        
        prompt = f"""
        Kreiraj DETALJNE WIREFRAME DESKRIPCIJE za ove ekrane:
        
        {screens_list}
        
        Za svaki ekran napiši:
        1. Layout (gde su elementi?)
        2. Elements (šta je na ekranu?)
        3. Interactions (šta se dešava kada klikneš?)
        4. States (kako izgleda kada je loading, error, itd?)
        
        Budi DOVOLJNO DETALJAN da developer može to da implementira!
        """
        
        response = self.gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return response.text
    
    def create_user_flows(self, main_feature):
        """Kreira User Flow dijagrame"""
        
        print("\n🔄 Kreiram user flows...")
        
        prompt = f"""
        Kreiraj USER FLOW za: {main_feature}
        
        Prikaži:
        1. Početna tačka (gde korisnik počinje?)
        2. Koraci (šta radi korisnik?)
        3. Odluke (gde se deljenju putanja?)
        4. End goal (šta korisnik dostiže?)
        
        Format: ASCII diagram sa strelicama
        
        Primer:
        [Login] → [Choose action] → [Add expense] → [Success]
                                  ↘ [View report] →
        
        Napravi za našu aplikaciju!
        """
        
        response = self.gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return response.text


# TEST
if __name__ == "__main__":
    expert = DesignerExpert()
    
    app_name = "FinanceAI"
    description = "Aplikacija za upravljanje finansijama sa AI savetima"
    
    design_system = expert.create_design_system(app_name, description)
    print(design_system)
