import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Sparkles, 
  FileText, 
  Shield, 
  Code, 
  Users,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Target,
  TrendingUp,
  Loader2,
  ArrowRight,
  Lightbulb,
  Plus,
  Check,
  PlayCircle,
  Circle,
  BarChart3
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Category icons and colors
const CATEGORY_CONFIG = {
  content: { 
    icon: FileText, 
    color: 'violet',
    bgClass: 'bg-violet-500/20',
    borderClass: 'border-violet-500/30',
    textClass: 'text-violet-400'
  },
  authority: { 
    icon: Shield, 
    color: 'cyan',
    bgClass: 'bg-cyan-500/20',
    borderClass: 'border-cyan-500/30',
    textClass: 'text-cyan-400'
  },
  technical: { 
    icon: Code, 
    color: 'green',
    bgClass: 'bg-green-500/20',
    borderClass: 'border-green-500/30',
    textClass: 'text-green-400'
  },
  engagement: { 
    icon: Users, 
    color: 'orange',
    bgClass: 'bg-orange-500/20',
    borderClass: 'border-orange-500/30',
    textClass: 'text-orange-400'
  }
};

const PRIORITY_CONFIG = {
  critical: { color: 'red', label: 'Critique', icon: AlertTriangle },
  high: { color: 'orange', label: 'Élevée', icon: Zap },
  medium: { color: 'yellow', label: 'Moyenne', icon: Target },
  low: { color: 'slate', label: 'Faible', icon: Clock }
};

export function StrategyPanel({ analysisId, globalScore, rateScores, diagnostics, onClose, projectId }) {
  const [strategy, setStrategy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [expandedRecs, setExpandedRecs] = useState({});
  const [progress, setProgress] = useState(null);
  const [trackingRec, setTrackingRec] = useState(null);

  useEffect(() => {
    generateStrategy();
    if (projectId) {
      fetchProgress();
    }
  }, [analysisId, globalScore, projectId]);

  const fetchProgress = async () => {
    if (!projectId) return;
    try {
      const res = await axios.get(`${BACKEND_URL}/api/strategy/progress/${projectId}`, {
        withCredentials: true
      });
      setProgress(res.data);
    } catch (err) {
      console.error('Progress fetch error:', err);
    }
  };

  const trackRecommendation = async (rec) => {
    if (!projectId) {
      toast.error("Projet non identifié");
      return;
    }
    
    setTrackingRec(rec.title);
    try {
      await axios.post(`${BACKEND_URL}/api/strategy/progress/${projectId}/track`, {
        recommendation_id: `${rec.category}_${rec.title.toLowerCase().replace(/\s+/g, '_')}`,
        category: rec.category,
        title: rec.title,
        priority: rec.priority,
        initial_score: rec.current_score || globalScore
      }, { withCredentials: true });
      
      toast.success("Recommandation ajoutée au suivi");
      fetchProgress();
    } catch (err) {
      if (err.response?.status === 400) {
        toast.info("Déjà dans le suivi");
      } else {
        toast.error("Erreur lors de l'ajout");
      }
    } finally {
      setTrackingRec(null);
    }
  };

  const updateStatus = async (progressId, newStatus) => {
    try {
      await axios.put(`${BACKEND_URL}/api/strategy/progress/${progressId}/status`, {
        status: newStatus
      }, { withCredentials: true });
      
      toast.success(`Status mis à jour: ${newStatus}`);
      fetchProgress();
    } catch (err) {
      toast.error("Erreur lors de la mise à jour");
    }
  };

  const trackAllRecommendations = async () => {
    if (!projectId || !strategy?.recommendations) return;
    
    try {
      const res = await axios.post(`${BACKEND_URL}/api/strategy/progress/${projectId}/bulk-track`, {
        recommendations: strategy.recommendations.map(rec => ({
          recommendation_id: `${rec.category}_${rec.title.toLowerCase().replace(/\s+/g, '_')}`,
          category: rec.category,
          title: rec.title,
          priority: rec.priority,
          current_score: rec.current_score || globalScore
        }))
      }, { withCredentials: true });
      
      toast.success(`${res.data.added} recommandations ajoutées au suivi`);
      fetchProgress();
    } catch (err) {
      toast.error("Erreur lors de l'ajout en masse");
    }
  };

  const isTracked = (recTitle) => {
    if (!progress?.items) return false;
    return progress.items.some(i => i.title === recTitle);
  };

  const getTrackedStatus = (recTitle) => {
    if (!progress?.items) return null;
    const item = progress.items.find(i => i.title === recTitle);
    return item?.status;
  };

  const generateStrategy = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      if (analysisId) {
        // Generate from existing analysis
        response = await axios.post(
          `${BACKEND_URL}/api/strategy/from-analysis`,
          { analysis_id: analysisId },
          { withCredentials: true }
        );
      } else {
        // Generate from scores
        response = await axios.post(
          `${BACKEND_URL}/api/strategy/generate`,
          {
            global_score: globalScore || 50,
            relevance: rateScores?.relevance,
            authority: rateScores?.authority,
            thoroughness: rateScores?.thoroughness,
            engagement: rateScores?.engagement,
            diagnostics: diagnostics || {}
          },
          { withCredentials: true }
        );
      }
      
      setStrategy(response.data.strategy);
    } catch (err) {
      console.error('Strategy error:', err);
      setError(err.response?.data?.detail || 'Erreur lors de la génération de la stratégie');
    } finally {
      setLoading(false);
    }
  };

  const toggleRec = (index) => {
    setExpandedRecs(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const filteredRecommendations = strategy?.recommendations?.filter(rec => 
    activeCategory === 'all' || rec.category === activeCategory
  ) || [];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500 mb-4" />
        <p className="text-slate-400">Génération de la stratégie GEO...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <p className="text-red-300">{error}</p>
        <button 
          onClick={generateStrategy}
          className="mt-4 px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (!strategy) return null;

  const { summary, recommendations, action_plan, quick_wins } = strategy;

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className={`rounded-xl p-6 border ${
        summary.status === 'excellent' ? 'bg-green-500/10 border-green-500/30' :
        summary.status === 'good' ? 'bg-cyan-500/10 border-cyan-500/30' :
        summary.status === 'needs_work' ? 'bg-orange-500/10 border-orange-500/30' :
        'bg-red-500/10 border-red-500/30'
      }`}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className={`w-6 h-6 ${
                summary.status === 'excellent' ? 'text-green-400' :
                summary.status === 'good' ? 'text-cyan-400' :
                summary.status === 'needs_work' ? 'text-orange-400' :
                'text-red-400'
              }`} />
              <h2 className="text-xl font-bold text-white">
                Stratégie GEO - {summary.status_label}
              </h2>
            </div>
            <p className="text-slate-300 max-w-2xl">{summary.message}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-white">{summary.global_score}/100</p>
            <p className="text-sm text-slate-400">
              +{summary.estimated_improvement} pts potentiels
            </p>
          </div>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{summary.total_recommendations}</p>
            <p className="text-xs text-slate-400">Recommandations</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-400">{summary.priority_breakdown?.critical || 0}</p>
            <p className="text-xs text-slate-400">Critiques</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-400">{summary.priority_breakdown?.high || 0}</p>
            <p className="text-xs text-slate-400">Priorité haute</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-400">{quick_wins?.length || 0}</p>
            <p className="text-xs text-slate-400">Quick wins</p>
          </div>
        </div>
      </div>

      {/* Implementation Progress */}
      {progress && progress.stats.total > 0 && (
        <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-xl p-6 border border-green-500/20">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-green-400" />
            Progression d'Implémentation
          </h3>
          
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-400">
                {progress.stats.completed} / {progress.stats.total} recommandations
              </span>
              <span className="text-green-400 font-semibold">
                {progress.stats.completion_rate}%
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${progress.stats.completion_rate}%` }}
              />
            </div>
          </div>
          
          {/* Stats Row */}
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-green-400">{progress.stats.completed}</p>
              <p className="text-xs text-slate-400">Terminées</p>
            </div>
            <div>
              <p className="text-xl font-bold text-cyan-400">{progress.stats.in_progress}</p>
              <p className="text-xs text-slate-400">En cours</p>
            </div>
            <div>
              <p className="text-xl font-bold text-slate-400">{progress.stats.pending}</p>
              <p className="text-xs text-slate-400">En attente</p>
            </div>
            <div>
              <p className="text-xl font-bold text-violet-400">+{progress.stats.total_score_improvement}</p>
              <p className="text-xs text-slate-400">Points gagnés</p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Wins */}
      {quick_wins && quick_wins.length > 0 && (
        <div className="bg-gradient-to-r from-violet-500/10 to-cyan-500/10 rounded-xl p-6 border border-violet-500/20">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            Quick Wins - Actions Immédiates
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {quick_wins.slice(0, 4).map((win, i) => {
              const config = CATEGORY_CONFIG[win.category] || CATEGORY_CONFIG.content;
              const Icon = config.icon;
              return (
                <div key={i} className="flex items-center gap-3 bg-slate-800/50 rounded-lg p-3">
                  <Icon className={`w-5 h-5 ${config.textClass}`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{win.title}</p>
                    <p className="text-xs text-slate-400">{win.timeline}</p>
                  </div>
                  <CheckCircle className="w-4 h-4 text-green-400" />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Category Filter */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeCategory === 'all'
                ? 'bg-violet-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Toutes ({recommendations?.length || 0})
          </button>
          {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
            const count = recommendations?.filter(r => r.category === key).length || 0;
            const Icon = config.icon;
            return (
              <button
                key={key}
                onClick={() => setActiveCategory(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeCategory === key
                    ? `${config.bgClass} ${config.textClass} border ${config.borderClass}`
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {key.charAt(0).toUpperCase() + key.slice(1)} ({count})
              </button>
            );
          })}
        </div>
        
        {/* Track All Button */}
        {projectId && (
          <button
            onClick={trackAllRecommendations}
            className="px-4 py-2 bg-green-500/20 text-green-400 rounded-lg text-sm font-medium hover:bg-green-500/30 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Tout tracker
          </button>
        )}
      </div>

      {/* Recommendations List */}
      <div className="space-y-3">
        {filteredRecommendations.map((rec, index) => {
          const config = CATEGORY_CONFIG[rec.category] || CATEGORY_CONFIG.content;
          const priorityConfig = PRIORITY_CONFIG[rec.priority] || PRIORITY_CONFIG.medium;
          const Icon = config.icon;
          const PriorityIcon = priorityConfig.icon;
          const isExpanded = expandedRecs[index];
          const tracked = isTracked(rec.title);
          const trackedStatus = getTrackedStatus(rec.title);
          
          return (
            <div 
              key={index}
              className={`rounded-xl border ${config.borderClass} overflow-hidden transition-all ${tracked ? 'ring-2 ring-green-500/30' : ''}`}
            >
              <button
                onClick={() => toggleRec(index)}
                className={`w-full ${config.bgClass} p-4 flex items-center justify-between hover:bg-opacity-80 transition-colors`}
              >
                <div className="flex items-center gap-3">
                  {tracked ? (
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      trackedStatus === 'completed' ? 'bg-green-500' :
                      trackedStatus === 'in_progress' ? 'bg-cyan-500' :
                      'bg-slate-600'
                    }`}>
                      {trackedStatus === 'completed' ? <Check className="w-4 h-4 text-white" /> :
                       trackedStatus === 'in_progress' ? <PlayCircle className="w-4 h-4 text-white" /> :
                       <Circle className="w-4 h-4 text-white" />}
                    </div>
                  ) : (
                    <Icon className={`w-5 h-5 ${config.textClass}`} />
                  )}
                  <div className="text-left">
                    <p className="font-semibold text-white">{rec.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded bg-${priorityConfig.color}-500/20 text-${priorityConfig.color}-400 flex items-center gap-1`}>
                        <PriorityIcon className="w-3 h-3" />
                        {priorityConfig.label}
                      </span>
                      <span className="text-xs text-slate-400">
                        Impact: {rec.impact} • Effort: {rec.effort}
                      </span>
                    </div>
                  </div>
                </div>
                <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </button>
              
              {isExpanded && (
                <div className="p-4 bg-slate-900/50 border-t border-slate-700">
                  <p className="text-slate-300 mb-4">{rec.description}</p>
                  
                  <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-400" />
                    Actions recommandées
                  </h4>
                  <ul className="space-y-2">
                    {rec.actions?.map((action, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <ArrowRight className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                        {action}
                      </li>
                    ))}
                  </ul>
                  
                  <div className="flex items-center justify-between gap-4 mt-4 pt-4 border-t border-slate-700">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-400">Durée:</span>
                        <span className="text-white">{rec.timeline}</span>
                      </div>
                      {rec.current_score !== undefined && (
                        <div className="flex items-center gap-2 text-sm">
                          <TrendingUp className="w-4 h-4 text-slate-400" />
                          <span className="text-slate-400">Score:</span>
                          <span className="text-white">{rec.current_score}/100</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Tracking Actions */}
                    {projectId && (
                      <div className="flex items-center gap-2">
                        {!tracked ? (
                          <button
                            onClick={(e) => { e.stopPropagation(); trackRecommendation(rec); }}
                            disabled={trackingRec === rec.title}
                            className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm hover:bg-green-500/30 transition-colors flex items-center gap-2"
                          >
                            {trackingRec === rec.title ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Plus className="w-4 h-4" />
                            )}
                            Tracker
                          </button>
                        ) : (
                          <div className="flex items-center gap-2">
                            {trackedStatus !== 'completed' && (
                              <>
                                {trackedStatus !== 'in_progress' && (
                                  <button
                                    onClick={(e) => { 
                                      e.stopPropagation(); 
                                      const item = progress.items.find(i => i.title === rec.title);
                                      if (item) updateStatus(item.progress_id, 'in_progress');
                                    }}
                                    className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition-colors flex items-center gap-1"
                                  >
                                    <PlayCircle className="w-4 h-4" />
                                    Démarrer
                                  </button>
                                )}
                                <button
                                  onClick={(e) => { 
                                    e.stopPropagation(); 
                                    const item = progress.items.find(i => i.title === rec.title);
                                    if (item) updateStatus(item.progress_id, 'completed');
                                  }}
                                  className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm hover:bg-green-500/30 transition-colors flex items-center gap-1"
                                >
                                  <Check className="w-4 h-4" />
                                  Terminé
                                </button>
                              </>
                            )}
                            {trackedStatus === 'completed' && (
                              <span className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm flex items-center gap-1">
                                <CheckCircle className="w-4 h-4" />
                                Complété
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action Plan */}
      {action_plan && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-violet-400" />
            Plan d'Action
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(action_plan).map(([phase, data]) => (
              <div key={phase} className="bg-slate-900/50 rounded-lg p-4">
                <h4 className="font-medium text-white mb-2">{data.name}</h4>
                <p className="text-xs text-slate-400 mb-3">{data.description}</p>
                
                {data.actions?.length > 0 ? (
                  <ul className="space-y-2">
                    {data.actions.slice(0, 3).map((action, i) => {
                      const config = CATEGORY_CONFIG[action.category] || CATEGORY_CONFIG.content;
                      return (
                        <li key={i} className="flex items-center gap-2 text-sm">
                          <div className={`w-2 h-2 rounded-full ${config.bgClass}`} />
                          <span className="text-slate-300 truncate">{action.title}</span>
                        </li>
                      );
                    })}
                    {data.actions.length > 3 && (
                      <li className="text-xs text-slate-500">
                        +{data.actions.length - 3} autres actions
                      </li>
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Aucune action pour cette phase</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyPanel;
