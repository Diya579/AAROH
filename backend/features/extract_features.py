import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from text_features import extract_text_features
from behavioural_features import (
    extract_behavioural_features
)
from engagement_features import (
    extract_engagement_features
)


def extract_all_features(interaction):

    text_features = extract_text_features(
        interaction.text_response
    )

    behavioural_features = extract_behavioural_features(
        interaction.safety_response,
        interaction.sleep_disruption,
        interaction.fear_level,
        interaction.social_support
    )

    engagement_features = extract_engagement_features(
        interaction.response_completed,
        interaction.voice_available,
        interaction.data_quality
    )

    features = {}

    features.update(text_features)
    features.update(behavioural_features)
    features.update(engagement_features)

    return features