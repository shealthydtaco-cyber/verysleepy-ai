# config.py

OLLAMA_URL = "http://localhost:11434"

ROUTER_MODEL = "phi3:mini"
BRAIN_MODEL  = "mistral:7b"

ALLOWED_PATHS = [
    "C:/Users"
]

ALLOWED_APPS = [
    "notepad.exe",
    "chrome.exe"

]

# Opinion mode controls output style for opinion analysis
# options: balanced | blunt | critical | academic
OPINION_MODE = "blunt"
VOICE_ENABLED = True
VOICE_INPUT = True
VOICE_OUTPUT = True
