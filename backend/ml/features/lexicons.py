"""Centralized multilingual lexicons for observable text indicators (Slice 2.2).

Single source of truth for English, Hindi (Devanagari), and Hinglish (Romanized)
lexicons. Extractor modules consume these dictionaries without hard-coding keywords.
"""

from __future__ import annotations

import re
from typing import Mapping

# -------------------------------------------------------------------------
# DISTRESS LEXICONS
# -------------------------------------------------------------------------
DISTRESS_LEXICONS: Mapping[str, tuple[str, ...]] = {
    "fear": (
        # English
        "afraid",
        "scared",
        "fear",
        "frightened",
        "terrified",
        "worried",
        "panic",
        "horrified",
        "dread",
        "unsafe",
        # Hindi (Devanagari)
        "डर",
        "भय",
        "खौफ",
        "घबराहट",
        "सहमा",
        "डरा",
        "आतंक",
        "कांप",
        "चिंता",
        "असुरक्षित",
        # Hinglish
        "darr",
        "dar",
        "khauf",
        "ghabrahat",
        "dahshat",
        "sehme",
    ),
    "hopelessness": (
        # English
        "hopeless",
        "nothing will change",
        "no point",
        "give up",
        "cannot continue",
        "can't continue",
        "lost all hope",
        "meaningless",
        "no future",
        # Hindi (Devanagari)
        "निराश",
        "नाउम्मीद",
        "कोई उम्मीद नहीं",
        "सब खत्म",
        "कुछ नहीं बदलेगा",
        "हार मान",
        "बर्दाश्त नहीं",
        "कोई फायदा नहीं",
        # Hinglish
        "koi umeed nahi",
        "sab khatam",
        "kuch nahi badlega",
        "haar maan",
        "bardasht nahi",
    ),
    "isolation": (
        # English
        "alone",
        "isolated",
        "nobody",
        "no one",
        "no support",
        "no one understands",
        "abandoned",
        "lonely",
        "neglected",
        # Hindi (Devanagari)
        "अकेला",
        "तन्हा",
        "कोई नहीं",
        "कोई सहारा नहीं",
        "अलग-थलग",
        "अकेलापन",
        "बेसहारा",
        # Hinglish
        "akela",
        "akele",
        "akelapan",
        "tanha",
        "koi nahi hai",
        "koi sahara nahi",
    ),
    "helplessness": (
        # English
        "helpless",
        "unable to do anything",
        "trapped",
        "nowhere to go",
        "no way out",
        "cannot escape",
        "powerless",
        # Hindi (Devanagari)
        "बेबस",
        "लाचार",
        "मजबूर",
        "कोई रास्ता नहीं",
        "असहाय",
        "फंसा हुआ",
        "कुछ नहीं कर सकता",
        # Hinglish
        "bebas",
        "lachar",
        "majboor",
        "fasa hua",
        "fasi hui",
        "koi rasta nahi",
    ),
    "intimidation": (
        # English
        "threat",
        "threatened",
        "intimidate",
        "intimidated",
        "pressured",
        "warning",
        "they will come",
        "they know",
        "stalked",
        "blackmail",
        # Hindi (Devanagari)
        "धमकी",
        "धमकाया",
        "डराना",
        "दबाव",
        "चेतावनी",
        "पीछा",
        "ब्लैकमेल",
        "वे आ जाएंगे",
        "जान से मारने",
        # Hinglish
        "dhamki",
        "dhamkaya",
        "dabav",
        "blackmail",
        "jaan se maar",
        "picha kar rahe",
    ),
    "sadness": (
        # English
        "sad",
        "depressed",
        "grief",
        "crying",
        "sorrow",
        "tears",
        "miserable",
        "weeping",
        "despair",
        # Hindi (Devanagari)
        "उदास",
        "दुख",
        "गम",
        "रोना",
        "आंसू",
        "गमगीन",
        "मायूस",
        "कष्ट",
        "पीड़ा",
        # Hinglish
        "udaas",
        "udas",
        "dukh",
        "rona",
        "aansu",
        "ro rahi",
        "ro raha",
        "mayus",
    ),
    "anxiety": (
        # English
        "anxious",
        "anxiety",
        "nervous",
        "restless",
        "trembling",
        "racing heart",
        "overwhelmed",
        "tense",
        # Hindi (Devanagari)
        "बेचैनी",
        "व्याकुल",
        "तनाव",
        "कंपकंपी",
        "उलझन",
        "घबराया",
        # Hinglish
        "bechaini",
        "bechain",
        "tension",
        "stress",
        "ghabrana",
        "uljhan",
    ),
}

# -------------------------------------------------------------------------
# HELP-SEEKING LEXICONS
# -------------------------------------------------------------------------
HELP_SEEKING_LEXICONS: Mapping[str, tuple[str, ...]] = {
    "asking_for_help": (
        # English
        "help",
        "need help",
        "please help",
        "save me",
        "assist",
        "rescue",
        # Hindi (Devanagari)
        "मदद",
        "सहायता",
        "बचाओ",
        "मदद चाहिए",
        "प्लीज हेल्प",
        "गुहार",
        # Hinglish
        "madad",
        "bachao",
        "help karo",
        "help chahiye",
        "madad chahiye",
    ),
    "requesting_support": (
        # English
        "support",
        "need someone",
        "talk to someone",
        "counsellor",
        "counselling",
        "counseling",
        "shelter",
        "protection",
        "legal aid",
        # Hindi (Devanagari)
        "सहारा",
        "परामर्श",
        "किसी से बात",
        "आश्रय",
        "सुरक्षा",
        "वकील",
        "कानूनी मदद",
        # Hinglish
        "sahara",
        "kisi se baat",
        "counsellor",
        "counseling",
        "protection",
        "legal aid",
        "shelter",
    ),
    "emergency_language": (
        # English
        "emergency",
        "call police",
        "hospital",
        "ambulance",
        "urgent",
        "dying",
        "suicide",
        "attack",
        "bleeding",
        # Hindi (Devanagari)
        "आपातकाल",
        "पुलिस बुलाओ",
        "अस्पताल",
        "जान का खतरा",
        "हमला",
        "एम्बुलेंस",
        # Hinglish
        "emergency",
        "police bulao",
        "hospital",
        "attack",
        "jaan ka khatra",
        "ambulance",
    ),
}

# -------------------------------------------------------------------------
# SAFETY LEXICONS
# -------------------------------------------------------------------------
SAFETY_LEXICONS: Mapping[str, tuple[str, ...]] = {
    "urgency": (
        # English
        "urgent",
        "immediately",
        "right now",
        "as soon as possible",
        "asap",
        "running out of time",
        "critical",
        # Hindi (Devanagari)
        "तुरंत",
        "फौरन",
        "अभी",
        "तत्काल",
        "जल्द से जल्द",
        "समय नहीं है",
        # Hinglish
        "turant",
        "foran",
        "abhi ke abhi",
        "jaldi",
        "asap",
        "immediately",
    ),
    "danger_related_wording": (
        # English
        "danger",
        "unsafe",
        "hurt",
        "killed",
        "weapon",
        "knife",
        "gun",
        "poison",
        "violence",
        "abuse",
        "beat",
        "hitting",
        # Hindi (Devanagari)
        "खतरा",
        "असुरक्षित",
        "मारना",
        "जानलेवा",
        "हथियार",
        "बंदूक",
        "चाकू",
        "हिंसा",
        "मारपीट",
        "प्रताड़ना",
        # Hinglish
        "khatra",
        "maar",
        "maarpeet",
        "chaku",
        "bandook",
        "hinsa",
        "violence",
        "harm",
    ),
}


def find_matched_terms(text: str, patterns: tuple[str, ...]) -> tuple[str, ...]:
    """Finds all unique matching terms and phrases in text deterministically.

    Handles single words as well as multi-word phrases. Word boundaries are
    respected where applicable to avoid false substring matches.
    """
    if not text:
        return ()

    text_lower = text.lower()
    matches: set[str] = set()

    for pattern in patterns:
        pat_lower = pattern.lower().strip()
        if not pat_lower:
            continue

        # If pattern is multi-word, check exact substring presence
        if " " in pat_lower:
            if pat_lower in text_lower:
                matches.add(pattern)
        else:
            # Single word: use regex with boundary checks for Latin words,
            # or boundary/space checks for Indic scripts
            regex_pat = rf"(?:(?<=^)|(?<=\s)|(?<=[^\w]))" + re.escape(pat_lower) + rf"(?:(?=$)|(?=\s)|(?=[^\w]))"
            if re.search(regex_pat, text_lower):
                matches.add(pattern)

    return tuple(sorted(matches))
