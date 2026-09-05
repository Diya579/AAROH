import React from 'react';
import { 
  CheckCircle2, 
  Heart, 
  Clock,
  PhoneCall,
  ShieldCheck
} from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const PersonalTrendCard = () => {
  const milestones = [
    { day: 'Day 1', label: 'Intake Completed', desc: 'Baseline calibrated under clinical protocol', completed: true },
    { day: 'Day 7', label: 'Coping Tools Introduced', desc: 'Grounding techniques established', completed: true },
    { day: 'Day 14', label: 'Midway Clinical Equilibrium', desc: 'Safe shelter & psychosocial check-in', completed: true },
    { day: 'Day 21', label: 'Counselling Session #2', desc: 'Individual consultation with Dr. Rajesh', completed: true },
    { day: 'Day 30', label: '30-Day Recovery Horizon', desc: 'Continuous longitudinal monitoring', current: true },
  ];

  return (
    <UX4GCard elevation={1} liftOnHover={false} style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', paddingBottom: '14px', borderBottom: '1px solid var(--ux4g-border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '6px', backgroundColor: '#F0FDF4', color: '#15803D', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Heart size={16} />
          </div>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Recovery Milestones
            </h4>
            <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-muted)' }}>
              Longitudinal progress under Tele-MANAS clinical protocol
            </p>
          </div>
        </div>

        <span className="ux4g-badge ux4g-badge-low">In Progress</span>
      </div>

      {/* Stepper Timeline with Continuous Track */}
      <div style={{ position: 'relative', paddingLeft: '4px', marginBottom: '18px' }}>
        {/* Continuous background line */}
        <div
          style={{
            position: 'absolute',
            left: '14px',
            top: '12px',
            bottom: '16px',
            width: '2px',
            backgroundColor: '#E2E8F0',
            zIndex: 1,
          }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', zIndex: 2 }}>
          {milestones.map((m, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              {/* Node Icon */}
              <div
                style={{
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  backgroundColor: m.completed ? '#10B981' : m.current ? '#4B23B8' : '#CBD5E1',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '1px',
                  boxShadow: '0 0 0 3px #FFFFFF',
                }}
              >
                {m.completed ? <CheckCircle2 size={13} /> : <Clock size={11} />}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                  <span style={{ fontSize: '0.84rem', fontWeight: m.current ? 700 : 600, color: m.current ? 'var(--ux4g-violet-950)' : 'var(--ux4g-text-primary)' }}>
                    {m.label}
                  </span>
                  <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', backgroundColor: 'var(--ux4g-bg)', padding: '1px 6px', borderRadius: '3px' }}>
                    {m.day}
                  </span>
                </div>
                <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px', lineHeight: 1.4 }}>
                  {m.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Formal Helpline Bar */}
      <div style={{ padding: '10px 12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.76rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--ux4g-text-secondary)' }}>
          <ShieldCheck size={14} color="#15803D" />
          <span>Tele-MANAS Support: <strong>14416</strong></span>
        </div>
        <a href="tel:14416" style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600, textDecoration: 'none' }}>
          Call (24x7 Free)
        </a>
      </div>
    </UX4GCard>
  );
};
