import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Bot,
  Play,
  Loader2,
  XCircle,
  ArrowLeft,
  Download,
  FileText
} from "lucide-react";

const AnalysisPage = () => {
  const { analysisId } = useParams();
  const { user, currentProject } = useAuth();
  const navigate = useNavigate();
  
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (analysisId) {
      fetchAnalysis(analysisId);
    } else {
      setLoading(false);
    }
  }, [analysisId]);

  useEffect(() => {
    let interval;
    if (polling && analysis?.status === "running") {
      interval = setInterval(() => {
        fetchAnalysis(analysis.analysis_id);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [polling, analysis?.status, analysis?.analysis_id]);

  const fetchAnalysis = async (id) => {
    try {
      const response = await axios.get(`${API}/analysis/${id}`, { withCredentials: true });
      setAnalysis(response.data.analysis);
      
      if (response.data.analysis?.status === "running") {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error("Erreur lors du chargement de l'analyse");
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async () => {
    if (!currentProject) {
      toast.error("Aucun projet sélectionné");
      return;
    }

    setStarting(true);
    try {
      const response = await axios.post(
        `${API}/analysis/start`,
        { project_id: currentProject.project_id },
        { withCredentials: true }
      );
      
      toast.success("Analyse lancée !");
      navigate(`/analysis/${response.data.analysis_id}`);
    } catch (error) {
      console.error("Start analysis error:", error);
      // Handle auth errors specifically
      if (error.response?.status === 401) {
        toast.error("Session expirée. Veuillez vous reconnecter.");
        return;
      }
      toast.error(error.response?.data?.detail || "Erreur lors du lancement de l'analyse");
    } finally {
      setStarting(false);
    }
  };

  const downloadPDF = async () => {
    if (!analysis?.analysis_id) return;
    
    setDownloading(true);
    try {
      const response = await axios.get(
        `${API}/analysis/${analysis.analysis_id}/pdf`,
        { 
          withCredentials: true,
          responseType: 'blob'
        }
      );
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `IAskan_Rapport_${analysis.analysis_id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Rapport PDF téléchargé !");
    } catch (error) {
      console.error("PDF download error:", error);
      toast.error("Erreur lors du téléchargement du rapport");
    } finally {
      setDownloading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
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

  // Show analysis results if we have an analysis
  if (analysis) {
    return (
      <DashboardLayout>
        <div className="space-y-8" data-testid="analysis-results">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate("/dashboard")} data-testid="back-btn">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Retour
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Résultats de l'analyse</h1>
                <p className="text-slate-500 text-sm">
                  {new Date(analysis.created_at).toLocaleDateString("fr-FR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit"
                  })}
                </p>
              </div>
            </div>
            
            {/* Download PDF Button */}
            {analysis.status === "completed" && (
              <Button
                onClick={downloadPDF}
                disabled={downloading}
                className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 shadow-lg shadow-violet-500/25"
                data-testid="download-pdf-btn"
              >
                {downloading ? (
                  <span className="flex items-center">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Génération...
                  </span>
                ) : (
                  <span className="flex items-center">
                    <Download className="w-4 h-4 mr-2" />
                    Télécharger PDF
                  </span>
                )}
              </Button>
            )}
          </div>

          {/* Status */}
          {analysis.status === "running" && (
            <Card className="p-6 border-cyan-200 bg-cyan-50">
              <div className="flex items-center gap-4">
                <Loader2 className="w-8 h-8 text-cyan-600 animate-spin" />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Analyse en cours...</h3>
                  <p className="text-slate-600">
                    Interrogation des moteurs IA. Cela peut prendre quelques minutes.
                  </p>
                </div>
              </div>
            </Card>
          )}

          {analysis.status === "failed" && (
            <Card className="p-6 border-red-200 bg-red-50">
              <div className="flex items-center gap-4">
                <XCircle className="w-8 h-8 text-red-600" />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Analyse échouée</h3>
                  <p className="text-slate-600">
                    Une erreur s'est produite. Veuillez réessayer.
                  </p>
                </div>
              </div>
            </Card>
          )}

          {analysis.status === "completed" && (
            <>
              {/* Global Score */}
              <Card className="p-8 bg-white border-slate-100">
                <div className="grid md:grid-cols-2 gap-8 items-center">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900 mb-2">Score GEO Global</h2>
                    <div className={`text-7xl font-bold ${getScoreColor(analysis.global_score)}`}>
                      {Math.round(analysis.global_score)}
                    </div>
                    <p className="text-slate-500 mt-2">sur 100</p>
                  </div>

                  {/* R.A.T.E Breakdown */}
                  {analysis.rate_score && (
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-slate-500">Score R.A.T.E™</h3>
                      {[
                        { key: "relevance", label: "Relevance", color: "bg-violet-500" },
                        { key: "authority", label: "Authority", color: "bg-cyan-500" },
                        { key: "truthfulness", label: "Truthfulness", color: "bg-emerald-500" },
                        { key: "endorsement", label: "Endorsement", color: "bg-amber-500" }
                      ].map((item) => (
                        <div key={item.key} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">{item.label}</span>
                            <span className="text-slate-900 font-medium">
                              {Math.round(analysis.rate_score[item.key] || 0)}%
                            </span>
                          </div>
                          <div className="progress-bar">
                            <div
                              className={`progress-fill ${item.color}`}
                              style={{ width: `${analysis.rate_score[item.key] || 0}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>

              {/* AI Scores */}
              {analysis.ai_scores && Object.keys(analysis.ai_scores).length > 0 && (
                <Card className="p-6 bg-white border-slate-100">
                  <h3 className="text-lg font-semibold text-slate-900 mb-6">Score par moteur IA</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(analysis.ai_scores).map(([ai, score]) => (
                      <div key={ai} className="ai-card">
                        <div className={`ai-card-icon ${
                          ai === "chatgpt" ? "bg-emerald-100" :
                          ai === "claude" ? "bg-orange-100" :
                          ai === "gemini" ? "bg-blue-100" :
                          "bg-purple-100"
                        }`}>
                          <Bot className={`w-5 h-5 ${
                            ai === "chatgpt" ? "text-emerald-600" :
                            ai === "claude" ? "text-orange-600" :
                            ai === "gemini" ? "text-blue-600" :
                            "text-purple-600"
                          }`} />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-slate-500 capitalize">{ai}</p>
                          <p className={`text-2xl font-bold ${getScoreColor(score)}`}>
                            {Math.round(score)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Query Results */}
              {analysis.query_scores && analysis.query_scores.length > 0 && (
                <Card className="p-6 bg-white border-slate-100">
                  <h3 className="text-lg font-semibold text-slate-900 mb-6">Détail par requête</h3>
                  <div className="space-y-4">
                    {analysis.query_scores.map((query, index) => (
                      <div key={index} className="p-4 rounded-lg bg-slate-50 border border-slate-100">
                        <div className="flex items-start justify-between mb-3">
                          <p className="text-slate-900 font-medium">{query.query_text}</p>
                          <span className={`text-lg font-bold ${getScoreColor(query.avg_score)}`}>
                            {Math.round(query.avg_score)}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {query.responses?.map((resp, rIndex) => (
                            <span
                              key={rIndex}
                              className={`text-xs px-2 py-1 rounded-full ${
                                resp.brand_mentioned
                                  ? "bg-emerald-100 text-emerald-700"
                                  : "bg-slate-200 text-slate-600"
                              }`}
                            >
                              {resp.ai_type}: {resp.role || "absent"}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Recommendations */}
              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <Card className="p-6 bg-white border-slate-100">
                  <h3 className="text-lg font-semibold text-slate-900 mb-6">Recommandations</h3>
                  <div className="space-y-3">
                    {analysis.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className={`recommendation-card priority-${rec.priority}`}
                      >
                        <div className="flex-1">
                          <h4 className="text-slate-900 font-medium mb-1">{rec.title}</h4>
                          <p className="text-sm text-slate-500">{rec.description}</p>
                        </div>
                        <div className="text-right space-y-1">
                          <span className={`text-xs px-2 py-1 rounded-full block ${
                            rec.impact === "élevé" ? "bg-emerald-100 text-emerald-700" :
                            rec.impact === "moyen" ? "bg-amber-100 text-amber-700" :
                            "bg-slate-100 text-slate-600"
                          }`}>
                            Impact {rec.impact}
                          </span>
                          <span className="text-xs text-slate-400 block">
                            Effort {rec.effort}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    );
  }

  // Show new analysis form
  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="analysis-page">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Nouvelle Analyse</h1>
          <p className="text-slate-500">
            Lancez une analyse GEO pour {currentProject?.brand_name}
          </p>
        </div>

        <Card className="p-8 max-w-2xl bg-white border-slate-100">
          <div className="space-y-6">
            {/* Project Info */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-violet-50 to-cyan-50 border border-violet-100">
              <h4 className="font-semibold text-slate-900 mb-2">{currentProject?.name}</h4>
              <p className="text-violet-600">{currentProject?.brand_name}</p>
              {currentProject?.keywords?.length > 0 && (
                <p className="text-sm text-slate-500 mt-2">
                  Mots-clés: {currentProject.keywords.join(", ")}
                </p>
              )}
            </div>

            <div className="p-4 rounded-lg bg-cyan-50 border border-cyan-100">
              <h4 className="text-cyan-700 font-medium mb-2">Ce que l'analyse va faire :</h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• Générer des requêtes représentatives de votre marché</li>
                <li>• Interroger les moteurs IA (selon votre plan)</li>
                <li>• Analyser les réponses pour détecter votre visibilité</li>
                <li>• Calculer votre score R.A.T.E™</li>
                <li>• Générer des recommandations prioritaires</li>
              </ul>
            </div>

            <Button
              size="lg"
              className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 shadow-lg shadow-violet-500/25"
              onClick={startAnalysis}
              disabled={starting}
              data-testid="start-analysis-btn"
            >
              {starting ? (
                <span className="flex items-center">
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Lancement...
                </span>
              ) : (
                <span className="flex items-center">
                  <Play className="w-5 h-5 mr-2" />
                  Lancer l'analyse
                </span>
              )}
            </Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AnalysisPage;
