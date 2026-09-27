'use client';

import React, { useState } from 'react';
import { 
  TrendingUp, 
  Sparkles, 
  Sliders, 
  Bot, 
  Send, 
  BookOpen, 
  Search, 
  CheckCircle, 
  FileText, 
  Scale, 
  ShieldCheck, 
  CloudSun, 
  Calendar, 
  ArrowRight,
  Info,
  Copy,
  Check
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Input } from '@/components/design-system/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { AIRecommendationCard } from '@/components/design-system/AIRecommendationCard';
import { ConfirmDialog } from '@/components/design-system/ConfirmDialog';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  MOCK_FORECAST_SERIES, 
  MOCK_OPTIMIZER_RECOMMENDATIONS, 
  MOCK_KNOWLEDGE_BASE,
  ForecastPoint,
  OptimizerRecommendation,
  KnowledgeArticle
} from '@/lib/mockData';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid,
  Legend
} from 'recharts';

interface AiProps {
  onNavigate: (screen: ScreenId) => void;
  onOpenDonateModal: () => void;
  onShowSuccess: (msg: string) => void;
}

export { AiForecastScreen } from './AiForecastScreen';

export { ProductionOptimizerScreen } from './ProductionOptimizerScreen';

export { AIAssistantScreen, AIAssistantScreen as AiAssistantScreen } from './AIAssistantScreen';

// -------------------------------------------------------------
// 4. RAG KNOWLEDGE CENTER SCREEN
// -------------------------------------------------------------
export const RagKnowledgeCenterScreen: React.FC<AiProps> = ({ onShowSuccess }) => {
  const [articles, setArticles] = useState<KnowledgeArticle[]>(MOCK_KNOWLEDGE_BASE);
  const [query, setQuery] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const filteredArticles = articles.filter(
    (a) =>
      a.title.toLowerCase().includes(query.toLowerCase()) ||
      a.excerpt.toLowerCase().includes(query.toLowerCase()) ||
      a.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleCopyCitation = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    onShowSuccess('Citation copied to clipboard for audit report.');
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="teal" size="sm">Indexed Regulatory Corpus</Badge>
            <span className="text-xs text-slate-400">pgvector Semantic Embeddings</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">RAG Knowledge Center & Compliance SOPs</h1>
          <p className="text-xs text-slate-400">Authoritative legal and food-safety reference manuals for zero-liability surplus redistribution</p>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative max-w-xl">
        <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search FDA Food Code, Good Samaritan Act, HACCP cooling rules..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
        />
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredArticles.map((art) => (
          <div key={art.id} className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider">{art.source}</span>
                <span className="text-[10px] text-slate-400">{art.lastUpdated}</span>
              </div>

              <h2 className="text-base font-bold text-white leading-snug">{art.title}</h2>

              <p className="text-xs text-slate-300 leading-relaxed">{art.excerpt}</p>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <span className="text-[10px] uppercase font-bold text-amber-400">Operational Rule:</span>
                <p className="text-xs font-medium text-slate-200">{art.keyRule}</p>
              </div>
            </div>

            <div className="pt-3 border-t border-white/5 flex items-center justify-between">
              <Badge variant="purple" size="sm">{art.category}</Badge>
              <button
                onClick={() => handleCopyCitation(art.id, `${art.title} - ${art.keyRule}`)}
                className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
              >
                {copiedId === art.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedId === art.id ? 'Copied' : 'Copy Citation'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
