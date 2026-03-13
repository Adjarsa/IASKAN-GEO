import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FileText, 
  Link2, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  ChevronRight,
  Download,
  Sparkles,
  Target,
  Clock,
  Zap,
  BarChart3,
  BookOpen,
  ExternalLink,
  Copy,
  Check,
  PlayCircle
} from 'lucide-react';
import { ImpactSimulator } from '@/components/ImpactSimulator';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Score indicator component
const ScoreIndicator = ({ score, label, size = "md" }) => {
  const getColor = (s) => {
    if (s >= 70) return "text-green-500";
    if (s >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  const getBgColor = (s) => {
    if (s >= 70) return "bg-green-500/10";
    if (s >= 50) return "bg-yellow-500/10";
    return "bg-red-500/10";
  };

  const sizeClasses = {
    sm: "w-12 h-12 text-lg",
    md: "w-16 h-16 text-xl",
    lg: "w-24 h-24 text-3xl"
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`${sizeClasses[size]} ${getBgColor(score)} rounded-full flex items-center justify-center`}>
        <span className={`font-bold ${getColor(score)}`}>{Math.round(score)}</span>
      </div>
      {label && <span className="text-xs text-slate-400">{label}</span>}
    </div>
  );
};

// Diagnostic card component
const DiagnosticCard = ({ diagnostic }) => {
  const severityConfig = {
    critical: { color: "border-red-500 bg-red-500/5", icon: XCircle, iconColor: "text-red-500" },
    high: { color: "border-orange-500 bg-orange-500/5", icon: AlertTriangle, iconColor: "text-orange-500" },
    medium: { color: "border-yellow-500 bg-yellow-500/5", icon: AlertTriangle, iconColor: "text-yellow-500" },
    low: { color: "border-blue-500 bg-blue-500/5", icon: CheckCircle2, iconColor: "text-blue-500" }
  };

  const config = severityConfig[diagnostic.severity] || severityConfig.medium;
  const Icon = config.icon;

  return (
    <div className={`p-4 rounded-lg border-l-4 ${config.color}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 ${config.iconColor}`} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase font-semibold text-slate-400">{diagnostic.category}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${config.color}`}>
              {diagnostic.severity}
            </span>
          </div>
          <p className="text-sm text-white font-medium mb-1">{diagnostic.issue}</p>
          <p className="text-sm text-slate-400">{diagnostic.recommendation}</p>
        </div>
      </div>
    </div>
  );
};

// Action item component
const ActionItem = ({ action, phase }) => {
  const phaseConfig = {
    immediate: { color: "bg-red-500", label: "Immédiat" },
    short_term: { color: "bg-orange-500", label: "Court terme" },
    medium_term: { color: "bg-yellow-500", label: "Moyen terme" },
    long_term: { color: "bg-blue-500", label: "Long terme" }
  };

  const config = phaseConfig[phase] || phaseConfig.medium_term;

  return (
    <div className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg">
      <div className={`w-2 h-2 mt-2 rounded-full ${config.color}`} />
      <div className="flex-1">
        <p className="text-sm text-white">{action.action}</p>
        {action.query && (
          <p className="text-xs text-slate-400 mt-1">Requête: "{action.query.substring(0, 50)}..."</p>
        )}
      </div>
    </div>
  );
};

export default function ArticleOptimizerPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [content, setContent] = useState('');
  const [inputMode, setInputMode] = useState('url'); // 'url' or 'content'
  const [loading, setLoading] = useState(false);
  const [useLLM, setUseLLM] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [quota, setQuota] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchQuota();
  }, []);

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

  const analyzeArticle = async () => {
    if (inputMode === 'url' && !url) {
      setError('Veuillez entrer une URL');
      return;
    }
    if (inputMode === 'content' && !content) {
      setError('Veuillez coller du contenu');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const endpoint = useLLM ? '/api/article-optimizer/analyze-with-llm' : '/api/article-optimizer/analyze';
      const response = await axios.post(
        `${BACKEND_URL}${endpoint}`,
        {
          url: inputMode === 'url' ? url : null,
          content: inputMode === 'content' ? content : null,
          use_llm: useLLM
        },
        { withCredentials: true }
      );

      setResult(response.data);
      fetchQuota(); // Refresh quota
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'analyse');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const exportMarkdown = async () => {
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
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold">Optimiseur d'Article GEO</h1>
          </div>
          <p className="text-slate-400">
            Analysez vos articles et obtenez un plan d'action concret pour améliorer leur visibilité dans les réponses IA
          </p>
        </div>

        {/* Quota info */}
        {quota && (
          <div className="mb-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-violet-400" />
                <span className="text-sm text-slate-300">
                  {quota.allowed 
                    ? `Optimisations restantes: ${quota.remaining}`
                    : quota.reason
                  }
                </span>
              </div>
              {!quota.allowed && (
                <button
                  onClick={() => navigate('/pricing')}
                  className="text-sm text-violet-400 hover:text-violet-300"
                >
                  Upgrader →
                </button>
              )}
            </div>
          </div>
        )}

        {/* Input Section */}
        {!result && (
          <div className="bg-slate-800/30 rounded-xl border border-slate-700 p-6 mb-6">
            {/* Input mode toggle */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setInputMode('url')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  inputMode === 'url'
                    ? 'bg-violet-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
                data-testid="input-mode-url"
              >
                <Link2 className="w-4 h-4" />
                URL
              </button>
              <button
                onClick={() => setInputMode('content')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  inputMode === 'content'
                    ? 'bg-violet-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
                data-testid="input-mode-content"
              >
                <FileText className="w-4 h-4" />
                Contenu
              </button>
            </div>

            {/* URL Input */}
            {inputMode === 'url' && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  URL de l'article à analyser
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-white placeholder-slate-500"
                  data-testid="url-input"
                />
              </div>
            )}

            {/* Content Input */}
            {inputMode === 'content' && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Collez le contenu de votre article (HTML ou texte)
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Collez le contenu HTML ou texte de votre article ici..."
                  rows={8}
                  className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-white placeholder-slate-500 font-mono text-sm"
                  data-testid="content-input"
                />
              </div>
            )}

            {/* LLM toggle */}
            <div className="flex items-center gap-3 mb-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useLLM}
                  onChange={(e) => setUseLLM(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-600 text-violet-500 focus:ring-violet-500 bg-slate-900"
                />
                <span className="text-sm text-slate-300">
                  Analyse enrichie par IA (recommandations détaillées)
                </span>
              </label>
              <Sparkles className="w-4 h-4 text-violet-400" />
            </div>

            {/* Error display */}
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
                {error}
              </div>
            )}

            {/* Analyze button */}
            <button
              onClick={analyzeArticle}
              disabled={loading || (quota && !quota.allowed)}
              className="w-full py-3 bg-gradient-to-r from-violet-500 to-cyan-500 text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="analyze-button"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <Target className="w-5 h-5" />
                  Analyser l'article
                </>
              )}
            </button>
          </div>
        )}

        {/* Results Section */}
        {result && result.success && (
          <div className="space-y-6">
            {/* Results header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">{result.title || 'Résultats d\'analyse'}</h2>
                {result.url && (
                  <a 
                    href={result.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1"
                  >
                    {result.url.substring(0, 50)}...
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setResult(null);
                    setUrl('');
                    setContent('');
                  }}
                  className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                >
                  Nouvelle analyse
                </button>
                <button
                  onClick={exportMarkdown}
                  className="px-4 py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 transition-colors flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export
                </button>
              </div>
            </div>

            {/* Score cards */}
            <div className="grid grid-cols-5 gap-4">
              {[
                { key: 'overall', label: 'Global' },
                { key: 'structure', label: 'Structure' },
                { key: 'authority', label: 'Autorité' },
                { key: 'citability', label: 'Citabilité' },
                { key: 'freshness', label: 'Fraîcheur' }
              ].map(({ key, label }) => (
                <div key={key} className="bg-slate-800/50 rounded-lg p-4 text-center">
                  <ScoreIndicator 
                    score={result.scores?.[key] || 0} 
                    size={key === 'overall' ? 'md' : 'sm'}
                  />
                  <p className="text-sm text-slate-300 mt-2">{label}</p>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div className="border-b border-slate-700">
              <div className="flex gap-4">
                {[
                  { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
                  { id: 'diagnostics', label: 'Diagnostics', icon: AlertTriangle },
                  { id: 'actions', label: 'Plan d\'action', icon: Target },
                  { id: 'distribution', label: 'Distribution', icon: Zap },
                  { id: 'simulator', label: 'Simulateur', icon: PlayCircle }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-violet-500 text-white'
                        : 'border-transparent text-slate-400 hover:text-white'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab content */}
            <div className="bg-slate-800/30 rounded-xl border border-slate-700 p-6">
              {/* Overview tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Quick wins */}
                  {result.quick_wins?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <Zap className="w-5 h-5 text-yellow-500" />
                        Quick Wins
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {result.quick_wins.map((win, i) => (
                          <div key={i} className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                            <p className="text-sm text-white">{win.action}</p>
                            <div className="flex gap-2 mt-2">
                              <span className="text-xs px-2 py-0.5 bg-slate-700 rounded">
                                Effort: {win.effort}
                              </span>
                              <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded">
                                Impact: {win.impact}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing elements */}
                  {result.missing_elements?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <XCircle className="w-5 h-5 text-red-500" />
                        Éléments manquants
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {result.missing_elements.map((el, i) => (
                          <span key={i} className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-sm text-red-400">
                            {el}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Keyword opportunities */}
                  {result.keyword_opportunities?.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-violet-400" />
                        Opportunités de mots-clés
                      </h3>
                      <ul className="space-y-2">
                        {result.keyword_opportunities.map((opp, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                            <ChevronRight className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                            {opp}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* LLM Analysis */}
                  {result.llm_analysis && (
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-violet-400" />
                          Analyse IA détaillée
                        </h3>
                        <button
                          onClick={() => copyToClipboard(result.llm_analysis)}
                          className="text-sm text-slate-400 hover:text-white flex items-center gap-1"
                        >
                          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          {copied ? 'Copié!' : 'Copier'}
                        </button>
                      </div>
                      <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 prose prose-invert prose-sm max-w-none whitespace-pre-wrap">
                        {result.llm_analysis}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Diagnostics tab */}
              {activeTab === 'diagnostics' && (
                <div className="space-y-4">
                  {result.diagnostics?.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-green-500" />
                      <p>Aucun problème majeur détecté</p>
                    </div>
                  ) : (
                    result.diagnostics?.map((diag, i) => (
                      <DiagnosticCard key={i} diagnostic={diag} />
                    ))
                  )}
                </div>
              )}

              {/* Actions tab */}
              {activeTab === 'actions' && (
                <div className="space-y-6">
                  {Object.entries(result.action_plan || {}).map(([phase, data]) => {
                    if (!data.actions?.length) return null;
                    
                    const phaseLabels = {
                      immediate: { label: 'Actions immédiates', icon: Zap, color: 'text-red-400' },
                      short_term: { label: 'Court terme (1-2 semaines)', icon: Clock, color: 'text-orange-400' },
                      medium_term: { label: 'Moyen terme (1 mois)', icon: Target, color: 'text-yellow-400' },
                      long_term: { label: 'Long terme (3+ mois)', icon: BookOpen, color: 'text-blue-400' }
                    };
                    
                    const config = phaseLabels[phase] || phaseLabels.medium_term;
                    
                    return (
                      <div key={phase}>
                        <h3 className={`text-lg font-semibold mb-3 flex items-center gap-2 ${config.color}`}>
                          <config.icon className="w-5 h-5" />
                          {config.label}
                        </h3>
                        <div className="space-y-2">
                          {data.actions.map((action, i) => (
                            <ActionItem key={i} action={action} phase={phase} />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Distribution tab */}
              {activeTab === 'distribution' && (
                <div className="space-y-4">
                  {result.distribution_strategy?.map((strat, i) => (
                    <div key={i} className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-white">{strat.channel}</h4>
                        <span className={`text-xs px-2 py-1 rounded ${
                          strat.priority === 'high' ? 'bg-green-500/20 text-green-400' :
                          strat.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-slate-600 text-slate-300'
                        }`}>
                          Priorité: {strat.priority}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300 mb-2">{strat.action}</p>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Clock className="w-3 h-3" />
                        {strat.timing}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Simulator tab */}
              {activeTab === 'simulator' && (
                <ImpactSimulator
                  currentScore={result.scores?.overall || 50}
                  optimizationId={result.optimization_id}
                  onSimulationComplete={(simulation) => {
                    console.log('Simulation completed:', simulation);
                  }}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
