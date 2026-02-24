import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Users,
  TrendingUp,
  TrendingDown,
  Trophy,
  Target,
  Play,
  Loader2,
  Plus,
  X,
  BarChart3,
  Crown,
  Medal,
  Award
} from "lucide-react";

const CompetitorComparisonPage = () => {
  const { currentProject } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [comparisons, setComparisons] = useState([]);
  const [polling, setPolling] = useState(false);
  
  // Competitor input state
  const [competitors, setCompetitors] = useState([]);
  const [newCompetitor, setNewCompetitor] = useState("");

  useEffect(() => {
    if (currentProject) {
      // Initialize with project competitors
      setCompetitors(currentProject.competitors || []);
      fetchComparisons();
    }
  }, [currentProject]);

  useEffect(() => {
    let interval;
    if (polling && comparison?.status === "running") {
      interval = setInterval(() => {
        fetchComparison(comparison.comparison_id);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [polling, comparison?.status, comparison?.comparison_id]);

  const fetchComparisons = async () => {
    if (!currentProject) return;
    try {
      const response = await axios.get(
        `${API}/analysis/comparisons/${currentProject.project_id}`,
        { withCredentials: true }
      );
      setComparisons(response.data.comparisons || []);
      
      // Load latest comparison if exists
      if (response.data.comparisons?.length > 0) {
        const latest = response.data.comparisons[0];
        if (latest.status === "completed") {
          setComparison(latest);
        }
      }
    } catch (error) {
      console.error("Fetch comparisons error:", error);
    }
  };

  const fetchComparison = async (comparisonId) => {
    try {
      const response = await axios.get(
        `${API}/analysis/compare/${comparisonId}`,
        { withCredentials: true }
      );
      setComparison(response.data.comparison);
      if (response.data.comparison?.status === "completed") {
        setPolling(false);
        toast.success("Analyse comparative terminée !");
      }
    } catch (error) {
      console.error("Fetch comparison error:", error);
    }
  };

  const startComparison = async () => {
    if (!currentProject) return;
    if (competitors.length === 0) {
      toast.error("Ajoutez au moins un concurrent");
      return;
    }

    setStarting(true);
    try {
      const response = await axios.post(
        `${API}/analysis/compare`,
        {
          project_id: currentProject.project_id,
          competitors: competitors
        },
        { withCredentials: true }
      );
      
      setComparison({ comparison_id: response.data.comparison_id, status: "running" });
      setPolling(true);
      toast.info("Analyse comparative lancée...");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors du lancement");
    } finally {
      setStarting(false);
    }
  };

  const addCompetitor = () => {
    if (!newCompetitor.trim()) return;
    if (competitors.includes(newCompetitor.trim())) {
      toast.error("Ce concurrent existe déjà");
      return;
    }
    setCompetitors([...competitors, newCompetitor.trim()]);
    setNewCompetitor("");
  };

  const removeCompetitor = (index) => {
    setCompetitors(competitors.filter((_, i) => i !== index));
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Crown className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-5 h-5 text-slate-400" />;
    if (rank === 3) return <Award className="w-5 h-5 text-amber-600" />;
    return <span className="text-slate-400 font-bold">#{rank}</span>;
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  const getScoreBg = (score) => {
    if (score >= 70) return "bg-emerald-100";
    if (score >= 40) return "bg-amber-100";
    return "bg-red-100";
  };

  if (!currentProject) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <p className="text-slate-500">Sélectionnez un projet pour continuer</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="competitor-comparison-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Comparaison Concurrents</h1>
            <p className="text-slate-500 mt-1">
              Analysez votre positionnement face à vos concurrents dans les réponses IA
            </p>
          </div>
          <Button
            onClick={startComparison}
            disabled={starting || competitors.length === 0}
            className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
            data-testid="start-comparison-btn"
          >
            {starting ? (
              <span className="flex items-center">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyse en cours...
              </span>
            ) : (
              <span className="flex items-center">
                <Play className="w-4 h-4 mr-2" />
                Lancer la comparaison
              </span>
            )}
          </Button>
        </div>

        {/* Competitor Input */}
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-violet-600" />
            Concurrents à analyser
          </h3>
          
          <div className="flex gap-3 mb-4">
            <Input
              value={newCompetitor}
              onChange={(e) => setNewCompetitor(e.target.value)}
              placeholder="Nom du concurrent..."
              className="flex-1"
              onKeyDown={(e) => e.key === "Enter" && addCompetitor()}
              data-testid="competitor-input"
            />
            <Button onClick={addCompetitor} variant="outline" data-testid="add-competitor-btn">
              <Plus className="w-4 h-4 mr-2" />
              Ajouter
            </Button>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {competitors.map((comp, index) => (
              <Badge 
                key={index} 
                variant="secondary" 
                className="px-3 py-1.5 text-sm flex items-center gap-2"
              >
                {comp}
                <button
                  onClick={() => removeCompetitor(index)}
                  className="hover:text-red-600 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
            {competitors.length === 0 && (
              <p className="text-slate-400 text-sm">Aucun concurrent ajouté</p>
            )}
          </div>
          
          <p className="text-xs text-slate-400 mt-4">
            Votre marque: <span className="font-semibold text-violet-600">{currentProject.brand_name}</span>
          </p>
        </Card>

        {/* Loading State */}
        {comparison?.status === "running" && (
          <Card className="p-8 text-center">
            <Loader2 className="w-12 h-12 text-violet-600 animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              Analyse en cours...
            </h3>
            <p className="text-slate-500">
              Nous interrogeons les IAs pour comparer votre visibilité avec celle de vos concurrents.
              Cela peut prendre quelques minutes.
            </p>
          </Card>
        )}

        {/* Results */}
        {comparison?.status === "completed" && comparison.results && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-violet-100">
                    <Trophy className="w-6 h-6 text-violet-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Votre rang</p>
                    <p className="text-2xl font-bold text-slate-900">
                      #{comparison.results.summary?.user_rank || "-"}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-cyan-100">
                    <Target className="w-6 h-6 text-cyan-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Votre score</p>
                    <p className={`text-2xl font-bold ${getScoreColor(comparison.results.summary?.user_score || 0)}`}>
                      {comparison.results.summary?.user_score || 0}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-xl ${comparison.results.summary?.dominance_index >= 0 ? 'bg-emerald-100' : 'bg-red-100'}`}>
                    {comparison.results.summary?.dominance_index >= 0 ? (
                      <TrendingUp className="w-6 h-6 text-emerald-600" />
                    ) : (
                      <TrendingDown className="w-6 h-6 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Indice de dominance</p>
                    <p className={`text-2xl font-bold ${comparison.results.summary?.dominance_index >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {comparison.results.summary?.dominance_index >= 0 ? '+' : ''}{comparison.results.summary?.dominance_index || 0}%
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-amber-100">
                    <BarChart3 className="w-6 h-6 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Marques analysées</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {comparison.results.summary?.total_brands_analyzed || 0}
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Rankings Table */}
            <Card className="p-6">
              <h3 className="font-semibold text-slate-900 mb-6 flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-500" />
                Classement Global
              </h3>
              
              <div className="space-y-3">
                {Object.entries(comparison.results.rankings || {})
                  .sort((a, b) => a[1].rank - b[1].rank)
                  .map(([brand, data]) => (
                    <div 
                      key={brand}
                      className={`flex items-center justify-between p-4 rounded-xl transition-colors ${
                        data.is_user_brand 
                          ? 'bg-gradient-to-r from-violet-50 to-cyan-50 border-2 border-violet-200' 
                          : 'bg-slate-50 hover:bg-slate-100'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 flex items-center justify-center">
                          {getRankIcon(data.rank)}
                        </div>
                        <div>
                          <p className={`font-semibold ${data.is_user_brand ? 'text-violet-700' : 'text-slate-900'}`}>
                            {brand}
                            {data.is_user_brand && (
                              <Badge className="ml-2 bg-violet-600">Vous</Badge>
                            )}
                          </p>
                          <p className="text-sm text-slate-500">
                            Rang #{data.rank}
                          </p>
                        </div>
                      </div>
                      <div className={`px-4 py-2 rounded-lg ${getScoreBg(data.score)}`}>
                        <span className={`text-xl font-bold ${getScoreColor(data.score)}`}>
                          {data.score}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </Card>

            {/* AI Breakdown */}
            <Card className="p-6">
              <h3 className="font-semibold text-slate-900 mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-cyan-600" />
                Score par Moteur IA
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 text-slate-500 font-medium">Marque</th>
                      <th className="text-center py-3 px-4 text-slate-500 font-medium">ChatGPT</th>
                      <th className="text-center py-3 px-4 text-slate-500 font-medium">Claude</th>
                      <th className="text-center py-3 px-4 text-slate-500 font-medium">Gemini</th>
                      <th className="text-center py-3 px-4 text-slate-500 font-medium">Moyenne</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(comparison.results.rankings || {})
                      .sort((a, b) => a[1].rank - b[1].rank)
                      .map(([brand, data]) => {
                        const aiBreakdown = comparison.results.ai_breakdown || {};
                        const chatgptScore = Math.round(aiBreakdown.chatgpt?.[brand] || 0);
                        const claudeScore = Math.round(aiBreakdown.claude?.[brand] || 0);
                        const geminiScore = Math.round(aiBreakdown.gemini?.[brand] || 0);
                        
                        return (
                          <tr 
                            key={brand} 
                            className={`border-b border-slate-100 ${data.is_user_brand ? 'bg-violet-50' : ''}`}
                          >
                            <td className="py-4 px-4">
                              <span className={`font-medium ${data.is_user_brand ? 'text-violet-700' : 'text-slate-900'}`}>
                                {brand}
                                {data.is_user_brand && <span className="ml-2 text-xs text-violet-500">(vous)</span>}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={`font-semibold ${getScoreColor(chatgptScore)}`}>{chatgptScore}</span>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={`font-semibold ${getScoreColor(claudeScore)}`}>{claudeScore}</span>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={`font-semibold ${getScoreColor(geminiScore)}`}>{geminiScore}</span>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={`font-bold text-lg ${getScoreColor(data.score)}`}>{data.score}</span>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Insights */}
            <Card className="p-6 bg-gradient-to-r from-violet-50 to-cyan-50 border-violet-200">
              <h3 className="font-semibold text-slate-900 mb-4">💡 Insights</h3>
              <div className="space-y-3 text-slate-700">
                {comparison.results.summary?.user_rank === 1 ? (
                  <p>
                    🏆 <strong>Félicitations !</strong> Vous êtes en tête du classement. 
                    Continuez à maintenir votre présence pour garder cette position dominante.
                  </p>
                ) : (
                  <p>
                    📈 Vous êtes en position <strong>#{comparison.results.summary?.user_rank}</strong>. 
                    Le leader actuel est <strong>{comparison.results.summary?.top_competitor}</strong>.
                    Consultez nos recommandations pour améliorer votre visibilité.
                  </p>
                )}
                {comparison.results.summary?.dominance_index > 0 ? (
                  <p>
                    ✅ Votre indice de dominance est positif ({comparison.results.summary?.dominance_index}%), 
                    ce qui signifie que vous surpassez la moyenne de vos concurrents.
                  </p>
                ) : (
                  <p>
                    ⚠️ Votre indice de dominance est négatif ({comparison.results.summary?.dominance_index}%). 
                    Il est temps d'optimiser votre stratégie GEO pour rattraper la concurrence.
                  </p>
                )}
              </div>
            </Card>
          </>
        )}

        {/* No Results Yet */}
        {!comparison && comparisons.length === 0 && (
          <Card className="p-12 text-center">
            <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              Aucune analyse comparative
            </h3>
            <p className="text-slate-500 mb-6">
              Ajoutez vos concurrents et lancez une analyse pour voir comment vous vous positionnez.
            </p>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default CompetitorComparisonPage;
