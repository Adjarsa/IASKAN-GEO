import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  Crown,
  Target,
  AlertTriangle,
  CheckCircle,
  Eye,
  BarChart3,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Search
} from "lucide-react";

const CompetitorAnalysisCard = ({ analysis, brandName }) => {
  const [expanded, setExpanded] = useState(false);
  
  if (!analysis) return null;

  const competitorComparison = analysis.competitor_comparison || [];
  const analysisSummary = analysis.analysis_summary || {};
  const discoveredCompetitors = analysisSummary.discovered_competitors || [];
  const userDefinedCompetitors = analysisSummary.user_defined_competitors || [];
  const indices = analysis.indices || {};
  const dominanceIndex = indices.dominance_index || 0;

  // Separate discovered vs user-defined
  const aiDiscovered = competitorComparison.filter(c => c.discovered);
  const userDefined = competitorComparison.filter(c => c.user_defined);

  // Sort by visibility
  const sortedCompetitors = [...competitorComparison].sort((a, b) => 
    (b.visibility_rate || b.mentions || 0) - (a.visibility_rate || a.mentions || 0)
  );

  // Find leader (excluding our brand)
  const leader = sortedCompetitors[0];
  const brandPosition = sortedCompetitors.findIndex(c => 
    c.competitor?.toLowerCase() === brandName?.toLowerCase()
  ) + 1;

  // Calculate competitive insights
  const totalMentions = competitorComparison.reduce((sum, c) => sum + (c.mentions || 0), 0);
  const avgVisibility = competitorComparison.length > 0 
    ? competitorComparison.reduce((sum, c) => sum + (c.visibility_rate || 0), 0) / competitorComparison.length 
    : 0;

  const getVisibilityColor = (rate) => {
    if (rate >= 60) return "text-emerald-600 bg-emerald-50";
    if (rate >= 30) return "text-amber-600 bg-amber-50";
    return "text-red-600 bg-red-50";
  };

  const getPositionBadge = (position) => {
    if (position === 1) return { icon: Crown, color: "text-amber-500", label: "Leader" };
    if (position <= 3) return { icon: TrendingUp, color: "text-emerald-500", label: "Top 3" };
    if (position <= 5) return { icon: Minus, color: "text-slate-500", label: "Challenger" };
    return { icon: TrendingDown, color: "text-red-500", label: "À améliorer" };
  };

  // Generate recommendations based on competitive analysis
  const getCompetitiveRecommendations = () => {
    const recommendations = [];
    
    if (dominanceIndex < 40) {
      recommendations.push({
        priority: "high",
        title: "Augmenter votre présence",
        description: "Vos concurrents dominent les réponses IA. Créez du contenu expert sur vos mots-clés principaux.",
        action: "Publier 2-3 articles de fond par semaine"
      });
    }
    
    if (leader && leader.mentions > 5) {
      recommendations.push({
        priority: "medium",
        title: `Analyser ${leader.competitor}`,
        description: `${leader.competitor} est le plus visible. Étudiez leur stratégie de contenu et leur positionnement.`,
        action: "Identifier leurs sources de citations"
      });
    }
    
    if (aiDiscovered.length > userDefined.length) {
      recommendations.push({
        priority: "medium",
        title: "Nouveaux concurrents détectés",
        description: `${aiDiscovered.length} concurrents ont été découverts par l'analyse IA que vous n'aviez pas listés.`,
        action: "Surveiller ces nouveaux acteurs"
      });
    }

    if (avgVisibility < 30) {
      recommendations.push({
        priority: "high",
        title: "Améliorer la citabilité",
        description: "La visibilité moyenne est faible. Renforcez vos données structurées et FAQ.",
        action: "Ajouter Schema.org et enrichir la FAQ"
      });
    }

    return recommendations;
  };

  const recommendations = getCompetitiveRecommendations();

  return (
    <Card className="p-6" data-testid="competitor-analysis-card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center">
            <Users className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Analyse Concurrentielle</h3>
            <p className="text-sm text-slate-500">{competitorComparison.length} concurrents analysés</p>
          </div>
        </div>
        <Badge className={`${dominanceIndex >= 50 ? 'bg-emerald-100 text-emerald-700' : dominanceIndex >= 30 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>
          Dominance: {Math.round(dominanceIndex)}%
        </Badge>
      </div>

      {/* Methodology Box */}
      <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-100">
        <div className="flex items-start gap-3">
          <Search className="w-5 h-5 text-slate-400 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-slate-900 mb-1">Méthodologie d'analyse</h4>
            <p className="text-xs text-slate-600">
              Cette analyse est basée sur <strong>{analysisSummary.total_prompts || 0} requêtes</strong> exécutées 
              sur <strong>{analysisSummary.ai_engines_used?.length || 0} moteurs IA</strong> (
              {analysisSummary.ai_engines_used?.join(", ") || "N/A"}). 
              Chaque requête est répétée <strong>{analysisSummary.runs_per_query || 3} fois</strong> pour mesurer la stabilité.
              Les concurrents sont identifiés par leur fréquence d'apparition et leur position dans les réponses.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-white rounded-xl border border-slate-100 text-center">
          <div className="text-2xl font-bold text-violet-600">{aiDiscovered.length}</div>
          <p className="text-xs text-slate-600 mt-1">Découverts par IA</p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-100 text-center">
          <div className="text-2xl font-bold text-cyan-600">{userDefined.length}</div>
          <p className="text-xs text-slate-600 mt-1">Définis par vous</p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-100 text-center">
          <div className="text-2xl font-bold text-slate-700">{totalMentions}</div>
          <p className="text-xs text-slate-600 mt-1">Mentions totales</p>
        </div>
      </div>

      {/* Competitors Table */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-slate-900 mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Classement des concurrents
        </h4>
        <div className="space-y-2">
          {sortedCompetitors.slice(0, expanded ? undefined : 5).map((competitor, index) => {
            const position = getPositionBadge(index + 1);
            return (
              <div 
                key={competitor.competitor}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  index === 0 ? 'bg-amber-50 border-amber-200' : 'bg-white border-slate-100'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    index === 0 ? 'bg-amber-100' : 'bg-slate-100'
                  }`}>
                    <span className={`text-sm font-bold ${index === 0 ? 'text-amber-600' : 'text-slate-600'}`}>
                      {index + 1}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{competitor.competitor}</span>
                      {competitor.discovered && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-violet-600 border-violet-200">
                          <Sparkles className="w-2.5 h-2.5 mr-0.5" />
                          IA
                        </Badge>
                      )}
                      {competitor.user_defined && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-cyan-600 border-cyan-200">
                          <Eye className="w-2.5 h-2.5 mr-0.5" />
                          Suivi
                        </Badge>
                      )}
                    </div>
                    {competitor.ai_sources?.length > 0 && (
                      <p className="text-xs text-slate-500">
                        Vu sur: {competitor.ai_sources.slice(0, 3).join(", ")}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm font-semibold text-slate-900">{competitor.mentions || 0} mentions</div>
                    <div className={`text-xs px-2 py-0.5 rounded-full ${getVisibilityColor(competitor.visibility_rate || 0)}`}>
                      {Math.round(competitor.visibility_rate || 0)}% visibilité
                    </div>
                    {competitor.presence_rate > 0 && (
                      <div className="text-xs text-slate-500 mt-0.5">
                        Présent dans {Math.round(competitor.presence_rate)}% des réponses
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {sortedCompetitors.length > 5 && (
          <Button 
            variant="ghost" 
            className="w-full mt-2 text-slate-600"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <>
                <ChevronUp className="w-4 h-4 mr-2" />
                Voir moins
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-2" />
                Voir {sortedCompetitors.length - 5} de plus
              </>
            )}
          </Button>
        )}
      </div>

      {/* AI Discovered Section */}
      {aiDiscovered.length > 0 && (
        <div className="mb-6 p-4 bg-violet-50 rounded-xl border border-violet-100">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-violet-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-violet-900 mb-2">
                Concurrents découverts par l'IA
              </h4>
              <p className="text-xs text-violet-700 mb-3">
                Ces marques apparaissent fréquemment dans les réponses IA pour vos mots-clés, 
                mais n'étaient pas dans votre liste initiale.
              </p>
              <div className="flex flex-wrap gap-2">
                {aiDiscovered.map(c => (
                  <Badge key={c.competitor} className="bg-white text-violet-700 border border-violet-200">
                    {c.competitor}
                    <span className="ml-1 text-violet-500">({c.mentions || 0})</span>
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Defined Not Found */}
      {userDefined.filter(c => c.mentions === 0).length > 0 && (
        <div className="mb-6 p-4 bg-amber-50 rounded-xl border border-amber-100">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-amber-900 mb-2">
                Concurrents non trouvés
              </h4>
              <p className="text-xs text-amber-700 mb-3">
                Ces concurrents que vous suivez n'apparaissent pas dans les réponses IA analysées.
              </p>
              <div className="flex flex-wrap gap-2">
                {userDefined.filter(c => c.mentions === 0).map(c => (
                  <Badge key={c.competitor} variant="outline" className="text-amber-700 border-amber-300">
                    {c.competitor}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="p-4 bg-gradient-to-br from-slate-50 to-violet-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-violet-600" />
            <h4 className="font-medium text-slate-900">Axes d'amélioration</h4>
          </div>
          <div className="space-y-3">
            {recommendations.map((rec, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  rec.priority === 'high' ? 'bg-red-100' : 'bg-amber-100'
                }`}>
                  {rec.priority === 'high' ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                  ) : (
                    <Target className="w-3.5 h-3.5 text-amber-600" />
                  )}
                </div>
                <div>
                  <h5 className="text-sm font-medium text-slate-900">{rec.title}</h5>
                  <p className="text-xs text-slate-600 mt-0.5">{rec.description}</p>
                  <p className="text-xs text-violet-600 font-medium mt-1">
                    → {rec.action}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default CompetitorAnalysisCard;
