import React, { useState } from 'react';
import { Shield, Lock, PhoneCall, ExternalLink, FileText, CheckCircle2, BookOpen, AlertCircle } from 'lucide-react';
import { UX4GModal } from './UX4GModal';
import { UX4GButton } from './UX4GButton';

export const UX4GFooter = () => {
  const [activeModal, setActiveModal] = useState(null); // 'privacy' | 'terms' | 'docs' | null

  return (
    <footer
      style={{
        backgroundColor: '#FFFFFF',
        borderTop: '1px solid var(--ux4g-border)',
        marginTop: 'auto',
        color: 'var(--ux4g-text-secondary)',
        fontSize: '0.85rem',
      }}
    >
      {/* Upper Footer: Emergency Helplines Strip */}
      <div style={{ backgroundColor: 'var(--ux4g-violet-50)', borderBottom: '1px solid var(--ux4g-violet-100)', padding: '16px 0' }}>
        <div className="container flex-between" style={{ flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-violet-700)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <PhoneCall size={18} />
            </div>
            <div>
              <p style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)', fontSize: '0.9rem' }}>
                National Crisis Helplines & Emergency Assistance
              </p>
              <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                Toll-free, confidential support available 24x7 across all Indian languages
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--ux4g-violet-900)' }}>Tele-MANAS:</span>
              <a href="tel:14416" style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, textDecoration: 'none' }}>
                14416 / 1800-891-4416
              </a>
            </div>
            <div style={{ color: 'var(--ux4g-border)' }}>|</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--ux4g-violet-900)' }}>Emergency Response:</span>
              <a href="tel:112" style={{ color: 'var(--ux4g-danger)', fontWeight: 700, textDecoration: 'none' }}>
                112
              </a>
            </div>
            <div style={{ color: 'var(--ux4g-border)' }}>|</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--ux4g-violet-900)' }}>Women Helpline:</span>
              <a href="tel:181" style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, textDecoration: 'none' }}>
                181
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer Links & Compliance Notice */}
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
            {/* Column 1: AAROH Project */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                  AAROH
                </span>
                <span
                  style={{
                    backgroundColor: 'var(--ux4g-violet-50)',
                    color: 'var(--ux4g-violet-700)',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--ux4g-violet-200)',
                  }}
                >
                  Gov.in Portal
                </span>
              </div>
              <p style={{ color: 'var(--ux4g-text-muted)', lineHeight: '1.6', fontSize: '0.825rem', marginBottom: '16px' }}>
                AI-Powered Dynamic Mental Health Monitoring and Distress Prediction System for Victims of Atrocities.
                Administered by the Ministry of Social Justice & Empowerment, Government of India.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--ux4g-violet-800)', fontSize: '0.8rem', fontWeight: 600 }}>
                <Shield size={16} />
                <span>Protected under DPDP Act 2023</span>
              </div>
            </div>

            {/* Column 2: Legal & Privacy */}
            <div>
              <h4 style={{ color: 'var(--ux4g-violet-950)', fontWeight: 700, marginBottom: '14px', fontSize: '0.92rem' }}>
                Privacy & Legal Policies
              </h4>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '9px', fontSize: '0.825rem' }}>
                <li>
                  <button
                    type="button"
                    onClick={() => setActiveModal('privacy')}
                    style={{ background: 'none', border: 'none', color: 'var(--ux4g-text-secondary)', cursor: 'pointer', textAlign: 'left', padding: 0, textDecoration: 'underline' }}
                  >
                    Privacy Policy (DPDP 2023)
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setActiveModal('terms')}
                    style={{ background: 'none', border: 'none', color: 'var(--ux4g-text-secondary)', cursor: 'pointer', textAlign: 'left', padding: 0, textDecoration: 'underline' }}
                  >
                    Terms & Conditions of Portal
                  </button>
                </li>
                <li>Citizen Charter for Victims of Atrocities</li>
                <li>Non-Discrimination & Confidentiality Oath</li>
                <li>Safe Hour Communication Guarantee</li>
              </ul>
            </div>

            {/* Column 3: Standards & Compliance */}
            <div>
              <h4 style={{ color: 'var(--ux4g-violet-950)', fontWeight: 700, marginBottom: '14px', fontSize: '0.92rem' }}>
                Standards & Compliance
              </h4>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.825rem' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={14} color="var(--ux4g-success)" />
                  <span>GIGW 3.0 Accessibility Compliant</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={14} color="var(--ux4g-success)" />
                  <span>WCAG 2.1 Level AA Certified</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={14} color="var(--ux4g-success)" />
                  <span>Zero Automated Penalties</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={14} color="var(--ux4g-success)" />
                  <span>Human-in-the-Loop Safeguards</span>
                </li>
              </ul>
            </div>

            {/* Column 4: Documentation & Technical Specs */}
            <div>
              <h4 style={{ color: 'var(--ux4g-violet-950)', fontWeight: 700, marginBottom: '14px', fontSize: '0.92rem' }}>
                Documentation & Specs
              </h4>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '9px', fontSize: '0.825rem' }}>
                <li>
                  <button
                    type="button"
                    onClick={() => setActiveModal('docs')}
                    style={{ background: 'none', border: 'none', color: 'var(--ux4g-text-secondary)', cursor: 'pointer', textAlign: 'left', padding: 0, textDecoration: 'underline' }}
                  >
                    System Architecture & API Docs
                  </button>
                </li>
                <li>Multimodal Speech ASR Pipeline Specs</li>
                <li>District Magistrate SLA Guidelines</li>
                <li>Counsellor Clinical Protocol Manual</li>
                <li>RBAC Governance & Audit Model</li>
              </ul>
            </div>

            {/* Column 5: Grievance & Liaison */}
            <div>
              <h4 style={{ color: 'var(--ux4g-violet-950)', fontWeight: 700, marginBottom: '14px', fontSize: '0.92rem' }}>
                Grievance Redressal
              </h4>
              <p style={{ color: 'var(--ux4g-text-muted)', lineHeight: '1.5', fontSize: '0.825rem', marginBottom: '10px' }}>
                Direct oversight under the Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act.
              </p>
              <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-violet-700)', fontWeight: 600 }}>
                CPGRAMS Grievance Portal: pgportal.gov.in
              </div>
            </div>
          </div>

          {/* Bottom Copyright Strip */}
          <div
            style={{
              paddingTop: '24px',
              borderTop: '1px solid var(--ux4g-border-subtle)',
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.78rem',
              color: 'var(--ux4g-text-muted)',
            }}
          >
            <div>
              © 2026 Government of India. All rights reserved. AAROH Portal.
            </div>

            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <span style={{ cursor: 'pointer' }} onClick={() => setActiveModal('privacy')}>Privacy Policy</span>
              <span>•</span>
              <span style={{ cursor: 'pointer' }} onClick={() => setActiveModal('terms')}>Terms of Service</span>
              <span>•</span>
              <span style={{ cursor: 'pointer' }} onClick={() => setActiveModal('docs')}>Documentation</span>
              <span>•</span>
              <span>Accessibility Statement</span>
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
