import React, { useState } from 'react';
import { Shield, Lock, PhoneCall, ExternalLink, FileText, CheckCircle2, BookOpen, AlertCircle } from 'lucide-react';
import { UX4GModal } from './UX4GModal';
import { UX4GButton } from './UX4GButton';

export const UX4GFooter = () => {
  const [activeModal, setActiveModal] = useState(null); // 'privacy' | 'terms' | 'docs' | null

  return (
    <footer
      style={{
        backgroundColor: '#EFE7DA',
        borderTop: '2px solid #3A2312',
        marginTop: 'auto',
        color: '#543118',
        fontSize: '0.85rem',
        fontFamily: '"Space Mono", "Courier Prime", monospace',
      }}
    >
      {/* Upper Colophon: Global Network & Heartbeat Strip */}
      <div style={{ backgroundColor: '#E6DAC9', borderBottom: '1.5px solid #3A2312', padding: '14px 0' }}>
        <div className="container flex-between" style={{ flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#443F24',
                boxShadow: '0 0 0 3px rgba(68,63,36,0.2)',
              }}
            />
            <span style={{ fontWeight: 800, color: '#2B1508', fontSize: '0.8rem', letterSpacing: '0.04em' }}>
              GLOBAL RESILIENCE NETWORK • ALL SYSTEMS OPERATIONAL
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', fontSize: '0.78rem' }}>
            <span style={{ color: '#78604F' }}>SLA Compliance: <strong style={{ color: '#2B1508' }}>98.6%</strong></span>
            <span style={{ color: '#AB8867' }}>•</span>
            <span style={{ color: '#78604F' }}>Distress Latency: <strong style={{ color: '#2B1508' }}>108ms</strong></span>
            <span style={{ color: '#AB8867' }}>•</span>
            <span style={{ color: '#78604F' }}>DPDP Act 2023: <strong style={{ color: '#443F24' }}>Encrypted &amp; Audited</strong></span>
          </div>
        </div>
      </div>

      {/* Main Colophon Grid */}
      <div style={{ padding: '48px 0 32px' }}>
        <div className="container">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '36px',
              marginBottom: '36px',
            }}
          >
            {/* Column 1: AAROH Brand */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 900, color: '#2B1508', fontFamily: '"Fraunces", "Playfair Display", Georgia, serif', letterSpacing: '-0.02em' }}>
                  AAROH
                </span>
                <span
                  style={{
                    backgroundColor: '#E6DAC9',
                    color: '#3A2312',
                    fontSize: '0.68rem',
                    fontWeight: 800,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: '1px solid #AB8867',
                    letterSpacing: '0.06em',
                  }}
                >
                  EDITION 2026
                </span>
              </div>
              <p style={{ color: '#78604F', lineHeight: '1.7', fontSize: '0.8rem', marginBottom: '16px' }}>
                A proactive psychological resilience platform combining paralinguistic acoustic modeling with certified clinical intervention — protecting dignity through consensual, privacy-first care.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#543118', fontSize: '0.78rem', fontWeight: 700 }}>
                <Shield size={14} color="#8C6240" />
                <span>Encrypted &amp; DPDP Compliant Architecture</span>
              </div>
            </div>

            {/* Column 2: Acoustic Intelligence Engine */}
            <div>
              <h4 style={{ color: '#2B1508', fontWeight: 800, marginBottom: '14px', fontSize: '0.88rem', letterSpacing: '0.04em' }}>
                Intelligence Engine
              </h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '9px', fontSize: '0.8rem', color: '#78604F' }}>
                <li>Multimodal Acoustic Paralinguistics</li>
                <li>F0 Pitch &amp; Jitter Deviation Modeling</li>
                <li>Longitudinal Calibrated Baseline Tracking</li>
                <li>Non-Punitive AI: Zero Automated Penalties</li>
                <li>Real-Time Multi-Tier Triage Routing</li>
              </ul>
            </div>

            {/* Column 3: Governance & Safeguards */}
            <div>
              <h4 style={{ color: '#2B1508', fontWeight: 800, marginBottom: '14px', fontSize: '0.88rem', letterSpacing: '0.04em' }}>
                Safeguards &amp; Privacy
              </h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8rem', color: '#78604F' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={13} color="#443F24" />
                  <span>DPDP Act 2023 Consent Flow</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={13} color="#443F24" />
                  <span>Human-in-the-Loop Clinical Review</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={13} color="#443F24" />
                  <span>Zero Outreach Outside Safe Window</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={13} color="#443F24" />
                  <span>Automated Audio Erasure Guarantee</span>
                </li>
              </ul>
            </div>

            {/* Column 4: Documentation & Protocol */}
            <div>
              <h4 style={{ color: '#2B1508', fontWeight: 800, marginBottom: '14px', fontSize: '0.88rem', letterSpacing: '0.04em' }}>
                Architecture &amp; Protocol
              </h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '9px', fontSize: '0.8rem' }}>
                <li>
                  <button
                    type="button"
                    onClick={() => setActiveModal('docs')}
                    style={{ background: 'none', border: 'none', color: '#543118', cursor: 'pointer', textAlign: 'left', padding: 0, textDecoration: 'underline', fontFamily: 'inherit', fontSize: 'inherit', fontWeight: 700 }}
                  >
                    System Architecture &amp; API Docs
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setActiveModal('privacy')}
                    style={{ background: 'none', border: 'none', color: '#543118', cursor: 'pointer', textAlign: 'left', padding: 0, textDecoration: 'underline', fontFamily: 'inherit', fontSize: 'inherit', fontWeight: 700 }}
                  >
                    Privacy Architecture (DPDP)
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setActiveModal('terms')}
                    style={{ background: 'none', border: 'none', color: '#543118', cursor: 'pointer', textAlign: 'left', padding: 0, textDecoration: 'underline', fontFamily: 'inherit', fontSize: 'inherit', fontWeight: 700 }}
                  >
                    Terms of Platform Access
                  </button>
                </li>
                <li style={{ color: '#78604F' }}>Clinical Triage SLA Protocol</li>
              </ul>
            </div>
          </div>

          {/* Bottom Colophon Strip */}
          <div
            style={{
              paddingTop: '20px',
              borderTop: '1px solid #CDB397',
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.76rem',
              color: '#78604F',
            }}
          >
            <div>
              © 2026 AAROH Intelligence Platform. Built for human resilience &amp; care.
            </div>

            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <span style={{ cursor: 'pointer' }} onClick={() => setActiveModal('privacy')}>Privacy Architecture</span>
              <span>•</span>
              <span style={{ cursor: 'pointer' }} onClick={() => setActiveModal('terms')}>Platform Terms</span>
              <span>•</span>
              <span style={{ cursor: 'pointer' }} onClick={() => setActiveModal('docs')}>API Specs</span>
            </div>
          </div>
        </div>
      </div>

      {/* ================= MODAL: PRIVACY POLICY ================= */}
      <UX4GModal
        isOpen={activeModal === 'privacy'}
        onClose={() => setActiveModal(null)}
        title="AAROH Privacy Policy (DPDP Act 2023)"
        subtitle="Digital Personal Data Protection & Consent Governance"
        maxWidth="640px"
        footer={
          <UX4GButton variant="primary" size="sm" onClick={() => setActiveModal(null)}>
            I Understand & Agree
          </UX4GButton>
        }
      >
        <div style={{ fontSize: '0.88rem', lineHeight: '1.7', color: 'var(--ux4g-text-primary)' }}>
          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>1. Scope & Purpose</h4>
          <p style={{ marginBottom: '14px' }}>
            AAROH operates solely for the psychological rehabilitation, safety monitoring, and crisis mitigation of victims of atrocities. All personal data processing strictly adheres to the Digital Personal Data Protection (DPDP) Act 2023.
          </p>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>2. Explicit Consent Architecture</h4>
          <p style={{ marginBottom: '14px' }}>
            Periodic check-ins, text processing, and speech audio recording require explicit, granular beneficiary consent. Beneficiaries may modify their safe communication windows or revoke consent at any time without penalty or loss of statutory entitlements.
          </p>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>3. Data Storage & Encryption</h4>
          <p style={{ marginBottom: '14px' }}>
            All interaction records and distress predictions are stored within sovereign Indian government cloud facilities (NIC/MeitY empaneled) using AES-256 encryption at rest and TLS 1.3 in transit.
          </p>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>4. Zero Automated Penalties</h4>
          <p>
            No algorithmic prediction can result in punitive measures, cancellation of compensation, or legal prejudice. All clinical recommendations must be validated by certified human professionals.
          </p>
        </div>
      </UX4GModal>

      {/* ================= MODAL: TERMS & CONDITIONS ================= */}
      <UX4GModal
        isOpen={activeModal === 'terms'}
        onClose={() => setActiveModal(null)}
        title="Terms and Conditions of Portal Access"
        subtitle="Authorized Government System Usage Rules"
        maxWidth="640px"
        footer={
          <UX4GButton variant="primary" size="sm" onClick={() => setActiveModal(null)}>
            Close Terms
          </UX4GButton>
        }
      >
        <div style={{ fontSize: '0.88rem', lineHeight: '1.7', color: 'var(--ux4g-text-primary)' }}>
          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>1. Authorized Access Only</h4>
          <p style={{ marginBottom: '14px' }}>
            Access to the AAROH portal is restricted to authorized beneficiaries, licensed counsellors, and designated government nodal officials. Unauthorized access attempts are monitored and prosecutable under the Information Technology Act 2000.
          </p>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>2. Role Boundaries (RBAC)</h4>
          <p style={{ marginBottom: '14px' }}>
            Users must strictly remain within their designated jurisdictional scope. Officials must not attempt to circumvent role boundaries or inspect beneficiary data outside their district or department.
          </p>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>3. Statutory Reporting SLAs</h4>
          <p>
            Designated counsellors and district magistrates are bound by statutory response timeframes for escalating cases, ensuring rapid relief and clinical support.
          </p>
        </div>
      </UX4GModal>

      {/* ================= MODAL: DOCUMENTATION ================= */}
      <UX4GModal
        isOpen={activeModal === 'docs'}
        onClose={() => setActiveModal(null)}
        title="AAROH System Architecture & Documentation"
        subtitle="Technical Overview for Frontend & API Integration"
        maxWidth="680px"
        footer={
          <UX4GButton variant="primary" size="sm" onClick={() => setActiveModal(null)}>
            Close Documentation
          </UX4GButton>
        }
      >
        <div style={{ fontSize: '0.88rem', lineHeight: '1.7', color: 'var(--ux4g-text-primary)' }}>
          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>Frontend Architectural Specification</h4>
          <p style={{ marginBottom: '14px' }}>
            Built using React 19 + Vite, adhering strictly to the UX4G Design System 3.0 standard. All styling is derived from UX4G CSS tokens with a light pastel palette, 4 elevation levels, focus glow micro-interactions, and a Universal Motion Toggle for GIGW 3.0 accessibility.
          </p>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>API Contracts & Endpoints</h4>
          <ul style={{ paddingLeft: '20px', marginBottom: '14px' }}>
            <li><code>/api/v1/auth/login</code> — Role verification & secure session token issuance.</li>
            <li><code>/api/v1/interactions/checkin</code> — Multi-modal voice/text intake payload.</li>
            <li><code>/api/v1/predictions/distress</code> — Longitudinal baseline deviation score & confidence.</li>
            <li><code>/api/v1/interventions/sla</code> — District magistrate case assignment & follow-up tracking.</li>
          </ul>

          <h4 style={{ color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>Voice/ASR Pipeline Interface</h4>
          <p>
            The voice subsystem connects to the central ASR pipeline, processing audio through 5 strict gates: Record → Review → Submit → Processing → Confirmation, with fallback to written text.
          </p>
        </div>
      </UX4GModal>
    </footer>
  );
};
