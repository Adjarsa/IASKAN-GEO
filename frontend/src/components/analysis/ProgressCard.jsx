import { memo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Shield, Loader2, CheckCircle2 } from "lucide-react";

// Analysis phases configuration
const PHASES = [
  { id: "query_generation", label: "Génération des requêtes", icon: "🎯" },
  { id: "ai_querying", label: "Interrogation des moteurs IA", icon: "🤖" },
  { id: "calculating_indices", label: "Calcul des indices", icon: "📊" }
];

// Calculate progress percentage based on phase and queries
const calculateProgress = (phase, queriesProcessed, totalQueries) => {
  const phaseIndex = PHASES.findIndex(p => p.id === phase);
  if (phaseIndex === -1) return 10;
  
  if (phase === "query_generation") return 20;
  if (phase === "calculating_indices") return 90;
  if (phase === "ai_querying") {
    const queryProgress = totalQueries > 0 
      ? Math.round((queriesProcessed / totalQueries) * 60) 
      : 30;
    return Math.min(20 + queryProgress, 80);
  }
  return 10;
};

// Running Analysis Card
export const RunningAnalysisCard = memo(({ analysis }) => {
  const currentPhase = analysis.current_phase || "query_generation";
  const queriesProcessed = analysis.queries_processed || 0;
  const totalQueries = analysis.total_queries || 0;
  const progress = calculateProgress(currentPhase, queriesProcessed, totalQueries);
  
  return (
    <Card className="p-6 border-violet-200 bg-gradient-to-br from-violet-50 to-cyan-50">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="relative w-14 h-14 flex-shrink-0">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-30"></div>
            <div className="absolute inset-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Analyse en cours</h3>
            <p className="text-sm text-slate-600">IAskan Verified™ Protocol</p>
          </div>
        </div>
        
        {/* Progress Steps */}
        <div className="space-y-2">
          {PHASES.map((step) => {
            const phaseIndex = PHASES.findIndex(p => p.id === step.id);
            const currentIndex = PHASES.findIndex(p => p.id === currentPhase);
            const isComplete = phaseIndex < currentIndex;
            const isCurrent = step.id === currentPhase;
            
            return (
              <div 
                key={step.id}
                className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                  isCurrent 
                    ? 'bg-white shadow-sm border border-violet-200' 
                    : isComplete 
                      ? 'bg-emerald-50/50 border border-emerald-100' 
                      : 'bg-white/50 border border-slate-100 opacity-50'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  isCurrent 
                    ? 'bg-gradient-to-r from-violet-600 to-cyan-600 text-white' 
                    : isComplete 
                      ? 'bg-emerald-500 text-white'
                      : 'bg-slate-100 text-slate-400'
                }`}>
                  {isComplete ? <CheckCircle2 className="w-4 h-4" /> : isCurrent ? <Loader2 className="w-4 h-4 animate-spin" /> : step.icon}
                </div>
                <span className={`flex-1 text-sm ${isCurrent ? 'font-medium text-slate-900' : isComplete ? 'text-emerald-700' : 'text-slate-400'}`}>
                  {step.label}
                  {isCurrent && step.id === "ai_querying" && totalQueries > 0 && (
                    <span className="text-violet-600 ml-1">({queriesProcessed}/{totalQueries})</span>
                  )}
                </span>
                {isCurrent && (
                  <span className="text-xs px-2 py-1 rounded-full bg-violet-100 text-violet-700 animate-pulse">
                    En cours
                  </span>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Global Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-slate-600">Progression</span>
            <span className="text-violet-600 font-medium">{progress}%</span>
          </div>
          <div className="w-full bg-white rounded-full h-2.5 overflow-hidden shadow-inner">
            <div 
              className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        
        {/* Protocol badges */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs px-3 py-1.5 rounded-full bg-white border border-violet-200 text-violet-700">
            🔄 Multi-runs (3x)
          </span>
          <span className="text-xs px-3 py-1.5 rounded-full bg-white border border-cyan-200 text-cyan-700">
            🤖 Multi-IA
          </span>
          <span className="text-xs px-3 py-1.5 rounded-full bg-white border border-emerald-200 text-emerald-700">
            🛡️ Anti-hallucination
          </span>
        </div>
      </div>
    </Card>
  );
});

RunningAnalysisCard.displayName = 'RunningAnalysisCard';

// Starting Analysis Card (Full screen loader)
export const StartingAnalysisCard = memo(() => (
  <Card className="p-8 max-w-lg w-full mx-auto bg-white border-slate-100">
    <div className="text-center space-y-6">
      <div className="relative mx-auto w-20 h-20">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-30"></div>
        <div className="absolute inset-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
          <Shield className="w-8 h-8 text-white" />
        </div>
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
      </div>
      
      <div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">
          Lancement de l'analyse...
        </h3>
        <p className="text-slate-600 text-sm">
          Initialisation du protocole IAskan Verified™
        </p>
      </div>
      
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
        <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
      </div>
    </div>
  </Card>
));

StartingAnalysisCard.displayName = 'StartingAnalysisCard';

// Loading Analysis Card
export const LoadingAnalysisCard = memo(() => (
  <Card className="p-8 max-w-lg w-full mx-auto bg-white border-slate-100">
    <div className="text-center space-y-6">
      <div className="relative mx-auto w-16 h-16">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-20"></div>
        <div className="absolute inset-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Chargement...</h3>
        <p className="text-slate-600 text-sm">Récupération des données d'analyse</p>
      </div>
      
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
        <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
      </div>
    </div>
  </Card>
));

LoadingAnalysisCard.displayName = 'LoadingAnalysisCard';

export default RunningAnalysisCard;
