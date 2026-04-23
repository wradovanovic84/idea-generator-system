import os
from dotenv import load_dotenv

load_dotenv()

# API KEYS
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# MODELS
GROQ_MODEL = "mixtral-8x7b-32768"
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
GEMINI_MODEL = "gemini-1.5-pro"  # Pro verzija!
GEMINI_FLASH_MODEL = "gemini-1.5-flash"  # Brža verzija

# TEMPERATURE (kreativnost)
BRAINSTORM_TEMP = 0.8
PLANNING_TEMP = 0.5
MARKETING_TEMP = 0.85
QA_TEMP = 0.3  # Manje kreativnosti za QA

# TOKEN LIMITS
MAX_BRAINSTORM_TOKENS = 800
MAX_PLAN_TOKENS = 1500
MAX_CODE_TOKENS = 2000
MAX_DESIGN_TOKENS = 1000

# STORAGE
IDEAS_FILE = "storage/ideas.json"
CONVERSATIONS_FILE = "storage/conversations.json"

print("✅ Config ucitan")
