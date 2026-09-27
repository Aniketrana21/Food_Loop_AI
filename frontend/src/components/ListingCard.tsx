'use client';

import React, { useState } from 'react';
import { FoodListing } from '@/types';
import { 
  Clock, 
  MapPin, 
  Thermometer, 
  Package, 
  Sparkles, 
  AlertCircle, 
  Check, 
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

interface ListingCardProps {
  listing: FoodListing;
  onClaim: (listing: FoodListing) => void;
  onAskSafety: (title: string, category: string) => void;
}

export const ListingCard: React.FC<ListingCardProps> = ({
  listing,
  onClaim,
  onAskSafety
}) => {
  const [claimed, setClaimed] = useState(listing.status !== 'available');
  const safeHours = listing.estimated_shelf_life_hours || 4.0;
  const isUrgent = safeHours <= 4.0;

  const categoryIcons: Record<string, string> = {
    cooked_meals: '🍲 Hot Catering',
    bakery: '🥖 Bakery Bake',
    dairy: '🥛 Chilled Dairy',
    fresh_produce: '🥗 Fresh Greens',
    packaged_goods: '📦 Packaged Goods',
    meat_seafood: '🥩 Protein'
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-2xl overflow-hidden border border-white/10 flex flex-col justify-between group">
      
      {/* Card Header & Photo Banner */}
      <div className="relative h-48 w-full overflow-hidden bg-slate-900">
        <img
          src={listing.photo_url || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"}
          alt={listing.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />

        {/* Top Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-slate-900/80 backdrop-blur-md text-emerald-400 border border-emerald-500/30 shadow-md">
            {categoryIcons[listing.category] || listing.category}
          </span>

          <span className={`px-2.5 py-1 rounded-lg text-[11px] font-bold backdrop-blur-md shadow-md flex items-center space-x-1 ${
            isUrgent
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
          }`}>
            <Clock className="w-3.5 h-3.5" />
            <span>{safeHours}h left</span>
          </span>
        </div>

        {/* Portions & Quantity Strip */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white">
          <div className="flex items-center space-x-2">
            <span className="text-lg font-black text-white">{listing.quantity_kg} kg</span>
            <span className="text-xs text-slate-300">({listing.portions} meals)</span>
          </div>

          <div className="flex items-center space-x-1 text-[11px] font-medium text-slate-300 bg-slate-900/70 px-2 py-0.5 rounded backdrop-blur-sm">
            <Thermometer className="w-3.5 h-3.5 text-emerald-400" />
            <span className="capitalize">{listing.storage_temp.replace('_', ' ')}</span>
          </div>
        </div>
      </div>

      {/* Card Content Body */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div>
          <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors line-clamp-1">
            {listing.title}
          </h3>
          <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
            {listing.description}
          </p>
        </div>

        {/* Dietary tags */}
        {listing.dietary_tags && listing.dietary_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {listing.dietary_tags.map((tag, tIdx) => (
              <span
                key={tIdx}
                className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-white/5 uppercase tracking-wide"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Donor & Location Details */}
        <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center space-x-1 truncate max-w-[200px]">
            <MapPin className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">{listing.pickup_address}</span>
          </div>

          <button
            onClick={() => onAskSafety(listing.title, listing.category)}
            className="flex items-center space-x-1 text-indigo-400 hover:text-indigo-300 font-semibold"
            title="Check FDA food safety standards for this item"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Safety SOP</span>
          </button>
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="p-4 pt-0">
        <button
          onClick={() => {
            if (!claimed) {
              setClaimed(true);
              onClaim(listing);
            }
          }}
          disabled={claimed}
          className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2 ${
            claimed
              ? 'bg-slate-800 text-slate-400 border border-white/5 cursor-not-allowed'
              : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/20 active:scale-[0.98]'
          }`}
        >
          {claimed ? (
            <>
              <Check className="w-4 h-4 text-emerald-400" />
              <span>Claimed for Shelter</span>
            </>
          ) : (
            <>
              <Package className="w-4 h-4" />
              <span>Claim Surplus Donation</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </div>

    </div>
  );
};
