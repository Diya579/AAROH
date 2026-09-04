import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )
)

from backend.database import SessionLocal
from sqlalchemy import text

from backend.models import (
    Case,
    Interaction,
    DistressState,
    Prediction,
    Consent,
    Intervention
)


def main():

    db = SessionLocal()

    try:

        print("\n========================================")
        print("        AAROH PIPELINE VALIDATION")
        print("========================================\n")

        # -----------------------------------------
        # COUNTS
        # -----------------------------------------

        cases = db.query(Case).count()
        interactions = db.query(Interaction).count()
        distress_states = db.query(DistressState).count()
        predictions = db.query(Prediction).count()
        consents = db.query(Consent).count()
        interventions = db.query(Intervention).count()

        print("DATABASE COUNTS")
        print("----------------")
        print(f"Cases          : {cases}")
        print(f"Interactions   : {interactions}")
        print(f"Distress       : {distress_states}")
        print(f"Predictions    : {predictions}")
        print(f"Consents       : {consents}")
        print(f"Interventions : {interventions}")

        # -----------------------------------------
        # BASIC VALIDATION
        # -----------------------------------------

        print("\nBASIC VALIDATION")
        print("----------------")

        checks = []

        checks.append(
            ("20 cases exist", cases == 20)
        )

        checks.append(
            ("200 interactions exist", interactions == 200)
        )

        checks.append(
            ("200 distress states exist", distress_states == 200)
        )

        checks.append(
            ("20 predictions exist", predictions == 20)
        )

        checks.append(
            ("20 consents exist", consents == 20)
        )

        checks.append(
            ("20 interventions exist", interventions == 20)
        )

        for name, passed in checks:

            print(
                f"{'PASS' if passed else 'FAIL'} | {name}"
            )

        # -----------------------------------------
        # CASE-LEVEL VALIDATION
        # -----------------------------------------

        print("\nCASE LEVEL VALIDATION")
        print("---------------------")

        cases = (
            db.query(Case)
            .order_by(Case.id)
            .all()
        )

        case_failures = 0

        for case in cases:

            interaction_count = (
                db.query(Interaction)
                .filter(
                    Interaction.case_id == case.id
                )
                .count()
            )

            distress_count = (
                db.query(DistressState)
                .filter(
                    DistressState.case_id == case.id
                )
                .count()
            )

            prediction = (
                db.query(Prediction)
                .filter(
                    Prediction.case_id == case.id
                )
                .order_by(
                    Prediction.prediction_date.desc()
                )
                .first()
            )

            intervention = (
                db.query(Intervention)
                .filter(
                    Intervention.case_id == case.id,
                    Intervention.status == "PENDING"
                )
                .order_by(
                    Intervention.id.desc()
                )
                .first()
            )

            passed = (
                interaction_count == 10
                and distress_count == 10
                and prediction is not None
                and intervention is not None
            )

            if not passed:
                case_failures += 1

            print(
                f"{case.case_id} | "
                f"interactions={interaction_count} | "
                f"distress={distress_count} | "
                f"prediction="
                f"{'YES' if prediction is not None else 'NO'} | "
                f"intervention="
                f"{'YES' if intervention is not None else 'NO'} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        # -----------------------------------------
        # PREDICTION VALIDATION
        # -----------------------------------------

        print("\nPREDICTION VALIDATION")
        print("---------------------")

        prediction_failures = 0

        predictions = (
            db.query(Prediction)
            .order_by(Prediction.case_id)
            .all()
        )

        for prediction in predictions:

            probability = prediction.escalation_probability
            confidence = prediction.confidence
            horizon = prediction.target_horizon_days

            valid_probability = (
                probability is not None
                and 0.0 <= probability <= 1.0
            )

            valid_confidence = (
                confidence is not None
                and 0.0 <= confidence <= 1.0
            )

            valid_horizon = (
                horizon is not None
                and horizon > 0
            )

            passed: bool = (
                bool(valid_probability)
                and bool(valid_confidence)
                and bool(valid_horizon)
            )

            if not passed:
                prediction_failures += 1

            print(
                f"Case {prediction.case_id} | "
                f"probability={probability} | "
                f"confidence={confidence} | "
                f"horizon={horizon}d | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        # -----------------------------------------
        # INTERVENTION VALIDATION
        # -----------------------------------------

        print("\nINTERVENTION VALIDATION")
        print("-----------------------")

        intervention_failures = 0

        interventions = (
            db.query(Intervention)
            .order_by(Intervention.case_id)
            .all()
        )

        valid_types = {
            "PRIORITY_HUMAN_REVIEW",
            "HUMAN_FOLLOW_UP",
            "CONTINUE_MONITORING",
            "ROUTINE_MONITORING",
            "NO_AUTOMATED_INTERVENTION"
        }

        valid_statuses = {
            "PENDING",
            "COMPLETED",
            "CANCELLED"
        }

        for intervention in interventions:

            valid_intervention_type = (
                intervention.intervention_type in valid_types
            )

            valid_intervention_status = (
                intervention.status in valid_statuses
            )

            passed: bool = (
                bool(valid_intervention_type)
                and bool(valid_intervention_status)
            )

            if not passed:
                intervention_failures += 1

            print(
                f"Case {intervention.case_id} | "
                f"{intervention.intervention_type} | "
                f"{intervention.status} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        # -----------------------------------------
        # DUPLICATE PENDING CHECK
        # -----------------------------------------

        print("\nDUPLICATE CHECK")
        print("---------------")

        duplicate_query = """
        SELECT case_id, intervention_type, COUNT(*)
        FROM interventions
        WHERE status = 'PENDING'
        GROUP BY case_id, intervention_type
        HAVING COUNT(*) > 1
        """

        duplicates = db.execute(
            text(duplicate_query)
        ).fetchall()

        if duplicates:

            print("FAIL | Duplicate pending interventions found.")

            for row in duplicates:
                print(row)

        else:

            print(
                "PASS | No duplicate pending interventions."
            )

        # -----------------------------------------
        # FINAL RESULT
        # -----------------------------------------

        total_failures = (
            sum(
                1
                for _, passed in checks
                if not passed
            )
            + case_failures
            + prediction_failures
            + intervention_failures
            + len(duplicates)
        )

        print("\n========================================")

        if total_failures == 0:

            print(
                "AAROH PIPELINE VALIDATION: PASSED"
            )

            print(
                "========================================\n"
            )

        else:

            print(
                f"AAROH PIPELINE VALIDATION: "
                f"FAILED ({total_failures} issues)"
            )

            print(
                "========================================\n"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()