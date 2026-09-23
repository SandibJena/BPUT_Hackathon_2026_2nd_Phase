'use client';
import { DISCLAIMER } from '@/lib/constants';

export default function AdminPage() {
  return (
    <div className="max-w-5xl mx-auto p-4 pb-24">
      <h1 className="text-2xl font-bold mb-6">Admin Panel</h1>
      <p className="text-gray-500 mb-8">System oversight, auditing, and analytics.</p>
      
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-bold text-lg mb-4">Audit Log Integrity</h2>
          <p className="text-sm mb-4">Cryptographic hashes ensure no triage notes have been tampered with post-submission.</p>
          <button className="btn-secondary w-full">Verify Hashes Now</button>
        </div>
        
        <div className="card">
          <h2 className="font-bold text-lg mb-4">Data Retention Settings</h2>
          <p className="text-sm mb-4">Current TTL for non-escalated demonstration data is set to 24 hours.</p>
          <button className="btn-danger w-full text-white">Purge Expired Data</button>
        </div>

        <div className="card md:col-span-2">
          <h2 className="font-bold text-lg mb-4">Responsible AI & Model Constraints</h2>
          <div className="bg-gray-50 p-4 border rounded text-sm space-y-2">
            <p><strong>System Goal:</strong> Extract structured clinical facts from noisy inputs.</p>
            <p><strong>Strict Restriction:</strong> System is explicitly prompted to NEVER output diagnostic conclusions or disease names.</p>
            <p><strong>Failsafe:</strong> Outputs containing common disease identifiers are flagged and blocked by the output parser.</p>
            <p className="text-amber-700 font-bold mt-4">{DISCLAIMER}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
