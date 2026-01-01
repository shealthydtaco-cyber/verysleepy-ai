def build_prompt(
    system_prompt: str,
    user_message: str,
    prefs: dict,
    short_term: list,
    long_term: list,
    include_system: bool = True,
) -> str:

    parts = []

    if include_system:
        parts.append(system_prompt.strip())

    if prefs:
        parts.append("\nUser Preferences:")
        for k, v in prefs.items():
            parts.append(f"- {k}: {v}")

    if long_term:
        parts.append("\nRelevant Stored Facts:")
        for fact in long_term:
            # fact may be a string or a dict with a 'content' field
            if isinstance(fact, dict):
                parts.append(f"- {fact.get('content')}")
            else:
                parts.append(f"- {fact}")

    if short_term:
        parts.append("\nRecent Context:")
        for row in short_term:
            parts.append(f"{row['role'].capitalize()}: {row['content']}")

    parts.append("\nCurrent User Message:")
    parts.append(f"User: {user_message}")

    parts.append("\nAssistant:")

    return "\n".join(parts)
