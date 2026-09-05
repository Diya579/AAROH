// AAROH Consent & Privacy Service — DPDP Act 2023 Granular Preferences

class ConsentService {
  constructor() {
    this.preferences = {
      monitoringConsent: true,
      textAnalysisConsent: true,
      voiceAnalysisConsent: true,
      caseLinkageConsent: true,
      safeChannel: 'voice_telemanas',
      safeTimeSlot: '17:00-19:00',
      allowEmergencyOutreach: true,
      preferredLanguage: 'hi',
    };
  }

  getPreferences() {
    return Promise.resolve({ ...this.preferences });
  }

  updatePreferences(newPrefs) {
    this.preferences = { ...this.preferences, ...newPrefs };
    return Promise.resolve({ ...this.preferences, updatedAt: new Date().toISOString() });
  }
}

export const consentService = new ConsentService();
