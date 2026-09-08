// AAROH Role-Based Notification Service
// Provides strictly segregated operational notifications per official persona & citizen role

export const ROLE_NOTIFICATIONS = {
  VICTIM: [
    {
      id: 'notif-vic-1',
      title: 'Safe Check-In Window Active',
      time: '12m ago',
      category: 'CHECK-IN',
      priority: 'primary',
      read: false,
      message: 'Your designated safe check-in window (17:00 – 19:00 IST) is open. You may submit your 90-second voice or text update.',
      actionLabel: 'Submit Daily Check-In',
    },
    {
      id: 'notif-vic-2',
      title: 'Clinical Review Logged',
      time: '1h ago',
      category: 'CARE TEAM',
      priority: 'success',
      read: false,
      message: 'Dr. Rajesh Varma reviewed your recent check-in. Coping trajectory is marked stable (Distress score: 38/100).',
    },
    {
      id: 'notif-vic-3',
      title: 'Statutory Relief Progress',
      time: '3h ago',
      category: 'LEGAL & WELFARE',
      priority: 'info',
      read: false,
      message: 'Phase-1 financial assistance verification under SC/ST PoA Rule 12(4) was forwarded to the South Delhi DM Cell.',
    },
    {
      id: 'notif-vic-4',
      title: 'DPDP Privacy Assurance',
      time: 'Yesterday',
      category: 'DATA PRIVACY',
      priority: 'neutral',
      read: true,
      message: 'Zero-knowledge encryption stamp active. Your voice biometrics and check-in records are strictly restricted to your care team.',
    },
  ],

  COUNSELLOR: [
    {
      id: 'notif-cns-1',
      title: 'Acoustic Distress Spike Flagged',
      time: '8m ago',
      category: 'URGENT TRIAGE',
      priority: 'critical',
      read: false,
      message: 'Beneficiary Meera Sharma (#CAS-9821) completed a 90s audio check-in. Algorithmic acoustic analysis flagged +18% baseline deviation.',
      actionLabel: 'Review Audio Telemetry',
    },
    {
      id: 'notif-cns-2',
      title: 'SLA Clinical Response Alert',
      time: '32m ago',
      category: 'SLA COMPLIANCE',
      priority: 'critical',
      read: false,
      message: 'Case #8402 (High Distress: 88/100) clinical review window has 48 minutes remaining before mandatory district escalation.',
      actionLabel: 'Open Case Triage',
    },
    {
      id: 'notif-cns-3',
      title: 'Intervention Plan Approved',
      time: '2h ago',
      category: 'CASELOAD',
      priority: 'success',
      read: false,
      message: 'South Delhi District Nodal Cell approved psychological rehabilitation voucher & safe housing plan for Case #4109.',
    },
    {
      id: 'notif-cns-4',
      title: 'Tele-MANAS Regional Transfer',
      time: '4h ago',
      category: 'INBOUND ROUTING',
      priority: 'info',
      read: true,
      message: '1 inbound crisis referral routed from national 14416 helpline. Assigned to your active South Delhi caseload (Total: 18 active).',
    },
  ],

  DISTRICT: [
    {
      id: 'notif-dst-1',
      title: 'DM Cell Urgent Escalation',
      time: '15m ago',
      category: 'DISTRICT ESCALATION',
      priority: 'critical',
      read: false,
      message: 'Case #8402 auto-escalated to District Magistrate oversight after counsellor response threshold exceeded. Immediate administrative intervention required.',
      actionLabel: 'Authorize Intervention',
    },
    {
      id: 'notif-dst-2',
      title: 'Counsellor Workload Warning',
      time: '45m ago',
      category: 'CAPACITY ALERT',
      priority: 'warning',
      read: false,
      message: 'South Delhi Sector 4 counselling wing reached 92% capacity (18/20 caseload threshold). Backup psychologists alerted for reserve activation.',
    },
    {
      id: 'notif-dst-3',
      title: 'Relief Disbursal Sanctioned',
      time: '2h ago',
      category: 'FINANCIAL SANCTION',
      priority: 'success',
      read: false,
      message: 'Statutory emergency relief grant of ₹1,25,000 sanctioned for Beneficiary Meera Sharma under District Victim Relief provisions.',
    },
    {
      id: 'notif-dst-4',
      title: 'Daily District Caseload Synthesis',
      time: '5h ago',
      category: 'JURISDICTION',
      priority: 'neutral',
      read: true,
      message: '42 active clinical interventions monitored across South Delhi jurisdiction today with 97.4% on-time resolution rate.',
    },
  ],

  STATE: [
    {
      id: 'notif-sta-1',
      title: 'Inter-District SLA Disparity Alert',
      time: '25m ago',
      category: 'STATE MONITORING',
      priority: 'warning',
      read: false,
      message: 'South-West Delhi district reported a 16% increase in 24h unresolved high-distress cases over the last 48 hours. Nodal advisory dispatched.',
      actionLabel: 'Inspect District Variance',
    },
    {
      id: 'notif-sta-2',
      title: 'Cross-District Resource Reallocation',
      time: '1h ago',
      category: 'RESOURCE OPTIMIZATION',
      priority: 'info',
      read: false,
      message: 'Executive transfer of 6 reserve clinical counsellors from North-East Delhi to South Delhi finalized to manage regional case influx.',
    },
    {
      id: 'notif-sta-3',
      title: 'State Distress Prevention Index',
      time: '3h ago',
      category: 'ANALYTICS',
      priority: 'success',
      read: false,
      message: 'Delhi NCT composite mental health distress prevention index reached 84.6% (+3.2% vs previous quarter). 11/11 districts reporting live telemetry.',
    },
    {
      id: 'notif-sta-4',
      title: 'Departmental Review Scheduled',
      time: '6h ago',
      category: 'DIRECTORATE',
      priority: 'neutral',
      read: true,
      message: 'Principal Secretary quarterly review on Delhi NCT Victim Mental Health & Protection System confirmed for tomorrow, 10:30 AM.',
    },
  ],

  NATIONAL: [
    {
      id: 'notif-nat-1',
      title: 'Macro Trend Anomaly Detected',
      time: '30m ago',
      category: 'NATIONAL INTEL',
      priority: 'warning',
      read: false,
      message: 'Aggregated distress indicators across Northern Zone states increased by 8.4% this week. Early intervention circular drafted for State Directors.',
      actionLabel: 'View National Heatmap',
    },
    {
      id: 'notif-nat-2',
      title: 'Inter-State Mobile Unit Deployment',
      time: '2h ago',
      category: 'CENTRAL MOBILIZATION',
      priority: 'info',
      read: false,
      message: 'Authorized emergency deployment of 12 central mobile Tele-MANAS mental health relief vans across high-vulnerability tribal districts.',
    },
    {
      id: 'notif-nat-3',
      title: 'National Tele-MANAS Ingestion Synced',
      time: '4h ago',
      category: 'CENTRAL INGESTION',
      priority: 'success',
      read: false,
      message: 'Central data sync completed across 28 States & 8 UTs. Over 1,420,000 anonymized interactions cataloged under national surveillance registry.',
    },
    {
      id: 'notif-nat-4',
      title: 'Parliamentary Standing Committee Dossier',
      time: '6h ago',
      category: 'CABINET REPORT',
      priority: 'neutral',
      read: true,
      message: 'Q3 National Mental Health Monitoring & Victim Distress Mitigation Report compiled and submitted to Ministry of Social Justice & Empowerment.',
    },
  ],

  ADMIN: [
    {
      id: 'notif-adm-1',
      title: 'DPDP 2023 Statutory Compliance Stamp',
      time: '12m ago',
      category: 'COMPLIANCE',
      priority: 'success',
      read: false,
      message: 'Automated Section 6 explicit consent verification executed across all portals. 100% cryptographic hashes verified without discrepancy.',
      actionLabel: 'View Audit Trail',
    },
    {
      id: 'notif-adm-2',
      title: 'API Voice Microservice Spike',
      time: '40m ago',
      category: 'SYSTEM HEALTH',
      priority: 'warning',
      read: false,
      message: 'Voice feature extraction microservice handled 5,100 concurrent requests/min during evening check-in window. Latency nominal at 38ms.',
    },
    {
      id: 'notif-adm-3',
      title: 'Privileged Session Audit Recorded',
      time: '2h ago',
      category: 'SECURITY AUDIT',
      priority: 'neutral',
      read: false,
      message: 'Privileged oversight access authenticated for State Nodal Authority from whitelisted NIC Gov Gateway IP (TLS 1.3 / SHA-256).',
    },
    {
      id: 'notif-adm-4',
      title: 'Zero-Trust KMS Master Key Rotation',
      time: '8h ago',
      category: 'CRYPTOGRAPHY',
      priority: 'info',
      read: true,
      message: 'Scheduled 90-day AES-256-GCM master database encryption key rotation completed smoothly across all regional data nodes.',
    },
  ],
};

/**
 * Normalizes user role string to one of standard keys
 * @param {string} role 
 * @returns {'VICTIM'|'COUNSELLOR'|'DISTRICT'|'STATE'|'NATIONAL'|'ADMIN'}
 */
export const normalizeNotificationRole = (role) => {
  if (!role) return 'VICTIM';
  const r = String(role).toUpperCase().trim();
  if (r === 'CITIZEN' || r === 'VICTIM') return 'VICTIM';
  if (r === 'COUNSELLOR') return 'COUNSELLOR';
  if (r === 'DISTRICT') return 'DISTRICT';
  if (r === 'STATE') return 'STATE';
  if (r === 'NATIONAL') return 'NATIONAL';
  if (r === 'ADMIN') return 'ADMIN';
  return 'VICTIM';
};

/**
 * Get notification list for a specific role
 * @param {string} role 
 * @returns {Array} List of notification objects
 */
export const getNotificationsForRole = (role) => {
  const norm = normalizeNotificationRole(role);
  return ROLE_NOTIFICATIONS[norm] || ROLE_NOTIFICATIONS.VICTIM;
};

/**
 * Get human-readable role badge and scope description for the notification drawer header
 * @param {string} role 
 * @returns {{ badge: string, scope: string, color: string }}
 */
export const getRoleNotificationMeta = (role) => {
  const norm = normalizeNotificationRole(role);
  switch (norm) {
    case 'VICTIM':
      return {
        badge: 'Citizen Beneficiary',
        scope: 'Confidential Care & Wellness Channel',
        color: '#1E3A8A',
      };
    case 'COUNSELLOR':
      return {
        badge: 'Clinical Caseload',
        scope: 'Tele-MANAS & Regional Triage Alerts',
        color: '#7C3AED',
      };
    case 'DISTRICT':
      return {
        badge: 'District Magistrate Cell',
        scope: 'South Delhi Administrative Alerts',
        color: '#D97706',
      };
    case 'STATE':
      return {
        badge: 'State Oversight Directorate',
        scope: 'Delhi NCT Multi-District Surveillance',
        color: '#2563EB',
      };
    case 'NATIONAL':
      return {
        badge: 'National Directorate',
        scope: 'Ministry of Social Justice & Central Telemetry',
        color: '#0D9488',
      };
    case 'ADMIN':
      return {
        badge: 'System Authority',
        scope: 'Security Audit & Infrastructure Telemetry',
        color: '#475569',
      };
    default:
      return {
        badge: 'Operational Alerts',
        scope: 'AAROH Official System',
        color: '#1E3A8A',
      };
  }
};
