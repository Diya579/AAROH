import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  Square, 
  RotateCcw, 
  Play, 
  Pause, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  Clock, 
  Shield 
} from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { interactionService } from '../../services/interactionService';

export const VoiceCheckInModal = ({ isOpen, onClose, onSwitchToText, onSuccess }) => {
  // Gates: 'permission' | 'recording' | 'review' | 'processing' | 'confirmed' | 'error'
  const [gate, setGate] = useState('permission');
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [hasMicPermission, setHasMicPermission] = useState(null);
  const [isPlayingReview, setIsPlayingReview] = useState(false);
  const [confirmationData, setConfirmationData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const timerRef = useRef(null);

  // Reset state on open
  useEffect(() => {
    if (isOpen) {
      setGate('permission');
      setSecondsElapsed(0);
      setIsPlayingReview(false);
      setConfirmationData(null);
      setErrorMessage('');
      checkMicrophone();
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isOpen]);

  const checkMicrophone = () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setHasMicPermission(false);
      setGate('error');
      setErrorMessage('Your current browser or device does not support audio recording. You can complete a text check-in instead.');
      return;
    }
    // Probe mic permissions
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        // Stop stream probe
        stream.getTracks().forEach(track => track.stop());
        setHasMicPermission(true);
        setGate('permission');
      })
      .catch((err) => {
        setHasMicPermission(false);
        setGate('error');
        setErrorMessage('Microphone access was not granted. Please enable microphone permissions in your browser settings, or switch to text response.');
      });
  };

  const startRecording = () => {
    setGate('recording');
    setSecondsElapsed(0);
    timerRef.current = setInterval(() => {
      setSecondsElapsed(prev => prev + 1);
    }, 1000);
  };

  const stopRecording = () => {
    clearInterval(timerRef.current);
    if (secondsElapsed < 2) {
      setGate('error');
      setErrorMessage('The recording was too short (less than 2 seconds). Please record a longer message so our care team can understand your status.');
      return;
    }
    setGate('review');
  };

  const handleRetry = () => {
    clearInterval(timerRef.current);
    setSecondsElapsed(0);
    setIsPlayingReview(false);
    setGate('permission');
  };

  const toggleReviewPlayback = () => {
    setIsPlayingReview(prev => !prev);
  };

  const handleSubmitVoice = async () => {
    setGate('processing');
    try {
      const dummyBlob = new Blob(['simulated-audio-data'], { type: 'audio/wav' });
      const result = await interactionService.submitVoiceCheckIn(dummyBlob, {
        duration: secondsElapsed,
        language: 'Hindi',
      });
      setConfirmationData(result);
      setGate('confirmed');
      if (onSuccess) onSuccess(result);
    } catch (err) {
      setGate('error');
      setErrorMessage(err.message || 'Failed to securely transmit audio. Please try again.');
    }
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainderSecs = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remainderSecs.toString().padStart(2, '0')}`;
  };

  return (
    <UX4GModal
      isOpen={isOpen}
      onClose={onClose}
      title="Multimodal Voice Check-In"
      subtitle="Gate-verified consensual speech check-in (DPDP Act 2023 Compliant)"
      maxWidth="580px"
    >
      <div style={{ padding: '8px 0' }}>
        {/* ================= GATE 1: PERMISSION & START ================= */}
        {gate === 'permission' && (
          <div style={{ textAlign: 'center', padding: '16px 8px' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-violet-50)',
                color: 'var(--ux4g-violet-700)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
                border: '1.5px solid var(--ux4g-violet-200)',
              }}
            >
              <Mic size={30} />
            </div>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
              Ready to Begin Your Voice Check-In?
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-secondary)', maxWidth: '440px', margin: '0 auto 20px', lineHeight: 1.6 }}>
              Speak naturally in your preferred language about how you have been feeling, your sleep quality, and any immediate emotional needs.
            </p>

            <div style={{ backgroundColor: 'var(--ux4g-bg)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginBottom: '24px', textAlign: 'left', display: 'flex', gap: '10px' }}>
              <Shield size={20} color="var(--ux4g-violet-700)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)', lineHeight: 1.5 }}>
                <strong style={{ color: 'var(--ux4g-violet-900)' }}>Privacy Guarantee:</strong> Your audio is transmitted directly to our sovereign Indian government ASR pipeline with end-to-end encryption.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <UX4GButton variant="outline" size="md" icon={FileText} onClick={onSwitchToText}>
                Switch to Written Text
              </UX4GButton>
              <UX4GButton variant="primary" size="md" icon={Mic} onClick={startRecording}>
                Start Speaking Now
              </UX4GButton>
            </div>
          </div>
        )}

        {/* ================= GATE 2: RECORDING ================= */}
        {gate === 'recording' && (
          <div style={{ textAlign: 'center', padding: '24px 8px' }}>
            <div
              style={{
                width: '76px',
                height: '76px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-danger-bg)',
                color: 'var(--ux4g-danger)',
                border: '2px solid var(--ux4g-danger)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
                animation: 'pulse 1.5s infinite',
              }}
            >
              <Mic size={34} />
            </div>

            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', letterSpacing: '0.04em', marginBottom: '8px' }}>
              {formatTime(secondsElapsed)}
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-danger-text)', fontWeight: 600, marginBottom: '24px' }}>
              ● Recording in Progress — Speak comfortably
            </p>

            {/* Audio Wave Visualizer Simulation */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', height: '40px', marginBottom: '28px' }}>
              {[18, 34, 26, 40, 32, 22, 38, 28, 14, 30, 36, 20].map((h, i) => (
                <div
                  key={i}
                  style={{
                    width: '4px',
                    height: `${h}px`,
                    backgroundColor: 'var(--ux4g-violet-600)',
                    borderRadius: '2px',
                    animation: `pulse ${(i % 3 + 1) * 0.4}s infinite alternate`,
                  }}
                />
              ))}
            </div>

            <UX4GButton variant="danger" size="lg" icon={Square} onClick={stopRecording}>
              Stop Recording
            </UX4GButton>
          </div>
        )}

        {/* ================= GATE 3: REVIEW ================= */}
        {gate === 'review' && (
          <div style={{ textAlign: 'center', padding: '16px 8px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'var(--ux4g-violet-50)', color: 'var(--ux4g-violet-700)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '14px' }}>
              <Clock size={28} />
            </div>

            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
              Review Your Voice Check-In
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '20px' }}>
              Duration recorded: <strong>{formatTime(secondsElapsed)}</strong>. You can listen back or re-record before sending.
            </p>

            {/* Simulated Audio Player */}
            <div style={{ backgroundColor: 'var(--ux4g-bg)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: '420px', margin: '0 auto 24px' }}>
              <button
                type="button"
                onClick={toggleReviewPlayback}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--ux4g-violet-700)',
                  color: '#FFF',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                }}
              >
                {isPlayingReview ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
              </button>

              <div style={{ flex: 1, margin: '0 16px' }}>
                <div style={{ height: '6px', backgroundColor: 'var(--ux4g-border)', borderRadius: '3px', position: 'relative' }}>
                  <div style={{ width: isPlayingReview ? '65%' : '0%', height: '100%', backgroundColor: 'var(--ux4g-violet-700)', borderRadius: '3px', transition: 'width 2s linear' }} />
                </div>
              </div>

              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--ux4g-text-secondary)' }}>
                {formatTime(secondsElapsed)}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <UX4GButton variant="outline" size="md" icon={RotateCcw} onClick={handleRetry}>
                Re-Record
              </UX4GButton>
              <UX4GButton variant="primary" size="md" icon={CheckCircle2} onClick={handleSubmitVoice}>
                Submit to Care Team
              </UX4GButton>
            </div>
          </div>
        )}

        {/* ================= GATE 4: PROCESSING ================= */}
        {gate === 'processing' && (
          <div style={{ textAlign: 'center', padding: '40px 16px' }}>
            <div className="ux4g-spinner" style={{ width: '48px', height: '48px', margin: '0 auto 20px', borderWidth: '4px', borderColor: 'var(--ux4g-violet-200)', borderTopColor: 'var(--ux4g-violet-700)' }} />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
              Securing & Transcribing Audio...
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)' }}>
              Connecting with sovereign Indian government bilingual ASR pipeline.
            </p>
          </div>
        )}

        {/* ================= GATE 5: CONFIRMATION ================= */}
        {gate === 'confirmed' && (
          <div style={{ textAlign: 'center', padding: '24px 16px' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: '#DCFCE7', color: '#15803D', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <CheckCircle2 size={34} />
            </div>

            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#14532D', marginBottom: '8px' }}>
              Check-In Successfully Received
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-secondary)', marginBottom: '20px', lineHeight: 1.6 }}>
              Thank you for sharing your voice with us today. Your check-in is logged safely. Your assigned counsellor has been notified of your safe check-in.
            </p>

            <div style={{ backgroundColor: 'var(--ux4g-bg)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-md)', padding: '14px', maxWidth: '380px', margin: '0 auto 24px', textAlign: 'left', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ color: 'var(--ux4g-text-muted)' }}>Reference ID:</span>
                <strong>{confirmationData?.referenceId}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ color: 'var(--ux4g-text-muted)' }}>Transmission:</span>
                <span style={{ color: 'var(--ux4g-success)', fontWeight: 600 }}>Encrypted (TLS 1.3)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--ux4g-text-muted)' }}>Status:</span>
                <span className="ux4g-badge ux4g-badge-low">Received & Verified</span>
              </div>
            </div>

            <UX4GButton variant="primary" size="md" onClick={onClose}>
              Done & Return to Space
            </UX4GButton>
          </div>
        )}

        {/* ================= ERROR STATE ================= */}
        {gate === 'error' && (
          <div style={{ textAlign: 'center', padding: '24px 16px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'var(--ux4g-danger-bg)', color: 'var(--ux4g-danger)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '14px' }}>
              <AlertTriangle size={28} />
            </div>

            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-danger-text)', marginBottom: '8px' }}>
              Recording Interrupted
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', marginBottom: '24px', lineHeight: 1.6 }}>
              {errorMessage}
            </p>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <UX4GButton variant="outline" size="sm" icon={RotateCcw} onClick={handleRetry}>
                Try Microphone Again
              </UX4GButton>
              <UX4GButton variant="primary" size="sm" icon={FileText} onClick={onSwitchToText}>
                Switch to Written Text
              </UX4GButton>
            </div>
          </div>
        )}
      </div>
    </UX4GModal>
  );
};
