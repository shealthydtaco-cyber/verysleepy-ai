# router.py

import requests
import json
from config import OLLAMA_URL, ROUTER_MODEL

NSFW_KEYWORDS = [
    "nsfw", "adult", "erotic", "explicit", "sex",
    "incest", "porn", "xxx", "18+"
]

SEARCH_KEYWORDS = [
    "find", "search", "what is", "who is", "why",
    "how", "explain", "latest", "news", "about",
    "is this", "facts", "details",
    "safe", "privacy", "secure", "risk", "trust",
    "scam", "legal", "security","what are the", 
    "tell me about","what are", "give me information on", 
    "information about", "looking for", "need to know", 
    "want to know"," details on", "data on", "insights on", 
    "overview of","what","who","when","where","why","how to"
]

PERSON_KEYWORDS = ["who is", "biography", "born", "age", "net worth"]

OPINION_KEYWORDS = [
    "what do you think",
    "your opinion",
    "do you agree",
    "is this right",
    "is this wrong",
    "thoughts on",
    "opinion on",
    "analyze this statement"
]

def route_intent(user_text: str) -> dict:
    text = user_text.lower()

    # 🔴 HARD RULE FIRST (no LLM)
    for word in NSFW_KEYWORDS:
        if word in text:
            return {"intent": "adult_recommendation"}

    # 🧾 Person-related queries -> always search
    for word in PERSON_KEYWORDS:
        if word in text:
            return {"intent": "search_and_explain"}

    # 🗣 Opinion-related queries -> opinion analysis
    for phrase in OPINION_KEYWORDS:
        if phrase in text:
            return {"intent": "opinion_analysis"}

    # 🔎 Simple search keyword routing
    for word in SEARCH_KEYWORDS:
        if word in text:
            return {"intent": "search_and_explain"}

    # Default to chat
    return {"intent": "chat"}  
