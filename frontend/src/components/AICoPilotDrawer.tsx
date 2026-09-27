'use client';

import React, { useState } from 'react';
import { 
  X, 
  Sparkles, 
  ShieldCheck, 
  ChefHat, 
  Send, 
  BookOpen, 
  Clock, 
  Utensils, 
  Check, 
  HelpCircle,
  FileText
} from 'lucide-react';
import { askFoodLoopAI, generateRescueRecipe } from '@/lib/api';

interface AICoPilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export const AICoPilotDrawer: React.FC<AICoPilotDrawerProps> = ({
  isOpen,
  onClose,
  initialQuery
}) => {
  const [activeTab, setActiveTab] = useState<'safety' | 'recipe'>('safety');
  
  // Safety Q&A State
  const [query, setQuery] = useState(initialQuery || '');
  const [safetyResponse, setSafetyResponse] = useState<any>(null);
  const [safetyLoading, setSafetyLoading] = useState(false);

  // Recipe Synthesizer State
  const [ingredientsText, setIngredientsText] = useState('Surplus roasted chicken, Cooked basmati rice, Bell peppers, Sourdough bread');
  const [dietary, setDietary] = useState('halal');
  const [servings, setServings] = useState(60);
  const [recipeResult, setRecipeResult] = useState<any>(null);
  const [recipeLoading, setRecipeLoading] = useState(false);

  if (!isOpen) return null;

  const handleSafetySubmit = async (e?: React.FormEvent, customQ?: string) => {
    if (e) e.preventDefault();
    const q = customQ || query;
    if (!q) return;

    setSafetyLoading(true);
    try {
      const res = await askFoodLoopAI(q);
      setSafetyResponse(res);
    } catch (err: any) {
      alert('Error fetching AI safety advice');
    } finally {
      setSafetyLoading(false);
    }
  };

  const handleRecipeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const list = ingredientsText.split(',').map(s => s.trim()).filter(Boolean);
    if (list.length === 0) return;

    setRecipeLoading(true);
    try {
      const res = await generateRescueRecipe(list, dietary, servings);
      setRecipeResult(res);
    } catch (err: any) {
      alert('Error generating rescue recipe');
    } finally {
      setRecipeLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-xl h-full bg-slate-900 border-l border-white/10 shadow-2xl flex flex-col justify-between overflow-hidden">
        
        {/* Drawer Header */}
        <div className="p-5 border-b border-white/10 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 text-white flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
                <span>FoodLoop AI Co-Pilot</span>
                <span className="px-2 py-0.5 text-[10px] rounded-full bg-indigo-500/20 text-indigo-300 font-mono border border-indigo-500/30">
                  RAG + LLM
                </span>
              </h2>
              <p className="text-xs text-slate-400">Food Safety Law & Commercial Rescue Kitchen Engine</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Co-Pilot Mode Tabs */}
        <div className="p-4 border-b border-white/5 bg-slate-900/60">
          <div className="grid grid-cols-2 gap-2 bg-slate-950 p-1 rounded-xl border border-white/5">
            <button
              onClick={() => setActiveTab('safety')}
              className={`flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'safety'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Safety & Law RAG</span>
            </button>
            <button
              onClick={() => setActiveTab('recipe')}
              className={`flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'recipe'
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ChefHat className="w-4 h-4" />
              <span>Rescue Recipe LLM</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Safety & Regulation RAG Content */}
        {activeTab === 'safety' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            
            {/* Quick Suggestion Chips */}
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-2">Verified Regulatory SOPs:</p>
              <div className="flex flex-wrap gap-2">
                {[
                  "Are donors protected by Good Samaritan Act?",
                  "FDA 4-Hour Rule for cooked food",
                  "Cold chain rules for volunteer couriers",
                  "Enhanced tax deduction under IRC 170(e)(3)"
                ].map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(chip);
                      handleSafetySubmit(undefined, chip);
                    }}
                    className="text-[11px] text-slate-300 hover:text-white bg-slate-950 hover:bg-indigo-950/60 px-3 py-1.5 rounded-lg border border-white/10 hover:border-indigo-500/40 transition-all text-left"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>

            {/* Answer Display */}
            {safetyResponse && (
              <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 space-y-3 animate-fade-in">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-indigo-300 flex items-center space-x-1.5">
                    <BookOpen className="w-4 h-4" />
                    <span>Verified Knowledge Citation</span>
                  </span>
                  <span className="text-[10px] text-emerald-400 font-mono font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    Match Confidence: {Math.round(safetyResponse.confidence_score * 100)}%
                  </span>
                </div>

                <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line">
                  {safetyResponse.answer}
                </div>

                {safetyResponse.sources && safetyResponse.sources.length > 0 && (
                  <div className="pt-2 border-t border-indigo-500/20">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                      Legal & Food Code Authorities:
                    </p>
                    <div className="space-y-1">
                      {safetyResponse.sources.map((s: any, sIdx: number) => (
                        <div key={sIdx} className="text-[11px] text-indigo-300/80 flex items-center space-x-1.5">
                          <FileText className="w-3 h-3 text-indigo-400" />
                          <span>{s.title} ({s.source})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {safetyLoading && (
              <div className="p-8 text-center text-xs text-indigo-300 animate-pulse">
                Querying Food Safety Vectors & Good Samaritan Regulatory Corpus...
              </div>
            )}

          </div>
        )}

        {/* Tab 2: Bulk Rescue Recipe Generator Content */}
        {activeTab === 'recipe' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            
            <form onSubmit={handleRecipeSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Surplus Ingredients on Hand
                </label>
                <textarea
                  rows={2}
                  required
                  value={ingredientsText}
                  onChange={(e) => setIngredientsText(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 resize-none"
                  placeholder="e.g. 20kg Lentils, 15 loaves sourdough, carrots, tomatoes"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Dietary Focus
                  </label>
                  <select
                    value={dietary}
                    onChange={(e) => setDietary(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
                  >
                    <option value="any">Standard / Omnivore</option>
                    <option value="halal">Halal Verified</option>
                    <option value="vegetarian">Vegetarian</option>
                    <option value="vegan">100% Plant-Based Vegan</option>
                    <option value="gluten_free">Gluten-Free</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Target Yield ({servings} portions)
                  </label>
                  <input
                    type="range"
                    min="20"
                    max="200"
                    step="10"
                    value={servings}
                    onChange={(e) => setServings(parseInt(e.target.value))}
                    className="w-full mt-2 accent-emerald-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={recipeLoading}
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-emerald-500/20 active:scale-95 flex items-center justify-center space-x-2"
              >
                <ChefHat className="w-4 h-4" />
                <span>{recipeLoading ? 'Synthesizing Commercial Recipe...' : 'Generate Scaled Rescue Recipe'}</span>
              </button>
            </form>

            {/* Generated Recipe View */}
            {recipeResult && (
              <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 space-y-3 animate-fade-in">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                  <h3 className="text-sm font-bold text-emerald-300">{recipeResult.recipe_title}</h3>
                  <span className="text-[11px] font-bold text-white bg-emerald-600/40 px-2 py-0.5 rounded">
                    {recipeResult.estimated_servings} Servings • {recipeResult.prep_time_mins} mins
                  </span>
                </div>

                <div>
                  <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                    Ingredients Scaled:
                  </h4>
                  <ul className="text-xs text-slate-300 list-disc list-inside space-y-0.5">
                    {recipeResult.ingredients_used?.map((ing: string, i: number) => (
                      <li key={i}>{ing}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                    Commercial Preparation Instructions:
                  </h4>
                  <ol className="text-xs text-slate-300 list-decimal list-inside space-y-1.5">
                    {recipeResult.instructions?.map((step: string, sIdx: number) => (
                      <li key={sIdx} className="leading-relaxed">{step}</li>
                    ))}
                  </ol>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950 border border-amber-500/30 text-[11px] text-amber-200">
                  <span className="font-bold">Critical Food Safety Steps: </span>
                  {recipeResult.safety_tips?.join(' ')}
                </div>
              </div>
            )}

          </div>
        )}

        {/* Bottom Input Form (For Safety Tab) */}
        {activeTab === 'safety' && (
          <div className="p-4 border-t border-white/10 bg-slate-950">
            <form onSubmit={handleSafetySubmit} className="flex items-center space-x-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about Food Safety, Good Samaritan Act, or temperature..."
                className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={safetyLoading}
                className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        )}

      </div>
    </div>
  );
};
