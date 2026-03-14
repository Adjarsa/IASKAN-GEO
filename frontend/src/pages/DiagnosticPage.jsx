import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function DiagnosticPage() {
  const [loading, setLoading] = useState(true);
  const [diagnosticData, setDiagnosticData] = useState(null);
  const [error, setError] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [claimResult, setClaimResult] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDiagnostic();
  }, []);

  const fetchDiagnostic = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_URL}/api/projects/debug`, {
        withCredentials: true
      });
      setDiagnosticData(response.data);
    } catch (err) {
      console.error('Diagnostic error:', err);
      if (err.response?.status === 401) {
        setError('Vous devez être connecté. Redirection vers la page de connexion...');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(err.response?.data?.detail || 'Erreur lors du diagnostic');
      }
    } finally {
      setLoading(false);
    }
  };

  const claimProject = async (projectId, projectName) => {
    try {
      setClaiming(true);
      setClaimResult(null);
      const response = await axios.post(`${API_URL}/api/projects/claim/${projectId}`, {}, {
        withCredentials: true
      });
      setClaimResult({
        success: true,
        message: `Projet "${projectName}" récupéré avec succès !`
      });
      // Refresh diagnostic data
      await fetchDiagnostic();
    } catch (err) {
      setClaimResult({
        success: false,
        message: err.response?.data?.detail || 'Erreur lors de la récupération du projet'
      });
    } finally {
      setClaiming(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300">Analyse en cours...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 max-w-md text-center">
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="mt-4 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg transition-colors"
          >
            Se connecter
          </button>
        </div>
      </div>
    );
  }

  const orphanedProjects = diagnosticData?.all_projects?.filter(p => !p.belongs_to_current_user) || [];
  const myProjects = diagnosticData?.all_projects?.filter(p => p.belongs_to_current_user) || [];

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Diagnostic des Projets</h1>
        <p className="text-slate-400 mb-8">Outil pour identifier et corriger les problèmes de visibilité des projets</p>

        {/* Session Info */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            Votre Session
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-slate-400 text-sm">Email</p>
              <p className="text-white font-mono">{diagnosticData?.current_session?.email}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">User ID (session)</p>
              <p className="text-white font-mono text-sm">{diagnosticData?.current_session?.user_id}</p>
            </div>
          </div>
        </div>

        {/* Database User Info */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${diagnosticData?.database_user?.id_matches_session ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
            Utilisateur en Base de Données
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-slate-400 text-sm">Existe en base</p>
              <p className={`font-semibold ${diagnosticData?.database_user?.exists ? 'text-green-400' : 'text-red-400'}`}>
                {diagnosticData?.database_user?.exists ? 'Oui' : 'Non'}
              </p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">User ID (base)</p>
              <p className="text-white font-mono text-sm">{diagnosticData?.database_user?.user_id || 'N/A'}</p>
            </div>
            <div className="md:col-span-2">
              <p className="text-slate-400 text-sm">IDs correspondent</p>
              <p className={`font-semibold ${diagnosticData?.database_user?.id_matches_session ? 'text-green-400' : 'text-red-400'}`}>
                {diagnosticData?.database_user?.id_matches_session ? '✓ Oui - Tout est normal' : '✗ Non - Problème détecté !'}
              </p>
            </div>
          </div>
        </div>

        {/* Claim Result */}
        {claimResult && (
          <div className={`rounded-xl p-4 mb-6 ${claimResult.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
            <p className={claimResult.success ? 'text-green-400' : 'text-red-400'}>
              {claimResult.message}
            </p>
          </div>
        )}

        {/* Orphaned Projects */}
        {orphanedProjects.length > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">
              ⚠️ Projets non assignés à votre compte ({orphanedProjects.length})
            </h2>
            <p className="text-slate-300 mb-4">
              Ces projets existent mais ne sont pas liés à votre compte actuel. Cliquez sur "Récupérer" pour les ajouter à votre compte.
            </p>
            <div className="space-y-3">
              {orphanedProjects.map(project => (
                <div key={project.project_id} className="bg-slate-800 rounded-lg p-4 flex items-center justify-between">
                  <div>
                    <p className="text-white font-semibold">{project.name}</p>
                    <p className="text-slate-400 text-sm font-mono">
                      ID: {project.project_id}
                    </p>
                    <p className="text-slate-500 text-xs font-mono">
                      Propriétaire actuel: {project.user_id}
                    </p>
                  </div>
                  <button
                    onClick={() => claimProject(project.project_id, project.name)}
                    disabled={claiming}
                    className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 disabled:bg-yellow-500/50 text-black font-semibold rounded-lg transition-colors"
                  >
                    {claiming ? 'En cours...' : 'Récupérer'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* My Projects */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span className="w-3 h-3 bg-violet-500 rounded-full"></span>
            Vos Projets ({myProjects.length})
          </h2>
          {myProjects.length > 0 ? (
            <div className="space-y-3">
              {myProjects.map(project => (
                <div key={project.project_id} className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-white font-semibold">{project.name}</p>
                  <p className="text-slate-400 text-sm font-mono">ID: {project.project_id}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400">Aucun projet assigné à votre compte.</p>
          )}
        </div>

        {/* Summary */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4">Résumé</h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <p className="text-3xl font-bold text-violet-400">{diagnosticData?.projects_summary?.total_in_database || 0}</p>
              <p className="text-slate-400 text-sm">Total projets</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <p className="text-3xl font-bold text-green-400">{myProjects.length}</p>
              <p className="text-slate-400 text-sm">Vos projets</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <p className="text-3xl font-bold text-yellow-400">{orphanedProjects.length}</p>
              <p className="text-slate-400 text-sm">À récupérer</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex gap-4">
          <button
            onClick={() => navigate('/projects')}
            className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-lg transition-colors"
          >
            Retour aux projets
          </button>
          <button
            onClick={fetchDiagnostic}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition-colors"
          >
            Rafraîchir
          </button>
        </div>
      </div>
    </div>
  );
}
