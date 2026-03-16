import { memo, useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link2, FileText, Sparkles, Target, Loader2, AlertCircle, BarChart3 } from "lucide-react";

// Input Form Component
const OptimizerInputForm = memo(({ 
  onAnalyze, 
  loading, 
  quota, 
  onNavigatePricing 
}) => {
  const [inputMode, setInputMode] = useState('url');
  const [url, setUrl] = useState('');
  const [content, setContent] = useState('');
  const [useLLM, setUseLLM] = useState(true);
  const [error, setError] = useState(null);

  const handleSubmit = useCallback(() => {
    if (inputMode === 'url' && !url) {
      setError('Veuillez entrer une URL');
      return;
    }
    if (inputMode === 'content' && !content) {
      setError('Veuillez coller du contenu');
      return;
    }
    setError(null);
    onAnalyze({
      url: inputMode === 'url' ? url : null,
      content: inputMode === 'content' ? content : null,
      useLLM
    });
  }, [inputMode, url, content, useLLM, onAnalyze]);

  return (
    <div className="space-y-6">
      {/* Quota Info */}
      {quota && (
        <Card className="p-4 bg-slate-800/50 border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-violet-400" />
              <span className="text-sm text-slate-300">
                {quota.allowed 
                  ? `Optimisations restantes: ${quota.remaining}`
                  : quota.reason
                }
              </span>
            </div>
            {!quota.allowed && (
              <Button
                variant="link"
                onClick={onNavigatePricing}
                className="text-sm text-violet-400 hover:text-violet-300 p-0 h-auto"
              >
                Upgrader →
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Main Input Card */}
      <Card className="p-6 bg-slate-800/30 border-slate-700">
        {/* Input Mode Toggle */}
        <div className="flex gap-2 mb-6">
          <Button
            onClick={() => setInputMode('url')}
            variant={inputMode === 'url' ? 'default' : 'outline'}
            className={inputMode === 'url' 
              ? 'bg-violet-600 hover:bg-violet-700 text-white' 
              : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600'
            }
            data-testid="input-mode-url"
          >
            <Link2 className="w-4 h-4 mr-2" />
            URL
          </Button>
          <Button
            onClick={() => setInputMode('content')}
            variant={inputMode === 'content' ? 'default' : 'outline'}
            className={inputMode === 'content' 
              ? 'bg-violet-600 hover:bg-violet-700 text-white' 
              : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600'
            }
            data-testid="input-mode-content"
          >
            <FileText className="w-4 h-4 mr-2" />
            Contenu
          </Button>
        </div>

        {/* URL Input */}
        {inputMode === 'url' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              URL de l'article à analyser
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-white placeholder-slate-500"
              data-testid="url-input"
            />
          </div>
        )}

        {/* Content Input */}
        {inputMode === 'content' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Collez le contenu de votre article
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Collez le contenu HTML ou texte de votre article ici..."
              rows={6}
              className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent text-white placeholder-slate-500 font-mono text-sm resize-none"
              data-testid="content-input"
            />
          </div>
        )}

        {/* LLM Toggle */}
        <div className="flex items-center gap-3 mb-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useLLM}
              onChange={(e) => setUseLLM(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 text-violet-500 focus:ring-violet-500 bg-slate-900"
            />
            <span className="text-sm text-slate-300">
              Analyse enrichie par IA
            </span>
          </label>
          <Sparkles className="w-4 h-4 text-violet-400" />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <span className="text-red-400 text-sm">{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={loading || (quota && !quota.allowed)}
          className="w-full py-3 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 text-white font-semibold shadow-lg shadow-violet-500/25"
          data-testid="analyze-button"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Analyse en cours...
            </>
          ) : (
            <>
              <Target className="w-5 h-5 mr-2" />
              Analyser l'article
            </>
          )}
        </Button>
      </Card>

      {/* Features Info */}
      <Card className="p-4 bg-gradient-to-r from-violet-500/10 to-cyan-500/10 border-violet-500/20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          {[
            { icon: "🎯", label: "Score de citabilité", desc: "Évaluation GEO complète" },
            { icon: "⚡", label: "Quick Wins", desc: "Actions à impact immédiat" },
            { icon: "📊", label: "Plan d'action", desc: "Roadmap d'optimisation" }
          ].map((item, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <span className="text-2xl">{item.icon}</span>
              <span className="text-sm font-medium text-white">{item.label}</span>
              <span className="text-xs text-slate-400">{item.desc}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
});

OptimizerInputForm.displayName = 'OptimizerInputForm';

export default OptimizerInputForm;
