// AAROH Case Service — Conforming to Backend Contracts & Rule 6 (De-identified Synthetic Data)

const initialCases = [
  {
    id: 'AAROH-CAS-9821',
    beneficiaryId: 'BEN-9821-DEL',
    beneficiaryName: 'Meera Sharma (Case #9821)',
    age: 28,
    gender: 'Female',
    district: 'South Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-08-12',
    priority: 'HIGH',
    stage: 'Assessment Completed',
    riskLevel: 'High',
    distressScore: 74,
    baselineScore: 56,
    baselineDeviation: '+18%',
    trend: 'Worsening',
    escalationProbability: '82%',
    predictionHorizon: '7 Days',
    confidence: '89%',
    assignedOfficial: 'Dr. Rajesh Verma (Senior Clinical Psychologist)',
    slaHoursRemaining: 4,
    slaStatus: 'URGENT',
    status: 'IN_PROGRESS',
    safeChannel: 'Voice Check-in & Tele-MANAS',
    safeHours: '17:00 – 19:00 IST',
    contributingFactors: [
      'Statistically significant +18% distress increase relative to calibrated 30-day baseline.',
      'Acoustic pitch perturbation and speech rate deceleration observed in check-in on 03 Sep.',
      'Linguistic distress markers detected: heightened fear terms, expressed helplessness.',
      'Check-in completion interval lengthened from daily to 48-hour latency.',
    ],
    recommendedIntervention: 'Trauma-Informed Psychological First Aid & Safe Housing Verification',
    timeline: [
      { date: '2026-09-04 18:15', type: 'PREDICTION_FLAG', title: 'Distress Spike Alert', description: 'Algorithmic baseline deviation reached +18%. Escalation probability flagged at 82%.' },
      { date: '2026-09-03 17:30', type: 'INTERACTION_VOICE', title: 'Voice Check-In Completed', description: 'Beneficiary completed 84-second Hindi audio response during designated safe hours.' },
      { date: '2026-08-28 11:00', type: 'INTERVENTION', title: 'Clinical Counselling Session #2', description: 'Cognitive grounding session conducted by Dr. Rajesh Verma. Coping mechanisms reinforced.' },
      { date: '2026-08-20 16:45', type: 'INTERACTION_TEXT', title: 'Text Check-In Completed', description: 'Reported moderate sleep disturbance; confirmed access to immediate safe shelter.' },
      { date: '2026-08-12 10:00', type: 'CASE_REGISTERED', title: 'Case Formally Registered', description: 'Referred under SC/ST Prevention of Atrocities Act. Baseline distress calibrated at 56/100.' },
    ],
    interactions: [
      { id: 'INT-901', date: '2026-09-03 17:30', channel: 'Voice Audio', language: 'Hindi', duration: '84s', status: 'Completed', textExcerpt: 'Pichle do din se darr lag raha hai... neend theek se nahi aa rahi.', voiceAvailable: true, qualityScore: '98%' },
      { id: 'INT-884', date: '2026-08-27 17:45', channel: 'Voice Audio', language: 'Hindi', duration: '62s', status: 'Completed', textExcerpt: 'Thoda behtar mehsoos hua kal ke counselling ke baad.', voiceAvailable: true, qualityScore: '96%' },
      { id: 'INT-842', date: '2026-08-20 16:45', channel: 'Text Form', language: 'Hindi / English', duration: '—', status: 'Completed', textExcerpt: 'Routine daily check-in: Feeling exhausted but physically safe.', voiceAvailable: false, qualityScore: '100%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 56, baseline: 56 },
      { day: 'Day 7', score: 58, baseline: 56 },
      { day: 'Day 14', score: 54, baseline: 56 },
      { day: 'Day 21', score: 62, baseline: 56 },
      { day: 'Day 25', score: 68, baseline: 56 },
      { day: 'Day 30', score: 74, baseline: 56 },
    ],
  },
  {
    id: 'AAROH-CAS-8402',
    beneficiaryId: 'BEN-8402-DEL',
    beneficiaryName: 'Beneficiary Anon-8402',
    age: 34,
    gender: 'Male',
    district: 'South Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-08-25',
    priority: 'CRITICAL',
    stage: 'Escalated to Nodal Officer',
    riskLevel: 'Critical',
    distressScore: 89,
    baselineScore: 61,
    baselineDeviation: '+28%',
    trend: 'Rapidly Worsening',
    escalationProbability: '94%',
    predictionHorizon: '48 Hours',
    confidence: '92%',
    assignedOfficial: 'Dr. Rajesh Verma / Escalated to DM Nodal Officer',
    slaHoursRemaining: 1,
    slaStatus: 'OVERDUE_RISK',
    status: 'ESCALATED',
    safeChannel: 'Secure Voice Only',
    safeHours: '19:00 – 21:00 IST',
    contributingFactors: [
      'Rapid severe deviation (+28%) over 72-hour window.',
      'Direct mention of external threat incidents and physical isolation.',
      'Somatic panic and tremor markers flagged in voice acoustic envelope.',
    ],
    recommendedIntervention: 'Emergency Witness Protection Protocol & Urgent Psychiatric Consultation',
    timeline: [
      { date: '2026-09-05 09:10', type: 'SLA_BREACH_WARNING', title: 'Statutory SLA Countdown Alert', description: 'Under 1 hour remaining before automated DM escalation breach notification.' },
      { date: '2026-09-04 20:00', type: 'PREDICTION_FLAG', title: 'Critical Risk Threshold Triggered', description: 'Score escalated to 89. Emergency protocol recommended.' },
      { date: '2026-08-25 14:00', type: 'CASE_REGISTERED', title: 'Case Registered', description: 'Intake initiated following local nodal cell report.' },
    ],
    interactions: [
      { id: 'INT-910', date: '2026-09-04 19:40', channel: 'Voice Audio', language: 'Hindi', duration: '110s', status: 'Completed', textExcerpt: 'Humein lag raha hai wo log hamare aas paas ghoom rahe hain.', voiceAvailable: true, qualityScore: '95%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 61, baseline: 61 },
      { day: 'Day 4', score: 65, baseline: 61 },
      { day: 'Day 7', score: 78, baseline: 61 },
      { day: 'Day 10', score: 89, baseline: 61 },
    ],
  },
  {
    id: 'AAROH-CAS-7719',
    beneficiaryId: 'BEN-7719-DEL',
    beneficiaryName: 'Beneficiary Anon-7719',
    age: 22,
    gender: 'Female',
    district: 'South Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-08-01',
    priority: 'MEDIUM',
    stage: 'Active Follow-up',
    riskLevel: 'Medium',
    distressScore: 58,
    baselineScore: 55,
    baselineDeviation: '+3%',
    trend: 'Stable',
    escalationProbability: '24%',
    predictionHorizon: '30 Days',
    confidence: '84%',
    assignedOfficial: 'Dr. Rajesh Verma (Senior Clinical Psychologist)',
    slaHoursRemaining: 24,
    slaStatus: 'COMPLIANT',
    status: 'ASSIGNED',
    safeChannel: 'WhatsApp / In-App Text',
    safeHours: '11:00 – 13:00 IST',
    contributingFactors: [
      'Distress within calibrated tolerance range (+3%).',
      'Positive response to cognitive restructuring sessions.',
      'Regular timely check-in adherence.',
    ],
    recommendedIntervention: 'Bi-weekly Supportive Therapy & Statutory Compensation Tracking',
    timeline: [
      { date: '2026-09-02 11:30', type: 'INTERACTION_TEXT', title: 'Routine Check-In Received', description: 'Beneficiary reported stable emotional equilibrium; continuing college study.' },
      { date: '2026-08-01 10:00', type: 'CASE_REGISTERED', title: 'Initial Intake', description: 'Baseline distress established at 55/100.' },
    ],
    interactions: [
      { id: 'INT-812', date: '2026-09-02 11:30', channel: 'Text Form', language: 'English', duration: '—', status: 'Completed', textExcerpt: 'Doing fine today, went for evening walk as advised.', voiceAvailable: false, qualityScore: '100%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 55, baseline: 55 },
      { day: 'Day 10', score: 57, baseline: 55 },
      { day: 'Day 20', score: 54, baseline: 55 },
      { day: 'Day 30', score: 58, baseline: 55 },
    ],
  },
  {
    id: 'AAROH-CAS-6105',
    beneficiaryId: 'BEN-6105-DEL',
    beneficiaryName: 'Beneficiary Anon-6105',
    age: 42,
    gender: 'Male',
    district: 'South Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-07-15',
    priority: 'LOW',
    stage: 'Post-Intervention Review',
    riskLevel: 'Low',
    distressScore: 32,
    baselineScore: 52,
    baselineDeviation: '-20%',
    trend: 'Improving',
    escalationProbability: '8%',
    predictionHorizon: '90 Days',
    confidence: '95%',
    assignedOfficial: 'Dr. Rajesh Verma (Senior Clinical Psychologist)',
    slaHoursRemaining: 72,
    slaStatus: 'COMPLIANT',
    status: 'COMPLETED',
    safeChannel: 'SMS & App Notifications',
    safeHours: '10:00 – 12:00 IST',
    contributingFactors: [
      'Substantial longitudinal distress recovery (-20% from baseline).',
      'Successful financial relief disbursement verified into beneficiary account.',
      'Zero distress spikes across 6 consecutive weekly evaluations.',
    ],
    recommendedIntervention: 'Transition to Monthly Longitudinal Monitoring',
    timeline: [
      { date: '2026-08-30 10:00', type: 'OUTCOME_RECORDED', title: 'Relief Intervention Closed', description: 'Target psychosocial milestones attained. Monthly maintenance scheduled.' },
      { date: '2026-07-15 09:30', type: 'CASE_REGISTERED', title: 'Registered Case', description: 'Initial distress 52/100.' },
    ],
    interactions: [
      { id: 'INT-730', date: '2026-08-29 10:15', channel: 'Voice Audio', language: 'Hindi', duration: '45s', status: 'Completed', textExcerpt: 'Ab sab normal hai, relief fund bhi mil gaya hai.', voiceAvailable: true, qualityScore: '99%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 52, baseline: 52 },
      { day: 'Day 15', score: 48, baseline: 52 },
      { day: 'Day 30', score: 40, baseline: 52 },
      { day: 'Day 45', score: 32, baseline: 52 },
    ],
  },
];

class CaseService {
  constructor() {
    this.cases = [...initialCases];
  }

  getAllCases() {
    return Promise.resolve([...this.cases]);
  }

  getCaseById(id) {
    const found = this.cases.find((c) => c.id === id);
    return Promise.resolve(found ? { ...found } : null);
  }

  recordOutcome(caseId, outcomePayload) {
    const caseIndex = this.cases.findIndex((c) => c.id === caseId);
    if (caseIndex === -1) return Promise.reject(new Error('Case not found'));

    const updatedCase = { ...this.cases[caseIndex] };
    updatedCase.status = outcomePayload.status || 'COMPLETED';
    updatedCase.stage = `Outcome: ${outcomePayload.outcomeType}`;
    
    const now = new Date();
    const formattedDate = now.toISOString().slice(0, 16).replace('T', ' ');
    updatedCase.timeline.unshift({
      date: formattedDate,
      type: 'OUTCOME_RECORDED',
      title: `Outcome: ${outcomePayload.outcomeType}`,
      description: outcomePayload.notes || 'Clinical outcome registered by assigned official.',
      author: outcomePayload.officerName || 'Dr. Rajesh Verma',
      followUpDate: outcomePayload.followUpDate,
    });

    this.cases[caseIndex] = updatedCase;
    return Promise.resolve(updatedCase);
  }

  updateIntervention(caseId, interventionPayload) {
    const caseIndex = this.cases.findIndex((c) => c.id === caseId);
    if (caseIndex === -1) return Promise.reject(new Error('Case not found'));

    const updatedCase = { ...this.cases[caseIndex] };
    updatedCase.recommendedIntervention = interventionPayload.category;
    updatedCase.status = 'IN_PROGRESS';
    updatedCase.slaHoursRemaining = interventionPayload.slaHours || 24;

    const now = new Date();
    const formattedDate = now.toISOString().slice(0, 16).replace('T', ' ');
    updatedCase.timeline.unshift({
      date: formattedDate,
      type: 'INTERVENTION_ASSIGNED',
      title: `Action Assigned: ${interventionPayload.category}`,
      description: interventionPayload.instructions || 'Statutory human intervention initiated.',
    });

    this.cases[caseIndex] = updatedCase;
    return Promise.resolve(updatedCase);
  }
}

export const caseService = new CaseService();
