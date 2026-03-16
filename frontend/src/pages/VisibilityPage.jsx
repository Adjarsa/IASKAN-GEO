import { useState, useEffect, useMemo, useCallback, memo } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Eye, Bot, TrendingUp, TrendingDown, Award, Target, BarChart3,
  RefreshCw, Sparkles, ArrowUp, ArrowDown, Minus, Info, Shield,
  Filter, Search, Crown, Medal, ChevronDown
} from "lucide-react";

import {
  BrandLogo,
  PositionBadge,
  AIEngineIcon,
  QueryAnalysisCard,
  SemanticAnalysisCard
} from "@/components/visibility";

// AI Engine Score Card
const AIEngineScoreCard = memo(({ engine, metrics, brandName }) => {
  const getTrendIcon = (trend) => {
    if (trend === "up") return <ArrowUp className="w-4 h-4 text-emerald-500" />;
    if (trend === "down") return <ArrowDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  const engineConfigs = {
    chatgpt: { bg: "bg-emerald-100", icon: "text-emerald-600" },
    openai: { bg: "bg-emerald-100", icon: "text-emerald-600" },
    claude: { bg: "bg-orange-100", icon: "text-orange-600" },
    gemini: { bg: "bg-blue-100", icon: "text-blue-600" },
    perplexity: { bg: "bg-purple-100", icon: "text-purple-600" }
  };

  const config = engineConfigs[engine.toLowerCase()] || { bg: "bg-slate-100", icon: "text-slate-600" };

  return (
    <Card className="p-5 bg-white border-slate-100 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${config.bg}`}>
          <Bot className={`w-5 h-5 ${config.icon}`} />
        </div>
        {getTrendIcon(metrics.trend)}
      </div>
      <h4 className="text-sm font-medium text-slate-700 capitalize mb-2">{engine}</h4>
      <p className={`text-3xl font-bold ${getScoreColor(metrics.score)}`}>{metrics.score}</p>
      <div className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between text-slate-600">
          <span>Position moyenne</span>
          <span className="font-medium text-slate-900">#{metrics.position_avg?.toFixed(1) || '-'}</span>
        </div>
        <div className="flex justify-between text-slate-600">
          <span>Taux de mention</span>
          <span className="font-medium text-slate-900">{metrics.mention_rate || 0}%</span>
        </div>
        {/* Brand comparison */}
        <div className="pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <BrandLogo brand={brandName} size="sm" />
            <span className="text-xs text-slate-500">vs concurrents</span>
          </div>
        </div>
      </div>
    </Card>
  );
});

AIEngineScoreCard.displayName = 'AIEngineScoreCard';

// Brand Leaderboard Component
const BrandLeaderboard = memo(({ analysis, brandName }) => {
  const leaderboard = useMemo(() => {
    const brands = new Map();
    
    analysis?.query_scores?.forEach(query => {
      query.responses?.forEach(resp => {
        // Our brand
        if (resp.brand_mentioned) {
          const existing = brands.get(brandName) || { mentions: 0, positions: [], isOurBrand: true };
          existing.mentions++;
          if (resp.position) existing.positions.push(resp.position);
          brands.set(brandName, existing);
        }
        
        // Competitors
        resp.competitors_mentioned?.forEach(comp => {
          const existing = brands.get(comp.name) || { mentions: 0, positions: [] };
          existing.mentions++;
          if (comp.position) existing.positions.push(comp.position);
          brands.set(comp.name, existing);
        });
      });
    });
    
    return Array.from(brands.entries())
      .map(([name, data]) => ({
        name,
        ...data,
        avgPosition: data.positions.length > 0 
          ? (data.positions.reduce((a, b) => a + b, 0) / data.positions.length).toFixed(1)
          : '-'
      }))
      .sort((a, b) => b.mentions - a.mentions)
      .slice(0, 10);
  }, [analysis, brandName]);

  if (leaderboard.length === 0) return null;

  const maxMentions = leaderboard[0]?.mentions || 1;

  return (
    <Card className="p-6 bg-white border-slate-200">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Crown className="w-5 h-5 text-amber-500" />
        Classement des Marques
      </h3>
      <div className="space-y-3">
        {leaderboard.map((brand, idx) => (
          <div 
            key={brand.name}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
              brand.isOurBrand 
                ? 'bg-violet-50 border border-violet-200' 
                : 'bg-slate-50 hover:bg-slate-100'
            }`}
          >
            {/* Rank */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              idx === 0 ? 'bg-amber-100 text-amber-700' :
              idx === 1 ? 'bg-slate-200 text-slate-700' :
              idx === 2 ? 'bg-orange-100 text-orange-700' :
              'bg-slate-100 text-slate-500'
            }`}>
              {idx + 1}
            </div>
            
            {/* Brand Logo */}
            <BrandLogo brand={brand.name} size="md" />
            
            {/* Brand Name & Stats */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`font-medium truncate ${brand.isOurBrand ? 'text-violet-700' : 'text-slate-900'}`}>
                  {brand.name}
                </span>
                {brand.isOurBrand && (
                  <Badge className="bg-violet-100 text-violet-700 border-0 text-xs">Vous</Badge>
                )}
              </div>
              {/* Progress bar */}
              <div className="mt-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all ${brand.isOurBrand ? 'bg-violet-500' : 'bg-slate-400'}`}
                  style={{ width: `${(brand.mentions / maxMentions) * 100}%` }}
                />
              </div>
            </div>
            
            {/* Metrics */}
            <div className="text-right">
              <p className="text-lg font-bold text-slate-900">{brand.mentions}</p>
              <p className="text-xs text-slate-500">mentions</p>
            </div>
            <div className="text-right w-16">
              <p className="text-sm font-medium text-slate-700">#{brand.avgPosition}</p>
              <p className="text-xs text-slate-500">pos. moy.</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
});

BrandLeaderboard.displayName = 'BrandLeaderboard';

// Main Visibility Page
const VisibilityPage = () => {
  const { currentProject } = useAuth();
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [filterEngine, setFilterEngine] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch latest analysis
  useEffect(() => {
    if (currentProject) {
      fetchLatestAnalysis();
    }
  }, [currentProject]);

  const fetchLatestAnalysis = async () => {
    if (!currentProject) return;
    setLoading(true);
    
    try {
      // Get analyses for this project
      const response = await axios.get(
        `${API}/projects/${currentProject.project_id}/analyses`,
        { withCredentials: true }
      );
      
      // Get the latest completed analysis
      const analyses = response.data.analyses || [];
      const latestCompleted = analyses.find(a => a.status === 'completed');
      
      if (latestCompleted) {
        // Fetch full analysis details
        const detailResponse = await axios.get(
          `${API}/analysis/${latestCompleted.analysis_id}`,
          { withCredentials: true }
        );
        setAnalysis(detailResponse.data.analysis);
      }
    } catch (error) {
      console.error("Error fetching analysis:", error);
      toast.error("Erreur lors du chargement des données");
    } finally {
      setLoading(false);
    }
  };

  // Calculate visibility stats from analysis
  const visibilityStats = useMemo(() => {
    if (!analysis) return null;
    
    const queryScores = analysis.query_scores || [];
    const totalQueries = queryScores.length;
    const mentionedQueries = queryScores.filter(q => q.mention_rate > 0).length;
    
    // Calculate by engine
    const byEngine = {};
    queryScores.forEach(q => {
      q.responses?.forEach(r => {
        if (!byEngine[r.ai_type]) {
          byEngine[r.ai_type] = { total: 0, mentioned: 0, positions: [] };
        }
        byEngine[r.ai_type].total++;
        if (r.brand_mentioned) {
          byEngine[r.ai_type].mentioned++;
          if (r.position) byEngine[r.ai_type].positions.push(r.position);
        }
      });
    });
    
    const engineStats = Object.entries(byEngine).reduce((acc, [engine, data]) => {
      acc[engine] = {
        score: data.total > 0 ? Math.round((data.mentioned / data.total) * 100) : 0,
        mention_rate: data.total > 0 ? Math.round((data.mentioned / data.total) * 100) : 0,
        position_avg: data.positions.length > 0 
          ? data.positions.reduce((a, b) => a + b, 0) / data.positions.length 
          : 0,
        trend: 'stable'
      };
      return acc;
    }, {});
    
    // Position distribution
    const positions = { first: 0, second: 0, third: 0, other: 0, absent: 0 };
    let totalResponses = 0;
    queryScores.forEach(q => {
      q.responses?.forEach(r => {
        totalResponses++;
        if (!r.brand_mentioned) positions.absent++;
        else if (r.position === 1) positions.first++;
        else if (r.position === 2) positions.second++;
        else if (r.position === 3) positions.third++;
        else positions.other++;
      });
    });
    
    const positionDistribution = totalResponses > 0 ? {
      first: Math.round((positions.first / totalResponses) * 100),
      second: Math.round((positions.second / totalResponses) * 100),
      third: Math.round((positions.third / totalResponses) * 100),
      other: Math.round((positions.other / totalResponses) * 100),
      absent: Math.round((positions.absent / totalResponses) * 100)
    } : positions;
    
    return {
      global_score: analysis.global_score || 0,
      total_queries: totalQueries,
      mention_rate: totalQueries > 0 ? Math.round((mentionedQueries / totalQueries) * 100) : 0,
      engines: engineStats,
      position_distribution: positionDistribution
    };
  }, [analysis]);

  // Filter queries
  const filteredQueries = useMemo(() => {
    if (!analysis?.query_scores) return [];
    
    return analysis.query_scores.filter(q => {
      // Type filter
      if (filterType !== 'all' && q.query_type !== filterType) return false;
      
      // Engine filter
      if (filterEngine !== 'all') {
        const hasEngine = q.responses?.some(r => r.ai_type?.toLowerCase() === filterEngine);
        if (!hasEngine) return false;
      }
      
      // Search filter
      if (searchQuery) {
        const search = searchQuery.toLowerCase();
        if (!q.query_text?.toLowerCase().includes(search)) return false;
      }
      
      return true;
    });
  }, [analysis, filterType, filterEngine, searchQuery]);

  // Get unique query types
  const queryTypes = useMemo(() => {
    if (!analysis?.query_scores) return [];
    return [...new Set(analysis.query_scores.map(q => q.query_type).filter(Boolean))];
  }, [analysis]);

  // Get unique engines
  const engines = useMemo(() => {
    if (!analysis?.query_scores) return [];
    const engineSet = new Set();
    analysis.query_scores.forEach(q => {
      q.responses?.forEach(r => {
        if (r.ai_type) engineSet.add(r.ai_type.toLowerCase());
      });
    });
    return [...engineSet];
  }, [analysis]);

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <div className="w-12 h-12 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin mx-auto" />
            <p className="text-slate-600">Chargement des données de visibilité...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!analysis) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Eye className="w-7 h-7 text-violet-600" />
              Visibilité Générative
            </h1>
            <p className="text-slate-600 mt-1">Tracking de présence dans les réponses IA</p>
          </div>
          
          <Card className="p-8 text-center bg-slate-50 border-slate-200">
            <Eye className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Aucune analyse disponible</h3>
            <p className="text-slate-600 mb-6">Lancez une analyse pour voir votre visibilité dans les réponses IA.</p>
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
      <div className="space-y-6" data-testid="visibility-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Eye className="w-7 h-7 text-violet-600" />
              Visibilité Générative
            </h1>
            <p className="text-slate-600 mt-1">
              Analyse détaillée de votre présence dans les réponses IA
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={fetchLatestAnalysis}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualiser
            </Button>
            <Link to="/analysis">
              <Button className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700">
                <Sparkles className="w-4 h-4 mr-2" />
                Nouvelle analyse
              </Button>
            </Link>
          </div>
        </div>

        {/* Global Score */}
        <Card className="p-6 bg-gradient-to-br from-violet-50 to-cyan-50 border-violet-200">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="relative">
                <svg className="w-28 h-28 transform -rotate-90">
                  <circle cx="56" cy="56" r="48" stroke="#e2e8f0" strokeWidth="10" fill="none" />
                  <circle
                    cx="56" cy="56" r="48"
                    stroke="url(#visGradient)"
                    strokeWidth="10"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={`${(visibilityStats?.global_score / 100) * 301} 301`}
                  />
                  <defs>
                    <linearGradient id="visGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#7c3aed" />
                      <stop offset="100%" stopColor="#06b6d4" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-3xl font-bold ${getScoreColor(visibilityStats?.global_score)}`}>
                    {Math.round(visibilityStats?.global_score || 0)}
                  </span>
                  <span className="text-xs text-slate-500">/100</span>
                </div>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Score de Visibilité</h2>
                <p className="text-slate-600 text-sm">{visibilityStats?.total_queries || 0} requêtes analysées</p>
                <div className="flex items-center gap-2 mt-2">
                  <BrandLogo brand={currentProject?.brand_name} size="sm" />
                  <Badge className="bg-white border-violet-200 text-violet-700">
                    <Shield className="w-3 h-3 mr-1" />
                    IAskan Verified™
                  </Badge>
                </div>
              </div>
            </div>
            
            {/* Quick stats */}
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{visibilityStats?.mention_rate || 0}%</p>
                <p className="text-xs text-slate-600">Taux de mention</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{visibilityStats?.position_distribution?.first || 0}%</p>
                <p className="text-xs text-slate-600">1ère position</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{Object.keys(visibilityStats?.engines || {}).length}</p>
                <p className="text-xs text-slate-600">Moteurs IA</p>
              </div>
            </div>
          </div>
        </Card>

        {/* AI Engines Grid */}
        {visibilityStats?.engines && Object.keys(visibilityStats.engines).length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Bot className="w-5 h-5 text-slate-600" />
              Performance par Moteur IA
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(visibilityStats.engines).map(([engine, metrics]) => (
                <AIEngineScoreCard 
                  key={engine} 
                  engine={engine} 
                  metrics={metrics} 
                  brandName={currentProject?.brand_name}
                />
              ))}
            </div>
          </div>
        )}

        {/* Position Distribution */}
        <Card className="p-6 bg-white border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-500" />
            Distribution des Positions
          </h3>
          <div className="grid grid-cols-5 gap-4">
            {[
              { key: "first", label: "1ère", icon: Crown, color: "from-amber-400 to-amber-500" },
              { key: "second", label: "2ème", icon: Medal, color: "from-slate-400 to-slate-500" },
              { key: "third", label: "3ème", icon: Award, color: "from-orange-400 to-orange-500" },
              { key: "other", label: "Autres", icon: null, color: "from-cyan-400 to-cyan-500" },
              { key: "absent", label: "Non cité", icon: null, color: "from-red-400 to-red-500" }
            ].map((pos) => (
              <div key={pos.key} className="text-center">
                <div className={`w-14 h-14 mx-auto mb-2 rounded-full bg-gradient-to-br ${pos.color} flex items-center justify-center text-white shadow-lg`}>
                  {pos.icon ? <pos.icon className="w-6 h-6" /> : <span className="text-lg font-bold">{pos.key === 'absent' ? '✗' : '+'}</span>}
                </div>
                <p className="text-2xl font-bold text-slate-900">{visibilityStats?.position_distribution?.[pos.key] || 0}%</p>
                <p className="text-xs text-slate-600">{pos.label}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Brand Leaderboard */}
        <BrandLeaderboard analysis={analysis} brandName={currentProject?.brand_name} />

        {/* Semantic Analysis */}
        <SemanticAnalysisCard 
          analysis={analysis} 
          brandName={currentProject?.brand_name}
          competitors={currentProject?.competitors}
        />

        {/* Questions Analysis */}
        <Card className="p-6 bg-white border-slate-200">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-violet-600" />
              Questions Analysées ({filteredQueries.length})
            </h3>
            
            {/* Filters */}
            <div className="flex flex-wrap gap-2">
              {/* Search */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>
              
              {/* Type filter */}
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500"
              >
                <option value="all">Tous les types</option>
                {queryTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              
              {/* Engine filter */}
              <select
                value={filterEngine}
                onChange={(e) => setFilterEngine(e.target.value)}
                className="px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500"
              >
                <option value="all">Tous les moteurs</option>
                {engines.map(engine => (
                  <option key={engine} value={engine}>{engine}</option>
                ))}
              </select>
            </div>
          </div>
          
          {/* Query Cards */}
          <div className="space-y-3">
            {filteredQueries.length > 0 ? (
              filteredQueries.map((query, idx) => (
                <QueryAnalysisCard 
                  key={idx}
                  query={query}
                  brandName={currentProject?.brand_name}
                  competitors={currentProject?.competitors}
                />
              ))
            ) : (
              <div className="text-center py-8 text-slate-500">
                Aucune question ne correspond aux filtres
              </div>
            )}
          </div>
        </Card>

        {/* Info Box */}
        <Card className="p-4 bg-cyan-50 border-cyan-200">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-cyan-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-cyan-800">
              <p className="font-medium mb-1">Comment améliorer votre visibilité ?</p>
              <ul className="list-disc list-inside space-y-1 text-cyan-700">
                <li>Analysez les requêtes où vos concurrents vous dépassent</li>
                <li>Optimisez votre contenu pour les types de questions où vous êtes faible</li>
                <li>Renforcez votre présence sur les moteurs IA où vous sous-performez</li>
                <li>Ajoutez des données structurées pour améliorer la citabilité</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default VisibilityPage;
