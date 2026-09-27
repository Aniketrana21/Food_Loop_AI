'use client';

import React, { useState } from 'react';
import { 
  Building2, 
  Mail, 
  Lock, 
  User, 
  ArrowRight, 
  ShieldCheck, 
  CheckCircle, 
  AlertCircle, 
  Sparkles,
  MapPin,
  Phone,
  ThermometerSnowflake,
  Utensils
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Input, Select } from '@/components/design-system/Input';
import { Badge } from '@/components/design-system/Badge';
import { ScreenId, UserRole } from '@/components/navigation/Sidebar';

interface AuthScreenProps {
  onNavigate: (screen: ScreenId) => void;
  onSetRole: (role: UserRole) => void;
  onShowSuccess: (msg: string) => void;
}

export const LoginScreen: React.FC<AuthScreenProps> = ({ onNavigate, onSetRole, onShowSuccess }) => {
  const [email, setEmail] = useState('marcus.vance@hyatt-culinary.com');
  const [password, setPassword] = useState('••••••••••••');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDemoLogin = (role: UserRole, demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('DemoSafePass2026!');
    setLoading(true);
    setError(null);
    setTimeout(() => {
      setLoading(false);
      onSetRole(role);
      const targetScreen = 
        role === 'super_admin' ? 'admin_dashboard' :
        role === 'fpu_mgr' ? 'processing_dashboard' :
        role === 'ngo_lead' ? 'ngo_dashboard' :
        role === 'driver' ? 'driver_dashboard' :
        role === 'auditor' ? 'audit_logs' : 'kitchen_dashboard';
      onNavigate(targetScreen);
      onShowSuccess(`Signed in securely as ${role.replace('_', ' ').toUpperCase()}`);
    }, 600);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide valid enterprise credentials.');
      return;
    }
    setLoading(true);
    setError(null);
    setTimeout(() => {
      setLoading(false);
      onSetRole('kitchen_mgr');
      onNavigate('kitchen_dashboard');
      onShowSuccess('Authenticated via Supabase Enterprise Auth with SSO');
    }, 700);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 items-center justify-center shadow-xl shadow-emerald-500/25 ring-1 ring-white/20 mb-2">
            <span className="text-xl font-black text-white">FL</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">FoodLoop AI Enterprise</h1>
          <p className="text-xs text-slate-400">Institutional Surplus Reduction & Redistribution Cloud</p>
        </div>

        {/* Demo Fast Login Pills */}
        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Fast Role Switcher</span>
            <Badge variant="purple" size="sm">Pre-Configured RBAC</Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={() => handleDemoLogin('kitchen_mgr', 'chef.vance@hyatt.com')}
              className="p-2 rounded-xl bg-slate-900/80 hover:bg-emerald-500/20 text-slate-300 hover:text-emerald-400 border border-white/5 transition-all text-left"
            >
              <div className="font-bold text-[11px] text-white">Kitchen Manager</div>
              <div className="text-[10px] text-slate-400">Grand Hyatt Culinary</div>
            </button>
            <button
              onClick={() => handleDemoLogin('super_admin', 'admin@foodloop.ai')}
              className="p-2 rounded-xl bg-slate-900/80 hover:bg-rose-500/20 text-slate-300 hover:text-rose-400 border border-white/5 transition-all text-left"
            >
              <div className="font-bold text-[11px] text-white">Super Admin</div>
              <div className="text-[10px] text-slate-400">Platform Governance</div>
            </button>
            <button
              onClick={() => handleDemoLogin('ngo_lead', 'director@stjudefoodbank.org')}
              className="p-2 rounded-xl bg-slate-900/80 hover:bg-indigo-500/20 text-slate-300 hover:text-indigo-400 border border-white/5 transition-all text-left"
            >
              <div className="font-bold text-[11px] text-white">NGO / Food Bank</div>
              <div className="text-[10px] text-slate-400">St. Jude Community</div>
            </button>
            <button
              onClick={() => handleDemoLogin('driver', 'alex.driver@looplogistics.com')}
              className="p-2 rounded-xl bg-slate-900/80 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-400 border border-white/5 transition-all text-left"
            >
              <div className="font-bold text-[11px] text-white">Logistics Courier</div>
              <div className="text-[10px] text-slate-400">Refrigerated EV Van #3</div>
            </button>
          </div>
        </div>

        {/* Main Form */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Work Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@organization.com"
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
            />

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center space-x-2 text-slate-400 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded bg-slate-900 border-white/20 text-emerald-500 focus:ring-emerald-500" />
                <span>Remember session (14 days)</span>
              </label>
              <button
                type="button"
                onClick={() => onShowSuccess('Password reset link dispatched via Supabase Auth')}
                className="text-emerald-400 hover:underline"
              >
                Forgot password?
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={loading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to FoodLoop
            </Button>
          </form>

          <div className="pt-3 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
            <span>New enterprise organization?</span>
            <button
              onClick={() => onNavigate('register')}
              className="font-bold text-emerald-400 hover:text-emerald-300"
            >
              Register Facility
            </button>
          </div>
        </div>

        {/* Compliance Footer */}
        <div className="flex items-center justify-center space-x-2 text-[11px] text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          <span>SOC-2 Type II Certified • FDA Food Code 2022 Compliant</span>
        </div>

      </div>
    </div>
  );
};

export const RegisterScreen: React.FC<AuthScreenProps> = ({ onNavigate, onShowSuccess }) => {
  const [formData, setFormData] = useState({
    fullName: 'Chef Marcus Vance',
    email: 'marcus.vance@hyatt-culinary.com',
    orgName: 'Grand Hyatt San Francisco',
    role: 'kitchen_mgr',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onShowSuccess('Registration completed! Please complete Organization Setup.');
      onNavigate('org_setup');
    }, 800);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-black text-white tracking-tight">Register New Facility</h1>
          <p className="text-xs text-slate-400">Join the smart surplus reduction network</p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Full Name & Title"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              placeholder="e.g. Executive Chef John Doe"
              required
            />

            <Input
              label="Institutional Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="name@hospitality.com"
              required
            />

            <Input
              label="Organization / Kitchen Entity"
              value={formData.orgName}
              onChange={(e) => setFormData({ ...formData, orgName: e.target.value })}
              placeholder="e.g. Grand Hyatt Culinary Operations"
              required
            />

            <Select
              label="Primary Facility Role"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              options={[
                { value: 'kitchen_mgr', label: 'Commercial / Institutional Kitchen Manager' },
                { value: 'fpu_mgr', label: 'Food Processing Unit (FPU) Plant Lead' },
                { value: 'ngo_lead', label: 'Registered NGO / Food Rescue Organization' },
                { value: 'driver', label: 'Cold-Chain Logistics Courier Fleet' },
                { value: 'auditor', label: 'Third-Party Food Safety Auditor' },
              ]}
            />

            <Input
              label="Create Secure Password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Min. 8 chars, uppercase, digit"
              required
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={loading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Continue to Facility Setup
            </Button>
          </form>

          <div className="pt-3 border-t border-white/10 text-center text-xs text-slate-400">
            <span>Already have enterprise credentials? </span>
            <button
              onClick={() => onNavigate('login')}
              className="font-bold text-emerald-400 hover:text-emerald-300"
            >
              Sign In
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export const OrgSetupScreen: React.FC<AuthScreenProps> = ({ onNavigate, onShowSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [facilityType, setFacilityType] = useState('hotel_resort');
  const [dailyCapacity, setDailyCapacity] = useState('1500');
  const [coldStorageKg, setColdStorageKg] = useState('450');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onShowSuccess('Organization configuration initialized and verified.');
      onNavigate('kitchen_dashboard');
    }, 700);
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-black text-white tracking-tight">Organization & Kitchen Setup</h1>
        <p className="text-xs text-slate-400">
          Configure physical capacities and critical control thresholds for automated surplus dispatch
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Step 1: Facility Profile */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center space-x-2 text-emerald-400">
            <Building2 className="w-4 h-4" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Facility Profile & Verification</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Legal Organization Name"
              defaultValue="Grand Hyatt San Francisco Culinary LLC"
              required
            />

            <Select
              label="Facility Classification"
              value={facilityType}
              onChange={(e) => setFacilityType(e.target.value)}
              options={[
                { value: 'hotel_resort', label: 'Luxury Hotel / Resort Banquet Facility' },
                { value: 'university_dining', label: 'University / College Dining Hall' },
                { value: 'corporate_cafeteria', label: 'Corporate Tech Campus Cafeteria' },
                { value: 'hospital_kitchen', label: 'Healthcare / Hospital Food Service' },
                { value: 'industrial_fpu', label: 'Industrial Food Processing & Canning Plant' },
              ]}
            />

            <Input
              label="Facility Dispatch Address"
              defaultValue="345 Stockton St, San Francisco, CA 94108"
              required
            />

            <Input
              label="Emergency Dispatch Phone"
              defaultValue="+1 (415) 398-1234"
              required
            />
          </div>
        </div>

        {/* Step 2: Operational Capacities */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center space-x-2 text-indigo-400">
            <Utensils className="w-4 h-4" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Kitchen & Holding Capacities</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Max Meal Service Capacity"
              type="number"
              value={dailyCapacity}
              onChange={(e) => setDailyCapacity(e.target.value)}
              helperText="Portions / Day"
              required
            />

            <Input
              label="Blast Chiller Storage"
              type="number"
              value={coldStorageKg}
              onChange={(e) => setColdStorageKg(e.target.value)}
              helperText="kg chilled capacity"
              required
            />

            <Select
              label="HACCP Rapid Cooling Method"
              defaultValue="blast_chiller"
              options={[
                { value: 'blast_chiller', label: 'Industrial Blast Chiller (<90 min)' },
                { value: 'ice_bath', label: 'Ice Bath & Stir Wand Protocol' },
                { value: 'shallow_pan', label: 'Shallow Pan Chilled Walk-In' },
              ]}
            />
          </div>
        </div>

        {/* Step 3: Redirection Preferences */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center space-x-2 text-amber-400">
            <ThermometerSnowflake className="w-4 h-4" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Redistribution SLA & Safety Protocol</h2>
          </div>

          <div className="space-y-3 text-xs">
            <label className="flex items-start space-x-3 text-slate-300 p-3 rounded-xl bg-slate-900 border border-white/5">
              <input type="checkbox" defaultChecked className="mt-0.5 rounded text-emerald-500 focus:ring-emerald-500" />
              <div>
                <span className="font-bold text-white">Enable Automated OR-Tools Dispatch</span>
                <p className="text-slate-400 text-[11px]">Surplus logged with &gt;2 hours shelf life will automatically trigger nearest verified recipient notification.</p>
              </div>
            </label>

            <label className="flex items-start space-x-3 text-slate-300 p-3 rounded-xl bg-slate-900 border border-white/5">
              <input type="checkbox" defaultChecked className="mt-0.5 rounded text-emerald-500 focus:ring-emerald-500" />
              <div>
                <span className="font-bold text-white">Enforce Bill Emerson Good Samaritan Act Shield</span>
                <p className="text-slate-400 text-[11px]">Generate tamper-evident digital bill of lading with HACCP temperature timestamp before courier release.</p>
              </div>
            </label>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3">
          <Button
            type="button"
            variant="ghost"
            onClick={() => onNavigate('kitchen_dashboard')}
          >
            Skip for Now
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={loading}
            rightIcon={<CheckCircle className="w-4 h-4" />}
          >
            Save & Enter Operations Hub
          </Button>
        </div>
      </form>
    </div>
  );
};
