def normalize_1_to_5(value):

    if value is None:
        return None

    value = max(1, min(5, value))

    return round(
        (value - 1) / 4,
        3
    )


def extract_behavioural_features(
    safety_response,
    sleep_disruption,
    fear_level,
    social_support
):

    safety = normalize_1_to_5(safety_response)
    sleep = normalize_1_to_5(sleep_disruption)
    fear = normalize_1_to_5(fear_level)
    support = normalize_1_to_5(social_support)

    features = {

        # Higher = worse
        "safety_distress": (
            None if safety is None else round(1 - safety, 3)
        ),

        "sleep_disturbance": sleep,

        "fear_intensity": fear,

        # Higher = worse
        "low_social_support": (
            None if support is None else round(1 - support, 3)
        )
    }

    available = [
        value for value in features.values()
        if value is not None
    ]

    if available:

        features["behavioural_distress"] = round(
            sum(available) / len(available),
            3
        )

    else:

        features["behavioural_distress"] = None

    return features