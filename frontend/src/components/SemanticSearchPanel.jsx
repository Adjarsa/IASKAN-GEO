import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Search,
  FileText,
  Link2,
  Database,
  Loader2,
  ChevronRight,
  Tag,
  Grid3x3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Plus,
  X,
  ArrowRight,
  Sparkles,
  Layers,
  Target,
  Lightbulb
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CONTENT_TYPE_CONFIG = {
  article: { label: 'Article', icon: FileText, color: 'text-blue-400', bg: 'bg-blue-500/20' },
  page: { label: 'Page', icon: Link2, color: 'text-purple-400', bg: 'bg-purple-500/20' },
  faq: { label: 'FAQ', icon: Lightbulb, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  product: { label: 'Produit', icon: Tag, color: 'text-green-400', bg: 'bg-green-500/20' }
};

export function SemanticSearchPanel({ projectId, onClose }) {
  const [activeTab, setActiveTab] = useState('search'); // search, gaps, clusters, index
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('queries'); // queries, content
  const [searchResults, setSearchResults] = useState([]);
  
  // Gaps state
  const [gaps, setGaps] = useState([]);
  
  // Clusters state
  const [clusters, setClusters] = useState([]);
  
  // Index state
  const [indexMode, setIndexMode] = useState('query'); // query, content
  const [indexForm, setIndexForm] = useState({
    query_text: '',
    query_type: 'informational',
    content_type: 'article',
    title: '',
    url: '',
    content: ''
  });

  useEffect(() => {
    fetchStats();
  }, [projectId]);

  const fetchStats = async () => {
    try {
      const res = await axios.get(
        `${BACKEND_URL}/api/semantic/stats/${projectId}`,
        { withCredentials: true }
      );
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Entrez une requête de recherche');
      return;
    }

    setLoading(true);
    try {
      const endpoint = searchType === 'queries' 
        ? '/api/semantic/search/queries'
        : '/api/semantic/search/content';
      
      const payload = searchType === 'queries'
        ? { query: searchQuery, project_id: projectId, limit: 15 }
        : { text: searchQuery, project_id: projectId, limit: 15 };
      
      const res = await axios.post(
        `${BACKEND_URL}${endpoint}`,
        payload,
        { withCredentials: true }
      );
      
      setSearchResults(res.data.results || []);
      
      if (res.data.results?.length === 0) {
        toast.info('Aucun résultat trouvé');
      }
    } catch (err) {
      console.error('Search error:', err);
      toast.error('Erreur lors de la recherche');
    } finally {
      setLoading(false);
    }
  };

  const fetchGaps = async () => {
    setLoading(true);
    try {
      const res = await axios.get(
        `${BACKEND_URL}/api/semantic/gaps/${projectId}`,
        { withCredentials: true }
      );
      setGaps(res.data.gaps || []);
    } catch (err) {
      console.error('Error fetching gaps:', err);
      toast.error('Erreur lors du chargement des lacunes');
    } finally {
      setLoading(false);
    }
  };

  const fetchClusters = async () => {
    setLoading(true);
    try {
      const res = await axios.get(
        `${BACKEND_URL}/api/semantic/clusters/${projectId}`,
        { withCredentials: true }
      );
      setClusters(res.data.clusters || []);
    } catch (err) {
      console.error('Error fetching clusters:', err);
      toast.error('Erreur lors du chargement des clusters');
    } finally {
      setLoading(false);
    }
  };

  const handleIndex = async () => {
    setLoading(true);
    try {
      if (indexMode === 'query') {
        if (!indexForm.query_text.trim()) {
          toast.error('Entrez une requête à indexer');
          setLoading(false);
          return;
        }
        
        await axios.post(
          `${BACKEND_URL}/api/semantic/index/query`,
          {
            project_id: projectId,
            query_text: indexForm.query_text,
            query_type: indexForm.query_type,
            source: 'manual'
          },
          { withCredentials: true }
        );
        
        toast.success('Requête indexée avec succès');
        setIndexForm({ ...indexForm, query_text: '' });
      } else {
        if (!indexForm.title.trim() || !indexForm.content.trim()) {
          toast.error('Titre et contenu requis');
          setLoading(false);
          return;
        }
        
        await axios.post(
          `${BACKEND_URL}/api/semantic/index/content`,
          {
            project_id: projectId,
            content_type: indexForm.content_type,
            title: indexForm.title,
            url: indexForm.url,
            content: indexForm.content
          },
          { withCredentials: true }
        );
        
        toast.success('Contenu indexé avec succès');
        setIndexForm({ ...indexForm, title: '', url: '', content: '' });
      }
      
      fetchStats();
    } catch (err) {
      console.error('Index error:', err);
      toast.error("Erreur lors de l'indexation");
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'search', label: 'Recherche', icon: Search },
    { id: 'gaps', label: 'Lacunes', icon: AlertTriangle },
    { id: 'clusters', label: 'Clusters', icon: Grid3x3 },
    { id: 'index', label: 'Indexer', icon: Plus }
  ];

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Recherche Sémantique</h2>
            <p className="text-sm text-slate-400">Powered by pgvector + OpenAI</p>
          </div>
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-800 text-slate-400"
            data-testid="close-semantic-panel"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-700 flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-violet-400" />
            <span className="text-slate-400">Requêtes:</span>
            <span className="text-white font-medium">{stats.query_embeddings}</span>
          </div>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-400">Contenus:</span>
            <span className="text-white font-medium">{stats.content_embeddings}</span>
          </div>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-green-400" />
            <span className="text-slate-400">Réponses:</span>
            <span className="text-white font-medium">{stats.response_embeddings}</span>
          </div>
          <div className={`ml-auto px-2 py-0.5 rounded text-xs ${
            stats.embedding_service_available 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-red-500/20 text-red-400'
          }`}>
            {stats.embedding_service_available ? 'Service actif' : 'Service limité'}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                if (tab.id === 'gaps' && gaps.length === 0) fetchGaps();
                if (tab.id === 'clusters' && clusters.length === 0) fetchClusters();
              }}
              className={`flex-1 px-4 py-3 flex items-center justify-center gap-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-violet-400 bg-violet-500/10 border-b-2 border-violet-400'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="p-4 max-h-[600px] overflow-y-auto">
        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-4">
            {/* Search type toggle */}
            <div className="flex gap-2">
              <button
                onClick={() => setSearchType('queries')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  searchType === 'queries'
                    ? 'bg-violet-500/20 text-violet-400'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                Requêtes similaires
              </button>
              <button
                onClick={() => setSearchType('content')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  searchType === 'content'
                    ? 'bg-violet-500/20 text-violet-400'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                Contenus similaires
              </button>
            </div>

            {/* Search input */}
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder={searchType === 'queries' 
                    ? "Rechercher des requêtes similaires..."
                    : "Rechercher des contenus similaires..."
                  }
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500"
                  data-testid="semantic-search-input"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={loading}
                className="px-4 py-2.5 bg-violet-500 hover:bg-violet-600 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2"
                data-testid="semantic-search-btn"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Rechercher
              </button>
            </div>

            {/* Results */}
            {searchResults.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-slate-400">
                  {searchResults.length} résultat(s) trouvé(s)
                </p>
                {searchResults.map((result, i) => (
                  <div 
                    key={i}
                    className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-slate-600"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        {searchType === 'queries' ? (
                          <>
                            <p className="text-white font-medium">{result.query_text}</p>
                            <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                              <span className="px-2 py-0.5 bg-slate-700 rounded">
                                {result.query_type || 'général'}
                              </span>
                              <span>Source: {result.source || 'inconnu'}</span>
                            </div>
                          </>
                        ) : (
                          <>
                            <p className="text-white font-medium">{result.title}</p>
                            {result.url && (
                              <a 
                                href={result.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-violet-400 hover:underline"
                              >
                                {result.url}
                              </a>
                            )}
                            {result.snippet && (
                              <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                                {result.snippet}
                              </p>
                            )}
                          </>
                        )}
                      </div>
                      <div className="flex flex-col items-end">
                        <div className={`text-sm font-medium ${
                          result.similarity >= 0.8 ? 'text-green-400' :
                          result.similarity >= 0.6 ? 'text-yellow-400' :
                          'text-slate-400'
                        }`}>
                          {Math.round(result.similarity * 100)}%
                        </div>
                        <span className="text-xs text-slate-500">similarité</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Gaps Tab */}
        {activeTab === 'gaps' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Opportunités de contenu identifiées
              </p>
              <button
                onClick={fetchGaps}
                disabled={loading}
                className="text-sm text-violet-400 hover:underline flex items-center gap-1"
              >
                {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                Actualiser
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
              </div>
            ) : gaps.length > 0 ? (
              <div className="space-y-3">
                {gaps.map((gap, i) => (
                  <div key={i} className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="text-white font-medium">{gap.query_text}</p>
                        <div className="flex items-center gap-2 mt-2 text-xs">
                          <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded">
                            {gap.query_type}
                          </span>
                          <span className="text-slate-400">
                            AI: {gap.ai_engine}
                          </span>
                        </div>
                        <p className="text-sm text-slate-400 mt-2">
                          <Target className="w-3 h-3 inline mr-1" />
                          {gap.suggested_action}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-amber-400">
                          {Math.round(gap.importance_score)}
                        </div>
                        <span className="text-xs text-slate-500">importance</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Aucune lacune de contenu identifiée</p>
                <p className="text-sm mt-1">Lancez plus d'analyses pour découvrir des opportunités</p>
              </div>
            )}
          </div>
        )}

        {/* Clusters Tab */}
        {activeTab === 'clusters' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Groupes sémantiques de requêtes
              </p>
              <button
                onClick={fetchClusters}
                disabled={loading}
                className="text-sm text-violet-400 hover:underline flex items-center gap-1"
              >
                {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                Actualiser
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
              </div>
            ) : clusters.length > 0 ? (
              <div className="space-y-4">
                {clusters.map((cluster, i) => (
                  <div key={i} className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-white font-medium flex items-center gap-2">
                        <Grid3x3 className="w-4 h-4 text-violet-400" />
                        {cluster.name}
                      </h4>
                      <span className="text-sm text-slate-400">
                        {cluster.query_count} requêtes
                      </span>
                    </div>
                    
                    {cluster.keywords?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {cluster.keywords.map((kw, j) => (
                          <span key={j} className="px-2 py-0.5 bg-violet-500/20 text-violet-400 rounded text-xs">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    <div className="space-y-1">
                      {cluster.queries?.slice(0, 3).map((q, j) => (
                        <div key={j} className="text-sm text-slate-300 flex items-center gap-2">
                          <ChevronRight className="w-3 h-3 text-slate-500" />
                          {q.text}
                        </div>
                      ))}
                      {cluster.queries?.length > 3 && (
                        <p className="text-xs text-slate-500 ml-5">
                          +{cluster.queries.length - 3} autres requêtes
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <Grid3x3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Aucun cluster disponible</p>
                <p className="text-sm mt-1">Indexez des requêtes pour créer des clusters</p>
              </div>
            )}
          </div>
        )}

        {/* Index Tab */}
        {activeTab === 'index' && (
          <div className="space-y-4">
            {/* Mode toggle */}
            <div className="flex gap-2">
              <button
                onClick={() => setIndexMode('query')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  indexMode === 'query'
                    ? 'bg-violet-500/20 text-violet-400'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                Indexer une requête
              </button>
              <button
                onClick={() => setIndexMode('content')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  indexMode === 'content'
                    ? 'bg-violet-500/20 text-violet-400'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                Indexer un contenu
              </button>
            </div>

            {indexMode === 'query' ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Requête</label>
                  <input
                    type="text"
                    value={indexForm.query_text}
                    onChange={(e) => setIndexForm({ ...indexForm, query_text: e.target.value })}
                    placeholder="Ex: meilleur outil SEO pour e-commerce"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500"
                    data-testid="index-query-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Type de requête</label>
                  <select
                    value={indexForm.query_type}
                    onChange={(e) => setIndexForm({ ...indexForm, query_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="informational">Informationnelle</option>
                    <option value="transactional">Transactionnelle</option>
                    <option value="comparative">Comparative</option>
                    <option value="exploratory">Exploratoire</option>
                    <option value="local">Locale</option>
                  </select>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Type de contenu</label>
                  <select
                    value={indexForm.content_type}
                    onChange={(e) => setIndexForm({ ...indexForm, content_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="article">Article</option>
                    <option value="page">Page</option>
                    <option value="faq">FAQ</option>
                    <option value="product">Produit</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Titre</label>
                  <input
                    type="text"
                    value={indexForm.title}
                    onChange={(e) => setIndexForm({ ...indexForm, title: e.target.value })}
                    placeholder="Titre du contenu"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500"
                    data-testid="index-title-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">URL (optionnel)</label>
                  <input
                    type="text"
                    value={indexForm.url}
                    onChange={(e) => setIndexForm({ ...indexForm, url: e.target.value })}
                    placeholder="https://..."
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Contenu</label>
                  <textarea
                    value={indexForm.content}
                    onChange={(e) => setIndexForm({ ...indexForm, content: e.target.value })}
                    placeholder="Collez le contenu à indexer..."
                    rows={5}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500 resize-none"
                    data-testid="index-content-textarea"
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleIndex}
              disabled={loading}
              className="w-full py-2.5 bg-violet-500 hover:bg-violet-600 disabled:opacity-50 rounded-lg text-white font-medium flex items-center justify-center gap-2"
              data-testid="index-submit-btn"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Indexer
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default SemanticSearchPanel;
