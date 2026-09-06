# AAROH — Operational Intervention Rules & Specification
**Author:** Preet (Intervention, Routing, Outcomes & Analytics Owner)  
**Status:** FROZEN OPERATIONAL SPECIFICATION  
**Scope:** Action & Operational Subsystem (`Prediction Contract → Operational Priority → Intervention Recommendation → District Routing → Primary/Backup Assignment → SLA → Outcome → Closed Loop → Multi-Tier Analytics`)

---

## 1. System Philosophy & Ethical Boundaries

AAROH converts upstream predictive risk into structured, human-centered workflows.
1. **Human-in-the-Loop:** AI recommends and prioritizes. It **never** autonomously decides medical treatment, prescription, relocation, witness protection, or legal sanctions.
2. **Separation of Concerns:** The intervention subsystem consumes the upstream ML prediction contract. It **never** recalculates ML models or clinical distress scores.
3. **Traceability:** Every operational decision generates a grounded, explainable reason reflecting actual model outputs and consent states.

---

## 2. Upstream ML Prediction Contract & Uncertainty Handling

The intervention engine consumes the validated output from `backend.ml.contract.MlInferenceResult`.

### 2.1 Thresholds & Uncertainty Policies
* **High Escalation Threshold:** `escalation_probability >= 0.75`
* **Moderate Escalation Threshold:** `escalation_probability >= 0.40`
* **Confidence Floor:** `confidence >= 0.50`
* **Uncertainty Routing (Rule 9):**
  If `ml_status` is `LOW_CONFIDENCE`, `ABSTAINED`, or `INSUFFICIENT_DATA` (or `confidence < 0.50`), the engine **never** assumes low risk. It deterministically routes the case to:
  - `intervention_type`: `PRIORITY_HUMAN_REVIEW`
  - `priority`: `HIGH`
  - `reason.abstention_reason`: `"Model confidence is insufficient (<status>). Human review required."`

---

## 3. Consent Enforcement (Rule 8)

The system enforces four separate consent dimensions:
1. `monitoring_consent`
2. `text_analysis_consent`
3. `voice_analysis_consent`
4. `case_linkage_consent`

### Consent Rule:
* `monitoring_consent` is the **absolute gateway**. If `monitoring_consent == False`, automated interventions are completely halted:
  - `intervention_type`: `NO_AUTOMATED_INTERVENTION`
  - `priority`: `NONE`
  - `reason.abstention_reason`: `"Monitoring consent is absent or revoked; automated intervention blocked."`
* If secondary consents (`voice_analysis_consent`, etc.) are absent, they are recorded in `reason.consent_status` to explain feature exclusion without blocking urgent monitoring.

---

## 4. Risk → Priority & Decision Matrix (Rule 14)

| Situation | Risk Level | Trajectory | Probability | Confidence / Status | Intervention Recommendation | Priority | SLA Window |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **No Consent** | Any | Any | Any | Any | `NO_AUTOMATED_INTERVENTION` | `NONE` | None |
| **Uncertainty / Abstain** | Any | Any | Any | `LOW_CONFIDENCE` / `ABSTAINED` / $< 0.50$ | `PRIORITY_HUMAN_REVIEW` | `HIGH` | 24 Hours |
| **Critical Escalation** | `HIGH` | `RAPIDLY_WORSENING` | $\ge 0.75$ | $\ge 0.50$ | `PRIORITY_HUMAN_REVIEW` | `URGENT` | 4 Hours |
| **Elevated Escalation** | `HIGH` | Any | $\ge 0.75$ | $\ge 0.50$ | `PRIORITY_HUMAN_REVIEW` | `URGENT` | 4 Hours |
| **Deteriorating** | `MODERATE` | `WORSENING` / `RAPIDLY_WORSENING` | $\ge 0.40$ | $\ge 0.50$ | `HUMAN_FOLLOW_UP` | `HIGH` | 24 Hours |
| **Moderate Concern** | `MODERATE` | `STABLE` | $\ge 0.40$ | $\ge 0.50$ | `HUMAN_FOLLOW_UP` | `HIGH` | 24 Hours |
| **Improving Trend** | Any | `IMPROVING` / `RAPIDLY_IMPROVING` | $< 0.40$ | $\ge 0.50$ | `CONTINUE_MONITORING` | `LOW` | 120 Hours |
| **Stable Baseline** | `LOW` | `STABLE` | $< 0.40$ | $\ge 0.50$ | `ROUTINE_MONITORING` | `ROUTINE` | 72 Hours |

---

## 5. Eight Authorized Intervention Categories (Rule 7)

Human caseworkers review cases with suggested domain-specific support categories:
1. `COUNSELLING_PSYCHOLOGICAL_SUPPORT`
2. `MEDICAL_TREATMENT_REFERRAL`
3. `WITNESS_PROTECTION_SUPPORT` (suggested when intimidation/threat factors are detected)
4. `RELOCATION_SAFETY_SUPPORT` (suggested for urgent/high escalation cases)
5. `FINANCIAL_COMPENSATION_ASSISTANCE`
6. `LEGAL_AID`
7. `REHABILITATION_SUPPORT`
8. `CONTINUED_MONITORING`

---

## 6. District-Aware Routing & Deterministic Assignment (Rules 1, 2, 13)

### 6.1 Strict District Isolation
* **Case jurisdiction is authoritative:** Cases must be assigned **only** to officers within the case's specified district.
* **Cross-district routing is strictly forbidden.** If no local officer is available in that district, the router returns `ROUTING_UNAVAILABLE`.
* **Missing or invalid district:** Handled explicitly with status `INVALID_JURISDICTION`.

### 6.2 Target Role Mapping
* `PRIORITY_HUMAN_REVIEW` with `URGENT` $\to$ `DESIGNATED_OFFICER`
* `PRIORITY_HUMAN_REVIEW` with `HIGH` $\to$ `COUNSELLOR`
* `HUMAN_FOLLOW_UP` $\to$ `COUNSELLOR`
* `ROUTINE_MONITORING` / `CONTINUE_MONITORING` $\to$ `CASE_OFFICER`

### 6.3 Deterministic Tie-Breaking
Eligible officers within the district are filtered by `(role == target_role, is_available == True, active_caseload < max_capacity)`.
Sorting is strictly deterministic:
$$\text{Sort Key} = (\text{active\_caseload}, \text{official\_id})$$
1. Lowest active caseload wins.
2. If caseloads are equal, alphabetical `official_id` is the stable tie-breaker.

### 6.4 Backup Assignee Selection
* Backup assignee must satisfy the exact same district and capacity constraints.
* Selected as the second-best candidate from the sorted district pool, or falls back to a verified, available `DISTRICT_AUTHORITY` in the same district.
* If no backup exists in that district, `backup_assignee` remains `None`.

---

## 7. Centralized SLA Configuration & Overdue Logic (Rules 3, 4)

### 7.1 Windows by Priority
* `URGENT`: 4.0 Hours
* `HIGH`: 24.0 Hours
* `ROUTINE`: 72.0 Hours
* `LOW`: 120.0 Hours
* `NONE`: 0.0 Hours

### 7.2 Timestamps & Start Event
* All timestamps generated on the server are standardized to **timezone-aware UTC** (`datetime.now(timezone.utc)`).
* **SLA Start Event:** The creation of the intervention (`created_at`).

### 7.3 Overdue vs Completion Status Separation
* `is_overdue`: Evaluated as `now > due_at AND completed_at is None`.
* Once completed, an intervention is **never** actively overdue. Its terminal SLA compliance status is:
  - `MET` if `completed_at <= due_at`
  - `BREACHED` if `completed_at > due_at`
* Active interventions approaching the deadline (80% of window elapsed) are flagged as `DUE_SOON`.

---

## 8. Outcome Lifecycle & State Machine (Rules 5, 15)

### 8.1 Status Transition Rules
```text
PENDING   ──> ASSIGNED, ESCALATED, CANCELLED
ASSIGNED  ──> ACKNOWLEDGED, PENDING (reassign), ESCALATED, CANCELLED
ACKNOWLEDGED ──> IN_PROGRESS, ESCALATED
IN_PROGRESS  ──> COMPLETED, ESCALATED
ESCALATED    ──> ASSIGNED, ACKNOWLEDGED, IN_PROGRESS
COMPLETED    ──> (TERMINAL, no transitions permitted)
CANCELLED    ──> (TERMINAL, no transitions permitted)
```
Retrograde transitions (e.g. `COMPLETED → PENDING`) and shortcut jumps (e.g. `PENDING → COMPLETED`) raise a `ValueError`.

### 8.2 Outcome Recording
* Controlled vocabulary: `CONTACTED`, `COUNSELLING_PROVIDED`, `FOLLOW_UP_REQUIRED`, `REFERRED`, `UNABLE_TO_CONTACT`, `DECLINED`, `RESOLVED`, `OTHER`.
* Fields: `case_id`, `intervention_id`, `outcome_type`, `completed`, `follow_up_required`, `notes`, `recorded_at`.
* **Latest Outcome Selection:** Strictly resolved by finding `max(outcomes, key=recorded_at)`. List ordering is never assumed.

---

## 9. Closed-Loop Feedback (Rule 6)

Compares distress observation before intervention against distress observation after intervention completion:
* `diff <= -0.10` $\to$ `SUBSEQUENT_IMPROVEMENT`
* `diff >= 0.10` $\to$ `SUBSEQUENT_DETERIORATION`
* Otherwise $\to$ `SUBSEQUENT_STABLE`

*Rule:* Documented strictly as **observed temporal correlation**, never claiming causal clinical proof.

---

## 10. Multi-Tier Analytics & Privacy Safeguards (Rules 10, 11, 12)

### 10.1 Mathematically Sound Aggregations (Rule 11)
* **Never average percentages.** District SLA rates are not averaged to calculate state SLA rates.
* **Numerator & Denominator Rollup:**
  $$\text{State SLA Compliance Rate} = \frac{\sum_{\text{districts}} \text{met\_sla\_interventions}}{\sum_{\text{districts}} \text{evaluated\_sla\_interventions}} \times 100$$
  $$\text{State Avg Response Time} = \frac{\sum_{\text{districts}} \text{total\_response\_time\_sum\_hours}}{\sum_{\text{districts}} \text{total\_responded\_interventions}}$$
* The identical principle applies from State to National aggregation.

### 10.2 Small-Cell Privacy Suppression (<3) (Rule 10)
To prevent victim re-identification in sparse districts:
* Granular district counts of $1$ or $2$ are masked as `"<3"` in exported dictionary representations (`to_dict(suppress_small_cells=True)`).
* **Suppressed metrics:**
  - `risk_distribution.HIGH`, `risk_distribution.MODERATE`, `risk_distribution.LOW`
  - `trajectory_alerts.RAPIDLY_WORSENING`, `trajectory_alerts.WORSENING`
  - Specific counts in `outcome_distribution`
* **Preserved broad totals:** `total_monitored_cases`, `pending`, `completed`, and state/national macro totals are **not** suppressed.

### 10.3 Privacy & Missing Data Integrity (Rule 12)
* No raw victim statements, audio paths, transcript texts, or caseworker internal notes are exposed in analytics summaries.
* Missing metrics are represented strictly as `None`, remaining distinguishable from `0` or `0.0`.
