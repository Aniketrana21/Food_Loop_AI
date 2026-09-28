'use client';

import React, { useState } from 'react';
import { 
  FileText, 
  Code, 
  Play, 
  Check, 
  Sparkles, 
  AlertCircle, 
  Send,
  Eye
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { NotificationTemplate } from './types';

interface NotificationTemplatesTabProps {
  templates: NotificationTemplate[];
  onTestRender: (eventType: string, payload: Record<string, any>) => Promise<any>;
}

export const NotificationTemplatesTab: React.FC<NotificationTemplatesTabProps> = ({
  templates,
  onTestRender,
}) => {
  const [selectedEvent, setSelectedEvent] = useState<string>(templates[0]?.event_type || 'surplus.urgent');
  const [samplePayload, setSamplePayload] = useState<string>(
    JSON.stringify(
      {
        item_name: 'Prepared Rice & Vegetable Curry',
        quantity_kg: 35.0,
        facility_name: 'Metro Kitchen Unit 4',
        hours_remaining: 2,
        expiry_time: '19:30 UTC',
        recipient_name: 'St. Jude Homeless Shelter',
        donation_id: 'DON-94821',
        courier_name: 'Driver Alex Chen',
        eta_minutes: 18,
        delay_reason: 'Interstate highway obstruction',
        new_eta_minutes: 32,
        waste_kg: 48.2,
        percentage_increase: 42,
        waste_category: 'OVERPRODUCTION',
        target_date: 'Tomorrow Morning',
        projected_headcount: 320,
        estimated_surplus_kg: 24.5,
        confidence_score: 91,
        recommendation_title: 'Freeze Surplus Stock for Stew Prep',
        recommendation_summary: 'Blast chill 35kg vegetable lot to preserve safety index for Friday soup batches.',
        potential_saving_kg: 35.0
      },
      null,
      2
    )
  );

  const [renderedResult, setRenderedResult] = useState<any>(null);
  const [isRendering, setIsRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);

  const activeTemplate = templates.find(t => t.event_type === selectedEvent) || templates[0];

  const handleRunRender = async () => {
    setIsRendering(true);
    setRenderError(null);
    try {
      const parsed = JSON.parse(samplePayload);
      const res = await onTestRender(selectedEvent, parsed);
      setRenderedResult(res);
    } catch (e: any) {
      setRenderError(e.message || 'Invalid JSON payload structure');
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-5 rounded-3xl glass-panel bg-slate-900 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="cyan" size="sm">Template Registry</Badge>
            <span className="text-xs text-slate-400">10 Canonical Operational Events</span>
          </div>
          <h2 className="text-xl font-black text-white tracking-tight mt-1">Notification Templates & Variable Engine</h2>
          <p className="text-xs text-slate-400">Standardized, multilingual notification copy dynamically evaluated across in-app, email, and push channels.</p>
        </div>

        <Button
          variant="ai"
          size="sm"
          onClick={handleRunRender}
          isLoading={isRendering}
          leftIcon={<Play className="w-3.5 h-3.5" />}
        >
          Test Render Template
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Template Selector List */}
        <div className="lg:col-span-4 space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">
            Canonical Event Types ({templates.length})
          </span>
          <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
            {templates.map(tmpl => {
              const isSelected = tmpl.event_type === selectedEvent;
              return (
                <button
                  key={tmpl.id}
                  onClick={() => {
                    setSelectedEvent(tmpl.event_type);
                    setRenderedResult(null);
                  }}
                  className={`w-full text-left p-3 rounded-2xl border transition-all flex items-start justify-between gap-2 ${
                    isSelected
                      ? 'bg-slate-800 border-cyan-500/40 shadow-lg'
                      : 'bg-slate-900/60 border-white/5 hover:border-white/15'
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-1.5">
                      <span className="text-xs font-bold text-white">{tmpl.name}</span>
                      <Badge
                        variant={tmpl.default_priority === 'CRITICAL' ? 'danger' : tmpl.default_priority === 'HIGH' ? 'warning' : 'neutral'}
                        size="sm"
                      >
                        {tmpl.default_priority}
                      </Badge>
                    </div>
                    <div className="text-[10px] text-cyan-400 font-mono">{tmpl.event_type}</div>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Template Detail & Interactive Simulator */}
        <div className="lg:col-span-8 space-y-4">
          {activeTemplate ? (
            <div className="p-5 rounded-3xl glass-panel bg-slate-900 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-black text-white">{activeTemplate.name}</h3>
                  <span className="text-xs text-slate-400">{activeTemplate.description}</span>
                </div>
                <span className="text-xs font-mono text-cyan-400 px-2.5 py-1 rounded-xl bg-slate-950 border border-white/10">
                  {activeTemplate.event_type}
                </span>
              </div>

              {/* Template Channels Layout */}
              <div className="space-y-3 pt-2 border-t border-white/10">
                {/* Title Template */}
                <div>
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Title Template:</span>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-white/10 text-xs font-mono text-white mt-1">
                    {activeTemplate.title_template}
                  </div>
                </div>

                {/* In-App Body */}
                <div>
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">In-App Body Template:</span>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-white/10 text-xs font-mono text-slate-300 mt-1 whitespace-pre-wrap">
                    {activeTemplate.in_app_template}
                  </div>
                </div>

                {/* Email Subject & Body */}
                {activeTemplate.email_subject_template && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">Email Subject:</span>
                      <div className="p-2.5 rounded-xl bg-slate-950 border border-white/10 text-xs font-mono text-slate-300 mt-1">
                        {activeTemplate.email_subject_template}
                      </div>
                    </div>
                    <div>
                      <span className="text-[11px] font-bold text-purple-400 uppercase tracking-wider">Push Title:</span>
                      <div className="p-2.5 rounded-xl bg-slate-950 border border-white/10 text-xs font-mono text-slate-300 mt-1">
                        {activeTemplate.push_title_template || activeTemplate.title_template}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Interactive Test Render Simulator */}
              <div className="pt-4 border-t border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Code className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">Sample Context Payload (JSON)</span>
                  </div>
                  <span className="text-[10px] text-slate-400">Editable test parameters</span>
                </div>

                <textarea
                  value={samplePayload}
                  onChange={(e) => setSamplePayload(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-2 rounded-2xl bg-slate-950 border border-white/10 font-mono text-[11px] text-emerald-400 focus:outline-none focus:border-cyan-500/50"
                />

                {renderError && (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{renderError}</span>
                  </div>
                )}

                {/* Rendered Preview Card */}
                {renderedResult && (
                  <div className="p-4 rounded-2xl bg-slate-950 border border-cyan-500/30 space-y-2 mt-3">
                    <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Live Rendered Output:</span>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500">Rendered Title:</span>
                        <p className="font-bold text-white mt-0.5">{renderedResult.rendered_title}</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500">Rendered In-App Copy:</span>
                        <p className="text-slate-300 mt-0.5 leading-relaxed">{renderedResult.rendered_in_app}</p>
                      </div>
                      {renderedResult.rendered_email_subject && (
                        <div>
                          <span className="text-[10px] uppercase font-bold text-slate-500">Rendered Email Subject:</span>
                          <p className="text-cyan-300 font-mono text-[11px] mt-0.5">{renderedResult.rendered_email_subject}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-3xl glass-panel bg-slate-900 border border-white/10 text-slate-400">
              Select a template to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
