"""
Seeds DistressState and Prediction records for existing cases in PostgreSQL.
"""

from datetime import datetime, timedelta, timezone
import random
from backend.database import SessionLocal
from backend.models import Case, DistressState, Prediction, Consent


def seed_case_predictions():
    db = SessionLocal()
    try:
        cases = db.query(Case).all()
        if not cases:
            print("No cases found to seed.")
            return

        print(f"Seeding predictions and distress states for {len(cases)} cases...")

        for idx, case in enumerate(cases):
            # Check existing predictions
            existing_pred = db.query(Prediction).filter(Prediction.case_id == case.id).first()
            if existing_pred:
                continue

            # Case scenarios
            if idx == 0:
                # Urgent High Risk + Rapidly Worsening
                prob = 0.88
                traj = "RAPIDLY_WORSENING"
                conf = 0.95
                distress = 0.85
            elif idx == 1:
                # High Risk + Worsening
                prob = 0.78
                traj = "WORSENING"
                conf = 0.90
                distress = 0.75
            elif idx == 2:
                # Moderate Risk + Worsening
                prob = 0.55
                traj = "WORSENING"
                conf = 0.85
                distress = 0.60
            elif idx == 3:
                # Stable Baseline
                prob = 0.25
                traj = "STABLE"
                conf = 0.88
                distress = 0.35
            elif idx == 4:
                # Improving
                prob = 0.15
                traj = "IMPROVING"
                conf = 0.92
                distress = 0.25
            elif idx == 5:
                # Low confidence (Uncertainty routing)
                prob = 0.30
                traj = "STABLE"
                conf = 0.35
                distress = 0.40
            elif idx == 6:
                # Revoked consent
                prob = 0.85
                traj = "RAPIDLY_WORSENING"
                conf = 0.90
                distress = 0.80
                # Update consent
                c = db.query(Consent).filter(Consent.case_id == case.id).first()
                if c:
                    c.monitoring_consent = False
            else:
                prob = round(random.uniform(0.1, 0.9), 2)
                traj = random.choice(["RAPIDLY_WORSENING", "WORSENING", "STABLE", "IMPROVING"])
                conf = round(random.uniform(0.6, 0.95), 2)
                distress = round(random.uniform(0.2, 0.8), 2)

            d_state = DistressState(
                case_id=case.id,
                observation_date=datetime.now(timezone.utc) - timedelta(days=2),
                distress_score=distress,
                trajectory=traj,
                confidence=conf,
            )
            db.add(d_state)

            pred = Prediction(
                case_id=case.id,
                prediction_date=datetime.now(timezone.utc) - timedelta(days=2),
                escalation_probability=prob,
                target_horizon_days=7,
                confidence=conf,
            )
            db.add(pred)

        db.commit()
        print("Seeding completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_case_predictions()
