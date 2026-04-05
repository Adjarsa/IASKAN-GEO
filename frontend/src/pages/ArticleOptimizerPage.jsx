import { useState, useEffect, useMemo, useCallback, memo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth, API } from '@/App';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles, Download, Copy, Check, ExternalLink, FileText, 
  Code, RefreshCw, Loader2, AlertCircle, 
  PenTool, FileQuestion, GitCompare, Braces, Wand2, FileEdit,
  ArrowRight, Bot, Target, Search, CheckCircle2, ArrowDown,
  FileCode, Send
} from 'lucide-react';

import {
  RewriteCard,
  MissingContentCard,
  CompetitorSourceCard,
  SchemaMarkupCard,
  ProjectedScoreCard,
  DiagnosticBadge
} from '@/components/optimizer/OptimizerV2Cards';

// Tab configuration for Optimize mode
const TABS = [
  { id: 'rewrites', label: 'Rewrites citables', icon: PenTool },
  { id: 'missing', label: 'Contenus manquants', icon: FileQuestion },
  { id: 'sources', label: 'Vs sources citées', icon: GitCompare },
  { id: 'schema', label: 'Balisage IA', icon: Braces }
];

// Content type options
const CONTENT_TYPES = [
  { value: 'article_fond', label: 'Article de fond GEO' },
  { value: 'comparatif', label: 'Comparatif produits' },
  { value: 'guide', label: 'Guide d\'achat' },
  { value: 'faq', label: 'Page FAQ optimisée' },
  { value: 'landing', label: 'Landing page produit' }
];

// Mode Toggle Component
const ModeToggle = memo(({ mode, onModeChange }) => (
  <div className="flex gap-2 p-1 bg-slate-100 rounded-xl">
    <button
      onClick={() => onModeChange('optimize')}
      className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
        mode === 'optimize'
          ? 'bg-white text-slate-900 shadow-sm'
          : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
      }`}
    >
      <FileEdit className="w-4 h-4" />
      Optimiser un article existant
    </button>
    <button
      onClick={() => onModeChange('generate')}
      className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
        mode === 'generate'
          ? 'bg-white text-slate-900 shadow-sm'
          : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
      }`}
    >
      <Wand2 className="w-4 h-4" />
      Créer un nouveau contenu
    </button>
  </div>
));

ModeToggle.displayName = 'ModeToggle';

// Reconnaissance Step Component
const ReconnaissanceStep = memo(({ step, status, details }) => {
  const statusConfig = {
    pending: { color: 'text-slate-400', bg: 'bg-slate-100', label: '' },
    running: { color: 'text-amber-600', bg: 'bg-amber-100', label: 'En cours' },
    done: { color: 'text-emerald-600', bg: 'bg-emerald-100', label: 'Fait' }
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <div className={`p-4 rounded-lg transition-all ${status === 'running' ? 'bg-amber-50 border border-amber-200' : 'bg-white'}`}>
      <div className="flex items-start gap-3">
        <div className={`w-7 h-7 rounded-full ${config.bg} flex items-center justify-center text-sm font-bold ${config.color}`}>
          {status === 'done' ? <CheckCircle2 className="w-4 h-4" /> : step}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className={`font-medium ${status === 'pending' ? 'text-slate-400' : 'text-slate-900'}`}>
              {details.title}
            </h4>
            {status !== 'pending' && (
              <span className={`text-sm font-medium ${config.color}`}>{details.result || config.label}</span>
            )}
          </div>
          <p className={`text-sm mt-1 ${status === 'pending' ? 'text-slate-300' : 'text-slate-600'}`}>
            {details.description}
          </p>
        </div>
      </div>
    </div>
  );
});

ReconnaissanceStep.displayName = 'ReconnaissanceStep';

// Citation Strategy Tag
const StrategyTag = memo(({ text, type }) => {
  const types = {
    gap: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    format: 'bg-slate-100 text-slate-700 border-slate-200',
    addition: 'bg-amber-100 text-amber-800 border-amber-200'
  };
  
  return (
    <span className={`px-3 py-2 rounded-lg text-sm border ${types[type] || types.format}`}>
      {text}
    </span>
  );
});

StrategyTag.displayName = 'StrategyTag';

// GEO Indicator Card
const GeoIndicator = memo(({ title, value, description }) => (
  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-100">
    <h4 className="font-semibold text-emerald-800">{title}</h4>
    <p className="text-sm text-emerald-600 mt-1">{description}</p>
  </div>
));

GeoIndicator.displayName = 'GeoIndicator';

// Generate Mode - Full Component
const GenerateMode = memo(({ project, onSendToOptimizer }) => {
  const [contentType, setContentType] = useState('article_fond');
  const [targetQuestion, setTargetQuestion] = useState('');
  const [differentiator, setDifferentiator] = useState('');
  const [phase, setPhase] = useState('input'); // input, reconnaissance, generated
  const [reconSteps, setReconSteps] = useState([
    { status: 'pending', result: '' },
    { status: 'pending', result: '' },
    { status: 'pending', result: '' },
    { status: 'pending', result: '' }
  ]);
  const [generatedContent, setGeneratedContent] = useState(null);
  const [copied, setCopied] = useState(null);

  const brandName = project?.brand_name || 'Votre marque';

  // Start reconnaissance process
  const startReconnaissance = async () => {
    if (!targetQuestion.trim()) {
      toast.error('Entrez une question utilisateur à cibler');
      return;
    }

    setPhase('reconnaissance');
    
    // Step 1: Interrogate LLMs
    setReconSteps(prev => prev.map((s, i) => i === 0 ? { status: 'running', result: '' } : s));
    await new Promise(r => setTimeout(r, 1500));
    setReconSteps(prev => prev.map((s, i) => i === 0 ? { status: 'done', result: 'Fait' } : s));
    
    // Step 2: Identify sources
    setReconSteps(prev => prev.map((s, i) => i === 1 ? { status: 'running', result: '' } : s));
    await new Promise(r => setTimeout(r, 1200));
    setReconSteps(prev => prev.map((s, i) => i === 1 ? { status: 'done', result: '3 sources' } : s));
    
    // Step 3: Analyze patterns
    setReconSteps(prev => prev.map((s, i) => i === 2 ? { status: 'running', result: '' } : s));
    await new Promise(r => setTimeout(r, 1000));
    setReconSteps(prev => prev.map((s, i) => i === 2 ? { status: 'done', result: '3 patterns' } : s));
    
    // Step 4: Detect gaps
    setReconSteps(prev => prev.map((s, i) => i === 3 ? { status: 'running', result: '' } : s));
    await new Promise(r => setTimeout(r, 1500));
    setReconSteps(prev => prev.map((s, i) => i === 3 ? { status: 'done', result: '2 gaps' } : s));
  };

  // Generate content after reconnaissance
  const generateContent = async () => {
    setPhase('generating');
    
    try {
      const response = await axios.post(
        `${API}/article-optimizer/generate-geo-content`,
        {
          target_question: targetQuestion,
          brand_name: brandName,
          content_type: contentType,
          differentiator: differentiator,
          project_id: project?.project_id
        },
        { withCredentials: true }
      );
      
      setGeneratedContent(response.data);
      setPhase('generated');
    } catch (error) {
      console.error('Error generating content:', error);
      toast.error('Erreur lors de la génération du contenu. Veuillez réessayer.');
      setPhase('input');
    }
  };

  // Copy handlers
  const handleCopy = (content, type) => {
    navigator.clipboard.writeText(content);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
    toast.success('Copié !');
  };

  // Reset to start over
  const reset = () => {
    setPhase('input');
    setReconSteps([
      { status: 'pending', result: '' },
      { status: 'pending', result: '' },
      { status: 'pending', result: '' },
      { status: 'pending', result: '' }
    ]);
    setGeneratedContent(null);
    setTargetQuestion('');
    setDifferentiator('');
  };

  const reconStepsConfig = [
    { title: 'Interroger les LLMs', description: 'Poser la question cible à ChatGPT, Perplexity, Gemini' },
    { title: 'Identifier les sources citées', description: 'GSMArena (3/3), DxOMark (2/3), The Verge (1/3)' },
    { title: 'Analyser les patterns de citation', description: 'Tableaux comparatifs, scores chiffrés, ton neutre' },
    { title: 'Détecter les lacunes exploitables', description: 'Ce que personne ne couvre encore' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900">Générateur de contenu GEO</h2>
        <p className="text-slate-600">
          Créez du contenu pré-optimisé pour être cité par les LLMs — pas juste du contenu générique
        </p>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Input */}
        <Card className="p-6 bg-white border-slate-200">
          <h3 className="font-semibold text-slate-900 mb-4">Étape 1 : Quel contenu ?</h3>
          
          {/* Content Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">Type de contenu</label>
            <select
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              disabled={phase !== 'input'}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent bg-white text-slate-900"
            >
              {CONTENT_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          {/* Target Question */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">Question utilisateur à cibler</label>
            <input
              type="text"
              value={targetQuestion}
              onChange={(e) => setTargetQuestion(e.target.value)}
              disabled={phase !== 'input'}
              placeholder={`"Quel est le meilleur CRM pour PME en 2026 ?"`}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-900"
            />
          </div>

          {/* Brand (from project) */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">Marque / produit à positionner</label>
            <div className="px-4 py-3 bg-violet-50 border border-violet-200 rounded-lg">
              <span className="text-violet-700 font-medium">{brandName}</span>
              <span className="text-violet-500 text-sm ml-2">(depuis le projet)</span>
            </div>
          </div>

          {/* Differentiator */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Angle différenciateur <span className="text-slate-400">(optionnel)</span>
            </label>
            <input
              type="text"
              value={differentiator}
              onChange={(e) => setDifferentiator(e.target.value)}
              disabled={phase !== 'input'}
              placeholder={`ex: "meilleur rapport qualité-prix", "innovation IA"`}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-900"
            />
          </div>
        </Card>

        {/* Right Column - Reconnaissance */}
        <Card className="p-6 bg-slate-50 border-slate-200">
          <h3 className="font-semibold text-slate-900 mb-2">Étape 2 : Reconnaissance du terrain IA</h3>
          <p className="text-sm text-slate-600 mb-4">
            Avant de générer, on analyse ce que les LLMs répondent déjà sur ce sujet
          </p>
          
          <div className="space-y-3">
            {reconStepsConfig.map((config, i) => (
              <ReconnaissanceStep
                key={i}
                step={i + 1}
                status={reconSteps[i].status}
                details={{
                  title: config.title,
                  description: config.description,
                  result: reconSteps[i].result
                }}
              />
            ))}
          </div>

          {phase === 'input' && (
            <div className="mt-6 text-center">
              <ArrowDown className="w-6 h-6 text-slate-400 mx-auto mb-2" />
              <p className="text-sm text-slate-500">
                Cette reconnaissance prend ~30s. Elle garantit que le contenu généré sera calibré pour dépasser les sources actuellement citées.
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Action Button */}
      {phase === 'input' && (
        <Button
          onClick={startReconnaissance}
          className="w-full py-4 bg-violet-600 hover:bg-violet-700 text-white text-lg"
        >
          <Search className="w-5 h-5 mr-2" />
          Lancer la reconnaissance du terrain
        </Button>
      )}

      {phase === 'reconnaissance' && reconSteps.every(s => s.status === 'done') && (
        <Button
          onClick={generateContent}
          className="w-full py-4 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 text-white text-lg"
        >
          <Wand2 className="w-5 h-5 mr-2" />
          Générer le contenu GEO-optimisé
        </Button>
      )}

      {phase === 'generating' && (
        <Card className="p-6 bg-violet-50 border-violet-200">
          <div className="flex items-center justify-center gap-4">
            <Loader2 className="w-6 h-6 text-violet-600 animate-spin" />
            <p className="font-medium text-slate-900">Génération du contenu optimisé...</p>
          </div>
        </Card>
      )}

      {/* Generated Content */}
      {phase === 'generated' && generatedContent && (
        <div className="space-y-6">
          {/* Content Header */}
          <Card className="p-6 bg-white border-slate-200">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Contenu généré</h3>
                <p className="text-sm text-slate-600">
                  Pré-optimisé pour citation IA · Basé sur l'analyse des {generatedContent.sources_analyzed} sources actuellement citées
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Score GEO estimé</p>
                <p className="text-3xl font-bold text-emerald-600">{generatedContent.score}<span className="text-lg text-slate-400">/100</span></p>
              </div>
            </div>

            {/* Citation Strategy */}
            <div className="p-4 bg-slate-50 rounded-xl mb-6">
              <h4 className="font-medium text-slate-900 mb-3">Stratégie de citation choisie par l'IA</h4>
              <div className="flex flex-wrap gap-2">
                {generatedContent.citation_strategy.map((strat, i) => (
                  <StrategyTag key={i} text={strat.text} type={strat.type} />
                ))}
              </div>
            </div>

            {/* Content Preview */}
            <div className="p-6 bg-white border border-slate-200 rounded-xl">
              <h4 className="text-xl font-bold text-slate-900 mb-4">{generatedContent.title}</h4>
              <p className="text-slate-700 leading-relaxed mb-6">{generatedContent.content}</p>
              
              {/* Comparison Table */}
              {generatedContent.comparison_table && (
                <div className="mb-6">
                  <h5 className="font-medium text-slate-700 mb-3">Tableau comparatif intégré</h5>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="bg-slate-50">
                          {generatedContent.comparison_table.headers.map((h, i) => (
                            <th key={i} className="px-4 py-3 text-left text-sm font-semibold text-slate-700 border-b border-slate-200">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {generatedContent.comparison_table.rows.map((row, i) => (
                          <tr key={i} className={i === 0 ? 'bg-emerald-50' : ''}>
                            {row.map((cell, j) => (
                              <td key={j} className={`px-4 py-3 text-sm border-b border-slate-100 ${i === 0 ? 'text-emerald-800 font-medium' : 'text-slate-600'}`}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <p className="text-sm text-slate-600">{generatedContent.content_after_table}</p>
            </div>
          </Card>

          {/* GEO Indicators */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <GeoIndicator
              title="Réponse directe"
              description={generatedContent.geo_indicators.direct_answer.description}
            />
            <GeoIndicator
              title={`${generatedContent.geo_indicators.facts_count.value} faits chiffrés`}
              description={generatedContent.geo_indicators.facts_count.description}
            />
            <GeoIndicator
              title={`${generatedContent.geo_indicators.sources_count.value} sources tierces`}
              description={generatedContent.geo_indicators.sources_count.description}
            />
            <GeoIndicator
              title="Ton neutre"
              description={generatedContent.geo_indicators.neutral_tone.description}
            />
          </div>

          {/* Included Schemas */}
          <Card className="p-4 bg-slate-50 border-slate-200">
            <p className="text-sm text-slate-600 mb-2">Inclus automatiquement dans le contenu :</p>
            <div className="flex flex-wrap gap-2">
              {generatedContent.included_schemas.map((schema, i) => (
                <Badge key={i} variant="outline" className="bg-white">
                  {schema}
                </Badge>
              ))}
            </div>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => handleCopy(generatedContent.full_article, 'full')}
              className="flex-1 py-4 bg-violet-600 hover:bg-violet-700 text-white"
            >
              {copied === 'full' ? <Check className="w-5 h-5 mr-2" /> : <Copy className="w-5 h-5 mr-2" />}
              Copier l'article complet
            </Button>
            <Button
              variant="outline"
              onClick={() => handleCopy(`<!-- HTML + Schema -->\n${generatedContent.full_article}`, 'html')}
              className="border-slate-200"
            >
              {copied === 'html' ? <Check className="w-4 h-4 mr-2" /> : <FileCode className="w-4 h-4 mr-2" />}
              HTML + Schema
            </Button>
            <Button
              variant="outline"
              onClick={() => handleCopy(generatedContent.full_article, 'md')}
              className="border-slate-200"
            >
              {copied === 'md' ? <Check className="w-4 h-4 mr-2" /> : <FileText className="w-4 h-4 mr-2" />}
              Markdown
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                onSendToOptimizer?.(generatedContent);
                toast.success('Envoyé vers l\'Optimiseur !');
              }}
              className="border-violet-200 text-violet-700 hover:bg-violet-50"
            >
              <Send className="w-4 h-4 mr-2" />
              Envoyer vers Optimiseur
            </Button>
          </div>

          {/* New Generation Button */}
          <Button variant="outline" onClick={reset} className="w-full">
            <RefreshCw className="w-4 h-4 mr-2" />
            Générer un autre contenu
          </Button>
        </div>
      )}
    </div>
  );
});

GenerateMode.displayName = 'GenerateMode';

// Header Component for Optimize Mode
const OptimizerHeader = memo(({ analysis, project }) => {
  const citedCount = useMemo(() => {
    if (!analysis?.query_scores) return { cited: 0, total: 0 };
    const engines = new Set();
    let cited = 0;
    analysis.query_scores.forEach(q => {
      q.responses?.forEach(r => {
        engines.add(r.ai_type);
        if (r.brand_mentioned) cited++;
      });
    });
    return { 
      cited: Math.round((cited / Math.max(analysis.query_scores.length * 3, 1)) * engines.size),
      total: engines.size 
    };
  }, [analysis]);

  return (
    <Card className="p-6 bg-gradient-to-br from-slate-50 to-violet-50 border-slate-200 rounded-xl">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="flex-1">
          <p className="text-sm text-slate-500 mb-1">Optimiseur GEO — résultats automatiques</p>
          <h2 className="text-xl font-bold text-slate-900 mb-1">
            {analysis?.analysis_summary?.target_query || project?.keywords?.[0] || 'Analyse GEO'}
          </h2>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <a 
              href={project?.website_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-violet-600 hover:underline flex items-center gap-1"
            >
              {project?.website_url?.replace(/^https?:\/\//, '').substring(0, 40)}
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>·</span>
            <span>Audit du {new Date(analysis?.created_at).toLocaleDateString('fr-FR')}</span>
          </div>
        </div>
        
        <div className="text-right">
          <p className="text-sm text-slate-500 mb-1">Score GEO actuel</p>
          <p className="text-4xl font-bold">
            <span className={analysis?.global_score >= 50 ? 'text-emerald-500' : 'text-red-500'}>
              {Math.round(analysis?.global_score || 0)}
            </span>
            <span className="text-slate-400 text-xl">/100</span>
          </p>
          <p className="text-sm text-slate-500 mt-1">
            Cité {citedCount.cited}/{citedCount.total} LLMs
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
        <DiagnosticBadge 
          label="Réponse directe" 
          value={analysis?.indices?.direct_answer ? "Présente" : "Absente"}
          status={analysis?.indices?.direct_answer ? "good" : "bad"}
        />
        <DiagnosticBadge 
          label="Données vérifiables" 
          value={`${analysis?.indices?.verifiable_facts || 0} faits`}
          status={(analysis?.indices?.verifiable_facts || 0) >= 5 ? "good" : "warning"}
        />
        <DiagnosticBadge 
          label="Ton" 
          value={analysis?.indices?.tone || "Promotionnel"}
          status={analysis?.indices?.tone === "Expert" ? "good" : "warning"}
        />
        <DiagnosticBadge 
          label="Expertise technique" 
          value={analysis?.indices?.technical_expertise || "Moyenne"}
          status={analysis?.indices?.technical_expertise === "Forte" ? "good" : "warning"}
        />
      </div>
    </Card>
  );
});

OptimizerHeader.displayName = 'OptimizerHeader';

// Tab Navigation
const TabNavigation = memo(({ activeTab, onTabChange }) => (
  <div className="flex gap-1 p-1 bg-slate-100 rounded-xl overflow-x-auto">
    {TABS.map(tab => (
      <button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
          activeTab === tab.id
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
        }`}
      >
        <tab.icon className="w-4 h-4" />
        {tab.label}
      </button>
    ))}
  </div>
));

TabNavigation.displayName = 'TabNavigation';

// Main Optimizer Page
export default function ArticleOptimizerPage() {
  const navigate = useNavigate();
  const { currentProject } = useAuth();
  
  const [mode, setMode] = useState('generate'); // Default to generate mode for demo
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [optimizations, setOptimizations] = useState(null);
  const [activeTab, setActiveTab] = useState('rewrites');
  const [copied, setCopied] = useState(false);

  // Fetch latest analysis for optimize mode
  useEffect(() => {
    if (currentProject && mode === 'optimize') {
      fetchLatestAnalysis();
    }
  }, [currentProject, mode]);

  const fetchLatestAnalysis = useCallback(async () => {
    if (!currentProject) return;
    setLoading(true);
    
    try {
      const response = await axios.get(
        `${API}/projects/${currentProject.project_id}/analyses?status=completed`,
        { withCredentials: true }
      );
      
      const analyses = response.data.analyses || [];
      if (analyses.length > 0) {
        const detailResponse = await axios.get(
          `${API}/analysis/${analyses[0].analysis_id}`,
          { withCredentials: true }
        );
        setAnalysis(detailResponse.data.analysis);
        await generateOptimizations(detailResponse.data.analysis);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  const generateOptimizations = useCallback(async (analysisData) => {
    setGenerating(true);
    
    try {
      const response = await axios.post(
        `${API}/article-optimizer/generate-from-analysis`,
        { 
          analysis_id: analysisData.analysis_id,
          project_id: currentProject?.project_id
        },
        { withCredentials: true }
      );
      setOptimizations(response.data);
    } catch (error) {
      console.error('Error generating optimizations:', error);
      toast.error('Erreur lors de la génération des optimisations');
      setOptimizations(null);
    } finally {
      setGenerating(false);
    }
  }, [currentProject]);

  const handleCopyAll = useCallback(() => {
    if (!optimizations?.rewrites) return;
    const allContent = optimizations.rewrites
      .map((r) => `--- ${r.section} ---\n${r.optimized}`)
      .join('\n\n');
    navigator.clipboard.writeText(allContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Contenu optimisé copié !');
  }, [optimizations]);

  const handleSendToOptimizer = (content) => {
    // Switch to optimize mode with the generated content
    setMode('optimize');
    toast.info('Vous pouvez maintenant suivre la performance de ce contenu');
  };

  // Loading state
  if (loading && mode === 'optimize') {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <div className="w-12 h-12 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin mx-auto" />
            <p className="text-slate-600">Chargement de l'analyse...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="article-optimizer-page">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/25">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Optimiseur GEO</h1>
            <p className="text-sm text-slate-600">
              Optimisez un article existant ou créez du contenu GEO-ready
            </p>
          </div>
        </div>

        {/* Mode Toggle */}
        <ModeToggle mode={mode} onModeChange={setMode} />

        {/* GENERATE MODE */}
        {mode === 'generate' && (
          <GenerateMode 
            project={currentProject} 
            onSendToOptimizer={handleSendToOptimizer}
          />
        )}

        {/* OPTIMIZE MODE */}
        {mode === 'optimize' && (
          <>
            {!analysis ? (
              <Card className="p-8 text-center bg-slate-50 border-slate-200">
                <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Aucune analyse disponible</h3>
                <p className="text-slate-600 mb-6">
                  Lancez d'abord une analyse GEO pour obtenir des optimisations.
                </p>
                <div className="flex justify-center gap-3">
                  <Link to="/analysis">
                    <Button className="bg-gradient-to-r from-violet-600 to-cyan-600">
                      <Sparkles className="w-4 h-4 mr-2" />
                      Lancer une analyse
                    </Button>
                  </Link>
                  <Button variant="outline" onClick={() => setMode('generate')}>
                    <Wand2 className="w-4 h-4 mr-2" />
                    Créer du contenu
                  </Button>
                </div>
              </Card>
            ) : (
              <>
                <OptimizerHeader analysis={analysis} project={currentProject} />

                {generating && (
                  <Card className="p-6 bg-violet-50 border-violet-200">
                    <div className="flex items-center gap-4">
                      <Loader2 className="w-6 h-6 text-violet-600 animate-spin" />
                      <p className="font-medium text-slate-900">Génération des optimisations...</p>
                    </div>
                  </Card>
                )}

                {optimizations && !generating && (
                  <>
                    <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

                    <div className="space-y-4">
                      {activeTab === 'rewrites' && (
                        <>
                          <p className="text-slate-600">
                            Paragraphes réécrits pour maximiser la citabilité IA
                          </p>
                          {optimizations.rewrites?.map((rewrite, idx) => (
                            <RewriteCard key={idx} rewrite={rewrite} index={idx} />
                          ))}
                          <Button
                            onClick={handleCopyAll}
                            className="w-full py-4 bg-violet-600 hover:bg-violet-700 text-white"
                          >
                            {copied ? <Check className="w-5 h-5 mr-2" /> : <Copy className="w-5 h-5 mr-2" />}
                            {copied ? 'Copié !' : 'Copier tout l\'article optimisé'}
                          </Button>
                        </>
                      )}

                      {activeTab === 'missing' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {optimizations.missing_contents?.map((content, idx) => (
                            <MissingContentCard key={idx} content={content} />
                          ))}
                        </div>
                      )}

                      {activeTab === 'sources' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {optimizations.competitor_sources?.map((source, idx) => (
                            <CompetitorSourceCard key={idx} source={source} />
                          ))}
                        </div>
                      )}

                      {activeTab === 'schema' && (
                        <div className="space-y-4">
                          {optimizations.schemas?.map((schema, idx) => (
                            <SchemaMarkupCard key={idx} schema={schema} />
                          ))}
                        </div>
                      )}
                    </div>

                    <ProjectedScoreCard 
                      currentScore={optimizations.current_score}
                      projectedScore={optimizations.projected_score}
                      improvements={{
                        rewrites: optimizations.rewrites?.length || 0,
                        contents: optimizations.missing_contents?.length || 0
                      }}
                    />
                  </>
                )}
              </>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
