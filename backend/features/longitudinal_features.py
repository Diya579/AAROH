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
from models import Interaction


def normalize_1_to_5(value):

    if value is None:
        return None

    return (value - 1) / 4


def calculate_distress(interaction):

    values = []

    # Safety: lower safety = higher distress
    safety = normalize_1_to_5(
        interaction.safety_response
    )

    if safety is not None:
        values.append(1 - safety)

    # Sleep disruption
    sleep = normalize_1_to_5(
        interaction.sleep_disruption
    )

    if sleep is not None:
        values.append(sleep)

    # Fear
    fear = normalize_1_to_5(
        interaction.fear_level
    )

    if fear is not None:
        values.append(fear)

    # Low social support
    support = normalize_1_to_5(
        interaction.social_support
    )

    if support is not None:
        values.append(1 - support)

    if not values:
        return None

    return round(
        sum(values) / len(values),
        3
    )


def calculate_case_features(interactions):

    interactions = sorted(
        interactions,
        key=lambda x: x.interaction_date
    )

    if not interactions:
        return []

    baseline = interactions[0]

    baseline_distress = calculate_distress(
        baseline
    )

    results = []

    previous_distress = None

    for index, interaction in enumerate(
        interactions
    ):

        current_distress = calculate_distress(
            interaction
        )

        # -------------------------
        # CHANGE FROM PREVIOUS
        # -------------------------

        if (
            current_distress is not None
            and previous_distress is not None
        ):

            distress_change = round(
                current_distress
                - previous_distress,
                3
            )

        else:

            distress_change = None

        # -------------------------
        # CHANGE FROM BASELINE
        # -------------------------

        if (
            current_distress is not None
            and baseline_distress is not None
        ):

            baseline_change = round(
                current_distress
                - baseline_distress,
                3
            )

        else:

            baseline_change = None

        # -------------------------
        # OBSERVATION COUNT
        # -------------------------

        observations_available = index + 1

        # -------------------------
        # BASELINE STATUS
        # -------------------------

        baseline_available = (
            1 if observations_available >= 1
            else 0
        )

        result = {

            "interaction_id": interaction.id,

            "current_distress":
                current_distress,

            "previous_distress":
                previous_distress,

            "distress_change":
                distress_change,

            "baseline_distress":
                baseline_distress,

            "distress_from_baseline":
                baseline_change,

            "observations_available":
                observations_available,

            "baseline_available":
                baseline_available
        }

        results.append(result)

        previous_distress = current_distress

    return results


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

        cases = {}

        for interaction in interactions:

            if interaction.case_id not in cases:
                cases[interaction.case_id] = []

            cases[interaction.case_id].append(
                interaction
            )

        print(
            f"Found {len(cases)} cases."
        )

        total = 0

        for case_id, case_interactions in cases.items():

            features = calculate_case_features(
                case_interactions
            )

            print(
                f"\nCase {case_id}: "
                f"{len(features)} observations"
            )

            for feature in features:

                print(
                    feature
                )

                total += 1

        print(
            f"\nProcessed {total} longitudinal observations."
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()