'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Camera,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Scale,
  RefreshCw,
  Trash2,
  Share2,
  Info,
  Sliders,
  History,
  ShieldAlert,
  ArrowRight,
  Eye,
  Check,
  RotateCcw,
  Sparkles,
  Layers,
  Activity
} from 'lucide-react';
import { ScreenId } from '@/components/navigation/Sidebar';
import {
  CanonicalFoodCategory,
  VisionClassificationResult,
  VisionSampleImage,
  VisionScanHistoryItem,
  VisionBenchmarkReport,
} from '@/types';
import {
  classifyFoodImage,
  classifyFoodFile,
  confirmVisionResult,
  fetchVisionHistory,
  fetchVisionSamples,
  fetchVisionBenchmark,
} from '@/lib/api';

const CANONICAL_CATEGORIES: CanonicalFoodCategory[] = [
  'Rice',
  'Dal',
  'Vegetables',
  'Chapati',
  'Bread',
  'Fruit',
  'Dessert',
  'Other',
];

interface ComputerVisionScreenProps {
  onNavigate?: (screen: ScreenId) => void;
  onShowSuccess?: (msg: string) => void;
}

export const ComputerVisionScreen: React.FC<ComputerVisionScreenProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  // State
  const [samples, setSamples] = useState<VisionSampleImage[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null);
  const [uploadedImagePreview, setUploadedImagePreview] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [classificationResult, setClassificationResult] = useState<VisionClassificationResult | null>(null);
  
  // Human Confirmation & Correction State
  const [selectedCategory, setSelectedCategory] = useState<CanonicalFoodCategory | null>(null);
  const [scaleWeightKg, setScaleWeightKg] = useState<string>('5.0');
  const [workerNotes, setWorkerNotes] = useState<string>('');
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  // History & Benchmark State
  const [history, setHistory] = useState<VisionScanHistoryItem[]>([]);
  const [benchmark, setBenchmark] = useState<VisionBenchmarkReport | null>(null);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load initial data
  useEffect(() => {
    loadSamples();
    loadHistory();
    loadBenchmark();
  }, []);

  const loadSamples = async () => {
    try {
      const data = await fetchVisionSamples();
      setSamples(data);
    } catch (err) {
      console.error('Failed to load sample images:', err);
    }
  };

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await fetchVisionHistory(15);
      setHistory(data);
    } catch (err) {
      console.error('Failed to load vision history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const loadBenchmark = async () => {
    try {
      const data = await fetchVisionBenchmark();
      setBenchmark(data);
    } catch (err) {
      console.error('Failed to load benchmark:', err);
    }
  };

  // Run AI classification on a selected sample
  const handleSelectSample = async (sample: VisionSampleImage) => {
    setSelectedSampleId(sample.sample_id);
    setUploadedFile(null);
    setUploadedImagePreview(sample.preview_svg);
    setActionSuccessMessage(null);
    setIsAnalyzing(true);

    try {
      const result = await classifyFoodImage({
        sample_id: sample.sample_id,
        notes: `Selected calibrated demo sample: ${sample.title}`,
      });
      setClassificationResult(result);
      setSelectedCategory(result.prediction);
    } catch (err: any) {
      console.error('Classification error:', err);
      alert(err.message || 'Vision classification failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle image upload from camera or file
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedSampleId(null);
    setUploadedFile(file);
    setActionSuccessMessage(null);

    // Create local preview
    const reader = new FileReader();
    reader.onload = async () => {
      setUploadedImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    setIsAnalyzing(true);
    try {
      const result = await classifyFoodFile(file);
      setClassificationResult(result);
      setSelectedCategory(result.prediction);
    } catch (err: any) {
      console.error('File classification error:', err);
      alert(err.message || 'Failed to analyze uploaded camera image');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Execute Dispatch Action (Confirm, Log as Waste, Declare as Surplus)
  const handleConfirmAction = async (action: 'CONFIRM_ONLY' | 'LOG_WASTE' | 'DECLARE_SURPLUS') => {
    if (!classificationResult || !selectedCategory) return;

    const parsedWeight = parseFloat(scaleWeightKg);
    if ((action === 'LOG_WASTE' || action === 'DECLARE_SURPLUS') && (isNaN(parsedWeight) || parsedWeight <= 0)) {
      alert('Please enter a valid scale-measured weight (> 0 kg) from your digital kitchen scale.');
      return;
    }

    setIsSubmittingAction(true);
    try {
      const res = await confirmVisionResult({
        scan_id: classificationResult.scan_id,
        confirmed_label: selectedCategory,
        action,
        weight_kg: isNaN(parsedWeight) ? undefined : parsedWeight,
        notes: workerNotes || undefined,
      });

      setActionSuccessMessage(res.message);
      if (onShowSuccess) {
        onShowSuccess(res.message);
      }
      // Refresh audit history
      await loadHistory();
    } catch (err: any) {
      console.error('Confirm error:', err);
      alert(err.message || 'Operational confirmation failed');
    } finally {
      setIsSubmittingAction(false);
    }
  };

  // Check if current action requires manual confirmation
  const isCorrection = classificationResult && selectedCategory !== classificationResult.prediction;
  const isLowConfidence = classificationResult && classificationResult.confidence < 0.70;

  return (
    <div className="flex-1 overflow-y-auto bg-[#070b14] text-slate-100 p-4 md:p-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500/20 to-orange-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/10">
              <Camera className="w-5 h-5" />
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Computer Vision Food Classifier
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Phase 13 AI Vision
            </span>
          </div>
          <p className="text-slate-400 text-sm max-w-2xl">
            Real-time vision assistance for commercial kitchen workers. Identifies 8 culinary categories from RGB images with human-in-the-loop review, verified scale inputs, and strict low-confidence safety guardrails.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowBenchmarkModal(true)}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-300 hover:text-white text-xs font-semibold transition"
          >
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>Model Benchmark</span>
          </button>
          <button
            onClick={() => onNavigate && onNavigate('waste_reporting')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-300 hover:text-white text-xs font-semibold transition"
          >
            <Trash2 className="w-4 h-4 text-rose-400" />
            <span>Waste Logs</span>
          </button>
          <button
            onClick={() => onNavigate && onNavigate('surplus_marketplace')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition"
          >
            <Share2 className="w-4 h-4" />
            <span>Surplus Marketplace</span>
          </button>
        </div>
      </div>

      {/* Critical Operational & Safety Disclaimers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Anti-Weight Assumption Warning */}
        <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30 flex items-start space-x-3.5">
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-amber-300 flex items-center gap-1.5">
              Strict Weight Guardrail Enforced
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Standard 2D RGB imagery cannot deduce volumetric mass or food density. The vision model detects category morphology only. Final financial and environmental metrics mandate verified tare weight from a digital kitchen scale.
            </p>
          </div>
        </div>

        {/* Low-Confidence Safety Guardrail Notice */}
        <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 flex items-start space-x-3.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-indigo-300 flex items-center gap-1.5">
              Human-in-the-Loop Architecture
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Predictions below 70% confidence are blocked from triggering automated operational actions. Kitchen workers retain full authority to correct classifications before records are committed to the audit trail.
            </p>
          </div>
        </div>
      </div>

      {/* Main Scanner Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Image Input & Controlled Sample Bench (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Upload / Camera Card */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Camera className="w-4 h-4 text-amber-400" />
                Live Camera / Image Upload
              </h3>
              <span className="text-[11px] text-slate-500">RGB Lanczos (384x384)</span>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept="image/*"
              className="hidden"
            />

            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-700 hover:border-amber-500/50 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-950/40 hover:bg-slate-950/80 group"
            >
              <div className="w-12 h-12 rounded-2xl bg-slate-800 group-hover:bg-amber-500/10 border border-slate-700 group-hover:border-amber-500/30 flex items-center justify-center text-slate-400 group-hover:text-amber-400 mx-auto mb-3 transition">
                <UploadCloud className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-slate-200">
                Click to snap photo or upload image
              </p>
              <p className="text-xs text-slate-500 mt-1">
                JPEG, PNG, WEBP, or direct camera feed
              </p>
            </div>
          </div>

          {/* Controlled Reference Sample Test Bench */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  Controlled Demo Test Bench
                </h3>
                <p className="text-[11px] text-slate-500">
                  Calibrated reference profiles for prototype evaluation
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                8 Classes
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2">
              {samples.map((s) => {
                const isSelected = selectedSampleId === s.sample_id;
                return (
                  <button
                    key={s.sample_id}
                    onClick={() => handleSelectSample(s)}
                    className={`p-2.5 rounded-xl border text-left transition flex flex-col justify-between ${
                      isSelected
                        ? 'bg-amber-500/10 border-amber-500 text-amber-200 shadow-md shadow-amber-500/10'
                        : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="w-full aspect-square rounded-lg overflow-hidden bg-slate-900 mb-2 border border-slate-800 flex items-center justify-center">
                      <img
                        src={s.preview_svg}
                        alt={s.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs font-bold truncate">
                      <span className="truncate">{s.expected_category}</span>
                      <span className={`text-[10px] ${s.is_low_confidence ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {Math.round(s.expected_confidence * 100)}%
                      </span>
                    </div>
                    <span className="text-[9px] text-slate-500 truncate block mt-0.5">
                      {s.is_low_confidence ? 'Low Conf Demo' : 'Calibrated Tray'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Inference Canvas & Human Confirmation (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Main Visual Inference & Bounding Box Canvas */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Eye className="w-4 h-4 text-indigo-400" />
                Detection & Classification Pipeline
              </h3>
              {classificationResult && (
                <span className="text-xs text-slate-500 font-mono">
                  Scan ID: #{classificationResult.scan_id.slice(0, 8)}
                </span>
              )}
            </div>

            {/* Image Preview Canvas with Bounding Box Overlay */}
            <div className="relative w-full aspect-video md:aspect-[16/9] rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center">
              {uploadedImagePreview ? (
                <>
                  <img
                    src={uploadedImagePreview}
                    alt="Vision Target Preview"
                    className="w-full h-full object-contain"
                  />

                  {/* Bounding Box Overlay */}
                  {classificationResult?.bounding_box && (
                    <div
                      className={`absolute border-2 rounded-lg pointer-events-none transition-all duration-300 ${
                        classificationResult.confidence >= 0.85
                          ? 'border-emerald-400 bg-emerald-400/10'
                          : classificationResult.confidence >= 0.65
                          ? 'border-amber-400 bg-amber-400/10'
                          : 'border-rose-400 bg-rose-400/10'
                      }`}
                      style={{
                        top: `${classificationResult.bounding_box.y * 100}%`,
                        left: `${classificationResult.bounding_box.x * 100}%`,
                        width: `${classificationResult.bounding_box.width * 100}%`,
                        height: `${classificationResult.bounding_box.height * 100}%`,
                      }}
                    >
                      <div className="absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-bold bg-slate-950/90 text-white border border-slate-700 shadow-lg flex items-center space-x-1.5">
                        <span className="capitalize">{classificationResult.prediction}</span>
                        <span className="text-emerald-400">
                          {Math.round(classificationResult.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Analyzing Overlay Spinner */}
                  {isAnalyzing && (
                    <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center space-y-3">
                      <RefreshCw className="w-8 h-8 text-amber-400 animate-spin" />
                      <p className="text-xs font-semibold text-slate-200">
                        Running aspect Lanczos preprocessing & food classifier...
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center p-8">
                  <Camera className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                  <p className="text-sm font-semibold text-slate-400">
                    No image loaded
                  </p>
                  <p className="text-xs text-slate-600 mt-1">
                    Select a sample tray or snap an RGB photo to begin
                  </p>
                </div>
              )}
            </div>

            {/* Inference Result Card */}
            {classificationResult && (
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div>
                    <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-500">
                      Model Prediction
                    </span>
                    <div className="flex items-center space-x-3 mt-0.5">
                      <span className="text-xl font-extrabold text-white">
                        {classificationResult.prediction}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                          classificationResult.confidence_tier === 'HIGH'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : classificationResult.confidence_tier === 'MODERATE'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}
                      >
                        {Math.round(classificationResult.confidence * 100)}% Confidence ({classificationResult.confidence_tier})
                      </span>
                    </div>
                  </div>

                  {classificationResult.requires_manual_confirmation && (
                    <div className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      <span>Low Confidence: Worker Review Required</span>
                    </div>
                  )}
                </div>

                {/* Candidate Probability Breakdown */}
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-2">
                    Candidate Probability Distribution
                  </span>
                  <div className="space-y-2">
                    {classificationResult.top_candidates.map((cand) => (
                      <div key={cand.category} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-300 font-medium">{cand.category}</span>
                          <span className="text-slate-400 font-mono">
                            {Math.round(cand.confidence * 100)}%
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              cand.category === classificationResult.prediction
                                ? 'bg-amber-400'
                                : 'bg-slate-600'
                            }`}
                            style={{ width: `${cand.confidence * 100}%` }}
                          />
                        </div>
                        {cand.description && (
                          <span className="text-[10px] text-slate-500 block truncate">
                            {cand.description}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Human Confirmation, Label Correction & Action Dispatch Panel */}
          {classificationResult && (
            <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800 space-y-6 shadow-xl">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  Worker Review & Human-in-the-Loop Confirmation
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Verify or correct the AI classification before logging records. Normal RGB predictions cannot deduce weight.
                </p>
              </div>

              {/* Category Selector Pills (User Correction Capability) */}
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  Confirm or Correct Category (8 Canonical Classes)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {CANONICAL_CATEGORIES.map((cat) => {
                    const isSelected = selectedCategory === cat;
                    const isAiPick = classificationResult.prediction === cat;
                    return (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`px-3 py-2.5 rounded-xl border text-xs font-semibold flex items-center justify-between transition ${
                          isSelected
                            ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/20'
                            : 'bg-slate-900/80 border-slate-700/80 hover:border-slate-600 text-slate-300'
                        }`}
                      >
                        <span>{cat}</span>
                        {isAiPick && (
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                              isSelected ? 'bg-emerald-800 text-emerald-200' : 'bg-slate-800 text-amber-400'
                            }`}
                          >
                            AI
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>

                {isCorrection && (
                  <div className="mt-2.5 p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center space-x-2">
                    <Info className="w-4 h-4 text-amber-400 shrink-0" />
                    <span>
                      <strong>Human Correction Applied:</strong> Changing from AI-predicted <strong>{classificationResult.prediction}</strong> to <strong>{selectedCategory}</strong>.
                    </span>
                  </div>
                )}
              </div>

              {/* Digital Scale Tare Weight Input */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                    Certified Scale Weight (kg) <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Scale className="w-4 h-4 text-emerald-400" />
                    </div>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={scaleWeightKg}
                      onChange={(e) => setScaleWeightKg(e.target.value)}
                      placeholder="e.g. 5.5"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-700 focus:border-emerald-500 focus:outline-none text-sm font-mono text-white placeholder-slate-600"
                    />
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    Must read directly from digital tare scale.
                  </span>
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                    Station / Batch Notes (Optional)
                  </label>
                  <input
                    type="text"
                    value={workerNotes}
                    onChange={(e) => setWorkerNotes(e.target.value)}
                    placeholder="e.g. Main lunch buffet hot-holding pan #3"
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-700 focus:border-emerald-500 focus:outline-none text-sm text-white placeholder-slate-600"
                  />
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    Recorded with forensic scan metadata.
                  </span>
                </div>
              </div>

              {/* Success Notification Alert */}
              {actionSuccessMessage && (
                <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center space-x-2 animate-fade-in">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{actionSuccessMessage}</span>
                </div>
              )}

              {/* Operational Dispatch Actions */}
              <div className="pt-2 border-t border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-slate-400 block">
                  Commitment & Downstream Routing
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    disabled={isSubmittingAction}
                    onClick={() => handleConfirmAction('CONFIRM_ONLY')}
                    className="px-4 py-3 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-bold transition flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <Check className="w-4 h-4 text-slate-400" />
                    <span>Confirm Audit Only</span>
                  </button>

                  <button
                    disabled={isSubmittingAction}
                    onClick={() => handleConfirmAction('LOG_WASTE')}
                    className="px-4 py-3 rounded-xl border border-rose-500/30 hover:border-rose-500/60 bg-rose-950/40 hover:bg-rose-950/70 text-rose-300 text-xs font-bold transition flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4 text-rose-400" />
                    <span>Log as Kitchen Waste</span>
                  </button>

                  <button
                    disabled={isSubmittingAction}
                    onClick={() => handleConfirmAction('DECLARE_SURPLUS')}
                    className="px-4 py-3 rounded-xl border border-emerald-500/40 hover:border-emerald-500/80 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/20 disabled:opacity-50"
                  >
                    <Share2 className="w-4 h-4" />
                    <span>Declare as Surplus</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Audit Trail of Vision Scans */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <History className="w-5 h-5 text-indigo-400" />
              Vision Scan Audit Trail
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Forensic record storing original AI prediction, confidence, human corrections, and linked operational records.
            </p>
          </div>
          <button
            onClick={loadHistory}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingHistory ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 uppercase tracking-wider font-semibold">
                <th className="py-3 px-3">Scan ID</th>
                <th className="py-3 px-3">Timestamp</th>
                <th className="py-3 px-3">AI Prediction</th>
                <th className="py-3 px-3">Confidence</th>
                <th className="py-3 px-3">Human Corrected Label</th>
                <th className="py-3 px-3">Downstream Record</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {history.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                    No vision scans recorded yet. Select a sample or snap a photo above.
                  </td>
                </tr>
              ) : (
                history.map((scan) => {
                  const wasCorrected = scan.corrected_label && scan.corrected_label !== scan.prediction;
                  return (
                    <tr key={scan.id} className="hover:bg-slate-800/30 transition font-sans">
                      <td className="py-3 px-3 font-mono text-slate-400">
                        #{scan.id.slice(0, 8)}
                      </td>
                      <td className="py-3 px-3 text-slate-400 whitespace-nowrap">
                        {new Date(scan.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </td>
                      <td className="py-3 px-3 font-bold text-white">
                        {scan.prediction}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            scan.confidence >= 0.85
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : scan.confidence >= 0.65
                              ? 'bg-amber-500/10 text-amber-400'
                              : 'bg-rose-500/10 text-rose-400'
                          }`}
                        >
                          {Math.round(scan.confidence * 100)}%
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        {scan.corrected_label ? (
                          <div className="flex items-center space-x-1.5">
                            <span className="font-semibold text-slate-200">
                              {scan.corrected_label}
                            </span>
                            {wasCorrected && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                Corrected
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-600 italic">Unconfirmed</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        {scan.created_record_type ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            {scan.created_record_type} #{scan.created_record_id?.slice(0, 6)}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        {scan.is_confirmed ? (
                          <span className="flex items-center space-x-1 text-emerald-400 text-xs font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Verified</span>
                          </span>
                        ) : (
                          <span className="text-amber-400/80 text-xs font-semibold">
                            Pending Review
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Benchmark Transparency Modal */}
      {showBenchmarkModal && benchmark && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-slate-900 border border-slate-700/80 rounded-2xl p-6 space-y-6 shadow-2xl animate-scale-up">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-400" />
                  Model Benchmark & Architecture Disclosures
                </h3>
                <span className="text-xs text-slate-400">
                  {benchmark.model_name} ({benchmark.version})
                </span>
              </div>
              <button
                onClick={() => setShowBenchmarkModal(false)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
              >
                ✕
              </button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">Overall Accuracy</span>
                <p className="text-2xl font-extrabold text-emerald-400 mt-1">
                  {(benchmark.overall_accuracy * 100).toFixed(1)}%
                </p>
                <span className="text-[10px] text-slate-500">240 Test Trays</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">Macro F1 Score</span>
                <p className="text-2xl font-extrabold text-indigo-400 mt-1">
                  {(benchmark.macro_f1_score * 100).toFixed(1)}%
                </p>
                <span className="text-[10px] text-slate-500">Balanced 8 Classes</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">Inference Latency</span>
                <p className="text-2xl font-extrabold text-amber-400 mt-1">
                  {benchmark.average_latency_ms.toFixed(1)}ms
                </p>
                <span className="text-[10px] text-slate-500">FastAPI Async Loop</span>
              </div>
            </div>

            {/* Per-class Metrics Table */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Per-Class Performance (Controlled Calibration Set)
              </h4>
              <div className="border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-500 uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="py-2 px-3">Class</th>
                      <th className="py-2 px-3">Precision</th>
                      <th className="py-2 px-3">Recall</th>
                      <th className="py-2 px-3">F1 Score</th>
                      <th className="py-2 px-3">Support</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono">
                    {Object.entries(benchmark.per_class_metrics).map(([cat, m]) => (
                      <tr key={cat} className="hover:bg-slate-800/30">
                        <td className="py-2 px-3 font-sans font-semibold text-slate-200">{cat}</td>
                        <td className="py-2 px-3 text-slate-300">{(m.precision * 100).toFixed(0)}%</td>
                        <td className="py-2 px-3 text-slate-300">{(m.recall * 100).toFixed(0)}%</td>
                        <td className="py-2 px-3 text-emerald-400 font-bold">{(m.f1 * 100).toFixed(1)}%</td>
                        <td className="py-2 px-3 text-slate-500">{m.support || 30}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Prototype Disclosures */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-1.5">
              <p className="font-semibold text-slate-300">Prototype Disclosure Notice:</p>
              <p>{benchmark.disclaimer}</p>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowBenchmarkModal(false)}
                className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
