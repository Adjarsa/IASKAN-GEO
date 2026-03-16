import { useState, useEffect, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Sparkles, Download, ExternalLink, Copy, Check, 
  BarChart3, AlertTriangle, Target, Zap, PlayCircle
} from 'lucide-react';
import { ImpactSimulator } from '@/components/ImpactSimulator';

// Import optimized components
import {
  ScoreCardsGrid,
  DiagnosticsList,
  ActionPlan,
  QuickWins,
  MissingElements,
  KeywordOpportunities,
  DistributionStrategy,
  OptimizerInputForm
} from '@/components/optimizer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Tab configuration
const TABS = [
  { id: 'overview', label: "Vue d'ensemble", icon: BarChart3 },
  { id: 'diagnostics', label: 'Diagnostics', icon: AlertTriangle },
  { id: 'actions', label: "Plan d'action", icon: Target },
  { id: 'distribution', label: 'Distribution', icon: Zap },
  { id: 'simulator', label: 'Simulateur', icon: PlayCircle }
];

// Results Header Component
const ResultsHeader = memo(({ result, onReset, onExport }) => (
  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
    <div className="min-w-0">
      <h2 className="text-xl font-semibold text-white truncate">{result.title || "Résultats d'analyse"}</h2>
      {result.url && (
        <a 
          href={result.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1 mt-1"
        >
          <span className="truncate max-w-[300px]">{result.url}</span>
          <ExternalLink className="w-3 h-3 flex-shrink-0" />
        </a>
      )}
    </div>
    <div className="flex gap-2 flex-shrink-0">
      <Button
        onClick={onReset}
        variant="outline"
        className="bg-slate-700 border-slate-600 text-white hover:bg-slate-600"
      >
        Nouvelle analyse
      </Button>
      <Button
        onClick={onExport}
        className="bg-violet-600 hover:bg-violet-700 text-white"
      >
        <Download className="w-4 h-4 mr-2" />
        Export
      </Button>
    </div>
  </div>
));

ResultsHeader.displayName = 'ResultsHeader';

// Tab Navigation Component
const TabNavigation = memo(({ activeTab, onTabChange }) => (
  <div className="border-b border-slate-700 overflow-x-auto">
    <div className="flex gap-1 min-w-max">
      {TABS.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === tab.id
              ? 'border-violet-500 text-white'
              : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800/50'
          }`}
        >
          <tab.icon className="w-4 h-4" />
          {tab.label}
        </button>
      ))}
    </div>
  </div>
));

TabNavigation.displayName = 'TabNavigation';

// LLM Analysis Section
const LLMAnalysisSection = memo(({ analysis }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = useCallback(() => {
    navigator.clipboard.writeText(analysis);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [analysis]);

  if (!analysis) return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold flex items-center gap-2 text-violet-400">
          <Sparkles className="w-5 h-5" />
          Analyse IA détaillée
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={copyToClipboard}
          className="text-slate-400 hover:text-white"
        >
          {copied ? <Check className="w-4 h-4 mr-1" /> : <Copy className="w-4 h-4 mr-1" />}
          {copied ? 'Copié!' : 'Copier'}
        </Button>
      </div>
      <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-sm text-slate-300 whitespace-pre-wrap max-h-[400px] overflow-y-auto">
        {analysis}
      </div>
    </div>
  );
});

LLMAnalysisSection.displayName = 'LLMAnalysisSection';

// Main Page Component
export default function ArticleOptimizerPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [quota, setQuota] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch quota on mount
  useEffect(() => {
    const fetchQuota = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/article-optimizer/quota`, {
          withCredentials: true
        });
        setQuota(response.data);
      } catch (err) {
        console.error('Error fetching quota:', err);
      }
    };
    fetchQuota();
  }, []);

  // Analyze handler
  const handleAnalyze = useCallback(async ({ url, content, useLLM }) => {
    setLoading(true);

    try {
      const endpoint = useLLM ? '/api/article-optimizer/analyze-with-llm' : '/api/article-optimizer/analyze';
      const response = await axios.post(
        `${BACKEND_URL}${endpoint}`,
        { url, content, use_llm: useLLM },
        { withCredentials: true }
      );

      setResult(response.data);
      toast.success('Analyse terminée !');
      
      // Refresh quota
      const quotaResponse = await axios.get(`${BACKEND_URL}/api/article-optimizer/quota`, {
        withCredentials: true
      });
      setQuota(quotaResponse.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors de l'analyse");
    } finally {
      setLoading(false);
    }
  }, []);

  // Reset handler
  const handleReset = useCallback(() => {
    setResult(null);
    setActiveTab('overview');
  }, []);

  // Export handler
  const handleExport = useCallback(async () => {
    if (!result?.optimization_id) return;
    
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/article-optimizer/export/${result.optimization_id}?format=markdown`,
        { withCredentials: true }
      );
      
      const blob = new Blob([response.data.markdown], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `optimization-${result.optimization_id}.md`;
      a.click();
      toast.success('Export téléchargé !');
    } catch (err) {
      toast.error("Erreur lors de l'export");
    }
  }, [result]);

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="article-optimizer-page">
        {/* Header */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Optimiseur d'Article GEO</h1>
              <p className="text-sm text-slate-600">
                Analysez vos articles et améliorez leur visibilité dans les réponses IA
              </p>
            </div>
          </div>
        </div>

        {/* Input Form (when no results) */}
        {!result && (
          <OptimizerInputForm
            onAnalyze={handleAnalyze}
            loading={loading}
            quota={quota}
            onNavigatePricing={() => navigate('/pricing')}
          />
        )}

        {/* Results Section */}
        {result && result.success && (
          <div className="space-y-6">
            {/* Results Header */}
            <ResultsHeader 
              result={result} 
              onReset={handleReset} 
              onExport={handleExport} 
            />

            {/* Score Cards */}
            <ScoreCardsGrid scores={result.scores} />

            {/* Tab Navigation */}
            <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

            {/* Tab Content */}
            <Card className="p-6 bg-white border-slate-200">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <QuickWins quickWins={result.quick_wins} />
                  <MissingElements elements={result.missing_elements} />
                  <KeywordOpportunities opportunities={result.keyword_opportunities} />
                  <LLMAnalysisSection analysis={result.llm_analysis} />
                </div>
              )}

              {/* Diagnostics Tab */}
              {activeTab === 'diagnostics' && (
                <DiagnosticsList diagnostics={result.diagnostics} />
              )}

              {/* Actions Tab */}
              {activeTab === 'actions' && (
                <ActionPlan actionPlan={result.action_plan} />
              )}

              {/* Distribution Tab */}
              {activeTab === 'distribution' && (
                <DistributionStrategy strategy={result.distribution_strategy} />
              )}

              {/* Simulator Tab */}
              {activeTab === 'simulator' && (
                <ImpactSimulator
                  currentScore={result.scores?.overall || 50}
                  optimizationId={result.optimization_id}
                  onSimulationComplete={(simulation) => {
                    console.log('Simulation completed:', simulation);
                  }}
                />
              )}
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
