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
  Eye,
  Bot,
  TrendingUp,
  TrendingDown,
  Award,
  Target,
  BarChart3,
  RefreshCw,
  ChevronRight,
  Sparkles,
  ArrowUp,
  ArrowDown,
  Minus,
  Info,
  Shield
} from "lucide-react";

const VisibilityPage = () => {
  const { currentProject } = useAuth();
  const [loading, setLoading] = useState(true);
  const [visibilityData, setVisibilityData] = useState(null);

  useEffect(() => {
    if (currentProject) {
      fetchVisibilityData();
    }
  }, [currentProject]);

  const fetchVisibilityData = async () => {
    if (!currentProject) return;
    setLoading(true);
    
    try {
      const response = await axios.get(
        `${API}/visibility/${currentProject.project_id}`,
        { withCredentials: true }
      );
      setVisibilityData(response.data);
    } catch (error) {
      console.error("Visibility error:", error);
      // Use mock data if endpoint not yet implemented
      setVisibilityData(getMockVisibilityData());
    } finally {
      setLoading(false);
    }
  };

  const getMockVisibilityData = () => {
    return {
      global_visibility_score: 65,
      ai_engines: {
        chatgpt: { score: 72, position_avg: 2.3, mention_rate: 68, trend: "up" },
        claude: { score: 58, position_avg: 3.1, mention_rate: 52, trend: "stable" },
        gemini: { score: 61, position_avg: 2.8, mention_rate: 55, trend: "up" },
        perplexity: { score: 69, position_avg: 2.5, mention_rate: 62, trend: "down" }
      },
      position_distribution: {
        first: 25,
        second: 30,
        third: 20,
        other: 15,
        absent: 10
      },
      thematic_visibility: [
        { theme: "solution logicielle", score: 78, frequency: 12 },
        { theme: "comparatif prix", score: 45, frequency: 8 },
        { theme: "avis utilisateurs", score: 62, frequency: 15 },
        { theme: "fonctionnalites", score: 71, frequency: 10 },
        { theme: "support client", score: 38, frequency: 5 }
      ],
      recent_queries: [
        { query: "Meilleur logiciel de gestion", mentioned: true, position: 1, ai: "chatgpt" },
        { query: "Comparatif solutions B2B", mentioned: true, position: 3, ai: "claude" },
        { query: "Alternative à [concurrent]", mentioned: false, position: null, ai: "gemini" },
        { query: "Prix logiciel entreprise", mentioned: true, position: 2, ai: "perplexity" }
      ]
    };
  };

  const getTrendIcon = (trend) => {
    if (trend === "up") return <ArrowUp className="w-4 h-4 text-emerald-500" />;
    if (trend === "down") return <ArrowDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  const getPositionBadge = (position) => {
    if (position === 1) return "bg-amber-100 text-amber-700 border-amber-200";
    if (position === 2) return "bg-slate-100 text-slate-700 border-slate-200";
    if (position === 3) return "bg-orange-100 text-orange-700 border-orange-200";
    return "bg-slate-50 text-slate-500 border-slate-100";
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <div className="spinner w-12 h-12 mx-auto" />
            <p className="text-slate-600">Chargement des données de visibilite...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const data = visibilityData || getMockVisibilityData();

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="visibility-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Eye className="w-8 h-8 text-violet-600" />
              <h1 className="text-3xl font-bold text-slate-900">Visibilite Generative</h1>
            </div>
            <p className="text-slate-600 mt-1">
              Tracking de presence dans les reponses des moteurs IA generatifs
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={fetchVisibilityData} data-testid="refresh-visibility">
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualiser
            </Button>
            <Link to="/analysis">
              <Button className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700">
                <Sparkles className="w-4 h-4 mr-2" />
                Nouvelle analyse
              </Button>
            </Link>
          </div>
        </div>

        {/* Global Score */}
        <Card className="p-6 bg-gradient-to-br from-violet-50 to-cyan-50 border-violet-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="w-24 h-24 rounded-full bg-white shadow-lg flex items-center justify-center">
                <span className={`text-4xl font-bold ${getScoreColor(data.global_visibility_score)}`}>
                  {data.global_visibility_score}
                </span>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Score de Visibilite Globale</h2>
                <p className="text-slate-600">Base sur {Object.keys(data.ai_engines).length} moteurs IA</p>
                <Badge className="mt-2 bg-white border-violet-200 text-violet-700">
                  <Shield className="w-3 h-3 mr-1" />
                  IAskan Verified
                </Badge>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="text-right">
                <p className="text-sm text-slate-600">Derniere analyse</p>
                <p className="text-slate-900 font-medium">{new Date().toLocaleDateString("fr-FR")}</p>
              </div>
            </div>
          </div>
        </Card>

        {/* AI Engines Breakdown */}
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Bot className="w-5 h-5 text-slate-600" />
            Score par moteur generatif
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(data.ai_engines).map(([engine, metrics]) => (
              <Card key={engine} className="p-5 bg-white border-slate-100 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    engine === "chatgpt" ? "bg-emerald-100" :
                    engine === "claude" ? "bg-orange-100" :
                    engine === "gemini" ? "bg-blue-100" :
                    "bg-purple-100"
                  }`}>
                    <Bot className={`w-5 h-5 ${
                      engine === "chatgpt" ? "text-emerald-600" :
                      engine === "claude" ? "text-orange-600" :
                      engine === "gemini" ? "text-blue-600" :
                      "text-purple-600"
                    }`} />
                  </div>
                  {getTrendIcon(metrics.trend)}
                </div>
                <h4 className="text-sm font-medium text-slate-700 capitalize mb-2">{engine}</h4>
                <p className={`text-3xl font-bold ${getScoreColor(metrics.score)}`}>{metrics.score}</p>
                <div className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between text-slate-600">
                    <span>Position moyenne</span>
                    <span className="font-medium text-slate-900">#{metrics.position_avg.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Taux de mention</span>
                    <span className="font-medium text-slate-900">{metrics.mention_rate}%</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Position Distribution */}
        <Card className="p-6 bg-white border-slate-100">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-500" />
            Distribution des positions
          </h3>
          <div className="grid grid-cols-5 gap-4">
            {[
              { key: "first", label: "1ere position", icon: "1", color: "from-amber-400 to-amber-500" },
              { key: "second", label: "2eme position", icon: "2", color: "from-slate-400 to-slate-500" },
              { key: "third", label: "3eme position", icon: "3", color: "from-orange-400 to-orange-500" },
              { key: "other", label: "Autres positions", icon: "+", color: "from-cyan-400 to-cyan-500" },
              { key: "absent", label: "Non cite", icon: "-", color: "from-red-400 to-red-500" }
            ].map((pos) => (
              <div key={pos.key} className="text-center">
                <div className={`w-16 h-16 mx-auto mb-3 rounded-full bg-gradient-to-br ${pos.color} flex items-center justify-center text-white text-2xl font-bold shadow-lg`}>
                  {pos.icon}
                </div>
                <p className="text-2xl font-bold text-slate-900">{data.position_distribution[pos.key]}%</p>
                <p className="text-xs text-slate-600">{pos.label}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Thematic Visibility */}
        <Card className="p-6 bg-white border-slate-100">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-600" />
            Visibilite par thematique
          </h3>
          <div className="space-y-4">
            {data.thematic_visibility.map((theme, index) => (
              <div key={index} className="flex items-center gap-4">
                <div className="w-48 flex-shrink-0">
                  <p className="text-sm font-medium text-slate-900 capitalize">{theme.theme}</p>
                  <p className="text-xs text-slate-500">{theme.frequency} requetes analysees</p>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Progress value={theme.score} className="flex-1 h-3" />
                    <span className={`text-sm font-bold w-12 text-right ${getScoreColor(theme.score)}`}>
                      {theme.score}%
                    </span>
                  </div>
                </div>
                <div className="w-20 text-right">
                  {theme.score >= 70 ? (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0">Fort</Badge>
                  ) : theme.score >= 40 ? (
                    <Badge className="bg-amber-100 text-amber-700 border-0">Moyen</Badge>
                  ) : (
                    <Badge className="bg-red-100 text-red-700 border-0">Faible</Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Recent Queries */}
        <Card className="p-6 bg-white border-slate-100">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-violet-600" />
              Requetes recentes analysees
            </h3>
            <Link to="/analysis">
              <Button variant="ghost" size="sm" className="text-violet-600">
                Voir toutes les requetes
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
          <div className="space-y-3">
            {data.recent_queries.map((query, index) => (
              <div 
                key={index} 
                className={`p-4 rounded-lg border ${query.mentioned ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-slate-900 font-medium">"{query.query}"</p>
                    <div className="flex items-center gap-3 mt-2 text-sm">
                      <span className={`capitalize px-2 py-0.5 rounded ${
                        query.ai === "chatgpt" ? "bg-emerald-100 text-emerald-700" :
                        query.ai === "claude" ? "bg-orange-100 text-orange-700" :
                        query.ai === "gemini" ? "bg-blue-100 text-blue-700" :
                        "bg-purple-100 text-purple-700"
                      }`}>
                        {query.ai}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    {query.mentioned ? (
                      <div>
                        <Badge className={`${getPositionBadge(query.position)} font-bold`}>
                          #{query.position}
                        </Badge>
                        <p className="text-xs text-emerald-600 mt-1">Cite</p>
                      </div>
                    ) : (
                      <div>
                        <Badge className="bg-red-100 text-red-700 border-red-200">Absent</Badge>
                        <p className="text-xs text-red-600 mt-1">Non mentionne</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Info Box */}
        <Card className="p-4 bg-cyan-50 border-cyan-200">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-cyan-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-cyan-800">
              <p className="font-medium mb-1">Comment ameliorer votre visibilite ?</p>
              <ul className="list-disc list-inside space-y-1 text-cyan-700">
                <li>Optimisez vos contenus pour les formats privilegies par les LLMs</li>
                <li>Ajoutez des donnees structurees (schema.org) a votre site</li>
                <li>Creez du contenu repondant aux questions frequentes de votre secteur</li>
                <li>Renforcez votre autorite via des backlinks de qualite</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default VisibilityPage;
