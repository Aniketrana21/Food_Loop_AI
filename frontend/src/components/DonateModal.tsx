'use client';

import React, { useState, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  Package, 
  Clock, 
  AlertTriangle, 
  MapPin, 
  Thermometer, 
  CheckCircle2,
  Calendar
} from 'lucide-react';
import { createListing } from '@/lib/api';
import { FoodListing } from '@/types';

interface DonateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newListing: FoodListing) => void;
}

export const DonateModal: React.FC<DonateModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: 'Warm Herb Roasted Turkey Breast & Gravy',
    description: 'Fresh banquet surplus. Kept hot above 63°C in food-grade cambro hotel pans.',
    category: 'cooked_meals',
    quantity_kg: 28.0,
    portions: 55,
    packaging_type: 'sealed_trays',
    storage_temp: 'room_temp',
    pickup_address: '100 Grand Avenue, Banquet Kitchen Bay 4',
    pickup_lat: 37.7749,
    pickup_lng: -122.4194,
    dietary_tags: 'halal, nut_free, high_protein'
  });

  const [aiPrediction, setAiPrediction] = useState({
    safeHours: 4.0,
    urgency: 'IMMEDIATE_ACTION',
    tip: 'FDA 4-hour rule: Must be dispatched and distributed within 4 hours of prep time.'
  });

  // Calculate real-time AI shelf-life estimate when category or storage_temp changes
  useEffect(() => {
    let hours = 4.0;
    let tip = 'FDA Danger Zone rule applies (4°C-60°C). Dispatch within 4 hours.';
    let urgency = 'IMMEDIATE_ACTION';

    if (formData.category === 'cooked_meals') {
      if (formData.storage_temp === 'refrigerated') {
        hours = 72.0;
        tip = 'Cold chain maintained: Safe for up to 3 days under 4°C.';
        urgency = 'STANDARD';
      } else {
        hours = 4.0;
        tip = 'Hot banquet surplus: Must reach recipient kitchen within 4 hours of prep.';
        urgency = 'IMMEDIATE_ACTION';
      }
    } else if (formData.category === 'bakery') {
      hours = 28.0;
      tip = 'Room temperature safe for 24-48 hours. Consolidate with evening delivery.';
      urgency = 'STANDARD';
    } else if (formData.category === 'dairy') {
      hours = formData.storage_temp === 'refrigerated' ? 48.0 : 2.0;
      tip = formData.storage_temp === 'refrigerated' ? 'Keep below 4°C during courier transit.' : 'Perishable dairy at ambient temperature must be rescued within 2 hours!';
      urgency = formData.storage_temp === 'refrigerated' ? 'EXPEDITED' : 'CRITICAL';
    } else if (formData.category === 'fresh_produce') {
      hours = 72.0;
      tip = 'High humidity tolerance. Suitable for standard ambient cargo van.';
      urgency = 'STANDARD';
    }

    setAiPrediction({ safeHours: hours, urgency, tip });
  }, [formData.category, formData.storage_temp]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const now = new Date();
      const expiry = new Date(now.getTime() + aiPrediction.safeHours * 3600000);
      const pickupEnd = new Date(now.getTime() + Math.min(aiPrediction.safeHours, 4) * 3600000);

      const tagsArray = formData.dietary_tags
        .split(',')
        .map(t => t.trim().toLowerCase())
        .filter(Boolean);

      const payload = {
        title: formData.title,
        description: formData.description,
        category: formData.category,
        quantity_kg: Number(formData.quantity_kg),
        portions: Number(formData.portions),
        packaging_type: formData.packaging_type,
        storage_temp: formData.storage_temp,
        expiry_at: expiry.toISOString(),
        pickup_start: now.toISOString(),
        pickup_end: pickupEnd.toISOString(),
        pickup_address: formData.pickup_address,
        pickup_lat: formData.pickup_lat,
        pickup_lng: formData.pickup_lng,
        dietary_tags: tagsArray,
        photo_url: formData.category === 'bakery'
          ? 'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80'
          : (formData.category === 'dairy'
            ? 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80'
            : 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80')
      };

      const result = await createListing(payload);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      alert(err.message || 'Error publishing surplus donation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-white/15 rounded-3xl p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
              <Package className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Post Surplus Food Donation</h2>
              <p className="text-xs text-slate-400">Instantly match with food banks & dispatch volunteer couriers</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* AI Predictive Shelf-Life Ribbon */}
        <div className="my-4 p-3.5 rounded-2xl bg-gradient-to-r from-emerald-950/60 to-slate-900 border border-emerald-500/30 flex items-start space-x-3">
          <Sparkles className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5 flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300">
                AI Thermodynamic Spoilage Engine: {aiPrediction.safeHours}h Remaining
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                {aiPrediction.urgency.replace('_', ' ')}
              </span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              {aiPrediction.tip}
            </p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Food Item Title
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              placeholder="e.g. Vegetable Penne & Herb Chicken Breast"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="cooked_meals">Cooked Prepared Meals</option>
                <option value="bakery">Artisan Bakery & Pastries</option>
                <option value="dairy">Dairy & Refrigerated Items</option>
                <option value="fresh_produce">Fresh Produce & Fruits</option>
                <option value="meat_seafood">Meat & Seafood</option>
                <option value="packaged_goods">Packaged Pantry Goods</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Storage Condition
              </label>
              <select
                value={formData.storage_temp}
                onChange={(e) => setFormData({ ...formData, storage_temp: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="room_temp">Room Temperature (Ambient)</option>
                <option value="refrigerated">Refrigerated (≤ 4°C)</option>
                <option value="frozen">Deep Frozen (≤ -18°C)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Total Weight (kg)
              </label>
              <input
                type="number"
                step="0.5"
                min="1"
                required
                value={formData.quantity_kg}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  quantity_kg: parseFloat(e.target.value) || 0,
                  portions: Math.round((parseFloat(e.target.value) || 0) * 2.0)
                })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Estimated Portions / Servings
              </label>
              <input
                type="number"
                min="1"
                required
                value={formData.portions}
                onChange={(e) => setFormData({ ...formData, portions: parseInt(e.target.value) || 0 })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Pickup Address & Bay Number
            </label>
            <input
              type="text"
              required
              value={formData.pickup_address}
              onChange={(e) => setFormData({ ...formData, pickup_address: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              placeholder="e.g. 100 Grand Avenue, Loading Dock Bay 4"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Dietary & Allergen Tags (comma-separated)
            </label>
            <input
              type="text"
              value={formData.dietary_tags}
              onChange={(e) => setFormData({ ...formData, dietary_tags: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
              placeholder="e.g. halal, vegetarian, nut_free, gluten_free"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Handling & Packaging Notes
            </label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 resize-none"
              placeholder="Include packaging type, temperature instructions, or loading bay instructions..."
            />
          </div>

          {/* Legal Protection Disclaimer */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-white/5 text-[11px] text-slate-400 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Protected under the <strong>Bill Emerson Good Samaritan Food Donation Act</strong> from liability when donating in good faith.
            </span>
          </div>

          {/* Submit Actions */}
          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/25 active:scale-95 transition-all flex items-center space-x-2"
            >
              {loading ? (
                <span>Publishing & Dispatching...</span>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Broadcast Surplus Rescue</span>
                </>
              )}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
