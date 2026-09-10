import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Filter, 
  Clock, 
  AlertTriangle, 
  FileText, 
  CheckCircle, 
  ShieldAlert, 
  X, 
  ArrowRight,
  PhoneCall,
  UserCheck
} from 'lucide-react';
import { RetroStamp } from '../components/RetroStamp';
import { RetroTiltCard } from '../components/RetroTiltCard';
import { caseService } from '../../services/caseService';

export const RetroCounsellorView = () => {
  const [cases, setCases] = useState([]);
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCase, setSelectedCase] = useState(null);
  const [actionSuccess, setActionSuccess] = useState('');

  useEffect(() => {
    async function fetchCases() {
      const data = await caseService.getCases();
      setCases(data);
    }
    fetchCases();
  }, []);

  const filteredCases = cases.filter((c) => {
    const matchesPriority = filterPriority === 'ALL' || c.priority === filterPriority;
    const matchesSearch =
      c.beneficiaryName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.district.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesPriority && matchesSearch;
  });

  const handleRouteIntervention = (caseId, type) => {
    setActionSuccess(`Intervention "${type}" officially logged for ${caseId}. SLA timer refreshed.`);
    setTimeout(() => setActionSuccess(''), 4000);
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Top Header Tag */}
      <div
        style={{
          borderBottom: '2.5px solid var(--retro-ink-black)',
          paddingBottom: '14px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RetroStamp type="urgent" label="CHIEF CLINICAL BUREAU" size="sm" />
            <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.78rem' }}>
              DISTRESS TRIAGE & PSYCHOLOGICAL DISPATCH REGISTRY
            </span>
          </div>
          <h2 className="retro-headline-md" style={{ margin: '6px 0 0 0' }}>
            Active Beneficiary Docket Registry ({cases.length} Total Dossiers)
          </h2>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <RetroStamp type="urgent" label="PILOT PHASE: ACTIVE" />
          <RetroStamp type="verified" label="ZERO SLA BREACHES" />
        </div>
      </div>

      {actionSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--retro-stamp-green-bg)',
            border: '2px solid var(--retro-stamp-green)',
            fontFamily: 'var(--retro-font-mono)',
            fontSize: '0.82rem',
            color: 'var(--retro-stamp-green)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle size={16} />
          <span>{actionSuccess}</span>
        </motion.div>
      )}

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
          backgroundColor: 'var(--retro-bg-paper-light)',
          border: '1.5px solid var(--retro-ink-black)',
          padding: '14px 18px',
          marginBottom: '24px',
          boxShadow: 'var(--retro-shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1 1 260px' }}>
          <Search size={15} style={{ color: 'var(--retro-ink-muted)' }} />
          <input
            type="text"
            placeholder="Search dossier by name, ID, or district..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              background: 'transparent',
              border: 'none',
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.82rem',
              color: 'var(--retro-ink-black)',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
            PRIORITY FILTER:
          </span>
          {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilterPriority(lvl)}
              className="retro-btn"
              style={{
                fontSize: '0.72rem',
                padding: '4px 10px',
                backgroundColor: filterPriority === lvl ? 'var(--retro-bg-cardboard-dark)' : 'var(--retro-bg-paper)',
                borderWidth: filterPriority === lvl ? '2px' : '1px',
              }}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Case Dossiers Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {filteredCases.map((c) => (
          <RetroTiltCard key={c.id} paper>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                <span
                  style={{
                    fontFamily: 'var(--retro-font-mono)',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    backgroundColor: 'var(--retro-bg-cardboard)',
                    padding: '2px 6px',
                    border: '1px solid var(--retro-ink-black)',
                    marginRight: '6px',
                  }}
                >
                  {c.id}
                </span>
                <RetroStamp
                  type={c.priority === 'HIGH' ? 'urgent' : c.priority === 'MEDIUM' ? 'amber' : 'verified'}
                  label={c.riskLevel.toUpperCase()}
                  size="sm"
                />
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  color: c.slaHoursRemaining <= 4 ? 'var(--retro-stamp-red)' : 'var(--retro-ink-black)',
                }}
              >
                <Clock size={12} />
                <span>{c.slaHoursRemaining}h SLA</span>
              </div>
            </div>

            <h4
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '1.2rem',
                fontWeight: 800,
                margin: '0 0 6px 0',
              }}
            >
              {c.beneficiaryName}
            </h4>

            <div
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.75rem',
                color: 'var(--retro-ink-muted)',
                marginBottom: '12px',
              }}
            >
              District: {c.district}, {c.state} • Registered: {c.registrationDate}
            </div>

            {/* Distress Seismograph Numbers */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '10px 12px',
                backgroundColor: 'var(--retro-bg-paper-light)',
                border: '1px solid var(--retro-ink-black)',
                marginBottom: '14px',
              }}
            >
              <div>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.68rem', color: 'var(--retro-ink-muted)' }}>
                  DISTRESS SCORE
                </div>
                <div
                  style={{
                    fontFamily: 'var(--retro-font-headline)',
                    fontSize: '1.5rem',
                    fontWeight: 900,
                    color: c.distressScore > 70 ? 'var(--retro-stamp-red)' : 'var(--retro-ink-black)',
                  }}
                >
                  {c.distressScore}/100
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.68rem', color: 'var(--retro-ink-muted)' }}>
                  BASELINE DEVIATION
                </div>
                <div
                  style={{
                    fontFamily: 'var(--retro-font-mono)',
                    fontSize: '1.1rem',
                    fontWeight: 800,
                    color: c.baselineDeviation.startsWith('+') ? 'var(--retro-stamp-red)' : 'var(--retro-stamp-green)',
                  }}
                >
                  {c.baselineDeviation}
                </div>
              </div>
            </div>

            <p className="retro-typewriter" style={{ fontSize: '0.78rem', marginBottom: '14px' }}>
              <strong>Recommended Action:</strong> {c.recommendedIntervention}
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span
                style={{
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.72rem',
                  color: 'var(--retro-ink-faint)',
                }}
              >
                Assignee: {c.primaryAssignee || c.assignedOfficial}
              </span>

              <button
                onClick={() => setSelectedCase(c)}
                className="retro-btn"
                style={{ fontSize: '0.75rem', padding: '6px 12px' }}
              >
                <span>EXAMINE DOSSIER</span>
                <ArrowRight size={12} />
              </button>
            </div>
          </RetroTiltCard>
        ))}
      </div>

      {/* Case Details Modal */}
      <AnimatePresence>
        {selectedCase && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              width: '100vw',
              height: '100vh',
              backgroundColor: 'rgba(26, 23, 21, 0.65)',
              backdropFilter: 'blur(3px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10000,
              padding: '20px',
              boxSizing: 'border-box',
            }}
            onClick={() => setSelectedCase(null)}
          >
            <motion.div
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.92, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                width: '100%',
                maxWidth: '780px',
                maxHeight: '90vh',
                overflowY: 'auto',
                backgroundColor: 'var(--retro-bg-paper-light)',
                border: '3px solid var(--retro-ink-black)',
                boxShadow: 'var(--retro-shadow-xl)',
                padding: '28px',
                position: 'relative',
              }}
            >
              <button
                onClick={() => setSelectedCase(null)}
                style={{
                  position: 'absolute',
                  top: '16px',
                  right: '16px',
                  background: 'transparent',
                  border: '1.5px solid var(--retro-ink-black)',
                  padding: '4px',
                  cursor: 'pointer',
                }}
              >
                <X size={16} />
              </button>

              {/* Modal Header */}
              <div style={{ borderBottom: '2px solid var(--retro-ink-black)', paddingBottom: '12px', marginBottom: '18px' }}>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--retro-font-mono)',
                      fontSize: '0.8rem',
                      fontWeight: 800,
                      backgroundColor: 'var(--retro-bg-cardboard)',
                      padding: '2px 8px',
                      border: '1px solid var(--retro-ink-black)',
                    }}
                  >
                    {selectedCase.id}
                  </span>
                  <RetroStamp type={selectedCase.priority === 'HIGH' ? 'urgent' : 'verified'} label={selectedCase.riskLevel} />
                </div>
                <h3 className="retro-headline-md" style={{ margin: 0 }}>
                  {selectedCase.beneficiaryName} — Complete Clinical Docket
                </h3>
              </div>

              {/* Factors */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.82rem', fontWeight: 800, marginBottom: '8px' }}>
                  ALGORITHMIC DISTRESS MARKERS DETECTED:
                </h4>
                <ul
                  style={{
                    fontFamily: 'var(--retro-font-mono)',
                    fontSize: '0.78rem',
                    lineHeight: '1.7',
                    paddingLeft: '18px',
                    margin: 0,
                  }}
                >
                  {selectedCase.contributingFactors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>

              {/* Audio Interaction Record */}
              {selectedCase.interactions && selectedCase.interactions.length > 0 && (
                <div
                  style={{
                    border: '1.5px solid var(--retro-ink-black)',
                    padding: '14px',
                    backgroundColor: 'var(--retro-bg-cardboard)',
                    marginBottom: '20px',
                  }}
                >
                  <h4 style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.8rem', fontWeight: 800, margin: '0 0 6px 0' }}>
                    LATEST MULTIMODAL AUDIO CHECK-IN (INTERACTION #{selectedCase.interactions[0].id})
                  </h4>
                  <div className="retro-typewriter" style={{ fontSize: '0.78rem', fontStyle: 'italic', marginBottom: '6px' }}>
                    "{selectedCase.interactions[0].textExcerpt}"
                  </div>
                  <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem', color: 'var(--retro-ink-muted)' }}>
                    Language: {selectedCase.interactions[0].language} • Duration: {selectedCase.interactions[0].duration} • ASR Quality: {selectedCase.interactions[0].qualityScore}
                  </div>
                </div>
              )}

              {/* Quick Actions */}
              <div style={{ borderTop: '2px solid var(--retro-ink-black)', paddingTop: '16px' }}>
                <h4 style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.8rem', fontWeight: 800, marginBottom: '10px' }}>
                  DISPATCH OFFICIAL REHABILITATION INTERVENTION:
                </h4>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => {
                      handleRouteIntervention(selectedCase.id, 'Clinical Psychological First Aid');
                      setSelectedCase(null);
                    }}
                    className="retro-btn retro-btn-urgent"
                    style={{ fontSize: '0.75rem' }}
                  >
                    <span>CLINICAL FIRST AID (TELE-MANAS)</span>
                  </button>
                  <button
                    onClick={() => {
                      handleRouteIntervention(selectedCase.id, 'NALSA Legal Aid Referral');
                      setSelectedCase(null);
                    }}
                    className="retro-btn"
                    style={{ fontSize: '0.75rem' }}
                  >
                    <span>NALSA LEGAL AID</span>
                  </button>
                  <button
                    onClick={() => {
                      handleRouteIntervention(selectedCase.id, 'Safe Shelter & Witness Relocation');
                      setSelectedCase(null);
                    }}
                    className="retro-btn"
                    style={{ fontSize: '0.75rem' }}
                  >
                    <span>SAFE RELOCATION</span>
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RetroCounsellorView;
