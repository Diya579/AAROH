import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database import SessionLocal
from models import (
    Interaction,
    TextFeature,
    VoiceFeature,
    EngagementFeature
)

from extract_features import extract_all_features


def save_interaction_features(db, interaction):

    features = extract_all_features(interaction)

    # -------------------------
    # TEXT FEATURES
    # -------------------------

    text_feature = TextFeature(
        interaction_id=interaction.id,

        distress_intensity=features[
            "text_distress_intensity"
        ],

        fear=features["fear"],
        intimidation=features["intimidation"],
        hopelessness=features["hopelessness"],
        isolation=features["isolation"],
        help_seeking=features["help_seeking"],

        # Prototype language confidence
        language_confidence=1.0
    )

    # -------------------------
    # VOICE FEATURES
    # -------------------------

    voice_feature = VoiceFeature(
        interaction_id=interaction.id,

        # We don't have actual audio yet.
        speech_rate=None,
        pause_ratio=None,
        response_latency=None,
        pitch_variability=None,
        energy_variation=None,
        audio_quality=None,
        baseline_deviation=None
    )

    # -------------------------
    # ENGAGEMENT FEATURES
    # -------------------------

    engagement_feature = EngagementFeature(
        interaction_id=interaction.id,

        response_delay=None,

        missed_checkin=(
            features["missed_checkin"] == 1
        ),

        engagement_change=None
    )

    db.add(text_feature)
    db.add(voice_feature)
    db.add(engagement_feature)


def main():

    db = SessionLocal()

    try:

        interactions = (
            db.query(Interaction)
            .order_by(
                Interaction.case_id,
                Interaction.interaction_date
            )
            .all()
        )

        print(
            f"Found {len(interactions)} interactions."
        )

        # Remove previously generated features
        # so the script can safely be rerun.

        db.query(TextFeature).delete()
        db.query(VoiceFeature).delete()
        db.query(EngagementFeature).delete()

        db.commit()

        for index, interaction in enumerate(
            interactions,
            start=1
        ):

            save_interaction_features(
                db,
                interaction
            )

            print(
                f"Processed {index}/{len(interactions)}"
            )

        db.commit()

        print(
            "\nFeature extraction completed successfully."
        )

    except Exception as e:

        db.rollback()

        print(
            "\nERROR:",
            e
        )

        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()