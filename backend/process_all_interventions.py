import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

from backend.database import SessionLocal
from backend.models import Case
from backend.interventions.db_service import DatabaseOperationalService


def main():

    db = SessionLocal()

    try:

        # -----------------------------------------
        # GET ALL CASES
        # -----------------------------------------

        cases = (
            db.query(Case)
            .order_by(Case.id)
            .all()
        )

        print(
            f"\nFound {len(cases)} cases.\n"
        )

        print("==============================")
        print("AAROH INTERVENTION PROCESSING")
        print("==============================\n")

        created = 0
        existing = 0
        failed = 0

        # -----------------------------------------
        # PROCESS EACH CASE
        # -----------------------------------------

        for case in cases:

            try:

                result = DatabaseOperationalService().process_case_intervention(
                    db=db,
                    case_id=case.id,
                    auto_commit=True
                )

                if result.get("is_duplicate"):

                    existing += 1
                    action = "EXISTING"

                else:

                    created += 1
                    action = "CREATED"

                print(
                    f"{case.case_id} | "
                    f"{result['intervention_type']} | "
                    f"Priority: {result['priority']} | "
                    f"Probability: "
                    f"{result['escalation_probability']:.2f} | "
                    f"Status: {result['status']} | "
                    f"{action}"
                )

            except Exception as e:

                failed += 1

                print(
                    f"{case.case_id} | ERROR | {e}"
                )

        # -----------------------------------------
        # SUMMARY
        # -----------------------------------------

        print("\n==============================")
        print("INTERVENTION SUMMARY")
        print("==============================")

        print(
            f"Total cases : {len(cases)}"
        )

        print(
            f"Created     : {created}"
        )

        print(
            f"Existing    : {existing}"
        )

        print(
            f"Failed      : {failed}"
        )

        print("==============================\n")

    finally:

        db.close()


if __name__ == "__main__":
    main()