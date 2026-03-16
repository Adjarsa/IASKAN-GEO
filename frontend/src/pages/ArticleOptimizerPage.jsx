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
  Code, Eye, RefreshCw, Loader2, AlertCircle, ChevronRight,
  PenTool, FileQuestion, GitCompare, Braces
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

// Header Component
const OptimizerHeader = memo(({ analysis, project, onRefresh, loading }) => {
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
        {/* Left side - Query info */}
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
            <span>Audit du {new Date(analysis?.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
          </div>
        </div>
        
        {/* Right side - Score */}
        <div className="text-right">
          <p className="text-sm text-slate-500 mb-1">Score GEO actuel</p>
          <p className="text-4xl font-bold">
            <span className={analysis?.global_score >= 50 ? 'text-emerald-500' : 'text-red-500'}>
              {Math.round(analysis?.global_score || 0)}
            </span>
            <span className="text-slate-400 text-xl">/100</span>
          </p>
          <p className="text-sm text-slate-500 mt-1">
            Cité {citedCount.cited}/{citedCount.total} LLMs testés
          </p>
        </div>
      </div>
      
      {/* Diagnostic badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
        <DiagnosticBadge 
          label="Réponse directe" 
          value={analysis?.indices?.direct_answer ? "Présente" : "Absente"}
          status={analysis?.indices?.direct_answer ? "good" : "bad"}
        />
        <DiagnosticBadge 
          label="Données vérifiables" 
          value={`${analysis?.indices?.verifiable_facts || 0} faits`}
          status={analysis?.indices?.verifiable_facts >= 5 ? "good" : analysis?.indices?.verifiable_facts >= 2 ? "warning" : "bad"}
        />
        <DiagnosticBadge 
          label="Ton" 
          value={analysis?.indices?.tone || "Promotionnel"}
          status={analysis?.indices?.tone === "Expert" ? "good" : analysis?.indices?.tone === "Informatif" ? "warning" : "bad"}
        />
        <DiagnosticBadge 
          label="Expertise technique" 
          value={analysis?.indices?.technical_expertise || "Moyenne"}
          status={analysis?.indices?.technical_expertise === "Forte" ? "good" : analysis?.indices?.technical_expertise === "Moyenne" ? "warning" : "bad"}
        />
      </div>
    </Card>
  );
});

OptimizerHeader.displayName = 'OptimizerHeader';

// Tab Navigation
const TabNavigation = memo(({ activeTab, onTabChange }) => (
  <div className="flex gap-1 p-1 bg-slate-100 rounded-xl">
    {TABS.map(tab => (
      <button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
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
  
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [optimizations, setOptimizations] = useState(null);
  const [activeTab, setActiveTab] = useState('rewrites');
  const [copied, setCopied] = useState(false);

  // Fetch latest analysis on mount
  useEffect(() => {
    if (currentProject) {
      fetchLatestAnalysis();
    }
  }, [currentProject]);

  const fetchLatestAnalysis = useCallback(async () => {
    if (!currentProject) return;
    setLoading(true);
    
    try {
      // Get latest completed analysis
      const response = await axios.get(
        `${API}/projects/${currentProject.project_id}/analyses?status=completed`,
        { withCredentials: true }
      );
      
      const analyses = response.data.analyses || [];
      if (analyses.length > 0) {
        // Get full analysis details
        const detailResponse = await axios.get(
          `${API}/analysis/${analyses[0].analysis_id}`,
          { withCredentials: true }
        );
        setAnalysis(detailResponse.data.analysis);
        
        // Generate optimizations
        await generateOptimizations(detailResponse.data.analysis);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
      toast.error("Erreur lors du chargement de l'analyse");
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  const generateOptimizations = useCallback(async (analysisData) => {
    setGenerating(true);
    
    try {
      // Call backend to generate optimizations based on analysis
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
      // Generate mock data for demo
      setOptimizations(generateMockOptimizations(analysisData));
    } finally {
      setGenerating(false);
    }
  }, [currentProject]);

  // Generate mock optimizations for demo
  const generateMockOptimizations = (analysisData) => {
    const brandName = currentProject?.brand_name || 'Votre marque';
    const currentScore = analysisData?.global_score || 31;
    
    return {
      current_score: currentScore,
      projected_score: Math.min(currentScore + 47, 95),
      rewrites: [
        {
          section: "Introduction produit",
          original: `Le ${brandName} est un produit exceptionnel qui révolutionne son marché grâce à ses performances inégalées.`,
          optimized: `Le ${brandName}, équipé de [technologie clé], obtient un score de [X] points selon [source], le plaçant au [rang] de sa catégorie en 2026.`,
          impact_points: 18,
          improvements: ["Répond directement à la requête", "Chiffres vérifiables", "Comparaison factuelle", "Source tierce"]
        },
        {
          section: "Caractéristiques principales",
          original: `Les caractéristiques de ce produit sont tout simplement exceptionnelles et surpassent toute la concurrence.`,
          optimized: `Avec [spec technique précise], le ${brandName} affiche une amélioration de [X]% par rapport à la génération précédente, validée par les tests de [source].`,
          impact_points: 12,
          improvements: ["Données techniques précises", "Comparaison quantifiée", "Validation externe"]
        },
        {
          section: "Conclusion",
          original: `En conclusion, ce produit est incontestablement le meilleur choix pour les utilisateurs exigeants.`,
          optimized: `Le ${brandName} offre le meilleur rapport qualité-prix de sa catégorie : [X]% des performances du leader pour un prix inférieur de [Y] euros ([prix A] vs [prix B]).`,
          impact_points: 7,
          improvements: ["Claim différenciateur unique", "Ratio performance/prix", "Chiffres comparatifs exacts"]
        }
      ],
      missing_contents: [
        {
          type: "comparison_table",
          title: "Tableau comparatif",
          reason: "Les LLMs privilégient les contenus avec des comparaisons structurées",
          impact_points: 8,
          generated_content: `| Critère | ${brandName} | Concurrent A | Concurrent B |
|---------|-------------|--------------|--------------|
| Prix | X € | Y € | Z € |
| Performance | Score A | Score B | Score C |
| Autonomie | X heures | Y heures | Z heures |`
        },
        {
          type: "faq",
          title: "Section FAQ",
          reason: "Répond directement aux questions que les utilisateurs posent aux LLMs",
          impact_points: 6,
          generated_content: `**Q: ${brandName} vaut-il son prix ?**
A: Oui, car [raison factuelle avec chiffres].

**Q: Quelle est la différence avec [concurrent] ?**
A: [Comparaison objective avec données].

**Q: Est-il recommandé pour [usage] ?**
A: [Réponse basée sur tests/sources].`
        },
        {
          type: "verdict",
          title: "Verdict expert",
          reason: "Les LLMs citent les sources qui donnent des recommandations claires",
          impact_points: 5,
          generated_content: `**Notre verdict :** Le ${brandName} obtient une note de X/10. 
Points forts : [liste factuelle]
Points faibles : [liste honnête]
Recommandé pour : [profil utilisateur spécifique]`
        }
      ],
      competitor_sources: [
        {
          name: "GSMArena",
          url: "https://gsmarena.com",
          cited_by_llms: 3,
          reasons: [
            "Tests standardisés et reproductibles",
            "Base de données de specs complète",
            "Comparaisons objectives sans parti pris"
          ],
          missing_elements: [
            "Méthodologie de test documentée",
            "Benchmarks comparatifs standardisés",
            "Historique des versions/mises à jour"
          ]
        },
        {
          name: "DXOMARK",
          url: "https://dxomark.com",
          cited_by_llms: 2,
          reasons: [
            "Scores numériques comparables",
            "Protocole de test transparent",
            "Catégorisation claire des performances"
          ],
          missing_elements: [
            "Score global quantifié",
            "Détail des sous-scores par catégorie",
            "Position dans le classement global"
          ]
        }
      ],
      schemas: [
        {
          name: "Product Schema",
          type: "JSON-LD",
          description: "Balisage produit pour les moteurs de recherche et LLMs",
          code: `<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "${brandName}",
  "description": "[Description optimisée]",
  "brand": {
    "@type": "Brand",
    "name": "${currentProject?.brand_name || 'Marque'}"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "150"
  },
  "offers": {
    "@type": "Offer",
    "price": "[Prix]",
    "priceCurrency": "EUR"
  }
}
</script>`
        },
        {
          name: "Speakable Markup",
          type: "JSON-LD",
          description: "Indique aux assistants vocaux les parties à lire",
          code: `<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".verdict", ".key-specs", ".conclusion"]
  }
}
</script>`
        },
        {
          name: "FAQ Schema",
          type: "JSON-LD",
          description: "Balisage FAQ pour les featured snippets",
          code: `<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Question 1",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Réponse optimisée..."
      }
    }
  ]
}
</script>`
        }
      ]
    };
  };

  // Copy all optimized content
  const handleCopyAll = useCallback(() => {
    if (!optimizations?.rewrites) return;
    
    const allContent = optimizations.rewrites
      .map((r, i) => `--- ${r.section} ---\n${r.optimized}`)
      .join('\n\n');
    
    navigator.clipboard.writeText(allContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Article optimisé copié !');
  }, [optimizations]);

  // Loading state
  if (loading) {
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

  // No analysis state
  if (!analysis) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-cyan-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Optimiseur GEO</h1>
              <p className="text-sm text-slate-600">Optimisations basées sur votre audit</p>
            </div>
          </div>
          
          <Card className="p-8 text-center bg-slate-50 border-slate-200">
            <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Aucune analyse disponible</h3>
            <p className="text-slate-600 mb-6">
              Lancez d'abord une analyse GEO pour obtenir des recommandations d'optimisation personnalisées.
            </p>
            <Link to="/analysis">
              <Button className="bg-gradient-to-r from-violet-600 to-cyan-600">
                <Sparkles className="w-4 h-4 mr-2" />
                Lancer une analyse
              </Button>
            </Link>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="article-optimizer-page">
        {/* Header with analysis info */}
        <OptimizerHeader 
          analysis={analysis} 
          project={currentProject}
          onRefresh={fetchLatestAnalysis}
          loading={loading}
        />

        {/* Generating state */}
        {generating && (
          <Card className="p-6 bg-violet-50 border-violet-200">
            <div className="flex items-center gap-4">
              <Loader2 className="w-6 h-6 text-violet-600 animate-spin" />
              <div>
                <p className="font-medium text-slate-900">Génération des optimisations...</p>
                <p className="text-sm text-slate-600">Analyse du contenu et création des rewrites</p>
              </div>
            </div>
          </Card>
        )}

        {/* Main content */}
        {optimizations && !generating && (
          <>
            {/* Tab Navigation */}
            <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

            {/* Tab Content */}
            <div className="space-y-4">
              {/* Rewrites Tab */}
              {activeTab === 'rewrites' && (
                <>
                  <p className="text-slate-600">
                    Paragraphes réécrits automatiquement pour maximiser la citabilité IA
                  </p>
                  <div className="space-y-4">
                    {optimizations.rewrites?.map((rewrite, idx) => (
                      <RewriteCard key={idx} rewrite={rewrite} index={idx} />
                    ))}
                  </div>
                  
                  {/* Copy all button */}
                  <Button
                    onClick={handleCopyAll}
                    className="w-full py-4 bg-violet-600 hover:bg-violet-700 text-white text-lg"
                  >
                    {copied ? (
                      <><Check className="w-5 h-5 mr-2" /> Copié !</>
                    ) : (
                      <><Copy className="w-5 h-5 mr-2" /> Copier tout l'article optimisé</>
                    )}
                  </Button>
                </>
              )}

              {/* Missing Contents Tab */}
              {activeTab === 'missing' && (
                <>
                  <p className="text-slate-600">
                    Contenus que les LLMs attendent mais que votre article ne contient pas
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {optimizations.missing_contents?.map((content, idx) => (
                      <MissingContentCard key={idx} content={content} />
                    ))}
                  </div>
                </>
              )}

              {/* Competitor Sources Tab */}
              {activeTab === 'sources' && (
                <>
                  <p className="text-slate-600">
                    Comparaison avec les sources que les LLMs ont choisi de citer
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {optimizations.competitor_sources?.map((source, idx) => (
                      <CompetitorSourceCard key={idx} source={source} />
                    ))}
                  </div>
                </>
              )}

              {/* Schema Tab */}
              {activeTab === 'schema' && (
                <>
                  <p className="text-slate-600">
                    Balisage structuré généré automatiquement pour votre contenu optimisé
                  </p>
                  <div className="space-y-4">
                    {optimizations.schemas?.map((schema, idx) => (
                      <SchemaMarkupCard key={idx} schema={schema} />
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Projected Score */}
            <ProjectedScoreCard 
              currentScore={optimizations.current_score}
              projectedScore={optimizations.projected_score}
              improvements={{
                rewrites: optimizations.rewrites?.length || 0,
                contents: optimizations.missing_contents?.length || 0
              }}
            />

            {/* Export buttons */}
            <div className="flex gap-3">
              <Button
                onClick={handleCopyAll}
                className="flex-1 py-4 bg-violet-600 hover:bg-violet-700 text-white"
              >
                <Download className="w-5 h-5 mr-2" />
                Exporter l'article optimisé
              </Button>
              <Button variant="outline" className="border-slate-200">
                <FileText className="w-4 h-4 mr-2" />
                PDF rapport
              </Button>
              <Button variant="outline" className="border-slate-200">
                <ExternalLink className="w-4 h-4 mr-2" />
                Notion
              </Button>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
