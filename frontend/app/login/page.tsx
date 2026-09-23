'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { setToken } from '@/lib/auth';
import { useTranslation } from '@/lib/i18n';
import ErrorMessage from '@/components/ErrorMessage';

const DEMO_USERS = [
  { role: 'Health Worker', user: 'hw_demo', pass: 'demo123' },
  { role: 'Nurse', user: 'nurse_demo', pass: 'demo123' },
  { role: 'Doctor', user: 'doc_demo', pass: 'demo123' },
  { role: 'Admin', user: 'admin_demo', pass: 'demo123' },
];

export default function LoginPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.auth.login(username, password);
      setToken(res.access_token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Login failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-4 pb-20">
      <h1 className="text-2xl font-bold text-center mb-6">{t('Login')}</h1>
      
      <form onSubmit={handleLogin} className="card mb-8">
        {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Username</label>
          <input 
            type="text" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full border border-gray-300 rounded p-2"
            required 
          />
        </div>
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">Password</label>
          <input 
            type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-gray-300 rounded p-2"
            required 
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? 'Logging in...' : t('Login')}
        </button>
      </form>

      <div className="grid grid-cols-2 gap-4">
        {DEMO_USERS.map((u) => (
          <div key={u.role} className="card text-sm p-3 cursor-pointer hover:bg-gray-50" onClick={() => { setUsername(u.user); setPassword(u.pass); }}>
            <div className="font-bold text-primary mb-1">{u.role}</div>
            <div>U: {u.user}</div>
            <div>P: {u.pass}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
