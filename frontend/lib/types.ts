export type PriorityCategory = 'EMERGENCY' | 'HIGH' | 'NORMAL' | 'INSUFFICIENT_INFO';
export type Role = 'health_worker' | 'nurse' | 'doctor' | 'admin';

export interface User {
  id: string;
  username: string;
  role: Role;
  name: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Symptom {
  name: string;
  severity?: string;
  duration?: string;
}

export interface Vitals {
  temperature?: number;
  pulse?: number;
  respiratory_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  spo2?: number;
}

export interface History {
  conditions: string[];
  medications: string[];
  allergies: string[];
}

export interface RiskAssessment {
  priority: PriorityCategory;
  reasons: string[];
  rule_ids_triggered: string[];
  missing_critical_info: string[];
  suggested_questions: string[];
}

export interface PatientInfo {
  patient_id: string;
  age_band: string;
  sex: string;
  preferred_language: string;
  facility_type: string;
  scenario: string;
}

export interface TriageNote {
  id: string;
  created_at: string;
  patient_info: PatientInfo;
  chief_complaint: string;
  symptoms: Symptom[];
  vitals: Vitals;
  history: History;
  risk_assessment: RiskAssessment;
  raw_input_text: string;
  status: 'PENDING' | 'REVIEWED' | 'ESCALATED';
  reviewed_by?: string;
}

export interface TextIntakeRequest {
  text: string;
  patient_info: PatientInfo;
  vitals?: Vitals;
}
