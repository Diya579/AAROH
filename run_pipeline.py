"""
run_pipeline.py — AAROH local development pipeline runner.

Executes the full data pipeline in sequence:
  1. Extract and save features for all interactions
  2. Process all cases to generate distress states
  3. Generate predictions for all cases
  4. Create interventions for all cases

This script exists because the legacy pipeline scripts use mixed
import styles that require specific sys.path configuration.
Run from the project root:
    python run_pipeline.py
"""

import sys
import os

# Project root on sys.path (for `from backend.xxx import ...`)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# backend/ on sys.path (for `from database import ...`, `from models import ...`)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

# backend/features/ on sys.path (for `from extract_features import ...`)
FEATURES_DIR = os.path.join(BACKEND_DIR, "features")
sys.path.insert(0, FEATURES_DIR)

# backend/risk/ on sys.path (for `from risk_scoring import ...`)
RISK_DIR = os.path.join(BACKEND_DIR, "risk")
sys.path.insert(0, RISK_DIR)


# ---------------------------------------------------------------------------
# STEP 1 — Feature extraction
# ---------------------------------------------------------------------------

print("=" * 50)
print("STEP 1: Feature Extraction")
print("=" * 50)

from database import SessionLocal
from models import (
    Interaction,
    TextFeature,
    VoiceFeature,
    EngagementFeature,
    Case,
    DistressState,
    Prediction,
)

# Import feature extractors as bare modules (features/ is on sys.path)
import importlib.util

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


text_features_mod = _load_module(
    "text_features",
    os.path.join(FEATURES_DIR, "text_features.py"),
)
behavioural_features_mod = _load_module(
    "behavioural_features",
    os.path.join(FEATURES_DIR, "behavioural_features.py"),
)
engagement_features_mod = _load_module(
    "engagement_features",
    os.path.join(FEATURES_DIR, "engagement_features.py"),
)


def extract_all_features(interaction):
    text_feats = text_features_mod.extract_text_features(
        interaction.text_response
    )
    behav_feats = behavioural_features_mod.extract_behavioural_features(
        interaction.safety_response,
        interaction.sleep_disruption,
        interaction.fear_level,
        interaction.social_support,
    )
    engage_feats = engagement_features_mod.extract_engagement_features(
        interaction.response_completed,
        interaction.voice_available,
        interaction.data_quality,
    )
    features = {}
    features.update(text_feats)
    features.update(behav_feats)
    features.update(engage_feats)
    return features


db = SessionLocal()
try:
    interactions = (
        db.query(Interaction)
        .order_by(Interaction.case_id, Interaction.interaction_date)
        .all()
    )
    print(f"Found {len(interactions)} interactions.")

    db.query(TextFeature).delete()
    db.query(VoiceFeature).delete()
    db.query(EngagementFeature).delete()
    db.commit()

    for idx, interaction in enumerate(interactions, start=1):
        features = extract_all_features(interaction)

        text_feature = TextFeature(
            interaction_id=interaction.id,
            distress_intensity=features["text_distress_intensity"],
            fear=features["fear"],
            intimidation=features["intimidation"],
            hopelessness=features["hopelessness"],
            isolation=features["isolation"],
            help_seeking=features["help_seeking"],
            language_confidence=1.0,
        )
        voice_feature = VoiceFeature(
            interaction_id=interaction.id,
            speech_rate=None,
            pause_ratio=None,
            response_latency=None,
            pitch_variability=None,
            energy_variation=None,
            audio_quality=None,
            baseline_deviation=None,
        )
        engagement_feature = EngagementFeature(
            interaction_id=interaction.id,
            response_delay=None,
            missed_checkin=(features["missed_checkin"] == 1),
            engagement_change=None,
        )
        db.add(text_feature)
        db.add(voice_feature)
        db.add(engagement_feature)

        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(interactions)}")

    db.commit()
    print("Feature extraction completed.")
finally:
    db.close()


# ---------------------------------------------------------------------------
# STEP 2 — Risk scoring / distress states
# ---------------------------------------------------------------------------

print("\n" + "=" * 50)
print("STEP 2: Distress State Processing")
print("=" * 50)

# Load risk_scoring as bare module
risk_scoring_mod = _load_module(
    "risk_scoring",
    os.path.join(RISK_DIR, "risk_scoring.py"),
)
calculate_risk = risk_scoring_mod.calculate_risk


def calculate_trajectory(current, previous):
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
    return "STABLE"


db = SessionLocal()
try:
    interactions = (
        db.query(Interaction)
        .order_by(Interaction.case_id, Interaction.interaction_date)
        .all()
    )

    from models import TextFeature as TF

    db.query(DistressState).delete()
    db.commit()

    previous_distress = {}
    baseline_distress = {}
    skipped = 0

    for interaction in interactions:
        case_id = interaction.case_id

        text_feature = (
            db.query(TF)
            .filter(TF.interaction_id == interaction.id)
            .first()
        )

        if not text_feature:
            skipped += 1
            continue

        features = {
            "text_available": 1 if interaction.text_response else 0,
            "fear": text_feature.fear or 0,
            "intimidation": text_feature.intimidation or 0,
            "hopelessness": text_feature.hopelessness or 0,
            "isolation": text_feature.isolation or 0,
            "help_seeking": text_feature.help_seeking or 0,
            "text_distress_intensity": text_feature.distress_intensity or 0,
            "sleep_disturbance": max(0, min(1, ((interaction.sleep_disruption or 1) - 1) / 4)),
            "fear_intensity": max(0, min(1, ((interaction.fear_level or 1) - 1) / 4)),
            "low_social_support": max(0, min(1, (4 - (interaction.social_support or 4)) / 4)),
            "behavioural_distress": (
                ((interaction.safety_response or 1) - 1) / 4
                + ((interaction.sleep_disruption or 1) - 1) / 4
                + ((interaction.fear_level or 1) - 1) / 4
                + (4 - (interaction.social_support or 4)) / 4
            ) / 4,
            "sleep_disturbance_feature": interaction.sleep_disruption,
            "data_quality_insufficient": 1 if interaction.data_quality != "good" else 0,
        }

        current_distress = features["behavioural_distress"]

        if case_id not in baseline_distress:
            baseline_distress[case_id] = current_distress
        baseline = baseline_distress[case_id]

        previous = previous_distress.get(case_id)
        distress_change = (current_distress - previous) if previous is not None else None
        distress_from_baseline = current_distress - baseline

        longitudinal = {
            "current_distress": current_distress,
            "previous_distress": previous,
            "distress_change": distress_change,
            "baseline_distress": baseline,
            "distress_from_baseline": distress_from_baseline,
        }

        result = calculate_risk(features, longitudinal)
        trajectory = calculate_trajectory(current_distress, previous)

        state = DistressState(
            case_id=case_id,
            observation_date=interaction.interaction_date,
            distress_score=current_distress,
            trajectory=trajectory,
            confidence=1.0,
        )
        db.add(state)
        previous_distress[case_id] = current_distress

    db.commit()
    print(f"Distress states saved. Skipped {skipped} interactions (no features).")
finally:
    db.close()


# ---------------------------------------------------------------------------
# STEP 3 — Predictions
# ---------------------------------------------------------------------------

print("\n" + "=" * 50)
print("STEP 3: Generating Predictions")
print("=" * 50)

from datetime import datetime

db = SessionLocal()
try:
    # Delete old predictions
    db.query(Prediction).delete()
    db.commit()

    cases = db.query(Case).order_by(Case.id).all()
    print(f"Found {len(cases)} cases.")

    for case in cases:
        all_states = (
            db.query(DistressState)
            .filter(DistressState.case_id == case.id)
            .order_by(DistressState.observation_date.asc())
            .all()
        )

        if not all_states:
            print(f"  {case.case_id}: no distress states, skipping.")
            continue

        latest = all_states[-1]
        previous = all_states[-2] if len(all_states) >= 2 else None

        recent_change = (
            latest.distress_score - previous.distress_score
            if previous else None
        )
        baseline = all_states[0].distress_score
        baseline_deviation = latest.distress_score - baseline

        # Inline probability calculation (same logic as risk/prediction.py)
        prob = 0.0
        conf = 0.50

        cd = latest.distress_score
        if cd >= 0.75:
            prob += 0.35
        elif cd >= 0.55:
            prob += 0.25
        elif cd >= 0.40:
            prob += 0.12

        traj = latest.trajectory
        if traj == "RAPIDLY_WORSENING":
            prob += 0.30
        elif traj == "WORSENING":
            prob += 0.15
        elif traj == "IMPROVING":
            prob -= 0.10
        elif traj == "RAPIDLY_IMPROVING":
            prob -= 0.15

        if recent_change is not None:
            if recent_change >= 0.15:
                prob += 0.20
            elif recent_change >= 0.05:
                prob += 0.10

        if baseline_deviation >= 0.30:
            prob += 0.15
        elif baseline_deviation >= 0.15:
            prob += 0.07

        prob = max(0.0, min(1.0, prob))

        if cd is not None:
            conf += 0.10
        if traj != "STABLE":
            conf += 0.10
        if recent_change is not None:
            conf += 0.10
        if baseline_deviation is not None:
            conf += 0.10
        conf = max(0.0, min(1.0, conf))

        prediction = Prediction(
            case_id=case.id,
            prediction_date=datetime.utcnow(),
            escalation_probability=round(prob, 3),
            target_horizon_days=7,
            confidence=round(conf, 3),
        )
        db.add(prediction)

    db.commit()
    print("Predictions generated.")
finally:
    db.close()


# ---------------------------------------------------------------------------
# STEP 4 — Interventions
# ---------------------------------------------------------------------------

print("\n" + "=" * 50)
print("STEP 4: Creating Interventions")
print("=" * 50)

from models import Consent, Intervention

db = SessionLocal()
try:
    from typing import cast

    cases = db.query(Case).order_by(Case.id).all()
    print(f"Found {len(cases)} cases.")

    # Clear existing interventions
    db.query(Intervention).delete()
    db.commit()

    for case in cases:
        prediction = (
            db.query(Prediction)
            .filter(Prediction.case_id == case.id)
            .order_by(Prediction.prediction_date.desc())
            .first()
        )
        if not prediction:
            print(f"  {case.case_id}: no prediction, skipping.")
            continue

        consent = (
            db.query(Consent)
            .filter(Consent.case_id == case.id)
            .first()
        )
        monitoring_consent = (
            consent.monitoring_consent if consent else case.monitoring_consent
        )

        distress_state = (
            db.query(DistressState)
            .filter(DistressState.case_id == case.id)
            .order_by(DistressState.observation_date.desc())
            .first()
        )
        trajectory = distress_state.trajectory if distress_state else "STABLE"
        probability = prediction.escalation_probability or 0.0

        if probability >= 0.75:
            risk_level = "HIGH"
        elif probability >= 0.40:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        if not monitoring_consent:
            itype = "NO_AUTOMATED_INTERVENTION"
        elif risk_level == "HIGH" or probability >= 0.75 or trajectory == "RAPIDLY_WORSENING":
            itype = "PRIORITY_HUMAN_REVIEW"
        elif risk_level == "MODERATE" or probability >= 0.40 or trajectory == "WORSENING":
            itype = "HUMAN_FOLLOW_UP"
        elif trajectory in ("IMPROVING", "RAPIDLY_IMPROVING"):
            itype = "CONTINUE_MONITORING"
        else:
            itype = "ROUTINE_MONITORING"

        intervention = Intervention(
            case_id=case.id,
            intervention_type=itype,
            status="PENDING",
            assigned_to=None,
        )
        db.add(intervention)

    db.commit()
    print("Interventions created.")
finally:
    db.close()

print("\n" + "=" * 50)
print("AAROH PIPELINE COMPLETE")
print("=" * 50)
