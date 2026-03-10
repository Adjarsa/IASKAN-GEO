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
  RefreshCw
} from 'lucide-react';

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
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-slate-400">Liste des analyses à venir...</p>
          </div>
        )}
      </div>
    </div>
  );
}
