import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Building2, 
  Users, 
  Plus, 
  Settings, 
  Mail,
  Loader2,
  ChevronRight,
  Crown,
  UserPlus,
  Trash2,
  Edit2,
  Check,
  X
} from 'lucide-react';
import DashboardLayout from '@/components/layout/DashboardLayout';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Role badge component
const RoleBadge = ({ role }) => {
  const roleConfig = {
    owner: { label: 'Propriétaire', color: 'bg-violet-500/20 text-violet-400' },
    admin: { label: 'Admin', color: 'bg-cyan-500/20 text-cyan-400' },
    member: { label: 'Membre', color: 'bg-slate-500/20 text-slate-400' },
    viewer: { label: 'Lecteur', color: 'bg-slate-600/20 text-slate-500' }
  };
  
  const config = roleConfig[role] || roleConfig.member;
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${config.color}`}>
      {config.label}
    </span>
  );
};

export default function OrganizationsPage() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/organizations`, {
        withCredentials: true
      });
      setOrganizations(response.data.organizations);
      if (response.data.organizations.length > 0 && !selectedOrg) {
        setSelectedOrg(response.data.organizations[0]);
      }
    } catch (err) {
      console.error('Error fetching organizations:', err);
    } finally {
      setLoading(false);
    }
  };

  const createOrganization = async () => {
    if (!newOrgName.trim()) return;
    
    setProcessing(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/organizations`,
        { name: newOrgName },
        { withCredentials: true }
      );
      setOrganizations([...organizations, response.data.organization]);
      setSelectedOrg(response.data.organization);
      setShowCreateModal(false);
      setNewOrgName('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création');
    } finally {
      setProcessing(false);
    }
  };

  const inviteMember = async () => {
    if (!inviteEmail.trim() || !selectedOrg) return;
    
    setProcessing(true);
    try {
      await axios.post(
        `${BACKEND_URL}/api/organizations/${selectedOrg.organization_id}/invite`,
        { email: inviteEmail, role: inviteRole },
        { withCredentials: true }
      );
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('member');
      // Refresh org data
      fetchOrganizations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'invitation');
    } finally {
      setProcessing(false);
    }
  };

  const removeMember = async (memberId) => {
    if (!selectedOrg) return;
    
    if (!window.confirm('Êtes-vous sûr de vouloir retirer ce membre ?')) return;
    
    try {
      await axios.delete(
        `${BACKEND_URL}/api/organizations/${selectedOrg.organization_id}/members/${memberId}`,
        { withCredentials: true }
      );
      fetchOrganizations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du retrait');
    }
  };

  const updateMemberRole = async (memberId, newRole) => {
    if (!selectedOrg) return;
    
    try {
      await axios.put(
        `${BACKEND_URL}/api/organizations/${selectedOrg.organization_id}/members/${memberId}/role`,
        { role: newRole },
        { withCredentials: true }
      );
      fetchOrganizations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Organisations</h1>
            <p className="text-slate-600">Gérez vos équipes et workspaces</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-500 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus className="w-4 h-4" />
            Nouvelle organisation
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
            <button onClick={() => setError(null)} className="float-right">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Content */}
        {organizations.length === 0 ? (
          <div className="text-center py-16 bg-slate-50 rounded-xl border border-slate-200">
            <Building2 className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              Aucune organisation
            </h3>
            <p className="text-slate-500 mb-6">
              Créez une organisation pour collaborer avec votre équipe
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 transition-colors"
            >
              Créer une organisation
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Organizations list */}
            <div className="space-y-3">
              {organizations.map(org => (
                <button
                  key={org.organization_id}
                  onClick={() => setSelectedOrg(org)}
                  className={`w-full text-left p-4 rounded-xl border transition-colors ${
                    selectedOrg?.organization_id === org.organization_id
                      ? 'bg-violet-50 border-violet-200'
                      : 'bg-white border-slate-200 hover:border-violet-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-lg flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-slate-900 truncate">{org.name}</p>
                      <p className="text-sm text-slate-500">
                        {org.members?.length || 0} membre{(org.members?.length || 0) > 1 ? 's' : ''}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  </div>
                </button>
              ))}
            </div>

            {/* Selected organization details */}
            {selectedOrg && (
              <div className="lg:col-span-2 space-y-6">
                {/* Org header */}
                <div className="bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-xl flex items-center justify-center">
                        <Building2 className="w-8 h-8 text-white" />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-slate-900">{selectedOrg.name}</h2>
                        <p className="text-sm text-slate-500">Créé le {new Date(selectedOrg.created_at).toLocaleDateString('fr-FR')}</p>
                      </div>
                    </div>
                    <button className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
                      <Settings className="w-5 h-5 text-slate-600" />
                    </button>
                  </div>
                  
                  {selectedOrg.website_url && (
                    <p className="text-sm text-violet-600">{selectedOrg.website_url}</p>
                  )}
                </div>

                {/* Members */}
                <div className="bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                      <Users className="w-5 h-5 text-violet-500" />
                      Membres ({selectedOrg.members?.length || 0})
                    </h3>
                    <button
                      onClick={() => setShowInviteModal(true)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-violet-50 text-violet-700 rounded-lg hover:bg-violet-100 transition-colors text-sm"
                    >
                      <UserPlus className="w-4 h-4" />
                      Inviter
                    </button>
                  </div>

                  <div className="space-y-3">
                    {selectedOrg.members?.map(member => (
                      <div 
                        key={member.user_id}
                        className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-slate-400 to-slate-500 rounded-full flex items-center justify-center">
                            <span className="text-white font-semibold">
                              {member.name?.charAt(0) || 'U'}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{member.name}</p>
                            <p className="text-sm text-slate-500">{member.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <RoleBadge role={member.role} />
                          {member.role !== 'owner' && (
                            <button
                              onClick={() => removeMember(member.user_id)}
                              className="p-1.5 hover:bg-red-100 rounded transition-colors"
                              title="Retirer"
                            >
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Create Organization Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                Nouvelle organisation
              </h3>
              <input
                type="text"
                value={newOrgName}
                onChange={(e) => setNewOrgName(e.target.value)}
                placeholder="Nom de l'organisation"
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 mb-4"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50"
                >
                  Annuler
                </button>
                <button
                  onClick={createOrganization}
                  disabled={processing || !newOrgName.trim()}
                  className="flex-1 px-4 py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 disabled:opacity-50"
                >
                  {processing ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Créer'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Invite Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                Inviter un membre
              </h3>
              <div className="space-y-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="email@exemple.com"
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Rôle
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="viewer">Lecteur</option>
                    <option value="member">Membre</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50"
                >
                  Annuler
                </button>
                <button
                  onClick={inviteMember}
                  disabled={processing || !inviteEmail.trim()}
                  className="flex-1 px-4 py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 disabled:opacity-50"
                >
                  {processing ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Inviter'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
