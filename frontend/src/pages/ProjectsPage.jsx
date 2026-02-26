import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Plus,
  FolderKanban,
  Globe,
  Tag,
  Users,
  Trash2,
  Edit,
  MoreVertical
} from "lucide-react";

const ProjectsPage = () => {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  
  const [formData, setFormData] = useState({
    name: "",
    website_url: "",
    brand_name: "",
    competitors: "",
    keywords: ""
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`, { withCredentials: true });
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error("Projects error:", error);
      toast.error("Erreur lors du chargement des projets");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const payload = {
        name: formData.name,
        website_url: formData.website_url,
        brand_name: formData.brand_name,
        competitors: formData.competitors.split(",").map(c => c.trim()).filter(c => c),
        keywords: formData.keywords.split(",").map(k => k.trim()).filter(k => k)
      };

      if (editingProject) {
        await axios.put(`${API}/projects/${editingProject.project_id}`, payload, {
          withCredentials: true
        });
        toast.success("Projet mis à jour !");
      } else {
        await axios.post(`${API}/projects`, payload, { withCredentials: true });
        toast.success("Projet créé !");
      }

      setDialogOpen(false);
      resetForm();
      fetchProjects();
    } catch (error) {
      console.error("Save error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (project) => {
    setEditingProject(project);
    setFormData({
      name: project.name,
      website_url: project.website_url,
      brand_name: project.brand_name,
      competitors: project.competitors?.join(", ") || "",
      keywords: project.keywords?.join(", ") || ""
    });
    setDialogOpen(true);
  };

  const handleDelete = async (projectId) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce projet ?")) {
      return;
    }

    try {
      await axios.delete(`${API}/projects/${projectId}`, { withCredentials: true });
      toast.success("Projet supprimé");
      fetchProjects();
    } catch (error) {
      console.error("Delete error:", error);
      toast.error("Erreur lors de la suppression");
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      website_url: "",
      brand_name: "",
      competitors: "",
      keywords: ""
    });
    setEditingProject(null);
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
      <div className="space-y-8" data-testid="projects-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Projets</h1>
            <p className="text-slate-700">
              Gérez vos projets et marques à analyser
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700" data-testid="create-project-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nouveau Projet
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>
                  {editingProject ? "Modifier le projet" : "Créer un projet"}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nom du projet</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Mon projet GEO"
                    required
                    data-testid="project-name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="brand_name">Nom de la marque</Label>
                  <Input
                    id="brand_name"
                    value={formData.brand_name}
                    onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                    placeholder="Ma Marque"
                    required
                    data-testid="brand-name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="website_url">URL du site web</Label>
                  <Input
                    id="website_url"
                    type="url"
                    value={formData.website_url}
                    onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                    placeholder="https://example.com"
                    data-testid="website-url-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="keywords">Mots-clés (séparés par des virgules)</Label>
                  <Input
                    id="keywords"
                    value={formData.keywords}
                    onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                    placeholder="SEO, marketing digital, GEO"
                    data-testid="keywords-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="competitors">Concurrents (séparés par des virgules)</Label>
                  <Input
                    id="competitors"
                    value={formData.competitors}
                    onChange={(e) => setFormData({ ...formData, competitors: e.target.value })}
                    placeholder="Concurrent1, Concurrent2"
                    data-testid="competitors-input"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Annuler
                  </Button>
                  <Button type="submit" disabled={saving} data-testid="save-project-btn">
                    {saving ? "Enregistrement..." : (editingProject ? "Mettre à jour" : "Créer")}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Projects Grid */}
        {projects.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Card key={project.project_id} className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  {project.logo_url ? (
                    <img 
                      src={project.logo_url} 
                      alt={project.name}
                      className="w-12 h-12 rounded-xl object-contain bg-white border border-slate-200 p-1"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div 
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br from-violet-100 to-cyan-100 items-center justify-center ${project.logo_url ? 'hidden' : 'flex'}`}
                  >
                    <FolderKanban className="w-6 h-6 text-violet-600" />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEdit(project)}
                      data-testid={`edit-project-${project.project_id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => handleDelete(project.project_id)}
                      data-testid={`delete-project-${project.project_id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-slate-900 mb-1">{project.name}</h3>
                <p className="text-violet-600 text-sm mb-4">{project.brand_name}</p>

                <div className="space-y-2 text-sm">
                  {project.website_url && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Globe className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate">
                        {(() => {
                          const url = project.website_url.replace(/^https?:\/\/(www\.)?/, '').split('?')[0];
                          const parts = url.split('/').filter(Boolean);
                          return parts.length > 2 ? `${parts[0]}/${parts[1]}/...` : url.replace(/\/$/, '');
                        })()}
                      </span>
                    </div>
                  )}
                  {project.keywords?.length > 0 && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Tag className="w-4 h-4" />
                      <span className="truncate">{project.keywords.slice(0, 3).join(", ")}</span>
                    </div>
                  )}
                  {project.competitors?.length > 0 && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Users className="w-4 h-4" />
                      <span>{project.competitors.length} concurrent(s)</span>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center bg-white border-slate-100">
            <FolderKanban className="w-16 h-16 text-slate-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Aucun projet</h3>
            <p className="text-slate-600 mb-6">
              Créez votre premier projet pour commencer à analyser votre visibilité GEO
            </p>
            <Button className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700" onClick={() => setDialogOpen(true)} data-testid="empty-create-btn">
              <Plus className="w-4 h-4 mr-2" />
              Créer un projet
            </Button>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ProjectsPage;
