def extract_engagement_features(
    response_completed,
    voice_available,
    data_quality
):

    response_completed = bool(response_completed)
    voice_available = bool(voice_available)

    return {

        "response_completed": int(
            response_completed
        ),

        "missed_checkin": int(
            not response_completed
        ),

        "voice_available": int(
            voice_available
        ),

        "data_quality_good": int(
            data_quality == "good"
        ),

        "data_quality_insufficient": int(
            data_quality == "insufficient"
        )
    }