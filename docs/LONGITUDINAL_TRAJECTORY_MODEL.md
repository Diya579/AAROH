# Longitudinal Trajectory Model Architecture & Specification (Slice 3.7)

## 1. Executive Summary & Operational Definition

The **Longitudinal Trajectory Model** is the temporal reasoning subsystem within the AAROH ML pipeline. While the Dynamic Distress Model (Slice 3.6) measures acute psychological distress at an isolated interaction, the Longitudinal Trajectory Model determines **how distress evolves over time across an interaction history**.

### What Trajectory IS:
- A dynamic, temporal estimation of rate of change, direction, and acceleration in psychological strain across sequential interactions:
  $$\text{trend\_velocity} = \frac{\Delta \text{distress}}{\Delta t} \quad \left[\frac{\text{score}}{\text{week}}\right]$$
  $$\text{trend\_acceleration} = \frac{\Delta \text{velocity}}{\Delta t}$$
- A continuous slope score:
  $$\text{trajectory\_score} \in [-1.00, +1.00]$$
  where $-1.0$ indicates marked improvement, $0.0$ indicates stability, $+0.5$ indicates gradual worsening, and $+1.0$ indicates sharp escalation.
- A five-tier operational state classification:
  - `Improving`
  - `Stable`
  - `Slowly worsening`
  - `Rapidly worsening`
  - `Recovering`
- A 128-dimensional unit hypersphere latent embedding ($\|\mathbf{z}\|_2 = 1.0$) encoding historical progression for downstream escalation assessment (Slice 3.8).
- Fully transparent, machine-readable evidence grounded strictly in observable temporal shifts.

### What Trajectory IS NOT (Strict Clinical Boundaries):
- **NOT a clinical psychiatric prognosis**: The model does not predict disease progression or long-term clinical remission.
- **NOT a clinical diagnosis**: Does not predict depression, generalized anxiety, bipolar disorder, or PTSD.
- **NOT a suicide or self-harm predictor**: Urgent crisis risk is decoupled and handled exclusively by safety escalation protocols.
- **NOT an escalation action or triage decision**: Computing immediate counselor alerts or crisis dispatch is the exclusive role of the Escalation Policy Engine (Slice 3.8).
- **NOT a treatment recommendation**: The model never recommends medications, therapeutic interventions, or clinical referrals.

---

## 2. Model Design & Architectural Justification

### Why GRU + Statistical Temporal Aggregation (vs. Heavy Transformer Encoder)?

| Requirement | Heavy Transformer Encoder | GRU + Deterministic Temporal MLP | Architectural Decision |
| :--- | :--- | :--- | :--- |
| **Sequence Length** | Optimizes for long sequences ($T > 100$) | Tailored for short clinical history windows ($T \in [2, 10]$) | **GRU / Temporal MLP** prevents overfitting on short sequences |
| **Irregular Sampling ($\Delta t$)** | Requires complex continuous positional encodings | Continuous $\Delta t_{\text{hours}}$ feature directly modulates transitions | **GRU / Temporal MLP** natively captures non-uniform inter-session gaps |
| **Latency & Resource Footprint** | $\mathcal{O}(T^2)$ self-attention, $\approx 80\text{MB}+$ memory | $\mathcal{O}(T)$ recurrence, $<2\text{ms}$ CPU inference, $113\text{k}-163\text{k}$ params | **GRU / Temporal MLP** meets strict real-time edge/CPU budget |
| **Deterministic Fallback** | Hard to replicate accurately without heavy runtime | Full pure-Python arithmetic fallback without external dependencies | **Guarantees zero-dependency CPU fallback** |

The AAROH repository adopts a hybrid approach:
1. **PyTorch Mode (`PYTORCH_FROZEN` / `PYTORCH_FINETUNE`)**: Single-layer `nn.GRU(input_size=128, hidden_size=128)` with linear projection and temporal classification head.
2. **Fallback Mode (`FALLBACK`)**: Pure-Python temporal aggregation (timestep projection $\to$ mean pooling + first/last delta $\to$ MLP projection $\to$ unit hypersphere normalization $\to$ trajectory head).

---

## 3. Mathematical Formulation

### 3.1 Timestep Input Representation ($\mathbb{R}^{432}$)

Each interaction timestep $\mathbf{x}_t$ in an individual's history is packaged into a 432-dimensional composite vector:

$$\mathbf{x}_t = [\mathbf{e}_{\text{fused}} \;\|\; \mathbf{e}_{\text{distress}} \;\|\; s_{\text{distress}} \;\|\; \mathbf{l}_{\text{one-hot}} \;\|\; \mathbf{b}_{\text{values}} \;\|\; \mathbf{b}_{\text{mask}} \;\|\; \mathbf{g}_{\text{values}} \;\|\; \mathbf{g}_{\text{mask}} \;\|\; \tau_{\text{norm}}] \in \mathbb{R}^{432}$$

| Component | Dims | Source / Description | Missingness Policy |
| :--- | :--- | :--- | :--- |
| $\mathbf{e}_{\text{fused}}$ | 256 | Fused multimodal representation from Slice 3.5 | Neutral vector if missing |
| $\mathbf{e}_{\text{distress}}$ | 128 | Latent distress embedding from Slice 3.6 ($\|\mathbf{e}\|_2 = 1.0$) | Unit baseline vector |
| $s_{\text{distress}}$ | 1 | Continuous acute distress score in $[0.0, 1.0]$ | Standardized float |
| $\mathbf{l}_{\text{one-hot}}$ | 4 | One-hot discrete level (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) | Standard one-hot |
| $\mathbf{b}_{\text{values}}$ | 8 | Behavioural features (sleep, withdrawal, safety, appetite) | Standardized floats; zeroed if missing |
| $\mathbf{b}_{\text{mask}}$ | 8 | Behavioural missingness indicator ($1.0 = \text{present}$, $0.0 = \text{missing}$) | Preserves `None != 0.0` semantic integrity |
| $\mathbf{g}_{\text{values}}$ | 13 | Engagement features (session latency, frequency, drop-off) | Standardized floats; zeroed if missing |
| $\mathbf{g}_{\text{mask}}$ | 13 | Engagement missingness indicator ($1.0 = \text{present}$, $0.0 = \text{missing}$) | Preserves `None != 0.0` semantic integrity |
| $\tau_{\text{norm}}$ | 1 | Elapsed time since previous interaction: $\min(1.0, \Delta t_{\text{hours}} / 168.0)$ | Normalized $[0.0, 1.0]$ |

### 3.2 Sequence Windowing Strategy ($W = 10$)

For any case trajectory with $N$ interactions:
- **$N < W$**: Left-pad with zero vectors; `padding_mask = True` for padded positions, `False` for valid interactions.
- **$N = W$**: Use full sequence directly; `padding_mask = False` across all positions.
- **$N > W$**: Truncate to retain ONLY the most recent $W$ interactions in chronological order; `padding_mask = False`.

### 3.3 Latent State & Continuous Trajectory Score

1. **Latent Trajectory Embedding ($\mathbf{z} \in \mathbb{R}^{128}$)**:
   $$\mathbf{z} = \frac{\mathbf{h}_{\text{trajectory}}}{\|\mathbf{h}_{\text{trajectory}}\|_2 + \epsilon}$$
   Constrained to the unit hypersphere $\mathcal{S}^{127}$, providing scale-invariant angular representations for the downstream Escalation Model (Slice 3.8).

2. **Continuous Trajectory Score ($s_{\text{traj}} \in [-1.00, +1.00]$)**:
   $$s_{\text{traj}} = \sum_{c \in \mathcal{C}} P(c) \cdot \text{Score}(c)$$
   where:
   - $\text{Score}(\text{IMPROVING}) = -1.0$
   - $\text{Score}(\text{STABLE}) = 0.0$
   - $\text{Score}(\text{WORSENING}) = +0.5$
   - $\text{Score}(\text{RAPIDLY\_WORSENING}) = +1.0$

### 3.4 Operational Trajectory States

In addition to the 4 canonical labels required by Slice 3.8 contracts (`STABLE`, `IMPROVING`, `WORSENING`, `RAPIDLY_WORSENING`), the system produces an enriched 5-state clinical triage output:

$$\text{State}(s_{\text{traj}}, v, a) = \begin{cases}
\text{Rapidly worsening} & v \ge +0.20/\text{week} \lor \text{streak}_{\text{worsening}} \ge 3 \lor \Delta_{\text{baseline}} \ge 0.30 \\
\text{Slowly worsening} & v \ge +0.04/\text{week} \lor \text{streak}_{\text{worsening}} \ge 2 \lor \Delta_{\text{baseline}} \ge 0.15 \\
\text{Recovering} & (\text{distress}_0 \ge 0.55 \land \text{distress}_t \le 0.40) \lor (\text{streak}_{\text{improving}} \ge 2 \land \text{distress}_0 \ge 0.50) \\
\text{Improving} & v \le -0.04/\text{week} \lor \text{streak}_{\text{improving}} \ge 2 \lor \Delta_{\text{baseline}} \le -0.15 \\
\text{Stable} & \text{otherwise}
\end{cases}$$

---

## 4. Explainability & Evidence Architecture

Every prediction produces machine-readable `TrajectoryEvidence` strictly grounded in input history:

```json
{
  "trajectory_score": 0.83,
  "trajectory_state": "Rapidly worsening",
  "trajectory_label": "RAPIDLY_WORSENING",
  "confidence": 0.91,
  "trend_velocity": 0.17,
  "trend_velocity_display": "+0.17/week",
  "trend_acceleration": 0.06,
  "reasons": [
    "Distress increased for 4 consecutive interactions",
    "Negative trend persisted for 12 days (net shift: +0.45)",
    "Sleep disruption increased across recent interactions",
    "Engagement decreased across recent interactions"
  ],
  "observations_count": 4,
  "history_span_days": 12.0,
  "delta_from_baseline": 0.45,
  "delta_from_previous": 0.15,
  "model_version": "aaroh-trajectory-v1",
  "label_disclaimer": "SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH"
}
```

---

## 5. End-to-End Inference Pipeline (`TrajectoryInferencePipeline`)

The complete production flow wires all upstream subsystems sequentially:

```
Interaction Text ("I feel terrified and hopeless")
   │
   ▼
TextEmotionModel (Slice 3.3)
   ├─► Emotion Probabilities (fear: 0.65, sadness: 0.40)
   └─► Emotion Embedding (768-dim)
   │
   ▼
DynamicDistressModel (Slice 3.6)
   ├─► acute distress_score: 0.68
   ├─► distress_level: HIGH
   └─► distress_embedding: 128-dim unit vector
   │
   ▼
Longitudinal History Window Assembly
   ├─► Append new interaction to case history (preserving chronological order)
   ├─► Compute inter-interaction elapsed time (Δt_hours)
   └─► Construct 432-dim TrajectoryInputRecord
   │
   ▼
LongitudinalTrajectoryModel (Slice 3.7)
   │
   ▼
Trajectory Prediction Payload
   ├─ trajectory_score: +0.83
   ├─ trajectory_state: "Rapidly worsening"
   ├─ trajectory_label: "RAPIDLY_WORSENING"
   ├─ trend_velocity: +0.17/week
   ├─ trend_acceleration: +0.06
   ├─ confidence: 0.91
   ├─ reasons: [...]
   └─ trajectory_embedding: 128-dim unit vector (consumed by Slice 3.8 Escalation)
```

---

## 6. Integration Contract with Slice 3.8 (Escalation Prediction)

The Escalation Model (Slice 3.8) directly consumes:
1. `trajectory_score`: continuous linear feature in $[-1.0, 1.0]$.
2. `trajectory_label`: discrete categorical indicator (`STABLE`, `IMPROVING`, `WORSENING`, `RAPIDLY_WORSENING`).
3. `trajectory_probabilities`: multi-class probability dictionary.
4. `trajectory_embedding`: 128-dimensional unit vector concatenating into the escalation feature vector.

---

## 7. Verification & Test Suite

The subsystem is verified by 43 unit tests across three dedicated test suites:
- `backend/ml/tests/test_longitudinal_subsystem.py`: 11 tests covering improving, worsening, stable, noisy, missing timestamps, multilingual text history, artifact roundtrip, and explainability.
- `backend/ml/tests/test_longitudinal_trajectory_model.py`: 19 architectural, padding, truncation, parameter accounting, and boundary tests.
- `backend/ml/tests/test_longitudinal_features.py`: 13 feature extraction and trend classification tests.
