import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  Zap,
  ArrowRight,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock
} from "lucide-react";

const DashboardPage = () => {
  const { user, subscription, refreshSubscription } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkingPayment, setCheckingPayment] = useState(false);

  useEffect(() => {
    // Check for payment success
    const paymentStatus = searchParams.get("payment");
    const sessionId = searchParams.get("session_id");

    if (paymentStatus === "success" && sessionId) {
      pollPaymentStatus(sessionId);
    }

    fetchDashboardStats();
  }, [searchParams]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    setCheckingPayment(true);
    const maxAttempts = 5;

    if (attempts >= maxAttempts) {
      toast.info("Vérification du paiement en cours. Veuillez patienter.");
      setCheckingPayment(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/checkout/status/${sessionId}`, {
        withCredentials: true
      });

      if (response.data.payment_status === "paid") {
        toast.success("Paiement confirmé ! Votre abonnement est actif.");
        await refreshSubscription();
        setCheckingPayment(false);
        // Clear URL params
        navigate("/dashboard", { replace: true });
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
    } catch (error) {
      console.error("Payment status error:", error);
      setCheckingPayment(false);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`, {
        withCredentials: true
      });
      setStats(response.data);
    } catch (error) {
      console.error("Stats error:", error);
      toast.error("Erreur lors du chargement des statistiques");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-success";
    if (score >= 40) return "text-warning";
    return "text-destructive";
  };

  const getScoreGradient = (score) => {
    if (score >= 70) return "from-success to-emerald-400";
    if (score >= 40) return "from-warning to-amber-400";
    return "from-destructive to-red-400";
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="spinner w-12 h-12" />
        </div>
      </DashboardLayout>
    );
  }

  const globalScore = stats?.global_score || 0;
  const latestAnalysis = stats?.latest_analysis;
  const queriesUsed = subscription?.queries_used || 0;
  const queriesLimit = subscription?.queries_limit || 300;
  const queriesPercent = (queriesUsed / queriesLimit) * 100;

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="dashboard-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">
              Bonjour, {user?.name?.split(" ")[0] || ""}
            </h1>
            <p className="text-muted-foreground">
              Voici un aperçu de votre visibilité GEO
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={fetchDashboardStats} data-testid="refresh-stats">
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualiser
            </Button>
            <Link to="/analysis">
              <Button className="glow-primary" data-testid="new-analysis-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle Analyse
              </Button>
            </Link>
          </div>
        </div>

        {/* Payment checking notification */}
        {checkingPayment && (
          <Card className="glass p-4 border-info/30">
            <div className="flex items-center gap-3">
              <div className="spinner w-5 h-5" />
              <span className="text-info">Vérification du paiement en cours...</span>
            </div>
          </Card>
        )}

        {/* Score Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Score */}
          <Card className="glass p-8 lg:col-span-2">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white mb-1">Score GEO Global</h2>
                <p className="text-muted-foreground text-sm">Basé sur votre dernière analyse</p>
              </div>
              {latestAnalysis && (
                <span className="text-xs text-muted-foreground">
                  {new Date(latestAnalysis.created_at).toLocaleDateString("fr-FR")}
                </span>
              )}
            </div>

            <div className="flex flex-col md:flex-row items-center gap-8">
              {/* Score Circle */}
              <div className="score-display">
                <svg className="score-circle w-full h-full" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="url(#scoreGradient)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    className="score-ring"
                    style={{ "--score": globalScore }}
                  />
                  <defs>
                    <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#4F46E5" />
                      <stop offset="100%" stopColor="#3B82F6" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="score-value">
                  <span className={`text-5xl font-bold ${getScoreColor(globalScore)}`}>
                    {Math.round(globalScore)}
                  </span>
                  <span className="text-muted-foreground">/100</span>
                </div>
              </div>

              {/* R.A.T.E Breakdown */}
              {latestAnalysis?.rate_score && (
                <div className="flex-1 space-y-4">
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Score R.A.T.E™</h3>
                  {[
                    { key: "relevance", label: "Relevance", color: "bg-primary" },
                    { key: "authority", label: "Authority", color: "bg-accent" },
                    { key: "truthfulness", label: "Truthfulness", color: "bg-success" },
                    { key: "endorsement", label: "Endorsement", color: "bg-warning" }
                  ].map((item) => (
                    <div key={item.key} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{item.label}</span>
                        <span className="text-white font-medium">
                          {Math.round(latestAnalysis.rate_score[item.key] || 0)}%
                        </span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className={`progress-fill ${item.color}`}
                          style={{ width: `${latestAnalysis.rate_score[item.key] || 0}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {!latestAnalysis && (
                <div className="flex-1 text-center">
                  <p className="text-muted-foreground mb-4">
                    Aucune analyse effectuée
                  </p>
                  <Link to="/projects">
                    <Button data-testid="create-first-project">
                      Créer votre premier projet
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </Card>

          {/* Subscription Status */}
          <Card className="glass p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-white">
                  Plan {subscription?.plan?.charAt(0).toUpperCase() + subscription?.plan?.slice(1) || "Starter"}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {subscription?.status === "trial" ? "Essai gratuit" : "Actif"}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Requêtes utilisées</span>
                  <span className="text-white">{queriesUsed} / {queriesLimit}</span>
                </div>
                <Progress value={queriesPercent} className="h-2" />
              </div>

              {subscription?.trial_ends_at && (
                <div className="flex items-center gap-2 text-sm text-warning">
                  <Clock className="w-4 h-4" />
                  <span>
                    Essai expire le{" "}
                    {new Date(subscription.trial_ends_at).toLocaleDateString("fr-FR")}
                  </span>
                </div>
              )}

              <Link to="/pricing">
                <Button variant="outline" className="w-full" data-testid="upgrade-btn">
                  Améliorer mon plan
                </Button>
              </Link>
            </div>
          </Card>
        </div>

        {/* AI Scores */}
        {latestAnalysis?.ai_scores && (
          <Card className="glass p-6">
            <h3 className="text-lg font-semibold text-white mb-6">Score par moteur IA</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(latestAnalysis.ai_scores).map(([ai, score]) => (
                <div key={ai} className="ai-card">
                  <div className={`ai-card-icon ${
                    ai === "chatgpt" ? "bg-emerald-500/20" :
                    ai === "claude" ? "bg-orange-500/20" :
                    ai === "gemini" ? "bg-blue-500/20" :
                    "bg-purple-500/20"
                  }`}>
                    <Brain className={`w-5 h-5 ${
                      ai === "chatgpt" ? "text-emerald-500" :
                      ai === "claude" ? "text-orange-500" :
                      ai === "gemini" ? "text-blue-500" :
                      "text-purple-500"
                    }`} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground capitalize">{ai}</p>
                    <p className={`text-2xl font-bold ${getScoreColor(score)}`}>
                      {Math.round(score)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Quick Actions & Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Recommendations */}
          <Card className="glass p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">Recommandations prioritaires</h3>
              <Link to="/recommendations">
                <Button variant="ghost" size="sm" data-testid="view-all-recommendations">
                  Voir tout
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>

            {latestAnalysis?.recommendations?.length > 0 ? (
              <div className="space-y-3">
                {latestAnalysis.recommendations.slice(0, 3).map((rec, index) => (
                  <div
                    key={index}
                    className={`recommendation-card priority-${rec.priority}`}
                  >
                    <div className="flex-1">
                      <h4 className="text-white font-medium mb-1">{rec.title}</h4>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {rec.description}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        rec.impact === "élevé" ? "bg-success/20 text-success" :
                        rec.impact === "moyen" ? "bg-warning/20 text-warning" :
                        "bg-muted text-muted-foreground"
                      }`}>
                        Impact {rec.impact}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Target className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">
                  Lancez une analyse pour obtenir des recommandations
                </p>
              </div>
            )}
          </Card>

          {/* Recent Analyses */}
          <Card className="glass p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">Analyses récentes</h3>
              <Link to="/analysis">
                <Button variant="ghost" size="sm" data-testid="view-all-analyses">
                  Historique
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>

            {stats?.analyses_history?.length > 0 ? (
              <div className="space-y-3">
                {stats.analyses_history.slice(0, 5).map((analysis) => (
                  <Link
                    key={analysis.analysis_id}
                    to={`/analysis/${analysis.analysis_id}`}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        analysis.global_score >= 70 ? "bg-success/20" :
                        analysis.global_score >= 40 ? "bg-warning/20" :
                        "bg-destructive/20"
                      }`}>
                        <BarChart3 className={`w-5 h-5 ${
                          analysis.global_score >= 70 ? "text-success" :
                          analysis.global_score >= 40 ? "text-warning" :
                          "text-destructive"
                        }`} />
                      </div>
                      <div>
                        <p className="text-sm text-white">
                          Score: {Math.round(analysis.global_score)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(analysis.created_at).toLocaleDateString("fr-FR")}
                        </p>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted-foreground" />
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">
                  Aucune analyse pour le moment
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardPage;
