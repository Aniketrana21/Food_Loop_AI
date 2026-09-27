'use client';

import React, { useState } from 'react';
import { Sidebar, ScreenId, UserRole } from '@/components/navigation/Sidebar';
import { TopHeader } from '@/components/navigation/TopHeader';
import { DonateModal } from '@/components/DonateModal';
import { AICoPilotDrawer } from '@/components/AICoPilotDrawer';
import { FoodListing } from '@/types';
import { CheckCircle2, X } from 'lucide-react';

// Import Screen Components
import { 
  LoginScreen, 
  RegisterScreen, 
  OrgSetupScreen 
} from '@/components/screens/AuthScreens';

import { 
  KitchenDashboard, 
  AdminDashboard, 
  ProcessingDashboard, 
  NgoDashboard, 
  DriverDashboard 
} from '@/components/screens/DashboardScreens';

import { 
  KitchenProfileStaffScreen,
  InventoryScreen, 
  MenuManagementScreen, 
  ProductionPlanningScreen, 
  ConsumptionScreen, 
  WasteReportingScreen 
} from '@/components/screens/OperationsScreens';

import { ComputerVisionScreen } from '@/components/screens/ComputerVisionScreen';

import { 
  AiForecastScreen, 
  ProductionOptimizerScreen, 
  AiAssistantScreen, 
  RagKnowledgeCenterScreen 
} from '@/components/screens/AiScreens';

import { 
  SurplusMarketplaceScreen, 
  RecipientMatchingScreen, 
  DonationDetailsScreen, 
  MapLogisticsScreen, 
  QrVerificationScreen 
} from '@/components/screens/RedistributionScreens';

import { 
  ImpactDashboardScreen, 
  NotificationsScreen, 
  SettingsScreen, 
  AuditLogsScreen 
} from '@/components/screens/GovernanceScreens';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<ScreenId>('kitchen_dashboard');
  const [userRole, setUserRole] = useState<UserRole>('kitchen_mgr');
  
  // Navigation & Drawer States
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [donateModalOpen, setDonateModalOpen] = useState(false);
  const [aiDrawerOpen, setAiDrawerOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Success Toast Trigger
  const showToast = (message: string) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  // Role Switcher Handler
  const handleRoleChange = (newRole: UserRole) => {
    setUserRole(newRole);
    let defaultScreen: ScreenId = 'kitchen_dashboard';
    if (newRole === 'super_admin') defaultScreen = 'admin_dashboard';
    else if (newRole === 'fpu_mgr') defaultScreen = 'processing_dashboard';
    else if (newRole === 'ngo_lead') defaultScreen = 'ngo_dashboard';
    else if (newRole === 'driver') defaultScreen = 'driver_dashboard';
    else if (newRole === 'auditor') defaultScreen = 'audit_logs';

    setCurrentScreen(defaultScreen);
    showToast(`Role switched to ${newRole.replace('_', ' ').toUpperCase()}`);
  };

  const handleNewDonation = (listing: FoodListing) => {
    showToast(`Surplus batch "${listing.title}" successfully broadcasted to regional food banks.`);
  };

  // Check if current screen is unauthenticated / full page (Login, Register, Org Setup)
  const isAuthScreen = ['login', 'register', 'org_setup'].includes(currentScreen);

  // Screen Routing Renderer
  const renderCurrentScreen = () => {
    switch (currentScreen) {
      // 1. Auth Screens
      case 'login':
        return <LoginScreen onNavigate={setCurrentScreen} onSetRole={handleRoleChange} onShowSuccess={showToast} />;
      case 'register':
        return <RegisterScreen onNavigate={setCurrentScreen} onSetRole={handleRoleChange} onShowSuccess={showToast} />;
      case 'org_setup':
        return <OrgSetupScreen onNavigate={setCurrentScreen} onSetRole={handleRoleChange} onShowSuccess={showToast} />;

      // 2. Dashboards
      case 'kitchen_dashboard':
        return <KitchenDashboard onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'admin_dashboard':
        return <AdminDashboard onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'processing_dashboard':
        return <ProcessingDashboard onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'ngo_dashboard':
        return <NgoDashboard onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'driver_dashboard':
        return <DriverDashboard onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;

      // 3. Operations
      case 'kitchen_profile':
        return <KitchenProfileStaffScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'inventory':
        return <InventoryScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'menu_management':
        return <MenuManagementScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'production_planning':
        return <ProductionPlanningScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'consumption':
        return <ConsumptionScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'waste_reporting':
        return <WasteReportingScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'computer_vision':
        return <ComputerVisionScreen onNavigate={setCurrentScreen} onShowSuccess={showToast} />;

      // 4. Intelligence & Forecasting
      case 'ai_forecast':
        return <AiForecastScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'production_optimizer':
        return <ProductionOptimizerScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'ai_assistant':
        return <AiAssistantScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'rag_knowledge':
        return <RagKnowledgeCenterScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;

      // 5. Redistribution & Logistics
      case 'surplus_marketplace':
        return <SurplusMarketplaceScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'recipient_matching':
        return <RecipientMatchingScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'donation_details':
        return <DonationDetailsScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'map_logistics':
        return <MapLogisticsScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
      case 'qr_verification':
        return <QrVerificationScreen onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;

      // 6. Governance & System
      case 'impact_dashboard':
        return <ImpactDashboardScreen onNavigate={setCurrentScreen} onShowSuccess={showToast} />;
      case 'notifications':
        return <NotificationsScreen onNavigate={setCurrentScreen} onShowSuccess={showToast} />;
      case 'settings':
        return <SettingsScreen onNavigate={setCurrentScreen} onShowSuccess={showToast} />;
      case 'audit_logs':
        return <AuditLogsScreen onNavigate={setCurrentScreen} onShowSuccess={showToast} />;

      default:
        return <KitchenDashboard onNavigate={setCurrentScreen} onOpenDonateModal={() => setDonateModalOpen(true)} onShowSuccess={showToast} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col antialiased selection:bg-emerald-500 selection:text-slate-950">
      
      {/* Global Interactive Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-6 z-50 p-4 rounded-2xl glass-panel bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 shadow-2xl flex items-center space-x-3 max-w-md animate-slide-up">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <div className="text-xs font-semibold flex-1 leading-snug">{toastMessage}</div>
          <button
            onClick={() => setToastMessage(null)}
            className="p-1 rounded-lg text-emerald-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {isAuthScreen ? (
        // Full Page Layout for Auth Screens
        <main className="flex-1 w-full flex items-center justify-center p-4">
          {renderCurrentScreen()}
        </main>
      ) : (
        // Enterprise SaaS App Shell: Persistent Sidebar + Header + Content Area
        <div className="flex-1 flex w-full">
          {/* Navigation Sidebar */}
          <Sidebar
            currentScreen={currentScreen}
            onNavigate={setCurrentScreen}
            userRole={userRole}
            isMobileOpen={mobileMenuOpen}
            onCloseMobile={() => setMobileMenuOpen(false)}
          />

          {/* Main App Canvas */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Top Navigation Bar */}
            <TopHeader
              currentScreen={currentScreen}
              userRole={userRole}
              onRoleChange={handleRoleChange}
              onOpenMobileMenu={() => setMobileMenuOpen(true)}
              onOpenDonateModal={() => setDonateModalOpen(true)}
              onOpenAICoPilot={() => setAiDrawerOpen(true)}
              onOpenNotifications={() => setCurrentScreen('notifications')}
              unreadCount={3}
            />

            {/* View Area */}
            <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-fade-in">
              {renderCurrentScreen()}
            </main>

            {/* Enterprise Platform Footer */}
            <footer className="w-full border-t border-white/5 py-4 px-6 text-[11px] text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-400">FoodLoop AI</span>
                <span>&bull; Institutional Food Reduction & Redistribution Platform</span>
              </div>
              <div className="flex items-center space-x-4">
                <span>XGBoost R²=0.829</span>
                <span>Google OR-Tools CVRPTW</span>
                <span>FDA Food Code 2022</span>
                <span className="text-emerald-400 flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
                  <span>PostgreSQL Active</span>
                </span>
              </div>
            </footer>
          </div>
        </div>
      )}

      {/* Global Declare Surplus Modal */}
      <DonateModal
        isOpen={donateModalOpen}
        onClose={() => setDonateModalOpen(false)}
        onSuccess={handleNewDonation}
      />

      {/* Global AI Copilot Drawer */}
      <AICoPilotDrawer
        isOpen={aiDrawerOpen}
        onClose={() => setAiDrawerOpen(false)}
        initialQuery=""
      />

    </div>
  );
}
