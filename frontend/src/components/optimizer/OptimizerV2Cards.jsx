import { memo, useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ChevronRight, Copy, Check, ArrowRight, TrendingUp, 
  AlertCircle, FileText, Code, ExternalLink, Sparkles 
} from "lucide-react";

// Rewrite Card - Shows original vs optimized side by side
export const RewriteCard = memo(({ rewrite, index }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(rewrite.optimized);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [rewrite.optimized]);
  
  return (
    <Card className="p-5 bg-slate-50 border-slate-200 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-slate-900">
          Paragraphe {index + 1} — {rewrite.section || 'Contenu'}
        </h4>
        <span className="text-emerald-600 font-bold text-sm">
          Impact : +{rewrite.impact_points || 0} pts
        </span>
      </div>
      
      {/* Side by side comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-stretch">
        {/* Original */}
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <span className="text-red-600 text-sm font-medium mb-2 block">Actuel</span>
          <p className="text-slate-800 text-sm leading-relaxed">"{rewrite.original}"</p>
        </div>
        
        {/* Arrow */}
        <div className="hidden md:flex items-center justify-center absolute left-1/2 -translate-x-1/2">
          <ChevronRight className="w-6 h-6 text-slate-400" />
        </div>
        
        {/* Optimized */}
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg relative">
          <span className="text-emerald-600 text-sm font-medium mb-2 block">Optimisé GEO</span>
          <p className="text-slate-800 text-sm leading-relaxed">"{rewrite.optimized}"</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="absolute top-2 right-2 text-emerald-600 hover:text-emerald-700"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          </Button>
        </div>
      </div>
      
      {/* Tags */}
      {rewrite.improvements && rewrite.improvements.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {rewrite.improvements.map((tag, i) => (
            <span key={i} className="text-xs text-slate-500 border-b border-dotted border-slate-400">
              {tag}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
});

RewriteCard.displayName = 'RewriteCard';

// Missing Content Card
export const MissingContentCard = memo(({ content, onCopy }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content.generated_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  }, [content.generated_content, onCopy]);
  
  const typeIcons = {
    faq: "❓",
    comparison_table: "📊",
    verdict: "✅",
    specs: "📋",
    pros_cons: "⚖️"
  };
  
  return (
    <Card className="p-5 bg-white border-amber-200 rounded-xl">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{typeIcons[content.type] || "📝"}</span>
          <div>
            <h4 className="font-semibold text-slate-900">{content.title}</h4>
            <p className="text-sm text-slate-600">{content.reason}</p>
          </div>
        </div>
        <Badge className="bg-amber-100 text-amber-700 border-0">
          +{content.impact_points || 5} pts
        </Badge>
      </div>
      
      {/* Generated content preview */}
      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 mb-4 max-h-60 overflow-y-auto">
        <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans">
          {content.generated_content}
        </pre>
      </div>
      
      <Button
        onClick={handleCopy}
        className="w-full bg-amber-500 hover:bg-amber-600 text-white"
      >
        {copied ? (
          <><Check className="w-4 h-4 mr-2" /> Copié !</>
        ) : (
          <><Copy className="w-4 h-4 mr-2" /> Copier ce contenu</>
        )}
      </Button>
    </Card>
  );
});

MissingContentCard.displayName = 'MissingContentCard';

// Competitor Source Card
export const CompetitorSourceCard = memo(({ source }) => {
  return (
    <Card className="p-5 bg-white border-slate-200 rounded-xl">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cyan-100 rounded-lg flex items-center justify-center">
            <ExternalLink className="w-5 h-5 text-cyan-600" />
          </div>
          <div>
            <h4 className="font-semibold text-slate-900">{source.name}</h4>
            <a 
              href={source.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-cyan-600 hover:underline"
            >
              {source.url?.replace(/^https?:\/\//, '').substring(0, 40)}...
            </a>
          </div>
        </div>
        <Badge className={`${source.cited_by_llms > 2 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'} border-0`}>
          Cité par {source.cited_by_llms || 0} LLMs
        </Badge>
      </div>
      
      {/* Why they're cited */}
      <div className="mb-4">
        <h5 className="text-sm font-medium text-slate-700 mb-2">Pourquoi ils sont cités :</h5>
        <ul className="space-y-1">
          {source.reasons?.map((reason, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
              <TrendingUp className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
              {reason}
            </li>
          ))}
        </ul>
      </div>
      
      {/* What you're missing */}
      <div className="p-3 bg-red-50 rounded-lg border border-red-200">
        <h5 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Ce qui vous manque :
        </h5>
        <ul className="space-y-1">
          {source.missing_elements?.map((el, i) => (
            <li key={i} className="text-sm text-red-600 pl-4">• {el}</li>
          ))}
        </ul>
      </div>
    </Card>
  );
});

CompetitorSourceCard.displayName = 'CompetitorSourceCard';

// Schema Markup Card
export const SchemaMarkupCard = memo(({ schema, onCopy }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(schema.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  }, [schema.code, onCopy]);
  
  return (
    <Card className="p-5 bg-white border-violet-200 rounded-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center">
            <Code className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h4 className="font-semibold text-slate-900">{schema.name}</h4>
            <p className="text-sm text-slate-600">{schema.description}</p>
          </div>
        </div>
        <Badge className="bg-violet-100 text-violet-700 border-0">
          {schema.type}
        </Badge>
      </div>
      
      {/* Code preview */}
      <div className="p-4 bg-slate-900 rounded-lg mb-4 max-h-60 overflow-y-auto">
        <pre className="text-sm text-emerald-400 font-mono whitespace-pre-wrap">
          {schema.code}
        </pre>
      </div>
      
      <div className="flex gap-2">
        <Button
          onClick={handleCopy}
          className="flex-1 bg-violet-600 hover:bg-violet-700 text-white"
        >
          {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
          {copied ? 'Copié !' : 'Copier le code'}
        </Button>
      </div>
    </Card>
  );
});

SchemaMarkupCard.displayName = 'SchemaMarkupCard';

// Projected Score Card
export const ProjectedScoreCard = memo(({ currentScore, projectedScore, improvements }) => {
  const delta = projectedScore - currentScore;
  
  return (
    <Card className="p-6 bg-gradient-to-br from-slate-50 to-emerald-50 border-emerald-200 rounded-xl">
      <h3 className="font-semibold text-slate-900 mb-4">Score projeté après optimisation</h3>
      
      <div className="flex items-center gap-4 mb-4">
        <span className="text-4xl font-bold text-red-500">{currentScore}</span>
        <ArrowRight className="w-6 h-6 text-slate-400" />
        <span className="text-4xl font-bold text-emerald-500">{projectedScore}</span>
        <span className="text-slate-500">/100</span>
        
        {/* Progress bar */}
        <div className="flex-1 h-3 bg-slate-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-red-400 via-amber-400 to-emerald-500 rounded-full transition-all duration-500"
            style={{ width: `${projectedScore}%` }}
          />
        </div>
      </div>
      
      <p className="text-sm text-slate-600">
        Estimation basée sur l'application des {improvements?.rewrites || 0} rewrites + {improvements?.contents || 0} contenus manquants + balisage
      </p>
    </Card>
  );
});

ProjectedScoreCard.displayName = 'ProjectedScoreCard';

// Diagnostic Badge Component
export const DiagnosticBadge = memo(({ label, value, status }) => {
  const statusColors = {
    good: "bg-emerald-100 text-emerald-700 border-emerald-200",
    warning: "bg-amber-100 text-amber-700 border-amber-200",
    bad: "bg-red-100 text-red-700 border-red-200",
    neutral: "bg-slate-100 text-slate-700 border-slate-200"
  };
  
  return (
    <div className={`px-4 py-3 rounded-xl border ${statusColors[status] || statusColors.neutral}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  );
});

DiagnosticBadge.displayName = 'DiagnosticBadge';

export default RewriteCard;
