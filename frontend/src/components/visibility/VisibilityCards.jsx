import { memo, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Bot, ChevronDown, ChevronUp, TrendingUp, TrendingDown, 
  Minus, Crown, Medal, Award, AlertTriangle, Lightbulb
} from "lucide-react";

// Brand Logo component with fallback
export const BrandLogo = memo(({ brand, size = "md" }) => {
  const [imgError, setImgError] = useState(false);
  const [imgIndex, setImgIndex] = useState(0);
  
  const sizes = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base"
  };
  
  // Clean brand name for URL
  const cleanBrand = brand?.toLowerCase().replace(/\s+/g, '').replace(/[^a-z0-9]/g, '') || '';
  
  // Multiple logo sources to try
  const logoSources = [
    `https://www.google.com/s2/favicons?domain=${cleanBrand}.com&sz=64`,
    `https://icon.horse/icon/${cleanBrand}.com`,
    `https://api.faviconkit.com/${cleanBrand}.com/64`
  ];
  
  // Generate initials for fallback
  const initials = brand?.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase() || '?';
  
  // Generate consistent color based on brand name
  const getColorFromBrand = (name) => {
    const colors = [
      'bg-violet-500', 'bg-cyan-500', 'bg-emerald-500', 'bg-amber-500', 
      'bg-rose-500', 'bg-indigo-500', 'bg-teal-500', 'bg-orange-500'
    ];
    const hash = name?.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0;
    return colors[hash % colors.length];
  };
  
  const handleImageError = () => {
    if (imgIndex < logoSources.length - 1) {
      setImgIndex(imgIndex + 1);
    } else {
      setImgError(true);
    }
  };
  
  if (imgError || !cleanBrand) {
    return (
      <div className={`${sizes[size]} ${getColorFromBrand(brand)} rounded-lg flex items-center justify-center text-white font-bold shadow-sm`}>
        {initials}
      </div>
    );
  }
  
  return (
    <img
      src={logoSources[imgIndex]}
      alt={brand}
      className={`${sizes[size]} rounded-lg object-contain bg-white p-0.5 border border-slate-200`}
      onError={handleImageError}
    />
  );
});

BrandLogo.displayName = 'BrandLogo';

// Position Badge component
export const PositionBadge = memo(({ position, showIcon = true }) => {
  if (!position || position === 0) {
    return (
      <Badge className="bg-slate-100 text-slate-500 border-slate-200">
        Non cité
      </Badge>
    );
  }
  
  const configs = {
    1: { bg: "bg-amber-100 text-amber-700 border-amber-300", icon: Crown, label: "1er" },
    2: { bg: "bg-slate-200 text-slate-700 border-slate-300", icon: Medal, label: "2ème" },
    3: { bg: "bg-orange-100 text-orange-700 border-orange-300", icon: Award, label: "3ème" }
  };
  
  const config = configs[position] || { 
    bg: "bg-slate-100 text-slate-600 border-slate-200", 
    icon: null, 
    label: `${position}ème` 
  };
  
  const Icon = config.icon;
  
  return (
    <Badge className={`${config.bg} font-semibold`}>
      {showIcon && Icon && <Icon className="w-3 h-3 mr-1" />}
      {config.label}
    </Badge>
  );
});

PositionBadge.displayName = 'PositionBadge';

// AI Engine Icon component
export const AIEngineIcon = memo(({ engine, size = "md" }) => {
  const sizes = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-10 h-10"
  };
  
  const configs = {
    chatgpt: { bg: "bg-emerald-100", icon: "text-emerald-600", label: "ChatGPT" },
    openai: { bg: "bg-emerald-100", icon: "text-emerald-600", label: "OpenAI" },
    claude: { bg: "bg-orange-100", icon: "text-orange-600", label: "Claude" },
    gemini: { bg: "bg-blue-100", icon: "text-blue-600", label: "Gemini" },
    perplexity: { bg: "bg-purple-100", icon: "text-purple-600", label: "Perplexity" }
  };
  
  const config = configs[engine?.toLowerCase()] || { bg: "bg-slate-100", icon: "text-slate-600", label: engine };
  
  return (
    <div className={`${sizes[size]} ${config.bg} rounded-lg flex items-center justify-center`} title={config.label}>
      <Bot className={`w-4 h-4 ${config.icon}`} />
    </div>
  );
});

AIEngineIcon.displayName = 'AIEngineIcon';

// Single Query Analysis Card
export const QueryAnalysisCard = memo(({ query, brandName, competitors = [] }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Extract all brands mentioned across all responses
  const brandsMentioned = useMemo(() => {
    const brands = new Map();
    
    query.responses?.forEach(resp => {
      // Check our brand
      if (resp.brand_mentioned) {
        const existing = brands.get(brandName) || { count: 0, positions: [], engines: [] };
        existing.count++;
        if (resp.position) existing.positions.push(resp.position);
        existing.engines.push(resp.ai_type);
        existing.isOurBrand = true;
        brands.set(brandName, existing);
      }
      
      // Check competitors mentioned in response
      resp.competitors_mentioned?.forEach(comp => {
        const existing = brands.get(comp.name) || { count: 0, positions: [], engines: [] };
        existing.count++;
        if (comp.position) existing.positions.push(comp.position);
        existing.engines.push(resp.ai_type);
        brands.set(comp.name, existing);
      });
    });
    
    // Sort by average position (best first)
    return Array.from(brands.entries())
      .map(([name, data]) => ({
        name,
        ...data,
        avgPosition: data.positions.length > 0 
          ? data.positions.reduce((a, b) => a + b, 0) / data.positions.length 
          : 999
      }))
      .sort((a, b) => a.avgPosition - b.avgPosition);
  }, [query.responses, brandName]);
  
  // Group responses by AI engine
  const responsesByEngine = useMemo(() => {
    const grouped = {};
    query.responses?.forEach(resp => {
      if (!grouped[resp.ai_type]) grouped[resp.ai_type] = [];
      grouped[resp.ai_type].push(resp);
    });
    return grouped;
  }, [query.responses]);
  
  const ourBrandData = brandsMentioned.find(b => b.isOurBrand);
  const mentionRate = query.mention_rate || 0;
  
  return (
    <Card className="bg-white border-slate-200 overflow-hidden">
      {/* Header - Always visible */}
      <div 
        className="p-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-slate-900 font-medium mb-2">"{query.query_text}"</p>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline" className="text-xs">
                {query.query_type || 'général'}
              </Badge>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                mentionRate >= 50 ? 'bg-emerald-100 text-emerald-700' :
                mentionRate > 0 ? 'bg-amber-100 text-amber-700' :
                'bg-red-100 text-red-700'
              }`}>
                {Math.round(mentionRate)}% mentions
              </span>
            </div>
          </div>
          
          {/* Quick brand summary */}
          <div className="flex items-center gap-2">
            {brandsMentioned.slice(0, 4).map((brand, idx) => (
              <div key={brand.name} className="relative">
                <BrandLogo brand={brand.name} size="sm" />
                {brand.isOurBrand && (
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-violet-500 rounded-full border-2 border-white" />
                )}
              </div>
            ))}
            {brandsMentioned.length > 4 && (
              <span className="text-xs text-slate-500">+{brandsMentioned.length - 4}</span>
            )}
          </div>
          
          <Button variant="ghost" size="sm" className="flex-shrink-0">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>
      
      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-100 p-4 bg-slate-50/50 space-y-4">
          {/* Brand Rankings */}
          <div>
            <h4 className="text-sm font-semibold text-slate-700 mb-3">Classement des marques citées</h4>
            <div className="space-y-2">
              {brandsMentioned.map((brand, idx) => (
                <div 
                  key={brand.name}
                  className={`flex items-center gap-3 p-2 rounded-lg ${
                    brand.isOurBrand ? 'bg-violet-50 border border-violet-200' : 'bg-white border border-slate-100'
                  }`}
                >
                  <span className="text-sm font-bold text-slate-400 w-6">#{idx + 1}</span>
                  <BrandLogo brand={brand.name} size="sm" />
                  <span className={`text-sm font-medium flex-1 ${brand.isOurBrand ? 'text-violet-700' : 'text-slate-700'}`}>
                    {brand.name}
                    {brand.isOurBrand && <span className="ml-2 text-xs text-violet-500">(vous)</span>}
                  </span>
                  <div className="flex gap-1">
                    {brand.engines.slice(0, 3).map((eng, i) => (
                      <AIEngineIcon key={i} engine={eng} size="sm" />
                    ))}
                  </div>
                  <PositionBadge position={Math.round(brand.avgPosition)} showIcon={idx < 3} />
                </div>
              ))}
              {brandsMentioned.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-2">Aucune marque citée</p>
              )}
            </div>
          </div>
          
          {/* Responses by AI Engine */}
          <div>
            <h4 className="text-sm font-semibold text-slate-700 mb-3">Détail par moteur IA</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(responsesByEngine).map(([engine, responses]) => (
                <div key={engine} className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="flex items-center gap-2 mb-2">
                    <AIEngineIcon engine={engine} size="sm" />
                    <span className="text-sm font-medium text-slate-700 capitalize">{engine}</span>
                  </div>
                  {responses.map((resp, idx) => (
                    <div key={idx} className="text-xs text-slate-600 py-1 border-t border-slate-100 first:border-0">
                      <div className="flex items-center justify-between">
                        <span>Run {idx + 1}</span>
                        <div className="flex items-center gap-2">
                          {resp.brand_mentioned ? (
                            <>
                              <span className="text-emerald-600">✓ Cité</span>
                              {resp.position && <PositionBadge position={resp.position} showIcon={false} />}
                            </>
                          ) : (
                            <span className="text-red-500">✗ Absent</span>
                          )}
                        </div>
                      </div>
                      {resp.role && (
                        <p className="text-slate-500 mt-1">Rôle: {resp.role}</p>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
});

QueryAnalysisCard.displayName = 'QueryAnalysisCard';

// Semantic Analysis Card
export const SemanticAnalysisCard = memo(({ analysis, brandName, competitors }) => {
  // Analyze why competitors might outperform
  const insights = useMemo(() => {
    const results = [];
    const queryScores = analysis?.query_scores || [];
    
    // Group by query type
    const byType = queryScores.reduce((acc, q) => {
      const type = q.query_type || 'general';
      if (!acc[type]) acc[type] = { total: 0, mentioned: 0, queries: [] };
      acc[type].total++;
      if (q.mention_rate > 50) acc[type].mentioned++;
      acc[type].queries.push(q);
      return acc;
    }, {});
    
    // Find weak query types
    Object.entries(byType).forEach(([type, data]) => {
      const rate = data.total > 0 ? (data.mentioned / data.total) * 100 : 0;
      if (rate < 40 && data.total >= 2) {
        results.push({
          type: 'weak_type',
          severity: rate < 20 ? 'high' : 'medium',
          title: `Faible visibilité sur les requêtes "${type}"`,
          description: `Votre marque n'est citée que dans ${Math.round(rate)}% des requêtes ${type}. Analysez le contenu de vos concurrents pour ce type de requête.`,
          queryType: type
        });
      }
    });
    
    // Find AI engines where we underperform
    const byEngine = {};
    queryScores.forEach(q => {
      q.responses?.forEach(r => {
        if (!byEngine[r.ai_type]) byEngine[r.ai_type] = { total: 0, mentioned: 0 };
        byEngine[r.ai_type].total++;
        if (r.brand_mentioned) byEngine[r.ai_type].mentioned++;
      });
    });
    
    Object.entries(byEngine).forEach(([engine, data]) => {
      const rate = data.total > 0 ? (data.mentioned / data.total) * 100 : 0;
      if (rate < 30 && data.total >= 3) {
        results.push({
          type: 'weak_engine',
          severity: 'medium',
          title: `Sous-performance sur ${engine}`,
          description: `Votre marque n'apparaît que dans ${Math.round(rate)}% des réponses de ${engine}. Ce moteur peut avoir des sources de données différentes.`,
          engine
        });
      }
    });
    
    // Analyze competitor dominance
    const competitorMentions = {};
    queryScores.forEach(q => {
      q.responses?.forEach(r => {
        r.competitors_mentioned?.forEach(c => {
          if (!competitorMentions[c.name]) competitorMentions[c.name] = 0;
          competitorMentions[c.name]++;
        });
      });
    });
    
    const sortedCompetitors = Object.entries(competitorMentions)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3);
    
    if (sortedCompetitors.length > 0 && sortedCompetitors[0][1] > 5) {
      results.push({
        type: 'competitor_dominance',
        severity: 'info',
        title: `${sortedCompetitors[0][0]} domine les résultats`,
        description: `Ce concurrent est cité ${sortedCompetitors[0][1]} fois. Analysez leur stratégie de contenu et leur présence en ligne.`,
        competitor: sortedCompetitors[0][0]
      });
    }
    
    return results;
  }, [analysis]);
  
  if (insights.length === 0) {
    return (
      <Card className="p-6 bg-emerald-50 border-emerald-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h3 className="font-semibold text-emerald-800">Bonne performance globale</h3>
            <p className="text-sm text-emerald-700">
              Votre marque maintient une visibilité équilibrée sur tous les moteurs IA.
            </p>
          </div>
        </div>
      </Card>
    );
  }
  
  return (
    <Card className="p-6 bg-white border-slate-200">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Lightbulb className="w-5 h-5 text-amber-500" />
        Analyse Sémantique Comparative
      </h3>
      <div className="space-y-3">
        {insights.map((insight, idx) => (
          <div 
            key={idx}
            className={`p-4 rounded-lg border-l-4 ${
              insight.severity === 'high' ? 'bg-red-50 border-l-red-500' :
              insight.severity === 'medium' ? 'bg-amber-50 border-l-amber-500' :
              'bg-cyan-50 border-l-cyan-500'
            }`}
          >
            <div className="flex items-start gap-3">
              {insight.severity === 'high' ? (
                <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
              ) : insight.severity === 'medium' ? (
                <TrendingDown className="w-5 h-5 text-amber-500 flex-shrink-0" />
              ) : (
                <Lightbulb className="w-5 h-5 text-cyan-500 flex-shrink-0" />
              )}
              <div>
                <h4 className="font-medium text-slate-900">{insight.title}</h4>
                <p className="text-sm text-slate-600 mt-1">{insight.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
});

SemanticAnalysisCard.displayName = 'SemanticAnalysisCard';

export default QueryAnalysisCard;
