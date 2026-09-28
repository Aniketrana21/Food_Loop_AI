'use client';

import React, { useState } from 'react';
import { 
  MapPin, 
  Building2, 
  Factory, 
  HeartHandshake, 
  Truck, 
  Layers, 
  Maximize2, 
  Search, 
  Navigation, 
  Phone, 
  CheckCircle2, 
  Clock, 
  Thermometer, 
  ExternalLink 
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { AdminMapNode, AdminMapNodeType } from './types';

interface AdminGeoMapProps {
  nodes: AdminMapNode[];
  selectedNodeId?: string;
  onSelectNode?: (node: AdminMapNode | null) => void;
  isLoading?: boolean;
}

export const AdminGeoMap: React.FC<AdminGeoMapProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
  isLoading = false
}) => {
  const [filterType, setFilterType] = useState<AdminMapNodeType | 'ALL'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeNode, setActiveNode] = useState<AdminMapNode | null>(
    nodes.find(n => n.id === selectedNodeId) || null
  );

  // Filter nodes based on type and search query
  const filteredNodes = nodes.filter(n => {
    const matchesType = filterType === 'ALL' || n.node_type === filterType;
    const matchesSearch = n.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (n.address && n.address.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (n.organization_name && n.organization_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesType && matchesSearch;
  });

  // Calculate normalized coordinate bounds for SVG visualization
  // Bay Area reference bounds: Lat ~37.60 to 37.85, Lng ~ -122.52 to -122.35
  const minLat = 37.65;
  const maxLat = 37.82;
  const minLng = -122.48;
  const maxLng = -122.38;

  const projectToSvg = (lat: number, lng: number) => {
    const clampedLat = Math.max(minLat, Math.min(maxLat, lat));
    const clampedLng = Math.max(minLng, Math.min(maxLng, lng));
    const x = ((clampedLng - minLng) / (maxLng - minLng)) * 860 + 50;
    const y = (1 - (clampedLat - minLat) / (maxLat - minLat)) * 460 + 40;
    return { x, y };
  };

  const handleNodeClick = (node: AdminMapNode) => {
    setActiveNode(node);
    if (onSelectNode) onSelectNode(node);
  };

  const getNodeColor = (type: AdminMapNodeType) => {
    switch (type) {
      case 'KITCHEN': return { bg: 'bg-emerald-500', border: 'border-emerald-400', text: 'text-emerald-400', ring: 'ring-emerald-500/40' };
      case 'PROCESSING_UNIT': return { bg: 'bg-purple-500', border: 'border-purple-400', text: 'text-purple-400', ring: 'ring-purple-500/40' };
      case 'RECIPIENT': return { bg: 'bg-indigo-500', border: 'border-indigo-400', text: 'text-indigo-400', ring: 'ring-indigo-500/40' };
      case 'COURIER': return { bg: 'bg-cyan-500', border: 'border-cyan-400', text: 'text-cyan-400', ring: 'ring-cyan-500/40' };
    }
  };

  const getNodeIcon = (type: AdminMapNodeType, className: string = 'w-3.5 h-3.5') => {
    switch (type) {
      case 'KITCHEN': return <Building2 className={className} />;
      case 'PROCESSING_UNIT': return <Factory className={className} />;
      case 'RECIPIENT': return <HeartHandshake className={className} />;
      case 'COURIER': return <Truck className={className} />;
    }
  };

  return (
    <div className="relative rounded-3xl overflow-hidden border border-white/10 bg-slate-950/80 shadow-2xl backdrop-blur-md">
      {/* Top Map Toolbar */}
      <div className="p-4 border-b border-white/10 flex flex-wrap items-center justify-between gap-3 bg-slate-900/60">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
            <Navigation className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              Regional Operations Map
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            </h3>
            <p className="text-[11px] text-slate-400">Live multi-facility coordinates & automated courier telemetry</p>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-white/10">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterType === 'ALL'
                ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            All ({nodes.length})
          </button>
          <button
            onClick={() => setFilterType('KITCHEN')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterType === 'KITCHEN'
                ? 'bg-emerald-600/80 text-white shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Building2 className="w-3 h-3 text-emerald-400" />
            <span>Kitchens</span>
          </button>
          <button
            onClick={() => setFilterType('PROCESSING_UNIT')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterType === 'PROCESSING_UNIT'
                ? 'bg-purple-600/80 text-white shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Factory className="w-3 h-3 text-purple-400" />
            <span>FPUs</span>
          </button>
          <button
            onClick={() => setFilterType('RECIPIENT')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterType === 'RECIPIENT'
                ? 'bg-indigo-600/80 text-white shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <HeartHandshake className="w-3 h-3 text-indigo-400" />
            <span>Recipients</span>
          </button>
          <button
            onClick={() => setFilterType('COURIER')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterType === 'COURIER'
                ? 'bg-cyan-600/80 text-white shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Truck className="w-3 h-3 text-cyan-400" />
            <span>Couriers</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search facility / courier..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 pr-3 py-1.5 text-xs bg-slate-900 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 w-44"
          />
        </div>
      </div>

      {/* Main Map Canvas */}
      <div className="relative w-full h-[460px] bg-[#060a12] overflow-hidden select-none">
        {/* Stylized SVG Grid & Regional Base Overlay */}
        <svg className="w-full h-full" viewBox="0 0 960 540" preserveAspectRatio="none">
          <defs>
            <radialGradient id="mapGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#020617" stopOpacity="0" />
            </radialGradient>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
            </pattern>
          </defs>

          {/* Background Grid */}
          <rect width="960" height="540" fill="url(#grid)" />
          <circle cx="480" cy="270" r="320" fill="url(#mapGlow)" />

          {/* Stylized Bay Area Coastline Outline */}
          <path
            d="M 120 540 Q 200 420 280 320 T 360 220 Q 420 160 500 120 T 680 80 Q 780 40 880 20 L 960 20 L 960 540 Z"
            fill="rgba(16, 185, 129, 0.02)"
            stroke="rgba(16, 185, 129, 0.15)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />

          {/* Bay Shorelines & Road Transit Corridors */}
          <path
            d="M 220 480 Q 380 320 520 280 T 780 180"
            fill="none"
            stroke="rgba(56, 189, 248, 0.15)"
            strokeWidth="2"
          />
          <path
            d="M 310 500 L 460 310 L 620 240 L 710 140"
            fill="none"
            stroke="rgba(147, 51, 234, 0.12)"
            strokeWidth="1.5"
            strokeDasharray="6 3"
          />

          {/* Animated Courier Trajectory Lines */}
          {filteredNodes
            .filter(n => n.node_type === 'COURIER')
            .map((cNode) => {
              const pos = projectToSvg(cNode.latitude, cNode.longitude);
              return (
                <g key={`route-${cNode.id}`}>
                  <line
                    x1={pos.x - 70}
                    y1={pos.y + 40}
                    x2={pos.x}
                    y2={pos.y}
                    stroke="#06b6d4"
                    strokeWidth="2"
                    strokeDasharray="5 5"
                    className="animate-pulse"
                  />
                  <circle cx={pos.x - 70} cy={pos.y + 40} r="4" fill="#10b981" />
                </g>
              );
            })}
        </svg>

        {/* Interactive Map Nodes (HTML Pins on Top of SVG) */}
        {filteredNodes.map((node) => {
          const { x, y } = projectToSvg(node.latitude, node.longitude);
          const colors = getNodeColor(node.node_type);
          const isSelected = activeNode?.id === node.id;

          return (
            <div
              key={node.id}
              style={{ left: `${(x / 960) * 100}%`, top: `${(y / 540) * 100}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-20"
              onClick={() => handleNodeClick(node)}
            >
              {/* Pulsing ring for selected or live courier */}
              {(isSelected || node.node_type === 'COURIER') && (
                <span className={`absolute -inset-2 rounded-full ${colors.bg} opacity-30 animate-ping`} />
              )}

              {/* Pin Bubble */}
              <div
                className={`relative flex items-center justify-center w-8 h-8 rounded-full border-2 shadow-2xl transition-transform duration-200 group-hover:scale-125 ${
                  isSelected ? 'scale-125 ring-4 ' + colors.ring : ''
                } ${colors.bg} ${colors.border}`}
              >
                <div className="text-white">
                  {getNodeIcon(node.node_type)}
                </div>
              </div>

              {/* Label Tag on Hover or Selected */}
              <div className={`absolute top-9 left-1/2 -translate-x-1/2 whitespace-nowrap px-2 py-0.5 rounded-lg text-[10px] font-bold bg-slate-900/90 border border-white/20 text-white shadow-xl pointer-events-none transition-opacity ${
                isSelected ? 'opacity-100 z-30' : 'opacity-0 group-hover:opacity-100'
              }`}>
                {node.name}
              </div>
            </div>
          );
        })}

        {/* Selected Facility / Node Detail Overlay Card */}
        {activeNode && (
          <div className="absolute bottom-4 left-4 right-4 sm:right-auto sm:w-96 glass-panel bg-slate-900/95 border border-white/15 p-4 rounded-2xl shadow-2xl z-30 animate-slide-up">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${getNodeColor(activeNode.node_type).bg} text-white`}>
                  {getNodeIcon(activeNode.node_type)}
                </div>
                <div>
                  <Badge variant={activeNode.node_type === 'KITCHEN' ? 'emerald' : activeNode.node_type === 'PROCESSING_UNIT' ? 'purple' : activeNode.node_type === 'RECIPIENT' ? 'indigo' : 'cyan'} size="sm">
                    {activeNode.node_type.replace('_', ' ')}
                  </Badge>
                  <h4 className="text-sm font-bold text-white tracking-tight mt-0.5">{activeNode.name}</h4>
                </div>
              </div>
              <button
                onClick={() => setActiveNode(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg text-xs"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300 mt-2 flex items-center gap-1.5">
              <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
              <span>{activeNode.address || 'Address registered on file'}</span>
            </p>

            {/* Operational Specs Grid */}
            <div className="grid grid-cols-2 gap-2 mt-3 p-2.5 rounded-xl bg-slate-950/60 border border-white/5 text-[11px]">
              <div>
                <span className="text-slate-500 font-semibold uppercase text-[9px]">Status</span>
                <p className="font-bold text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {activeNode.status}
                </p>
              </div>

              {activeNode.node_type === 'KITCHEN' && (
                <div>
                  <span className="text-slate-500 font-semibold uppercase text-[9px]">Meal Capacity</span>
                  <p className="font-bold text-white">{activeNode.details.daily_meal_capacity || '1,200'} portions/day</p>
                </div>
              )}

              {activeNode.node_type === 'PROCESSING_UNIT' && (
                <div>
                  <span className="text-slate-500 font-semibold uppercase text-[9px]">Daily Intake</span>
                  <p className="font-bold text-white">{activeNode.details.daily_capacity_kg || '2,500'} kg/day</p>
                </div>
              )}

              {activeNode.node_type === 'RECIPIENT' && (
                <div>
                  <span className="text-slate-500 font-semibold uppercase text-[9px]">Cold Chain</span>
                  <p className="font-bold text-white">{activeNode.details.cold_storage_available ? 'Available (4°C)' : 'Ambient Only'}</p>
                </div>
              )}

              {activeNode.node_type === 'COURIER' && (
                <div>
                  <span className="text-slate-500 font-semibold uppercase text-[9px]">Cargo Payload</span>
                  <p className="font-bold text-cyan-300">{activeNode.details.cargo_weight_kg || '85'} kg</p>
                </div>
              )}

              {activeNode.contact_phone && (
                <div className="col-span-2 pt-1 border-t border-white/5 flex items-center gap-1.5 text-slate-400">
                  <Phone className="w-3 h-3 text-slate-400" />
                  <span>{activeNode.contact_phone}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Map Legend */}
        <div className="absolute top-4 right-4 bg-slate-900/90 border border-white/10 rounded-xl p-2.5 shadow-xl hidden md:flex flex-col space-y-1.5 text-[11px] z-10">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Facility Legend</span>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-300">Commercial Kitchen</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
            <span className="text-slate-300">Food Processing Unit</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
            <span className="text-slate-300">Registered Recipient</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-slate-300">Active Delivery Courier</span>
          </div>
        </div>
      </div>
    </div>
  );
};
