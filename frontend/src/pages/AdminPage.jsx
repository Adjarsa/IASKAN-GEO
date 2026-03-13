import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Users, 
  BarChart3, 
  CreditCard, 
  AlertTriangle,
  TrendingUp,
  Loader2,
  Search,
  ChevronRight,
  Building2,
  FileText,
  Sparkles,
  Shield,
  RefreshCw,
  LineChart as LineChartIcon
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Stat card component
const StatCard = ({ title, value, change, icon: Icon, color = "violet" }) => {
  const colorClasses = {
    violet: "from-violet-500 to-violet-600",
    cyan: "from-cyan-500 to-cyan-600",
    green: "from-green-500 to-green-600",
    orange: "from-orange-500 to-orange-600"
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {change >= 0 ? '+' : ''}{change}%
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
};

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/admin/stats`, { withCredentials: true }),
        axios.get(`${BACKEND_URL}/api/admin/users?limit=50`, { withCredentials: true })
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data.users);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const searchUsers = async () => {
    if (!searchQuery.trim()) {
      fetchData();
      return;
    }
    
    try {
      const res = await axios.get(
        `${BACKEND_URL}/api/admin/users?search=${encodeURIComponent(searchQuery)}`,
        { withCredentials: true }
      );
      setUsers(res.data.users);
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  const updateUserPlan = async (userId, newPlan) => {
    try {
      await axios.put(
        `${BACKEND_URL}/api/admin/users/${userId}/subscription`,
        { plan: newPlan },
        { withCredentials: true }
      );
      fetchData();
    } catch (err) {
      console.error('Update error:', err);
    }
  };

  const resetUserQuota = async (userId) => {
    try {
      await axios.post(
        `${BACKEND_URL}/api/admin/users/${userId}/reset-quota`,
        {},
        { withCredentials: true }
      );
      fetchData();
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-white text-lg">{error}</p>
          <p className="text-slate-400 text-sm mt-2">Accès admin requis</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Admin Backoffice</h1>
            <p className="text-slate-400">Gestion de la plateforme IAskan</p>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Actualiser
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-700 mb-6">
          <div className="flex gap-4">
            {[
              { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
              { id: 'analytics', label: 'Analytics', icon: LineChartIcon },
              { id: 'users', label: 'Utilisateurs', icon: Users },
              { id: 'analyses', label: 'Analyses', icon: FileText }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-violet-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <AnalyticsTab stats={stats} />
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-6">
            {/* Main Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard 
                title="Utilisateurs totaux" 
                value={stats.users?.total || 0}
                icon={Users}
                color="violet"
              />
              <StatCard 
                title="Analyses ce mois" 
                value={stats.analyses?.this_month || 0}
                icon={BarChart3}
                color="cyan"
              />
              <StatCard 
                title="MRR estimé" 
                value={`${stats.revenue?.estimated_mrr || 0}€`}
                icon={CreditCard}
                color="green"
              />
              <StatCard 
                title="Taux de conversion" 
                value={`${stats.subscriptions?.conversion_rate || 0}%`}
                icon={TrendingUp}
                color="orange"
              />
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* User Stats */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-violet-400" />
                  Utilisateurs
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Aujourd'hui</span>
                    <span className="font-semibold">{stats.users?.today || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Ce mois</span>
                    <span className="font-semibold">{stats.users?.this_month || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Vérifiés</span>
                    <span className="font-semibold">{stats.users?.verification_rate || 0}%</span>
                  </div>
                </div>
              </div>

              {/* Subscription Distribution */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-cyan-400" />
                  Abonnements
                </h3>
                <div className="space-y-3">
                  {Object.entries(stats.subscriptions?.distribution || {}).map(([plan, count]) => (
                    <div key={plan} className="flex justify-between">
                      <span className="text-slate-400 capitalize">{plan}</span>
                      <span className="font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Analysis Stats */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-green-400" />
                  Analyses
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total</span>
                    <span className="font-semibold">{stats.analyses?.total || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Réussies</span>
                    <span className="font-semibold text-green-400">{stats.analyses?.completed || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Échecs</span>
                    <span className="font-semibold text-red-400">{stats.analyses?.failed || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Taux de succès</span>
                    <span className="font-semibold">{stats.analyses?.success_rate || 0}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Additional Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Organizations */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-orange-400" />
                  Organisations
                </h3>
                <p className="text-3xl font-bold">{stats.organizations?.total || 0}</p>
                <p className="text-sm text-slate-400 mt-1">Workspaces créés</p>
              </div>

              {/* Article Optimizer */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-violet-400" />
                  Optimiseur d'Articles
                </h3>
                <p className="text-3xl font-bold">{stats.article_optimizer?.total || 0}</p>
                <p className="text-sm text-slate-400 mt-1">
                  {stats.article_optimizer?.this_month || 0} ce mois
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            {/* Search */}
            <div className="flex gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchUsers()}
                  placeholder="Rechercher par email ou nom..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-violet-500 text-white placeholder-slate-500"
                />
              </div>
              <button
                onClick={searchUsers}
                className="px-4 py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600"
              >
                Rechercher
              </button>
            </div>

            {/* Users Table */}
            <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Utilisateur</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Plan</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Usage</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {users.map((user) => (
                    <tr key={user.user_id} className="hover:bg-slate-800/50">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-white">{user.name}</p>
                          <p className="text-sm text-slate-400">{user.email}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          user.subscription?.plan === 'business' ? 'bg-violet-500/20 text-violet-400' :
                          user.subscription?.plan === 'pro' ? 'bg-cyan-500/20 text-cyan-400' :
                          user.subscription?.plan === 'starter' ? 'bg-green-500/20 text-green-400' :
                          'bg-slate-600 text-slate-300'
                        }`}>
                          {user.subscription?.plan || 'free'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {user.subscription?.queries_used || 0} / {user.subscription?.queries_limit || '∞'} requêtes
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <select
                            value={user.subscription?.plan || 'free'}
                            onChange={(e) => updateUserPlan(user.user_id, e.target.value)}
                            className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-sm text-white"
                          >
                            <option value="free">Free</option>
                            <option value="starter">Starter</option>
                            <option value="pro">Pro</option>
                            <option value="business">Business</option>
                          </select>
                          <button
                            onClick={() => resetUserQuota(user.user_id)}
                            className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs hover:bg-orange-500/30"
                            title="Réinitialiser quota"
                          >
                            Reset
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Analyses Tab */}
        {activeTab === 'analyses' && (
          <AnalysesTab />
        )}
      </div>
    </div>
  );
}

// Separate component for Analyses tab
function AnalysesTab() {
  const [analyses, setAnalyses] = useState([]);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('all');

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const fetchAnalyses = async () => {
    setLoading(true);
    try {
      const [analysesRes, errorsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/admin/analyses?limit=50`, { withCredentials: true }),
        axios.get(`${BACKEND_URL}/api/admin/errors?limit=20`, { withCredentials: true })
      ]);
      setAnalyses(analysesRes.data.analyses || []);
      setErrors(errorsRes.data.errors || []);
    } catch (err) {
      console.error('Fetch analyses error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Sub-tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveSubTab('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeSubTab === 'all' 
              ? 'bg-violet-500 text-white' 
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Toutes ({analyses.length})
        </button>
        <button
          onClick={() => setActiveSubTab('errors')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeSubTab === 'errors' 
              ? 'bg-red-500 text-white' 
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          <AlertTriangle className="w-4 h-4 inline mr-1" />
          Erreurs ({errors.length})
        </button>
      </div>

      {/* All Analyses */}
      {activeSubTab === 'all' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">ID</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Status</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Score</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-300">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {analyses.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-4 py-8 text-center text-slate-400">
                    Aucune analyse pour le moment
                  </td>
                </tr>
              ) : (
                analyses.map((analysis) => (
                  <tr key={analysis.analysis_id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono text-slate-300">
                        {analysis.analysis_id?.slice(0, 12)}...
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        analysis.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        analysis.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                        analysis.status === 'running' ? 'bg-cyan-500/20 text-cyan-400' :
                        'bg-slate-600 text-slate-300'
                      }`}>
                        {analysis.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {analysis.global_score ? (
                        <span className="font-semibold text-white">
                          {analysis.global_score}/100
                          {analysis.grade && <span className="ml-2 text-violet-400">{analysis.grade}</span>}
                        </span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {analysis.created_at ? new Date(analysis.created_at).toLocaleString('fr-FR') : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Errors */}
      {activeSubTab === 'errors' && (
        <div className="space-y-4">
          {errors.length === 0 ? (
            <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center">
              <AlertTriangle className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <p className="text-slate-300">Aucune erreur récente</p>
            </div>
          ) : (
            errors.map((error) => (
              <div key={error.analysis_id} className="bg-slate-800/50 rounded-xl p-4 border border-red-500/30">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-mono text-slate-400 mb-1">
                      {error.analysis_id}
                    </p>
                    <p className="text-red-300">{error.error_message || 'Erreur inconnue'}</p>
                    <p className="text-xs text-slate-500 mt-2">
                      {error.created_at ? new Date(error.created_at).toLocaleString('fr-FR') : ''}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// Analytics Tab Component with Charts
function AnalyticsTab({ stats }) {
  const [apiUsage, setApiUsage] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApiUsage();
  }, []);

  const fetchApiUsage = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/admin/api-usage?days=30`, { 
        withCredentials: true 
      });
      setApiUsage(res.data.daily_usage || []);
    } catch (err) {
      console.error('API usage error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Prepare data for subscription pie chart
  const subscriptionData = stats?.subscriptions?.distribution 
    ? Object.entries(stats.subscriptions.distribution).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value
      }))
    : [];

  const COLORS = ['#8b5cf6', '#06b6d4', '#22c55e', '#f97316'];

  // Generate mock trend data if no real data
  const trendData = apiUsage.length > 0 ? apiUsage : [
    { date: 'Lun', count: 0, completed: 0, failed: 0 },
    { date: 'Mar', count: 0, completed: 0, failed: 0 },
    { date: 'Mer', count: 0, completed: 0, failed: 0 },
    { date: 'Jeu', count: 0, completed: 0, failed: 0 },
    { date: 'Ven', count: 0, completed: 0, failed: 0 },
    { date: 'Sam', count: 0, completed: 0, failed: 0 },
    { date: 'Dim', count: 0, completed: 0, failed: 0 }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-violet-500/20 to-violet-600/20 rounded-xl p-4 border border-violet-500/30">
          <p className="text-sm text-violet-300 mb-1">Utilisateurs actifs</p>
          <p className="text-3xl font-bold text-white">{stats?.users?.total || 0}</p>
          <p className="text-xs text-violet-400 mt-1">+{stats?.users?.this_month || 0} ce mois</p>
        </div>
        <div className="bg-gradient-to-br from-cyan-500/20 to-cyan-600/20 rounded-xl p-4 border border-cyan-500/30">
          <p className="text-sm text-cyan-300 mb-1">Analyses totales</p>
          <p className="text-3xl font-bold text-white">{stats?.analyses?.total || 0}</p>
          <p className="text-xs text-cyan-400 mt-1">{stats?.analyses?.success_rate || 0}% succès</p>
        </div>
        <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 rounded-xl p-4 border border-green-500/30">
          <p className="text-sm text-green-300 mb-1">MRR Estimé</p>
          <p className="text-3xl font-bold text-white">{stats?.revenue?.estimated_mrr || 0}€</p>
          <p className="text-xs text-green-400 mt-1">{stats?.subscriptions?.paid_users || 0} payants</p>
        </div>
        <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/20 rounded-xl p-4 border border-orange-500/30">
          <p className="text-sm text-orange-300 mb-1">Taux conversion</p>
          <p className="text-3xl font-bold text-white">{stats?.subscriptions?.conversion_rate || 0}%</p>
          <p className="text-xs text-orange-400 mt-1">Free → Payant</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Analyses Trend */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-violet-400" />
            Évolution des Analyses (30 jours)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorAnalyses" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="date" 
                  stroke="#94a3b8" 
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  tickFormatter={(value) => value.slice(5)}
                />
                <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#f8fafc' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#8b5cf6" 
                  fillOpacity={1} 
                  fill="url(#colorAnalyses)"
                  name="Analyses"
                />
                <Line 
                  type="monotone" 
                  dataKey="completed" 
                  stroke="#22c55e" 
                  strokeWidth={2}
                  dot={false}
                  name="Réussies"
                />
                <Line 
                  type="monotone" 
                  dataKey="failed" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  dot={false}
                  name="Échouées"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Subscription Distribution */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-cyan-400" />
            Répartition des Abonnements
          </h3>
          <div className="h-64 flex items-center justify-center">
            {subscriptionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={subscriptionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                    labelLine={{ stroke: '#64748b' }}
                  >
                    {subscriptionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">Aucune donnée d'abonnement</p>
            )}
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {subscriptionData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm text-slate-300">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Activity Bar */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-green-400" />
            Activité par Jour
          </h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData.slice(-7)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="date" 
                  stroke="#94a3b8" 
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  tickFormatter={(value) => value.slice(8)}
                />
                <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} name="Analyses" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Success Rate Gauge */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-400" />
            Taux de Succès
          </h3>
          <div className="flex items-center justify-center h-40">
            <div className="relative">
              <svg className="w-32 h-32" viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#334155"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#22c55e"
                  strokeWidth="3"
                  strokeDasharray={`${stats?.analyses?.success_rate || 0}, 100`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {stats?.analyses?.success_rate || 0}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-orange-400" />
            Métriques Clés
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Projets</span>
              <span className="font-bold text-white">{stats?.projects?.total || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Organisations</span>
              <span className="font-bold text-white">{stats?.organizations?.total || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Optimisations</span>
              <span className="font-bold text-white">{stats?.article_optimizer?.total || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Vérification email</span>
              <span className="font-bold text-white">{stats?.users?.verification_rate || 0}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
