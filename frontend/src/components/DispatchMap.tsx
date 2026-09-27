'use client';

import React, { useState } from 'react';
import { FoodListing, OptimizationResult } from '@/types';
import { 
  MapPin, 
  Truck, 
  Navigation, 
  Clock, 
  Package, 
  Thermometer, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldCheck,
  Building2,
  Heart
} from 'lucide-react';

interface DispatchMapProps {
  listings: FoodListing[];
  optimization: OptimizationResult | null;
  onSelectListing: (listing: FoodListing) => void;
}

export const DispatchMap: React.FC<DispatchMapProps> = ({
  listings,
  optimization,
  onSelectListing
}) => {
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [filterMode, setFilterMode] = useState<'all' | 'donors' | 'shelters' | 'routes'>('all');

  // Realistic map coordinate projections for the San Francisco Bay Area canvas (lat 37.75 - 37.81, lng -122.45 - -122.38)
  const projectX = (lng: number) => {
    const minLng = -122.46;
    const maxLng = -122.38;
    return Math.max(8, Math.min(92, ((lng - minLng) / (maxLng - minLng)) * 100));
  };

  const projectY = (lat: number) => {
    const minLat = 37.75;
    const maxLat = 37.81;
    // Invert Y for canvas coordinate
    return Math.max(8, Math.min(92, (1 - (lat - minLat) / (maxLat - minLat)) * 100));
  };

  // Fixed Recipient Hubs for Map Presentation
  const recipientHubs = [
    {
      id: 'shelter-1',
      name: 'Hope Center Community Kitchen',
      type: 'shelter',
      address: '888 Mission St, SOMA',
      lat: 37.7818,
      lng: -122.4057,
      capacityKg: 300,
      currentOccupancy: '82%',
      urgentNeeds: 'Cooked proteins, fresh salads'
    },
    {
      id: 'shelter-2',
      name: 'St. Jude Homeless Shelter',
      type: 'shelter',
      address: '1240 Folsom St, SOMA',
      lat: 37.7735,
      lng: -122.4112,
      capacityKg: 250,
      currentOccupancy: '95%',
      urgentNeeds: 'Bakery, dairy, prepared soups'
    },
    {
      id: 'shelter-3',
      name: 'Westside Family Food Pantry',
      type: 'shelter',
      address: '1801 Haight St',
      lat: 37.7694,
      lng: -122.4497,
      capacityKg: 600,
      currentOccupancy: '45%',
      urgentNeeds: 'Fresh vegetables, milk'
    }
  ];

  return (
    <div className="relative w-full h-[640px] rounded-2xl overflow-hidden glass-panel border border-white/10 shadow-2xl flex flex-col">
      
      {/* Map Control Bar Header */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        
        {/* Title & Live Status */}
        <div className="glass-panel px-4 py-2 rounded-xl border border-white/15 pointer-events-auto flex items-center space-x-3 bg-slate-900/90 shadow-lg">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </div>
          <div>
            <div className="text-xs font-bold text-white tracking-wide flex items-center space-x-1.5">
              <span>Bay Area Rescue Grid</span>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20 font-mono">
                OR-Tools Active
              </span>
            </div>
            <p className="text-[10px] text-slate-400">
              {listings.length} Donors • {recipientHubs.length} Shelters • {optimization?.routes.length || 2} Fleet Routes
            </p>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="glass-panel p-1 rounded-xl border border-white/15 pointer-events-auto flex items-center space-x-1 bg-slate-900/90 shadow-lg">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterMode === 'all' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            All Nodes
          </button>
          <button
            onClick={() => setFilterMode('donors')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterMode === 'donors' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Surplus Donors
          </button>
          <button
            onClick={() => setFilterMode('shelters')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterMode === 'shelters' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Shelters / NGOs
          </button>
          <button
            onClick={() => setFilterMode('routes')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterMode === 'routes' ? 'bg-indigo-500 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Courier Routes
          </button>
        </div>

      </div>

      {/* Interactive Map Surface (Dark Cartographic Style Canvas) */}
      <div className="relative flex-1 w-full h-full bg-[#070b13] overflow-hidden select-none">
        
        {/* Subtle Map Grid lines and topographical road simulation */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid-pattern)" />
          
          {/* Simulated arterial highway curves */}
          <path d="M 50 100 Q 200 450 600 300 T 1100 200" fill="none" stroke="#1e293b" strokeWidth="8" />
          <path d="M 100 0 Q 300 300 700 350 T 1200 500" fill="none" stroke="#1e293b" strokeWidth="6" />
          <path d="M 450 50 L 520 600" fill="none" stroke="#1e293b" strokeWidth="5" />
          <path d="M 800 50 L 780 600" fill="none" stroke="#1e293b" strokeWidth="5" />
        </svg>

        {/* Dynamic Route SVG Polylines (Rendered from OR-Tools Optimizer) */}
        {(filterMode === 'all' || filterMode === 'routes') && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
            {optimization?.routes.map((route, rIdx) => {
              const strokeColor = rIdx === 0 ? '#10b981' : '#6366f1';
              // Connect stops sequentially
              const pointsStr = route.stops.map(s => `${projectX(s.longitude)}%,${projectY(s.latitude)}%`).join(' ');

              return (
                <g key={`route-group-${rIdx}`}>
                  {/* Glow outline */}
                  <polyline
                    points={pointsStr}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth="6"
                    strokeOpacity="0.3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {/* Core animated dashline */}
                  <polyline
                    points={pointsStr}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth="2.5"
                    strokeDasharray="6 6"
                    className="animate-pulse"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </g>
              );
            })}
          </svg>
        )}

        {/* 1. Depot Marker: Central Dispatch Hub */}
        <div
          style={{ left: `${projectX(-122.3937)}%`, top: `${projectY(37.7955)}%` }}
          className="absolute -translate-x-1/2 -translate-y-1/2 z-20 cursor-pointer group"
          onClick={() => setSelectedEntity({
            name: "FoodLoop Central Dispatch Hub",
            type: "depot",
            address: "1 Market St, San Francisco, CA",
            details: "Master hub for vehicle staging, Cambro sanitization, and thermal probe calibration."
          })}
        >
          <div className="w-9 h-9 rounded-xl bg-slate-900 border-2 border-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-500/30 group-hover:scale-110 transition-transform">
            <Building2 className="w-5 h-5 text-emerald-400" />
          </div>
          <span className="absolute top-10 left-1/2 -translate-x-1/2 bg-slate-900/90 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow border border-white/10 whitespace-nowrap pointer-events-none">
            Dispatch Hub
          </span>
        </div>

        {/* 2. Donor Pins (Food Listings) */}
        {(filterMode === 'all' || filterMode === 'donors') && listings.map((item) => {
          const x = projectX(item.pickup_lng);
          const y = projectY(item.pickup_lat);
          const isUrgent = (item.estimated_shelf_life_hours || 5) <= 4.0;

          return (
            <div
              key={item.id}
              style={{ left: `${x}%`, top: `${y}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-20 cursor-pointer group"
              onClick={() => {
                setSelectedEntity(item);
                onSelectListing(item);
              }}
            >
              {/* Pulsing halo */}
              <div className={`absolute -inset-2 rounded-full opacity-60 animate-beacon ${
                isUrgent ? 'bg-amber-400' : 'bg-emerald-400'
              }`} />

              <div className={`relative w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-xl transition-all group-hover:scale-125 ${
                isUrgent 
                  ? 'bg-amber-950 border-amber-400 text-amber-300 shadow-amber-500/40' 
                  : 'bg-emerald-950 border-emerald-400 text-emerald-300 shadow-emerald-500/40'
              }`}>
                <Package className="w-4 h-4" />
              </div>

              {/* Hover Badge */}
              <div className="absolute bottom-10 left-1/2 -translate-x-1/2 hidden group-hover:flex flex-col items-center pointer-events-none z-30">
                <div className="bg-slate-900/95 border border-white/20 text-white text-[11px] font-semibold px-2.5 py-1.5 rounded-lg shadow-2xl whitespace-nowrap">
                  <p className="font-bold text-emerald-400">{item.title}</p>
                  <p className="text-[10px] text-slate-300">{item.quantity_kg} kg • {item.portions} meals</p>
                  <p className="text-[9px] text-amber-300">Safe: {item.estimated_shelf_life_hours}h remaining</p>
                </div>
              </div>
            </div>
          );
        })}

        {/* 3. Recipient Shelter Pins */}
        {(filterMode === 'all' || filterMode === 'shelters') && recipientHubs.map((shelter) => {
          const x = projectX(shelter.lng);
          const y = projectY(shelter.lat);

          return (
            <div
              key={shelter.id}
              style={{ left: `${x}%`, top: `${y}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-20 cursor-pointer group"
              onClick={() => setSelectedEntity(shelter)}
            >
              <div className="w-8 h-8 rounded-full bg-violet-950 border-2 border-violet-400 text-violet-300 flex items-center justify-center shadow-xl shadow-violet-500/30 group-hover:scale-125 transition-all">
                <Heart className="w-4 h-4 text-violet-400 fill-violet-400/20" />
              </div>

              <span className="absolute top-9 left-1/2 -translate-x-1/2 bg-slate-900/90 text-violet-200 text-[10px] font-semibold px-2 py-0.5 rounded shadow border border-violet-500/30 whitespace-nowrap pointer-events-none">
                {shelter.name.split(' ')[0]} Shelter
              </span>
            </div>
          );
        })}

        {/* 4. Active Courier Vehicles */}
        {(filterMode === 'all' || filterMode === 'routes') && optimization?.routes.map((route, idx) => {
          // Place vehicle along 1st stop waypoint
          const currentStop = route.stops[1] || route.stops[0];
          const x = projectX(currentStop.longitude) + (idx === 0 ? -1.5 : 1.5);
          const y = projectY(currentStop.latitude) + (idx === 0 ? 1.5 : -1.5);

          return (
            <div
              key={`vehicle-${route.driver_id}`}
              style={{ left: `${x}%`, top: `${y}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-30 cursor-pointer group"
              onClick={() => setSelectedEntity(route)}
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-500 text-white flex items-center justify-center shadow-2xl ring-2 ring-white group-hover:scale-125 transition-transform animate-bounce">
                <Truck className="w-4 h-4" />
              </div>
              <div className="absolute top-10 left-1/2 -translate-x-1/2 bg-slate-950 text-indigo-300 text-[10px] font-bold px-2 py-0.5 rounded-full border border-indigo-400/40 whitespace-nowrap shadow-lg">
                {route.driver_name.split(' ')[0]} ({route.total_load_kg}kg)
              </div>
            </div>
          );
        })}

      </div>

      {/* Selected Entity Details Overlay Card (Bottom Drawer) */}
      {selectedEntity && (
        <div className="absolute bottom-4 left-4 right-4 z-30 glass-panel p-4 rounded-xl border border-white/20 bg-slate-900/95 shadow-2xl animate-slide-up flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {selectedEntity.category ? selectedEntity.category.replace('_', ' ') : (selectedEntity.vehicle_type || selectedEntity.type || 'Shelter')}
              </span>
              <h4 className="text-sm font-bold text-white tracking-tight">
                {selectedEntity.title || selectedEntity.name || selectedEntity.driver_name}
              </h4>
            </div>
            <p className="text-xs text-slate-300">
              {selectedEntity.description || selectedEntity.address || `Route includes ${selectedEntity.stops?.length || 4} optimized dispatch stops.`}
            </p>
            <div className="flex items-center space-x-4 text-[11px] text-slate-400 pt-1">
              {selectedEntity.quantity_kg && (
                <span className="flex items-center text-emerald-400 font-medium">
                  <Package className="w-3.5 h-3.5 mr-1" /> {selectedEntity.quantity_kg} kg ({selectedEntity.portions} portions)
                </span>
              )}
              {selectedEntity.estimated_shelf_life_hours && (
                <span className="flex items-center text-amber-300 font-medium">
                  <Clock className="w-3.5 h-3.5 mr-1" /> {selectedEntity.estimated_shelf_life_hours}h Safe Window
                </span>
              )}
              {selectedEntity.total_distance_km && (
                <span className="flex items-center text-indigo-300 font-medium">
                  <Navigation className="w-3.5 h-3.5 mr-1" /> {selectedEntity.total_distance_km} km • ETA: {selectedEntity.total_duration_mins} mins
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {selectedEntity.category && (
              <button
                onClick={() => onSelectListing(selectedEntity)}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-emerald-500/20"
              >
                Claim This Surplus
              </button>
            )}
            <button
              onClick={() => setSelectedEntity(null)}
              className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Map Legend (Bottom Right) */}
      <div className="absolute top-20 right-4 z-20 glass-panel p-2.5 rounded-xl border border-white/10 bg-slate-900/90 text-[10px] space-y-1.5 hidden md:block">
        <div className="font-bold text-slate-300 border-b border-white/10 pb-1">Map Legend</div>
        <div className="flex items-center space-x-2 text-slate-300">
          <div className="w-3 h-3 rounded-full bg-emerald-500 border border-white/50" />
          <span>Surplus Donor Hub</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-300">
          <div className="w-3 h-3 rounded-full bg-violet-500 border border-white/50" />
          <span>Recipient Shelter</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-300">
          <div className="w-3 h-3 rounded-full bg-indigo-500 border border-white/50" />
          <span>Volunteer Courier</span>
        </div>
      </div>

    </div>
  );
};
