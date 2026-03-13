import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Target,
  TrendingUp,
  Award,
  ChevronRight,
  CheckCircle,
  Clock,
  Loader2,
  Sparkles,
  ArrowUp,
  Trophy
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const GRADE_COLORS = {
  A: { bg: 'bg-green-500', text: 'text-green-400', border: 'border-green-500' },
  B: { bg: 'bg-cyan-500', text: 'text-cyan-400', border: 'border-cyan-500' },
  C: { bg: 'bg-yellow-500', text: 'text-yellow-400', border: 'border-yellow-500' },
  D: { bg: 'bg-red-500', text: 'text-red-400', border: 'border-red-500' }
};

export function GradeObjective({ currentScore, analysisId, onActionSelect }) {
  const [objective, setObjective] = useState(null);
  const [allPaths, setAllPaths] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedGrade, setSelectedGrade] = useState(null);
  const [showAllPaths, setShowAllPaths] = useState(false);

  useEffect(() => {
    fetchObjective();
  }, [currentScore, analysisId]);

  const fetchObjective = async () => {
    setLoading(true);
    try {
      let res;
      if (analysisId) {
        res = await axios.get(`${BACKEND_URL}/api/strategy/objective/from-analysis/${analysisId}`, {
          withCredentials: true
        });
      } else {
        res = await axios.get(`${BACKEND_URL}/api/strategy/objective/${Math.round(currentScore)}`, {
          withCredentials: true
        });
      }
      setObjective(res.data);
      
      // Also fetch all paths
      const pathsRes = await axios.get(`${BACKEND_URL}/api/strategy/paths/${Math.round(currentScore)}`, {
        withCredentials: true
      });
      setAllPaths(pathsRes.data);
    } catch (err) {
      console.error('Objective fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectTargetGrade = async (grade) => {
    setSelectedGrade(grade);
    setLoading(true);
    try {
      const res = await axios.get(
        `${BACKEND_URL}/api/strategy/objective/${Math.round(currentScore)}?target_grade=${grade}`,
        { withCredentials: true }
      );
      setObjective(res.data);
    } catch (err) {
      console.error('Grade selection error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !objective) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-violet-500" />
      </div>
    );
  }

  if (!objective) return null;

  const { objective: obj, actions, timeline, probability, milestones } = objective;
  const currentColors = GRADE_COLORS[obj.current_grade] || GRADE_COLORS.C;
  const targetColors = GRADE_COLORS[obj.target_grade] || GRADE_COLORS.B;

  return (
    <div className="space-y-4">
      {/* Header with Grade Transition */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-violet-400" />
            Objectif Automatique
          </h3>
          <button
            onClick={() => setShowAllPaths(!showAllPaths)}
            className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
          >
            {showAllPaths ? 'Masquer options' : 'Voir autres objectifs'}
          </button>
        </div>

        {/* Grade Transition Visual */}
        <div className="flex items-center justify-center gap-4 py-4">
          {/* Current Grade */}
          <div className="text-center">
            <div className={`w-20 h-20 rounded-full ${currentColors.bg}/20 border-2 ${currentColors.border} flex items-center justify-center mb-2`}>
              <span className={`text-3xl font-bold ${currentColors.text}`}>{obj.current_grade}</span>
            </div>
            <p className="text-sm text-slate-400">{obj.current_grade_name}</p>
            <p className="text-xs text-slate-500">{obj.current_score} pts</p>
          </div>

          {/* Arrow */}
          {obj.status !== 'achieved' && (
            <>
              <div className="flex flex-col items-center">
                <ArrowUp className="w-8 h-8 text-violet-400 rotate-90" />
                <span className="text-xs text-violet-400 mt-1">+{obj.points_needed} pts</span>
              </div>

              {/* Target Grade */}
              <div className="text-center">
                <div className={`w-20 h-20 rounded-full ${targetColors.bg}/20 border-2 ${targetColors.border} flex items-center justify-center mb-2 ring-4 ring-${targetColors.bg}/20`}>
                  <span className={`text-3xl font-bold ${targetColors.text}`}>{obj.target_grade}</span>
                </div>
                <p className="text-sm text-slate-400">{obj.target_grade_name}</p>
                <p className="text-xs text-slate-500">{obj.target_score} pts</p>
              </div>
            </>
          )}

          {obj.status === 'achieved' && (
            <div className="text-center ml-4">
              <Trophy className="w-12 h-12 text-yellow-400 mx-auto mb-2" />
              <p className="text-green-400 font-medium">Objectif atteint !</p>
            </div>
          )}
        </div>

        {/* Message */}
        <p className="text-center text-slate-300 mt-2">{obj.message}</p>

        {/* All Paths Option */}
        {showAllPaths && allPaths?.available_paths && (
          <div className="mt-4 pt-4 border-t border-slate-700">
            <p className="text-sm text-slate-400 mb-3">Choisir un autre objectif :</p>
            <div className="flex gap-2 justify-center">
              {Object.entries(allPaths.available_paths).map(([grade, data]) => {
                const colors = GRADE_COLORS[grade];
                return (
                  <button
                    key={grade}
                    onClick={() => selectTargetGrade(grade)}
                    className={`px-4 py-2 rounded-lg transition-all ${
                      selectedGrade === grade
                        ? `${colors.bg} text-white`
                        : `${colors.bg}/20 ${colors.text} hover:${colors.bg}/30`
                    }`}
                  >
                    <span className="font-bold">{grade}</span>
                    <span className="text-xs ml-1">+{data.objective.points_needed}pts</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Actions Required */}
      {obj.status !== 'achieved' && actions && actions.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              Plan d'action ({actions.length} étapes)
            </h4>
            <div className="flex items-center gap-2 text-sm">
              <Clock className="w-4 h-4 text-slate-400" />
              <span className="text-slate-400">{timeline}</span>
            </div>
          </div>

          <div className="space-y-3">
            {actions.map((action, i) => (
              <div 
                key={i}
                className="flex items-center gap-3 p-3 bg-slate-900/50 rounded-lg hover:bg-slate-900 transition-colors cursor-pointer"
                onClick={() => onActionSelect && onActionSelect(action)}
              >
                <div className="w-8 h-8 bg-violet-500/20 rounded-full flex items-center justify-center text-violet-400 font-bold text-sm">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <p className="text-white text-sm font-medium">{action.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      action.priority === 'critical' ? 'bg-red-500/20 text-red-400' :
                      action.priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-slate-600 text-slate-400'
                    }`}>
                      {action.category}
                    </span>
                    <span className="text-xs text-slate-500">•</span>
                    <span className="text-xs text-green-400">+{action.estimated_impact} pts</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500" />
              </div>
            ))}
          </div>

          {/* Probability */}
          {probability && (
            <div className="mt-4 pt-4 border-t border-slate-700 flex items-center justify-between">
              <span className="text-sm text-slate-400">Probabilité de succès</span>
              <div className={`px-3 py-1 rounded-lg text-sm ${
                probability.level === 'high' ? 'bg-green-500/20 text-green-400' :
                probability.level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-orange-500/20 text-orange-400'
              }`}>
                {probability.percentage}%
              </div>
            </div>
          )}
        </div>
      )}

      {/* Milestones */}
      {milestones && milestones.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h4 className="font-medium text-white mb-4 flex items-center gap-2">
            <Award className="w-4 h-4 text-cyan-400" />
            Jalons de progression
          </h4>
          <div className="relative">
            {/* Progress Line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700" />
            
            <div className="space-y-4">
              {milestones.map((milestone, i) => (
                <div key={i} className="flex items-center gap-4 relative">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center z-10 ${
                    milestone.status === 'completed' 
                      ? 'bg-green-500 text-white' 
                      : 'bg-slate-700 text-slate-400'
                  }`}>
                    {milestone.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <span className="text-sm font-bold">{milestone.number}</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-white">{milestone.action}</p>
                    <p className="text-xs text-slate-500">Objectif: {milestone.target_score} pts</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GradeObjective;
