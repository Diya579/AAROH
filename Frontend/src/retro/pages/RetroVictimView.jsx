import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Mic, 
  Square, 
  Send, 
  ShieldCheck, 
  Clock, 
  Heart, 
  AlertTriangle, 
  PhoneCall, 
  CheckCircle,
  FileCheck,
  Lock
} from 'lucide-react';
import { RetroStamp } from '../components/RetroStamp';
import { RetroTiltCard } from '../components/RetroTiltCard';
import { caseService } from '../../services/caseService';

export const RetroVictimView = () => {
  const [caseData, setCaseData] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [voiceSubmitted, setVoiceSubmitted] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [textSubmitted, setTextSubmitted] = useState(false);

  useEffect(() => {
    async function fetchCase() {
      const allCases = await caseService.getCases();
      if (allCases.length > 0) {
        setCaseData(allCases[0]); // Case #9821
      }
    }
    fetchCase();
  }, []);

  useEffect(() => {
    let timer;
    if (isRecording) {
      timer = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setRecordingSeconds(0);
    }
    return () => clearInterval(timer);
  }, [isRecording]);

  const handleVoiceSubmit = () => {
    setIsRecording(false);
    setVoiceSubmitted(true);
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textInput.trim()) {
      setTextSubmitted(true);
    }
  };

  if (!caseData) {
    return (
      <div style={{ maxWidth: '1000px', margin: '40px auto', textAlign: 'center', fontFamily: 'var(--retro-font-mono)' }}>
        PREPARING CONFIDENTIAL TELEGRAM DOSSIER...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Top Banner Tag */}
      <div
        style={{
          borderBottom: '2px solid var(--retro-ink-black)',
          paddingBottom: '12px',
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
            <RetroStamp type="sovereign" label="CONFIDENTIAL TELEGRAPHIC DESK" size="sm" />
            <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.78rem' }}>
              DOSSIER #{caseData.id} • {caseData.beneficiaryId}
            </span>
          </div>
          <h2 className="retro-headline-md" style={{ margin: '6px 0 0 0' }}>
            {caseData.beneficiaryName} — Personal Safety Docket
          </h2>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <RetroStamp type={caseData.priority === 'HIGH' ? 'urgent' : 'verified'} label={`STATUS: ${caseData.riskLevel.toUpperCase()}`} />
          <RetroStamp type="verified" label="CONSENT VERIFIED" />
        </div>
      </div>

      {/* Grid: Distress Seismograph & Safe Hours */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
          marginBottom: '32px',
        }}
      >
        {/* Card 1: Distress Seismograph */}
        <RetroTiltCard cardboard>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.8rem', fontWeight: 800 }}>
              SEISMOGRAPHIC DISTRESS INDEX
            </span>
            <RetroStamp type="urgent" label={`${caseData.baselineDeviation} SHIFT`} size="sm" />
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '12px' }}>
            <div
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '3.2rem',
                fontWeight: 900,
                color: 'var(--retro-stamp-red)',
                lineHeight: 1,
              }}
            >
              {caseData.distressScore}
            </div>
            <div>
              <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.82rem', fontWeight: 700 }}>
                CURRENT SCORE / 100
              </div>
              <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', color: 'var(--retro-ink-muted)' }}>
                Baseline: {caseData.baselineScore}/100 • Trend: {caseData.trend}
              </div>
            </div>
          </div>

          {/* Seismograph History Visualizer */}
          <div style={{ borderTop: '1px solid var(--retro-ink-black)', paddingTop: '12px' }}>
            <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem', fontWeight: 700, marginBottom: '8px' }}>
              30-DAY DISTRESS SEISMOGRAPH (HISTORICAL TRACE):
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end', height: '60px', backgroundColor: 'var(--retro-bg-paper)', padding: '8px', border: '1px solid var(--retro-ink-black)' }}>
              {caseData.distressHistory.map((item, i) => {
                const heightPct = (item.score / 100) * 100;
                return (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                    <div
                      style={{
                        width: '100%',
                        height: `${heightPct}%`,
                        backgroundColor: item.score > 70 ? 'var(--retro-stamp-red)' : 'var(--retro-ink-black)',
                        opacity: 0.85,
                      }}
                      title={`${item.day}: ${item.score}/100`}
                    />
                    <span style={{ fontSize: '0.62rem', fontFamily: 'var(--retro-font-mono)', marginTop: '4px' }}>
                      {item.day.replace('Day ', 'D')}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </RetroTiltCard>

        {/* Card 2: Safe Window & Tele-MANAS Assignee */}
        <RetroTiltCard paper>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.8rem', fontWeight: 800 }}>
              SOVEREIGN SAFE-WINDOW REGIME
            </span>
            <RetroStamp type="verified" label="PROTECTED" size="sm" />
          </div>

          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.82rem', marginBottom: '16px' }}>
            <div style={{ marginBottom: '8px' }}>
              <strong>Configured Safe Hours:</strong> {caseData.safeHours}
            </div>
            <div style={{ marginBottom: '8px' }}>
              <strong>Designated Channel:</strong> {caseData.safeChannel}
            </div>
            <div style={{ marginBottom: '8px' }}>
              <strong>Primary Psychologist:</strong> {caseData.assignedOfficial}
            </div>
            <div>
              <strong>Backup Clinical Assignee:</strong> {caseData.backupAssignee}
            </div>
          </div>

          <div
            style={{
              padding: '10px 12px',
              backgroundColor: 'var(--retro-stamp-red-bg)',
              border: '1.5px dashed var(--retro-stamp-red)',
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.75rem',
              color: 'var(--retro-stamp-red)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <PhoneCall size={14} />
            <span>DIRECT TELE-MANAS CLINICAL SPEED-DIAL: 14416 (EXT 201)</span>
          </div>
        </RetroTiltCard>
      </div>

      {/* Multimodal Check-In Station */}
      <section
        style={{
          border: '2px solid var(--retro-ink-black)',
          backgroundColor: 'var(--retro-bg-paper-light)',
          padding: '28px',
          boxShadow: 'var(--retro-shadow-md)',
          marginBottom: '32px',
        }}
      >
        <div
          style={{
            borderBottom: '1.5px solid var(--retro-ink-black)',
            paddingBottom: '12px',
            marginBottom: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <div>
            <h3 className="retro-headline-md" style={{ margin: 0 }}>
              Daily Safe-Hour Check-In Terminal
            </h3>
            <p className="retro-typewriter" style={{ fontSize: '0.78rem', margin: '4px 0 0 0' }}>
              Encrypted dispatch securely transmitted to your assigned clinical counselor.
            </p>
          </div>
          <RetroStamp type="urgent" label="ACTIVE SAFE-HOUR WINDOW" size="sm" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
          {/* Method A: Voice Audio Check-in */}
          <div
            style={{
              border: '1.5px solid var(--retro-ink-black)',
              padding: '20px',
              backgroundColor: 'var(--retro-bg-paper)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Mic size={18} style={{ color: 'var(--retro-stamp-red)' }} />
              <h4 style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '1.1rem', margin: 0 }}>
                1. Voice Telegram Check-In
              </h4>
            </div>
            <p className="retro-typewriter" style={{ fontSize: '0.78rem', marginBottom: '16px' }}>
              Speak naturally in Hindi, English, or your native dialect for 60–90 seconds. ASR extracts semantic clarity and paralinguistic tone.
            </p>

            {voiceSubmitted ? (
              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--retro-stamp-green-bg)',
                  border: '1.5px solid var(--retro-stamp-green)',
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.78rem',
                  color: 'var(--retro-stamp-green)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <CheckCircle size={16} />
                <span>Voice Telegram Dispatched. Acoustic Jitter: 0.84% (Normative).</span>
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
                  {!isRecording ? (
                    <button
                      onClick={() => setIsRecording(true)}
                      className="retro-btn retro-btn-urgent"
                      style={{ fontSize: '0.78rem', padding: '8px 14px' }}
                    >
                      <Mic size={14} />
                      <span>START RECORDING AUDIO</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleVoiceSubmit}
                      className="retro-btn"
                      style={{ fontSize: '0.78rem', padding: '8px 14px', backgroundColor: '#FEE2E2' }}
                    >
                      <Square size={14} style={{ color: 'var(--retro-stamp-red)' }} />
                      <span>HALT & DISPATCH ({recordingSeconds}s)</span>
                    </button>
                  )}

                  {isRecording && (
                    <motion.div
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ repeat: Infinity, duration: 1 }}
                      style={{
                        fontFamily: 'var(--retro-font-mono)',
                        fontSize: '0.75rem',
                        color: 'var(--retro-stamp-red)',
                        fontWeight: 800,
                      }}
                    >
                      ● TRANSMITTING ENCRYPTED AUDIO...
                    </motion.div>
                  )}
                </div>

                <div
                  style={{
                    fontFamily: 'var(--retro-font-mono)',
                    fontSize: '0.72rem',
                    color: 'var(--retro-ink-faint)',
                  }}
                >
                  Previous Entry: "Pichle do din se darr lag raha hai..." (Quality: 98%)
                </div>
              </div>
            )}
          </div>

          {/* Method B: Text Form Check-in */}
          <div
            style={{
              border: '1.5px solid var(--retro-ink-black)',
              padding: '20px',
              backgroundColor: 'var(--retro-bg-paper)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <FileCheck size={18} style={{ color: 'var(--retro-stamp-green)' }} />
              <h4 style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '1.1rem', margin: 0 }}>
                2. Typewriter Text Telegram
              </h4>
            </div>
            <p className="retro-typewriter" style={{ fontSize: '0.78rem', marginBottom: '12px' }}>
              Briefly describe your sleep quality, safety perception, and support requirements.
            </p>

            {textSubmitted ? (
              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--retro-stamp-green-bg)',
                  border: '1.5px solid var(--retro-stamp-green)',
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.78rem',
                  color: 'var(--retro-stamp-green)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <CheckCircle size={16} />
                <span>Text Dispatch Logged in Clinical Docket.</span>
              </div>
            ) : (
              <form onSubmit={handleTextSubmit}>
                <textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Type your confidential daily check-in here..."
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '8px',
                    fontFamily: 'var(--retro-font-mono)',
                    fontSize: '0.8rem',
                    border: '1.5px solid var(--retro-ink-black)',
                    backgroundColor: 'var(--retro-bg-paper-light)',
                    marginBottom: '10px',
                    boxSizing: 'border-box',
                  }}
                />
                <button
                  type="submit"
                  className="retro-btn retro-btn-forest"
                  style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                >
                  <Send size={13} />
                  <span>TRANSMIT TELEGRAM</span>
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* Historical Timeline of Interventions */}
      <section
        style={{
          border: '2px solid var(--retro-ink-black)',
          backgroundColor: 'var(--retro-bg-paper)',
          padding: '24px',
          boxShadow: 'var(--retro-shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 className="retro-headline-md" style={{ margin: 0 }}>
            Chronological Docket History
          </h3>
          <RetroStamp type="verified" label="AUDITED LEDGER" size="sm" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {caseData.timeline.map((event, idx) => (
            <div
              key={idx}
              style={{
                borderLeft: '3px solid var(--retro-ink-black)',
                paddingLeft: '14px',
                position: 'relative',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.72rem',
                  color: 'var(--retro-ink-muted)',
                }}
              >
                {event.date} • {event.type}
              </div>
              <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '1rem', fontWeight: 700 }}>
                {event.title}
              </div>
              <p className="retro-typewriter" style={{ fontSize: '0.78rem', margin: '2px 0 0 0' }}>
                {event.description}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default RetroVictimView;
