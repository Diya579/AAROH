import React, { useState } from 'react';
import { 
  User, 
  Clock, 
  MapPin, 
  Calendar, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  PhoneCall, 
  FileText, 
  Mic, 
  TrendingUp, 
  Sparkles, 
  Shield, 
  Edit3 
} from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { UX4GCard } from '../common/UX4GCard';
import { RiskBadge, StatusBadge } from '../common/UX4GBadge';
import { UX4GTable } from '../common/UX4GTable';
import { DistressTrendChart } from './DistressTrendChart';
import { ModelExplainabilityCard } from './ModelExplainabilityCard';
import { InterventionActionModal } from './InterventionActionModal';
import { OutcomeRecordModal } from './OutcomeRecordModal';

export const CaseDetailModal = ({ isOpen, onClose, caseData, onCaseUpdated }) => {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'timeline' | 'interactions' | 'monitoring'
  const [interventionModalOpen, setInterventionModalOpen] = useState(false);
  const [outcomeModalOpen, setOutcomeModalOpen] = useState(false);

  if (!caseData) return null;

  const handleCaseUpdated = (updated) => {
    if (onCaseUpdated) onCaseUpdated(updated);
  };

  const interactionColumns = [
    {
      header: 'ID / Date',
      key: 'id',
      render: (_, row) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{row.id}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>{row.date}</div>
        </div>
      ),
    },
    {
      header: 'Modality',
      key: 'channel',
      render: (_, row) => (
        <span className="ux4g-badge ux4g-badge-primary">
          {row.channel} {row.voiceAvailable && '🎙️'}
        </span>
      ),
    },
    {
      header: 'Language / Quality',
      key: 'language',
      render: (_, row) => (
        <div>
          <div>{row.language}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-success)', fontWeight: 600 }}>ASR Quality: {row.qualityScore}</div>
        </div>
      ),
    },
    {
      header: 'Transcribed Excerpt (Authorised View)',
      key: 'textExcerpt',
      render: (_, row) => (
        <div style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', fontStyle: 'italic', maxWidth: '320px' }}>
          "{row.textExcerpt}"
        </div>
      ),
    },
    {
      header: 'Status',
      key: 'status',
      render: (_, row) => (
        <span className="ux4g-badge ux4g-badge-low">
          {row.status}
        </span>
      ),
    },
  ];

  return (
    <>
      <UX4GModal
        isOpen={isOpen}
        onClose={onClose}
        title={`Case Dossier: ${caseData.id}`}
        subtitle={`${caseData.beneficiaryName} • District: ${caseData.district} • DPDP 2023 Secure View`}
        maxWidth="960px"
      >
        {/* Top Header Summary Strip */}
        <div style={{ padding: '16px 20px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '50%', backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-800)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
              {caseData.beneficiaryName.charAt(0)}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                  {caseData.beneficiaryName}
                </h3>
                <RiskBadge level={caseData.riskLevel} size="sm" />
                <StatusBadge status={caseData.status} size="sm" />
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>
                Safe Hours: <strong>{caseData.safeHours}</strong> • Channel: <strong>{caseData.safeChannel}</strong>
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <UX4GButton
              variant="outline"
              size="sm"
              icon={Shield}
              onClick={() => setInterventionModalOpen(true)}
            >
              Assign Action
            </UX4GButton>
            <UX4GButton
              variant="primary"
              size="sm"
              icon={Edit3}
              onClick={() => setOutcomeModalOpen(true)}
            >
              Record Outcome
            </UX4GButton>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--ux4g-border)', marginBottom: '20px' }}>
          {[
            { id: 'overview', label: 'Case Overview' },
            { id: 'monitoring', label: 'Mental Health & Visualizations' },
            { id: 'interactions', label: `Interactions (${caseData.interactions?.length || 0})` },
            { id: 'timeline', label: 'Chronological Timeline' },
          ].map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 18px',
                border: 'none',
                background: 'transparent',
                fontSize: '0.88rem',
                fontWeight: activeTab === tab.id ? 700 : 500,
                color: activeTab === tab.id ? 'var(--ux4g-violet-700)' : 'var(--ux4g-text-secondary)',
                borderBottom: activeTab === tab.id ? '2.5px solid var(--ux4g-violet-700)' : '2.5px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ================= TAB 1: CASE OVERVIEW ================= */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* 3-Col Meta Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '14px', backgroundColor: '#FFF', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Registration Details</span>
                <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)', marginTop: '4px' }}>Registered: {caseData.registrationDate}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Under SC/ST PoA Statutory Framework</div>
              </div>

              <div style={{ padding: '14px', backgroundColor: '#FFF', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>District Oversight</span>
                <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)', marginTop: '4px' }}>{caseData.district}, {caseData.state}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Nodal Cell: South Delhi DM Office</div>
              </div>

              <div style={{ padding: '14px', backgroundColor: '#FFF', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Statutory SLA Adherence</span>
                <div style={{ fontWeight: 700, color: caseData.slaHoursRemaining <= 2 ? 'var(--ux4g-danger)' : 'var(--ux4g-violet-950)', marginTop: '4px' }}>
                  {caseData.slaHoursRemaining} Hours Remaining
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Status: {caseData.slaStatus}</div>
              </div>
            </div>

            {/* Current Active Intervention Card */}
            <div style={{ padding: '16px 20px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={18} color="var(--ux4g-violet-700)" />
                  <strong style={{ fontSize: '0.92rem', color: 'var(--ux4g-violet-950)' }}>
                    Active Intervention Strategy
                  </strong>
                </div>
                <span className="ux4g-badge ux4g-badge-primary">{caseData.stage}</span>
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-primary)', lineHeight: 1.5, marginBottom: '10px' }}>
                {caseData.recommendedIntervention}
              </p>
              <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                Assigned Officer: <strong>{caseData.assignedOfficial}</strong>
              </div>
            </div>

            {/* Model Explainability Preview */}
            <ModelExplainabilityCard
              factors={caseData.contributingFactors}
              confidence={caseData.confidence}
              predictionHorizon={caseData.predictionHorizon}
            />
          </div>
        )}

        {/* ================= TAB 2: MENTAL HEALTH & VISUALIZATIONS ================= */}
        {activeTab === 'monitoring' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Distress Curve Component */}
            <DistressTrendChart caseData={caseData} />

            {/* Full Explainability Card */}
            <ModelExplainabilityCard
              factors={caseData.contributingFactors}
              confidence={caseData.confidence}
              predictionHorizon={caseData.predictionHorizon}
            />
          </div>
        )}

        {/* ================= TAB 3: INTERACTIONS HISTORY ================= */}
        {activeTab === 'interactions' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                Authorised Speech &amp; Text Interaction Logs
              </h4>
              <span className="ux4g-badge ux4g-badge-low">Explicit Consent Verified</span>
            </div>
            <UX4GTable
              columns={interactionColumns}
              data={caseData.interactions || []}
              caption="Authorised interaction logs table"
            />
          </div>
        )}

        {/* ================= TAB 4: TIMELINE ================= */}
        {activeTab === 'timeline' && (
          <div style={{ padding: '8px 0' }}>
            <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '18px' }}>
              Chronological Case Events &amp; Action Log
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', borderLeft: '2px solid var(--ux4g-violet-200)', paddingLeft: '18px', marginLeft: '6px' }}>
              {(caseData.timeline || []).map((event, idx) => (
                <div key={idx} style={{ position: 'relative' }}>
                  {/* Dot */}
                  <div
                    style={{
                      position: 'absolute',
                      left: '-25px',
                      top: '2px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      backgroundColor: event.type.includes('PREDICTION') || event.type.includes('SLA') ? 'var(--ux4g-danger)' : 'var(--ux4g-violet-700)',
                      border: '2px solid #FFF',
                      boxShadow: '0 0 0 2px var(--ux4g-violet-200)',
                    }}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--ux4g-violet-950)' }}>
                      {event.title}
                    </strong>
                    <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', backgroundColor: 'var(--ux4g-bg)', padding: '2px 8px', borderRadius: '4px' }}>
                      {event.date}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
                    {event.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </UX4GModal>

      {/* Sub-Modals for Intervention & Outcome */}
      <InterventionActionModal
        isOpen={interventionModalOpen}
        onClose={() => setInterventionModalOpen(false)}
        caseData={caseData}
        onInterventionUpdated={handleCaseUpdated}
      />

      <OutcomeRecordModal
        isOpen={outcomeModalOpen}
        onClose={() => setOutcomeModalOpen(false)}
        caseData={caseData}
        onOutcomeSaved={handleCaseUpdated}
      />
    </>
  );
};
