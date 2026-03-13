import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Target,
  TrendingUp,
  Clock,
  CheckCircle2,
  ChevronRight,
  Loader2,
  Award,
  Zap,
  ArrowRight,
  Flag,
  Star
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const GRADE_CONFIG = {
  A: { color: 'emerald', bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  B: { color: 'cyan', bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  C: { color: 'amber', bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  D: { color: 'red', bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' }
};

const EFFORT_CONFIG = {
  low: { label: 'Facile', color: 'text-green-400', bg: 'bg-green-500/20' },
  medium: { label: 'Moyen', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  high: { label: 'Difficile', color: 'text-red-400', bg: 'bg-red-500/20' }
};

const CATEGORY_ICONS = {
  content: '📝',
  authority: '🛡️',
  technical: '⚙️',
  engagement: '👥'
};

export function AutomaticObjectives({ 
  analysisId = null, 
  currentScore = 50, 
  targetGrade = null,
  showAllPaths = false,
  onObjectiveSelected = null
}) {
  const [objective, setObjective] = useState(null);
  const [allPaths, setAllPaths] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPath, setSelectedPath] = useState(targetGrade);
  const [expandedAction, setExpandedAction] = useState(null);

  useEffect(() => {
    if (analysisId) {
      fetchObjectiveFromAnalysis();
    } else if (showAllPaths) {
      fetchAllPaths();
    } else {
      fetchObjective();
    }
  }, [analysisId, currentScore, targetGrade, showAllPaths]);

  const fetchObjective = async () => {
    try {
      setLoading(true);
      const params = targetGrade ? `?target_grade=${targetGrade}` : '';
      const res = await axios.get(`${BACKEND_URL}/api/strategy/objective/${Math.round(currentScore)}${params}`, {
        withCredentials: true
      });
      setObjective(res.data);
    } catch (err) {
      console.error('Error fetching objective:', err);
      toast.error("Erreur lors du chargement de l'objectif");
    } finally {
      setLoading(false);
    }
  };

  const fetchObjectiveFromAnalysis = async () => {
    try {
      setLoading(true);
      const params = targetGrade ? `?target_grade=${targetGrade}` : '';
      const res = await axios.get(`${BACKEND_URL}/api/strategy/objective/from-analysis/${analysisId}${params}`, {
        withCredentials: true
      });
      setObjective(res.data);
    } catch (err) {
      console.error('Error fetching objective from analysis:', err);
      toast.error("Erreur lors du chargement de l'objectif");
    } finally {
      setLoading(false);
    }
  };

  const fetchAllPaths = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${BACKEND_URL}/api/strategy/paths/${Math.round(currentScore)}`, {
        withCredentials: true
      });
      setAllPaths(res.data);
      
      // Select first available path by default
      const paths = res.data.available_paths;
      if (paths && Object.keys(paths).length > 0) {
        const firstGrade = Object.keys(paths)[0];
        setSelectedPath(firstGrade);
        setObjective(paths[firstGrade]);
      }
    } catch (err) {
      console.error('Error fetching all paths:', err);
      toast.error("Erreur lors du chargement des objectifs");
    } finally {
      setLoading(false);
    }
  };

  const selectPath = (grade) => {
    if (allPaths?.available_paths?.[grade]) {
      setSelectedPath(grade);
      setObjective(allPaths.available_paths[grade]);
      if (onObjectiveSelected) {
        onObjectiveSelected(grade, allPaths.available_paths[grade]);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  if (!objective) {
    return (
      <div className="text-center py-8 text-slate-400">
        <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>Aucun objectif disponible</p>
      </div>
    );
  }

  const { objective: obj, actions, timeline, probability, milestones } = objective;
  const currentGradeConfig = GRADE_CONFIG[obj.current_grade] || GRADE_CONFIG.D;
  const targetGradeConfig = GRADE_CONFIG[obj.target_grade] || GRADE_CONFIG.A;

  // Already achieved
  if (obj.status === 'achieved') {
    return (
      <div className="space-y-4">
        <div className={`rounded-xl p-6 ${targetGradeConfig.bg} border ${targetGradeConfig.border}`}>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center">
              <Award className={`w-8 h-8 ${targetGradeConfig.text}`} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-400" />
                Objectif atteint !
              </h3>
              <p className="text-slate-300 mt-1">{obj.message}</p>
            </div>
          </div>
          
          <div className="mt-6 flex items-center justify-center gap-4">
            <div className="text-center">
              <p className="text-sm text-slate-400">Score actuel</p>
              <p className={`text-4xl font-bold ${targetGradeConfig.text}`}>{Math.round(obj.current_score)}</p>
              <p className="text-lg font-semibold text-white">Note {obj.current_grade}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Path selector if showing all paths */}
      {showAllPaths && allPaths?.available_paths && Object.keys(allPaths.available_paths).length > 1 && (
        <div className="flex gap-2 flex-wrap">
          {Object.keys(allPaths.available_paths).map((grade) => {
            const config = GRADE_CONFIG[grade] || GRADE_CONFIG.A;
            const path = allPaths.available_paths[grade];
            return (
              <button
                key={grade}
                onClick={() => selectPath(grade)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  selectedPath === grade
                    ? `${config.bg} ${config.text} border ${config.border}`
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
                data-testid={`path-selector-${grade}`}
              >
                Objectif {grade}
                <span className="ml-2 text-xs opacity-70">
                  (+{Math.round(path.objective.points_needed)} pts)
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Header - Score progression */}
      <div className="bg-gradient-to-r from-slate-800/50 to-slate-900/50 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-violet-400" />
            Objectif Automatique
          </h3>
          {probability && (
            <div className={`px-3 py-1 rounded-full text-sm ${
              probability.level === 'high' ? 'bg-green-500/20 text-green-400' :
              probability.level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {probability.percentage}% de réussite
            </div>
          )}
        </div>

        {/* Score comparison */}
        <div className="flex items-center justify-between gap-4">
          {/* Current */}
          <div className="flex-1 text-center">
            <div className={`w-20 h-20 mx-auto rounded-full ${currentGradeConfig.bg} border-2 ${currentGradeConfig.border} flex items-center justify-center mb-2`}>
              <span className={`text-3xl font-bold ${currentGradeConfig.text}`}>
                {obj.current_grade}
              </span>
            </div>
            <p className="text-sm text-slate-400">Actuel</p>
            <p className="text-2xl font-bold text-white">{Math.round(obj.current_score)}</p>
          </div>

          {/* Arrow with actions count */}
          <div className="flex flex-col items-center px-4">
            <div className="flex items-center gap-2 text-violet-400 mb-2">
              <ArrowRight className="w-8 h-8" />
            </div>
            <p className="text-sm text-slate-300 bg-violet-500/20 px-3 py-1 rounded-full">
              {actions?.length || 0} actions
            </p>
            <p className="text-xs text-slate-500 mt-1">+{Math.round(obj.points_needed)} pts</p>
          </div>

          {/* Target */}
          <div className="flex-1 text-center">
            <div className={`w-20 h-20 mx-auto rounded-full ${targetGradeConfig.bg} border-2 ${targetGradeConfig.border} flex items-center justify-center mb-2`}>
              <span className={`text-3xl font-bold ${targetGradeConfig.text}`}>
                {obj.target_grade}
              </span>
            </div>
            <p className="text-sm text-slate-400">Objectif</p>
            <p className="text-2xl font-bold text-white">{obj.target_score}</p>
          </div>
        </div>

        {/* Timeline and info */}
        <div className="flex items-center justify-center gap-6 mt-6 pt-4 border-t border-slate-700">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <Clock className="w-4 h-4 text-slate-400" />
            <span>Durée estimée: <strong>{timeline}</strong></span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <TrendingUp className="w-4 h-4 text-slate-400" />
            <span>Points projetés: <strong className="text-green-400">+{Math.round(obj.projected_points)}</strong></span>
          </div>
        </div>
      </div>

      {/* Milestones */}
      {milestones && milestones.length > 0 && (
        <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
          <h4 className="font-medium text-white mb-4 flex items-center gap-2">
            <Flag className="w-4 h-4 text-violet-400" />
            Jalons de progression
          </h4>
          <div className="flex items-center justify-between">
            {milestones.map((milestone, i) => (
              <div key={i} className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${
                  milestone.status === 'completed' 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-slate-700 text-slate-400'
                }`}>
                  {milestone.status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <span className="text-sm font-bold">{milestone.number}</span>
                  )}
                </div>
                <p className="text-xs text-slate-400">Score {Math.round(milestone.target_score)}</p>
                {i < milestones.length - 1 && (
                  <div className="absolute w-full h-0.5 bg-slate-700 top-5 left-1/2" style={{width: 'calc(100% - 40px)', marginLeft: '20px'}}></div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions list */}
      {actions && actions.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            Plan d'action ({actions.length} étapes)
          </h4>
          
          {actions.map((action, i) => {
            const effortConfig = EFFORT_CONFIG[action.effort] || EFFORT_CONFIG.medium;
            const isExpanded = expandedAction === i;
            
            return (
              <div 
                key={i}
                className={`rounded-lg border transition-all ${
                  action.priority === 'critical' ? 'border-red-500/30 bg-red-500/5' :
                  action.priority === 'high' ? 'border-orange-500/30 bg-orange-500/5' :
                  'border-slate-700 bg-slate-800/30'
                }`}
              >
                <button
                  onClick={() => setExpandedAction(isExpanded ? null : i)}
                  className="w-full p-4 flex items-center gap-3 text-left"
                  data-testid={`action-${i}`}
                >
                  <div className="w-8 h-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {i + 1}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg" title={action.category}>
                        {CATEGORY_ICONS[action.category] || '📋'}
                      </span>
                      <span className="font-medium text-white truncate">{action.title}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`px-2 py-0.5 rounded ${effortConfig.bg} ${effortConfig.color}`}>
                        {effortConfig.label}
                      </span>
                      <span className="text-slate-500">•</span>
                      <span className="text-green-400">+{Math.round(action.estimated_impact)} pts</span>
                      <span className="text-slate-500">•</span>
                      <span className="text-slate-400">{action.timeline}</span>
                    </div>
                  </div>
                  
                  <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </button>
                
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-slate-700/50 pt-3">
                    <div className="flex items-center gap-4 text-sm text-slate-300">
                      <div className="flex items-center gap-2">
                        <Star className="w-4 h-4 text-violet-400" />
                        <span>Priorité: <strong className="capitalize">{action.priority}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-violet-400" />
                        <span>Catégorie: <strong className="capitalize">{action.category}</strong></span>
                      </div>
                    </div>
                    <p className="text-sm text-slate-400 mt-2">
                      Impact estimé de +{Math.round(action.estimated_impact)} points sur votre score global.
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Summary message */}
      <div className="text-center p-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
        <p className="text-sm text-slate-300">{obj.message}</p>
      </div>
    </div>
  );
}

export default AutomaticObjectives;
