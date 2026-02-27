import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Bot,
  Play,
  Loader2,
  XCircle,
  ArrowLeft,
  Download,
  Shield,
  TrendingUp,
  Target,
  Zap,
  Award,
  BarChart3,
  Activity,
  CheckCircle2,
  AlertTriangle,
  FileDown,
  Eye,
  AlertCircle,
  Globe
} from "lucide-react";
import { generatePDFReport } from "@/services/pdfReportGenerator";
import ReportPreviewModal from "@/components/ReportPreviewModal";
import { useFingerprint } from "@/hooks/useFingerprint";
import { ScanDiffCard, SiteEnrichmentCard, BrandAnalysisCard } from "@/components/AdvancedScanCards";
import CompetitorAnalysisCard from "@/components/CompetitorAnalysisCard";

const AnalysisPage = () => {
  const { analysisId } = useParams();
  const { user, currentProject } = useAuth();
  const navigate = useNavigate();
  const { fingerprint } = useFingerprint();
  
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);
  const [eligibilityError, setEligibilityError] = useState(null);

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

  const fetchAnalysis = async (id, retryCount = 0) => {
    console.log("fetchAnalysis called with id:", id, "retry:", retryCount);
    try {
      setError(null);
      const response = await axios.get(`${API}/analysis/${id}`, { 
        withCredentials: true,
        timeout: 30000 // 30 second timeout
      });
      console.log("fetchAnalysis response:", response.data);
      setAnalysis(response.data.analysis);
      
      if (response.data.analysis?.status === "running") {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch (error) {
      console.error("Analysis error:", error);
      console.error("Error details:", error.message, error.code, error.response?.status);
      
      // Retry up to 2 times on timeout
      if (error.code === 'ECONNABORTED' && retryCount < 2) {
        console.log("Retrying fetch...", retryCount + 1);
        toast.info("Connexion lente, nouvelle tentative...");
        setTimeout(() => fetchAnalysis(id, retryCount + 1), 1000);
        return;
      }
      
      const errorMessage = error.code === 'ECONNABORTED' 
        ? "La connexion est très lente. Veuillez rafraîchir la page ou réessayer plus tard."
        : error.response?.data?.detail || `Erreur lors du chargement de l'analyse (${error.message})`;
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      if (retryCount === 0 || retryCount >= 2) {
        setLoading(false);
      }
    }
  };

  const startAnalysis = async () => {
    if (!currentProject) {
      toast.error("Aucun projet sélectionné");
      return;
    }

    setStarting(true);
    setEligibilityError(null);
    
    try {
      const response = await axios.post(
        `${API}/analysis/start`,
        { 
          project_id: currentProject.project_id,
          fingerprint: fingerprint || "unknown"
        },
        { withCredentials: true }
      );
      
      toast.success("Analyse IAskan Verified™ lancée !");
      navigate(`/analysis/${response.data.analysis_id}`);
    } catch (error) {
      console.error("Start analysis error:", error);
      
      if (error.response?.status === 401) {
        toast.error("Session expirée. Veuillez vous reconnecter.");
        return;
      }
      
      // Handle anti-abuse blocking
      const detail = error.response?.data?.detail;
      if (detail?.error === "free_trial_blocked") {
        setEligibilityError({
          reason: detail.reason,
          blocked_by: detail.blocked_by
        });
        toast.error(detail.reason);
        return;
      }
      
      // Handle email not verified
      if (detail?.error === "email_not_verified") {
        setEligibilityError({
          reason: detail.reason,
          blocked_by: "email_not_verified",
          requires_verification: true
        });
        toast.error(detail.reason);
        return;
      }
      
      toast.error(detail?.message || detail || "Erreur lors du lancement de l'analyse");
    } finally {
      setStarting(false);
    }
  };

  const downloadPDF = async () => {
    if (!analysis?.analysis_id || !currentProject) {
      toast.error("Données insuffisantes pour générer le rapport");
      return;
    }
    
    setDownloading(true);
    try {
      // Use client-side PDF generation with full 10-section report
      await generatePDFReport(analysis, currentProject);
      toast.success("Rapport PDF téléchargé avec succès !");
    } catch (error) {
      console.error("PDF download error:", error);
      toast.error("Erreur lors de la génération du rapport PDF");
    } finally {
      setDownloading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  const getGradeColor = (grade) => {
    const colors = {
      "A": "bg-emerald-100 text-emerald-700 border-emerald-200",
      "B": "bg-cyan-100 text-cyan-700 border-cyan-200",
      "C": "bg-amber-100 text-amber-700 border-amber-200",
      "D": "bg-orange-100 text-orange-700 border-orange-200",
      "F": "bg-red-100 text-red-700 border-red-200"
    };
    return colors[grade] || "bg-slate-100 text-slate-700 border-slate-200";
  };

  const getStabilityStatus = (score) => {
    if (score >= 80) return { label: "Élevée", color: "text-emerald-600", icon: CheckCircle2 };
    if (score >= 60) return { label: "Moyenne", color: "text-amber-600", icon: Activity };
    return { label: "Faible", color: "text-red-600", icon: AlertTriangle };
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]" data-testid="analysis-loading">
          <Card className="p-8 max-w-lg w-full bg-white border-slate-100">
            <div className="text-center space-y-6">
              {/* Animated Logo/Icon */}
              <div className="relative mx-auto w-20 h-20">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-20"></div>
                <div className="absolute inset-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
                  <Shield className="w-8 h-8 text-white animate-pulse" />
                </div>
                {/* Spinning ring */}
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Chargement de l'analyse...
                </h3>
                <p className="text-slate-600 text-sm">
                  Veuillez patienter pendant que nous récupérons vos données
                </p>
              </div>
              
              {/* Progress bar animation */}
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Show error state if analysis failed to load
  if (error && analysisId && !analysis) {
    return (
      <DashboardLayout>
        <div className="space-y-8" data-testid="analysis-error">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/dashboard")} data-testid="back-btn">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
            <h1 className="text-2xl font-bold text-slate-900">Analyse</h1>
          </div>
          
          <Card className="p-8 max-w-2xl bg-white border-slate-100">
            <div className="text-center">
              <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">Erreur de chargement</h3>
              <p className="text-slate-600 mb-6">{error}</p>
              <div className="flex justify-center gap-4">
                <Button 
                  variant="outline"
                  onClick={() => fetchAnalysis(analysisId)}
                >
                  Réessayer
                </Button>
                <Button 
                  onClick={() => navigate("/analysis")}
                  className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
                >
                  Nouvelle analyse
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Show waiting state when we have analysisId but no analysis yet (and no error)
  if (analysisId && !analysis && !error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]" data-testid="analysis-waiting">
          <Card className="p-8 max-w-lg w-full bg-white border-slate-100">
            <div className="text-center space-y-6">
              {/* Animated Logo/Icon */}
              <div className="relative mx-auto w-20 h-20">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-20"></div>
                <div className="absolute inset-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
                  <Shield className="w-8 h-8 text-white animate-pulse" />
                </div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Chargement de l'analyse en cours...
                </h3>
                <p className="text-slate-600 text-sm">
                  La connexion peut prendre quelques instants
                </p>
                <p className="text-xs text-slate-400 mt-2">
                  ID: {analysisId}
                </p>
              </div>
              
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
              </div>
              
              <div className="flex gap-3 justify-center mt-4">
                <Button 
                  variant="outline" 
                  onClick={() => fetchAnalysis(analysisId)}
                >
                  Actualiser
                </Button>
                <Button 
                  variant="ghost" 
                  onClick={() => navigate("/dashboard")}
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Retour
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Show analysis results if we have an analysis
  if (analysis) {
    const indices = analysis.indices || {};
    const stabilityData = analysis.stability_data || {};
    const queryTypeBreakdown = analysis.query_type_breakdown || {};
    const analysisSummary = analysis.analysis_summary || {};
    const stabilityStatus = getStabilityStatus(indices.stability_index || 0);

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
                <div className="flex items-center gap-3">
                  {/* Project Logo */}
                  {currentProject?.logo_url ? (
                    <img 
                      src={currentProject.logo_url} 
                      alt={currentProject.name}
                      className="w-10 h-10 rounded-lg object-contain bg-white border border-slate-200 p-1"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center">
                      <Globe className="w-5 h-5 text-violet-600" />
                    </div>
                  )}
                  <div>
                    <h1 className="text-2xl font-bold text-slate-900">{currentProject?.name || "Résultats de l'analyse"}</h1>
                    {currentProject?.website_url && (
                      <a 
                        href={currentProject.website_url.startsWith("http") ? currentProject.website_url : `https://${currentProject.website_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-violet-600 hover:underline"
                        title={currentProject.website_url}
                      >
                        {formatUrl(currentProject.website_url)}
                      </a>
                    )}
                  </div>
                  {analysis.status === "completed" && (
                    <Badge className="bg-gradient-to-r from-violet-600 to-cyan-600 text-white border-0 text-xs ml-2">
                      <Shield className="w-3 h-3 mr-1" />
                      IAskan Verified™
                    </Badge>
                  )}
                </div>
                <p className="text-slate-500 text-sm mt-1 ml-13">
                  Analyse du {new Date(analysis.created_at).toLocaleDateString("fr-FR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit"
                  })}
                </p>
              </div>
            </div>
            
            {analysis.status === "completed" && (
              <div className="flex gap-3">
                <ReportPreviewModal 
                  analysisData={analysis} 
                  projectData={currentProject}
                >
                  <Button
                    variant="outline"
                    className="border-violet-200 text-violet-700 hover:bg-violet-50"
                    data-testid="preview-report-btn"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Prévisualiser
                  </Button>
                </ReportPreviewModal>
                <Button
                  onClick={downloadPDF}
                  disabled={downloading}
                  className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 shadow-lg shadow-violet-500/25"
                  data-testid="download-pdf-btn"
                >
                  {downloading ? (
                    <span className="flex items-center">
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Génération du rapport...
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <FileDown className="w-4 h-4 mr-2" />
                      Exporter PDF
                    </span>
                  )}
                </Button>
              </div>
            )}
          </div>

          {/* Status - Running */}
          {analysis.status === "running" && (
            <Card className="p-8 border-violet-200 bg-gradient-to-br from-violet-50 to-cyan-50">
              <div className="space-y-6">
                {/* Header with animated icon */}
                <div className="flex items-center gap-4">
                  <div className="relative w-16 h-16 flex-shrink-0">
                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-30"></div>
                    <div className="absolute inset-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                    <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">Analyse IAskan Verified™ en cours</h3>
                    <p className="text-slate-600 text-sm">Temps estimé : 1-2 minutes</p>
                  </div>
                </div>
                
                {/* Progress Steps */}
                <div className="space-y-3">
                  {[
                    { id: "query_generation", label: "Génération des requêtes multi-dimensions", icon: "🎯" },
                    { id: "ai_querying", label: `Interrogation des moteurs IA${analysis.queries_processed ? ` (${analysis.queries_processed}/${analysis.total_queries || '?'})` : ''}`, icon: "🤖" },
                    { id: "calculating_indices", label: "Calcul des indices avancés", icon: "📊" }
                  ].map((step, index) => {
                    const currentPhase = analysis.current_phase || "query_generation";
                    const phases = ["query_generation", "ai_querying", "calculating_indices"];
                    const currentIndex = phases.indexOf(currentPhase);
                    const stepIndex = phases.indexOf(step.id);
                    const isComplete = stepIndex < currentIndex;
                    const isCurrent = step.id === currentPhase;
                    
                    return (
                      <div 
                        key={step.id}
                        className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                          isCurrent 
                            ? 'bg-white shadow-md border border-violet-200' 
                            : isComplete 
                              ? 'bg-emerald-50 border border-emerald-200' 
                              : 'bg-slate-50 border border-slate-200 opacity-50'
                        }`}
                      >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                          isCurrent 
                            ? 'bg-gradient-to-r from-violet-600 to-cyan-600 text-white' 
                            : isComplete 
                              ? 'bg-emerald-500 text-white'
                              : 'bg-slate-200 text-slate-500'
                        }`}>
                          {isComplete ? '✓' : isCurrent ? <Loader2 className="w-4 h-4 animate-spin" /> : step.icon}
                        </div>
                        <span className={`flex-1 ${isCurrent ? 'font-medium text-slate-900' : isComplete ? 'text-emerald-700' : 'text-slate-500'}`}>
                          {step.label}
                        </span>
                        {isCurrent && (
                          <span className="text-xs px-2 py-1 rounded-full bg-violet-100 text-violet-700 animate-pulse">
                            En cours...
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {/* Global Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Progression globale</span>
                    <span className="text-violet-600 font-medium">
                      {analysis.current_phase === "query_generation" && "~20%"}
                      {analysis.current_phase === "ai_querying" && `~${Math.min(20 + Math.round((analysis.queries_processed || 0) / (analysis.total_queries || 1) * 60), 80)}%`}
                      {analysis.current_phase === "calculating_indices" && "~90%"}
                      {!analysis.current_phase && "En cours..."}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full transition-all duration-500 ease-out"
                      style={{ 
                        width: analysis.current_phase === "query_generation" ? "20%" 
                             : analysis.current_phase === "ai_querying" ? `${Math.min(20 + Math.round((analysis.queries_processed || 0) / (analysis.total_queries || 1) * 60), 80)}%`
                             : analysis.current_phase === "calculating_indices" ? "90%"
                             : "10%"
                      }}
                    ></div>
                  </div>
                </div>
                
                {/* Protocol badges */}
                <div className="flex flex-wrap gap-2 pt-2">
                  <span className="text-xs px-3 py-1.5 rounded-full bg-white border border-violet-200 text-violet-700">
                    <span className="mr-1">🔄</span> Multi-runs (3x)
                  </span>
                  <span className="text-xs px-3 py-1.5 rounded-full bg-white border border-cyan-200 text-cyan-700">
                    <span className="mr-1">🤖</span> Multi-IA
                  </span>
                  <span className="text-xs px-3 py-1.5 rounded-full bg-white border border-emerald-200 text-emerald-700">
                    <span className="mr-1">🛡️</span> Anti-hallucination
                  </span>
                </div>
              </div>
            </Card>
          )}

          {/* Status - Failed */}
          {analysis.status === "failed" && (
            <Card className="p-6 border-red-200 bg-red-50">
              <div className="flex items-center gap-4">
                <XCircle className="w-8 h-8 text-red-600" />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Analyse échouée</h3>
                  <p className="text-slate-700">
                    {analysis.error || "Une erreur s'est produite. Veuillez réessayer."}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Completed Results */}
          {analysis.status === "completed" && (
            <>
              {/* Global Score + Grade */}
              <Card className="p-8 bg-white border-slate-100">
                <div className="grid md:grid-cols-2 gap-8 items-center">
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <h2 className="text-xl font-semibold text-slate-900">Score GEO Global</h2>
                      {analysis.grade && (
                        <span className={`text-2xl font-bold px-3 py-1 rounded-lg border ${getGradeColor(analysis.grade)}`}>
                          {analysis.grade}
                        </span>
                      )}
                    </div>
                    <div className={`text-7xl font-bold ${getScoreColor(analysis.global_score)}`}>
                      {Math.round(analysis.global_score)}
                    </div>
                    <p className="text-slate-700 mt-2">sur 100</p>
                    
                    {/* Protocol Badge */}
                    <div className="mt-4 p-3 rounded-lg bg-gradient-to-r from-violet-50 to-cyan-50 border border-violet-100">
                      <div className="flex items-center gap-2 text-sm">
                        <Shield className="w-4 h-4 text-violet-600" />
                        <span className="font-medium text-slate-900">IAskan Verified GEO Protocol™</span>
                      </div>
                      <p className="text-xs text-slate-700 mt-1">
                        {analysisSummary.total_queries || 0} requêtes × {analysisSummary.methodology?.runs_per_query || 3} runs × {analysisSummary.ai_engines_used?.length || 1} IAs
                      </p>
                    </div>
                  </div>

                  {/* R.A.T.E Breakdown */}
                  {analysis.rate_score && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-slate-700">Score R.A.T.E™</h3>
                        <span className="text-xs text-slate-600">
                          {analysis.rate_score.weights?.relevance} R | {analysis.rate_score.weights?.authority} A | {analysis.rate_score.weights?.truthfulness} T | {analysis.rate_score.weights?.endorsement} E
                        </span>
                      </div>
                      {[
                        { key: "relevance", label: "Relevance", color: "bg-violet-500", desc: "Pertinence" },
                        { key: "authority", label: "Authority", color: "bg-cyan-500", desc: "Autorité" },
                        { key: "truthfulness", label: "Truthfulness", color: "bg-emerald-500", desc: "Véracité" },
                        { key: "endorsement", label: "Endorsement", color: "bg-amber-500", desc: "Recommandation" }
                      ].map((item) => (
                        <div key={item.key} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-700">{item.label}</span>
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

              {/* Advanced Indices - IAskan Verified™ */}
              {indices && Object.keys(indices).length > 0 && (
                <Card className="p-6 bg-white border-slate-100">
                  <div className="flex items-center gap-2 mb-6">
                    <Award className="w-5 h-5 text-violet-600" />
                    <h3 className="text-lg font-semibold text-slate-900">Indices IAskan Verified™</h3>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Stability Index */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-violet-50 to-violet-100 border border-violet-200">
                      <div className="flex items-center gap-2 mb-2">
                        <stabilityStatus.icon className={`w-4 h-4 ${stabilityStatus.color}`} />
                        <span className="text-xs font-medium text-slate-700">Stability Index™</span>
                      </div>
                      <div className={`text-3xl font-bold ${stabilityStatus.color}`}>
                        {Math.round(indices.stability_index || 0)}%
                      </div>
                      <p className="text-xs text-slate-600 mt-1">Cohérence: {stabilityStatus.label}</p>
                    </div>
                    
                    {/* Dominance Index */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-50 to-cyan-100 border border-cyan-200">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="w-4 h-4 text-cyan-600" />
                        <span className="text-xs font-medium text-slate-700">Dominance Index™</span>
                      </div>
                      <div className={`text-3xl font-bold ${indices.dominance_index >= 50 ? 'text-cyan-600' : 'text-amber-600'}`}>
                        {Math.round(indices.dominance_index || 0)}%
                      </div>
                      <p className="text-xs text-slate-600 mt-1">Position vs concurrents</p>
                    </div>
                    
                    {/* Trust Gap */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200">
                      <div className="flex items-center gap-2 mb-2">
                        <Shield className="w-4 h-4 text-emerald-600" />
                        <span className="text-xs font-medium text-slate-700">Trust Gap™</span>
                      </div>
                      <div className={`text-3xl font-bold ${indices.trust_gap >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {indices.trust_gap >= 0 ? '+' : ''}{Math.round(indices.trust_gap || 0)}
                      </div>
                      <p className="text-xs text-slate-600 mt-1">Écart de confiance</p>
                    </div>
                    
                    {/* Opportunity Score */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200">
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-amber-600" />
                        <span className="text-xs font-medium text-slate-700">Opportunity Score™</span>
                      </div>
                      <div className={`text-3xl font-bold ${indices.opportunity_score >= 50 ? 'text-amber-600' : 'text-slate-600'}`}>
                        {Math.round(indices.opportunity_score || 0)}%
                      </div>
                      <p className="text-xs text-slate-600 mt-1">Potentiel d'amélioration</p>
                    </div>
                  </div>
                </Card>
              )}

              {/* NEW: Scan Diff - Evolution depuis le dernier scan */}
              {analysis.scan_diff && (
                <ScanDiffCard scanDiff={analysis.scan_diff} />
              )}

              {/* NEW: Site Enrichment - Analyse de citabilité */}
              {analysis.site_enrichment && (
                <SiteEnrichmentCard siteEnrichment={analysis.site_enrichment} />
              )}

              {/* NEW: Brand Analysis - Détection avancée de marque */}
              {analysis.brand_analysis && (
                <BrandAnalysisCard brandAnalysis={analysis.brand_analysis} />
              )}

              {/* NEW: Competitor Analysis - Analyse concurrentielle détaillée */}
              {analysis.competitor_comparison && analysis.competitor_comparison.length > 0 && (
                <CompetitorAnalysisCard 
                  analysis={analysis} 
                  brandName={currentProject?.brand_name || analysis.analysis_summary?.brand_name}
                />
              )}

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
                          <p className="text-sm text-slate-700 capitalize">{ai}</p>
                          <p className={`text-2xl font-bold ${getScoreColor(score)}`}>
                            {Math.round(score)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Query Type Breakdown */}
              {queryTypeBreakdown && Object.keys(queryTypeBreakdown).length > 0 && (
                <Card className="p-6 bg-white border-slate-100">
                  <h3 className="text-lg font-semibold text-slate-900 mb-6">Analyse par type de requête</h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {Object.entries(queryTypeBreakdown).map(([type, data]) => {
                      const typeLabels = {
                        transactional: { label: "Transactionnel", icon: "💳", color: "bg-violet-50 border-violet-200" },
                        comparative: { label: "Comparatif", icon: "⚖️", color: "bg-cyan-50 border-cyan-200" },
                        informational: { label: "Informationnel", icon: "📚", color: "bg-emerald-50 border-emerald-200" },
                        local: { label: "Local", icon: "📍", color: "bg-amber-50 border-amber-200" },
                        exploratory: { label: "Exploratoire", icon: "🔍", color: "bg-purple-50 border-purple-200" }
                      };
                      const typeInfo = typeLabels[type] || { label: type, icon: "📊", color: "bg-slate-50 border-slate-200" };
                      
                      return (
                        <div key={type} className={`p-3 rounded-lg border ${typeInfo.color}`}>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">{typeInfo.icon}</span>
                            <span className="text-xs font-medium text-slate-700">{typeInfo.label}</span>
                          </div>
                          <div className="text-xl font-bold text-slate-900">{Math.round(data.avg_score || 0)}</div>
                          <p className="text-xs text-slate-600">{data.count} requêtes • {Math.round(data.mention_rate || 0)}% mentions</p>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Questions Analysées - Section dédiée */}
              <Card className="p-6 bg-white border-slate-100">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">Questions Analysées</h3>
                    <p className="text-sm text-slate-600">
                      {analysis.query_scores?.length || 0} requêtes simulant des utilisateurs réels
                    </p>
                  </div>
                  {analysis.query_scores && analysis.query_scores.length > 0 && (
                    <div className="text-right">
                      <p className="text-sm text-slate-600">Taux de mention global</p>
                      <p className="text-2xl font-bold text-violet-600">
                        {Math.round(analysis.query_scores.reduce((acc, q) => acc + (q.mention_rate || 0), 0) / analysis.query_scores.length)}%
                      </p>
                    </div>
                  )}
                </div>
                
                {analysis.query_scores && analysis.query_scores.length > 0 ? (
                  <>
                    {/* Liste des questions groupées par type */}
                    <div className="space-y-6">
                      {Object.entries(
                        analysis.query_scores.reduce((groups, query) => {
                          const type = query.query_type || 'général';
                          if (!groups[type]) groups[type] = [];
                          groups[type].push(query);
                          return groups;
                        }, {})
                      ).map(([type, queries]) => {
                        const typeLabels = {
                          transactional: { label: "Questions Transactionnelles", desc: "Intentions d'achat", color: "border-l-violet-500" },
                          comparative: { label: "Questions Comparatives", desc: "Recherche du meilleur", color: "border-l-cyan-500" },
                          informational: { label: "Questions Informationnelles", desc: "Recherche d'information", color: "border-l-emerald-500" },
                          local: { label: "Questions Locales", desc: "Recherche géographique", color: "border-l-amber-500" },
                          exploratory: { label: "Questions Exploratoires", desc: "Demande de recommandation", color: "border-l-purple-500" }
                        };
                        const typeInfo = typeLabels[type] || { label: type, desc: "", color: "border-l-slate-500" };
                        
                        return (
                          <div key={type} className={`border-l-4 ${typeInfo.color} pl-4`}>
                            <div className="flex items-center justify-between mb-3">
                              <div>
                                <h4 className="font-semibold text-slate-900">{typeInfo.label}</h4>
                                <p className="text-xs text-slate-500">{typeInfo.desc}</p>
                              </div>
                              <span className="text-sm text-slate-600">{queries.length} questions</span>
                            </div>
                            <div className="space-y-2">
                              {queries.map((query, qIndex) => (
                                <div 
                                  key={qIndex} 
                                  className="p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                                >
                                  <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                      <p className="text-slate-800 font-medium text-sm">
                                        "{query.query_text}"
                                      </p>
                                      <div className="flex items-center gap-3 mt-2 text-xs">
                                        <span className={`px-2 py-0.5 rounded-full ${
                                          query.mention_rate >= 50 
                                            ? "bg-emerald-100 text-emerald-700" 
                                            : query.mention_rate > 0 
                                              ? "bg-amber-100 text-amber-700"
                                              : "bg-red-100 text-red-700"
                                        }`}>
                                          {Math.round(query.mention_rate || 0)}% mentions
                                        </span>
                                        {query.stability?.consistent && (
                                          <span className="flex items-center gap-1 text-emerald-600">
                                            <CheckCircle2 className="w-3 h-3" />
                                            Stable
                                          </span>
                                        )}
                                        <span className="text-slate-500">
                                          Score: {Math.round(query.avg_score || 0)}/100
                                        </span>
                                      </div>
                                    </div>
                                    <div className="flex flex-wrap gap-1 max-w-[200px]">
                                      {query.responses?.slice(0, 3).map((resp, rIndex) => (
                                        <span
                                          key={rIndex}
                                          className={`text-xs px-1.5 py-0.5 rounded ${
                                            resp.brand_mentioned
                                              ? "bg-emerald-100 text-emerald-700"
                                              : "bg-slate-200 text-slate-500"
                                          }`}
                                          title={`${resp.ai_type}: ${resp.role}`}
                                        >
                                          {resp.ai_type?.charAt(0).toUpperCase()}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    
                    {/* Légende */}
                    <div className="mt-6 pt-4 border-t border-slate-200">
                      <p className="text-xs text-slate-500 mb-2">Légende des réponses IA :</p>
                      <div className="flex flex-wrap gap-3 text-xs">
                        <span className="flex items-center gap-1">
                          <span className="w-4 h-4 rounded bg-emerald-100"></span>
                          <span className="text-slate-600">Marque mentionnée</span>
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-4 h-4 rounded bg-slate-200"></span>
                          <span className="text-slate-600">Marque absente</span>
                        </span>
                        <span className="text-slate-500">|</span>
                        <span className="text-slate-600">C = ChatGPT/Claude</span>
                        <span className="text-slate-600">G = Gemini</span>
                        <span className="text-slate-600">P = Perplexity</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-slate-500">
                      Les questions analysées seront affichées ici après une nouvelle analyse avec le protocole IAskan Verified™.
                    </p>
                    <p className="text-sm text-slate-400 mt-2">
                      Cette analyse a été effectuée avec une version antérieure du protocole.
                    </p>
                  </div>
                )}
              </Card>

              {/* Recommendations */}
              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <Card className="p-6 bg-white border-slate-100">
                  <h3 className="text-lg font-semibold text-slate-900 mb-6">Recommandations Prioritaires</h3>
                  <div className="space-y-3">
                    {analysis.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className={`recommendation-card priority-${rec.priority}`}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            {rec.priority === "critical" && <AlertTriangle className="w-4 h-4 text-red-500" />}
                            <h4 className="text-slate-900 font-medium">{rec.title}</h4>
                          </div>
                          <p className="text-sm text-slate-700">{rec.description}</p>
                          {rec.metrics_impacted && rec.metrics_impacted.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {rec.metrics_impacted.map((metric, mIdx) => (
                                <span key={mIdx} className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                                  {metric}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="text-right space-y-1">
                          <span className={`text-xs px-2 py-1 rounded-full block ${
                            rec.impact === "critique" || rec.impact === "élevé" ? "bg-emerald-100 text-emerald-700" :
                            rec.impact === "moyen" ? "bg-amber-100 text-amber-700" :
                            "bg-slate-100 text-slate-600"
                          }`}>
                            Impact {rec.impact}
                          </span>
                          <span className="text-xs text-slate-600 block">
                            Effort {rec.effort}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* PDF Export Card - After Recommendations */}
              <Card className="p-6 bg-gradient-to-br from-violet-50 to-cyan-50 border border-violet-100">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-white rounded-lg shadow-sm">
                    <FileDown className="h-6 w-6 text-violet-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-800 mb-1">
                      Rapport d'Audit PDF Complet
                    </h3>
                    <p className="text-sm text-slate-600 mb-4">
                      Générez un rapport professionnel avec les 10 sections d'analyse : 
                      Introduction, Localisation, Requêtes, Citations IA, Contenu, 
                      Technique, Confiance, Concurrence, Requêtes IA et Plan d'Action.
                    </p>
                    
                    <div className="flex flex-wrap gap-2 mb-4">
                      {[
                        'Introduction',
                        'Localisation', 
                        'Requêtes',
                        'Citations IA',
                        'Contenu',
                        'Technique',
                        'Confiance',
                        'Concurrence',
                        'Requêtes IA',
                        'Plan d\'Action'
                      ].map((section, i) => (
                        <span 
                          key={i}
                          className="text-xs px-2 py-1 bg-white/70 rounded-full text-slate-600 border border-slate-200"
                        >
                          {section}
                        </span>
                      ))}
                    </div>

                    <div className="flex gap-3">
                      <ReportPreviewModal 
                        analysisData={analysis} 
                        projectData={currentProject}
                      >
                        <Button
                          variant="outline"
                          className="border-violet-200 text-violet-700 hover:bg-violet-50"
                          data-testid="pdf-preview-card-button"
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          Prévisualiser
                        </Button>
                      </ReportPreviewModal>
                      <Button
                        onClick={downloadPDF}
                        disabled={downloading}
                        className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 text-white"
                        data-testid="pdf-export-card-button"
                      >
                        {downloading ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            Génération en cours...
                          </>
                        ) : (
                          <>
                            <FileDown className="h-4 w-4 mr-2" />
                            Télécharger PDF
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      </DashboardLayout>
    );
  }

  // Show new analysis form
  if (starting) {
    // Full-screen starting state
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]" data-testid="analysis-starting">
          <Card className="p-8 max-w-lg w-full bg-white border-slate-100">
            <div className="text-center space-y-6">
              <div className="relative mx-auto w-24 h-24">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-30"></div>
                <div className="absolute inset-3 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 flex items-center justify-center">
                  <Shield className="w-10 h-10 text-white" />
                </div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 border-r-cyan-600 animate-spin"></div>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Lancement de l'analyse IAskan Verified™
                </h3>
                <p className="text-slate-600 text-sm">
                  Initialisation du protocole multi-IA en cours...
                </p>
              </div>
              
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
              </div>
              
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                <span className="text-xs px-3 py-1.5 rounded-full bg-violet-50 border border-violet-200 text-violet-700">
                  Multi-runs (3x)
                </span>
                <span className="text-xs px-3 py-1.5 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-700">
                  Multi-IA
                </span>
                <span className="text-xs px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">
                  Anti-hallucination
                </span>
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="analysis-page">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Nouvelle Analyse</h1>
          <p className="text-slate-700">
            Lancez une analyse GEO certifiée {currentProject?.brand_name ? `pour ${currentProject.brand_name}` : ''}
          </p>
        </div>

        {!currentProject ? (
          <Card className="p-8 max-w-2xl bg-white border-slate-100">
            <div className="text-center">
              <Shield className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">Aucun projet sélectionné</h3>
              <p className="text-slate-600 mb-6">
                Veuillez d'abord sélectionner un projet pour lancer une analyse.
              </p>
              <Button 
                onClick={() => navigate("/projects")}
                className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
              >
                Voir mes projets
              </Button>
            </div>
          </Card>
        ) : (
          <Card className="p-8 max-w-2xl bg-white border-slate-100">
            <div className="space-y-6">
              {/* Protocol Badge */}
              <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-violet-50 to-cyan-50 border border-violet-200">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-600 to-cyan-600 flex items-center justify-center">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">IAskan Verified GEO Protocol™</h3>
                  <p className="text-sm text-slate-700">Méthodologie certifiée multi-IA, multi-requêtes, multi-analyses</p>
                </div>
              </div>

              {/* Project Info */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <h4 className="font-semibold text-slate-900 mb-2">{currentProject.name}</h4>
                <p className="text-violet-600">{currentProject.brand_name}</p>
                {currentProject.keywords?.length > 0 && (
                  <p className="text-sm text-slate-700 mt-2">
                    Mots-clés: {currentProject.keywords.join(", ")}
                  </p>
                )}
                {currentProject.competitors?.length > 0 && (
                  <p className="text-sm text-slate-700 mt-1">
                    Concurrents: {currentProject.competitors.join(", ")}
                  </p>
                )}
              </div>

              {/* Protocol Features */}
              <div className="p-4 rounded-lg bg-cyan-50 border border-cyan-100">
                <h4 className="text-cyan-700 font-medium mb-3">Ce que le protocole IAskan va faire :</h4>
                <ul className="text-sm text-slate-700 space-y-2">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
                    <span><strong>Prompts stratégiques</strong> - Requêtes transactionnelles, comparatives, informationnelles, locales</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
                    <span><strong>3 runs par prompt</strong> - Mesure de la stabilité des réponses IA</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
                    <span><strong>Formule</strong> - Prompts × 3 runs × Moteurs IA = Requêtes totales</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
                    <span><strong>4 couches d'analyse</strong> - Présence, Rôle, Crédibilité, Conversion</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
                    <span><strong>Indices avancés</strong> - Stability Index™, Dominance Index™, Trust Gap™</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
                    <span><strong>Anti-hallucination</strong> - Vérification de la cohérence des réponses IA</span>
                  </li>
                </ul>
              </div>

              {/* Eligibility Error Message */}
              {eligibilityError && (
                <div className={`p-4 rounded-lg ${eligibilityError.requires_verification ? 'bg-amber-50 border border-amber-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="flex items-start gap-3">
                    <AlertCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${eligibilityError.requires_verification ? 'text-amber-600' : 'text-red-600'}`} />
                    <div>
                      <h4 className={`font-medium ${eligibilityError.requires_verification ? 'text-amber-800' : 'text-red-800'}`}>
                        {eligibilityError.requires_verification ? 'Vérification email requise' : 'Essai gratuit non disponible'}
                      </h4>
                      <p className={`text-sm mt-1 ${eligibilityError.requires_verification ? 'text-amber-600' : 'text-red-600'}`}>
                        {eligibilityError.reason}
                      </p>
                      {eligibilityError.requires_verification ? (
                        <p className="text-xs text-amber-500 mt-2">
                          Vérifiez votre boîte de réception (et les spams) pour le lien de vérification.
                        </p>
                      ) : (
                        <p className="text-xs text-red-500 mt-2">
                          Pour continuer, veuillez souscrire à un abonnement.
                        </p>
                      )}
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className={`mt-3 ${eligibilityError.requires_verification ? 'border-amber-200 text-amber-700 hover:bg-amber-50' : 'border-red-200 text-red-700 hover:bg-red-50'}`}
                        onClick={() => navigate(eligibilityError.requires_verification ? '/dashboard' : '/pricing')}
                      >
                        {eligibilityError.requires_verification ? 'Renvoyer l\'email' : 'Voir les abonnements'}
                      </Button>
                    </div>
                  </div>
                </div>
              )}

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
                    Initialisation du protocole...
                  </span>
                ) : (
                  <span className="flex items-center">
                    <Play className="w-5 h-5 mr-2" />
                    Lancer l'analyse IAskan Verified™
                  </span>
                )}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AnalysisPage;
