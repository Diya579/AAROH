"""Explainability and Evidence Generation for Longitudinal Trajectory Model (Slice 3.7).

Produces structured, machine-readable evidence explaining trajectory state predictions
grounded strictly in observable longitudinal signals across historical interaction sequences:
- Trend velocity (rate of change per day / per week)
- Trend acceleration (second derivative of distress trajectory)
- Consecutive interaction trends (consecutive increases or decreases)
- Feature drift (shifts in fear, sadness, sleep disruption, engagement)
- Temporal duration and baseline comparison

Strict Clinical Invariant:
- Machine-readable evidence provides operational trend support only.
- It NEVER states or implies a psychiatric diagnosis, escalation urgency, or clinical prognosis.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from backend.ml.training.models.trajectory.dataset import (
    DEFAULT_HISTORY_WINDOW,
    LABEL_DISCLAIMER,
    LABEL_IMPROVING,
    LABEL_RAPIDLY_WORSENING,
    LABEL_STABLE,
    LABEL_WORSENING,
    CaseTrajectory,
    TrajectoryInputRecord,
)

# Canonical Trajectory States
STATE_IMPROVING = "Improving"
STATE_STABLE = "Stable"
STATE_SLOWLY_WORSENING = "Slowly worsening"
STATE_RAPIDLY_WORSENING = "Rapidly worsening"
STATE_RECOVERING = "Recovering"


@dataclass
class TrajectoryEvidence:
    """Structured machine-readable evidence for a longitudinal trajectory prediction."""

    trajectory_score: float
    trajectory_state: str
    trajectory_label: str
    confidence: float
    trend_velocity: float
    trend_velocity_display: str
    trend_acceleration: float
    reasons: List[str]
    observations_count: int
    history_span_days: float
    delta_from_baseline: float
    delta_from_previous: float
    model_version: str
    evidence_details: Dict[str, Any] = field(default_factory=dict)
    label_disclaimer: str = LABEL_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        """Serializes evidence into a clean dictionary."""
        return asdict(self)


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime.datetime]:
    """Safely parses timestamp string in ISO or date format."""
    if not ts:
        return None
    # Strip Z if present
    clean_ts = ts.rstrip("Z")
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.datetime.strptime(clean_ts, fmt)
        except ValueError:
            pass
    return None


def calculate_trajectory_metrics(
    records: Sequence[TrajectoryInputRecord],
) -> Dict[str, Any]:
    """Calculates deterministic temporal metrics across an ordered sequence of interactions.

    Returns:
    - observations_count: total interactions in window
    - history_span_days: days between first and last interaction
    - baseline_distress: distress score of first interaction
    - current_distress: distress score of most recent interaction
    - previous_distress: distress score of second-to-last interaction (if >=2)
    - delta_from_baseline: current - baseline
    - delta_from_previous: current - previous
    - trend_velocity_daily: rate of distress change per day
    - trend_velocity_weekly: rate of distress change per week
    - trend_acceleration: rate of change of velocity
    - consecutive_worsening_count: consecutive times distress increased
    - consecutive_improving_count: consecutive times distress decreased
    """
    n = len(records)
    if n == 0:
        return {
            "observations_count": 0,
            "history_span_days": 0.0,
            "baseline_distress": 0.0,
            "current_distress": 0.0,
            "previous_distress": 0.0,
            "delta_from_baseline": 0.0,
            "delta_from_previous": 0.0,
            "trend_velocity_daily": 0.0,
            "trend_velocity_weekly": 0.0,
            "trend_acceleration": 0.0,
            "consecutive_worsening_count": 0,
            "consecutive_improving_count": 0,
        }

    scores = [max(0.0, min(1.0, float(r.distress_score))) for r in records]
    baseline_distress = scores[0]
    current_distress = scores[-1]
    previous_distress = scores[-2] if n >= 2 else scores[0]
    delta_from_baseline = round(current_distress - baseline_distress, 4)
    delta_from_previous = round(current_distress - previous_distress, 4)

    # Compute time span in days
    t_first = _parse_timestamp(records[0].timestamp)
    t_last = _parse_timestamp(records[-1].timestamp)
    if t_first and t_last and t_last >= t_first:
        total_seconds = (t_last - t_first).total_seconds()
        history_span_days = max(0.1, round(total_seconds / 86400.0, 2))
    else:
        # Fallback if timestamps are missing or invalid: assume 1 day per interaction
        history_span_days = max(1.0, float(n - 1))

    # Calculate velocity: change per week
    # If single interaction, velocity is 0.0
    if n < 2:
        trend_velocity_daily = 0.0
        trend_velocity_weekly = 0.0
        trend_acceleration = 0.0
    else:
        trend_velocity_daily = delta_from_baseline / max(1.0, history_span_days)
        trend_velocity_weekly = round(trend_velocity_daily * 7.0, 4)

        # Acceleration: difference between recent velocity and earlier velocity
        if n >= 3:
            mid = n // 2
            span_first_half = max(1.0, history_span_days / 2.0)
            span_second_half = max(1.0, history_span_days / 2.0)
            v_early = (scores[mid] - scores[0]) / span_first_half
            v_recent = (scores[-1] - scores[mid]) / span_second_half
            trend_acceleration = round((v_recent - v_early) * 7.0, 4)
        else:
            trend_acceleration = 0.0

    # Consecutive streak analysis
    consecutive_worsening = 0
    consecutive_improving = 0
    for i in range(len(scores) - 1, 0, -1):
        diff = scores[i] - scores[i - 1]
        if diff > 0.02:
            if consecutive_improving == 0:
                consecutive_worsening += 1
            else:
                break
        elif diff < -0.02:
            if consecutive_worsening == 0:
                consecutive_improving += 1
            else:
                break
        else:
            break

    # Calculate max step increase and decrease
    max_step_increase = 0.0
    max_step_decrease = 0.0
    for i in range(1, len(scores)):
        diff = scores[i] - scores[i - 1]
        if diff > max_step_increase:
            max_step_increase = diff
        if diff < -max_step_decrease:
            max_step_decrease = -diff

    return {
        "observations_count": n,
        "history_span_days": history_span_days,
        "baseline_distress": round(baseline_distress, 4),
        "current_distress": round(current_distress, 4),
        "previous_distress": round(previous_distress, 4),
        "delta_from_baseline": delta_from_baseline,
        "delta_from_previous": delta_from_previous,
        "max_step_increase": round(max_step_increase, 4),
        "max_step_decrease": round(max_step_decrease, 4),
        "trend_velocity_daily": round(trend_velocity_daily, 4),
        "trend_velocity_weekly": trend_velocity_weekly,
        "trend_acceleration": trend_acceleration,
        "consecutive_worsening_count": consecutive_worsening,
        "consecutive_improving_count": consecutive_improving,
    }


def determine_trajectory_state_and_confidence(
    trajectory_score: float,
    metrics: Dict[str, Any],
) -> Tuple[str, float]:
    """Maps trajectory score and temporal dynamics to fine-grained state and confidence."""
    n = metrics["observations_count"]
    v_week = metrics["trend_velocity_weekly"]
    delta_base = metrics["delta_from_baseline"]
    max_inc = metrics.get("max_step_increase", 0.0)
    consec_worse = metrics["consecutive_worsening_count"]
    consec_imp = metrics["consecutive_improving_count"]
    base_dist = metrics["baseline_distress"]
    curr_dist = metrics["current_distress"]

    if n < 2:
        return STATE_STABLE, 0.70

    # 1. Rapidly Worsening: requires steep velocity (>= 0.70/week), large single-step leap (>= 0.18),
    # or reaching critical distress (>= 0.80) with high velocity
    is_rapid = (
        v_week >= 0.70 or
        max_inc >= 0.18 or
        (curr_dist >= 0.80 and v_week >= 0.35)
    )
    if is_rapid and v_week > 0.15:
        state = STATE_RAPIDLY_WORSENING
        conf = 0.88 + min(0.10, abs(v_week) * 0.1)

    # 2. Slowly Worsening: gradual continuous increase without sharp single-step spikes
    elif v_week >= 0.04 or consec_worse >= 2 or delta_base >= 0.10:
        state = STATE_SLOWLY_WORSENING
        conf = 0.82 + min(0.12, abs(v_week) * 0.2)

    # 3. Improving / Recovering: downward trajectory
    elif v_week <= -0.04 or consec_imp >= 2 or delta_base <= -0.10:
        # If baseline was severe/elevated and current is substantially lower
        if (base_dist >= 0.65 and curr_dist <= 0.35) and "recovering" in [STATE_RECOVERING.lower()]:
            state = STATE_IMPROVING  # or STATE_RECOVERING as appropriate
        else:
            state = STATE_IMPROVING
        conf = 0.85 + min(0.10, abs(v_week) * 0.1)

    # 4. Stable: bounded within minimal drift
    else:
        state = STATE_STABLE
        conf = 0.88 - min(0.20, abs(v_week) * 0.5)

    return state, round(float(max(0.50, min(0.99, conf))), 2)


def generate_trajectory_reasons(
    metrics: Dict[str, Any],
    records: Sequence[TrajectoryInputRecord],
) -> List[str]:
    """Generates strictly input-grounded bullet reasons explaining the trajectory."""
    reasons: List[str] = []
    n = metrics["observations_count"]
    v_week = metrics["trend_velocity_weekly"]
    span_days = metrics["history_span_days"]
    consec_worse = metrics["consecutive_worsening_count"]
    consec_imp = metrics["consecutive_improving_count"]
    delta_base = metrics["delta_from_baseline"]

    if n < 2:
        return ["Baseline interaction: insufficient history to establish longitudinal trend"]

    # Reason 1: Consecutive trajectory streak
    if consec_worse >= 2:
        reasons.append(f"Distress increased for {consec_worse} consecutive interactions")
    elif consec_imp >= 2:
        reasons.append(f"Distress decreased for {consec_imp} consecutive interactions")

    # Reason 2: Persistence and duration
    if delta_base > 0.10:
        reasons.append(f"Negative trend persisted for {int(span_days)} days (net shift: +{delta_base:.2f})")
    elif delta_base < -0.10:
        reasons.append(f"Improvement trend persisted for {int(span_days)} days (net shift: {delta_base:.2f})")
    else:
        reasons.append(f"Distress remained stable within ±0.10 across {int(span_days)} days")

    # Reason 3: Feature-level drift (behavioural and engagement shifts)
    if len(records) >= 2:
        r_first = records[0]
        r_last = records[-1]

        # Check sleep disruption if present in behavioural features (index 1 in standard registry)
        if len(r_first.behavioural_features) >= 2 and len(r_last.behavioural_features) >= 2:
            s_init = r_first.behavioural_features[1]
            s_curr = r_last.behavioural_features[1]
            if s_curr > s_init + 0.20:
                reasons.append("Sleep disruption increased across recent interactions")
            elif s_curr < s_init - 0.20:
                reasons.append("Sleep disruption decreased across recent interactions")

        # Check engagement shift (session latency / check-in regularity in engagement features)
        if len(r_first.engagement_features) >= 1 and len(r_last.engagement_features) >= 1:
            e_init = r_first.engagement_features[0]
            e_curr = r_last.engagement_features[0]
            if e_curr < e_init - 0.20:
                reasons.append("Engagement decreased across recent interactions")
            elif e_curr > e_init + 0.20:
                reasons.append("Engagement increased across recent interactions")

    return reasons


def generate_trajectory_evidence(
    records: Sequence[TrajectoryInputRecord],
    trajectory_score: float,
    trajectory_label: str,
    model_version: str = "aaroh-trajectory-v1",
) -> TrajectoryEvidence:
    """Constructs comprehensive machine-readable evidence grounded strictly in historical inputs."""
    metrics = calculate_trajectory_metrics(records)
    state, conf = determine_trajectory_state_and_confidence(trajectory_score, metrics)
    reasons = generate_trajectory_reasons(metrics, records)

    v_disp = f"{metrics['trend_velocity_weekly']:+.2f}/week"

    return TrajectoryEvidence(
        trajectory_score=trajectory_score,
        trajectory_state=state,
        trajectory_label=trajectory_label,
        confidence=conf,
        trend_velocity=metrics["trend_velocity_weekly"],
        trend_velocity_display=v_disp,
        trend_acceleration=metrics["trend_acceleration"],
        reasons=reasons,
        observations_count=metrics["observations_count"],
        history_span_days=metrics["history_span_days"],
        delta_from_baseline=metrics["delta_from_baseline"],
        delta_from_previous=metrics["delta_from_previous"],
        model_version=model_version,
        evidence_details=metrics,
    )
