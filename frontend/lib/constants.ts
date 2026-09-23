export const DISCLAIMER = 'Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice.';

export const PRIORITY_COLORS: Record<string, string> = {
  EMERGENCY: 'bg-emergency',
  HIGH: 'bg-high',
  NORMAL: 'bg-normal',
  INSUFFICIENT_INFO: 'bg-insufficient',
};

export const PRIORITY_LABELS: Record<string, string> = {
  EMERGENCY: 'EMERGENCY',
  HIGH: 'HIGH',
  NORMAL: 'NORMAL',
  INSUFFICIENT_INFO: 'NEEDS INFO',
};

export const FACILITY_TYPES = [
  { id: 'chc', name: 'Community Health Centre (CHC)' },
  { id: 'phc', name: 'Primary Health Centre (PHC)' },
  { id: 'dh', name: 'District Hospital' },
];

export const SCENARIOS = [
  { id: 'fever_clinic', name: 'Fever Clinic' },
  { id: 'maternal', name: 'Maternal Health' },
  { id: 'trauma', name: 'Trauma/Emergency' },
  { id: 'general_opd', name: 'General OPD' }
];

export const AGE_BANDS = [
  { id: 'infant', name: '0-1 year' },
  { id: 'child', name: '1-12 years' },
  { id: 'teen', name: '13-17 years' },
  { id: 'adult', name: '18-60 years' },
  { id: 'senior', name: '60+ years' },
];
