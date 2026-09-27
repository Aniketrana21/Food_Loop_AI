'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  FileText,
  ShieldCheck,
  Building2,
  Database,
  RefreshCw,
  Trash2,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Info,
  BookOpen,
  Upload,
  Plus,
  Layers,
  ArrowRight,
  HelpCircle,
  BarChart3,
  Calendar,
  DollarSign,
  Droplets,
  Leaf,
  ShieldAlert
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { ScreenId } from '@/components/navigation/Sidebar';
import {
  RAGQueryRequest,
  RAGQueryResponse,
  SourceReferenceOut,
  OperationalContextOut,
  SuggestedPromptOut,
  ChatMessageOut,
  DocumentListItem,
  DocumentIngestRequest
} from '@/types';
import {
  chatWithRagAssistant,
  fetchSuggestedPrompts,
  fetchChatHistory,
  clearChatSession,
  fetchDocuments,
  ingestDocument,
  fetchDocumentChunks
} from '@/lib/api';

interface AIAssistantScreenProps {
  onNavigate: (screen: ScreenId) => void;
  onOpenDonateModal?: () => void;
  onShowSuccess: (msg: string) => void;
}

interface MessageItem {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  time: string;
  sources?: SourceReferenceOut[];
  operational_context?: OperationalContextOut | null;
  is_insufficient_evidence?: boolean;
}

const DEMO_TENANTS = [
  { id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', name: 'Grand Hyatt SF Culinary Center', role: 'KITCHEN_MANAGER' },
  { id: 'cccccccc-cccc-cccc-cccc-cccccccccccc', name: 'Bay Area Canning & Puree Plant', role: 'PROCESSOR' },
  { id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', name: 'Global Platform Administrator', role: 'ADMIN' },
];

export const AIAssistantScreen: React.FC<AIAssistantScreenProps> = ({ onShowSuccess }) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge'>('chat');
  const [currentTenant, setCurrentTenant] = useState(DEMO_TENANTS[0]);
  const [sessionId, setSessionId] = useState<string>('');
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [suggestedPrompts, setSuggestedPrompts] = useState<SuggestedPromptOut[]>([]);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  
  // Knowledge Base tab states
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [ingestForm, setIngestForm] = useState<DocumentIngestRequest>({
    title: '',
    content: '',
    category: 'HACCP_SOP',
    document_type: 'HACCP_SOP',
    version: '2024.1',
    access_level: 'ORGANIZATION_INTERNAL',
    source: '',
    doc_date: new Date().toISOString().split('T')[0]
  });
  const [ingesting, setIngesting] = useState(false);
  const [viewingDocChunks, setViewingDocChunks] = useState<any[] | null>(null);
  const [selectedDocTitle, setSelectedDocTitle] = useState<string>('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize session and fetch suggested prompts
  useEffect(() => {
    let sid = localStorage.getItem('foodloop_rag_session_id');
    if (!sid) {
      sid = 'session-' + Math.random().toString(36).substring(2, 10);
      localStorage.setItem('foodloop_rag_session_id', sid);
    }
    setSessionId(sid);

    loadInitialData(sid);
  }, [currentTenant.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadInitialData = async (sid: string) => {
    try {
      // 1. Load Suggested Prompts
      const prompts = await fetchSuggestedPrompts();
      if (prompts && prompts.length > 0) {
        setSuggestedPrompts(prompts);
      } else {
        // Fallback default prompts
        setSuggestedPrompts([
          { prompt: 'Why did waste increase?', category: 'OPERATIONAL_ANALYSIS', description: 'Analyze week-over-week waste trend and root causes.' },
          { prompt: 'Which food causes the most waste?', category: 'WASTE_ATTRIBUTION', description: 'Rank top food items by weight and cost loss.' },
          { prompt: 'What should we produce tomorrow?', category: 'PRODUCTION_OPTIMIZATION', description: 'Recommend tomorrow batch production quantities.' },
          { prompt: 'Which surplus is urgent?', category: 'SURPLUS_DISPATCH', description: 'Identify active surplus batches near expiry.' },
          { prompt: "Show this month's impact.", category: 'IMPACT_REPORTING', description: 'Summarize meals provided and GHG avoided.' },
        ]);
      }

      // 2. Load History
      const hist = await fetchChatHistory(sid).catch(() => null);
      if (hist && hist.messages && hist.messages.length > 0) {
        const formatted: MessageItem[] = hist.messages.map((m: any) => ({
          id: m.id,
          sender: m.role === 'user' ? 'user' : 'assistant',
          text: m.content,
          time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          sources: m.sources,
          operational_context: m.data_context && Object.keys(m.data_context).length > 0 ? (m.data_context as any) : null,
          is_insufficient_evidence: m.content.includes("I don't have enough verified information")
        }));
        setMessages(formatted);
      } else {
        // Welcome message
        setMessages([
          {
            id: 'welcome-msg',
            sender: 'assistant',
            text: `Welcome to FoodLoop AI Production RAG Assistant. I answer operational and regulatory questions with zero hallucinations using verified institutional SOPs, government guidelines, and live PostgreSQL telemetry.\n\nActive Tenant: **${currentTenant.name}**\nStrict multi-tenant access control is enforced. Click any suggested prompt below or type your question.`,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      }

      // 3. Load Documents for Knowledge Base Tab
      loadDocuments();
    } catch (err) {
      console.warn('Initial data load warning:', err);
    }
  };

  const loadDocuments = async () => {
    try {
      setDocsLoading(true);
      const res = await fetchDocuments({ limit: 50 });
      if (res && res.items) {
        setDocuments(res.items);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setDocsLoading(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query) return;

    const userMessage: MessageItem = {
      id: 'usr-' + Date.now(),
      sender: 'user',
      text: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setLoading(true);

    try {
      const response: RAGQueryResponse = await chatWithRagAssistant({
        query,
        session_id: sessionId,
        top_k: 4
      });

      const assistantMessage: MessageItem = {
        id: 'ast-' + Date.now(),
        sender: 'assistant',
        text: response.answer,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources,
        operational_context: response.operational_context,
        is_insufficient_evidence: response.is_insufficient_evidence
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: MessageItem = {
        id: 'err-' + Date.now(),
        sender: 'assistant',
        text: `Error processing query: ${err.message || 'Unable to connect to RAG service.'}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (confirm('Are you sure you want to clear chat history for this session?')) {
      try {
        await clearChatSession(sessionId);
        setMessages([
          {
            id: 'cleared-msg',
            sender: 'assistant',
            text: 'Chat history cleared. How can I assist you with operational records or compliance standards today?',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        onShowSuccess('Chat history cleared.');
      } catch (err) {
        console.error('Failed to clear history:', err);
      }
    }
  };

  const toggleSourceExpand = (id: string) => {
    setExpandedSources((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleIngestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ingestForm.title || !ingestForm.content || !ingestForm.source) {
      alert('Please fill out all required fields (Title, Source, Content).');
      return;
    }

    try {
      setIngesting(true);
      const payload: DocumentIngestRequest = {
        ...ingestForm,
        organization_id: ingestForm.access_level === 'PUBLIC' ? undefined : currentTenant.id
      };

      const res = await ingestDocument(payload);
      onShowSuccess(`Document ingested successfully! Created ${res.total_chunks} semantic vector chunks.`);
      setShowIngestModal(false);
      setIngestForm({
        title: '',
        content: '',
        category: 'HACCP_SOP',
        document_type: 'HACCP_SOP',
        version: '2024.1',
        access_level: 'ORGANIZATION_INTERNAL',
        source: '',
        doc_date: new Date().toISOString().split('T')[0]
      });
      loadDocuments();
    } catch (err: any) {
      alert(`Ingestion failed: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleViewChunks = async (docId: string, title: string) => {
    try {
      setSelectedDocTitle(title);
      const chunks = await fetchDocumentChunks(docId);
      setViewingDocChunks(chunks);
    } catch (err: any) {
      alert(`Failed to load chunks: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-5 rounded-3xl border border-indigo-500/30 bg-slate-900/90 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 flex items-center justify-center shadow-lg shadow-indigo-500/10">
            <Bot className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-black text-white tracking-tight">FoodLoop Production RAG Assistant</h1>
              <Badge variant="teal" size="sm" className="font-mono text-[10px]">PHASE 12 RAG</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Strict Access-Controlled Multi-Tenant Retrieval • Operational DB Grounding • Verified Citations
            </p>
          </div>
        </div>

        {/* Tenant Switcher & Session Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Tenant Selector */}
          <div className="flex items-center space-x-1.5 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-white/10 text-xs">
            <Building2 className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Tenant:</span>
            <select
              value={currentTenant.id}
              onChange={(e) => {
                const found = DEMO_TENANTS.find((t) => t.id === e.target.value);
                if (found) setCurrentTenant(found);
              }}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer pr-1"
            >
              {DEMO_TENANTS.map((t) => (
                <option key={t.id} value={t.id} className="bg-slate-900 text-white">
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-1 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1.5 rounded-xl text-[11px] text-emerald-400 font-mono">
            <Database className="w-3 h-3 text-emerald-400" />
            <span>PostgreSQL Active</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearHistory}
            className="text-slate-400 hover:text-rose-400 border border-white/5"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center space-x-2 border-b border-white/10 pb-3">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'chat'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span>Interactive RAG Assistant</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('knowledge');
            loadDocuments();
          }}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'knowledge'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Verified Knowledge Base & Ingestion</span>
          <span className="px-1.5 py-0.5 rounded-md bg-white/10 text-[10px]">{documents.length}</span>
        </button>
      </div>

      {/* TAB 1: INTERACTIVE CHAT */}
      {activeTab === 'chat' && (
        <div className="space-y-4">
          {/* Suggested Prompts Pill Strip */}
          <div className="glass-panel p-3.5 rounded-2xl border border-white/10 bg-slate-900/60 space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span className="flex items-center space-x-1.5 text-indigo-300">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Suggested Operational & Compliance Prompts:</span>
              </span>
              <span className="text-[10px] text-slate-500 font-mono">1-Click Live Retrieval</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {suggestedPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(p.prompt)}
                  disabled={loading}
                  className="group flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 hover:border-indigo-500/50 hover:bg-indigo-950/30 text-slate-200 text-xs transition-all text-left shadow-sm"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 group-hover:scale-125 transition-transform" />
                  <span className="font-medium group-hover:text-indigo-200">{p.prompt}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Main Chat Stream Card */}
          <Card className="h-[620px] flex flex-col justify-between border border-white/10 bg-slate-950/80 shadow-2xl rounded-3xl overflow-hidden">
            <CardContent className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-2xl w-full p-4 sm:p-5 rounded-2xl text-xs space-y-3 ${
                      m.sender === 'user'
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-medium rounded-br-none ml-12 shadow-lg shadow-emerald-500/10'
                        : 'bg-slate-900/90 border border-white/10 text-slate-200 rounded-bl-none mr-12 shadow-xl'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between border-b border-white/10 pb-2">
                      <div className="flex items-center space-x-2">
                        {m.sender === 'user' ? (
                          <span className="font-bold text-slate-950 uppercase tracking-wider text-[10px]">
                            Kitchen Operator ({currentTenant.name.split(' ')[0]})
                          </span>
                        ) : (
                          <div className="flex items-center space-x-1.5">
                            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                            <span className="font-bold text-indigo-300 uppercase tracking-wider text-[10px]">
                              FoodLoop Grounded RAG Assistant
                            </span>
                          </div>
                        )}
                      </div>
                      <span className={`text-[10px] ${m.sender === 'user' ? 'text-slate-800' : 'text-slate-500 font-mono'}`}>
                        {m.time}
                      </span>
                    </div>

                    {/* Content Text */}
                    <div className="whitespace-pre-line leading-relaxed text-slate-100 text-[13px]">
                      {m.text}
                    </div>

                    {/* Operational Data Card (if DB context returned) */}
                    {m.operational_context && (
                      <div className="mt-3 p-3.5 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center space-x-1.5 text-xs font-bold text-indigo-300">
                            <Database className="w-3.5 h-3.5 text-indigo-400" />
                            <span>Live Database Telemetry ({m.operational_context.query_type.replace('_', ' ').toUpperCase()})</span>
                          </span>
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 text-[10px] font-mono">
                            {m.operational_context.metric_count} Records Analyzed
                          </span>
                        </div>

                        {/* Key Metrics Chips */}
                        {m.operational_context.key_metrics && Object.keys(m.operational_context.key_metrics).length > 0 && (
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                            {Object.entries(m.operational_context.key_metrics).slice(0, 4).map(([key, val], kIdx) => (
                              <div key={kIdx} className="p-2 rounded-lg bg-slate-900 border border-white/5 space-y-0.5">
                                <div className="text-[10px] uppercase text-slate-400 tracking-wider truncate">
                                  {key.replace(/_/g, ' ')}
                                </div>
                                <div className="text-xs font-bold text-emerald-400 truncate">
                                  {typeof val === 'number' ? (key.includes('usd') || key.includes('loss') ? `$${val.toFixed(2)}` : val.toLocaleString()) : String(val)}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Itemized Table Breakdown */}
                        {m.operational_context.records && m.operational_context.records.length > 0 && (
                          <div className="overflow-x-auto border-t border-white/5 pt-2">
                            <table className="w-full text-[11px] text-left">
                              <thead>
                                <tr className="text-slate-400 border-b border-white/5">
                                  {Object.keys(m.operational_context.records[0]).slice(0, 3).map((col, cIdx) => (
                                    <th key={cIdx} className="pb-1 uppercase tracking-wider font-semibold">
                                      {col.replace(/_/g, ' ')}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-white/5 text-slate-300">
                                {m.operational_context.records.slice(0, 3).map((rec, rIdx) => (
                                  <tr key={rIdx}>
                                    {Object.values(rec).slice(0, 3).map((val: any, vIdx) => (
                                      <td key={vIdx} className="py-1 pr-2 truncate max-w-[140px]">
                                        {String(val)}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Source Citations Drawer */}
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-white/10 space-y-2">
                        <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold">
                          <span className="flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-indigo-400" />
                            <span>Verified Source References ({m.sources.length}):</span>
                          </span>
                          <span className="text-[10px] text-indigo-300 font-mono">Strict Access Verified</span>
                        </div>

                        <div className="space-y-1.5">
                          {m.sources.map((src, sIdx) => {
                            const isExpanded = expandedSources[`${m.id}-${sIdx}`];
                            return (
                              <div
                                key={sIdx}
                                className="p-2.5 rounded-xl bg-slate-950/70 border border-white/5 hover:border-indigo-500/30 transition-all space-y-1"
                              >
                                <div
                                  onClick={() => toggleSourceExpand(`${m.id}-${sIdx}`)}
                                  className="flex items-center justify-between cursor-pointer"
                                >
                                  <div className="flex items-center space-x-2 truncate pr-2">
                                    <Badge variant="purple" size="sm" className="text-[9px] uppercase font-mono">
                                      {src.document_type}
                                    </Badge>
                                    <span className="font-semibold text-slate-200 text-xs truncate">
                                      {src.title}
                                    </span>
                                  </div>
                                  <div className="flex items-center space-x-2 shrink-0">
                                    <span className="text-[10px] font-mono text-emerald-400">
                                      {Math.round(src.relevance_score * 100)}% match
                                    </span>
                                    {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
                                  </div>
                                </div>

                                <div className="flex flex-wrap items-center gap-x-3 text-[10px] text-slate-400 font-mono">
                                  <span>Version: {src.version}</span>
                                  <span>&bull;</span>
                                  <span>Access: {src.access_level}</span>
                                  <span>&bull;</span>
                                  <span>Source: {src.source}</span>
                                </div>

                                {isExpanded && (
                                  <div className="mt-2 p-2 rounded-lg bg-slate-900 border border-white/5 text-[11px] text-slate-300 font-mono leading-relaxed animate-fade-in">
                                    "{src.snippet}"
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Insufficient Evidence Fallback Alert */}
                    {m.is_insufficient_evidence && (
                      <div className="mt-2 p-2.5 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300 flex items-start space-x-2 text-xs">
                        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold">Strict Anti-Hallucination Guardrail Active:</span> No verified internal or regulatory documents matched this query. The assistant refrains from speculative answers.
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-900 p-3.5 rounded-2xl border border-indigo-500/30 text-xs text-indigo-300 flex items-center space-x-2.5 shadow-lg">
                    <Sparkles className="w-4 h-4 text-indigo-400 animate-spin" />
                    <span>Executing access-controlled vector search & querying live operational database...</span>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </CardContent>

            {/* Input Form */}
            <div className="p-3.5 border-t border-white/10 bg-slate-950/90">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center space-x-2"
              >
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder={`Ask about waste trends, tomorrow's production, urgent surplus, or FDA regulations...`}
                  className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-indigo-500 placeholder:text-slate-500"
                  disabled={loading}
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  disabled={loading || !inputQuery.trim()}
                  rightIcon={<Send className="w-4 h-4" />}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold"
                >
                  Send
                </Button>
              </form>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 2: VERIFIED KNOWLEDGE BASE & INGESTION */}
      {activeTab === 'knowledge' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900/90">
            <div>
              <div className="flex items-center space-x-2">
                <Badge variant="teal" size="sm">Document Repository</Badge>
                <span className="text-xs text-slate-400">Strict Multi-Tenant Ingestion Pipeline</span>
              </div>
              <h2 className="text-xl font-black text-white mt-1">Authorized Compliance Documents & SOPs</h2>
              <p className="text-xs text-slate-400">
                Documents are chunked, embedded with term vectors, and access-restricted before semantic retrieval.
              </p>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowIngestModal(true)}
              leftIcon={<Plus className="w-4 h-4" />}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
            >
              Ingest New Document
            </Button>
          </div>

          {/* Document Grid */}
          {docsLoading ? (
            <div className="p-12 text-center text-slate-400">Loading verified knowledge base...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="glass-panel p-5 rounded-2xl border border-white/10 bg-slate-900/70 hover:border-indigo-500/40 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <Badge variant="purple" size="sm" className="font-mono text-[10px]">
                        {doc.document_type || doc.category}
                      </Badge>
                      <span className="text-[10px] font-mono text-slate-400">{doc.doc_date || '2024'}</span>
                    </div>

                    <h3 className="text-sm font-bold text-white leading-snug">{doc.title}</h3>

                    <div className="text-xs text-slate-300 font-mono space-y-1 bg-slate-950 p-2.5 rounded-xl border border-white/5">
                      <div><span className="text-slate-500">Source:</span> {doc.regulatory_source}</div>
                      <div><span className="text-slate-500">Version:</span> {doc.version} &bull; <span className="text-slate-500">Access:</span> <span className={doc.access_level === 'PUBLIC' ? 'text-emerald-400' : 'text-amber-400'}>{doc.access_level}</span></div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
                    <span className="text-slate-400 font-mono text-[11px]">
                      {doc.total_chunks || 1} Semantic Chunks
                    </span>
                    <button
                      onClick={() => handleViewChunks(doc.id, doc.title)}
                      className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
                    >
                      <Layers className="w-3.5 h-3.5" />
                      <span>Inspect Chunks</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Ingest Document Modal */}
      {showIngestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="bg-slate-900 border border-white/15 rounded-3xl p-6 max-w-xl w-full shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center space-x-2">
                <Upload className="w-5 h-5 text-emerald-400" />
                <h3 className="text-lg font-black text-white">Ingest Compliance Document</h3>
              </div>
              <button
                onClick={() => setShowIngestModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleIngestSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Document Title *</label>
                <input
                  type="text"
                  required
                  value={ingestForm.title}
                  onChange={(e) => setIngestForm({ ...ingestForm, title: e.target.value })}
                  placeholder="e.g. Standard Operating Procedure for Food Safety"
                  className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Document Type</label>
                  <select
                    value={ingestForm.document_type}
                    onChange={(e) => setIngestForm({ ...ingestForm, document_type: e.target.value })}
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white"
                  >
                    <option value="HACCP_SOP">HACCP SOP</option>
                    <option value="INSTITUTIONAL_POLICY">Institutional Policy</option>
                    <option value="WASTE_MANAGEMENT_POLICY">Waste Management Policy</option>
                    <option value="DONATION_PROCEDURE">Donation Procedure</option>
                    <option value="GOVERNMENT_GUIDELINE">Government Guideline</option>
                    <option value="OPERATIONAL_MANUAL">Operational Manual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Access Level</label>
                  <select
                    value={ingestForm.access_level}
                    onChange={(e) => setIngestForm({ ...ingestForm, access_level: e.target.value })}
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white"
                  >
                    <option value="ORGANIZATION_INTERNAL">Organization Internal</option>
                    <option value="CONFIDENTIAL">Confidential</option>
                    <option value="PUBLIC">Public</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Version Code</label>
                  <input
                    type="text"
                    value={ingestForm.version}
                    onChange={(e) => setIngestForm({ ...ingestForm, version: e.target.value })}
                    placeholder="e.g. 2024.1"
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Regulatory / Org Source *</label>
                  <input
                    type="text"
                    required
                    value={ingestForm.source}
                    onChange={(e) => setIngestForm({ ...ingestForm, source: e.target.value })}
                    placeholder="e.g. Grand Hyatt Culinary Board"
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Full Document Text *</label>
                <textarea
                  required
                  rows={6}
                  value={ingestForm.content}
                  onChange={(e) => setIngestForm({ ...ingestForm, content: e.target.value })}
                  placeholder="Paste complete standard operating procedure or policy text here. The pipeline will automatically slice it into overlapping semantic chunks and generate vector embeddings."
                  className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-white font-mono text-[11px]"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowIngestModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={ingesting}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {ingesting ? 'Chunking & Indexing...' : 'Ingest into Vector Store'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspect Document Chunks Modal */}
      {viewingDocChunks && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="bg-slate-900 border border-white/15 rounded-3xl p-6 max-w-2xl w-full shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center space-x-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white truncate max-w-md">
                  Semantic Chunks: {selectedDocTitle}
                </h3>
              </div>
              <button
                onClick={() => setViewingDocChunks(null)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-3">
              {viewingDocChunks.map((c, i) => (
                <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-white/10 space-y-1.5 font-mono text-xs">
                  <div className="flex items-center justify-between text-[10px] text-indigo-400">
                    <span>Chunk #{c.chunk_index + 1}</span>
                    <span>{c.token_count} words</span>
                  </div>
                  <p className="text-slate-300 leading-relaxed font-sans">{c.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
