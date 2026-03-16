import { Shield, TrendingUp, Target, Activity, CheckCircle2, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/card";

// Score color utility
export const getScoreColor = (score) => {
  if (score >= 70) return "text-emerald-600";
  if (score >= 40) return "text-amber-600";
  return "text-red-600";
};

// Grade color utility
export const getGradeColor = (grade) => {
  const colors = {
    "A": "bg-emerald-100 text-emerald-700 border-emerald-200",
    "B": "bg-cyan-100 text-cyan-700 border-cyan-200",
    "C": "bg-amber-100 text-amber-700 border-amber-200",
    "D": "bg-orange-100 text-orange-700 border-orange-200",
    "F": "bg-red-100 text-red-700 border-red-200"
  };
  return colors[grade] || "bg-slate-100 text-slate-700 border-slate-200";
};

// Main Score Card Component
export const GlobalScoreCard = ({ analysis }) => {
  const rateScore = analysis.rate_score || {};
  
  return (
    <Card className="p-6 bg-white border-slate-100">
      <div className="grid md:grid-cols-2 gap-8 items-center">
        {/* Left: Global Score */}
        <div className="text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-3 mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Score GEO Global</h2>
            {analysis.grade && (
              <span className={`text-xl font-bold px-3 py-1 rounded-lg border ${getGradeColor(analysis.grade)}`}>
                {analysis.grade}
              </span>
            )}
          </div>
          
          {/* Score Circle */}
          <div className="relative inline-flex items-center justify-center">
            <svg className="w-36 h-36 transform -rotate-90">
              <circle cx="72" cy="72" r="64" stroke="#e2e8f0" strokeWidth="12" fill="none" />
              <circle
                cx="72" cy="72" r="64"
                stroke="url(#scoreGradient)"
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${(analysis.global_score / 100) * 402} 402`}
              />
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#7c3aed" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-4xl font-bold ${getScoreColor(analysis.global_score)}`}>
                {Math.round(analysis.global_score)}
              </span>
              <span className="text-sm text-slate-500">/ 100</span>
            </div>
          </div>
          
          {/* Protocol Badge */}
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-violet-50 to-cyan-50 border border-violet-100">
            <Shield className="w-4 h-4 text-violet-600" />
            <span className="text-xs font-medium text-slate-700">IAskan Verified™</span>
          </div>
        </div>

        {/* Right: R.A.T.E Breakdown */}
        {rateScore && Object.keys(rateScore).length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-600 mb-4">Score R.A.T.E™</h3>
            {[
              { key: "relevance", label: "Relevance", color: "from-violet-500 to-violet-600", desc: "Pertinence des mentions" },
              { key: "authority", label: "Authority", color: "from-cyan-500 to-cyan-600", desc: "Autorité perçue" },
              { key: "truthfulness", label: "Truthfulness", color: "from-emerald-500 to-emerald-600", desc: "Exactitude des infos" },
              { key: "endorsement", label: "Endorsement", color: "from-amber-500 to-amber-600", desc: "Recommandation" }
            ].map((item) => (
              <div key={item.key} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">{item.label}</span>
                  <span className="font-semibold text-slate-900">
                    {Math.round(rateScore[item.key] || 0)}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${item.color} rounded-full transition-all duration-500`}
                    style={{ width: `${rateScore[item.key] || 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};

// Indices Card Component
export const IndicesCard = ({ indices }) => {
  if (!indices || Object.keys(indices).length === 0) return null;
  
  const getStabilityStatus = (score) => {
    if (score >= 80) return { label: "Élevée", color: "text-emerald-600", bg: "bg-emerald-50", icon: CheckCircle2 };
    if (score >= 60) return { label: "Moyenne", color: "text-amber-600", bg: "bg-amber-50", icon: Activity };
    return { label: "Faible", color: "text-red-600", bg: "bg-red-50", icon: AlertTriangle };
  };
  
  const stabilityStatus = getStabilityStatus(indices.stability_index || 0);
  
  const indicesData = [
    {
      key: "stability_index",
      label: "Stability Index™",
      desc: "Cohérence des réponses",
      icon: stabilityStatus.icon,
      gradient: "from-violet-50 to-violet-100",
      border: "border-violet-200",
      iconColor: stabilityStatus.color
    },
    {
      key: "dominance_index",
      label: "Dominance Index™",
      desc: "Position vs concurrents",
      icon: TrendingUp,
      gradient: "from-cyan-50 to-cyan-100",
      border: "border-cyan-200",
      iconColor: "text-cyan-600"
    },
    {
      key: "trust_gap",
      label: "Trust Gap™",
      desc: "Écart de confiance",
      icon: Shield,
      gradient: "from-emerald-50 to-emerald-100",
      border: "border-emerald-200",
      iconColor: "text-emerald-600",
      showSign: true
    },
    {
      key: "opportunity_score",
      label: "Opportunity Score™",
      desc: "Potentiel d'amélioration",
      icon: Target,
      gradient: "from-amber-50 to-amber-100",
      border: "border-amber-200",
      iconColor: "text-amber-600"
    }
  ];
  
  return (
    <Card className="p-6 bg-white border-slate-100">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Indices Avancés</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {indicesData.map(({ key, label, desc, icon: Icon, gradient, border, iconColor, showSign }) => {
          const value = indices[key] || 0;
          const displayValue = showSign && value >= 0 ? `+${Math.round(value)}` : Math.round(value);
          
          return (
            <div key={key} className={`p-4 rounded-xl bg-gradient-to-br ${gradient} border ${border}`}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${iconColor}`} />
                <span className="text-xs font-medium text-slate-600">{label}</span>
              </div>
              <div className={`text-2xl font-bold ${iconColor}`}>
                {displayValue}{!showSign && '%'}
              </div>
              <p className="text-xs text-slate-500 mt-1">{desc}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default GlobalScoreCard;
