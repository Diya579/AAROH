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
    EngagementFeature,
    DistressState
)

from risk.risk_scoring import calculate_risk


# ==========================================
# TRAJECTORY CALCULATION
# ==========================================

def calculate_trajectory(current, previous):
    """
    Determine distress trajectory based on
    change from the previous interaction.
    """

    if previous is None:
        return "STABLE"

    change = current - previous

    if change >= 0.15:
        return "RAPIDLY_WORSENING"

    elif change >= 0.05:
        return "WORSENING"

    elif change <= -0.15:
        return "RAPIDLY_IMPROVING"

    elif change <= -0.05:
        return "IMPROVING"

    else:
        return "STABLE"


# ==========================================
# MAIN
# ==========================================

def main():

    db = SessionLocal()

    try:

        # ----------------------------------
        # GET ALL INTERACTIONS
        # ----------------------------------

        interactions = (
            db.query(Interaction)
            .order_by(
                Interaction.case_id,
                Interaction.interaction_date
            )
            .all()
        )

        print(
            f"\nFound {len(interactions)} interactions.\n"
        )

        # ----------------------------------
        # REMOVE PREVIOUSLY GENERATED STATES
        # ----------------------------------

        db.query(DistressState).delete()
        db.commit()

        print(
            "Previous distress states cleared.\n"
        )

        # ----------------------------------
        # COUNTERS
        # ----------------------------------

        total = 0
        low = 0
        moderate = 0
        high = 0

        # ----------------------------------
        # LONGITUDINAL TRACKING
        # ----------------------------------

        previous_distress = {}
        baseline_distress = {}

        # ==================================
        # PROCESS EACH INTERACTION
        # ==================================

        for interaction in interactions:

            case_id = interaction.case_id

            # ----------------------------------
            # GET TEXT FEATURES
            # ----------------------------------

            text_feature = (
                db.query(TextFeature)
                .filter(
                    TextFeature.interaction_id
                    == interaction.id
                )
                .first()
            )

            # ----------------------------------
            # GET VOICE FEATURES
            # ----------------------------------

            voice_feature = (
                db.query(VoiceFeature)
                .filter(
                    VoiceFeature.interaction_id
                    == interaction.id
                )
                .first()
            )

            # ----------------------------------
            # GET ENGAGEMENT FEATURES
            # ----------------------------------

            engagement_feature = (
                db.query(EngagementFeature)
                .filter(
                    EngagementFeature.interaction_id
                    == interaction.id
                )
                .first()
            )

            # ----------------------------------
            # SKIP IF TEXT FEATURES MISSING
            # ----------------------------------

            if not text_feature:

                print(
                    f"Skipping interaction "
                    f"{interaction.id}: "
                    f"no text features."
                )

                continue

            # ----------------------------------
            # BUILD FEATURE DICTIONARY
            # ----------------------------------

            features = {

                "text_available": (
                    1
                    if interaction.text_response
                    else 0
                ),

                "fear": (
                    text_feature.fear or 0
                ),

                "intimidation": (
                    text_feature.intimidation or 0
                ),

                "hopelessness": (
                    text_feature.hopelessness or 0
                ),

                "isolation": (
                    text_feature.isolation or 0
                ),

                "help_seeking": (
                    text_feature.help_seeking or 0
                ),

                "text_distress_intensity": (
                    text_feature.distress_intensity or 0
                ),

                "sleep_disturbance": (
                    max(
                        0,
                        min(
                            1,
                            (
                                (interaction.sleep_disruption or 1)
                                - 1
                            ) / 4
                        )
                    )
                ),

                "fear_intensity": (
                    max(
                        0,
                        min(
                            1,
                            (
                                (interaction.fear_level or 1)
                                - 1
                            ) / 4
                        )
                    )
                ),

                "low_social_support": (
                    max(
                        0,
                        min(
                            1,
                            (
                                4
                                - (
                                    interaction.social_support
                                    or 4
                                )
                            ) / 4
                        )
                    )
                ),

                "behavioural_distress": (
                    (
                        (
                            (
                                interaction.safety_response
                                or 1
                            ) - 1
                        ) / 4
                        +
                        (
                            (
                                interaction.sleep_disruption
                                or 1
                            ) - 1
                        ) / 4
                        +
                        (
                            (
                                interaction.fear_level
                                or 1
                            ) - 1
                        ) / 4
                        +
                        (
                            4
                            - (
                                interaction.social_support
                                or 4
                            )
                        ) / 4
                    ) / 4
                ),

                "sleep_disturbance_feature": (
                    interaction.sleep_disruption
                ),

                "data_quality_insufficient": (
                    1
                    if interaction.data_quality
                    != "good"
                    else 0
                )
            }

            # ----------------------------------
            # CURRENT DISTRESS
            # ----------------------------------

            current_distress = (
                features["behavioural_distress"]
            )

            # ----------------------------------
            # BASELINE
            # ----------------------------------

            if case_id not in baseline_distress:

                baseline_distress[case_id] = (
                    current_distress
                )

            baseline = baseline_distress[case_id]

            # ----------------------------------
            # PREVIOUS DISTRESS
            # ----------------------------------

            previous = previous_distress.get(
                case_id
            )

            if previous is not None:

                distress_change = (
                    current_distress - previous
                )

            else:

                distress_change = None

            # ----------------------------------
            # CHANGE FROM BASELINE
            # ----------------------------------

            distress_from_baseline = (
                current_distress - baseline
            )

            # ----------------------------------
            # LONGITUDINAL DATA
            # ----------------------------------

            longitudinal = {

                "current_distress":
                    current_distress,

                "previous_distress":
                    previous,

                "distress_change":
                    distress_change,

                "baseline_distress":
                    baseline,

                "distress_from_baseline":
                    distress_from_baseline
            }

            # ----------------------------------
            # CALCULATE RISK
            # ----------------------------------

            result = calculate_risk(
                features,
                longitudinal
            )

            # ----------------------------------
            # CALCULATE TRAJECTORY
            # ----------------------------------

            trajectory = calculate_trajectory(
                current_distress,
                previous
            )

            # ----------------------------------
            # SAVE DISTRESS STATE
            # ----------------------------------

            distress_state = DistressState(

                case_id=case_id,

                observation_date=(
                    interaction.interaction_date
                ),

                distress_score=current_distress,

                trajectory=trajectory,

                confidence=1.0
            )

            db.add(distress_state)

            # ----------------------------------
            # UPDATE COUNTERS
            # ----------------------------------

            total += 1

            if result["risk_level"] == "LOW":

                low += 1

            elif result["risk_level"] == "MODERATE":

                moderate += 1

            elif result["risk_level"] == "HIGH":

                high += 1

            # ----------------------------------
            # PRINT RESULT
            # ----------------------------------

            print(
                f"Interaction {interaction.id} | "
                f"Case {case_id} | "
                f"Distress: "
                f"{current_distress:.2f} | "
                f"Risk: "
                f"{result['risk_level']} | "
                f"Score: "
                f"{result['risk_score']} | "
                f"Trajectory: "
                f"{trajectory}"
            )

            # ----------------------------------
            # SAVE CURRENT AS PREVIOUS
            # ----------------------------------

            previous_distress[case_id] = (
                current_distress
            )

        # ==================================
        # SAVE ALL DISTRESS STATES
        # ==================================

        db.commit()

        print(
            "\nDistress states saved successfully."
        )

        # ==================================
        # SUMMARY
        # ==================================

        print("\n==============================")
        print("AAROH RISK ASSESSMENT SUMMARY")
        print("==============================")

        print(
            f"Total assessed : {total}"
        )

        print(
            f"LOW            : {low}"
        )

        print(
            f"MODERATE       : {moderate}"
        )

        print(
            f"HIGH           : {high}"
        )

        print("==============================\n")

    except Exception as e:

        db.rollback()

        print(
            "\nERROR:",
            e
        )

        raise

    finally:

        db.close()


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()