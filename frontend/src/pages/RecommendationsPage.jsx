import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Target,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  Filter
} from "lucide-react";

const RecommendationsPage = () => {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      const response = await axios.get(`${API}/analyses`, { withCredentials: true });
      const analyses = response.data.analyses || [];
      
      // Get recommendations from the latest completed analysis
      const completedAnalyses = analyses.filter(a => a.status === "completed");
      if (completedAnalyses.length > 0) {
        const latestAnalysis = await axios.get(
          `${API}/analysis/${completedAnalyses[0].analysis_id}`,
          { withCredentials: true }
        );
        setRecommendations(latestAnalysis.data.analysis?.recommendations || []);
      }
    } catch (error) {
      console.error("Recommendations error:", error);
      toast.error("Erreur lors du chargement des recommandations");
    } finally {
      setLoading(false);
    }
  };

  const filteredRecommendations = filter === "all" 
    ? recommendations 
    : recommendations.filter(r => r.priority === filter);

  const priorityConfig = {
    high: { label: "Haute", color: "bg-destructive/20 text-destructive border-destructive/30", icon: AlertTriangle },
    medium: { label: "Moyenne", color: "bg-warning/20 text-warning border-warning/30", icon: TrendingUp },
    low: { label: "Basse", color: "bg-success/20 text-success border-success/30", icon: CheckCircle2 }
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

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="recommendations-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Recommandations</h1>
            <p className="text-muted-foreground">
              Actions prioritaires pour améliorer votre score GEO
            </p>
          </div>
          
          <div className="flex gap-2">
            {["all", "high", "medium", "low"].map((f) => (
              <Button
                key={f}
                variant={filter === f ? "default" : "outline"}
                size="sm"
                onClick={() => setFilter(f)}
                data-testid={`filter-${f}`}
              >
                {f === "all" ? "Toutes" : priorityConfig[f]?.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="glass p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-destructive/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-destructive" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {recommendations.filter(r => r.priority === "high").length}
                </p>
                <p className="text-sm text-muted-foreground">Priorité haute</p>
              </div>
            </div>
          </Card>
          <Card className="glass p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-warning/20 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {recommendations.filter(r => r.priority === "medium").length}
                </p>
                <p className="text-sm text-muted-foreground">Priorité moyenne</p>
              </div>
            </div>
          </Card>
          <Card className="glass p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-success/20 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {recommendations.filter(r => r.priority === "low").length}
                </p>
                <p className="text-sm text-muted-foreground">Priorité basse</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Recommendations List */}
        {filteredRecommendations.length > 0 ? (
          <div className="space-y-4">
            {filteredRecommendations.map((rec, index) => {
              const config = priorityConfig[rec.priority] || priorityConfig.low;
              const Icon = config.icon;
              
              return (
                <Card key={index} className="glass p-6">
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      rec.priority === "high" ? "bg-destructive/20" :
                      rec.priority === "medium" ? "bg-warning/20" :
                      "bg-success/20"
                    }`}>
                      <Icon className={`w-5 h-5 ${
                        rec.priority === "high" ? "text-destructive" :
                        rec.priority === "medium" ? "text-warning" :
                        "text-success"
                      }`} />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <h3 className="text-lg font-semibold text-white">{rec.title}</h3>
                        <Badge variant="outline" className={config.color}>
                          Priorité {config.label.toLowerCase()}
                        </Badge>
                      </div>
                      
                      <p className="text-muted-foreground mb-4">{rec.description}</p>
                      
                      <div className="flex flex-wrap gap-4 text-sm">
                        <span className="flex items-center gap-1">
                          <span className="text-muted-foreground">Impact:</span>
                          <span className={`font-medium ${
                            rec.impact === "élevé" ? "text-success" :
                            rec.impact === "moyen" ? "text-warning" :
                            "text-muted-foreground"
                          }`}>
                            {rec.impact}
                          </span>
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="text-muted-foreground">Effort:</span>
                          <span className="text-white">{rec.effort}</span>
                        </span>
                        {rec.category && (
                          <span className="flex items-center gap-1">
                            <span className="text-muted-foreground">Catégorie:</span>
                            <span className="text-white capitalize">{rec.category}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="glass p-12 text-center">
            <Target className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              {recommendations.length === 0 
                ? "Aucune recommandation" 
                : "Aucun résultat pour ce filtre"}
            </h3>
            <p className="text-muted-foreground">
              {recommendations.length === 0 
                ? "Lancez une analyse pour obtenir des recommandations personnalisées"
                : "Essayez de modifier les filtres"}
            </p>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default RecommendationsPage;
