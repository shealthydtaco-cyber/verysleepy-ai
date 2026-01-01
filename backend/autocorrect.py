# autocorrect.py
from symspellpy import SymSpell, Verbosity
import os

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

# Resolve dictionary path without pkg_resources
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(
    BASE_DIR,
    "frequency_dictionary_en_82_765.txt"
)

# Download dictionary once if missing
if not os.path.exists(DICT_PATH):
    raise FileNotFoundError(
        "Missing frequency_dictionary_en_82_765.txt. "
        "Download it from symspellpy GitHub and place it next to autocorrect.py"
    )

sym_spell.load_dictionary(DICT_PATH, term_index=0, count_index=1)


def autocorrect_text(text: str) -> str:
    words = text.split()
    corrected = []

    for word in words:
        suggestions = sym_spell.lookup(
            word,
            Verbosity.CLOSEST,
            max_edit_distance=2
        )
        corrected.append(suggestions[0].term if suggestions else word)

    return " ".join(corrected)
