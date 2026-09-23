import type { Metadata } from 'next';
import './globals.css';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'Healthcare Triage Assistant',
  description: 'Educational prototype for triage support only.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased text-gray-900 bg-gray-50 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow">
          {children}
        </main>
        <DisclaimerBanner position="bottom" />
      </body>
    </html>
  );
}
