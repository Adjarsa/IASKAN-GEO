import { memo } from "react";
import { Card } from "@/components/ui/card";
import { Bot, AlertTriangle } from "lucide-react";
import { getScoreColor } from "./ScoreCard";

// AI Engine configurations
const AI_CONFIGS = {
  chatgpt: { name: "ChatGPT", color: "bg-emerald-100", iconColor: "text-emerald-600" },
  openai: { name: "OpenAI", color: "bg-emerald-100", iconColor: "text-emerald-600" },
  claude: { name: "Claude", color: "bg-orange-100", iconColor: "text-orange-600" },
  gemini: { name: "Gemini", color: "bg-blue-100", iconColor: "text-blue-600" },
  perplexity: { name: "Perplexity", color: "bg-purple-100", iconColor: "text-purple-600" }
};

// AI Score Card
const AIScoreCard = memo(({ aiName, score }) => {
  const config = AI_CONFIGS[aiName.toLowerCase()] || { 
    name: aiName, 
    color: "bg-slate-100", 
    iconColor: "text-slate-600" 
  };
  
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-colors">
      <div className={`w-10 h-10 rounded-lg ${config.color} flex items-center justify-center`}>
        <Bot className={`w-5 h-5 ${config.iconColor}`} />
      </div>
      <div className="flex-1">
        <p className="text-sm text-slate-600 capitalize">{config.name}</p>
        <p className={`text-2xl font-bold ${getScoreColor(score)}`}>
          {Math.round(score)}
        </p>
      </div>
      {/* Mini progress bar */}
      <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${
            score >= 70 ? 'bg-emerald-500' : score >= 40 ? 'bg-amber-500' : 'bg-red-500'
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
});

AIScoreCard.displayName = 'AIScoreCard';

// Main AI Scores Card
const AIScoresCard = ({ aiScores }) => {
  if (!aiScores || Object.keys(aiScores).length === 0) return null;
  
  // Sort by score descending
  const sortedScores = Object.entries(aiScores).sort((a, b) => b[1] - a[1]);
  const avgScore = Math.round(
    sortedScores.reduce((sum, [, score]) => sum + score, 0) / sortedScores.length
  );
  
  return (
    <Card className="p-6 bg-white border-slate-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900">Score par Moteur IA</h3>
        <div className="text-right">
          <span className="text-sm text-slate-500">Moyenne</span>
          <span className={`ml-2 text-lg font-bold ${getScoreColor(avgScore)}`}>{avgScore}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {sortedScores.map(([ai, score]) => (
          <AIScoreCard key={ai} aiName={ai} score={score} />
        ))}
      </div>
    </Card>
  );
};

// Recommendations Card
export const RecommendationsCard = memo(({ recommendations }) => {
  if (!recommendations || recommendations.length === 0) return null;
  
  const priorityColors = {
    critical: "border-l-red-500 bg-red-50",
    high: "border-l-orange-500 bg-orange-50",
    medium: "border-l-amber-500 bg-amber-50",
    low: "border-l-slate-400 bg-slate-50"
  };
  
  const impactBadges = {
    critique: "bg-red-100 text-red-700",
    élevé: "bg-orange-100 text-orange-700",
    moyen: "bg-amber-100 text-amber-700",
    faible: "bg-slate-100 text-slate-600"
  };
  
  return (
    <Card className="p-6 bg-white border-slate-100">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Recommandations Prioritaires</h3>
      <div className="space-y-3">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg border-l-4 ${priorityColors[rec.priority] || priorityColors.low}`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {rec.priority === "critical" && <AlertTriangle className="w-4 h-4 text-red-500" />}
                  <h4 className="text-slate-900 font-medium">{rec.title}</h4>
                </div>
                <p className="text-sm text-slate-600">{rec.description}</p>
                {rec.metrics_impacted && rec.metrics_impacted.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {rec.metrics_impacted.map((metric, idx) => (
                      <span key={idx} className="text-xs px-2 py-0.5 rounded bg-white/50 text-slate-600">
                        {metric}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <span className={`text-xs px-2 py-1 rounded-full ${impactBadges[rec.impact] || impactBadges.faible}`}>
                  Impact {rec.impact}
                </span>
                {rec.effort && (
                  <p className="text-xs text-slate-500 mt-1">Effort: {rec.effort}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
});

RecommendationsCard.displayName = 'RecommendationsCard';

export default memo(AIScoresCard);
