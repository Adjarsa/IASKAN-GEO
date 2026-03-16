import { memo, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { 
  CheckCircle2, XCircle, AlertTriangle, Zap, Clock, Target, BookOpen, ChevronRight 
} from "lucide-react";

// Score utilities
export const getScoreColor = (score) => {
  if (score >= 70) return { text: "text-emerald-500", bg: "bg-emerald-500", light: "bg-emerald-500/10" };
  if (score >= 50) return { text: "text-amber-500", bg: "bg-amber-500", light: "bg-amber-500/10" };
  return { text: "text-red-500", bg: "bg-red-500", light: "bg-red-500/10" };
};

// Circular Score Component
export const CircularScore = memo(({ score, size = "md", label }) => {
  const colors = getScoreColor(score);
  const sizes = {
    sm: { container: "w-16 h-16", text: "text-lg", stroke: 8, radius: 24 },
    md: { container: "w-20 h-20", text: "text-2xl", stroke: 10, radius: 32 },
    lg: { container: "w-28 h-28", text: "text-3xl", stroke: 12, radius: 44 }
  };
  const s = sizes[size];
  const circumference = 2 * Math.PI * s.radius;
  const progress = (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`${s.container} relative`}>
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="50%" cy="50%" r={s.radius}
            stroke="currentColor"
            strokeWidth={s.stroke}
            fill="none"
            className="text-slate-700"
          />
          <circle
            cx="50%" cy="50%" r={s.radius}
            stroke="url(#optimizerGradient)"
            strokeWidth={s.stroke}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={`${progress} ${circumference}`}
            className="transition-all duration-500"
          />
          <defs>
            <linearGradient id="optimizerGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#7c3aed" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`font-bold ${s.text} ${colors.text}`}>{Math.round(score)}</span>
        </div>
      </div>
      {label && <span className="text-xs text-slate-400 text-center">{label}</span>}
    </div>
  );
});

CircularScore.displayName = 'CircularScore';

// Score Cards Grid
export const ScoreCardsGrid = memo(({ scores }) => {
  const scoreItems = [
    { key: 'overall', label: 'Global', size: 'md' },
    { key: 'structure', label: 'Structure', size: 'sm' },
    { key: 'authority', label: 'Autorité', size: 'sm' },
    { key: 'citability', label: 'Citabilité', size: 'sm' },
    { key: 'freshness', label: 'Fraîcheur', size: 'sm' }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {scoreItems.map(({ key, label, size }) => (
        <Card key={key} className="bg-slate-800/50 border-slate-700 p-4 flex flex-col items-center">
          <CircularScore score={scores?.[key] || 0} size={size} />
          <p className="text-sm text-slate-300 mt-2">{label}</p>
        </Card>
      ))}
    </div>
  );
});

ScoreCardsGrid.displayName = 'ScoreCardsGrid';

// Diagnostic Card Component
export const DiagnosticCard = memo(({ diagnostic }) => {
  const severityConfig = {
    critical: { border: "border-l-red-500", bg: "bg-red-500/5", icon: XCircle, iconColor: "text-red-500" },
    high: { border: "border-l-orange-500", bg: "bg-orange-500/5", icon: AlertTriangle, iconColor: "text-orange-500" },
    medium: { border: "border-l-amber-500", bg: "bg-amber-500/5", icon: AlertTriangle, iconColor: "text-amber-500" },
    low: { border: "border-l-cyan-500", bg: "bg-cyan-500/5", icon: CheckCircle2, iconColor: "text-cyan-500" }
  };

  const config = severityConfig[diagnostic.severity] || severityConfig.medium;
  const Icon = config.icon;

  return (
    <div className={`p-4 rounded-lg border-l-4 ${config.border} ${config.bg}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs uppercase font-semibold text-slate-400">{diagnostic.category}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${config.bg} ${config.iconColor}`}>
              {diagnostic.severity}
            </span>
          </div>
          <p className="text-sm text-white font-medium mb-1">{diagnostic.issue}</p>
          <p className="text-sm text-slate-400">{diagnostic.recommendation}</p>
        </div>
      </div>
    </div>
  );
});

DiagnosticCard.displayName = 'DiagnosticCard';

// Diagnostics List Component
export const DiagnosticsList = memo(({ diagnostics }) => {
  if (!diagnostics || diagnostics.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-emerald-500" />
        <p>Aucun problème majeur détecté</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {diagnostics.map((diag, i) => (
        <DiagnosticCard key={i} diagnostic={diag} />
      ))}
    </div>
  );
});

DiagnosticsList.displayName = 'DiagnosticsList';

// Action Item Component
const ActionItem = memo(({ action, phase }) => {
  const phaseConfig = {
    immediate: { color: "bg-red-500" },
    short_term: { color: "bg-orange-500" },
    medium_term: { color: "bg-amber-500" },
    long_term: { color: "bg-cyan-500" }
  };

  const config = phaseConfig[phase] || phaseConfig.medium_term;

  return (
    <div className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800/70 transition-colors">
      <div className={`w-2 h-2 mt-2 rounded-full flex-shrink-0 ${config.color}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white">{action.action}</p>
        {action.query && (
          <p className="text-xs text-slate-400 mt-1 truncate">Requête: "{action.query}"</p>
        )}
      </div>
    </div>
  );
});

ActionItem.displayName = 'ActionItem';

// Action Plan Component
export const ActionPlan = memo(({ actionPlan }) => {
  const phases = useMemo(() => [
    { key: 'immediate', label: 'Actions immédiates', icon: Zap, color: 'text-red-400' },
    { key: 'short_term', label: 'Court terme (1-2 semaines)', icon: Clock, color: 'text-orange-400' },
    { key: 'medium_term', label: 'Moyen terme (1 mois)', icon: Target, color: 'text-amber-400' },
    { key: 'long_term', label: 'Long terme (3+ mois)', icon: BookOpen, color: 'text-cyan-400' }
  ], []);

  if (!actionPlan) return null;

  return (
    <div className="space-y-6">
      {phases.map(({ key, label, icon: Icon, color }) => {
        const data = actionPlan[key];
        if (!data?.actions?.length) return null;
        
        return (
          <div key={key}>
            <h3 className={`text-base font-semibold mb-3 flex items-center gap-2 ${color}`}>
              <Icon className="w-5 h-5" />
              {label}
            </h3>
            <div className="space-y-2">
              {data.actions.map((action, i) => (
                <ActionItem key={i} action={action} phase={key} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
});

ActionPlan.displayName = 'ActionPlan';

// Quick Wins Component
export const QuickWins = memo(({ quickWins }) => {
  if (!quickWins?.length) return null;

  return (
    <div>
      <h3 className="text-base font-semibold mb-3 flex items-center gap-2 text-amber-400">
        <Zap className="w-5 h-5" />
        Quick Wins
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {quickWins.map((win, i) => (
          <div key={i} className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <p className="text-sm text-white mb-2">{win.action}</p>
            <div className="flex gap-2">
              <span className="text-xs px-2 py-0.5 bg-slate-700 rounded text-slate-300">
                Effort: {win.effort}
              </span>
              <span className="text-xs px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">
                Impact: {win.impact}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

QuickWins.displayName = 'QuickWins';

// Missing Elements Component
export const MissingElements = memo(({ elements }) => {
  if (!elements?.length) return null;

  return (
    <div>
      <h3 className="text-base font-semibold mb-3 flex items-center gap-2 text-red-400">
        <XCircle className="w-5 h-5" />
        Éléments manquants
      </h3>
      <div className="flex flex-wrap gap-2">
        {elements.map((el, i) => (
          <span key={i} className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-sm text-red-400">
            {el}
          </span>
        ))}
      </div>
    </div>
  );
});

MissingElements.displayName = 'MissingElements';

// Keyword Opportunities Component
export const KeywordOpportunities = memo(({ opportunities }) => {
  if (!opportunities?.length) return null;

  return (
    <div>
      <h3 className="text-base font-semibold mb-3 flex items-center gap-2 text-violet-400">
        <BookOpen className="w-5 h-5" />
        Opportunités de mots-clés
      </h3>
      <ul className="space-y-2">
        {opportunities.map((opp, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
            <ChevronRight className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
            <span>{opp}</span>
          </li>
        ))}
      </ul>
    </div>
  );
});

KeywordOpportunities.displayName = 'KeywordOpportunities';

// Distribution Strategy Component
export const DistributionStrategy = memo(({ strategy }) => {
  if (!strategy?.length) return null;

  return (
    <div className="space-y-3">
      {strategy.map((strat, i) => (
        <Card key={i} className="p-4 bg-slate-800/50 border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-white">{strat.channel}</h4>
            <span className={`text-xs px-2 py-1 rounded ${
              strat.priority === 'high' ? 'bg-emerald-500/20 text-emerald-400' :
              strat.priority === 'medium' ? 'bg-amber-500/20 text-amber-400' :
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
        </Card>
      ))}
    </div>
  );
});

DistributionStrategy.displayName = 'DistributionStrategy';

export default CircularScore;
