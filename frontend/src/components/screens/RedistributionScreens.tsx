'use client';

import React, { useState } from 'react';
import { 
  Share2, 
  HeartHandshake, 
  FileText, 
  Truck, 
  QrCode, 
  MapPin, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Thermometer, 
  ShieldCheck, 
  ArrowRight, 
  PlusCircle, 
  Search, 
  Filter,
  UserCheck,
  PhoneCall,
  Check,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { Modal } from '@/components/design-system/Modal';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  MOCK_RECIPIENTS, 
  MOCK_DONATION_MANIFEST, 
  MOCK_DRIVER_WAYPOINTS,
  RecipientMatch,
  DonationManifest
} from '@/lib/mockData';
import { QrCustodyScreen } from './QrCustodyScreen';

interface RedistributionProps {
  onNavigate: (screen: ScreenId) => void;
  onOpenDonateModal: () => void;
  onShowSuccess: (msg: string) => void;
}

// -------------------------------------------------------------
// 1. SURPLUS MARKETPLACE / LIVE SURPLUS DASHBOARD (PHASE 8)
// -------------------------------------------------------------
export { LiveSurplusDashboardScreen as SurplusMarketplaceScreen } from './LiveSurplusDashboardScreen';
export { LiveSurplusDashboardScreen } from './LiveSurplusDashboardScreen';

const _DeprecatedSurplusMarketplaceScreen: React.FC<RedistributionProps> = ({
  onNavigate,
  onOpenDonateModal,
  onShowSuccess,
}) => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [claimModalOpen, setClaimModalOpen] = useState(false);
  const [activeItem, setActiveItem] = useState<any>(null);
  const [claimedPortions, setClaimedPortions] = useState(50);

  const [listings, setListings] = useState([
    {
      id: 'lst-1',
      title: 'Mediterranean Lemon Herb Grilled Chicken',
      donor: 'Grand Hyatt Culinary Center',
      category: 'Cooked Meals',
      quantityKg: 42.5,
      portions: 85,
      temp: 'Chilled (3.2°C)',
      timeLeft: '3h 15m',
      address: '345 Stockton St, SF',
      dietary: ['Halal Compliant', 'High Protein'],
      status: 'available',
    },
    {
      id: 'lst-2',
      title: 'Artisan Brioche & Sourdough Loaves',
      donor: 'Golden Crust Boulangerie',
      category: 'Bakery',
      quantityKg: 28.0,
      portions: 60,
      temp: 'Dry Ambient (19°C)',
      timeLeft: '5h 45m',
      address: '120 Market St, SF',
      dietary: ['Vegetarian'],
      status: 'available',
    },
    {
      id: 'lst-3',
      title: 'Organic Whole Milk & Natural Yogurt',
      donor: 'Meadow Gold Dairy Depot',
      category: 'Dairy',
      quantityKg: 35.0,
      portions: 70,
      temp: 'Chilled (2.8°C)',
      timeLeft: '18h 00m',
      address: '450 Mission Bay Blvd',
      dietary: ['Gluten-Free', 'Vegetarian'],
      status: 'available',
    },
    {
      id: 'lst-4',
      title: 'Fresh Heirloom Tomatoes & Cucumbers',
      donor: 'Valley Fresh Agri Hub',
      category: 'Produce',
      quantityKg: 95.0,
      portions: 190,
      temp: 'Chilled (5.0°C)',
      timeLeft: '24h 00m',
      address: '780 Industrial Pkwy',
      dietary: ['Vegan', 'Organic'],
      status: 'available',
    },
  ]);

  const handleOpenClaim = (item: any) => {
    setActiveItem(item);
    setClaimedPortions(item.portions);
    setClaimModalOpen(true);
  };

  const handleConfirmClaim = () => {
    setListings((prev) =>
      prev.map((l) => (l.id === activeItem.id ? { ...l, status: 'reserved' } : l))
    );
    setClaimModalOpen(false);
    onShowSuccess(`Claimed ${claimedPortions} portions of ${activeItem.title}! Cold chain courier assigned.`);
  };

  const filtered = listings.filter((l) => {
    const matchesCat = selectedCategory === 'All' || l.category === selectedCategory;
    const matchesSearch = l.title.toLowerCase().includes(search.toLowerCase()) || l.donor.toLowerCase().includes(search.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="emerald" size="sm">Live Rescue Network</Badge>
            <span className="text-xs text-slate-400">FDA 4-Hour Time Control Verified</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Surplus Food Marketplace</h1>
          <p className="text-xs text-slate-400">Available food donations broadcasted to registered regional food banks and shelters</p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={onOpenDonateModal}
          leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
        >
          Post Surplus Donation
        </Button>
      </div>

      {/* Category Pills & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-panel p-4 rounded-2xl border border-white/10">
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 sm:pb-0">
          {['All', 'Cooked Meals', 'Bakery', 'Dairy', 'Produce'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search donations by dish or donor..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
          />
        </div>
      </div>

      {/* Listings Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {filtered.map((item) => (
          <div
            key={item.id}
            className={`glass-panel p-6 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
              item.status === 'reserved'
                ? 'border-emerald-500/40 bg-emerald-950/10 opacity-75'
                : 'border-white/10 hover:border-emerald-500/30'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="purple" size="sm">{item.category}</Badge>
                  <h3 className="text-base font-bold text-white mt-1.5">{item.title}</h3>
                  <p className="text-xs text-slate-400 flex items-center space-x-1 mt-0.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    <span>{item.donor} &bull; {item.address}</span>
                  </p>
                </div>

                <Badge variant={item.status === 'reserved' ? 'neutral' : 'warning'} size="sm">
                  <Clock className="w-3 h-3 mr-1" />
                  {item.status === 'reserved' ? 'Reserved' : item.timeLeft}
                </Badge>
              </div>

              {/* Specs */}
              <div className="grid grid-cols-3 gap-2 p-3 rounded-xl bg-slate-950/60 border border-white/5 text-xs text-center">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Weight</span>
                  <span className="font-bold text-white font-mono">{item.quantityKg} kg</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Portions</span>
                  <span className="font-bold text-emerald-400 font-mono">{item.portions}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Temp Target</span>
                  <span className="font-bold text-cyan-400 font-mono text-[11px] truncate block">{item.temp}</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {item.dietary.map((d: string) => (
                  <span key={d} className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-medium">
                    {d}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-white/5 flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('donation_details')}
              >
                Inspect Manifest
              </Button>

              <Button
                variant={item.status === 'reserved' ? 'ghost' : 'primary'}
                size="sm"
                disabled={item.status === 'reserved'}
                onClick={() => handleOpenClaim(item)}
              >
                {item.status === 'reserved' ? 'Courier Dispatched' : 'Claim Donation'}
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Claim Modal */}
      {activeItem && (
        <Modal
          isOpen={claimModalOpen}
          onClose={() => setClaimModalOpen(false)}
          title={`Claim Food Rescue: ${activeItem.title}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>Available Portions:</span>
                <span className="font-bold text-white">{activeItem.portions} meals ({activeItem.quantityKg} kg)</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>HACCP Temp Check:</span>
                <span className="font-bold text-emerald-400">{activeItem.temp}</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="font-bold text-white">How many portions will your facility intake?</label>
              <input
                type="range"
                min="10"
                max={activeItem.portions}
                step="5"
                value={claimedPortions}
                onChange={(e) => setClaimedPortions(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
              <div className="flex justify-between text-slate-400 font-mono text-[11px]">
                <span>10 portions</span>
                <span className="text-emerald-400 font-bold">{claimedPortions} portions</span>
                <span>{activeItem.portions} portions (All)</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-indigo-300 text-[11px]">
              Upon confirmation, Google OR-Tools will dynamically schedule the nearest refrigerated courier driver to pick up the shipment and deliver to your address.
            </div>

            <div className="flex justify-end space-x-3 pt-3">
              <Button variant="ghost" onClick={() => setClaimModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleConfirmClaim}>
                Confirm Rescue Claim
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

// -------------------------------------------------------------
// 2. RECIPIENT MATCHING SCREEN (AI Bipartite Matcher)
// -------------------------------------------------------------
export const RecipientMatchingScreen: React.FC<RedistributionProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [recipients, setRecipients] = useState<RecipientMatch[]>(MOCK_RECIPIENTS);

  const handleConfirmMatch = (id: string, name: string) => {
    setRecipients((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'Assigned' } : r))
    );
    onShowSuccess(`Confirmed match with ${name}. Automated pickup manifest generated.`);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">Bipartite Matching Engine</Badge>
            <span className="text-xs text-slate-400">OR-Tools Affinity Optimization</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Recipient Compatibility Matching</h1>
          <p className="text-xs text-slate-400">
            Multi-attribute matching algorithm evaluating distance, cold-chain capacity, dietary requirements, and past intake velocity
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {recipients.map((rec) => (
          <div
            key={rec.id}
            className={`glass-panel p-6 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
              rec.status === 'Assigned'
                ? 'border-emerald-500/40 bg-emerald-950/15'
                : 'border-white/10 hover:border-white/20'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="neutral" size="sm">{rec.facilityType}</Badge>
                  <h3 className="text-base font-bold text-white mt-1.5">{rec.recipientOrg}</h3>
                </div>

                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Affinity</span>
                  <span className="text-lg font-black text-emerald-400 font-mono">
                    {rec.affinityScorePct}%
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-xs text-slate-300 p-3 rounded-xl bg-slate-950/60 border border-white/5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Distance & ETA:</span>
                  <span className="font-bold text-white">{rec.distanceKm} km ({rec.transitTimeMins} mins)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Intake Capacity:</span>
                  <span className="font-bold text-white">{rec.demandCapacityKg} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Walk-in Chiller:</span>
                  <span className={`font-bold ${rec.coldStorageAvailable ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {rec.coldStorageAvailable ? 'Certified Active' : 'Ambient Only'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Contact:</span>
                  <span className="text-slate-300">{rec.contactPerson}</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-white/5 flex items-center justify-between">
              <Badge variant={rec.status === 'Assigned' ? 'success' : 'warning'} size="sm">
                {rec.status}
              </Badge>

              <Button
                variant={rec.status === 'Assigned' ? 'ghost' : 'primary'}
                size="sm"
                disabled={rec.status === 'Assigned'}
                onClick={() => handleConfirmMatch(rec.id, rec.recipientOrg)}
              >
                {rec.status === 'Assigned' ? 'Match Confirmed' : 'Assign to Courier'}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// -------------------------------------------------------------
// 3. DONATION DETAILS SCREEN (Digital Bill of Lading & Manifest)
// -------------------------------------------------------------
export const DonationDetailsScreen: React.FC<RedistributionProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const manifest = MOCK_DONATION_MANIFEST;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">Digital Bill of Lading</Badge>
            <span className="text-xs font-mono text-slate-400">{manifest.manifestId}</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Donation Manifest & Chain of Custody</h1>
          <p className="text-xs text-slate-400">Immutable cold chain provenance record under the Bill Emerson Good Samaritan Act</p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigate('map_logistics')}
            leftIcon={<Truck className="w-3.5 h-3.5" />}
          >
            Track Route
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigate('qr_verification')}
            leftIcon={<QrCode className="w-3.5 h-3.5" />}
          >
            Digital Handover QR
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Manifest Specs */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Shipment Specifications</CardTitle>
              <CardDescription>Verified batch payload and transport constraints</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Donor Facility</span>
                  <div className="font-bold text-white">{manifest.donorOrg}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Recipient Entity</span>
                  <div className="font-bold text-white">{manifest.recipientOrg}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Payload Weight</span>
                  <div className="font-bold text-emerald-400 font-mono">{manifest.totalWeightKg} kg ({manifest.mealPortions} portions)</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Transit Temperature</span>
                  <div className="font-bold text-cyan-400 font-mono">{manifest.transitTemperatureC}°C (Target: &lt;4.0°C)</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Courier Driver</span>
                  <div className="font-bold text-white">{manifest.courierDriver}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Vehicle Plate</span>
                  <div className="font-bold text-white font-mono">{manifest.vehiclePlate}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Chain of Custody Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Chain of Custody Event Ledger</CardTitle>
              <CardDescription>Cryptographically sealed handover events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { title: 'Surplus Declared & Blast Chilled', time: '11:15 AM', actor: 'Executive Chef Vance', status: 'completed' },
                  { title: 'Courier Loading Inspection Passed (3.2°C)', time: '11:45 AM', actor: 'Courier Alex Mercer', status: 'completed' },
                  { title: 'Refrigerated Vehicle En Route', time: '11:55 AM', actor: 'EV Van #3 Live GPS', status: 'active' },
                  { title: 'Recipient Shelter Receiving & Temperature Scan', time: 'Est. 12:15 PM', actor: 'St. Jude Food Bank Officer', status: 'pending' },
                ].map((step, idx) => (
                  <div key={idx} className="flex items-start space-x-3 text-xs">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                      step.status === 'completed' ? 'bg-emerald-500 text-slate-950 font-bold' :
                      step.status === 'active' ? 'bg-indigo-500 text-white animate-pulse' : 'bg-slate-800 text-slate-500'
                    }`}>
                      {step.status === 'completed' ? '✓' : idx + 1}
                    </div>
                    <div className="flex-1 pb-3 border-b border-white/5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">{step.title}</span>
                        <span className="text-[10px] text-slate-400 font-mono">{step.time}</span>
                      </div>
                      <span className="text-[11px] text-slate-400">{step.actor}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Legal Signatures Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Digital Signatures</CardTitle>
              <CardDescription>HMAC-SHA256 authenticated</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white">Donor Release</span>
                  <Badge variant="success" size="sm">Signed</Badge>
                </div>
                <p className="text-[10px] text-slate-400">Marcus Vance &bull; 11:46 AM</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white">Courier Intake</span>
                  <Badge variant="success" size="sm">Signed</Badge>
                </div>
                <p className="text-[10px] text-slate-400">Alex Mercer &bull; 11:47 AM</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white">Recipient Verification</span>
                  <Badge variant="warning" size="sm">Awaiting Handover</Badge>
                </div>
                <p className="text-[10px] text-slate-400">Pending arrival at 812 Mission Blvd</p>
              </div>

              <Button
                variant="primary"
                className="w-full"
                size="sm"
                onClick={() => onNavigate('qr_verification')}
              >
                Scan Handover QR
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// -------------------------------------------------------------
// 4. MAP & LOGISTICS SCREEN (Phase 10 Fleet Routing & Courier Console)
// -------------------------------------------------------------
import { DriverDashboardScreen } from './DriverDashboardScreen';

export const MapLogisticsScreen: React.FC<RedistributionProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  return <DriverDashboardScreen onNavigate={onNavigate} onShowSuccess={onShowSuccess} />;
};


// -------------------------------------------------------------
// 5. QR VERIFICATION SCREEN (Dynamic HMAC Handover Token)
// -------------------------------------------------------------
export const QrVerificationScreen: React.FC<RedistributionProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  return <QrCustodyScreen onNavigate={onNavigate} onShowSuccess={onShowSuccess} />;
};
