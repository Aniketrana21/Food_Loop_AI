import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FoodLoop AI - Intelligent Surplus Food Redistribution & Dispatch',
  description: 'AI-driven surplus food rescue platform connecting commercial kitchens, food banks, and volunteer drivers with automated OR-Tools vehicle routing and XGBoost shelf-life forecasting.',
  keywords: 'food rescue, food waste, surplus redistribution, vehicle routing, OR-Tools, food bank logistics',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-emerald-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
