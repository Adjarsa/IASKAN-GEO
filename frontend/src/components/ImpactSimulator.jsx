import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Sparkles,
  TrendingUp,
  Clock,
  Target,
  CheckCircle,
  ChevronRight,
  Loader2,
  Play,
  RotateCcw,
  Zap,
  ArrowRight
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CATEGORY_COLORS = {
  content: { bg: 'bg-violet-500/20', text: 'text-violet-400', border: 'border-violet-500/30' },
  authority: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  technical: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
  engagement: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' }
};

export function ImpactSimulator({ currentScore = 50, optimizationId = null, onSimulationComplete }) {
  const [improvementOptions, setImprovementOptions] = useState(null);
  const [selectedImprovements, setSelectedImprovements] = useState([]);
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    fetchImprovementOptions();
  }, []);

  const fetchImprovementOptions = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/article-optimizer/improvement-options`, {
        withCredentials: true
      });
      setImprovementOptions(res.data.categories);
    } catch (err) {
      toast.error("Erreur lors du chargement des options");
    } finally {
      setLoading(false);
    }
  };

  const toggleImprovement = (id) => {
    setSelectedImprovements(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
    setSimulation(null); // Reset simulation when selection changes
  };

  const runSimulation = async () => {
    if (selectedImprovements.length === 0) {
      toast.error("Sélectionnez au moins une amélioration");
      return;
    }

    setSimulating(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/article-optimizer/simulate`, {
        optimization_id: optimizationId,
        overall_score: currentScore,
        improvements: selectedImprovements
      }, { withCredentials: true });
      
      setSimulation(res.data);
      if (onSimulationComplete) {
        onSimulationComplete(res.data);
      }
    } catch (err) {
      toast.error("Erreur lors de la simulation");
    } finally {
      setSimulating(false);
    }
  };

  const resetSelection = () => {
    setSelectedImprovements([]);
    setSimulation(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-400" />
            Simulateur d'Impact
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Sélectionnez les améliorations pour voir leur impact potentiel
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedImprovements.length > 0 && (
            <button
              onClick={resetSelection}
              className="px-3 py-2 bg-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-600 transition-colors flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Réinitialiser
            </button>
          )}
          <button
            onClick={runSimulation}
            disabled={selectedImprovements.length === 0 || simulating}
            className="px-4 py-2 bg-violet-500 text-white rounded-lg text-sm font-medium hover:bg-violet-600 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {simulating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Simuler ({selectedImprovements.length})
          </button>
        </div>
      </div>

      {/* Simulation Result */}
      {simulation && (
        <div className="bg-gradient-to-r from-violet-500/10 to-cyan-500/10 rounded-xl p-6 border border-violet-500/20">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h4 className="font-semibold text-white mb-1">Résultat de la Simulation</h4>
              <p className="text-sm text-slate-400">
                Impact projeté avec {simulation.simulation.improvements_applied.length} améliorations
              </p>
            </div>
            <div className={`px-3 py-1 rounded-lg text-sm ${
              simulation.confidence.level === 'high' ? 'bg-green-500/20 text-green-400' :
              simulation.confidence.level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-orange-500/20 text-orange-400'
            }`}>
              Confiance: {simulation.confidence.percentage}%
            </div>
          </div>

          {/* Score Comparison */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-slate-800/50 rounded-lg p-4 text-center">
              <p className="text-sm text-slate-400 mb-1">Score actuel</p>
              <p className="text-3xl font-bold text-slate-300">{simulation.simulation.current_score}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4 text-center flex flex-col items-center justify-center">
              <ArrowRight className="w-6 h-6 text-violet-400" />
              <p className="text-lg font-bold text-green-400 mt-1">
                +{simulation.simulation.score_improvement}
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg p-4 text-center border border-green-500/30">
              <p className="text-sm text-green-300 mb-1">Score projeté</p>
              <p className="text-3xl font-bold text-white">{simulation.simulation.projected_score}</p>
              <p className="text-sm text-green-400">{simulation.simulation.projected_grade}</p>
            </div>
          </div>

          {/* Effort Estimate */}
          <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg mb-4">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-slate-400" />
              <div>
                <p className="text-sm text-white font-medium">Effort estimé</p>
                <p className="text-xs text-slate-400">{simulation.estimated_effort.estimated_timeline}</p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded text-sm ${
              simulation.estimated_effort.overall_difficulty === 'easy' ? 'bg-green-500/20 text-green-400' :
              simulation.estimated_effort.overall_difficulty === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {simulation.estimated_effort.overall_difficulty === 'easy' ? 'Facile' :
               simulation.estimated_effort.overall_difficulty === 'medium' ? 'Moyen' : 'Difficile'}
            </div>
          </div>

          {/* Implementation Order */}
          <div>
            <h5 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
              <Target className="w-4 h-4 text-violet-400" />
              Ordre d'implémentation recommandé
            </h5>
            <div className="space-y-2">
              {simulation.recommendations.slice(0, 5).map((rec, i) => (
                <div key={rec.improvement} className="flex items-center gap-3 text-sm">
                  <span className="w-6 h-6 bg-violet-500/20 text-violet-400 rounded-full flex items-center justify-center text-xs font-bold">
                    {i + 1}
                  </span>
                  <span className="text-slate-300 flex-1">{rec.improvement.replace(/_/g, ' ')}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    rec.impact === 'high' ? 'bg-green-500/20 text-green-400' :
                    rec.impact === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-slate-600 text-slate-400'
                  }`}>
                    {rec.impact}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Improvement Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {improvementOptions && Object.entries(improvementOptions).map(([category, data]) => {
          const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.content;
          const selectedInCategory = data.improvements.filter(imp => 
            selectedImprovements.includes(imp.id)
          ).length;

          return (
            <div key={category} className={`rounded-xl border ${colors.border} overflow-hidden`}>
              <div className={`${colors.bg} px-4 py-3 flex items-center justify-between`}>
                <h4 className={`font-medium ${colors.text}`}>{data.name}</h4>
                {selectedInCategory > 0 && (
                  <span className="px-2 py-0.5 bg-white/10 rounded text-xs text-white">
                    {selectedInCategory} sélectionné(s)
                  </span>
                )}
              </div>
              <div className="p-3 space-y-2 bg-slate-900/30">
                {data.improvements.map(imp => {
                  const isSelected = selectedImprovements.includes(imp.id);
                  return (
                    <button
                      key={imp.id}
                      onClick={() => toggleImprovement(imp.id)}
                      className={`w-full text-left p-3 rounded-lg transition-all flex items-center gap-3 ${
                        isSelected 
                          ? `${colors.bg} ${colors.border} border` 
                          : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        isSelected 
                          ? `${colors.border} ${colors.bg}` 
                          : 'border-slate-600'
                      }`}>
                        {isSelected && <CheckCircle className={`w-4 h-4 ${colors.text}`} />}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-white">{imp.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            imp.impact === 'high' ? 'bg-green-500/20 text-green-400' :
                            imp.impact === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-slate-600 text-slate-400'
                          }`}>
                            Impact {imp.impact}
                          </span>
                          <span className="text-xs text-slate-500">
                            • {imp.effort === 'easy' ? 'Facile' : imp.effort === 'medium' ? 'Moyen' : 'Difficile'}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ImpactSimulator;
