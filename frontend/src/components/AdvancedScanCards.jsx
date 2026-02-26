import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Globe,
  FileCheck,
  HelpCircle,
  Shield,
  Link2,
  AlertTriangle,
  CheckCircle,
  History,
  Tag,
  Search
} from "lucide-react";

// ================== SCAN DIFF COMPONENT ==================
export const ScanDiffCard = ({ scanDiff }) => {
  if (!scanDiff || !scanDiff.has_previous) {
    return (
      <Card className="p-6 bg-slate-50 border-dashed">
        <div className="flex items-center gap-3 text-slate-500">
          <History className="w-5 h-5" />
          <div>
            <p className="font-medium">Premier scan</p>
            <p className="text-sm">Aucune donnée de comparaison disponible</p>
          </div>
        </div>
      </Card>
    );
  }

  const { score_evolution, rate_evolution, ai_evolution, trends, improvements, regressions, days_between_scans } = scanDiff;

  const getDirectionIcon = (direction) => {
    switch (direction) {
      case "up":
        return <TrendingUp className="w-4 h-4 text-emerald-500" />;
      case "down":
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-slate-400" />;
    }
  };

  const getChangeColor = (change) => {
    if (change > 0) return "text-emerald-600";
    if (change < 0) return "text-red-600";
    return "text-slate-500";
  };

  return (
    <Card className="p-6" data-testid="scan-diff-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <History className="w-5 h-5 text-violet-600" />
          Évolution depuis le dernier scan
        </h3>
        <Badge variant="outline" className="text-xs">
          Il y a {days_between_scans} jour{days_between_scans > 1 ? "s" : ""}
        </Badge>
      </div>

      {/* Score Evolution */}
      <div className="mb-6 p-4 bg-gradient-to-r from-violet-50 to-cyan-50 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-600">Score Global</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-slate-900">{score_evolution.current}</span>
              <span className="text-sm text-slate-500">/ 100</span>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1">
              {getDirectionIcon(score_evolution.direction)}
              <span className={`text-xl font-bold ${getChangeColor(score_evolution.change)}`}>
                {score_evolution.change > 0 ? "+" : ""}{score_evolution.change}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              vs {score_evolution.previous}
            </p>
          </div>
        </div>
      </div>

      {/* R.A.T.E. Evolution */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {Object.entries(rate_evolution || {}).map(([metric, data]) => (
          <div key={metric} className="p-3 bg-white rounded-lg border border-slate-100">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-500 capitalize">{metric}</span>
              {getDirectionIcon(data.direction)}
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-semibold">{data.current}</span>
              <span className={`text-xs ${getChangeColor(data.change)}`}>
                {data.change > 0 ? "+" : ""}{data.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Trends */}
      {trends && trends.length > 0 && (
        <div className="space-y-2 mb-4">
          {trends.map((trend, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-2 p-2 rounded-lg text-sm ${
                trend.type === "positive"
                  ? "bg-emerald-50 text-emerald-700"
                  : trend.type === "negative"
                  ? "bg-red-50 text-red-700"
                  : trend.type === "warning"
                  ? "bg-amber-50 text-amber-700"
                  : "bg-slate-50 text-slate-600"
              }`}
            >
              {trend.type === "positive" && <TrendingUp className="w-4 h-4" />}
              {trend.type === "negative" && <TrendingDown className="w-4 h-4" />}
              {trend.type === "warning" && <AlertTriangle className="w-4 h-4" />}
              {trend.type === "neutral" && <Minus className="w-4 h-4" />}
              <span>{trend.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Improvements & Regressions */}
      <div className="grid grid-cols-2 gap-4">
        {improvements && improvements.length > 0 && (
          <div>
            <p className="text-xs font-medium text-emerald-600 mb-2">Améliorations</p>
            <div className="space-y-1">
              {improvements.map((item, idx) => (
                <Badge key={idx} variant="outline" className="text-emerald-600 border-emerald-200 bg-emerald-50">
                  {item}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {regressions && regressions.length > 0 && (
          <div>
            <p className="text-xs font-medium text-red-600 mb-2">À surveiller</p>
            <div className="space-y-1">
              {regressions.map((item, idx) => (
                <Badge key={idx} variant="outline" className="text-red-600 border-red-200 bg-red-50">
                  {item}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

// ================== SITE ENRICHMENT COMPONENT ==================
export const SiteEnrichmentCard = ({ siteEnrichment }) => {
  if (!siteEnrichment || siteEnrichment.error) {
    return null;
  }

  const { schema_org, faq_presence, about_page, contact_info, trust_signals, key_pages, score, recommendations } = siteEnrichment;

  const getScoreColor = (score) => {
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <Card className="p-6" data-testid="site-enrichment-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Globe className="w-5 h-5 text-cyan-600" />
          Analyse du Site (Citabilité)
        </h3>
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${getScoreColor(score)}`}>{score}</span>
          <span className="text-sm text-slate-500">/ 100</span>
        </div>
      </div>

      {/* Schema.org Status */}
      <div className="mb-4 p-4 bg-slate-50 rounded-xl">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-violet-600" />
            <span className="font-medium text-slate-900">Données Structurées (Schema.org)</span>
          </div>
          {schema_org?.detected ? (
            <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Détecté</Badge>
          ) : (
            <Badge className="bg-red-100 text-red-700 hover:bg-red-100">Absent</Badge>
          )}
        </div>
        {schema_org?.detected && schema_org?.types?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {schema_org.types.map((type, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                {type}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Key Signals Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="p-3 bg-white rounded-lg border border-slate-100 text-center">
          <HelpCircle className={`w-5 h-5 mx-auto mb-1 ${faq_presence ? "text-emerald-500" : "text-slate-300"}`} />
          <p className="text-xs text-slate-600">FAQ</p>
          <p className={`text-sm font-medium ${faq_presence ? "text-emerald-600" : "text-slate-400"}`}>
            {faq_presence ? "Présent" : "Absent"}
          </p>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-100 text-center">
          <Shield className={`w-5 h-5 mx-auto mb-1 ${about_page ? "text-emerald-500" : "text-slate-300"}`} />
          <p className="text-xs text-slate-600">À propos</p>
          <p className={`text-sm font-medium ${about_page ? "text-emerald-600" : "text-slate-400"}`}>
            {about_page ? "Présent" : "Absent"}
          </p>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-100 text-center">
          <Link2 className={`w-5 h-5 mx-auto mb-1 ${contact_info ? "text-emerald-500" : "text-slate-300"}`} />
          <p className="text-xs text-slate-600">Contact</p>
          <p className={`text-sm font-medium ${contact_info ? "text-emerald-600" : "text-slate-400"}`}>
            {contact_info ? "Présent" : "Absent"}
          </p>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-100 text-center">
          <Shield className="w-5 h-5 mx-auto mb-1 text-violet-500" />
          <p className="text-xs text-slate-600">Signaux confiance</p>
          <p className="text-sm font-medium text-violet-600">{trust_signals?.length || 0}</p>
        </div>
      </div>

      {/* Trust Signals */}
      {trust_signals && trust_signals.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-medium text-slate-500 mb-2">Signaux de confiance détectés</p>
          <div className="flex flex-wrap gap-1">
            {trust_signals.map((signal, idx) => (
              <Badge key={idx} variant="outline" className="text-xs capitalize">
                {signal.replace("_", " ")}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Key Pages */}
      {key_pages && key_pages.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-medium text-slate-500 mb-2">Pages clés identifiées</p>
          <div className="flex flex-wrap gap-1">
            {key_pages.map((page, idx) => (
              <Badge key={idx} className="bg-cyan-100 text-cyan-700 hover:bg-cyan-100 text-xs capitalize">
                {page.replace("_", " ")}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="mt-4 p-4 bg-amber-50 rounded-xl">
          <p className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Recommandations pour améliorer la citabilité
          </p>
          <ul className="space-y-2">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="text-sm text-amber-700 flex items-start gap-2">
                <span className="text-amber-500">•</span>
                <div>
                  <span className="font-medium">{rec.action}</span>
                  {rec.impact && <span className="text-xs text-amber-600 ml-1">— {rec.impact}</span>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
};

// ================== BRAND ANALYSIS COMPONENT ==================
export const BrandAnalysisCard = ({ brandAnalysis }) => {
  if (!brandAnalysis) {
    return null;
  }

  const { variants_used, mention_quality_distribution, variants_found_summary } = brandAnalysis;

  const qualityColors = {
    strong: "bg-emerald-100 text-emerald-700",
    moderate: "bg-cyan-100 text-cyan-700",
    weak: "bg-amber-100 text-amber-700",
    variant_only: "bg-violet-100 text-violet-700",
    absent: "bg-slate-100 text-slate-500"
  };

  const qualityLabels = {
    strong: "Forte",
    moderate: "Modérée",
    weak: "Faible",
    variant_only: "Variante uniquement",
    absent: "Absent"
  };

  return (
    <Card className="p-6" data-testid="brand-analysis-card">
      <div className="flex items-center gap-2 mb-6">
        <Search className="w-5 h-5 text-violet-600" />
        <h3 className="text-lg font-semibold text-slate-900">Détection de Marque Avancée</h3>
      </div>

      {/* Mention Quality Distribution */}
      {mention_quality_distribution && Object.keys(mention_quality_distribution).length > 0 && (
        <div className="mb-6">
          <p className="text-sm font-medium text-slate-700 mb-3">Qualité des mentions</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(mention_quality_distribution).map(([quality, count]) => (
              <Badge
                key={quality}
                className={`${qualityColors[quality] || "bg-slate-100 text-slate-600"} hover:opacity-90`}
              >
                {qualityLabels[quality] || quality}: {count}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Variants Found */}
      {variants_found_summary && Object.keys(variants_found_summary).length > 0 && (
        <div className="mb-6">
          <p className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2">
            <Tag className="w-4 h-4" />
            Variantes détectées dans les réponses
          </p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(variants_found_summary).slice(0, 10).map(([variant, count]) => (
              <Badge key={variant} variant="outline" className="font-mono text-xs">
                {variant} <span className="text-violet-600 ml-1">×{count}</span>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Variants Used for Detection */}
      {variants_used && variants_used.length > 0 && (
        <details className="group">
          <summary className="text-sm text-slate-500 cursor-pointer hover:text-slate-700 flex items-center gap-1">
            <span>Voir les {variants_used.length} variantes surveillées</span>
          </summary>
          <div className="mt-2 p-3 bg-slate-50 rounded-lg max-h-32 overflow-y-auto">
            <div className="flex flex-wrap gap-1">
              {variants_used.map((variant, idx) => (
                <span key={idx} className="text-xs text-slate-500 font-mono bg-white px-2 py-0.5 rounded border">
                  {variant}
                </span>
              ))}
            </div>
          </div>
        </details>
      )}
    </Card>
  );
};

export default { ScanDiffCard, SiteEnrichmentCard, BrandAnalysisCard };
