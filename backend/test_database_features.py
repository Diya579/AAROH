from database import SessionLocal
from models import Interaction

from features.extract_features import extract_all_features


db = SessionLocal()

interaction = (
    db.query(Interaction)
    .order_by(Interaction.interaction_date)
    .first()
)

if interaction is None:

    print("No interactions found.")
    db.close()
    raise SystemExit


print("\nCASE:")
print(interaction.case_id)

print("\nRAW DATA:")
print("Text:", interaction.text_response)
print("Safety:", interaction.safety_response)
print("Sleep:", interaction.sleep_disruption)
print("Fear:", interaction.fear_level)
print("Social support:", interaction.social_support)
print("Voice:", interaction.voice_available)
print("Data quality:", interaction.data_quality)


features = extract_all_features(interaction)


print("\nEXTRACTED FEATURES:")

for name, value in features.items():

    print(
        f"{name}: {value}"
    )


db.close()