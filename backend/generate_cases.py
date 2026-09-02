import os
import random
from datetime import datetime, timedelta

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Case, CaseEvent, Interaction, Consent


random.seed(42)

db = SessionLocal()


LANGUAGES = [
    "English",
    "Hindi",
    "Gujarati",
    "Hindi-English",
    "Gujarati-English"
]

DISTRICT_TYPES = [
    "urban",
    "rural"
]

STAGES = [
    "Registration",
    "Investigation",
    "Trial",
    "Rehabilitation",
    "Compensation"
]

CHANNELS = [
    "mobile_app",
    "sms",
    "chatbot",
    "ivr"
]

USE_CASES = [
    "rape_or_gang_rape",
    "murder_grievous_hurt_arson",
    "witness_intimidation",
    "caste_based_violence_family"
]


def create_case(case_number):

    case_id = f"AAROH-{case_number:03d}"

    language = random.choice(LANGUAGES)

    district_type = random.choice(DISTRICT_TYPES)

    use_case = random.choice(USE_CASES)

    start_date = datetime(2026, 1, 1) + timedelta(
        days=case_number * 2
    )

    case = Case(
        case_id=case_id,
        language=language,
        district_type=district_type,
        district=(
            "Synthetic Urban District"
            if district_type == "urban"
            else "Synthetic Rural District"
        ),
        priority_use_case=use_case,
        current_stage="Investigation",
        voice_opted_in=(case_number % 3 != 0),
        monitoring_consent=True,
        created_at=start_date
    )

    db.add(case)

    db.flush()

    # Consent record

    consent = Consent(
        case_id=case.id,
        monitoring_consent=True,
        text_analysis_consent=True,
        voice_analysis_consent=case.voice_opted_in,
        case_linkage_consent=True,
        safe_channel="sms",
        safe_time="after_19:00"
    )

    db.add(consent)

    # Timeline

    for day in range(0, 50, 5):

        observation_date = start_date + timedelta(days=day)

        # Progress through case stages

        if day < 10:
            stage = "Registration"
        elif day < 25:
            stage = "Investigation"
        elif day < 40:
            stage = "Trial"
        else:
            stage = random.choice(
                ["Rehabilitation", "Compensation"]
            )

        event_type = random.choice([
            "case_update",
            "investigation_milestone",
            "hearing",
            "support_followup"
        ])

        event = CaseEvent(
            case_id=case.id,
            event_date=observation_date,
            event_type=event_type,
            description=f"Synthetic {event_type}",
            case_stage=stage
        )

        db.add(event)

        # Different trajectories

        if case_number % 5 == 0:
            # Improving

            distress = max(
                15,
                65 - day * 0.8
            )

        elif case_number % 5 == 1:
            # Stable

            distress = 35 + random.uniform(-5, 5)

        elif case_number % 5 == 2:
            # Gradually worsening

            distress = min(
                85,
                30 + day * 0.9
            )

        elif case_number % 5 == 3:
            # Rapid deterioration

            distress = min(
                95,
                25 + day * 1.7
            )

        else:
            # Volatile

            distress = min(
                90,
                max(
                    20,
                    50 + random.uniform(-25, 25)
                )
            )

        distress = round(distress, 2)

        safety = max(
            1,
            min(
                5,
                round(6 - distress / 20)
            )
        )

        sleep = max(
            1,
            min(
                5,
                round(distress / 20)
            )
        )

        fear = max(
            1,
            min(
                5,
                round(distress / 20)
            )
        )

        social_support = max(
            1,
            min(
                5,
                6 - round(distress / 20)
            )
        )

        # Synthetic text

        if distress < 35:
            text = random.choice([
                "Things are manageable.",
                "I am doing okay.",
                "I feel supported."
            ])

        elif distress < 60:
            text = random.choice([
                "I have been feeling worried.",
                "The situation has been difficult.",
                "I am having trouble sleeping."
            ])

        else:
            text = random.choice([
                "I feel very afraid after the recent court event.",
                "I am worried about what may happen to my family.",
                "I don't feel safe and I need someone to talk to."
            ])

        # Missing interaction occasionally

        missed = (
            case_number % 7 == 0
            and day >= 25
            and day % 10 == 5
        )

        interaction = Interaction(
            case_id=case.id,
            interaction_date=observation_date,
            channel=random.choice(CHANNELS),
            language=language,
            text_response=None if missed else text,
            voice_available=(
                case.voice_opted_in
                and not missed
            ),
            response_completed=not missed,
            safety_response=None if missed else safety,
            sleep_disruption=None if missed else sleep,
            fear_level=None if missed else fear,
            social_support=None if missed else social_support,
            help_requested=(
                distress >= 75
                and not missed
            ),
            data_quality=(
                "insufficient"
                if missed
                else "good"
            )
        )

        db.add(interaction)

    return case_id


# Remove existing synthetic data

db.query(Interaction).delete()
db.query(CaseEvent).delete()
db.query(Consent).delete()
db.query(Case).delete()

db.commit()


print("Generating 20 synthetic AAROH cases...\n")

for i in range(1, 21):

    case_id = create_case(i)

    print(f"Created {case_id}")


db.commit()
db.close()

print("\nDone.")
print("20 longitudinal cases generated.")
print("Each case contains multiple observations across 50 days.")