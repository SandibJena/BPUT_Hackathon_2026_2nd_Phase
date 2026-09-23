export const DISCLAIMER = 'Educational prototype for triage support only. This system provides decision-support information only. It does not diagnose, prescribe treatment, or replace a qualified healthcare professional.';

export const FACILITIES = [
  ['OPD', 'Outpatient department'], ['PHC', 'Primary health centre'],
  ['CHC', 'Community health centre'], ['district', 'District hospital'],
  ['camp', 'Public health camp'], ['company_clinic', 'Company clinic'],
  ['industrial_unit', 'Industrial-estate unit'], ['campus', 'Campus health centre'],
] as const;

export const SCENARIOS = [
  ['opd_queue', 'Outpatient queue'], ['campus_fever', 'Campus fever'],
  ['industrial_screening', 'Industrial screening'], ['maternal_followup', 'Maternal follow-up'],
  ['chronic_checkin', 'Chronic check-in'], ['health_camp', 'Public health camp'],
  ['referral', 'Referral preparation'],
] as const;
