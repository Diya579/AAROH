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
    primaryAssignee: 'Dr. Rajesh Verma',
    backupAssignee: 'Dr. Sunita Rao',
    capacityIndicator: '85%',
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
    primaryAssignee: 'Dr. Rajesh Verma',
    backupAssignee: 'Shri Vikram Malhotra',
    capacityIndicator: '90%',
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
    primaryAssignee: 'Dr. Rajesh Verma',
    backupAssignee: 'Dr. Priya Nambiar',
    capacityIndicator: '70%',
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
    primaryAssignee: 'Dr. Rajesh Verma',
    backupAssignee: 'Dr. Sunita Rao',
    capacityIndicator: '50%',
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
  // Additional Multi-District & Multi-State Synthetic Cases for Day 3 Analytics & Drill-Down
  {
    id: 'AAROH-CAS-5201',
    beneficiaryId: 'BEN-5201-DEL',
    beneficiaryName: 'Beneficiary Anon-5201',
    age: 31,
    gender: 'Female',
    district: 'North Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-08-18',
    priority: 'HIGH',
    stage: 'Clinical Triage',
    riskLevel: 'High',
    distressScore: 78,
    baselineScore: 58,
    baselineDeviation: '+20%',
    trend: 'Worsening',
    escalationProbability: '86%',
    predictionHorizon: '5 Days',
    confidence: '90%',
    assignedOfficial: 'Dr. Sunita Rao',
    primaryAssignee: 'Dr. Sunita Rao',
    backupAssignee: 'Dr. Rajesh Verma',
    capacityIndicator: '75%',
    slaHoursRemaining: 3,
    slaStatus: 'URGENT',
    status: 'ASSIGNED',
    safeChannel: 'Tele-MANAS Audio Call',
    safeHours: '16:00 – 18:00 IST',
    contributingFactors: [
      'Social ostracization indicators flagged in North Delhi rural belt.',
      'Sustained high baseline shift (+20%).',
    ],
    recommendedIntervention: 'Legal Aid (NALSA) & Immediate Safe Shelter Routing',
    timeline: [
      { date: '2026-09-04 14:00', type: 'CASE_ASSIGNED', title: 'Assigned to Dr. Sunita Rao', description: 'Urgent counselling protocol initiated.' },
    ],
    interactions: [
      { id: 'INT-601', date: '2026-09-04 16:30', channel: 'Voice Audio', language: 'Hindi', duration: '75s', status: 'Completed', textExcerpt: 'Gaon mein log pareshan kar rahe hain.', voiceAvailable: true, qualityScore: '97%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 58, baseline: 58 },
      { day: 'Day 10', score: 66, baseline: 58 },
      { day: 'Day 20', score: 78, baseline: 58 },
    ],
  },
  {
    id: 'AAROH-CAS-4309',
    beneficiaryId: 'BEN-4309-DEL',
    beneficiaryName: 'Beneficiary Anon-4309',
    age: 26,
    gender: 'Female',
    district: 'West Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-08-05',
    priority: 'MEDIUM',
    stage: 'Active Follow-up',
    riskLevel: 'Medium',
    distressScore: 60,
    baselineScore: 57,
    baselineDeviation: '+3%',
    trend: 'Stable',
    escalationProbability: '28%',
    predictionHorizon: '14 Days',
    confidence: '86%',
    assignedOfficial: 'Shri Vikram Malhotra',
    primaryAssignee: 'Shri Vikram Malhotra',
    backupAssignee: 'Dr. Priya Nambiar',
    capacityIndicator: '80%',
    slaHoursRemaining: 18,
    slaStatus: 'COMPLIANT',
    status: 'IN_PROGRESS',
    safeChannel: 'In-App Text Form',
    safeHours: '14:00 – 16:00 IST',
    contributingFactors: [
      'Job loss following court deposition.',
      'Stable response to psychological grounding.',
    ],
    recommendedIntervention: 'Rehabilitation & Livelihood Scheme Linkage',
    timeline: [
      { date: '2026-08-20 12:00', type: 'INTERVENTION', title: 'DLSA Retainer Consultation', description: 'Legal aid lawyer appointed.' },
    ],
    interactions: [
      { id: 'INT-550', date: '2026-09-01 14:30', channel: 'Text Form', language: 'Hindi', duration: '—', status: 'Completed', textExcerpt: 'Lawyer se baat ho gayi, thoda relief mila.', voiceAvailable: false, qualityScore: '100%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 57, baseline: 57 },
      { day: 'Day 15', score: 62, baseline: 57 },
      { day: 'Day 30', score: 60, baseline: 57 },
    ],
  },
  {
    id: 'AAROH-CAS-3180',
    beneficiaryId: 'BEN-3180-DEL',
    beneficiaryName: 'Beneficiary Anon-3180',
    age: 39,
    gender: 'Male',
    district: 'East Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-08-29',
    priority: 'CRITICAL',
    stage: 'Emergency Escrow',
    riskLevel: 'Critical',
    distressScore: 92,
    baselineScore: 64,
    baselineDeviation: '+28%',
    trend: 'Rapidly Worsening',
    escalationProbability: '96%',
    predictionHorizon: '24 Hours',
    confidence: '94%',
    assignedOfficial: 'Dr. Priya Nambiar',
    primaryAssignee: 'Dr. Priya Nambiar',
    backupAssignee: 'Dr. Rajesh Verma',
    capacityIndicator: '65%',
    slaHoursRemaining: 2,
    slaStatus: 'EMERGENCY',
    status: 'ESCALATED',
    safeChannel: 'Voice Only',
    safeHours: '18:00 – 20:00 IST',
    contributingFactors: [
      'Severe physical intimidation incident reported to local police.',
      'Extreme insomnia and panic symptom markers.',
    ],
    recommendedIntervention: 'Witness Protection Protocol & Emergency Police Escort',
    timeline: [
      { date: '2026-09-05 11:00', type: 'SLA_BREACH_WARNING', title: 'Statutory 2-Hour Alert', description: 'Urgent Police Protection Nodal Officer notified.' },
    ],
    interactions: [
      { id: 'INT-410', date: '2026-09-05 10:15', channel: 'Voice Audio', language: 'Hindi', duration: '95s', status: 'Completed', textExcerpt: 'Ghar par aakar dhamki dekar gaye hain, bohot dar lag raha hai.', voiceAvailable: true, qualityScore: '96%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 64, baseline: 64 },
      { day: 'Day 4', score: 78, baseline: 64 },
      { day: 'Day 7', score: 92, baseline: 64 },
    ],
  },
  {
    id: 'AAROH-CAS-2904',
    beneficiaryId: 'BEN-2904-DEL',
    beneficiaryName: 'Beneficiary Anon-2904',
    age: 35,
    gender: 'Female',
    district: 'Central Delhi',
    state: 'Delhi NCT',
    registrationDate: '2026-07-20',
    priority: 'LOW',
    stage: 'Stabilized Maintenance',
    riskLevel: 'Low',
    distressScore: 35,
    baselineScore: 50,
    baselineDeviation: '-15%',
    trend: 'Improving',
    escalationProbability: '6%',
    predictionHorizon: '60 Days',
    confidence: '96%',
    assignedOfficial: 'Dr. Sunita Rao',
    primaryAssignee: 'Dr. Sunita Rao',
    backupAssignee: 'Shri Vikram Malhotra',
    capacityIndicator: '40%',
    slaHoursRemaining: 48,
    slaStatus: 'COMPLIANT',
    status: 'COMPLETED',
    safeChannel: 'SMS Notifications',
    safeHours: '09:00 – 11:00 IST',
    contributingFactors: [
      'Full rehabilitation compensation disbursed.',
      'Stable psycho-social support verified by DM Cell.',
    ],
    recommendedIntervention: 'Continued Baseline Longitudinal Monitoring',
    timeline: [
      { date: '2026-08-25 15:00', type: 'OUTCOME_RECORDED', title: 'Rehabilitation Successfully Closed', description: 'Case transitioned to monthly welfare audit.' },
    ],
    interactions: [
      { id: 'INT-302', date: '2026-08-24 10:00', channel: 'Text Form', language: 'Hindi', duration: '—', status: 'Completed', textExcerpt: 'Sab kuch kushal mangal hai.', voiceAvailable: false, qualityScore: '100%' },
    ],
    distressHistory: [
      { day: 'Day 1', score: 50, baseline: 50 },
      { day: 'Day 15', score: 42, baseline: 50 },
      { day: 'Day 30', score: 35, baseline: 50 },
    ],
  },
  // Multi-State Examples
  {
    id: 'AAROH-CAS-1120',
    beneficiaryId: 'BEN-1120-MAH',
    beneficiaryName: 'Beneficiary Anon-1120',
    age: 29,
    gender: 'Female',
    district: 'Pune',
    state: 'Maharashtra',
    registrationDate: '2026-08-10',
    priority: 'HIGH',
    stage: 'Active Intervention',
    riskLevel: 'High',
    distressScore: 72,
    baselineScore: 54,
    baselineDeviation: '+18%',
    trend: 'Worsening',
    escalationProbability: '80%',
    predictionHorizon: '7 Days',
    confidence: '88%',
    assignedOfficial: 'Dr. Ananya Kulkarni',
    primaryAssignee: 'Dr. Ananya Kulkarni',
    backupAssignee: 'Dr. R. Patil',
    capacityIndicator: '82%',
    slaHoursRemaining: 4,
    slaStatus: 'URGENT',
    status: 'IN_PROGRESS',
    safeChannel: 'Voice (Marathi / Hindi)',
    safeHours: '17:00 – 19:00 IST',
    contributingFactors: ['Traumatic memory intrusive episodes', 'Pending SC/ST PoA charge sheet filing'],
    recommendedIntervention: 'Counselling / psychological support',
    timeline: [{ date: '2026-09-02 18:00', type: 'INTERACTION_VOICE', title: 'Marathi Voice Check-In', description: 'Speech analysis completed via regional ASR pipeline.' }],
    interactions: [{ id: 'INT-210', date: '2026-09-02 18:00', channel: 'Voice Audio', language: 'Marathi', duration: '70s', status: 'Completed', textExcerpt: 'Khup tras hoto ahe vichar karun.', voiceAvailable: true, qualityScore: '97%' }],
    distressHistory: [{ day: 'Day 1', score: 54, baseline: 54 }, { day: 'Day 15', score: 65, baseline: 54 }, { day: 'Day 30', score: 72, baseline: 54 }],
  },
  {
    id: 'AAROH-CAS-1085',
    beneficiaryId: 'BEN-1085-UP',
    beneficiaryName: 'Beneficiary Anon-1085',
    age: 45,
    gender: 'Male',
    district: 'Lucknow',
    state: 'Uttar Pradesh',
    registrationDate: '2026-08-20',
    priority: 'CRITICAL',
    stage: 'District Escalation',
    riskLevel: 'Critical',
    distressScore: 88,
    baselineScore: 60,
    baselineDeviation: '+28%',
    trend: 'Rapidly Worsening',
    escalationProbability: '93%',
    predictionHorizon: '24 Hours',
    confidence: '91%',
    assignedOfficial: 'Dr. S. K. Yadav',
    primaryAssignee: 'Dr. S. K. Yadav',
    backupAssignee: 'Shri Manoj Singh',
    capacityIndicator: '92%',
    slaHoursRemaining: 1,
    slaStatus: 'EMERGENCY',
    status: 'ESCALATED',
    safeChannel: 'Voice Only',
    safeHours: '20:00 – 22:00 IST',
    contributingFactors: ['Agrarian land coercion incident', 'High biometric tremor amplitude in voice'],
    recommendedIntervention: 'Witness protection & Urgent Magistrate Protection Order',
    timeline: [{ date: '2026-09-05 08:30', type: 'SLA_BREACH_WARNING', title: '1-Hour SLA Notice', description: 'Emergency District Protection Unit alerted.' }],
    interactions: [{ id: 'INT-190', date: '2026-09-04 20:30', channel: 'Voice Audio', language: 'Hindi', duration: '90s', status: 'Completed', textExcerpt: 'Khet mein aane se mana kiya hai, hamla karne ki koshish ki.', voiceAvailable: true, qualityScore: '94%' }],
    distressHistory: [{ day: 'Day 1', score: 60, baseline: 60 }, { day: 'Day 7', score: 75, baseline: 60 }, { day: 'Day 14', score: 88, baseline: 60 }],
  },
  {
    id: 'AAROH-CAS-0940',
    beneficiaryId: 'BEN-0940-TN',
    beneficiaryName: 'Beneficiary Anon-0940',
    age: 24,
    gender: 'Female',
    district: 'Chennai',
    state: 'Tamil Nadu',
    registrationDate: '2026-08-02',
    priority: 'MEDIUM',
    stage: 'Rehabilitation',
    riskLevel: 'Medium',
    distressScore: 52,
    baselineScore: 54,
    baselineDeviation: '-2%',
    trend: 'Stable',
    escalationProbability: '18%',
    predictionHorizon: '30 Days',
    confidence: '89%',
    assignedOfficial: 'Dr. Meenakshi Sundaram',
    primaryAssignee: 'Dr. Meenakshi Sundaram',
    backupAssignee: 'Dr. K. Swaminathan',
    capacityIndicator: '68%',
    slaHoursRemaining: 24,
    slaStatus: 'COMPLIANT',
    status: 'COMPLETED',
    safeChannel: 'Tamil Voice & Text',
    safeHours: '12:00 – 14:00 IST',
    contributingFactors: ['Educational placement secured', 'Regular family support framework'],
    recommendedIntervention: 'Financial / compensation assistance',
    timeline: [{ date: '2026-08-28 14:00', type: 'OUTCOME_RECORDED', title: 'Compensation Sanctioned', description: 'Tamil Nadu Adi Dravidar Welfare grant verified.' }],
    interactions: [{ id: 'INT-105', date: '2026-08-28 12:30', channel: 'Voice Audio', language: 'Tamil', duration: '55s', status: 'Completed', textExcerpt: 'College-il admission kidaithuvittadhu, romba sandhosham.', voiceAvailable: true, qualityScore: '98%' }],
    distressHistory: [{ day: 'Day 1', score: 54, baseline: 54 }, { day: 'Day 15', score: 53, baseline: 54 }, { day: 'Day 30', score: 52, baseline: 54 }],
  },
  {
    id: 'AAROH-CAS-0812',
    beneficiaryId: 'BEN-0812-KAR',
    beneficiaryName: 'Beneficiary Anon-0812',
    age: 33,
    gender: 'Female',
    district: 'Bengaluru Urban',
    state: 'Karnataka',
    registrationDate: '2026-07-28',
    priority: 'LOW',
    stage: 'Routine Maintenance',
    riskLevel: 'Low',
    distressScore: 34,
    baselineScore: 48,
    baselineDeviation: '-14%',
    trend: 'Improving',
    escalationProbability: '5%',
    predictionHorizon: '90 Days',
    confidence: '94%',
    assignedOfficial: 'Dr. Ramesh Hegde',
    primaryAssignee: 'Dr. Ramesh Hegde',
    backupAssignee: 'Dr. B. Shastry',
    capacityIndicator: '45%',
    slaHoursRemaining: 72,
    slaStatus: 'COMPLIANT',
    status: 'COMPLETED',
    safeChannel: 'Kannada / English Text',
    safeHours: '15:00 – 17:00 IST',
    contributingFactors: ['Stable workplace rehabilitation', 'Trauma resolution milestones attained'],
    recommendedIntervention: 'Continued monitoring',
    timeline: [{ date: '2026-08-22 16:00', type: 'OUTCOME_RECORDED', title: 'Longitudinal Clearance', description: 'Patient transitioned to self-care app log.' }],
    interactions: [{ id: 'INT-098', date: '2026-08-22 15:15', channel: 'Text Form', language: 'Kannada', duration: '—', status: 'Completed', textExcerpt: 'Ella sari aagide, dhanyavadagalu.', voiceAvailable: false, qualityScore: '100%' }],
    distressHistory: [{ day: 'Day 1', score: 48, baseline: 48 }, { day: 'Day 20', score: 40, baseline: 48 }, { day: 'Day 40', score: 34, baseline: 48 }],
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

  getCasesByDistrict(district) {
    if (!district || district === 'ALL') {
      return Promise.resolve([...this.cases]);
    }
    const filtered = this.cases.filter(
      (c) => c.district.toLowerCase() === district.toLowerCase()
    );
    return Promise.resolve(filtered);
  }

  getCasesByState(state) {
    if (!state || state === 'ALL') {
      return Promise.resolve([...this.cases]);
    }
    const filtered = this.cases.filter(
      (c) => c.state.toLowerCase() === state.toLowerCase()
    );
    return Promise.resolve(filtered);
  }

  // Section 13: Routing & Assignment Interface
  assignOfficial(caseId, assignmentPayload) {
    const caseIndex = this.cases.findIndex((c) => c.id === caseId);
    if (caseIndex === -1) return Promise.reject(new Error('Case not found'));

    const updatedCase = { ...this.cases[caseIndex] };
    updatedCase.primaryAssignee = assignmentPayload.primaryAssignee || updatedCase.primaryAssignee;
    updatedCase.backupAssignee = assignmentPayload.backupAssignee || updatedCase.backupAssignee;
    updatedCase.assignedOfficial = `${updatedCase.primaryAssignee} (Primary) / ${updatedCase.backupAssignee} (Backup)`;
    updatedCase.recommendedIntervention = assignmentPayload.category || updatedCase.recommendedIntervention;
    updatedCase.priority = assignmentPayload.priority || updatedCase.priority;
    updatedCase.slaHoursRemaining = assignmentPayload.slaHours || 24;
    updatedCase.slaStatus = assignmentPayload.slaHours <= 2 ? 'EMERGENCY' : assignmentPayload.slaHours <= 4 ? 'URGENT' : 'STANDARD';
    updatedCase.status = 'ASSIGNED';
    updatedCase.stage = `Assigned: ${assignmentPayload.category}`;

    const now = new Date();
    const formattedDate = now.toISOString().slice(0, 16).replace('T', ' ');
    updatedCase.timeline.unshift({
      date: formattedDate,
      type: 'INTERVENTION_ASSIGNED',
      title: `Intervention Assigned: ${assignmentPayload.category}`,
      description: `Primary Assignee: ${updatedCase.primaryAssignee} • Backup: ${updatedCase.backupAssignee} • Statutory SLA: ${assignmentPayload.slaHours}h. Instructions: ${assignmentPayload.instructions || 'Standard statutory protocol'}`,
    });

    this.cases[caseIndex] = updatedCase;
    return Promise.resolve(updatedCase);
  }

  // Section 14: Outcome Interface
  recordOutcome(caseId, outcomePayload) {
    const caseIndex = this.cases.findIndex((c) => c.id === caseId);
    if (caseIndex === -1) return Promise.reject(new Error('Case not found'));

    const updatedCase = { ...this.cases[caseIndex] };
    updatedCase.status = outcomePayload.status || (outcomePayload.outcomeType === 'Resolved' || outcomePayload.outcomeType === 'Counselling provided' ? 'COMPLETED' : 'IN_PROGRESS');
    updatedCase.stage = `Outcome Recorded: ${outcomePayload.outcomeType}`;
    
    const now = new Date();
    const formattedDate = now.toISOString().slice(0, 16).replace('T', ' ');
    updatedCase.timeline.unshift({
      date: formattedDate,
      type: 'OUTCOME_RECORDED',
      title: `Outcome: ${outcomePayload.outcomeType}`,
      description: outcomePayload.notes || 'Official clinical outcome registered into statutory monitoring audit log.',
      author: outcomePayload.officerName || updatedCase.primaryAssignee || 'Authorized Official',
      followUpDate: outcomePayload.followUpDate,
      followUpRequired: outcomePayload.followUpRequired,
    });

    this.cases[caseIndex] = updatedCase;
    return Promise.resolve(updatedCase);
  }

  updateIntervention(caseId, interventionPayload) {
    return this.assignOfficial(caseId, interventionPayload);
  }
}

export const caseService = new CaseService();

