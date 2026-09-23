'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { AGE_BANDS, FACILITY_TYPES, SCENARIOS } from '@/lib/constants';
import { useTranslation } from '@/lib/i18n';
import ConsentModal from '@/components/ConsentModal';
import ErrorMessage from '@/components/ErrorMessage';

export default function IntakePage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [step, setStep] = useState(1);
  const [consentGiven, setConsentGiven] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    patient_info: {
      patient_id: `PT-${Math.floor(Math.random() * 10000)}`,
      age_band: 'adult',
      sex: 'O',
      preferred_language: 'en',
      facility_type: 'phc',
      scenario: 'general_opd'
    },
    text: '',
    vitals: {
      temperature: '',
      pulse: ''
    }
  });

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const vitalsObj = {};
      if (formData.vitals.temperature) Object.assign(vitalsObj, { temperature: Number(formData.vitals.temperature) });
      if (formData.vitals.pulse) Object.assign(vitalsObj, { pulse: Number(formData.vitals.pulse) });
      
      const res = await api.intake.submitText({
        text: formData.text,
        patient_info: formData.patient_info,
        vitals: Object.keys(vitalsObj).length > 0 ? vitalsObj : undefined
      });
      router.push(`/patient/${res.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit intake.');
      setLoading(false);
    }
  };

  if (step === 1 && !consentGiven) {
    return <ConsentModal isOpen={true} onConsent={() => { setConsentGiven(true); setStep(2); }} />;
  }

  return (
    <div className="max-w-2xl mx-auto p-4 pb-24">
      <h1 className="text-2xl font-bold mb-6">{t('Intake Form')}</h1>
      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
      
      <div className="card space-y-6">
        <div>
          <h2 className="font-semibold text-lg border-b pb-2 mb-4">Patient Info (Demo)</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">Age Band</label>
              <select className="w-full border p-2 rounded min-h-[44px]" value={formData.patient_info.age_band} onChange={e => setFormData({...formData, patient_info: {...formData.patient_info, age_band: e.target.value}})}>
                {AGE_BANDS.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1">Sex</label>
              <select className="w-full border p-2 rounded min-h-[44px]" value={formData.patient_info.sex} onChange={e => setFormData({...formData, patient_info: {...formData.patient_info, sex: e.target.value}})}>
                <option value="M">Male</option><option value="F">Female</option><option value="O">Other</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <h2 className="font-semibold text-lg border-b pb-2 mb-4">Clinical Notes</h2>
          <label className="block text-sm mb-1">Symptoms & Observations</label>
          <textarea 
            className="w-full border p-2 rounded min-h-[120px]" 
            placeholder="E.g. patient has high fever for 3 days and severe cough..."
            value={formData.text}
            onChange={e => setFormData({...formData, text: e.target.value})}
          ></textarea>
        </div>

        <div>
          <h2 className="font-semibold text-lg border-b pb-2 mb-4">Vitals (Optional)</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">Temp (°F)</label>
              <input type="number" className="w-full border p-2 rounded min-h-[44px]" value={formData.vitals.temperature} onChange={e => setFormData({...formData, vitals: {...formData.vitals, temperature: e.target.value}})} />
            </div>
            <div>
              <label className="block text-sm mb-1">Pulse (bpm)</label>
              <input type="number" className="w-full border p-2 rounded min-h-[44px]" value={formData.vitals.pulse} onChange={e => setFormData({...formData, vitals: {...formData.vitals, pulse: e.target.value}})} />
            </div>
          </div>
        </div>

        <button onClick={handleSubmit} disabled={loading || !formData.text.trim()} className="btn-primary w-full text-lg mt-6">
          {loading ? 'Processing Analysis...' : 'Submit Triage Request'}
        </button>
      </div>
    </div>
  );
}
