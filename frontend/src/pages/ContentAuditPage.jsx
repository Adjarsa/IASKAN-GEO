import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  FileText,
  Search,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sparkles,
  Code,
  List,
  Quote,
  BarChart2,
  Link as LinkIcon,
  FileCode,
  Target,
  TrendingUp,
  Lightbulb,
  ChevronRight,
  Info,
  Shield
} from "lucide-react";

const ContentAuditPage = () => {
  const { currentProject } = useAuth();
  const [loading, setLoading] = useState(true);
  const [auditData, setAuditData] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);

  useEffect(() => {
    if (currentProject) {
      fetchAuditData();
    }
  }, [currentProject]);

  const fetchAuditData = async () => {
    if (!currentProject) return;
    setLoading(true);
    
    try {
      const response = await axios.get(
        `${API}/content-audit/${currentProject.project_id}`,
        { withCredentials: true }
      );
      setAuditData(response.data);
    } catch (error) {
      console.error("Content audit error:", error);
      // Show error state instead of mock data
      toast.error("Impossible de charger l'audit de contenu. Veuillez réessayer.");
      setAuditData(null);
    } finally {
      setLoading(false);
    }
  };

  // Empty state when no data
  const getEmptyAuditData = () => ({
    global_citability_score: 0,
    pages_analyzed: 0,
    structure_score: 0,
    content_gaps: 0,
    schema_coverage: 0,
    pages: [],
    gaps: [],
    structure_recommendations: []
  });

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  const getScoreBg = (score) => {
    if (score >= 70) return "bg-emerald-100 border-emerald-200";
    if (score >= 40) return "bg-amber-100 border-amber-200";
    return "bg-red-100 border-red-200";
  };

  const getPriorityColor = (priority) => {
    if (priority === "high") return "bg-red-100 text-red-700 border-red-200";
    if (priority === "medium") return "bg-amber-100 text-amber-700 border-amber-200";
    return "bg-slate-100 text-slate-700 border-slate-200";
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <div className="spinner w-12 h-12 mx-auto" />
            <p className="text-slate-600">Analyse du contenu en cours...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const data = auditData || getEmptyAuditData();

  // Show empty state if no data
  if (!auditData || (data.pages.length === 0 && !loading)) {
    return (
      <DashboardLayout>
        <div className="space-y-8" data-testid="content-audit-page">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <FileText className="w-8 h-8 text-violet-600" />
                <h1 className="text-3xl font-bold text-slate-900">Audit de Contenu</h1>
              </div>
              <p className="text-slate-600 mt-1">
                Analysez la citabilite de vos pages par les moteurs IA generatifs
              </p>
            </div>
          </div>
          <Card className="p-12 text-center bg-slate-50 border-slate-200">
            <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Aucun audit disponible</h3>
            <p className="text-slate-600 mb-6 max-w-md mx-auto">
              Lancez un audit de contenu pour analyser la citabilite de vos pages web par les moteurs IA.
            </p>
            <Button 
              onClick={fetchAuditData}
              className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Lancer l'audit
            </Button>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="content-audit-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <FileText className="w-8 h-8 text-violet-600" />
              <h1 className="text-3xl font-bold text-slate-900">Audit de Contenu</h1>
            </div>
            <p className="text-slate-600 mt-1">
              Analysez la citabilite de vos pages par les moteurs IA generatifs
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={fetchAuditData} data-testid="refresh-audit">
              <RefreshCw className="w-4 h-4 mr-2" />
              Re-analyser
            </Button>
            <Button className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700">
              <Sparkles className="w-4 h-4 mr-2" />
              Audit complet
            </Button>
          </div>
        </div>

        {/* Global Scores */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-5 bg-gradient-to-br from-violet-50 to-violet-100 border-violet-200">
            <div className="flex items-center gap-2 mb-2">
              <Quote className="w-4 h-4 text-violet-600" />
              <span className="text-sm font-medium text-slate-700">Score Citabilite</span>
            </div>
            <p className={`text-4xl font-bold ${getScoreColor(data.global_citability_score)}`}>
              {data.global_citability_score}%
            </p>
            <p className="text-xs text-slate-600 mt-1">Probabilite d'etre cite</p>
          </Card>
          
          <Card className="p-5 bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
            <div className="flex items-center gap-2 mb-2">
              <List className="w-4 h-4 text-cyan-600" />
              <span className="text-sm font-medium text-slate-700">Structure</span>
            </div>
            <p className={`text-4xl font-bold ${getScoreColor(data.structure_score)}`}>
              {data.structure_score}%
            </p>
            <p className="text-xs text-slate-600 mt-1">Formats LLM-friendly</p>
          </Card>
          
          <Card className="p-5 bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
            <div className="flex items-center gap-2 mb-2">
              <Code className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-medium text-slate-700">Schema.org</span>
            </div>
            <p className={`text-4xl font-bold ${getScoreColor(data.schema_coverage)}`}>
              {data.schema_coverage}%
            </p>
            <p className="text-xs text-slate-600 mt-1">Couverture donnees structurees</p>
          </Card>
          
          <Card className="p-5 bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span className="text-sm font-medium text-slate-700">Lacunes</span>
            </div>
            <p className="text-4xl font-bold text-amber-600">
              {data.content_gaps}
            </p>
            <p className="text-xs text-slate-600 mt-1">Sujets non couverts</p>
          </Card>
        </div>

        {/* Content Gaps - Opportunities */}
        <Card className="p-6 bg-white border-slate-100">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-red-500" />
            Lacunes detectees - Opportunites manquees
          </h3>
          <p className="text-sm text-slate-600 mb-4">
            Sujets ou vous devriez etre cite mais ne l'etes pas encore
          </p>
          <div className="space-y-3">
            {data.gaps.map((gap, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200 hover:border-violet-300 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    gap.priority === "high" ? "bg-red-100" : 
                    gap.priority === "medium" ? "bg-amber-100" : "bg-slate-100"
                  }`}>
                    <Lightbulb className={`w-5 h-5 ${
                      gap.priority === "high" ? "text-red-600" :
                      gap.priority === "medium" ? "text-amber-600" : "text-slate-600"
                    }`} />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">{gap.topic}</p>
                    <Badge className={`mt-1 ${getPriorityColor(gap.priority)}`}>
                      Priorite {gap.priority === "high" ? "haute" : gap.priority === "medium" ? "moyenne" : "basse"}
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-emerald-500" />
                    <span className="text-emerald-600 font-bold">+{gap.potential_impact}%</span>
                  </div>
                  <p className="text-xs text-slate-500">Impact potentiel</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Pages Analysis */}
        <Card className="p-6 bg-white border-slate-100">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <FileCode className="w-5 h-5 text-violet-600" />
            Analyse page par page
          </h3>
          <div className="space-y-4">
            {data.pages.map((page, index) => (
              <div 
                key={index}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedPage === index 
                    ? 'border-violet-300 bg-violet-50' 
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
                onClick={() => setSelectedPage(selectedPage === index ? null : index)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${getScoreBg(page.citability_score)}`}>
                      <span className={`text-lg font-bold ${getScoreColor(page.citability_score)}`}>
                        {page.citability_score}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{page.title}</p>
                      <p className="text-sm text-slate-500">{page.url}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {page.has_schema ? (
                      <Badge className="bg-emerald-100 text-emerald-700 border-0">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Schema.org
                      </Badge>
                    ) : (
                      <Badge className="bg-red-100 text-red-700 border-0">
                        <XCircle className="w-3 h-3 mr-1" />
                        Sans schema
                      </Badge>
                    )}
                    <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${selectedPage === index ? 'rotate-90' : ''}`} />
                  </div>
                </div>
                
                {/* Expanded Details */}
                {selectedPage === index && (
                  <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-700 mb-2">Metriques</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Longueur contenu</span>
                          <span className="text-slate-900">{page.content_length} mots</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Titres (H1-H6)</span>
                          <span className="text-slate-900">{page.headings_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Listes</span>
                          <span className="text-slate-900">{page.lists_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Score structure</span>
                          <span className={`font-medium ${getScoreColor(page.structure_score)}`}>{page.structure_score}%</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      {page.issues.length > 0 && (
                        <div className="mb-3">
                          <p className="text-sm font-medium text-red-700 mb-2">Problemes detectes</p>
                          <ul className="space-y-1">
                            {page.issues.map((issue, i) => (
                              <li key={i} className="text-sm text-red-600 flex items-center gap-2">
                                <XCircle className="w-3 h-3" />
                                {issue}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {page.strengths.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-emerald-700 mb-2">Points forts</p>
                          <ul className="space-y-1">
                            {page.strengths.map((strength, i) => (
                              <li key={i} className="text-sm text-emerald-600 flex items-center gap-2">
                                <CheckCircle2 className="w-3 h-3" />
                                {strength}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Structure Recommendations */}
        <Card className="p-6 bg-white border-slate-100">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-cyan-600" />
            Recommandations de structure
          </h3>
          <p className="text-sm text-slate-600 mb-4">
            Les LLMs privilegient certains formats de contenu. Voici comment optimiser vos pages.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.structure_recommendations.map((rec, index) => (
              <div 
                key={index}
                className="p-4 rounded-lg border border-slate-200 bg-slate-50 hover:bg-white transition-colors"
              >
                <div className="flex items-center gap-3 mb-2">
                  {rec.type === "schema" && <Code className="w-5 h-5 text-violet-600" />}
                  {rec.type === "faq" && <Search className="w-5 h-5 text-cyan-600" />}
                  {rec.type === "heading" && <List className="w-5 h-5 text-emerald-600" />}
                  {rec.type === "list" && <List className="w-5 h-5 text-amber-600" />}
                  <span className="font-medium text-slate-900">{rec.title}</span>
                </div>
                <p className="text-sm text-slate-600">
                  {rec.pages} page{rec.pages > 1 ? 's' : ''} concernee{rec.pages > 1 ? 's' : ''}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* Info Box */}
        <Card className="p-4 bg-violet-50 border-violet-200">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-violet-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-violet-800">
              <p className="font-medium mb-1">Qu'est-ce que la citabilite ?</p>
              <p className="text-violet-700">
                Le score de citabilite mesure la probabilite qu'un LLM cite votre contenu dans ses reponses. 
                Il prend en compte la structure du contenu, la presence de donnees structurees, la richesse 
                semantique et la pertinence par rapport aux requetes utilisateurs.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default ContentAuditPage;
