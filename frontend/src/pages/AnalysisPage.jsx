import { useState, useEffect, useCallback, memo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Play, Loader2, XCircle, ArrowLeft, Shield, Globe,
  Sparkles, Search, Eye, FileDown, CheckCircle2, AlertCircle
} from "lucide-react";
import { generatePDFReport } from "@/services/pdfReportGenerator";
import ReportPreviewModal from "@/components/ReportPreviewModal";
import { useFingerprint } from "@/hooks/useFingerprint";
import { ScanDiffCard, SiteEnrichmentCard, BrandAnalysisCard } from "@/components/AdvancedScanCards";
import CompetitorAnalysisCard from "@/components/CompetitorAnalysisCard";
import { StrategyPanel } from "@/components/StrategyPanel";
import { SemanticSearchPanel } from "@/components/SemanticSearchPanel";

// Optimized analysis components
import {
  GlobalScoreCard,
  IndicesCard,
  QueriesCard,
  QueryTypeBreakdown,
  AIScoresCard,
  RecommendationsCard,
  RunningAnalysisCard,
  StartingAnalysisCard,
  LoadingAnalysisCard,
  getGradeColor
} from "@/components/analysis";

// Utility to format URLs
const formatUrl = (url, maxLength = 35) => {
  if (!url) return "";
  let formatted = url.replace(/^https?:\/\//, "").replace(/\/$/, "");
  return formatted.length > maxLength ? formatted.substring(0, maxLength) + "..." : formatted;
};

// Header Component - Memoized
const AnalysisHeader = memo(({ analysis, project, onBack, onDownload, downloading, onStrategy, onSemanticSearch }) => (
  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
    <div className="flex items-center gap-4">
      <Button variant="ghost" onClick={onBack} data-testid="back-btn" className="flex-shrink-0">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Retour
      </Button>
      <div className="flex items-center gap-3">
        {project?.logo_url ? (
          <img 
            src={project.logo_url} 
            alt={project.name}
            className="w-10 h-10 rounded-lg object-contain bg-white border border-slate-200 p-1"
            onError={(e) => e.target.style.display = 'none'}
          />
        ) : (
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center">
            <Globe className="w-5 h-5 text-violet-600" />
          </div>
        )}
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">{project?.name || "Analyse"}</h1>
            {analysis.status === "completed" && (
              <Badge className="bg-gradient-to-r from-violet-600 to-cyan-600 text-white border-0 text-xs">
                <Shield className="w-3 h-3 mr-1" />
                Verified™
              </Badge>
            )}
          </div>
          {project?.website_url && (
            <a 
              href={project.website_url.startsWith("http") ? project.website_url : `https://${project.website_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-violet-600 hover:underline"
            >
              {formatUrl(project.website_url)}
            </a>
          )}
        </div>
      </div>
    </div>
    
    {analysis.status === "completed" && (
      <div className="flex flex-wrap gap-2">
        <ReportPreviewModal analysisData={analysis} projectData={project}>
          <Button variant="outline" className="border-violet-200 text-violet-700 hover:bg-violet-50" data-testid="preview-btn">
            <Eye className="w-4 h-4 mr-2" />
            Prévisualiser
          </Button>
        </ReportPreviewModal>
        <Button
          onClick={onDownload}
          disabled={downloading}
          className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 shadow-lg shadow-violet-500/25"
          data-testid="download-pdf-btn"
        >
          {downloading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <FileDown className="w-4 h-4 mr-2" />}
          {downloading ? "Export..." : "PDF"}
        </Button>
        <Button onClick={onStrategy} variant="outline" className="border-violet-200 text-violet-700 hover:bg-violet-50">
          <Sparkles className="w-4 h-4 mr-2" />
          Stratégie
        </Button>
        <Button onClick={onSemanticSearch} variant="outline" className="border-cyan-200 text-cyan-700 hover:bg-cyan-50">
          <Search className="w-4 h-4 mr-2" />
          Recherche
        </Button>
      </div>
    )}
  </div>
));

AnalysisHeader.displayName = 'AnalysisHeader';

// New Analysis Form Component
const NewAnalysisForm = memo(({ project, onStart, starting, eligibilityError }) => (
  <Card className="p-6 max-w-2xl bg-white border-slate-100">
    <div className="space-y-6">
      {/* Protocol Badge */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-violet-50 to-cyan-50 border border-violet-200">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-600 to-cyan-600 flex items-center justify-center">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900">IAskan Verified GEO Protocol™</h3>
          <p className="text-sm text-slate-600">Méthodologie certifiée multi-IA</p>
        </div>
      </div>

      {/* Project Info */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
        <h4 className="font-semibold text-slate-900 mb-1">{project.name}</h4>
        <p className="text-violet-600 text-sm">{project.brand_name}</p>
        {project.keywords?.length > 0 && (
          <p className="text-xs text-slate-600 mt-2">Mots-clés: {project.keywords.join(", ")}</p>
        )}
      </div>

      {/* Protocol Features */}
      <div className="p-4 rounded-lg bg-cyan-50/50 border border-cyan-100">
        <h4 className="text-cyan-700 font-medium mb-3 text-sm">Ce que l'analyse va faire :</h4>
        <ul className="text-sm text-slate-600 space-y-2">
          {[
            "Prompts stratégiques multi-types (transactionnel, comparatif, informationnel)",
            "3 runs par prompt pour mesurer la stabilité",
            "4 couches d'analyse : Présence, Rôle, Crédibilité, Conversion",
            "Indices avancés : Stability™, Dominance™, Trust Gap™"
          ].map((item, i) => (
            <li key={i} className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Eligibility Error */}
      {eligibilityError && (
        <div className={`p-4 rounded-lg ${eligibilityError.requires_verification ? 'bg-amber-50 border border-amber-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-start gap-3">
            <AlertCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${eligibilityError.requires_verification ? 'text-amber-600' : 'text-red-600'}`} />
            <div>
              <h4 className={`font-medium text-sm ${eligibilityError.requires_verification ? 'text-amber-800' : 'text-red-800'}`}>
                {eligibilityError.requires_verification ? 'Vérification email requise' : 'Accès limité'}
              </h4>
              <p className={`text-sm mt-1 ${eligibilityError.requires_verification ? 'text-amber-600' : 'text-red-600'}`}>
                {eligibilityError.reason}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Start Button */}
      <Button
        size="lg"
        className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 shadow-lg shadow-violet-500/25"
        onClick={onStart}
        disabled={starting}
        data-testid="start-analysis-btn"
      >
        {starting ? (
          <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Initialisation...</>
        ) : (
          <><Play className="w-5 h-5 mr-2" /> Lancer l'analyse</>
        )}
      </Button>
    </div>
  </Card>
));

NewAnalysisForm.displayName = 'NewAnalysisForm';

// Main Analysis Page Component
const AnalysisPage = () => {
  const { analysisId } = useParams();
  const { user, currentProject, runningAnalysis, startTrackingAnalysis, stopTrackingAnalysis } = useAuth();
  const navigate = useNavigate();
  const { fingerprint } = useFingerprint();
  
  const [localAnalysis, setLocalAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);
  const [eligibilityError, setEligibilityError] = useState(null);
  const [showStrategy, setShowStrategy] = useState(false);
  const [showSemanticSearch, setShowSemanticSearch] = useState(false);

  // Determine which analysis to display
  const analysis = analysisId 
    ? (runningAnalysis?.analysis_id === analysisId ? runningAnalysis : localAnalysis)
    : null;

  // Fetch analysis data
  const fetchAnalysis = useCallback(async (id, retryCount = 0) => {
    try {
      setError(null);
      const response = await axios.get(`${API}/analysis/${id}`, { 
        withCredentials: true,
        timeout: 30000
      });
      const fetchedAnalysis = response.data.analysis;
      setLocalAnalysis(fetchedAnalysis);
      
      if (fetchedAnalysis?.status === "running") {
        startTrackingAnalysis(fetchedAnalysis);
      } else if (fetchedAnalysis?.status === "completed" || fetchedAnalysis?.status === "failed") {
        stopTrackingAnalysis();
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED' && retryCount < 2) {
        toast.info("Connexion lente, nouvelle tentative...");
        setTimeout(() => fetchAnalysis(id, retryCount + 1), 1000);
        return;
      }
      setError(err.response?.data?.detail || `Erreur de chargement`);
      toast.error("Erreur lors du chargement de l'analyse");
    } finally {
      if (retryCount === 0 || retryCount >= 2) setLoading(false);
    }
  }, [startTrackingAnalysis, stopTrackingAnalysis]);

  useEffect(() => {
    if (analysisId) {
      if (runningAnalysis?.analysis_id === analysisId) {
        setLocalAnalysis(runningAnalysis);
        setLoading(false);
      } else {
        const timer = setTimeout(() => fetchAnalysis(analysisId), 500);
        return () => clearTimeout(timer);
      }
    } else {
      setLoading(false);
    }
  }, [analysisId, fetchAnalysis, runningAnalysis]);

  // Sync with global running analysis
  useEffect(() => {
    if (runningAnalysis?.analysis_id === analysisId) {
      setLocalAnalysis(runningAnalysis);
      setLoading(false);
    }
  }, [runningAnalysis, analysisId]);

  // Start analysis handler
  const startAnalysis = useCallback(async () => {
    if (!currentProject) {
      toast.error("Aucun projet sélectionné");
      return;
    }

    setStarting(true);
    setEligibilityError(null);
    
    try {
      const response = await axios.post(
        `${API}/analysis/start`,
        { project_id: currentProject.project_id, fingerprint: fingerprint || "unknown" },
        { withCredentials: true }
      );
      
      const newAnalysis = {
        analysis_id: response.data.analysis_id,
        project_id: currentProject.project_id,
        status: 'running',
        current_phase: 'query_generation',
        total_queries: 0,
        queries_processed: 0,
        created_at: new Date().toISOString()
      };
      startTrackingAnalysis(newAnalysis);
      setLocalAnalysis(newAnalysis);
      setLoading(false);
      
      toast.success("Analyse lancée !");
      navigate(`/analysis/${response.data.analysis_id}`);
    } catch (err) {
      if (err.response?.status === 401) {
        toast.error("Session expirée");
        return;
      }
      
      const detail = err.response?.data?.detail;
      if (detail?.error === "free_trial_blocked" || detail?.error === "email_not_verified") {
        setEligibilityError({
          reason: detail.reason,
          blocked_by: detail.blocked_by || detail.error,
          requires_verification: detail.error === "email_not_verified"
        });
        toast.error(detail.reason);
        return;
      }
      
      toast.error(detail?.message || "Erreur lors du lancement");
    } finally {
      setStarting(false);
    }
  }, [currentProject, fingerprint, navigate, startTrackingAnalysis]);

  // Download PDF handler
  const downloadPDF = useCallback(async () => {
    if (!analysis?.analysis_id || !currentProject) {
      toast.error("Données insuffisantes");
      return;
    }
    
    setDownloading(true);
    try {
      await generatePDFReport(analysis, currentProject);
      toast.success("Rapport PDF téléchargé !");
    } catch {
      toast.error("Erreur lors de la génération du PDF");
    } finally {
      setDownloading(false);
    }
  }, [analysis, currentProject]);

  // Loading state
  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]" data-testid="analysis-loading">
          <LoadingAnalysisCard />
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error && analysisId && !analysis) {
    return (
      <DashboardLayout>
        <div className="space-y-6" data-testid="analysis-error">
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Retour
          </Button>
          <Card className="p-8 max-w-2xl mx-auto bg-white border-slate-100">
            <div className="text-center">
              <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Erreur</h3>
              <p className="text-slate-600 mb-6">{error}</p>
              <div className="flex justify-center gap-3">
                <Button variant="outline" onClick={() => fetchAnalysis(analysisId)}>Réessayer</Button>
                <Button onClick={() => navigate("/analysis")} className="bg-gradient-to-r from-violet-600 to-cyan-600">
                  Nouvelle analyse
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Starting state (full screen)
  if (starting) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]" data-testid="analysis-starting">
          <StartingAnalysisCard />
        </div>
      </DashboardLayout>
    );
  }

  // Analysis results view
  if (analysis) {
    return (
      <DashboardLayout>
        <div className="space-y-6" data-testid="analysis-results">
          {/* Header */}
          <AnalysisHeader
            analysis={analysis}
            project={currentProject}
            onBack={() => navigate("/dashboard")}
            onDownload={downloadPDF}
            downloading={downloading}
            onStrategy={() => setShowStrategy(true)}
            onSemanticSearch={() => setShowSemanticSearch(true)}
          />

          {/* Running Status */}
          {analysis.status === "running" && (
            <RunningAnalysisCard analysis={analysis} />
          )}

          {/* Failed Status */}
          {analysis.status === "failed" && (
            <Card className="p-6 border-red-200 bg-red-50">
              <div className="flex items-center gap-4">
                <XCircle className="w-8 h-8 text-red-600" />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Analyse échouée</h3>
                  <p className="text-slate-600">{analysis.error || "Une erreur s'est produite"}</p>
                </div>
              </div>
            </Card>
          )}

          {/* Completed Results */}
          {analysis.status === "completed" && (
            <>
              {/* Main Score */}
              <GlobalScoreCard analysis={analysis} />
              
              {/* Advanced Indices */}
              <IndicesCard indices={analysis.indices} />
              
              {/* Scan Diff */}
              {analysis.scan_diff && <ScanDiffCard scanDiff={analysis.scan_diff} />}
              
              {/* Site Enrichment */}
              {analysis.site_enrichment && <SiteEnrichmentCard siteEnrichment={analysis.site_enrichment} />}
              
              {/* Brand Analysis */}
              {analysis.brand_analysis && <BrandAnalysisCard brandAnalysis={analysis.brand_analysis} />}
              
              {/* Competitor Analysis */}
              {analysis.competitor_comparison?.length > 0 && (
                <CompetitorAnalysisCard 
                  analysis={analysis} 
                  brandName={currentProject?.brand_name || analysis.analysis_summary?.brand_name}
                />
              )}
              
              {/* AI Scores */}
              <AIScoresCard aiScores={analysis.ai_scores} />
              
              {/* Query Type Breakdown */}
              <QueryTypeBreakdown queryTypeBreakdown={analysis.query_type_breakdown} />
              
              {/* Detailed Queries */}
              <QueriesCard queryScores={analysis.query_scores} />
              
              {/* Recommendations */}
              <RecommendationsCard recommendations={analysis.recommendations} />
              
              {/* Export Card */}
              <Card className="p-6 bg-gradient-to-br from-violet-50 to-cyan-50 border border-violet-100">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-white rounded-lg shadow-sm">
                    <FileDown className="h-6 w-6 text-violet-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-800 mb-1">Rapport d'Audit PDF</h3>
                    <p className="text-sm text-slate-600 mb-4">
                      Rapport complet avec les 10 sections d'analyse.
                    </p>
                    <div className="flex gap-3">
                      <ReportPreviewModal analysisData={analysis} projectData={currentProject}>
                        <Button variant="outline" className="border-violet-200 text-violet-700 hover:bg-violet-50">
                          <Eye className="h-4 w-4 mr-2" /> Prévisualiser
                        </Button>
                      </ReportPreviewModal>
                      <Button
                        onClick={downloadPDF}
                        disabled={downloading}
                        className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 text-white"
                      >
                        {downloading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <FileDown className="h-4 w-4 mr-2" />}
                        Télécharger PDF
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>

        {/* Strategy Panel Modal */}
        {showStrategy && analysis && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-4 flex items-center justify-between">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-violet-400" />
                  Stratégie GEO
                </h2>
                <Button variant="ghost" onClick={() => setShowStrategy(false)} className="text-slate-400 hover:text-white">
                  ✕
                </Button>
              </div>
              <StrategyPanel analysisData={analysis} projectData={currentProject} />
            </div>
          </div>
        )}

        {/* Semantic Search Panel Modal */}
        {showSemanticSearch && analysis && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between">
                <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                  <Search className="w-5 h-5 text-cyan-600" />
                  Recherche Sémantique
                </h2>
                <Button variant="ghost" onClick={() => setShowSemanticSearch(false)}>✕</Button>
              </div>
              <SemanticSearchPanel analysisData={analysis} projectData={currentProject} />
            </div>
          </div>
        )}
      </DashboardLayout>
    );
  }

  // New analysis form
  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="analysis-page">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Nouvelle Analyse</h1>
          <p className="text-slate-600">
            Lancez une analyse GEO {currentProject?.brand_name ? `pour ${currentProject.brand_name}` : ''}
          </p>
        </div>

        {!currentProject ? (
          <Card className="p-8 max-w-2xl bg-white border-slate-100">
            <div className="text-center">
              <Shield className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Aucun projet</h3>
              <p className="text-slate-600 mb-6">Sélectionnez un projet pour lancer une analyse.</p>
              <Button onClick={() => navigate("/projects")} className="bg-gradient-to-r from-violet-600 to-cyan-600">
                Voir mes projets
              </Button>
            </div>
          </Card>
        ) : (
          <NewAnalysisForm
            project={currentProject}
            onStart={startAnalysis}
            starting={starting}
            eligibilityError={eligibilityError}
          />
        )}
      </div>
    </DashboardLayout>
  );
};

export default AnalysisPage;
