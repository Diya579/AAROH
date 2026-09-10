# AAROH — Frontend Implementation

> **AI-Powered Dynamic Mental Health Monitoring & Distress Prediction System for Victims of Atrocities**  
> Built strictly adhering to the **UX4G (Government of India 3.0)** Design System, GIGW 3.0 accessibility standards, and the Digital Personal Data Protection (DPDP) Act 2023.

---

## 👥 Frontend Team & Task Allocation

According to the **AAROH Frontend Master Implementation Plan (Section 30 & 35)**, the frontend team is structured as follows:

| Developer | Primary Responsibility | Day 1 Deliverables (Architecture & Auth) | Day 2 Deliverables (User & Counsellor) |
| :--- | :--- | :--- | :--- |
| **Yashashvi** | **Frontend Foundation, Architecture & User Experience** | • Frontend setup & Vite/React configuration<br>• UX4G theme & design tokens (`ux4g-theme.css`)<br>• Global layout (`Header`, `Navigation`, `Footer`)<br>• Public Home Page (`HomePage.jsx`)<br>• Sign-In Page with strict No-Sign-Up (`SignInPage.jsx`)<br>• Routing architecture & Role guards (`App.jsx`) | • User / Victim Dashboard (`VictimDashboard.jsx`)<br>• User Profile & Preferences (`UserProfilePreferencesModal.jsx`)<br>• Consent interface (`ConsentPreferencesModal.jsx`, `consentService.js`)<br>• Check-in interface (Voice & Text choices)<br>• Text interaction UI (`TextCheckInModal.jsx`)<br>• Voice interaction UI with 5-gate pipeline (`VoiceCheckInModal.jsx`)<br>• Monitoring history audit table<br>• Support & statutory intervention status<br>• Notifications drawer (`UX4GOffcanvas`) |
| **Blessy** | **Shared Components, Counsellor Workflow & Visualisations** | • Page & component hierarchy definition<br>• Reusable UX4G shared components (`src/components/common/`): Cards, Buttons, Tables, Badges, Modals, Offcanvas, Alerts, Accordion, Inputs, States<br>• Responsive & mobile layout patterns<br>• Accessibility baseline (WCAG 2.1 AA) | • Counsellor Dashboard (`CounsellorDashboard.jsx`)<br>• Caseload queue table<br>• Multi-criteria case filtering & search<br>• Case Detail Dossier (`CaseDetailModal.jsx`)<br>• Chronological Case Timeline<br>• Speech/Text Interaction history with ASR quality<br>• Distress visualisation (`DistressTrendChart.jsx`)<br>• Risk visualisation (`ModelExplainabilityCard.jsx`)<br>• Escalation information & SLA countdowns<br>• Intervention assignment (`InterventionActionModal.jsx`)<br>• Clinical outcome recording (`OutcomeRecordModal.jsx`) |

### 🔗 Backend Team Integration Contracts
The frontend interfaces consume and integrate against synthetic backend contracts developed by:
- **Diya**: Architecture, Database, Cloud, Integration & Voice/ASR Pipeline
- **Adwait**: AI/ML, Model Training & Longitudinal Distress Inference
- **Mahendra**: FastAPI, Application Layer & Database Integration
- **Preet**: Intervention, Routing, Outcomes & Analytics

---

## 🏛️ Project Structure & Component Arrangements

```
aaroh-frontend/
├── public/
│   ├── ashoka-emblem.png         # State Emblem of India
│   └── favicon.svg
├── src/
│   ├── assets/                   # Static media & emblem assets
│   ├── components/
│   │   ├── auth/                 # [Yashashvi] Route Guards & Protected Routes
│   │   │   └── ProtectedRoute.jsx
│   │   ├── common/               # [Blessy] Shared UX4G Reusable Component Suite (Rule 34.10)
│   │   │   ├── AshokaEmblem.jsx
│   │   │   ├── GlobalOffcanvasDrawer.jsx
│   │   │   ├── UX4GAccordion.jsx
│   │   │   ├── UX4GAlert.jsx
│   │   │   ├── UX4GBadge.jsx
│   │   │   ├── UX4GButton.jsx
│   │   │   ├── UX4GCard.jsx
│   │   │   ├── UX4GEmptyState.jsx
│   │   │   ├── UX4GErrorState.jsx
│   │   │   ├── UX4GFooter.jsx
│   │   │   ├── UX4GHeader.jsx
│   │   │   ├── UX4GInput.jsx
│   │   │   ├── UX4GLoadingState.jsx
│   │   │   ├── UX4GModal.jsx
│   │   │   ├── UX4GOffcanvas.jsx
│   │   │   └── UX4GTable.jsx
│   │   ├── counsellor/           # [Blessy] Counsellor Case Management & Clinical Analytics
│   │   │   ├── CaseDetailModal.jsx
│   │   │   ├── DistressTrendChart.jsx
│   │   │   ├── InterventionActionModal.jsx
│   │   │   ├── ModelExplainabilityCard.jsx
│   │   │   └── OutcomeRecordModal.jsx
│   │   ├── effects/              # Subtle Government UI Visual Transitions
│   │   │   ├── BentoGrid.jsx
│   │   │   ├── KineticTiltCard.jsx
│   │   │   ├── MarqueeTicker.jsx
│   │   │   └── TextMaskReveal.jsx
│   │   └── victim/               # [Yashashvi] Citizen / Victim Confidential Care Experience
│   │       ├── ConsentPreferencesModal.jsx
│   │       ├── PersonalTrendCard.jsx
│   │       ├── TextCheckInModal.jsx
│   │       ├── UserProfilePreferencesModal.jsx
│   │       └── VoiceCheckInModal.jsx
│   ├── context/                  # [Yashashvi & Blessy] State Management
│   │   ├── AuthContext.jsx       # 6-Role Session RBAC
│   │   └── ThemeAccessibilityContext.jsx # Contrast & Reduced Motion Controls
│   ├── pages/                    # Routed Application Pages
│   │   ├── HomePage.jsx          # [Yashashvi] Public Government Landing Page
│   │   ├── SignInPage.jsx        # [Yashashvi] Administrative Sign-In (NO Public Sign-Up)
│   │   └── dashboards/
│   │       ├── DashboardShell.jsx      # [Yashashvi] Unified Collapsible Responsive Shell
│   │       ├── VictimDashboard.jsx     # [Yashashvi] Day 2 Citizen Care & Check-In Portal
│   │       ├── CounsellorDashboard.jsx # [Blessy] Day 2 Clinical Caseload Triage Queue
│   │       ├── DistrictDashboard.jsx   # Day 3 Official Dashboard
│   │       ├── StateDashboard.jsx      # Day 3 Official Dashboard
│   │       ├── NationalDashboard.jsx   # Day 3 Official Dashboard
│   │       ├── AdminDashboard.jsx      # System Governance & RBAC Dashboard
│   │       └── UnauthorizedPage.jsx   # 403 Security Interceptor
│   ├── services/                 # Self-Contained Backend Contract Mocks
│   │   ├── caseService.js        # [Blessy] Caseloads, Timelines & Outcomes
│   │   ├── consentService.js     # [Yashashvi] DPDP Act 2023 Consent Records
│   │   └── interactionService.js # [Yashashvi] Speech ASR & Text Interactions
│   ├── styles/
│   │   └── ux4g-theme.css        # UX4G 3.0 Design Tokens & Color Palettes
│   ├── App.jsx                   # Role-Based Routing Architecture
│   └── main.jsx                  # React 19 Root
├── package.json
└── vite.config.js                # Vite 8 + Rolldown Production Chunker
```

---

## 🚀 Running Locally

```bash
# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev

# 3. Build for production
npm run build
```

The application runs locally at `http://localhost:5173/`.

### 🔑 Verified Demonstration Personas

| Role | Test Username | Password | Operational Access Scope |
| :--- | :--- | :--- | :--- |
| **Citizen / Beneficiary** | `meera.s@citizen` | `password123` | Confidential care space, 5-gate voice check-in, DPDP consent, statutory status |
| **Clinical Counsellor** | `dr.rajesh@aaroh.gov.in` | `password123` | Clinical caseload triage, 30-day SVG distress trajectory, model explainability, outcome recording |
| **District Official** | `ananya.sen@ias.nic.in` | `password123` | South Delhi operational monitoring, workload balance, statutory SLAs |
| **State Official** | `k.ramanathan@delhi.gov.in` | `password123` | Delhi NCT inter-district comparison, state distress index |
| **National Director** | `p.venkat@socialjustice.gov.in` | `password123` | All-India 28 states & 8 UTs executive oversight, national intervention trends |
| **System Administrator** | `sysadmin@aaroh.nic.in` | `password123` | RBAC access control, immutable audit logs, platform security |

---

## 🌿 GitHub Branching & Workflow Rules (Section 34)

As defined in **Section 34 of the Master Implementation Plan**, all development must follow a clean Git workflow:

### Branch Structure
```
main (always stable & production-ready)
│
├── feature/yashashvi-foundation    # Day 1: Architecture, UX4G Tokens, Home, Sign-In
├── feature/blessy-components       # Day 1: Shared UX4G Reusable Components
├── feature/yashashvi-user-flow     # Day 2: Victim Dashboard, Voice & Text Check-Ins, Consent
├── feature/blessy-counsellor       # Day 2: Counsellor Caseload, Distress Chart, Dossier
└── feature/official-dashboards     # Day 3: District, State, National Portals
```

### Commit Convention
```
feat: add UX4G home page
feat: implement sign in flow
feat: add user dashboard
feat: add 5-gate voice check-in
feat: add counsellor case list
feat: add distress trend SVG chart
fix: refine formal table layout
refactor: extract shared dashboard components
```

---

## 🛡️ Critical Design & Security Rules
- **Rule 1 — UX4G ONLY**: Pure UX4G components and design tokens; no secondary frameworks (Bootstrap, MUI, Chakra) introduced.
- **Rule 2 — NO PUBLIC SIGN UP**: User accounts are administrative provisions under official government mandate.
- **Rule 3 — Backend Authority**: Frontend route guards enforce RBAC; backend remains the security boundary.
- **Rule 4 — Human in the Loop (Rule 5)**: AI recommendations are distinct from statutory decisions made by authorized clinical psychologists.
- **Rule 6 — Privacy First**: Non-alarming, supportive language on citizen-facing screens; raw ML probabilities reserved for clinical staff.
- **Rule 34.10 — Shared Component Rule**: Single shared component implementations under `src/components/common/`.

