import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale/fr";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  Activity,
  Calendar,
  Target,
  Loader2,
  RefreshCw
} from "lucide-react";

const HistoryChartsPage = () => {
  const { currentProject } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [analysisHistory, setAnalysisHistory] = useState(null);
  const [comparisonHistory, setComparisonHistory] = useState(null);
  const [activeTab, setActiveTab] = useState("score");

  useEffect(() => {
    if (currentProject) {
      fetchHistory();
    }
  }, [currentProject]);

  const fetchHistory = async () => {
    if (!currentProject) return;
    setLoading(true);
    try {
      const [analysisRes, comparisonRes] = await Promise.all([
        axios.get(`${API}/analyses/history/${currentProject.project_id}`, { withCredentials: true }),
        axios.get(`${API}/comparisons/history/${currentProject.project_id}`, { withCredentials: true })
      ]);
      setAnalysisHistory(analysisRes.data.history);
      setComparisonHistory(comparisonRes.data.history);
    } catch (error) {
      console.error("Fetch history error:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), "dd MMM", { locale: fr });
    } catch {
      return dateString?.substring(0, 10) || "";
    }
  };

  const formatFullDate = (dateString) => {
    try {
      return format(parseISO(dateString), "dd MMMM yyyy à HH:mm", { locale: fr });
    } catch {
      return dateString || "";
    }
  };

  const getTrendIcon = (trend) => {
    if (trend === "up") return <TrendingUp className="w-5 h-5 text-emerald-600" />;
    if (trend === "down") return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <Minus className="w-5 h-5 text-slate-600" />;
  };

  const getTrendColor = (trend) => {
    if (trend === "up") return "text-emerald-600";
    if (trend === "down") return "text-red-600";
    return "text-slate-600";
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
          <p className="text-sm font-medium text-slate-900 mb-2">{formatFullDate(label)}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: <span className="font-semibold">{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (!currentProject) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <p className="text-slate-600">Sélectionnez un projet pour continuer</p>
        </div>
      </DashboardLayout>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 text-violet-600 animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  const hasData = analysisHistory?.score_evolution?.length > 0;

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="history-charts-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Évolution & Tendances</h1>
            <p className="text-slate-600 mt-1">
              Suivez l'évolution de votre visibilité GEO dans le temps
            </p>
          </div>
          <Button onClick={fetchHistory} variant="outline" data-testid="refresh-btn">
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualiser
          </Button>
        </div>

        {!hasData ? (
          /* No Data State */
          <Card className="p-12 text-center">
            <BarChart3 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              Pas encore de données
            </h3>
            <p className="text-slate-600 mb-6">
              Lancez plusieurs analyses pour voir l'évolution de votre score GEO.
            </p>
            <Button onClick={() => navigate("/analysis")}>
              Lancer une analyse
            </Button>
          </Card>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-violet-100">
                    <Activity className="w-6 h-6 text-violet-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Analyses</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {analysisHistory.summary.total_analyses}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-xl ${
                    analysisHistory.summary.trend === "up" ? "bg-emerald-100" :
                    analysisHistory.summary.trend === "down" ? "bg-red-100" : "bg-slate-100"
                  }`}>
                    {getTrendIcon(analysisHistory.summary.trend)}
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Évolution</p>
                    <p className={`text-2xl font-bold ${getTrendColor(analysisHistory.summary.trend)}`}>
                      {analysisHistory.summary.score_change > 0 ? "+" : ""}
                      {analysisHistory.summary.score_change} pts
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
                    <p className="text-sm text-slate-600">Score actuel</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {analysisHistory.score_evolution[analysisHistory.score_evolution.length - 1]?.score || 0}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-amber-100">
                    <Calendar className="w-6 h-6 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Dernière analyse</p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatDate(analysisHistory.summary.last_analysis)}
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2 border-b border-slate-200 pb-2">
              {[
                { id: "score", label: "Score Global" },
                { id: "rate", label: "R.A.T.E.™" },
                { id: "ai", label: "Par Moteur IA" },
                { id: "competitors", label: "Concurrents" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? "bg-violet-100 text-violet-700"
                      : "text-slate-600 hover:text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Score Evolution Chart */}
            {activeTab === "score" && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-6">Évolution du Score GEO Global</h3>
                <div className="w-full h-80 min-h-[320px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={analysisHistory.score_evolution}>
                      <defs>
                        <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={formatDate}
                        stroke="#94a3b8"
                        fontSize={12}
                      />
                      <YAxis 
                        domain={[0, 100]} 
                        stroke="#94a3b8"
                        fontSize={12}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="score"
                        name="Score GEO"
                        stroke="#7c3aed"
                        strokeWidth={3}
                        fill="url(#scoreGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}

            {/* R.A.T.E. Evolution Chart */}
            {activeTab === "rate" && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-6">Évolution des Scores R.A.T.E.™</h3>
                <div className="w-full h-80 min-h-[320px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={analysisHistory.rate_evolution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={formatDate}
                        stroke="#94a3b8"
                        fontSize={12}
                      />
                      <YAxis 
                        domain={[0, 100]} 
                        stroke="#94a3b8"
                        fontSize={12}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="relevance" 
                        name="Relevance" 
                        stroke="#8b5cf6" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="authority" 
                        name="Authority" 
                        stroke="#06b6d4" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="truthfulness" 
                        name="Truthfulness" 
                        stroke="#10b981" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="endorsement" 
                        name="Endorsement" 
                        stroke="#f59e0b" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <Badge className="bg-violet-100 text-violet-700">Relevance</Badge>
                  <Badge className="bg-cyan-100 text-cyan-700">Authority</Badge>
                  <Badge className="bg-emerald-100 text-emerald-700">Truthfulness</Badge>
                  <Badge className="bg-amber-100 text-amber-700">Endorsement</Badge>
                </div>
              </Card>
            )}

            {/* AI Evolution Chart */}
            {activeTab === "ai" && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-6">Évolution par Moteur IA</h3>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analysisHistory.score_evolution.map((item, index) => ({
                      date: item.date,
                      ChatGPT: analysisHistory.ai_evolution.chatgpt[index]?.score || 0,
                      Claude: analysisHistory.ai_evolution.claude[index]?.score || 0,
                      Gemini: analysisHistory.ai_evolution.gemini[index]?.score || 0,
                      Perplexity: analysisHistory.ai_evolution.perplexity[index]?.score || 0
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={formatDate}
                        stroke="#94a3b8"
                        fontSize={12}
                      />
                      <YAxis 
                        domain={[0, 100]} 
                        stroke="#94a3b8"
                        fontSize={12}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Bar dataKey="ChatGPT" fill="#10b981" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Claude" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Gemini" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Perplexity" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}

            {/* Competitor Evolution Chart */}
            {activeTab === "competitors" && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-6">Évolution du Classement Concurrentiel</h3>
                {comparisonHistory?.ranking_evolution?.length > 0 ? (
                  <>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={comparisonHistory.ranking_evolution}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis 
                            dataKey="date" 
                            tickFormatter={formatDate}
                            stroke="#94a3b8"
                            fontSize={12}
                          />
                          <YAxis 
                            domain={[0, 100]} 
                            stroke="#94a3b8"
                            fontSize={12}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Legend />
                          <Line 
                            type="monotone" 
                            dataKey="score" 
                            name="Votre Score" 
                            stroke="#7c3aed" 
                            strokeWidth={3}
                            dot={{ r: 5, fill: "#7c3aed" }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    
                    {/* Dominance Index Evolution */}
                    <div className="mt-8">
                      <h4 className="font-medium text-slate-900 mb-4">Indice de Dominance</h4>
                      <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={comparisonHistory.dominance_evolution}>
                            <defs>
                              <linearGradient id="dominanceGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis 
                              dataKey="date" 
                              tickFormatter={formatDate}
                              stroke="#94a3b8"
                              fontSize={12}
                            />
                            <YAxis stroke="#94a3b8" fontSize={12} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                              type="monotone"
                              dataKey="dominance"
                              name="Dominance %"
                              stroke="#10b981"
                              strokeWidth={2}
                              fill="url(#dominanceGradient)"
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-slate-600">
                      Lancez des analyses comparatives pour voir l'évolution de votre positionnement.
                    </p>
                    <Button onClick={() => navigate("/competitors")} className="mt-4">
                      Comparer aux concurrents
                    </Button>
                  </div>
                )}
              </Card>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default HistoryChartsPage;
