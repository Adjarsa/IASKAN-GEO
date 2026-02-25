import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Wand2,
  FileText,
  RefreshCw,
  Sparkles,
  Copy,
  Check,
  Download,
  List,
  HelpCircle,
  BookOpen,
  Table2,
  Shield,
  Award,
  Lightbulb,
  Loader2,
  ChevronRight,
  Zap,
  Target,
  BarChart3
} from "lucide-react";

const ContentGeneratorPage = () => {
  const { currentProject } = useAuth();
  
  // Generator state
  const [generatorType, setGeneratorType] = useState("article");
  const [topic, setTopic] = useState("");
  const [keywords, setKeywords] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState(null);
  const [copied, setCopied] = useState(false);
  
  // Reformulator state
  const [originalContent, setOriginalContent] = useState("");
  const [reformulating, setReformulating] = useState(false);
  const [optimizedContent, setOptimizedContent] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  const contentTypes = [
    { id: "article", label: "Article GEO", icon: FileText, desc: "Article optimise pour les LLMs" },
    { id: "faq", label: "FAQ Optimisee", icon: HelpCircle, desc: "Questions/Reponses structurees" },
    { id: "entity", label: "Fiche Entite", icon: Shield, desc: "Renforcer la reconnaissance IA" },
    { id: "guide", label: "Guide Definitif", icon: BookOpen, desc: "Contenu pilier exhaustif" },
    { id: "comparison", label: "Comparatif", icon: Table2, desc: "Tableau structure" }
  ];

  const generateContent = async () => {
    if (!topic.trim()) {
      toast.error("Veuillez entrer un sujet");
      return;
    }

    setGenerating(true);
    setGeneratedContent(null);

    try {
      const response = await axios.post(
        `${API}/content/generate`,
        {
          project_id: currentProject?.project_id,
          content_type: generatorType,
          topic: topic,
          keywords: keywords.split(",").map(k => k.trim()).filter(k => k),
          brand_name: currentProject?.brand_name || ""
        },
        { withCredentials: true, timeout: 120000 }
      );
      
      setGeneratedContent(response.data);
      toast.success("Contenu genere avec succes !");
    } catch (error) {
      console.error("Generation error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de la generation");
    } finally {
      setGenerating(false);
    }
  };

  const reformulateContent = async () => {
    if (!originalContent.trim()) {
      toast.error("Veuillez coller votre contenu a optimiser");
      return;
    }

    setReformulating(true);
    setOptimizedContent(null);
    setSuggestions([]);

    try {
      const response = await axios.post(
        `${API}/content/reformulate`,
        {
          project_id: currentProject?.project_id,
          content: originalContent,
          brand_name: currentProject?.brand_name || ""
        },
        { withCredentials: true, timeout: 120000 }
      );
      
      setOptimizedContent(response.data.optimized_content);
      setSuggestions(response.data.suggestions || []);
      toast.success("Contenu optimise !");
    } catch (error) {
      console.error("Reformulation error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de l'optimisation");
    } finally {
      setReformulating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copie dans le presse-papiers !");
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAsMarkdown = (content, filename) => {
    const blob = new Blob([content], { type: "text/markdown" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="content-generator-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Wand2 className="w-8 h-8 text-violet-600" />
              <h1 className="text-3xl font-bold text-slate-900">Generation de Contenu GEO</h1>
            </div>
            <p className="text-slate-600 mt-1">
              Creez et optimisez du contenu pour maximiser votre visibilite dans les reponses IA
            </p>
          </div>
          <Badge className="bg-gradient-to-r from-violet-600 to-cyan-600 text-white border-0 px-4 py-2">
            <Sparkles className="w-4 h-4 mr-2" />
            Powered by AI
          </Badge>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="generate" className="space-y-6">
          <TabsList className="bg-slate-100 p-1">
            <TabsTrigger value="generate" className="data-[state=active]:bg-white">
              <Wand2 className="w-4 h-4 mr-2" />
              Generer
            </TabsTrigger>
            <TabsTrigger value="optimize" className="data-[state=active]:bg-white">
              <RefreshCw className="w-4 h-4 mr-2" />
              Optimiser
            </TabsTrigger>
            <TabsTrigger value="formats" className="data-[state=active]:bg-white">
              <List className="w-4 h-4 mr-2" />
              Formats GEO
            </TabsTrigger>
          </TabsList>

          {/* Generate Tab */}
          <TabsContent value="generate" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Generator Form */}
              <Card className="lg:col-span-1 p-6 bg-white border-slate-100">
                <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-violet-600" />
                  Configuration
                </h3>

                {/* Content Type Selection */}
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 mb-2 block">
                      Type de contenu
                    </label>
                    <Select value={generatorType} onValueChange={setGeneratorType}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selectionnez un type" />
                      </SelectTrigger>
                      <SelectContent>
                        {contentTypes.map((type) => (
                          <SelectItem key={type.id} value={type.id}>
                            <div className="flex items-center gap-2">
                              <type.icon className="w-4 h-4" />
                              {type.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-slate-500 mt-1">
                      {contentTypes.find(t => t.id === generatorType)?.desc}
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-slate-700 mb-2 block">
                      Sujet principal *
                    </label>
                    <Input
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="Ex: Les avantages du CRM pour PME"
                      data-testid="topic-input"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-slate-700 mb-2 block">
                      Mots-cles (separes par virgule)
                    </label>
                    <Input
                      value={keywords}
                      onChange={(e) => setKeywords(e.target.value)}
                      placeholder="CRM, PME, gestion client, productivite"
                      data-testid="keywords-input"
                    />
                  </div>

                  {currentProject && (
                    <div className="p-3 rounded-lg bg-violet-50 border border-violet-100">
                      <p className="text-xs text-slate-600">Marque ciblee:</p>
                      <p className="text-sm font-medium text-violet-700">{currentProject.brand_name}</p>
                    </div>
                  )}

                  <Button
                    onClick={generateContent}
                    disabled={generating || !topic.trim()}
                    className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
                    data-testid="generate-btn"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generation en cours...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generer le contenu
                      </>
                    )}
                  </Button>
                </div>
              </Card>

              {/* Generated Content */}
              <Card className="lg:col-span-2 p-6 bg-white border-slate-100">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-cyan-600" />
                    Contenu Genere
                  </h3>
                  {generatedContent && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(generatedContent.content)}
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadAsMarkdown(generatedContent.content, `geo-${generatorType}-${Date.now()}`)}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>

                {generating ? (
                  <div className="flex flex-col items-center justify-center h-96">
                    <div className="relative w-20 h-20 mb-4">
                      <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-30"></div>
                      <div className="absolute inset-2 rounded-full bg-white flex items-center justify-center">
                        <Wand2 className="w-8 h-8 text-violet-600 animate-pulse" />
                      </div>
                      <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-600 animate-spin"></div>
                    </div>
                    <p className="text-slate-600">L'IA redige votre contenu optimise GEO...</p>
                    <p className="text-xs text-slate-500 mt-2">Cela peut prendre jusqu'a 2 minutes</p>
                  </div>
                ) : generatedContent ? (
                  <div className="space-y-4">
                    {/* Meta info */}
                    <div className="flex flex-wrap gap-2">
                      <Badge className="bg-emerald-100 text-emerald-700 border-0">
                        <Zap className="w-3 h-3 mr-1" />
                        Score GEO: {generatedContent.geo_score || 85}%
                      </Badge>
                      <Badge className="bg-cyan-100 text-cyan-700 border-0">
                        {generatedContent.word_count || 0} mots
                      </Badge>
                      <Badge className="bg-violet-100 text-violet-700 border-0">
                        E-E-A-T optimise
                      </Badge>
                    </div>

                    {/* Content */}
                    <div 
                      className="prose prose-slate max-w-none p-4 rounded-lg bg-slate-50 border border-slate-200 max-h-[500px] overflow-y-auto"
                      data-testid="generated-content"
                    >
                      <pre className="whitespace-pre-wrap text-sm text-slate-800 font-sans">
                        {generatedContent.content}
                      </pre>
                    </div>

                    {/* Tips */}
                    {generatedContent.tips && generatedContent.tips.length > 0 && (
                      <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                        <h4 className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-2">
                          <Lightbulb className="w-4 h-4" />
                          Conseils d'utilisation
                        </h4>
                        <ul className="text-sm text-amber-700 space-y-1">
                          {generatedContent.tips.map((tip, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <ChevronRight className="w-3 h-3 mt-1 flex-shrink-0" />
                              {tip}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-96 text-center">
                    <Wand2 className="w-16 h-16 text-slate-300 mb-4" />
                    <h4 className="text-lg font-medium text-slate-900 mb-2">
                      Pret a creer du contenu GEO-optimise
                    </h4>
                    <p className="text-slate-600 max-w-md">
                      Selectionnez un type de contenu, entrez votre sujet, et laissez l'IA 
                      generer du contenu structure pour maximiser votre visibilite dans les reponses IA.
                    </p>
                  </div>
                )}
              </Card>
            </div>
          </TabsContent>

          {/* Optimize Tab */}
          <TabsContent value="optimize" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Original Content */}
              <Card className="p-6 bg-white border-slate-100">
                <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-slate-600" />
                  Contenu Original
                </h3>
                <Textarea
                  value={originalContent}
                  onChange={(e) => setOriginalContent(e.target.value)}
                  placeholder="Collez ici le contenu que vous souhaitez optimiser pour les moteurs IA generatifs..."
                  className="min-h-[400px] resize-none"
                  data-testid="original-content-input"
                />
                <Button
                  onClick={reformulateContent}
                  disabled={reformulating || !originalContent.trim()}
                  className="w-full mt-4 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
                  data-testid="optimize-btn"
                >
                  {reformulating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Optimisation en cours...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Optimiser pour GEO
                    </>
                  )}
                </Button>
              </Card>

              {/* Optimized Content */}
              <Card className="p-6 bg-white border-slate-100">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-emerald-600" />
                    Contenu Optimise
                  </h3>
                  {optimizedContent && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(optimizedContent)}
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  )}
                </div>

                {reformulating ? (
                  <div className="flex flex-col items-center justify-center h-[400px]">
                    <Loader2 className="w-12 h-12 text-violet-600 animate-spin mb-4" />
                    <p className="text-slate-600">Analyse et optimisation en cours...</p>
                  </div>
                ) : optimizedContent ? (
                  <div className="space-y-4">
                    <div 
                      className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 max-h-[300px] overflow-y-auto"
                      data-testid="optimized-content"
                    >
                      <pre className="whitespace-pre-wrap text-sm text-slate-800 font-sans">
                        {optimizedContent}
                      </pre>
                    </div>

                    {/* Suggestions */}
                    {suggestions.length > 0 && (
                      <div className="p-4 rounded-lg bg-violet-50 border border-violet-200">
                        <h4 className="text-sm font-medium text-violet-800 mb-3 flex items-center gap-2">
                          <Lightbulb className="w-4 h-4" />
                          Ameliorations appliquees
                        </h4>
                        <ul className="space-y-2">
                          {suggestions.map((sug, i) => (
                            <li key={i} className="text-sm text-violet-700 flex items-start gap-2">
                              <Check className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                              {sug}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-[400px] text-center">
                    <RefreshCw className="w-16 h-16 text-slate-300 mb-4" />
                    <p className="text-slate-600">
                      Collez votre contenu existant et cliquez sur "Optimiser" pour 
                      recevoir une version amelioree pour les LLMs.
                    </p>
                  </div>
                )}
              </Card>
            </div>
          </TabsContent>

          {/* Formats Tab */}
          <TabsContent value="formats" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* FAQ Format */}
              <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center mb-4">
                  <HelpCircle className="w-6 h-6 text-violet-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">FAQ Optimisee</h3>
                <p className="text-sm text-slate-600 mb-4">
                  Format question/reponse que les LLMs adorent citer. Structure ideale pour 
                  les featured snippets et les reponses directes.
                </p>
                <div className="p-3 rounded-lg bg-slate-50 text-xs text-slate-600 mb-4">
                  <p className="font-medium mb-1">Format type:</p>
                  <p>Q: Question claire et specifique?</p>
                  <p>R: Reponse concise, factuelle, avec chiffres si possible.</p>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => { setGeneratorType("faq"); }}
                >
                  Generer une FAQ
                </Button>
              </Card>

              {/* Entity Sheet */}
              <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-cyan-100 flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-cyan-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">Fiche Entite</h3>
                <p className="text-sm text-slate-600 mb-4">
                  Renforce la reconnaissance de votre marque par les IA. 
                  Informations structurees pour le Knowledge Graph.
                </p>
                <div className="p-3 rounded-lg bg-slate-50 text-xs text-slate-600 mb-4">
                  <p className="font-medium mb-1">Inclut:</p>
                  <p>- Nom, description, categorie</p>
                  <p>- Fondation, siege, dirigeants</p>
                  <p>- Produits/services cles</p>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => { setGeneratorType("entity"); }}
                >
                  Creer une fiche
                </Button>
              </Card>

              {/* Definitive Guide */}
              <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center mb-4">
                  <BookOpen className="w-6 h-6 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">Guide Definitif</h3>
                <p className="text-sm text-slate-600 mb-4">
                  Contenu pilier exhaustif qui etablit votre autorite. 
                  Les LLMs preferent citer des sources completes.
                </p>
                <div className="p-3 rounded-lg bg-slate-50 text-xs text-slate-600 mb-4">
                  <p className="font-medium mb-1">Structure:</p>
                  <p>- Introduction + sommaire</p>
                  <p>- Sections detaillees</p>
                  <p>- Conclusion + ressources</p>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => { setGeneratorType("guide"); }}
                >
                  Creer un guide
                </Button>
              </Card>

              {/* Comparison Table */}
              <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center mb-4">
                  <Table2 className="w-6 h-6 text-amber-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">Comparatif Structure</h3>
                <p className="text-sm text-slate-600 mb-4">
                  Tableaux de comparaison que les LLMs peuvent facilement parser 
                  et citer dans leurs reponses.
                </p>
                <div className="p-3 rounded-lg bg-slate-50 text-xs text-slate-600 mb-4">
                  <p className="font-medium mb-1">Ideal pour:</p>
                  <p>- Comparaison produits/services</p>
                  <p>- Avantages/inconvenients</p>
                  <p>- Criteres de choix</p>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => { setGeneratorType("comparison"); }}
                >
                  Creer un comparatif
                </Button>
              </Card>

              {/* Article GEO */}
              <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">Article GEO</h3>
                <p className="text-sm text-slate-600 mb-4">
                  Article de blog optimise E-E-A-T avec structure, 
                  donnees factuelles et signaux d'autorite.
                </p>
                <div className="p-3 rounded-lg bg-slate-50 text-xs text-slate-600 mb-4">
                  <p className="font-medium mb-1">Caracteristiques:</p>
                  <p>- Definitions claires</p>
                  <p>- Donnees chiffrees</p>
                  <p>- Citations d'experts</p>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => { setGeneratorType("article"); }}
                >
                  Creer un article
                </Button>
              </Card>

              {/* Tips Card */}
              <Card className="p-6 bg-gradient-to-br from-violet-50 to-cyan-50 border-violet-200">
                <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center mb-4 shadow-sm">
                  <Award className="w-6 h-6 text-violet-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">Criteres E-E-A-T</h3>
                <p className="text-sm text-slate-600 mb-4">
                  Tous nos contenus generes respectent les criteres valorises par les LLMs:
                </p>
                <ul className="text-sm space-y-2">
                  <li className="flex items-center gap-2 text-slate-700">
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span><strong>Experience</strong> - Exemples concrets</span>
                  </li>
                  <li className="flex items-center gap-2 text-slate-700">
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span><strong>Expertise</strong> - Donnees precises</span>
                  </li>
                  <li className="flex items-center gap-2 text-slate-700">
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span><strong>Authority</strong> - Sources citees</span>
                  </li>
                  <li className="flex items-center gap-2 text-slate-700">
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span><strong>Trust</strong> - Ton factuel</span>
                  </li>
                </ul>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default ContentGeneratorPage;
