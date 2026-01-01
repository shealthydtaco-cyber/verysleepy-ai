# main.py
from autocorrect import autocorrect_text
from router import route_intent
from brain import think
from tools import open_file, open_app
from tools import load_adult_movies
from web_search import web_search
from config import OPINION_MODE, VOICE_ENABLED, VOICE_INPUT, VOICE_OUTPUT
from memory import add_turn, get_context, set_pref, get_pref
from memory_db import MemoryDB
from prompt_builder import build_prompt

# Optional audio-related imports are performed lazily inside `main` to avoid
# crashing import-time in environments without audio or required native libs.
# from voice import record_and_transcribe
# from tts import speak

# Initialize a dedicated memory instance (persistent DB file)
memory = MemoryDB()


def is_explicit_memory_command(text: str) -> bool:
    triggers = [
        "remember this",
        "save this",
        "from now on remember",
        "always remember",
    ]
    t = text.lower()
    return any(k in t for k in triggers)


def maybe_save_explicit(user_text: str, assistant_text: str, source: str = "text"):
    """Add the conversational turn and save long-term memory if the user explicitly asked.

    Respect source: never auto-save from voice. Also enforce disallowed content rules.
    """
    try:
        add_turn(user_text, assistant_text)
    except Exception:
        # best-effort fallback directly to memory DB
        try:
            memory.add_short_term("user", user_text)
            memory.add_short_term("assistant", assistant_text)
        except Exception:
            pass

    # Save long-term memory ONLY on explicit commands and only for non-voice sources
    if is_explicit_memory_command(user_text) and source != "voice":
        try:
            # memory.add_long_term will raise ValueError if content is disallowed
            memory.add_long_term(user_text, source="explicit")
        except Exception:
            # swallow to avoid crashing the assistant for disallowed content
            pass


def handle_user_input(user_text: str, max_tokens: int | None = None, source: str = "text") -> str:
    """Create a compact prompt using memory and call the LLM, then update memory."""
    try:
        prefs = memory.get_prefs()
        short_rows = memory.get_short_term(limit=6)
        # Respect the memory_enabled pref (defaults to true)
        memory_enabled = str(prefs.get("memory_enabled", "true")).lower() == "true"
        long_rows = memory.get_long_term(limit=8) if memory_enabled else []

        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()

        prompt_context = build_prompt(
            system_prompt=system_prompt,
            user_message=user_text,
            prefs=prefs,
            short_term=short_rows,
            long_term=long_rows,
            include_system=False,
        )

        if max_tokens is not None:
            answer = think(user_text, extra_context=prompt_context, max_tokens=max_tokens)
        else:
            answer = think(user_text, extra_context=prompt_context)
    except Exception:
        # fallback to older simple context
        memory_context = get_context()
        extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
        answer = think(user_text, extra_context=extra_context)

    # persist short-term and possibly explicit long-term memory
    maybe_save_explicit(user_text, answer, source=source)

    return answer

# Safe, lazy TTS wrapper. If TTS dependencies are missing, this becomes a no-op.
_say_func = None

def _speak(text, voice=None):
    global _say_func
    if _say_func is None:
        try:
            from tts import speak as _s
            _say_func = _s
        except Exception:
            _say_func = lambda *args, **kwargs: None
    try:
        if voice:
            _say_func(text, voice=voice)
        else:
            _say_func(text)
    except Exception:
        # Swallow TTS runtime errors to keep the text API robust
        pass


def main():
    # Load persisted preferences
    OPINION_MODE = get_pref("opinion_mode", OPINION_MODE)

    print("AI Assistant ready (type 'exit' to quit)\n")

    while True:
        # Input (voice or text)
        if VOICE_INPUT:
            try:
                from voice import record_and_transcribe
                raw_input = record_and_transcribe(6)
                source = "voice"
                print("You:", raw_input)
            except Exception:
                print("DEBUG | voice input unavailable, falling back to text input.")
                raw_input = input("You: ")
                source = "text"
        else:
            raw_input = input("You: ")
            source = "text"

        user_input = autocorrect_text(raw_input)
        if raw_input != user_input:
            print(f"DEBUG | autocorrected: '{raw_input}' → '{user_input}'")
        # Soft grammar cleanup: normalize whitespace and lowercase (does not rewrite content)
        user_input = user_input.strip().lower()
        if user_input.lower() == "exit":
            break

        # 🚫 Block junk input
        if len(user_input) < 4 or (user_input.isalpha() and user_input.lower() == user_input):
            print("AI: Please enter a meaningful request.")
            continue

        route = route_intent(user_input)
        intent = route.get("intent")
        print("DEBUG | Intent:", intent)

       

        if intent == "adult_recommendation":
            movies = load_adult_movies()

            context = "\n".join(movies)

            prompt = (
                "From the following list of adult / NSFW movies, "
                "select up to 10 relevant titles.\n\n"
                "Movie list:\n"
                f"{context}\n\n"
                "Rules:\n"
                "- Use ONLY movies from the list\n"
                "- Only output titles\n"
                "- No explanations\n"
                "- No substitutions"
            )

            memory_context = get_context()
            extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
            answer = think(user_input, extra_context=extra_context + prompt)
            print("AI:", answer)
            maybe_save_explicit(user_input, answer, source=source)
            if VOICE_OUTPUT:
                if any(ch in user_input for ch in "అఆఇఈఉ"):
                    _speak(answer, voice="te_IN")
                else:
                    _speak(answer, voice="en_US-lessac")

        elif intent == "file_open":
            result = open_file(route.get("path", ""))
            print("AI:", result)
            maybe_save_explicit(user_input, result, source=source)
            if VOICE_OUTPUT:
                _speak(result, voice="en_US-lessac")

        elif intent == "app_open":
            result = open_app(route.get("app", ""))
            print("AI:", result)
            maybe_save_explicit(user_input, result, source=source)
            if VOICE_OUTPUT:
                _speak(result, voice="en_US-lessac")

        elif intent == "opinion_analysis":
            # 1️⃣ Get external context
            results = web_search(user_input, max_results=6)

            if len(results) < 2:
                print("AI: Not enough reliable information to form a reasoned opinion.")
                continue

            evidence = "\n".join(f"- {r['body']}" for r in results)

            # 2️⃣ Mode-specific instruction
            if OPINION_MODE == "blunt":
                style = """
BLUNT MODE — NON-NEGOTIABLE RULES:

- START with harm or failure. No praise.
- DO NOT use: strength, weakness, interpretation, misinterpretation, reform, dialogue, coexistence, scholars.
- DO NOT quote scripture, surveys, studies, or theology.
- DO NOT generalize belief; analyze enforcement and outcomes.
- Focus ONLY on law, state action, institutions, or organized power.
- If responsibility is unclear, say so explicitly.
- END with a firm judgment. No solutions.
- Short, declarative sentences.

FORMAT RULES:
- Do NOT use numbered or bulleted lists.
- Use short paragraphs only.
- Do NOT include the phrases: 'it is important to note', 'not all interpretations', 'under any circumstances', 'it is essential to', 'should be addressed'.
- End with a judgment about power or enforcement, not values or policy advice.
"""

                prompt = f"""
{style}

Analyze the real-world outcomes produced by religious authority, law, or institutional enforcement.

Topic:
{user_input}

Evidence:
{evidence}

Required structure:
1. Describe the harm or failure.
2. Identify who enforced it (only if supported by evidence).
3. Describe the consequences.
4. End with a judgment about power or enforcement.
"""

            elif OPINION_MODE == "critical":
                style = """
CRITICAL MODE:

- Analyze power structures, legal mechanisms, and institutional enforcement.
- No individual blame.
- No harmony language.
- End with a firm analytical conclusion.
"""

                prompt = f"""
{style}

Analyze the topic critically.

Topic:
{user_input}

Evidence:
{evidence}
"""

            else:  # balanced / academic
                style = """
BALANCED MODE:

- Neutral tone.
- One strength.
- One weakness.
- Real-world consequences.
- No personal judgment unless asked.
"""

                prompt = f"""
{style}

Analyze the topic objectively.

Topic:
{user_input}

Evidence:
{evidence}
"""

            # 3️⃣ Memory injection
            mem_context = get_context()

            combined_context = (
                f"Conversation context:\n{mem_context}\n\n{prompt}"
                if mem_context else prompt
            )

            # 4️⃣ Generate
            memory_context = get_context()
            extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
            answer = think(
                user_input,
                extra_context=extra_context + prompt,
                max_tokens=320
            )
            print("AI:", answer)
            maybe_save_explicit(user_input, answer, source=source)
            set_pref("opinion_mode", OPINION_MODE)
            # Voice output (optional)
            if VOICE_OUTPUT:
                # simple language heuristic: detect Telugu characters as an example
                if any(ch in user_input for ch in "అఆఇఈఉ"):
                    _speak(answer, voice="te_IN")
                else:
                    _speak(answer, voice="en_US-lessac")

        elif intent == "search_and_explain":
            results = web_search(user_input, max_results=8)

            # Detect likely typo / generic placeholder queries
            tokens = user_input.lower().split()

            generic_tokens = {"xyz", "abc", "test", "testtest", "protesttest"}

            if any(t in generic_tokens for t in tokens):
                print(
                    "AI: The topic you asked about seems unclear or possibly a placeholder. "
                    "Please provide a specific name, place, or event."
                )
                continue

            if not results:
                print("AI: No useful information found.")
                continue

            if len(results) < 2:
                print("AI: I couldn't find reliable information about this topic. "
                      "It may be unclear, poorly documented, or incorrectly named.")
                continue

            # Improved ambiguity detection for "who is" queries
            if user_input.lower().startswith("who is"):
                titles = [r["title"].lower() for r in results if r.get("title")]

                # If titles strongly converge on the same name → NOT ambiguous
                name = user_input.lower().replace("who is", "").strip()

                matching = sum(1 for t in titles if name in t)

                if matching < max(2, len(titles) // 2):
                    print(
                        "AI: The name you asked about may refer to multiple people or entities. "
                        "Please specify which one you mean (profession, country, or context)."
                    )
                    continue

            context = ""
            for i, r in enumerate(results, start=1):
                context += f"Source {i}:\nTitle: {r['title']}\nInfo: {r['body']}\n\n"

            is_person_query = user_input.lower().startswith("who is")

            if is_person_query:
                prompt = (
                    "Give a concise biographical summary in 3–4 complete sentences.\n"
                    "Do not start a new idea in the last sentence.\n"
                    "Do not include anecdotes unless widely known.\n\n"
                    f"{context}"
                )
            else:
                prompt = (
                    "Using the sources below:\n"
                    "1. Identify the main causes mentioned by most sources\n"
                    "2. Mention secondary causes only if they appear in multiple sources\n"
                    "3. Ignore isolated or symbolic details\n"
                    "4. Briefly note disagreements if they affect the main conclusion\n\n"
                    f"{context}"
                )

            long_form = any(
                k in user_input.lower()
                for k in ["why", "causes", "reasons", "protesting", "movement"]
            )

            # choose tokens: 140 for person queries (short bios), 200 for long_form, 120 default
            tokens = 140 if is_person_query else (200 if long_form else 120)

            memory_context = get_context()
            extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
            answer = think(
                user_input,
                extra_context=extra_context + prompt,
                max_tokens=tokens
            )
            print("AI:", answer)
            maybe_save_explicit(user_input, answer, source=source)
            if VOICE_OUTPUT:
                if any(ch in user_input for ch in "అఆఇఈఉ"):
                    _speak(answer, voice="te_IN")
                else:
                    _speak(answer, voice="en_US-lessac")

        else:
            # Use structured memory-aware prompt + automatic short-term storage
            answer = handle_user_input(user_input, source=source)
            print("AI:", answer)
            if VOICE_OUTPUT:
                if any(ch in user_input for ch in "అఆఇఈఉ"):
                    _speak(answer, voice="te_IN")
                else:
                    _speak(answer, voice="en_US-lessac")

def handle_query(user_input: str, source: str = "text") -> str:
    """Run routing + appropriate action for a single user input and return the assistant's text response.

    This is a UI-friendly backend entrypoint (no direct TTS playback).

    The `source` parameter should be 'text' or 'voice'. Voice inputs will never trigger automatic long-term memory saves.
    """
    route = route_intent(user_input)
    intent = route.get("intent")

    # adult recommendation
    if intent == "adult_recommendation":
        movies = load_adult_movies()
        context = "\n".join(movies)
        prompt = (
            "From the following list of adult / NSFW movies, "
            "select up to 10 relevant titles.\n\n"
            "Movie list:\n"
            f"{context}\n\n"
            "Rules:\n"
            "- Use ONLY movies from the list\n"
            "- Only output titles\n"
            "- No explanations\n"
            "- No substitutions"
        )
        memory_context = get_context()
        extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
        answer = think(prompt, extra_context=extra_context)
        maybe_save_explicit(user_input, answer, source=source)
        return answer

    # open file
    if intent == "file_open":
        result = open_file(route.get("path", ""))
        maybe_save_explicit(user_input, result, source=source)
        return result

    # open app
    if intent == "app_open":
        result = open_app(route.get("app", ""))
        maybe_save_explicit(user_input, result, source=source)
        return result

    # opinion analysis
    if intent == "opinion_analysis":
        results = web_search(user_input, max_results=6)
        if len(results) < 2:
            return "Not enough reliable information to form a reasoned opinion."

        evidence = "\n".join(f"- {r['body']}" for r in results)

        if OPINION_MODE == "blunt":
            style = """
BLUNT MODE — NON-NEGOTIABLE RULES:

- START with harm or failure. No praise.
- DO NOT use: strength, weakness, interpretation, misinterpretation, reform, dialogue, coexistence, scholars.
- DO NOT quote scripture, surveys, studies, or theology.
- DO NOT generalize belief; analyze enforcement and outcomes.
- Focus ONLY on law, state action, institutions, or organized power.
- If responsibility is unclear, say so explicitly.
- END with a firm judgment. No solutions.
- Short, declarative sentences.

FORMAT RULES:
- Do NOT use numbered or bulleted lists.
- Use short paragraphs only.
- Do NOT include the phrases: 'it is important to note', 'not all interpretations', 'under any circumstances', 'it is essential to', 'should be addressed'.
- End with a judgment about power or enforcement, not values or policy advice.
"""

            prompt = f"""
{style}

Analyze the real-world outcomes produced by religious authority, law, or institutional enforcement.

Topic:
{user_input}

Evidence:
{evidence}

Required structure:
1. Describe the harm or failure.
2. Identify who enforced it (only if supported by evidence).
3. Describe the consequences.
4. End with a judgment about power or enforcement.
"""

        elif OPINION_MODE == "critical":
            style = """
CRITICAL MODE:

- Analyze power structures, legal mechanisms, and institutional enforcement.
- No individual blame.
- No harmony language.
- End with a firm analytical conclusion.
"""

            prompt = f"""
{style}

Analyze the topic critically.

Topic:
{user_input}

Evidence:
{evidence}
"""

        else:  # balanced / academic
            style = """
BALANCED MODE:

- Neutral tone.
- One strength.
- One weakness.
- Real-world consequences.
- No personal judgment unless asked.
"""

            prompt = f"""
{style}

Analyze the topic objectively.

Topic:
{user_input}

Evidence:
{evidence}
"""

        memory_context = get_context()
        extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
        answer = think(user_input, extra_context=extra_context + prompt, max_tokens=320)
        maybe_save_explicit(user_input, answer, source=source)
        set_pref("opinion_mode", OPINION_MODE)
        return answer

    # search and explain
    if intent == "search_and_explain":
        results = web_search(user_input, max_results=8)
        tokens = user_input.lower().split()
        generic_tokens = {"xyz", "abc", "test", "testtest", "protesttest"}
        if any(t in generic_tokens for t in tokens):
            return "The topic you asked about seems unclear or possibly a placeholder. Please provide a specific name, place, or event."

        if not results:
            return "No useful information found."

        if len(results) < 2:
            return "I couldn't find reliable information about this topic. It may be unclear, poorly documented, or incorrectly named."

        # who-is ambiguity detection
        if user_input.lower().startswith("who is"):
            titles = [r["title"].lower() for r in results if r.get("title")]
            name = user_input.lower().replace("who is", "").strip()
            matching = sum(1 for t in titles if name in t)
            if matching < max(2, len(titles) // 2):
                return "The name you asked about may refer to multiple people or entities. Please specify which one you mean (profession, country, or context)."

        context = ""
        for i, r in enumerate(results, start=1):
            context += f"Source {i}:\nTitle: {r['title']}\nInfo: {r['body']}\n\n"

        is_person_query = user_input.lower().startswith("who is")
        if is_person_query:
            prompt = (
                "Give a concise biographical summary in 3–4 complete sentences.\n"
                "Do not start a new idea in the last sentence.\n"
                "Do not include anecdotes unless widely known.\n\n"
                f"{context}"
            )
        else:
            prompt = (
                "Using the sources below:\n"
                "Identify the main causes mentioned by most sources\n"
                "Mention secondary causes only if they appear in multiple sources\n"
                "Ignore isolated or symbolic details\n"
                "Briefly note disagreements if they affect the main conclusion\n\n"
                f"{context}"
            )

        long_form = any(k in user_input.lower() for k in ["why", "causes", "reasons", "protesting", "movement"])
        tokens = 140 if is_person_query else (200 if long_form else 120)

        memory_context = get_context()
        extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
        answer = think(user_input, extra_context=extra_context + prompt, max_tokens=tokens)
        maybe_save_explicit(user_input, answer, source=source)
        return answer

    # fallback — prefer structured prompt when possible
    try:
        from prompt_builder import build_prompt
        from memory import get_prefs, get_long_term, get_short_term_rows

        prefs = get_prefs()
        short_rows = get_short_term_rows()
        memory_enabled = str(prefs.get("memory_enabled", "true")).lower() == "true"
        long_rows = get_long_term() if memory_enabled else []

        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()

        prompt_context = build_prompt(system_prompt, user_input, prefs, short_rows, long_rows, include_system=False)
        answer = think(user_input, extra_context=prompt_context)
    except Exception:
        memory_context = get_context()
        extra_context = f"Conversation context:\n{memory_context}\n\n" if memory_context else ""
        answer = think(user_input, extra_context=extra_context)

    maybe_save_explicit(user_input, answer, source=source)
    return answer


def process_input(user_input: str, mode: str, source: str = "text"):
    """External UI wrapper: set mode and process input through the backend."""
    global OPINION_MODE
    OPINION_MODE = mode
    set_pref("opinion_mode", OPINION_MODE)
    return handle_query(user_input, source=source)


if __name__ == "__main__":
    main()
