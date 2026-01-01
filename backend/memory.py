from memory_db import MemoryDB

memory = MemoryDB()

# User prefs

def set_pref(key: str, value: str):
    memory.set_pref(key, value)


def get_pref(key: str, default=None):
    prefs = memory.get_prefs()
    return prefs.get(key, default)

# Short-term / conversation-level

def add_turn(user_text: str, assistant_text: str):
    # store both sides as short-term memory
    memory.add_short_term("user", user_text)
    memory.add_short_term("assistant", assistant_text)


def get_context(limit=6):
    # return a readable joined context string (most recent last)
    rows = memory.get_short_term(limit=limit)
    if not rows:
        return ""
    parts = []
    for r in rows:
        # r may be sqlite Row-like with 'role' and 'content'
        role = r["role"] if isinstance(r, dict) or hasattr(r, "__getitem__") else getattr(r, "role", "user")
        content = r["content"] if isinstance(r, dict) or hasattr(r, "__getitem__") else getattr(r, "content", "")
        parts.append(f"{role.capitalize()}: {content}")
    return "\n".join(parts)


def get_short_term_rows(limit=6):
    return memory.get_short_term(limit=limit)

# Long-term

def is_disallowed_memory_content(text: str):
    """Return a reason string if the content should never be stored, else None."""
    if not text:
        return None
    t = text.lower()
    # Simple keyword-based heuristics
    politics_keywords = ["politic", "election", "vote", "govt", "government", "president", "senate", "congress", "party"]
    religion_keywords = ["religion", "god", "jesus", "christ", "islam", "muslim", "buddh", "hindu", "faith", "pray", "church", "mosque", "synagogue"]
    nsfw_keywords = ["porn", "sex", "nsfw", "xxx", "adult", "nude", "naked"]
    opinion_phrases = ["i think", "in my opinion", "i believe", "my view", "i feel", "i'm convinced", "should", "ought to"]

    for k in politics_keywords:
        if k in t:
            return "politics"
    for k in religion_keywords:
        if k in t:
            return "religion"
    for k in nsfw_keywords:
        if k in t:
            return "nsfw"
    for p in opinion_phrases:
        if p in t:
            return "opinion"
    return None


def add_long_term(text: str, source: str = "explicit"):
    reason = is_disallowed_memory_content(text)
    if reason:
        raise ValueError(f"Content disallowed for memory: {reason}")
    memory.add_long_term(text, source=source)


def get_long_term(limit=10):
    return memory.get_long_term(limit=limit)

def delete_long_term(entry_id: int):
    memory.delete_long_term(entry_id)

# Expose prefs map
def get_prefs():
    return memory.get_prefs()


def remember_last_user_message(last_user_text: str):
    """Convenience wrapper to explicitly remember the last user message."""
    # delegate to add_long_term which performs validation
    add_long_term(last_user_text, source="explicit")


def set_memory_enabled(enabled: bool):
    memory.set_pref("memory_enabled", "true" if enabled else "false")


def get_memory_snapshot():
    return {"prefs": memory.get_prefs(), "facts": memory.get_long_term(limit=50)}


def forget_memory_item(item_id: int):
    memory.delete_long_term(item_id)


# Utility: clear memory

def clear_all_memory():
    conn = memory.conn
    conn.execute("DELETE FROM short_term_memory")
    conn.execute("DELETE FROM long_term_memory")
    conn.execute("DELETE FROM user_prefs")
    conn.commit()

# Utility: clear memory

def clear_all_memory():
    conn = memory.conn
    conn.execute("DELETE FROM short_term_memory")
    conn.execute("DELETE FROM long_term_memory")
    conn.execute("DELETE FROM user_prefs")
    conn.commit()