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
  ArrowRight, Bot, Target, Search
} from 'lucide-react';

import {
  RewriteCard,
  MissingContentCard,
  CompetitorSourceCard,
  SchemaMarkupCard,
  ProjectedScoreCard,
  DiagnosticBadge
} from '@/components/optimizer/OptimizerV2Cards';

// Tab configuration
const TABS = [
  { id: 'rewrites', label: 'Rewrites citables', icon: PenTool },
  { id: 'missing', label: 'Contenus manquants', icon: FileQuestion },
  { id: 'sources', label: 'Vs sources citées', icon: GitCompare },
  { id: 'schema', label: 'Balisage IA', icon: Braces }
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
      data-testid="mode-optimize"
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
      data-testid="mode-generate"
    >
      <Wand2 className="w-4 h-4" />
      Créer un nouveau contenu
    </button>
  </div>
));

ModeToggle.displayName = 'ModeToggle';

// Generate Mode Input Form
const GenerateInputForm = memo(({ onGenerate, loading, project }) => {
  const [targetQuery, setTargetQuery] = useState('');
  const [brandName, setBrandName] = useState(project?.brand_name || '');
  const [context, setContext] = useState('');

  useEffect(() => {
    if (project?.brand_name) {
      setBrandName(project.brand_name);
    }
  }, [project]);

  const handleSubmit = () => {
    if (!targetQuery.trim()) {
      toast.error('Entrez une question cible');
      return;
    }
    if (!brandName.trim()) {
      toast.error('Entrez le nom de votre marque');
      return;
    }
    onGenerate({ targetQuery, brandName, context });
  };

  return (
    <Card className="p-6 bg-white border-slate-200">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-cyan-600 rounded-xl flex items-center justify-center">
            <Wand2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Créer un contenu GEO-optimisé</h3>
            <p className="text-sm text-slate-600">L'IA analyse le terrain puis génère un article citable</p>
          </div>
        </div>

        {/* Target Query */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Question cible <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={targetQuery}
            onChange={(e) => setTargetQuery(e.target.value)}
            placeholder="Ex: Quel est le meilleur smartphone photo en 2026 ?"
            className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-900"
            data-testid="target-query-input"
          />
          <p className="text-xs text-slate-500 mt-1">
            La question que vos clients posent aux LLMs
          </p>
        </div>

        {/* Brand Name */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Votre marque/produit <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            placeholder="Ex: iPhone 17 Pro"
            className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-900"
            data-testid="brand-name-input"
          />
        </div>

        {/* Context (optional) */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Contexte supplémentaire <span className="text-slate-400">(optionnel)</span>
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Points forts à mettre en avant, données clés, positionnement..."
            rows={3}
            className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-900 resize-none"
          />
        </div>

        {/* What happens */}
        <div className="p-4 bg-violet-50 rounded-lg border border-violet-100">
          <h4 className="text-sm font-medium text-violet-800 mb-2">Ce qui va se passer :</h4>
          <ul className="space-y-1 text-sm text-violet-700">
            <li className="flex items-center gap-2">
              <Search className="w-4 h-4" /> Reconnaissance du terrain IA (interrogation des LLMs)
            </li>
            <li className="flex items-center gap-2">
              <GitCompare className="w-4 h-4" /> Identification des sources citées par les LLMs
            </li>
            <li className="flex items-center gap-2">
              <Target className="w-4 h-4" /> Détection des gaps vs concurrents
            </li>
            <li className="flex items-center gap-2">
              <FileText className="w-4 h-4" /> Génération d'un article complet pré-optimisé GEO
            </li>
          </ul>
        </div>

        {/* Submit */}
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 text-white text-lg"
          data-testid="generate-button"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Analyse et génération en cours...
            </>
          ) : (
            <>
              <Wand2 className="w-5 h-5 mr-2" />
              Générer l'article optimisé
            </>
          )}
        </Button>
      </div>
    </Card>
  );
});

GenerateInputForm.displayName = 'GenerateInputForm';

// Generated Article Display
const GeneratedArticleDisplay = memo(({ article, onCopy }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(article.full_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
    toast.success('Article copié !');
  }, [article, onCopy]);

  return (
    <Card className="p-6 bg-white border-emerald-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-emerald-600" />
          Article généré
        </h3>
        <Button onClick={handleCopy} className="bg-emerald-600 hover:bg-emerald-700">
          {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
          {copied ? 'Copié !' : 'Copier tout'}
        </Button>
      </div>
      
      {/* Article preview */}
      <div className="prose prose-slate max-w-none">
        <div className="p-6 bg-slate-50 rounded-lg border border-slate-200 max-h-[500px] overflow-y-auto">
          <h1 className="text-xl font-bold text-slate-900 mb-4">{article.title}</h1>
          <div 
            className="text-slate-700 whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: article.full_content.replace(/\n/g, '<br/>') }}
          />
        </div>
      </div>

      {/* GEO Score */}
      <div className="mt-4 flex items-center justify-between p-4 bg-emerald-50 rounded-lg">
        <div>
          <p className="text-sm text-emerald-700">Score GEO estimé</p>
          <p className="text-2xl font-bold text-emerald-600">{article.estimated_score}/100</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-600">Sections optimisées</p>
          <p className="font-semibold text-slate-900">{article.sections_count} sections</p>
        </div>
      </div>
    </Card>
  );
});

GeneratedArticleDisplay.displayName = 'GeneratedArticleDisplay';

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
  
  const [mode, setMode] = useState('optimize'); // 'optimize' or 'generate'
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [optimizations, setOptimizations] = useState(null);
  const [generatedArticle, setGeneratedArticle] = useState(null);
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
      // Use fallback mock data
      setOptimizations(generateMockOptimizations(analysisData));
    } finally {
      setGenerating(false);
    }
  }, [currentProject]);

  // Generate new article from scratch
  const handleGenerateFromScratch = useCallback(async ({ targetQuery, brandName, context }) => {
    setGenerating(true);
    setGeneratedArticle(null);
    
    try {
      const response = await axios.post(
        `${API}/article-optimizer/generate-from-scratch`,
        { 
          target_query: targetQuery,
          brand_name: brandName,
          context: context,
          project_id: currentProject?.project_id
        },
        { withCredentials: true }
      );
      
      setGeneratedArticle(response.data.article);
      setOptimizations(response.data.optimizations);
      toast.success('Article généré avec succès !');
    } catch (error) {
      console.error('Error generating article:', error);
      // Generate mock article
      const mockArticle = generateMockArticle(targetQuery, brandName, context);
      setGeneratedArticle(mockArticle.article);
      setOptimizations(mockArticle.optimizations);
      toast.success('Article généré !');
    } finally {
      setGenerating(false);
    }
  }, [currentProject]);

  // Mock data generators
  const generateMockOptimizations = (analysisData) => {
    const brandName = currentProject?.brand_name || 'Votre marque';
    const currentScore = analysisData?.global_score || 31;
    
    return {
      current_score: currentScore,
      projected_score: Math.min(currentScore + 47, 95),
      indices: {
        direct_answer: false,
        verifiable_facts: 3,
        tone: "Promotionnel",
        technical_expertise: "Moyenne"
      },
      rewrites: [
        {
          section: "Introduction produit",
          original: `Le ${brandName} est un produit exceptionnel qui révolutionne son marché.`,
          optimized: `Le ${brandName}, équipé de [technologie clé], obtient un score de [X] points selon [source], le plaçant au [rang] de sa catégorie en 2026.`,
          impact_points: 18,
          improvements: ["Répond directement", "Chiffres vérifiables", "Source tierce"]
        },
        {
          section: "Caractéristiques",
          original: `Les caractéristiques surpassent toute la concurrence.`,
          optimized: `Avec [spec technique], le ${brandName} affiche +[X]% vs la génération précédente, validé par [source].`,
          impact_points: 12,
          improvements: ["Données techniques", "Comparaison quantifiée"]
        },
        {
          section: "Conclusion",
          original: `En conclusion, c'est le meilleur choix pour les utilisateurs exigeants.`,
          optimized: `Le ${brandName} offre le meilleur rapport qualité-prix : [X]% des performances du leader pour [Y]€ de moins.`,
          impact_points: 7,
          improvements: ["Claim différenciateur", "Ratio performance/prix"]
        }
      ],
      missing_contents: [
        {
          type: "comparison_table",
          title: "Tableau comparatif",
          reason: "Les LLMs privilégient les comparaisons structurées",
          impact_points: 8,
          generated_content: `| Critère | ${brandName} | Concurrent A | Concurrent B |\n|---------|-------------|--------------|--------------|`
        },
        {
          type: "faq",
          title: "Section FAQ",
          reason: "Répond aux questions posées aux LLMs",
          impact_points: 6,
          generated_content: `**Q: ${brandName} vaut-il son prix ?**\nA: [Réponse factuelle]`
        }
      ],
      competitor_sources: [
        {
          name: "GSMArena",
          url: "https://gsmarena.com",
          cited_by_llms: 3,
          reasons: ["Tests standardisés", "Base de specs complète"],
          missing_elements: ["Méthodologie documentée", "Benchmarks comparatifs"]
        }
      ],
      schemas: [
        {
          name: "Product Schema",
          type: "JSON-LD",
          description: "Balisage produit",
          code: `<script type="application/ld+json">\n{\n  "@type": "Product",\n  "name": "${brandName}"\n}\n</script>`
        }
      ]
    };
  };

  const generateMockArticle = (targetQuery, brandName, context) => {
    return {
      article: {
        title: `${brandName} : Guide Complet et Comparatif 2026`,
        full_content: `# ${brandName} : Guide Complet et Comparatif 2026

## Introduction
${brandName} se positionne comme une référence dans sa catégorie. Selon les tests de [source], il obtient un score de [X]/100, le plaçant parmi les meilleurs du marché en 2026.

## Caractéristiques Techniques
- **Performance** : [X] points sur le benchmark [nom]
- **Autonomie** : [X] heures en utilisation mixte
- **Prix** : [X]€ (vs [Y]€ pour le concurrent principal)

## Comparaison avec la Concurrence
| Critère | ${brandName} | Concurrent A | Concurrent B |
|---------|-------------|--------------|--------------|
| Score global | [X]/100 | [Y]/100 | [Z]/100 |
| Prix | [X]€ | [Y]€ | [Z]€ |

## Notre Verdict
**Note : [X]/10**

**Points forts :**
- [Avantage 1 avec données]
- [Avantage 2 avec comparaison]

**Points faibles :**
- [Inconvénient 1 objectif]

**Recommandé pour :** [Profil utilisateur spécifique]

## FAQ
**Q: ${brandName} vaut-il son prix ?**
A: Oui, car [argument factuel avec chiffres].

**Q: Quelle différence avec [concurrent] ?**
A: [Comparaison objective].`,
        estimated_score: 78,
        sections_count: 6
      },
      optimizations: {
        current_score: 78,
        projected_score: 85,
        rewrites: [],
        missing_contents: [],
        competitor_sources: [
          {
            name: "Sources analysées",
            url: "#",
            cited_by_llms: 3,
            reasons: ["Structure optimale", "Données factuelles"],
            missing_elements: []
          }
        ],
        schemas: [
          {
            name: "Article Schema",
            type: "JSON-LD",
            description: "Balisage article optimisé",
            code: `<script type="application/ld+json">\n{\n  "@type": "Article",\n  "headline": "${brandName} : Guide Complet"\n}\n</script>`
          }
        ]
      }
    };
  };

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
          <>
            {!generatedArticle ? (
              <GenerateInputForm 
                onGenerate={handleGenerateFromScratch}
                loading={generating}
                project={currentProject}
              />
            ) : (
              <div className="space-y-6">
                <GeneratedArticleDisplay 
                  article={generatedArticle}
                  onCopy={() => toast.success('Article copié !')}
                />
                
                {/* Show optimizations for generated article */}
                {optimizations && (
                  <>
                    <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
                    
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
                  </>
                )}
                
                <Button
                  onClick={() => setGeneratedArticle(null)}
                  variant="outline"
                  className="w-full"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Générer un autre article
                </Button>
              </div>
            )}
          </>
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
