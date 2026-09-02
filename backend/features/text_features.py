import re


# Prototype lexicons.
# These are transparent baseline signals, NOT clinical diagnoses.

ENGLISH_PATTERNS = {
    "fear": [
        "afraid",
        "scared",
        "fear",
        "frightened",
        "terrified",
        "worried",
        "unsafe",
        "danger"
    ],

    "intimidation": [
        "threat",
        "threatened",
        "intimidate",
        "pressured",
        "warning",
        "they will come",
        "they know"
    ],

    "hopelessness": [
        "hopeless",
        "nothing will change",
        "no point",
        "give up",
        "cannot continue",
        "can't continue"
    ],

    "isolation": [
        "alone",
        "isolated",
        "nobody",
        "no one",
        "no support",
        "no one understands"
    ],

    "help_seeking": [
        "help",
        "need someone",
        "talk to someone",
        "please help",
        "support",
        "counselling",
        "counseling"
    ]
}


def normalize_text(text):
    if not text:
        return ""

    text = text.lower().strip()

    # Normalize repeated whitespace
    text = re.sub(r"\s+", " ", text)

    return text


def count_matches(text, patterns):
    count = 0

    for phrase in patterns:
        if phrase in text:
            count += 1

    return count


def extract_text_features(text):

    text = normalize_text(text)

    if not text:
        return {
            "text_available": 0,
            "text_length": 0,
            "fear": 0.0,
            "intimidation": 0.0,
            "hopelessness": 0.0,
            "isolation": 0.0,
            "help_seeking": 0.0,
            "text_distress_intensity": 0.0
        }

    features = {}

    features["text_available"] = 1
    features["text_length"] = len(text)

    for category, patterns in ENGLISH_PATTERNS.items():

        matches = count_matches(text, patterns)

        # Binary-ish normalized score for prototype
        features[category] = min(
            matches / 2.0,
            1.0
        )

    # Overall textual distress signal.
    #
    # This is intentionally transparent and will later
    # be replaced/augmented by a trained NLP model.

    distress_components = [
        features["fear"],
        features["intimidation"],
        features["hopelessness"],
        features["isolation"]
    ]

    features["text_distress_intensity"] = round(
        sum(distress_components) / len(distress_components),
        3
    )

    return features