import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        emergency: '#DC2626', // red-600
        high: '#D97706', // amber-600
        normal: '#16A34A', // green-600
        insufficient: '#6B7280', // gray-500
        primary: '#1D4ED8', // blue-700
      }
    },
  },
  plugins: [],
};
export default config;
