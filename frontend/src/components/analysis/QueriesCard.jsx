import { memo, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { CheckCircle2 } from "lucide-react";

// Query type configurations
const QUERY_TYPES = {
  transactional: { 
    label: "Transactionnel", 
    desc: "Intentions d'achat",
    icon: "💳", 
    color: "border-l-violet-500",
    bg: "bg-violet-50 border-violet-200"
  },
  comparative: { 
    label: "Comparatif", 
    desc: "Recherche du meilleur",
    icon: "⚖️", 
    color: "border-l-cyan-500",
    bg: "bg-cyan-50 border-cyan-200"
  },
  informational: { 
    label: "Informationnel", 
    desc: "Recherche d'information",
    icon: "📚", 
    color: "border-l-emerald-500",
    bg: "bg-emerald-50 border-emerald-200"
  },
  local: { 
    label: "Local", 
    desc: "Recherche géographique",
    icon: "📍", 
    color: "border-l-amber-500",
    bg: "bg-amber-50 border-amber-200"
  },
  exploratory: { 
    label: "Exploratoire", 
    desc: "Demande de recommandation",
    icon: "🔍", 
    color: "border-l-purple-500",
    bg: "bg-purple-50 border-purple-200"
  }
};

// Single Query Item - Memoized for performance
const QueryItem = memo(({ query }) => {
  const mentionRate = query.mention_rate || 0;
  
  return (
    <div className="p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-slate-800 font-medium text-sm truncate" title={query.query_text}>
            "{query.query_text}"
          </p>
          <div className="flex items-center gap-3 mt-2 text-xs flex-wrap">
            <span className={`px-2 py-0.5 rounded-full whitespace-nowrap ${
              mentionRate >= 50 
                ? "bg-emerald-100 text-emerald-700" 
                : mentionRate > 0 
                  ? "bg-amber-100 text-amber-700"
                  : "bg-red-100 text-red-700"
            }`}>
              {Math.round(mentionRate)}% mentions
            </span>
            {query.stability?.consistent && (
              <span className="flex items-center gap-1 text-emerald-600 whitespace-nowrap">
                <CheckCircle2 className="w-3 h-3" />
                Stable
              </span>
            )}
            <span className="text-slate-500 whitespace-nowrap">
              Score: {Math.round(query.avg_score || 0)}/100
            </span>
          </div>
        </div>
        {/* AI Response indicators */}
        <div className="flex flex-wrap gap-1 max-w-[100px] flex-shrink-0">
          {query.responses?.slice(0, 3).map((resp, idx) => (
            <span
              key={idx}
              className={`text-xs px-1.5 py-0.5 rounded ${
                resp.brand_mentioned
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-200 text-slate-500"
              }`}
              title={`${resp.ai_type}: ${resp.role || 'N/A'}`}
            >
              {resp.ai_type?.charAt(0).toUpperCase() || '?'}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
});

QueryItem.displayName = 'QueryItem';

// Query Type Group - Memoized
const QueryTypeGroup = memo(({ type, queries }) => {
  const typeInfo = QUERY_TYPES[type] || { 
    label: type, 
    desc: "", 
    color: "border-l-slate-500",
    icon: "📊"
  };
  
  return (
    <div className={`border-l-4 ${typeInfo.color} pl-4`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="font-semibold text-slate-900">{typeInfo.label}</h4>
          <p className="text-xs text-slate-500">{typeInfo.desc}</p>
        </div>
        <span className="text-sm text-slate-600">{queries.length} questions</span>
      </div>
      <div className="space-y-2">
        {queries.map((query, idx) => (
          <QueryItem key={query.query_text || idx} query={query} />
        ))}
      </div>
    </div>
  );
});

QueryTypeGroup.displayName = 'QueryTypeGroup';

// Main Queries Card Component
const QueriesCard = ({ queryScores }) => {
  // Group queries by type - memoized for performance
  const groupedQueries = useMemo(() => {
    if (!queryScores || queryScores.length === 0) return {};
    
    return queryScores.reduce((groups, query) => {
      const type = query.query_type || 'general';
      if (!groups[type]) groups[type] = [];
      groups[type].push(query);
      return groups;
    }, {});
  }, [queryScores]);
  
  // Calculate global mention rate
  const globalMentionRate = useMemo(() => {
    if (!queryScores || queryScores.length === 0) return 0;
    const total = queryScores.reduce((acc, q) => acc + (q.mention_rate || 0), 0);
    return Math.round(total / queryScores.length);
  }, [queryScores]);
  
  return (
    <Card className="p-6 bg-white border-slate-100">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Questions Analysées</h3>
          <p className="text-sm text-slate-600">
            {queryScores?.length || 0} requêtes simulant des utilisateurs réels
          </p>
        </div>
        {queryScores && queryScores.length > 0 && (
          <div className="text-right">
            <p className="text-sm text-slate-600">Taux de mention global</p>
            <p className="text-2xl font-bold text-violet-600">{globalMentionRate}%</p>
          </div>
        )}
      </div>
      
      {queryScores && queryScores.length > 0 ? (
        <>
          <div className="space-y-6">
            {Object.entries(groupedQueries).map(([type, queries]) => (
              <QueryTypeGroup key={type} type={type} queries={queries} />
            ))}
          </div>
          
          {/* Legend */}
          <div className="mt-6 pt-4 border-t border-slate-200">
            <p className="text-xs text-slate-500 mb-2">Légende :</p>
            <div className="flex flex-wrap gap-4 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded bg-emerald-100"></span>
                <span className="text-slate-600">Marque mentionnée</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded bg-slate-200"></span>
                <span className="text-slate-600">Marque absente</span>
              </span>
              <span className="text-slate-400">|</span>
              <span className="text-slate-500">C = ChatGPT • G = Gemini • P = Perplexity</span>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-slate-500">
          Les questions analysées apparaîtront ici après l'analyse.
        </div>
      )}
    </Card>
  );
};

// Query Type Breakdown Summary Card
export const QueryTypeBreakdown = ({ queryTypeBreakdown }) => {
  if (!queryTypeBreakdown || Object.keys(queryTypeBreakdown).length === 0) return null;
  
  return (
    <Card className="p-6 bg-white border-slate-100">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Performance par Type</h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(queryTypeBreakdown).map(([type, data]) => {
          const typeInfo = QUERY_TYPES[type] || { label: type, icon: "📊", bg: "bg-slate-50 border-slate-200" };
          
          return (
            <div key={type} className={`p-3 rounded-lg border ${typeInfo.bg}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{typeInfo.icon}</span>
                <span className="text-xs font-medium text-slate-700">{typeInfo.label}</span>
              </div>
              <div className="text-xl font-bold text-slate-900">{Math.round(data.avg_score || 0)}</div>
              <p className="text-xs text-slate-600">
                {data.count} req. • {Math.round(data.mention_rate || 0)}%
              </p>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default memo(QueriesCard);
