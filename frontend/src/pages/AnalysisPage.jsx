import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Brain,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  BarChart3,
  ArrowLeft,
  RefreshCw
} from "lucide-react";

const AnalysisPage = () => {
  const { analysisId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    if (analysisId) {
      fetchAnalysis(analysisId);
    } else {
      fetchProjects();
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

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`, { withCredentials: true });
      setProjects(response.data.projects || []);
      if (response.data.projects?.length > 0) {
        setSelectedProject(response.data.projects[0].project_id);
      }
    } catch (error) {
      console.error("Projects error:", error);
    } finally {
      setLoading(false);
    }
  };

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
    if (!selectedProject) {
      toast.error("Veuillez sélectionner un projet");
      return;
    }

    setStarting(true);
    try {
      const response = await axios.post(
        `${API}/analysis/start`,
        { project_id: selectedProject },
        { withCredentials: true }
      );
      
      toast.success("Analyse lancée !");
      navigate(`/analysis/${response.data.analysis_id}`);
    } catch (error) {
      console.error("Start analysis error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors du lancement de l'analyse");
    } finally {
      setStarting(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-success";
    if (score >= 40) return "text-warning";
    return "text-destructive";
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
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/analysis")} data-testid="back-btn">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white">Résultats de l'analyse</h1>
              <p className="text-muted-foreground text-sm">
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

          {/* Status */}
          {analysis.status === "running" && (
            <Card className="glass p-6 border-info/30">
              <div className="flex items-center gap-4">
                <Loader2 className="w-8 h-8 text-info animate-spin" />
                <div>
                  <h3 className="text-lg font-semibold text-white">Analyse en cours...</h3>
                  <p className="text-muted-foreground">
                    Interrogation des moteurs IA. Cela peut prendre quelques minutes.
                  </p>
                </div>
              </div>
            </Card>
          )}

          {analysis.status === "failed" && (
            <Card className="glass p-6 border-destructive/30">
              <div className="flex items-center gap-4">
                <XCircle className="w-8 h-8 text-destructive" />
                <div>
                  <h3 className="text-lg font-semibold text-white">Analyse échouée</h3>
                  <p className="text-muted-foreground">
                    Une erreur s'est produite. Veuillez réessayer.
                  </p>
                </div>
              </div>
            </Card>
          )}

          {analysis.status === "completed" && (
            <>
              {/* Global Score */}
              <Card className="glass p-8">
                <div className="grid md:grid-cols-2 gap-8 items-center">
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-2">Score GEO Global</h2>
                    <div className={`text-7xl font-bold ${getScoreColor(analysis.global_score)}`}>
                      {Math.round(analysis.global_score)}
                    </div>
                    <p className="text-muted-foreground mt-2">sur 100</p>
                  </div>

                  {/* R.A.T.E Breakdown */}
                  {analysis.rate_score && (
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-muted-foreground">Score R.A.T.E™</h3>
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
                <Card className="glass p-6">
                  <h3 className="text-lg font-semibold text-white mb-6">Score par moteur IA</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(analysis.ai_scores).map(([ai, score]) => (
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

              {/* Query Results */}
              {analysis.query_scores && analysis.query_scores.length > 0 && (
                <Card className="glass p-6">
                  <h3 className="text-lg font-semibold text-white mb-6">Détail par requête</h3>
                  <div className="space-y-4">
                    {analysis.query_scores.map((query, index) => (
                      <div key={index} className="p-4 rounded-lg bg-white/5 border border-border">
                        <div className="flex items-start justify-between mb-3">
                          <p className="text-white font-medium">{query.query_text}</p>
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
                                  ? "bg-success/20 text-success"
                                  : "bg-muted text-muted-foreground"
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
                <Card className="glass p-6">
                  <h3 className="text-lg font-semibold text-white mb-6">Recommandations</h3>
                  <div className="space-y-3">
                    {analysis.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className={`recommendation-card priority-${rec.priority}`}
                      >
                        <div className="flex-1">
                          <h4 className="text-white font-medium mb-1">{rec.title}</h4>
                          <p className="text-sm text-muted-foreground">{rec.description}</p>
                        </div>
                        <div className="text-right space-y-1">
                          <span className={`text-xs px-2 py-1 rounded-full block ${
                            rec.impact === "élevé" ? "bg-success/20 text-success" :
                            rec.impact === "moyen" ? "bg-warning/20 text-warning" :
                            "bg-muted text-muted-foreground"
                          }`}>
                            Impact {rec.impact}
                          </span>
                          <span className="text-xs text-muted-foreground block">
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
          <h1 className="text-3xl font-bold text-white">Nouvelle Analyse</h1>
          <p className="text-muted-foreground">
            Lancez une analyse GEO pour mesurer votre visibilité dans les IA
          </p>
        </div>

        <Card className="glass p-8 max-w-2xl">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Sélectionnez un projet
              </label>
              {projects.length > 0 ? (
                <Select value={selectedProject} onValueChange={setSelectedProject}>
                  <SelectTrigger data-testid="project-select">
                    <SelectValue placeholder="Choisir un projet" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.project_id} value={project.project_id}>
                        {project.name} - {project.brand_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="text-center py-8 border border-dashed border-border rounded-lg">
                  <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                  <p className="text-muted-foreground mb-4">
                    Vous n'avez pas encore de projet
                  </p>
                  <Button onClick={() => navigate("/projects")} data-testid="create-project-btn">
                    Créer un projet
                  </Button>
                </div>
              )}
            </div>

            {projects.length > 0 && (
              <>
                <div className="p-4 rounded-lg bg-info/10 border border-info/20">
                  <h4 className="text-info font-medium mb-2">Ce que l'analyse va faire :</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Générer des requêtes représentatives de votre marché</li>
                    <li>• Interroger les moteurs IA (selon votre plan)</li>
                    <li>• Analyser les réponses pour détecter votre visibilité</li>
                    <li>• Calculer votre score R.A.T.E™</li>
                    <li>• Générer des recommandations prioritaires</li>
                  </ul>
                </div>

                <Button
                  size="lg"
                  className="w-full glow-primary"
                  onClick={startAnalysis}
                  disabled={starting || !selectedProject}
                  data-testid="start-analysis-btn"
                >
                  {starting ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Lancement...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5 mr-2" />
                      Lancer l'analyse
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AnalysisPage;
