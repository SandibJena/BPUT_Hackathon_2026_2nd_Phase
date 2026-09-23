import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: { extend: { colors: { ink: '#17333b', brand: '#0b625d', mist: '#eff7f5' } } },
  plugins: [],
} satisfies Config;
