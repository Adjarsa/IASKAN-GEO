import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Logo from "@/components/Logo";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Plus,
  FolderKanban,
  Globe,
  Tag,
  Users,
  ArrowRight,
  ChevronDown,
  Settings,
  LogOut,
  CreditCard,
  Sparkles
} from "lucide-react";

const ProjectSelectorPage = () => {
  const { user, logout, selectProject } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  
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

      const response = await axios.post(`${API}/projects`, payload, { withCredentials: true });
      toast.success("Projet créé !");
      setDialogOpen(false);
      resetForm();
      
      // Automatically select the new project
      selectProject(response.data.project);
      navigate("/dashboard");
    } catch (error) {
      console.error("Save error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  const handleSelectProject = (project) => {
    selectProject(project);
    navigate("/dashboard");
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const resetForm = () => {
    setFormData({
      name: "",
      website_url: "",
      brand_name: "",
      competitors: "",
      keywords: ""
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex items-center justify-center">
        <div className="spinner w-12 h-12" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <header className="border-b border-slate-100 bg-white/80 backdrop-blur-lg">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Logo />
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-3" data-testid="user-menu">
                <Avatar className="w-8 h-8">
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback className="bg-gradient-to-br from-violet-500 to-cyan-500 text-white">
                    {user?.name?.charAt(0) || "U"}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden md:block text-slate-700">{user?.name}</span>
                <ChevronDown className="w-4 h-4 text-slate-600" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-3 py-2">
                <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                <p className="text-xs text-slate-600">{user?.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate("/settings")}>
                <Settings className="w-4 h-4 mr-2" />
                Paramètres
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/pricing")}>
                <CreditCard className="w-4 h-4 mr-2" />
                Abonnement
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                <LogOut className="w-4 h-4 mr-2" />
                Déconnexion
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-slate-900 mb-3">
            Vos Projets
          </h1>
          <p className="text-slate-600">
            Sélectionnez un projet pour commencer ou créez-en un nouveau
          </p>
        </div>

        {/* Projects Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Create New Project Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card 
              className="p-6 h-full border-2 border-dashed border-slate-200 hover:border-violet-300 bg-slate-50/50 cursor-pointer transition-all hover:bg-violet-50/50 flex flex-col items-center justify-center min-h-[220px]"
              onClick={() => setDialogOpen(true)}
              data-testid="create-project-card"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center mb-4">
                <Plus className="w-8 h-8 text-violet-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-1">Nouveau Projet</h3>
              <p className="text-sm text-slate-600 text-center">Créez un projet pour analyser une marque</p>
            </Card>
          </motion.div>

          {/* Existing Projects */}
          {projects.map((project, index) => (
            <motion.div
              key={project.project_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: (index + 1) * 0.1 }}
            >
              <Card 
                className="p-6 h-full bg-white border-slate-100 hover:border-violet-300 cursor-pointer transition-all hover:shadow-lg hover:shadow-violet-500/10 min-h-[220px] flex flex-col"
                onClick={() => handleSelectProject(project)}
                data-testid={`project-card-${project.project_id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center">
                    <FolderKanban className="w-6 h-6 text-violet-600" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-300" />
                </div>

                <h3 className="text-lg font-semibold text-slate-900 mb-1">{project.name}</h3>
                <p className="text-violet-600 text-sm font-medium mb-4">{project.brand_name}</p>

                <div className="mt-auto space-y-2 text-sm">
                  {project.website_url && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Globe className="w-4 h-4" />
                      <span className="truncate">{project.website_url.replace(/https?:\/\//, '')}</span>
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
            </motion.div>
          ))}
        </div>

        {/* Empty State */}
        {projects.length === 0 && (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-violet-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              Bienvenue sur IAskan !
            </h3>
            <p className="text-slate-600 mb-6 max-w-md mx-auto">
              Créez votre premier projet pour commencer à analyser la visibilité de votre marque dans les réponses IA.
            </p>
            <Button 
              className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
              onClick={() => setDialogOpen(true)}
              data-testid="empty-create-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Créer mon premier projet
            </Button>
          </div>
        )}
      </div>

      {/* Create Project Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Créer un nouveau projet</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nom du projet *</Label>
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
              <Label htmlFor="brand_name">Nom de la marque *</Label>
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
              <Button 
                type="submit" 
                disabled={saving}
                className="bg-gradient-to-r from-violet-600 to-cyan-600"
                data-testid="save-project-btn"
              >
                {saving ? "Création..." : "Créer et continuer"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProjectSelectorPage;
