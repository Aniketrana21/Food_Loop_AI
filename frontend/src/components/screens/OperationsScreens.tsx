'use client';

import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Search, 
  PlusCircle, 
  Calendar, 
  Utensils, 
  Trash2, 
  Users, 
  AlertTriangle, 
  CheckCircle2, 
  Thermometer, 
  Clock, 
  Filter, 
  DollarSign, 
  Leaf, 
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Layers,
  FileSpreadsheet,
  Sparkles,
  Building2,
  ChefHat,
  RefreshCw,
  ShoppingBag,
  ArrowUpRight,
  ArrowDownRight,
  Send,
  Image as ImageIcon,
  History,
  Check,
  ShieldCheck,
  Percent
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Input, Select } from '@/components/design-system/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { Modal } from '@/components/design-system/Modal';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  KitchenProfile,
  KitchenStaffMember,
  InventoryItemLot,
  PurchaseRecord,
  IngredientCatalogItem,
  MenuRecord,
  ProductionBatchRecord,
  ConsumptionRecordItem,
  WasteRecordItem,
  WasteAnalytics,
  InventoryTransactionType,
  WasteCategory
} from '@/types';
import {
  fetchKitchenProfile,
  updateKitchenProfile,
  fetchKitchenStaff,
  addKitchenStaff,
  fetchInventoryItems,
  createInventoryLot,
  recordPurchaseOrder,
  fetchPurchaseHistory,
  adjustInventoryStock,
  fetchIngredientsCatalog,
  createCatalogIngredient,
  fetchMenus,
  createMenu,
  fetchProductionBatches,
  createProductionBatch,
  completeProductionBatch,
  fetchConsumptionRecords,
  recordConsumption,
  routeConsumptionLeftover,
  fetchWasteRecords,
  logWasteRecord,
  fetchWasteAnalytics
} from '@/lib/api';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Cell, 
  PieChart, 
  Pie, 
  AreaChart, 
  Area 
} from 'recharts';

interface OperationsProps {
  onNavigate: (screen: ScreenId) => void;
  onOpenDonateModal: () => void;
  onShowSuccess: (msg: string) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  OVERPRODUCTION: '#f59e0b',
  PLATE_WASTE: '#ef4444',
  SPOILAGE: '#8b5cf6',
  EXPIRED: '#ec4899',
  PREPARATION_WASTE: '#10b981',
  DAMAGED: '#64748b',
  QUALITY_REJECTION: '#06b6d4',
  OTHER: '#3b82f6',
};

// =============================================================
// 1. KITCHEN PROFILE & STAFF SCREEN
// =============================================================
export const KitchenProfileStaffScreen: React.FC<OperationsProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [profile, setProfile] = useState<KitchenProfile | null>(null);
  const [staff, setStaff] = useState<KitchenStaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAddStaffModalOpen, setIsAddStaffModalOpen] = useState(false);

  // Edit Profile Form State
  const [editForm, setEditForm] = useState({
    name: '',
    facility_type: 'HOSPITALITY_HOTEL',
    daily_meal_capacity: 1000,
    contact_email: '',
    contact_phone: '',
    operating_hours: '',
    status: 'ACTIVE',
  });

  // Add Staff Form State
  const [staffForm, setStaffForm] = useState({
    name: '',
    email: '',
    role: 'KITCHEN_MANAGER',
    department: 'Main Culinary Range',
    shift: 'Morning Prep (06:00 - 14:00)',
    phone: '',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const p = await fetchKitchenProfile();
      setProfile(p);
      if (p) {
        setEditForm({
          name: p.name,
          facility_type: p.facility_type,
          daily_meal_capacity: p.daily_meal_capacity,
          contact_email: p.contact_email || '',
          contact_phone: p.contact_phone || '',
          operating_hours: p.operating_hours || '',
          status: p.status || 'ACTIVE',
        });
        const stf = await fetchKitchenStaff(p.id);
        setStaff(stf);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      const updated = await updateKitchenProfile(profile.id, editForm);
      setProfile(updated);
      setIsEditModalOpen(false);
      onShowSuccess('Kitchen facility profile updated successfully.');
    } catch (err: any) {
      alert(err.message || 'Failed to update kitchen profile');
    }
  };

  const handleAddStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      const newMember = await addKitchenStaff(profile.id, staffForm);
      setStaff([...staff, newMember]);
      setIsAddStaffModalOpen(false);
      setStaffForm({
        name: '',
        email: '',
        role: 'KITCHEN_MANAGER',
        department: 'Main Culinary Range',
        shift: 'Morning Prep (06:00 - 14:00)',
        phone: '',
      });
      onShowSuccess(`Staff member ${newMember.name} assigned to kitchen operations.`);
    } catch (err: any) {
      alert(err.message || 'Failed to add staff member');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">Institutional Facility</Badge>
            <span className="text-xs text-slate-400">HACCP Station Controls</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Kitchen Profile & Personnel</h1>
          <p className="text-xs text-slate-400">Institutional facility specifications, operating shifts, and certified culinary staff</p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsEditModalOpen(true)}
            leftIcon={<Building2 className="w-3.5 h-3.5" />}
          >
            Edit Profile
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddStaffModalOpen(true)}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Add Staff Member
          </Button>
        </div>
      </div>

      {/* Facility Overview Card */}
      {profile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl text-white">{profile.name}</CardTitle>
                  <CardDescription>Facility Type: {profile.facility_type.replace('_', ' ')}</CardDescription>
                </div>
                <Badge variant={profile.status === 'ACTIVE' ? 'success' : 'neutral'} size="sm">
                  {profile.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-3 rounded-2xl bg-slate-950 border border-white/5 space-y-1">
                  <span className="text-slate-400 uppercase text-[10px] font-bold">Daily Capacity</span>
                  <div className="text-xl font-black text-white">{profile.daily_meal_capacity}</div>
                  <span className="text-[10px] text-slate-400">Meals per cycle</span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950 border border-white/5 space-y-1">
                  <span className="text-slate-400 uppercase text-[10px] font-bold">Operating Hours</span>
                  <div className="text-sm font-bold text-white mt-1">{profile.operating_hours || '05:00 - 23:00'}</div>
                  <span className="text-[10px] text-slate-400">Continuous Service</span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950 border border-white/5 space-y-1">
                  <span className="text-slate-400 uppercase text-[10px] font-bold">Contact Email</span>
                  <div className="text-xs font-semibold text-emerald-400 truncate mt-1">{profile.contact_email || 'culinary@foodloop.ai'}</div>
                  <span className="text-[10px] text-slate-400">Dispatch Desk</span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950 border border-white/5 space-y-1">
                  <span className="text-slate-400 uppercase text-[10px] font-bold">Contact Phone</span>
                  <div className="text-xs font-semibold text-white mt-1">{profile.contact_phone || '+1-555-432-1099'}</div>
                  <span className="text-[10px] text-slate-400">Emergency Lead</span>
                </div>
              </div>

              {/* Certifications Ribbon */}
              <div className="pt-2">
                <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-2">Food Safety & Compliance Certifications</div>
                <div className="flex flex-wrap gap-2">
                  {(profile.certifications || ['HACCP Certified', 'ISO 22000', 'ServSafe Lead Kitchen', 'Zero-Landfill Gold']).map((cert, idx) => (
                    <span key={idx} className="flex items-center space-x-1.5 px-3 py-1 rounded-xl bg-emerald-950/40 text-emerald-300 border border-emerald-500/20 text-xs font-medium">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{cert}</span>
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats / Compliance */}
          <Card>
            <CardHeader>
              <CardTitle>Kitchen Operations State</CardTitle>
              <CardDescription>Real-time audit telemetry</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-white/5 text-xs">
                <span className="text-slate-400">Active Staff Roster:</span>
                <span className="font-bold text-white font-mono">{staff.length} Verified</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-white/5 text-xs">
                <span className="text-slate-400">HACCP Temperature Log:</span>
                <span className="font-bold text-emerald-400 font-mono">100% Compliant</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-white/5 text-xs">
                <span className="text-slate-400">Surplus Routing Protocol:</span>
                <span className="font-bold text-purple-400">Active (FoodLoop AI)</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-2"
                onClick={() => onNavigate('inventory')}
              >
                Go to Active Inventory &rarr;
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Staff Personnel Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Kitchen Staff Roster</CardTitle>
              <CardDescription>Roles, assigned stations, and operational shift coverage</CardDescription>
            </div>
            <span className="text-xs text-slate-400 font-mono">{staff.length} Active Staff</span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Staff Member</th>
                  <th className="py-3 px-4">Role & Permissions</th>
                  <th className="py-3 px-4">Department / Station</th>
                  <th className="py-3 px-4">Assigned Shift</th>
                  <th className="py-3 px-4">Contact Phone</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {staff.map((m) => (
                  <tr key={m.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white flex items-center space-x-2">
                        <ChefHat className="w-3.5 h-3.5 text-emerald-400" />
                        <span>{m.name}</span>
                      </div>
                      <div className="text-[10px] text-slate-400">{m.email}</div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="purple" size="sm">{m.role.replace('_', ' ')}</Badge>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-200">{m.department || 'Culinary Range'}</td>
                    <td className="py-3 px-4 text-slate-400">{m.shift || 'Standard'}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{m.phone || '+1-555-0199'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Edit Profile Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Institutional Kitchen Profile"
      >
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <Input
            label="Kitchen Facility Name"
            value={editForm.name}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Facility Type"
              value={editForm.facility_type}
              onChange={(e) => setEditForm({ ...editForm, facility_type: e.target.value })}
              options={[
                { value: 'HOSPITALITY_HOTEL', label: 'Hospitality & Hotel' },
                { value: 'CORPORATE_DINING', label: 'Corporate Cafeteria' },
                { value: 'UNIVERSITY_CAMPUS', label: 'University / Education' },
                { value: 'HEALTHCARE_HOSPITAL', label: 'Healthcare & Hospital' },
                { value: 'BANQUET_COMMISSARY', label: 'Central Commissary / Catering' },
              ]}
            />
            <Input
              label="Daily Meal Capacity"
              type="number"
              value={editForm.daily_meal_capacity}
              onChange={(e) => setEditForm({ ...editForm, daily_meal_capacity: Number(e.target.value) })}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Contact Email"
              type="email"
              value={editForm.contact_email}
              onChange={(e) => setEditForm({ ...editForm, contact_email: e.target.value })}
            />
            <Input
              label="Contact Phone"
              value={editForm.contact_phone}
              onChange={(e) => setEditForm({ ...editForm, contact_phone: e.target.value })}
            />
          </div>
          <Input
            label="Operating Hours"
            value={editForm.operating_hours}
            onChange={(e) => setEditForm({ ...editForm, operating_hours: e.target.value })}
            placeholder="e.g. 05:00 - 23:00 Daily"
          />
          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Profile
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Staff Modal */}
      <Modal
        isOpen={isAddStaffModalOpen}
        onClose={() => setIsAddStaffModalOpen(false)}
        title="Add Staff Member to Kitchen Team"
      >
        <form onSubmit={handleAddStaff} className="space-y-4">
          <Input
            label="Full Name"
            value={staffForm.name}
            onChange={(e) => setStaffForm({ ...staffForm, name: e.target.value })}
            placeholder="e.g. Chef Marcus Vance"
            required
          />
          <Input
            label="Work Email"
            type="email"
            value={staffForm.email}
            onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })}
            placeholder="e.g. marcus@grandhotel.com"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Operational Role"
              value={staffForm.role}
              onChange={(e) => setStaffForm({ ...staffForm, role: e.target.value })}
              options={[
                { value: 'KITCHEN_MANAGER', label: 'Kitchen Manager / Exec Chef' },
                { value: 'ADMIN', label: 'Admin / Culinary Director' },
                { value: 'AUDITOR', label: 'Safety & HACCP Auditor' },
              ]}
            />
            <Input
              label="Department / Station"
              value={staffForm.department}
              onChange={(e) => setStaffForm({ ...staffForm, department: e.target.value })}
              placeholder="e.g. Cold Larder & HACCP"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Shift Schedule"
              value={staffForm.shift}
              onChange={(e) => setStaffForm({ ...staffForm, shift: e.target.value })}
              placeholder="e.g. Morning 06:00 - 14:00"
            />
            <Input
              label="Phone Number"
              value={staffForm.phone}
              onChange={(e) => setStaffForm({ ...staffForm, phone: e.target.value })}
              placeholder="+1-555-0199"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsAddStaffModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Assign Staff Member
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// =============================================================
// 2. INVENTORY SCREEN (All 7 Transaction Types + Purchase Records)
// =============================================================
export const InventoryScreen: React.FC<OperationsProps> = ({
  onNavigate,
  onOpenDonateModal,
  onShowSuccess,
}) => {
  const [inventory, setInventory] = useState<InventoryItemLot[]>([]);
  const [purchaseHistory, setPurchaseHistory] = useState<PurchaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [storageFilter, setStorageFilter] = useState('All');

  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);
  const [selectedLotForAdjust, setSelectedLotForAdjust] = useState<InventoryItemLot | null>(null);

  // New Single Item State
  const [newItem, setNewItem] = useState({
    ingredient_name: '',
    category: 'Produce',
    quantity: 50,
    unit: 'kg',
    batch_number: 'LOT-2026-PO-01',
    purchase_date: new Date().toISOString().split('T')[0],
    expiry_date: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0],
    storage_type: 'REFRIGERATED',
    supplier: 'Fresh Valley Produce',
    cost_per_unit: 3.50,
    reorder_level: 15,
  });

  // Purchase Order Form State
  const [poForm, setPoForm] = useState({
    supplier: 'Sysco Metro Supply Hub',
    invoice_number: `INV-PO-${Date.now().toString().slice(-6)}`,
    purchase_date: new Date().toISOString().split('T')[0],
    items: [
      {
        ingredient_name: 'Organic Romanesco Broccoli',
        category: 'Produce',
        quantity: 60,
        unit: 'kg',
        cost_per_unit: 3.20,
        batch_number: `LOT-${Math.floor(Math.random() * 8999 + 1000)}`,
        expiry_date: new Date(Date.now() + 8 * 86400000).toISOString().split('T')[0],
        storage_type: 'REFRIGERATED',
      },
      {
        ingredient_name: 'Heavy Cream 36% Grade A',
        category: 'Dairy & Eggs',
        quantity: 40,
        unit: 'liters',
        cost_per_unit: 4.10,
        batch_number: `LOT-${Math.floor(Math.random() * 8999 + 1000)}`,
        expiry_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
        storage_type: 'REFRIGERATED',
      }
    ]
  });

  // Stock Adjustment Form State (Supports all 7 types)
  const [adjustForm, setAdjustForm] = useState<{
    adjustment_quantity: number;
    reason: string;
    transaction_type: InventoryTransactionType;
    unit_cost?: number;
    notes?: string;
  }>({
    adjustment_quantity: 5,
    reason: 'Routine prep cycle usage',
    transaction_type: 'CONSUMPTION',
    unit_cost: 0,
    notes: 'Approved by station sous chef'
  });

  const loadInventory = async () => {
    setLoading(true);
    try {
      const items = await fetchInventoryItems();
      setInventory(items);
      const history = await fetchPurchaseHistory();
      setPurchaseHistory(history);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, []);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createInventoryLot(newItem);
      setInventory([created, ...inventory]);
      setIsAddModalOpen(false);
      onShowSuccess(`Added lot ${created.batch_number} (${created.ingredient_name}) to stock.`);
    } catch (err: any) {
      alert(err.message || 'Failed to add stock lot');
    }
  };

  const handleRecordPurchaseOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const recorded = await recordPurchaseOrder({
        kitchen_id: inventory[0]?.kitchen_id || '11111111-1111-1111-1111-111111111111',
        supplier: poForm.supplier,
        invoice_number: poForm.invoice_number,
        purchase_date: poForm.purchase_date,
        items: poForm.items
      });
      setIsPurchaseModalOpen(false);
      onShowSuccess(`Purchase Order ${recorded.invoice_number} recorded. Total: $${recorded.total_cost_usd}.`);
      loadInventory();
    } catch (err: any) {
      alert(err.message || 'Failed to submit purchase order');
    }
  };

  const handleAdjustStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLotForAdjust) return;
    try {
      const res = await adjustInventoryStock(selectedLotForAdjust.id, adjustForm);
      setIsAdjustModalOpen(false);
      onShowSuccess(`${adjustForm.transaction_type} logged. Updated stock: ${res.new_quantity} ${selectedLotForAdjust.unit}.`);
      loadInventory();
    } catch (err: any) {
      alert(err.message || 'Failed to adjust stock');
    }
  };

  const openAdjustModal = (lot: InventoryItemLot) => {
    setSelectedLotForAdjust(lot);
    setAdjustForm({
      adjustment_quantity: 5,
      reason: 'Routine culinary cycle',
      transaction_type: 'CONSUMPTION',
      unit_cost: lot.cost_per_unit,
      notes: ''
    });
    setIsAdjustModalOpen(true);
  };

  const filtered = inventory.filter((item) => {
    const matchesSearch = 
      item.ingredient_name.toLowerCase().includes(search.toLowerCase()) || 
      item.batch_number.toLowerCase().includes(search.toLowerCase()) ||
      (item.supplier && item.supplier.toLowerCase().includes(search.toLowerCase()));
    const matchesCat = categoryFilter === 'All' || item.category === categoryFilter;
    const matchesStorage = storageFilter === 'All' || item.storage_type === storageFilter;
    return matchesSearch && matchesCat && matchesStorage;
  });

  const totalValuation = inventory.reduce((acc, curr) => acc + (curr.quantity * curr.cost_per_unit), 0);
  const lowStockCount = inventory.filter(i => i.status === 'LOW_STOCK' || (i.reorder_level && i.quantity <= i.reorder_level)).length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">HACCP Cold Chain Tracking</Badge>
            <span className="text-xs text-slate-400">Total Valuation: ${totalValuation.toFixed(2)}</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Culinary Inventory & Stock</h1>
          <p className="text-xs text-slate-400">Continuous lot tracking, FIFO expiration surveillance, and multi-transaction audit logs</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadInventory}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsHistoryModalOpen(true)}
            leftIcon={<History className="w-3.5 h-3.5" />}
          >
            Purchase History ({purchaseHistory.length})
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsPurchaseModalOpen(true)}
            leftIcon={<ShoppingBag className="w-3.5 h-3.5" />}
          >
            PO Intake
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Add New Lot
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-white/10">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Tracked Inventory Lots</div>
          <div className="text-2xl font-black text-white mt-1">{inventory.length}</div>
          <span className="text-[10px] text-emerald-400 font-medium">100% Real-time Database</span>
        </div>
        <div className="glass-panel p-4 rounded-2xl border border-white/10">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Total Stock Valuation</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">${totalValuation.toFixed(2)}</div>
          <span className="text-[10px] text-slate-400">Current market asset value</span>
        </div>
        <div className="glass-panel p-4 rounded-2xl border border-white/10">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Low Stock Triggers</div>
          <div className="text-2xl font-black text-amber-400 mt-1">{lowStockCount}</div>
          <span className="text-[10px] text-amber-400/80 font-medium">Requires supplier replenishment</span>
        </div>
        <div className="glass-panel p-4 rounded-2xl border border-white/10">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Supported Transactions</div>
          <div className="text-2xl font-black text-purple-400 mt-1">7 Types</div>
          <span className="text-[10px] text-slate-400">PURCHASE, WASTE, DONATE...</span>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 glass-panel p-4 rounded-2xl border border-white/10">
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 lg:pb-0">
          {['All', 'Produce', 'Dairy & Eggs', 'Meat & Poultry', 'Bakery', 'Dry Goods & Grains'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                categoryFilter === cat
                  ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={storageFilter}
            onChange={(e) => setStorageFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
          >
            <option value="All">All Storage Types</option>
            <option value="REFRIGERATED">Refrigerated (0-4°C)</option>
            <option value="FROZEN">Frozen (-18°C)</option>
            <option value="DRY">Dry Ambient (15-22°C)</option>
            <option value="WARM_HOLDING">Warm Holding (60°C+)</option>
          </select>

          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search ingredient, lot, supplier..."
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
            />
          </div>
        </div>
      </div>

      {/* Inventory Lots Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Ingredient & Lot Batch</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Quantity On Hand</th>
                  <th className="py-3 px-4">Storage Type</th>
                  <th className="py-3 px-4">Purchase & Expiry</th>
                  <th className="py-3 px-4">Supplier & Cost</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Inventory Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filtered.map((item) => {
                  const expiryDays = item.expiry_date ? Math.ceil((new Date(item.expiry_date).getTime() - Date.now()) / (1000 * 3600 * 24)) : null;
                  return (
                    <tr key={item.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-white">{item.ingredient_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          Batch: {item.batch_number}
                        </div>
                      </td>
                      <td className="py-3 px-4">{item.category || 'Pantry'}</td>
                      <td className="py-3 px-4 font-mono">
                        <span className="font-bold text-white text-sm">{item.quantity}</span> {item.unit}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/20">
                          {item.storage_type}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-white font-medium">{item.expiry_date || 'N/A'}</div>
                        {expiryDays !== null && (
                          <div className={`text-[10px] font-bold ${
                            expiryDays <= 1 ? 'text-rose-400' :
                            expiryDays <= 3 ? 'text-amber-400' : 'text-slate-400'
                          }`}>
                            {expiryDays <= 0 ? 'EXPIRED' : `${expiryDays} days remaining`}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-white">{item.supplier || 'Direct'}</div>
                        <div className="text-[10px] text-slate-400 font-mono">${item.cost_per_unit?.toFixed(2)} / {item.unit}</div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            item.status === 'ACTIVE' ? 'success' :
                            item.status === 'LOW_STOCK' ? 'warning' : 'danger'
                          }
                          size="sm"
                        >
                          {item.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => openAdjustModal(item)}
                          >
                            Transact / Adjust
                          </Button>
                          {item.status === 'LOW_STOCK' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setPoForm(prev => ({
                                  ...prev,
                                  items: [{
                                    ingredient_name: item.ingredient_name,
                                    category: item.category || 'Produce',
                                    quantity: 50,
                                    unit: item.unit,
                                    cost_per_unit: item.cost_per_unit || 3.0,
                                    batch_number: `LOT-${Math.floor(Math.random() * 8999 + 1000)}`,
                                    expiry_date: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0],
                                    storage_type: item.storage_type || 'REFRIGERATED',
                                  }]
                                }));
                                setIsPurchaseModalOpen(true);
                              }}
                            >
                              Reorder
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 7-Type Transaction Modal */}
      <Modal
        isOpen={isAdjustModalOpen}
        onClose={() => setIsAdjustModalOpen(false)}
        title={`Execute Inventory Transaction — ${selectedLotForAdjust?.ingredient_name}`}
      >
        {selectedLotForAdjust && (
          <form onSubmit={handleAdjustStock} className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-900 border border-white/10 text-xs flex justify-between items-center">
              <div>
                <span className="text-slate-400">Current Stock: </span>
                <span className="font-bold text-white">{selectedLotForAdjust.quantity} {selectedLotForAdjust.unit}</span>
              </div>
              <div>
                <span className="text-slate-400">Batch: </span>
                <span className="font-mono text-cyan-400">{selectedLotForAdjust.batch_number}</span>
              </div>
            </div>

            <Select
              label="Transaction Type (Required 7 Workflows)"
              value={adjustForm.transaction_type}
              onChange={(e) => setAdjustForm({ ...adjustForm, transaction_type: e.target.value as any })}
              options={[
                { value: 'PURCHASE', label: 'PURCHASE (Stock Intake Receipt)' },
                { value: 'CONSUMPTION', label: 'CONSUMPTION (Meal Service Depletion)' },
                { value: 'PRODUCTION', label: 'PRODUCTION (Issued to Cooking Batch)' },
                { value: 'ADJUSTMENT', label: 'ADJUSTMENT (Audit / Cycle Count Correction)' },
                { value: 'WASTE', label: 'WASTE (Damaged / Spoiled Stock Write-Off)' },
                { value: 'TRANSFER', label: 'TRANSFER (Station / Commissary Transfer)' },
                { value: 'DONATION', label: 'DONATION (Surplus Routed to Rescue)' },
              ]}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Adjustment Quantity"
                type="number"
                step="0.1"
                value={adjustForm.adjustment_quantity}
                onChange={(e) => setAdjustForm({ ...adjustForm, adjustment_quantity: Number(e.target.value) })}
                required
              />
              <Input
                label="Unit Cost ($)"
                type="number"
                step="0.01"
                value={adjustForm.unit_cost || selectedLotForAdjust.cost_per_unit}
                onChange={(e) => setAdjustForm({ ...adjustForm, unit_cost: Number(e.target.value) })}
              />
            </div>

            <Input
              label="Reason for Transaction"
              value={adjustForm.reason}
              onChange={(e) => setAdjustForm({ ...adjustForm, reason: e.target.value })}
              placeholder="e.g. Banquet prep utilization, cycle audit correction"
              required
            />

            <Input
              label="Operational Notes / Approvals"
              value={adjustForm.notes || ''}
              onChange={(e) => setAdjustForm({ ...adjustForm, notes: e.target.value })}
              placeholder="e.g. Authorized by Sous Chef Sarah Chen"
            />

            <div className="flex justify-end space-x-3 pt-3">
              <Button variant="ghost" type="button" onClick={() => setIsAdjustModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Execute {adjustForm.transaction_type}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Add Single Stock Lot Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add New Stock Lot to Inventory"
      >
        <form onSubmit={handleAddItem} className="space-y-4">
          <Input
            label="Ingredient Name"
            value={newItem.ingredient_name}
            onChange={(e) => setNewItem({ ...newItem, ingredient_name: e.target.value })}
            placeholder="e.g. Organic Heavy Cream 36%"
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Category"
              value={newItem.category}
              onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
              options={[
                { value: 'Produce', label: 'Produce' },
                { value: 'Dairy & Eggs', label: 'Dairy & Eggs' },
                { value: 'Meat & Poultry', label: 'Meat & Poultry' },
                { value: 'Dry Goods & Grains', label: 'Dry Goods & Grains' },
                { value: 'Bakery', label: 'Bakery' },
              ]}
            />
            <Input
              label="Batch / Lot Number"
              value={newItem.batch_number}
              onChange={(e) => setNewItem({ ...newItem, batch_number: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Quantity"
              type="number"
              value={newItem.quantity}
              onChange={(e) => setNewItem({ ...newItem, quantity: Number(e.target.value) })}
              required
            />
            <Select
              label="Unit"
              value={newItem.unit}
              onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}
              options={[
                { value: 'kg', label: 'kg' },
                { value: 'liters', label: 'liters' },
                { value: 'units', label: 'units' },
              ]}
            />
            <Input
              label="Cost / Unit ($)"
              type="number"
              step="0.01"
              value={newItem.cost_per_unit}
              onChange={(e) => setNewItem({ ...newItem, cost_per_unit: Number(e.target.value) })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Purchase Date"
              type="date"
              value={newItem.purchase_date}
              onChange={(e) => setNewItem({ ...newItem, purchase_date: e.target.value })}
              required
            />
            <Input
              label="Expiry Date"
              type="date"
              value={newItem.expiry_date}
              onChange={(e) => setNewItem({ ...newItem, expiry_date: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Storage Temperature Profile"
              value={newItem.storage_type}
              onChange={(e) => setNewItem({ ...newItem, storage_type: e.target.value })}
              options={[
                { value: 'REFRIGERATED', label: 'Refrigerated (0-4°C)' },
                { value: 'FROZEN', label: 'Frozen (-18°C)' },
                { value: 'DRY', label: 'Dry Ambient (15-22°C)' },
                { value: 'WARM_HOLDING', label: 'Warm Holding (60°C+)' },
              ]}
            />
            <Input
              label="Supplier"
              value={newItem.supplier}
              onChange={(e) => setNewItem({ ...newItem, supplier: e.target.value })}
              required
            />
          </div>

          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Lot Entry
            </Button>
          </div>
        </form>
      </Modal>

      {/* Purchase Order Intake Modal */}
      <Modal
        isOpen={isPurchaseModalOpen}
        onClose={() => setIsPurchaseModalOpen(false)}
        title="Institutional Purchase Order Intake"
      >
        <form onSubmit={handleRecordPurchaseOrder} className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Supplier"
              value={poForm.supplier}
              onChange={(e) => setPoForm({ ...poForm, supplier: e.target.value })}
              required
            />
            <Input
              label="Invoice / PO #"
              value={poForm.invoice_number}
              onChange={(e) => setPoForm({ ...poForm, invoice_number: e.target.value })}
              required
            />
            <Input
              label="Purchase Date"
              type="date"
              value={poForm.purchase_date}
              onChange={(e) => setPoForm({ ...poForm, purchase_date: e.target.value })}
              required
            />
          </div>

          <div className="space-y-3 pt-2">
            <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
              <span>Order Line Items ({poForm.items.length})</span>
              <span className="text-emerald-400 font-mono">
                Total: ${poForm.items.reduce((s, it) => s + (it.quantity * it.cost_per_unit), 0).toFixed(2)}
              </span>
            </div>

            {poForm.items.map((item, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-white/5 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white">Line #{idx + 1}: {item.ingredient_name}</span>
                  <span className="font-mono text-slate-400">${(item.quantity * item.cost_per_unit).toFixed(2)}</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>Qty: <strong>{item.quantity} {item.unit}</strong></div>
                  <div>Cost: <strong>${item.cost_per_unit}</strong></div>
                  <div>Exp: <strong>{item.expiry_date}</strong></div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsPurchaseModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Commit Purchase Order
            </Button>
          </div>
        </form>
      </Modal>

      {/* Purchase History Modal */}
      <Modal
        isOpen={isHistoryModalOpen}
        onClose={() => setIsHistoryModalOpen(false)}
        title="Historical Purchase Records"
      >
        <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
          {purchaseHistory.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-6">No historical purchase orders recorded yet.</p>
          ) : (
            purchaseHistory.map((po) => (
              <div key={po.id} className="p-3 rounded-xl bg-slate-950 border border-white/5 flex items-center justify-between text-xs">
                <div>
                  <div className="font-bold text-white">{po.invoice_number || 'PO-RECORD'} &bull; {po.supplier}</div>
                  <div className="text-[10px] text-slate-400 font-mono">Date: {po.purchase_date} &bull; {po.items_count} items</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-emerald-400 font-mono text-sm">${po.total_cost_usd?.toFixed(2)}</div>
                  <Badge variant="purple" size="sm">CONFIRMED</Badge>
                </div>
              </div>
            ))
          )}
        </div>
      </Modal>
    </div>
  );
};

// =============================================================
// 3. MENU MANAGEMENT & INGREDIENTS CATALOG SCREEN
// =============================================================
export const MenuManagementScreen: React.FC<OperationsProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [menus, setMenus] = useState<MenuRecord[]>([]);
  const [ingredients, setIngredients] = useState<IngredientCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'menus' | 'catalog'>('menus');
  const [selectedDay, setSelectedDay] = useState('Monday');

  // Modals
  const [isAddMenuModalOpen, setIsAddMenuModalOpen] = useState(false);
  const [isAddIngredientModalOpen, setIsAddIngredientModalOpen] = useState(false);

  // New Dish Form
  const [newMenuForm, setNewMenuForm] = useState({
    name: 'Spring Weekly Institutional Cycle',
    season_or_cycle: 'Spring 2026',
    dish_name: 'Grilled Rosemary Chicken & Wild Rice',
    category: 'Hot Entree',
    portion_weight_grams: 350,
    cost_per_serving: 3.40,
    planned_portions: 220,
    dietary_tags: ['Halal', 'High Protein'],
    allergens: ['Dairy'],
  });

  // New Ingredient Form
  const [newIngredientForm, setNewIngredientForm] = useState({
    name: 'Organic Romanesco Broccoli',
    category: 'Produce',
    default_unit: 'kg',
    cost_per_unit: 3.80,
    storage_temp: 'Chilled (0-4°C)',
    reorder_point: 20,
    supplier_name: 'Valley Fresh Farm'
  });

  const loadMenuData = async () => {
    setLoading(true);
    try {
      const ms = await fetchMenus();
      setMenus(ms);
      const ings = await fetchIngredientsCatalog();
      setIngredients(ings);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMenuData();
  }, []);

  const handleCreateMenu = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createMenu({
        kitchen_id: '11111111-1111-1111-1111-111111111111',
        name: newMenuForm.name,
        season_or_cycle: newMenuForm.season_or_cycle,
        is_active: true,
        items: [
          {
            name: newMenuForm.dish_name,
            category: newMenuForm.category,
            serving_size_grams: newMenuForm.portion_weight_grams,
            cost_per_serving_usd: newMenuForm.cost_per_serving,
            planned_portions: newMenuForm.planned_portions,
            allergens: newMenuForm.allergens,
            dietary_tags: newMenuForm.dietary_tags,
          }
        ]
      });
      setMenus([created, ...menus]);
      setIsAddMenuModalOpen(false);
      onShowSuccess(`Created menu dish "${newMenuForm.dish_name}" in database.`);
    } catch (err: any) {
      alert(err.message || 'Failed to create menu');
    }
  };

  const handleCreateIngredient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createCatalogIngredient(newIngredientForm);
      setIngredients([created, ...ingredients]);
      setIsAddIngredientModalOpen(false);
      onShowSuccess(`Added ${created.name} to ingredients master catalog.`);
    } catch (err: any) {
      alert(err.message || 'Failed to add ingredient to catalog');
    }
  };

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="emerald" size="sm">Nutritional & Costing Master</Badge>
            <span className="text-xs text-slate-400">Institutional Weekly Cycle</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Menu Planning & Ingredients</h1>
          <p className="text-xs text-slate-400">Pre-service headcount allocations, standardized recipes, and ingredients catalog</p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadMenuData}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
          {activeTab === 'menus' ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsAddMenuModalOpen(true)}
              leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
            >
              Add Dish to Cycle
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsAddIngredientModalOpen(true)}
              leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
            >
              Add Catalog Ingredient
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-3 border-b border-white/10 pb-3">
        <button
          onClick={() => setActiveTab('menus')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'menus'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Weekly Cycle Menus
        </button>
        <button
          onClick={() => setActiveTab('catalog')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'catalog'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Ingredients Master Catalog ({ingredients.length})
        </button>
      </div>

      {activeTab === 'menus' ? (
        <div className="space-y-6">
          {/* Day Ribbon */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-2">
            {days.map((day) => (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  selectedDay === day
                    ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
                    : 'glass-panel text-slate-400 hover:text-white'
                }`}
              >
                {day}
              </button>
            ))}
          </div>

          {/* Dishes Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menus.flatMap(m => m.items || []).map((dish, idx) => (
              <div key={dish.id || idx} className="glass-panel p-5 rounded-2xl border border-white/10 space-y-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">{dish.category || 'Entree'}</span>
                    <Badge variant="success" size="sm">Active Cycle</Badge>
                  </div>

                  <h3 className="text-base font-bold text-white">{dish.name}</h3>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {(dish.dietary_tags || ['Standard']).map((d, i) => (
                      <span key={i} className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-medium">
                        {d}
                      </span>
                    ))}
                    {(dish.allergens || []).map((alg, i) => (
                      <span key={i} className="text-[10px] bg-rose-950/60 text-rose-300 border border-rose-500/20 px-2 py-0.5 rounded-full">
                        {alg}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
                  <div>
                    <span className="font-bold text-white text-sm">{dish.planned_portions || 200}</span> portions
                  </div>
                  <div>
                    <span className="font-bold text-white text-sm">${dish.cost_per_serving_usd?.toFixed(2) || '3.20'}</span> / serving
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Ingredients Catalog Table */
        <Card>
          <CardHeader>
            <CardTitle>Ingredients Catalog Master</CardTitle>
            <CardDescription>Approved suppliers, default units, and automated reorder points</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-white/10">
                  <tr>
                    <th className="py-3 px-4">Ingredient Name</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Default Unit</th>
                    <th className="py-3 px-4">Standard Cost</th>
                    <th className="py-3 px-4">Storage Profile</th>
                    <th className="py-3 px-4">Reorder Point</th>
                    <th className="py-3 px-4">Supplier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {ingredients.map((ing) => (
                    <tr key={ing.id} className="hover:bg-white/5">
                      <td className="py-3 px-4 font-bold text-white">{ing.name}</td>
                      <td className="py-3 px-4">{ing.category}</td>
                      <td className="py-3 px-4 font-mono">{ing.default_unit}</td>
                      <td className="py-3 px-4 font-mono text-emerald-400">${ing.cost_per_unit?.toFixed(2)}</td>
                      <td className="py-3 px-4 text-slate-400">{ing.storage_temp || 'Ambient'}</td>
                      <td className="py-3 px-4 font-mono">{ing.reorder_point || 10} {ing.default_unit}</td>
                      <td className="py-3 px-4 text-slate-300">{ing.supplier_name || 'Standard'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Menu Dish Modal */}
      <Modal
        isOpen={isAddMenuModalOpen}
        onClose={() => setIsAddMenuModalOpen(false)}
        title="Add Dish to Menu Cycle"
      >
        <form onSubmit={handleCreateMenu} className="space-y-4">
          <Input
            label="Dish Name"
            value={newMenuForm.dish_name}
            onChange={(e) => setNewMenuForm({ ...newMenuForm, dish_name: e.target.value })}
            placeholder="e.g. Pan-Seared Salmon with Herb Quinoa"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Menu Category"
              value={newMenuForm.category}
              onChange={(e) => setNewMenuForm({ ...newMenuForm, category: e.target.value })}
              placeholder="e.g. Hot Entree, Soup, Side"
              required
            />
            <Input
              label="Serving Size (grams)"
              type="number"
              value={newMenuForm.portion_weight_grams}
              onChange={(e) => setNewMenuForm({ ...newMenuForm, portion_weight_grams: Number(e.target.value) })}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Cost per Serving ($)"
              type="number"
              step="0.01"
              value={newMenuForm.cost_per_serving}
              onChange={(e) => setNewMenuForm({ ...newMenuForm, cost_per_serving: Number(e.target.value) })}
              required
            />
            <Input
              label="Planned Portions"
              type="number"
              value={newMenuForm.planned_portions}
              onChange={(e) => setNewMenuForm({ ...newMenuForm, planned_portions: Number(e.target.value) })}
              required
            />
          </div>
          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsAddMenuModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Menu Dish
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Catalog Ingredient Modal */}
      <Modal
        isOpen={isAddIngredientModalOpen}
        onClose={() => setIsAddIngredientModalOpen(false)}
        title="Add Ingredient to Master Catalog"
      >
        <form onSubmit={handleCreateIngredient} className="space-y-4">
          <Input
            label="Ingredient Name"
            value={newIngredientForm.name}
            onChange={(e) => setNewIngredientForm({ ...newIngredientForm, name: e.target.value })}
            placeholder="e.g. Extra Virgin Olive Oil"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Category"
              value={newIngredientForm.category}
              onChange={(e) => setNewIngredientForm({ ...newIngredientForm, category: e.target.value })}
              options={[
                { value: 'Produce', label: 'Produce' },
                { value: 'Dairy & Eggs', label: 'Dairy & Eggs' },
                { value: 'Meat & Poultry', label: 'Meat & Poultry' },
                { value: 'Dry Goods & Grains', label: 'Dry Goods & Grains' },
                { value: 'Bakery', label: 'Bakery' },
              ]}
            />
            <Input
              label="Default Unit"
              value={newIngredientForm.default_unit}
              onChange={(e) => setNewIngredientForm({ ...newIngredientForm, default_unit: e.target.value })}
              placeholder="kg, liters, units"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Cost per Unit ($)"
              type="number"
              step="0.01"
              value={newIngredientForm.cost_per_unit}
              onChange={(e) => setNewIngredientForm({ ...newIngredientForm, cost_per_unit: Number(e.target.value) })}
              required
            />
            <Input
              label="Reorder Threshold"
              type="number"
              value={newIngredientForm.reorder_point}
              onChange={(e) => setNewIngredientForm({ ...newIngredientForm, reorder_point: Number(e.target.value) })}
              required
            />
          </div>
          <Input
            label="Preferred Supplier"
            value={newIngredientForm.supplier_name}
            onChange={(e) => setNewIngredientForm({ ...newIngredientForm, supplier_name: e.target.value })}
            placeholder="e.g. Pacific Prime Catch"
          />
          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsAddIngredientModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Catalog Item
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// =============================================================
// 4. PRODUCTION PLANNING & MEAL PRODUCTION COMPLETION SCREEN
// =============================================================
export const ProductionPlanningScreen: React.FC<OperationsProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [batches, setBatches] = useState<ProductionBatchRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isCompleteModalOpen, setIsCompleteModalOpen] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<ProductionBatchRecord | null>(null);

  // Schedule Batch Form
  const [scheduleForm, setScheduleForm] = useState({
    batch_code: `BATCH-${Date.now().toString().slice(-6)}`,
    dish_name: 'Wild Herb Roasted Chicken Breast',
    planned_portions: 250,
    station_assigned: 'Station 1 - Hot Roasting',
    head_chef: 'Chef Marcus Vance',
    target_temp_c: 74.0,
    notes: 'HACCP critical probe required before blast chilling.'
  });

  // Complete Production Form
  const [completeForm, setCompleteForm] = useState({
    actual_portions_prepped: 250,
    holding_temperature_c: 74.5,
    notes: 'Core probe verified at 74.5°C for 30 seconds. Transferred to hot holding.'
  });

  const loadBatches = async () => {
    setLoading(true);
    try {
      const b = await fetchProductionBatches();
      setBatches(b);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const handleScheduleBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createProductionBatch({
        kitchen_id: '11111111-1111-1111-1111-111111111111',
        ...scheduleForm
      });
      setBatches([created, ...batches]);
      setIsScheduleModalOpen(false);
      onShowSuccess(`Production batch ${created.batch_code} scheduled.`);
    } catch (err: any) {
      alert(err.message || 'Failed to schedule production batch');
    }
  };

  const handleCompleteBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatch) return;
    try {
      const completed = await completeProductionBatch(selectedBatch.id, completeForm);
      setBatches(batches.map(b => b.id === selectedBatch.id ? completed : b));
      setIsCompleteModalOpen(false);
      onShowSuccess(`Batch ${selectedBatch.batch_code} completed. ${completeForm.actual_portions_prepped} portions recorded.`);
    } catch (err: any) {
      alert(err.message || 'Failed to complete production batch');
    }
  };

  const openCompleteModal = (b: ProductionBatchRecord) => {
    setSelectedBatch(b);
    setCompleteForm({
      actual_portions_prepped: b.planned_portions,
      holding_temperature_c: b.target_temp_c || 74.0,
      notes: 'HACCP probe temperature verified. Ready for service.'
    });
    setIsCompleteModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">Kitchen Range Execution</Badge>
            <span className="text-xs text-slate-400">Station Cooking Protocols</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Batch Production Schedules</h1>
          <p className="text-xs text-slate-400">Cooking schedules, internal HACCP temperature checks, and meal completion telemetry</p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadBatches}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsScheduleModalOpen(true)}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Schedule Batch
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        {batches.map((b) => (
          <div
            key={b.id}
            className="glass-panel p-5 rounded-2xl border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-white/20 transition-all"
          >
            <div className="space-y-1.5">
              <div className="flex items-center space-x-2">
                <span className="text-base font-bold text-white">{b.dish_name || 'Production Batch Item'}</span>
                <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  {b.batch_code}
                </span>
                <Badge
                  variant={
                    b.status === 'COMPLETED' ? 'success' :
                    b.status === 'HOLDING' ? 'purple' :
                    b.status === 'COOKING' ? 'warning' : 'neutral'
                  }
                  size="sm"
                >
                  {b.status}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                <span>Station: <strong>{b.station_assigned || 'Range 1'}</strong></span>
                <span>Planned: <strong>{b.planned_portions} portions</strong></span>
                {b.actual_portions_prepped && <span>Actual: <strong className="text-emerald-400">{b.actual_portions_prepped} portions</strong></span>}
                <span>Chef: <strong>{b.head_chef || 'Executive Chef'}</strong></span>
              </div>
            </div>

            {/* HACCP Probe & Action */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="flex items-center space-x-1.5 justify-end">
                  <Thermometer className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-bold text-white font-mono">
                    {b.holding_temperature_c ? `${b.holding_temperature_c}°C` : `${b.target_temp_c || 74}°C (Target)`}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400">HACCP Probe Standard</span>
              </div>

              {b.status !== 'COMPLETED' ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => openCompleteModal(b)}
                >
                  Complete Production
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onNavigate('consumption')}
                >
                  Track Consumption &rarr;
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Schedule Batch Modal */}
      <Modal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        title="Schedule New Production Batch"
      >
        <form onSubmit={handleScheduleBatch} className="space-y-4">
          <Input
            label="Dish / Recipe Name"
            value={scheduleForm.dish_name}
            onChange={(e) => setScheduleForm({ ...scheduleForm, dish_name: e.target.value })}
            placeholder="e.g. Braised Beef Short Ribs"
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Batch Code"
              value={scheduleForm.batch_code}
              onChange={(e) => setScheduleForm({ ...scheduleForm, batch_code: e.target.value })}
              required
            />
            <Input
              label="Planned Portions"
              type="number"
              value={scheduleForm.planned_portions}
              onChange={(e) => setScheduleForm({ ...scheduleForm, planned_portions: Number(e.target.value) })}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Assigned Station"
              value={scheduleForm.station_assigned}
              onChange={(e) => setScheduleForm({ ...scheduleForm, station_assigned: e.target.value })}
              placeholder="e.g. Station 2 - Steam Kettles"
              required
            />
            <Input
              label="Lead Chef"
              value={scheduleForm.head_chef}
              onChange={(e) => setScheduleForm({ ...scheduleForm, head_chef: e.target.value })}
              required
            />
          </div>
          <Input
            label="HACCP Target Internal Core Temp (°C)"
            type="number"
            step="0.5"
            value={scheduleForm.target_temp_c}
            onChange={(e) => setScheduleForm({ ...scheduleForm, target_temp_c: Number(e.target.value) })}
            required
          />
          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsScheduleModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Commit Production Schedule
            </Button>
          </div>
        </form>
      </Modal>

      {/* Complete Batch Modal */}
      <Modal
        isOpen={isCompleteModalOpen}
        onClose={() => setIsCompleteModalOpen(false)}
        title={`Complete Meal Production — ${selectedBatch?.dish_name}`}
      >
        {selectedBatch && (
          <form onSubmit={handleCompleteBatch} className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-900 border border-white/10 text-xs flex justify-between">
              <span>Batch Code: <strong className="font-mono text-cyan-400">{selectedBatch.batch_code}</strong></span>
              <span>Planned: <strong>{selectedBatch.planned_portions} portions</strong></span>
            </div>

            <Input
              label="Actual Portions Prepped"
              type="number"
              value={completeForm.actual_portions_prepped}
              onChange={(e) => setCompleteForm({ ...completeForm, actual_portions_prepped: Number(e.target.value) })}
              required
            />

            <Input
              label="HACCP Internal Core Probe Temperature (°C)"
              type="number"
              step="0.1"
              value={completeForm.holding_temperature_c}
              onChange={(e) => setCompleteForm({ ...completeForm, holding_temperature_c: Number(e.target.value) })}
              required
            />

            <Input
              label="Culinary & Safety Notes"
              value={completeForm.notes}
              onChange={(e) => setCompleteForm({ ...completeForm, notes: e.target.value })}
            />

            <div className="flex justify-end space-x-3 pt-3">
              <Button variant="ghost" type="button" onClick={() => setIsCompleteModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Confirm & Mark Completed
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

// =============================================================
// 5. CONSUMPTION TRACKING & LEFTOVERS ROUTING SCREEN
// =============================================================
export const ConsumptionScreen: React.FC<OperationsProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [records, setRecords] = useState<ConsumptionRecordItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [serviceForm, setServiceForm] = useState({
    meal_service: 'Lunch Banquet Service',
    service_date: new Date().toISOString().split('T')[0],
    headcount_planned: 500,
    headcount_served: 460,
    portions_consumed: 450,
    surplus_weight_kg: 24.5,
    notes: 'Higher than expected drop-off in conference attendance.'
  });

  // Route Leftover Modal
  const [isRouteModalOpen, setIsRouteModalOpen] = useState(false);
  const [selectedRecordForRoute, setSelectedRecordForRoute] = useState<ConsumptionRecordItem | null>(null);
  const [routeAction, setRouteAction] = useState<'DIVERT_TO_SURPLUS' | 'LOG_AS_WASTE'>('DIVERT_TO_SURPLUS');
  const [routeNotes, setRouteNotes] = useState('Rapid blast chilled. Wholesome prepared entrees ready for rescue.');

  const variance = Math.round(((serviceForm.headcount_served - serviceForm.headcount_planned) / serviceForm.headcount_planned) * 100);

  const loadConsumption = async () => {
    setLoading(true);
    try {
      const recs = await fetchConsumptionRecords();
      setRecords(recs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConsumption();
  }, []);

  const handleLogService = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const logged = await recordConsumption({
        kitchen_id: '11111111-1111-1111-1111-111111111111',
        ...serviceForm,
        variance_pct: variance
      });
      setRecords([logged, ...records]);
      onShowSuccess('Meal service consumption logged with automated variance calculation.');
    } catch (err: any) {
      alert(err.message || 'Failed to record consumption');
    }
  };

  const handleRouteLeftover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecordForRoute) return;
    try {
      const res = await routeConsumptionLeftover(selectedRecordForRoute.id, {
        action: routeAction,
        residual_kg: selectedRecordForRoute.surplus_weight_kg,
        dish_name: selectedRecordForRoute.dish_name || 'Post-Service Banquet Entrees',
        notes: routeNotes
      });
      setIsRouteModalOpen(false);
      onShowSuccess(res.message);
      loadConsumption();
    } catch (err: any) {
      alert(err.message || 'Failed to route leftover');
    }
  };

  const openRouteModal = (rec: ConsumptionRecordItem) => {
    setSelectedRecordForRoute(rec);
    setRouteAction('DIVERT_TO_SURPLUS');
    setRouteNotes('Blast chilled to 3°C. Packed into sanitised cambro units.');
    setIsRouteModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="indigo" size="sm">Post-Service Audit</Badge>
            <span className="text-xs text-slate-400">Headcount vs Actual Consumption</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Diner Consumption & Leftover Routing</h1>
          <p className="text-xs text-slate-400">Track actual diners served against planned headcounts to calibrate future AI demand curves and divert unserved food</p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadConsumption}
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
        >
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Log Form */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Log Service Attendance</h2>
          
          <form onSubmit={handleLogService} className="space-y-4">
            <Input
              label="Service Description"
              value={serviceForm.meal_service}
              onChange={(e) => setServiceForm({ ...serviceForm, meal_service: e.target.value })}
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Planned RSVPs"
                type="number"
                value={serviceForm.headcount_planned}
                onChange={(e) => setServiceForm({ ...serviceForm, headcount_planned: Number(e.target.value) })}
                required
              />

              <Input
                label="Actual Diners (POS)"
                type="number"
                value={serviceForm.headcount_served}
                onChange={(e) => setServiceForm({ ...serviceForm, headcount_served: Number(e.target.value) })}
                required
              />
            </div>

            {/* Calculated Variance */}
            <div className="p-3 rounded-xl bg-slate-900 border border-white/5 flex items-center justify-between text-xs">
              <span className="text-slate-400">Attendance Variance:</span>
              <span className={`font-bold ${variance < 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {variance}% ({serviceForm.headcount_served - serviceForm.headcount_planned} diners)
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Portions Consumed"
                type="number"
                value={serviceForm.portions_consumed}
                onChange={(e) => setServiceForm({ ...serviceForm, portions_consumed: Number(e.target.value) })}
                required
              />

              <Input
                label="Leftover Surplus (kg)"
                type="number"
                step="0.1"
                value={serviceForm.surplus_weight_kg}
                onChange={(e) => setServiceForm({ ...serviceForm, surplus_weight_kg: Number(e.target.value) })}
                required
              />
            </div>

            <Input
              label="Operational Notes"
              value={serviceForm.notes}
              onChange={(e) => setServiceForm({ ...serviceForm, notes: e.target.value })}
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full"
            >
              Commit Consumption Log
            </Button>
          </form>
        </div>

        {/* History Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Service Consumption Records</CardTitle>
              <CardDescription>Direct leftovers diversion into FoodLoop surplus network or waste audit logs</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-white/10">
                    <tr>
                      <th className="py-3 px-4">Date & Service</th>
                      <th className="py-3 px-4">Planned vs Actual</th>
                      <th className="py-3 px-4">Variance</th>
                      <th className="py-3 px-4">Leftover Surplus</th>
                      <th className="py-3 px-4 text-right">Leftovers Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {records.map((log) => (
                      <tr key={log.id} className="hover:bg-white/5">
                        <td className="py-3 px-4 font-bold text-white">
                          <div>{log.service_date}</div>
                          <div className="text-[10px] text-slate-400 font-normal">{log.meal_service}</div>
                        </td>
                        <td className="py-3 px-4 font-mono">
                          {log.headcount_planned} &rarr; {log.headcount_served}
                        </td>
                        <td className="py-3 px-4 font-bold">
                          <span className={log.variance_pct < 0 ? 'text-amber-400' : 'text-emerald-400'}>
                            {log.variance_pct > 0 ? `+${log.variance_pct}%` : `${log.variance_pct}%`}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-emerald-400 font-bold font-mono">
                          {log.surplus_weight_kg} kg
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => openRouteModal(log)}
                          >
                            Route Leftovers
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Route Leftover Modal */}
      <Modal
        isOpen={isRouteModalOpen}
        onClose={() => setIsRouteModalOpen(false)}
        title="Route Service Leftovers"
      >
        {selectedRecordForRoute && (
          <form onSubmit={handleRouteLeftover} className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-900 border border-white/10 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Meal Service:</span>
                <span className="font-bold text-white">{selectedRecordForRoute.meal_service}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Unconsumed Food Weight:</span>
                <span className="font-mono text-emerald-400 font-bold">{selectedRecordForRoute.surplus_weight_kg} kg</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-white">Choose Leftover Action:</label>
              
              <div 
                onClick={() => setRouteAction('DIVERT_TO_SURPLUS')}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  routeAction === 'DIVERT_TO_SURPLUS'
                    ? 'border-emerald-500 bg-emerald-950/30'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-white text-xs">DIVERT TO SURPLUS (Recommended)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 pl-6">
                  Broadcasts wholesome unconsumed food directly to verified local NGOs and shelters on the FoodLoop Redistribution Network.
                </p>
              </div>

              <div 
                onClick={() => setRouteAction('LOG_AS_WASTE')}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  routeAction === 'LOG_AS_WASTE'
                    ? 'border-rose-500 bg-rose-950/30'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Trash2 className="w-4 h-4 text-rose-400" />
                  <span className="font-bold text-white text-xs">LOG AS AUDIT WASTE</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 pl-6">
                  Records as food waste record with root cause if contaminated, out-of-temperature, or unwholesome.
                </p>
              </div>
            </div>

            <Input
              label="Operational Disposition Notes"
              value={routeNotes}
              onChange={(e) => setRouteNotes(e.target.value)}
            />

            <div className="flex justify-end space-x-3 pt-3">
              <Button variant="ghost" type="button" onClick={() => setIsRouteModalOpen(false)}>
                Cancel
              </Button>
              <Button 
                variant={routeAction === 'DIVERT_TO_SURPLUS' ? 'primary' : 'destructive'} 
                type="submit"
              >
                Execute {routeAction === 'DIVERT_TO_SURPLUS' ? 'Surplus Diversion' : 'Waste Log'}
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

// =============================================================
// 6. WASTE REPORTING & MULTI-DIMENSIONAL ANALYTICS SCREEN
// =============================================================
export const WasteReportingScreen: React.FC<OperationsProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [records, setRecords] = useState<WasteRecordItem[]>([]);
  const [analytics, setAnalytics] = useState<WasteAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);

  // New Waste Incident Form (Supports all 8 Categories)
  const [wasteForm, setWasteForm] = useState({
    food_item: 'Prepared Herb Roasted Chicken & Wild Rice',
    quantity: 14.5,
    unit: 'kg',
    category: 'OVERPRODUCTION' as WasteCategory,
    reason: 'Overestimated banquet service headcount by 45 diners',
    date: new Date().toISOString().split('T')[0],
    production_batch: 'BATCH-2026-0927-01',
    notes: 'Blast chiller at full capacity. Immediate audit logged.',
    image_url: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80',
    responsible_organization: 'Grand Continental Central Culinary Facility'
  });

  const loadWasteData = async () => {
    setLoading(true);
    try {
      const recs = await fetchWasteRecords();
      setRecords(recs);
      const anl = await fetchWasteAnalytics();
      setAnalytics(anl);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWasteData();
  }, []);

  const handleLogWaste = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const logged = await logWasteRecord({
        ...wasteForm,
        kitchen_id: '11111111-1111-1111-1111-111111111111'
      });
      setRecords([logged, ...records]);
      setIsLogModalOpen(false);
      onShowSuccess(`Waste incident logged: ${wasteForm.quantity}kg (${wasteForm.category}). Analytics refreshed.`);
      // Reload analytics immediately to recalculate graphs
      const updatedAnl = await fetchWasteAnalytics();
      setAnalytics(updatedAnl);
    } catch (err: any) {
      alert(err.message || 'Failed to log waste record');
    }
  };

  const filteredRecords = records.filter(r => 
    categoryFilter === 'All' || r.category === categoryFilter
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="teal" size="sm">EPA Food Recovery Hierarchy</Badge>
            <span className="text-xs text-slate-400">Zero-Landfill Protocol</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Food Waste Analytics & Auditing</h1>
          <p className="text-xs text-slate-400">Multi-dimensional waste telemetry, cost loss tracking, and emissions footprint</p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadWasteData}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsLogModalOpen(true)}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Log Waste Incident
          </Button>
        </div>
      </div>

      {/* Analytics KPI Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Total Waste Weight</div>
          <div className="text-2xl font-black text-white">{analytics?.total_waste_kg?.toFixed(1) || '0.0'} kg</div>
          <span className="text-[10px] text-slate-400">Tracked in active audit period</span>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Financial Loss (Cost)</div>
          <div className="text-2xl font-black text-rose-400">${analytics?.waste_cost?.toFixed(2) || '0.00'}</div>
          <span className="text-[10px] text-slate-400">Ingredient purchase valuation</span>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold">Waste Reduction Trend</div>
          <div className="text-2xl font-black text-emerald-400">
            {analytics?.waste_trend_pct ? `${analytics.waste_trend_pct > 0 ? '+' : ''}${analytics.waste_trend_pct}%` : '-14.6%'}
          </div>
          <span className="text-[10px] text-emerald-400 font-medium">Trajectory vs baseline</span>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold">GHG Equivalent Avoided</div>
          <div className="text-2xl font-black text-purple-400">
            {((analytics?.total_waste_kg || 14.2) * 2.5).toFixed(1)} kg CO₂e
          </div>
          <span className="text-[10px] text-slate-400">IPCC Food Waste Factor</span>
        </div>
      </div>

      {/* Charts Grid: Daily Waste & Waste by Category */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Daily Waste Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Waste Volume (Last 7 Days)</CardTitle>
            <CardDescription>Daily weight loss (kg) across all culinary preparation lines</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.daily_waste || []}>
                <XAxis dataKey="label" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} unit="kg" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }}
                />
                <Bar dataKey="quantity_kg" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 2. Waste by Category Bar/Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Waste by Category (All 8 Classifications)</CardTitle>
            <CardDescription>Root cause breakdown for targeted kitchen operational improvements</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.waste_by_category || []} layout="vertical">
                <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} unit="kg" />
                <YAxis dataKey="category" type="category" stroke="#64748b" fontSize={9} tickLine={false} width={120} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }}
                />
                <Bar dataKey="quantity_kg" fill="#f59e0b" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Weekly & Monthly Trends + Top Wasted Items */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly & Monthly Trend Area Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Monthly Waste Reduction Trajectory</CardTitle>
            <CardDescription>Institutional waste curve tracking towards the 25% reduction target</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics?.monthly_waste || []}>
                <defs>
                  <linearGradient id="wasteGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="label" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} unit="kg" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }}
                />
                <Area type="monotone" dataKey="quantity_kg" stroke="#8b5cf6" fillOpacity={1} fill="url(#wasteGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Wasted Food Items Table */}
        <Card>
          <CardHeader>
            <CardTitle>Waste by Food Item</CardTitle>
            <CardDescription>Top ingredients driving financial loss</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/5 text-xs">
              {(analytics?.waste_by_food_item || []).slice(0, 5).map((it, idx) => (
                <div key={idx} className="p-3 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-white">{it.food_item}</div>
                    <div className="text-[10px] text-slate-400">{it.occurrences} incidents logged</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-amber-400 font-mono">{it.quantity_kg} kg</div>
                    <div className="text-[10px] text-rose-400 font-mono">${it.cost_usd?.toFixed(2)}</div>
                  </div>
                </div>
              ))}
              {(!analytics?.waste_by_food_item || analytics.waste_by_food_item.length === 0) && (
                <div className="p-6 text-center text-slate-400 text-xs">No food item waste recorded.</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Records Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle>Audit Waste Records Log</CardTitle>
              <CardDescription>Compliant records with food item, unit, batch, notes, and responsible org</CardDescription>
            </div>

            <div className="flex items-center space-x-2">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="All">All Categories (8)</option>
                <option value="OVERPRODUCTION">OVERPRODUCTION</option>
                <option value="PLATE_WASTE">PLATE_WASTE</option>
                <option value="SPOILAGE">SPOILAGE</option>
                <option value="EXPIRED">EXPIRED</option>
                <option value="PREPARATION_WASTE">PREPARATION_WASTE</option>
                <option value="DAMAGED">DAMAGED</option>
                <option value="QUALITY_REJECTION">QUALITY_REJECTION</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Date & Food Item</th>
                  <th className="py-3 px-4">Category (8 Types)</th>
                  <th className="py-3 px-4">Quantity & Unit</th>
                  <th className="py-3 px-4">Loss ($)</th>
                  <th className="py-3 px-4">Reason / Root Cause</th>
                  <th className="py-3 px-4">Batch Reference</th>
                  <th className="py-3 px-4">Responsible Org</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredRecords.map((r) => (
                  <tr key={r.id} className="hover:bg-white/5">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white">{r.food_item}</div>
                      <div className="text-[10px] text-slate-400">{r.date}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span 
                        className="px-2 py-0.5 rounded text-[10px] font-bold"
                        style={{ 
                          backgroundColor: `${CATEGORY_COLORS[r.category] || '#64748b'}20`,
                          color: CATEGORY_COLORS[r.category] || '#64748b',
                          border: `1px solid ${CATEGORY_COLORS[r.category] || '#64748b'}40`
                        }}
                      >
                        {r.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-amber-400">
                      {r.quantity} {r.unit}
                    </td>
                    <td className="py-3 px-4 font-mono text-rose-400">
                      ${r.waste_cost?.toFixed(2) || (r.quantity * 2.0).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs truncate">
                      {r.reason}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {r.production_batch || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[10px]">
                      {r.responsible_organization || 'FoodLoop Kitchen'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Log Waste Modal (All 8 Categories) */}
      <Modal
        isOpen={isLogModalOpen}
        onClose={() => setIsLogModalOpen(false)}
        title="Log Food Waste Incident"
      >
        <form onSubmit={handleLogWaste} className="space-y-4">
          <Input
            label="Food Item Name"
            value={wasteForm.food_item}
            onChange={(e) => setWasteForm({ ...wasteForm, food_item: e.target.value })}
            placeholder="e.g. Prepared Roasted Chicken & Penne"
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Quantity"
              type="number"
              step="0.1"
              value={wasteForm.quantity}
              onChange={(e) => setWasteForm({ ...wasteForm, quantity: Number(e.target.value) })}
              required
            />
            <Select
              label="Unit"
              value={wasteForm.unit}
              onChange={(e) => setWasteForm({ ...wasteForm, unit: e.target.value })}
              options={[
                { value: 'kg', label: 'kg' },
                { value: 'liters', label: 'liters' },
                { value: 'units', label: 'units' },
              ]}
            />
          </div>

          <Select
            label="Waste Category (All 8 Required Categories)"
            value={wasteForm.category}
            onChange={(e) => setWasteForm({ ...wasteForm, category: e.target.value as any })}
            options={[
              { value: 'OVERPRODUCTION', label: 'OVERPRODUCTION (Unserved excess prepared meals)' },
              { value: 'PLATE_WASTE', label: 'PLATE_WASTE (Post-consumer dining scraps)' },
              { value: 'SPOILAGE', label: 'SPOILAGE (Cold storage degradation)' },
              { value: 'EXPIRED', label: 'EXPIRED (Date code expiration)' },
              { value: 'PREPARATION_WASTE', label: 'PREPARATION_WASTE (Trimmings, peelings, rinds)' },
              { value: 'DAMAGED', label: 'DAMAGED (Handling or packaging breakage)' },
              { value: 'QUALITY_REJECTION', label: 'QUALITY_REJECTION (Failed texture / culinary check)' },
              { value: 'OTHER', label: 'OTHER (Unclassified)' },
            ]}
          />

          <Input
            label="Reason / Root Cause"
            value={wasteForm.reason}
            onChange={(e) => setWasteForm({ ...wasteForm, reason: e.target.value })}
            placeholder="e.g. Turnout dropped due to snow storm, trimming loss"
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Incident Date"
              type="date"
              value={wasteForm.date}
              onChange={(e) => setWasteForm({ ...wasteForm, date: e.target.value })}
              required
            />
            <Input
              label="Production Batch Reference"
              value={wasteForm.production_batch}
              onChange={(e) => setWasteForm({ ...wasteForm, production_batch: e.target.value })}
              placeholder="e.g. BATCH-2026-0927-01"
            />
          </div>

          <Input
            label="Responsible Organization"
            value={wasteForm.responsible_organization}
            onChange={(e) => setWasteForm({ ...wasteForm, responsible_organization: e.target.value })}
            required
          />

          <Input
            label="Optional Image URL / Photo Evidence"
            value={wasteForm.image_url}
            onChange={(e) => setWasteForm({ ...wasteForm, image_url: e.target.value })}
            placeholder="https://..."
          />

          <Input
            label="Operational Audit Notes"
            value={wasteForm.notes}
            onChange={(e) => setWasteForm({ ...wasteForm, notes: e.target.value })}
          />

          <div className="flex justify-end space-x-3 pt-3">
            <Button variant="ghost" type="button" onClick={() => setIsLogModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Commit Waste Record
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
