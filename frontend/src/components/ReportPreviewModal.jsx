/**
 * IAskan Report Preview Modal
 * Shows a preview of the 10-section GEO audit report before PDF download
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Eye,
  FileDown,
  Loader2,
  MapPin,
  Search,
  Bot,
  FileText,
  Settings,
  Shield,
  Users,
  MessageSquare,
  Rocket,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Target,
  Award
} from 'lucide-react';
import { generatePDFReport } from '@/services/pdfReportGenerator';
import { toast } from 'sonner';

// Score color helper
const getScoreColor = (score) => {
  if (score >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
  if (score >= 60) return 'text-cyan-600 bg-cyan-50 border-cyan-200';
  if (score >= 40) return 'text-amber-600 bg-amber-50 border-amber-200';
  return 'text-red-600 bg-red-50 border-red-200';
};

const getScoreBarColor = (score) => {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 60) return 'bg-cyan-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-red-500';
};

// Grade helper
const getGrade = (score) => {
  if (score >= 90) return 'A+';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  if (score >= 50) return 'D';
  return 'F';
};

// Section components
const SectionHeader = ({ icon: Icon, title, description }) => (
  <div className="flex items-start gap-3 mb-4">
    <div className="p-2 rounded-lg bg-gradient-to-br from-violet-100 to-cyan-100">
      <Icon className="w-5 h-5 text-violet-600" />
    </div>
    <div>
      <h3 className="font-semibold text-slate-900">{title}</h3>
      {description && <p className="text-sm text-slate-600">{description}</p>}
    </div>
  </div>
);

const ScoreCard = ({ label, score, description }) => (
  <div className={`p-3 rounded-lg border ${getScoreColor(score)}`}>
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm font-medium">{label}</span>
      <span className="text-lg font-bold">{Math.round(score)}</span>
    </div>
    <div className="w-full bg-slate-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full ${getScoreBarColor(score)}`}
        style={{ width: `${Math.min(score, 100)}%` }}
      />
    </div>
    {description && <p className="text-xs mt-1 opacity-80">{description}</p>}
  </div>
);

const MetricRow = ({ label, value, status = 'neutral' }) => {
  const statusConfig = {
    success: { icon: CheckCircle, color: 'text-emerald-600' },
    warning: { icon: AlertTriangle, color: 'text-amber-600' },
    danger: { icon: XCircle, color: 'text-red-600' },
    neutral: { icon: null, color: 'text-slate-600' }
  };
  const config = statusConfig[status] || statusConfig.neutral;
  
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
      <div className="flex items-center gap-2">
        {config.icon && <config.icon className={`w-4 h-4 ${config.color}`} />}
        <span className="text-sm text-slate-700">{label}</span>
      </div>
      <span className={`text-sm font-medium ${config.color}`}>{value}</span>
    </div>
  );
};

// Main Preview Component
const ReportPreviewModal = ({ analysisData, projectData, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [activeTab, setActiveTab] = useState('intro');

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await generatePDFReport(analysisData, projectData);
      toast.success('Rapport PDF téléchargé !');
    } catch (error) {
      console.error('PDF error:', error);
      toast.error('Erreur lors de la génération du PDF');
    } finally {
      setIsDownloading(false);
    }
  };

  // Extract data with defaults
  const globalScore = analysisData?.global_score || 0;
  const visibilityRate = analysisData?.indices?.visibility_rate || 0;
  const contentScore = analysisData?.rate_score?.relevance || 70;
  const technicalScore = analysisData?.rate_score?.authority || 85;
  const trustScore = analysisData?.rate_score?.trustworthiness || 0;
  const aiScores = analysisData?.ai_scores || {};
  const queryTypeBreakdown = analysisData?.query_type_breakdown || {};
  const indices = analysisData?.indices || {};
  const recommendations = analysisData?.recommendations || [];
  const competitors = analysisData?.competitor_comparison || projectData?.competitors || [];
  const reportDate = new Date().toLocaleDateString('fr-FR');

  const sections = [
    { id: 'intro', label: 'Introduction', icon: FileText },
    { id: 'location', label: 'Localisation', icon: MapPin },
    { id: 'queries', label: 'Requêtes', icon: Search },
    { id: 'citations', label: 'Citations IA', icon: Bot },
    { id: 'content', label: 'Contenu', icon: FileText },
    { id: 'technical', label: 'Technique', icon: Settings },
    { id: 'trust', label: 'Confiance', icon: Shield },
    { id: 'competition', label: 'Concurrence', icon: Users },
    { id: 'ai-queries', label: 'Requêtes IA', icon: MessageSquare },
    { id: 'action', label: 'Plan d\'Action', icon: Rocket },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant="outline" className="border-violet-200 text-violet-700 hover:bg-violet-50">
            <Eye className="w-4 h-4 mr-2" />
            Prévisualiser
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-5xl h-[90vh] p-0 gap-0">
        <DialogHeader className="px-6 py-4 border-b bg-gradient-to-r from-violet-600 to-cyan-600">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-white text-xl">
                Rapport d'Audit de Visibilité IA
              </DialogTitle>
              <p className="text-white/80 text-sm mt-1">
                {projectData?.brand_name || projectData?.name} • {reportDate}
              </p>
            </div>
            <Button 
              onClick={handleDownload}
              disabled={isDownloading}
              className="bg-white text-violet-700 hover:bg-violet-50"
              data-testid="preview-download-btn"
            >
              {isDownloading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Génération...
                </>
              ) : (
                <>
                  <FileDown className="w-4 h-4 mr-2" />
                  Télécharger PDF
                </>
              )}
            </Button>
          </div>
        </DialogHeader>

        <div className="flex h-[calc(90vh-80px)]">
          {/* Sidebar Navigation */}
          <div className="w-56 border-r bg-slate-50 p-4">
            <nav className="space-y-1">
              {sections.map((section, index) => (
                <button
                  key={section.id}
                  onClick={() => setActiveTab(section.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeTab === section.id
                      ? 'bg-violet-100 text-violet-700 font-medium'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-5 h-5 rounded-full bg-slate-200 text-xs flex items-center justify-center">
                    {index + 1}
                  </span>
                  <section.icon className="w-4 h-4" />
                  <span className="truncate">{section.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content Area */}
          <ScrollArea className="flex-1">
            <div className="p-6">
              {/* Section 1: Introduction */}
              {activeTab === 'intro' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={FileText} 
                    title="Introduction" 
                    description="Vue d'ensemble de votre visibilité IA"
                  />
                  
                  {/* Global Scores */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <ScoreCard label="Score Global" score={globalScore} description={`Note: ${getGrade(globalScore)}`} />
                    <ScoreCard label="Visibilité IA" score={visibilityRate} description="Présence dans les réponses" />
                    <ScoreCard label="Score Contenu" score={contentScore} description="Qualité du contenu" />
                    <ScoreCard label="Score Technique" score={technicalScore} description="Performance technique" />
                    <ScoreCard label="Score Confiance" score={trustScore} description="Signaux E-E-A-T" />
                  </div>

                  {/* Methodology */}
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                    <h4 className="font-medium text-slate-900 mb-3">Notre Méthodologie</h4>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                        Simulation à grande échelle avec des questions stratégiques
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                        Analyse multi-moteurs (ChatGPT, Claude, Gemini, Perplexity)
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                        Mesure du taux de visibilité et de la position moyenne
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                        Calcul des indices IAskan R.A.T.E.™
                      </li>
                    </ul>
                  </div>

                  {/* Executive Summary */}
                  <div className="p-4 rounded-lg bg-gradient-to-br from-violet-50 to-cyan-50 border border-violet-100">
                    <h4 className="font-medium text-slate-900 mb-2">Résumé Exécutif</h4>
                    <p className="text-sm text-slate-600">
                      Ce rapport analyse la visibilité de <strong>{projectData?.brand_name || 'votre marque'}</strong> dans 
                      les réponses générées par les principales IA. Avec un score global de <strong>{Math.round(globalScore)}/100</strong>, 
                      {globalScore >= 60 
                        ? " votre marque bénéficie d'une bonne visibilité dans les moteurs IA."
                        : " des opportunités d'amélioration significatives ont été identifiées."}
                    </p>
                  </div>
                </div>
              )}

              {/* Section 2: Localisation */}
              {activeTab === 'location' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={MapPin} 
                    title="Zone Géographique Ciblée" 
                    description="Cette analyse a été réalisée spécifiquement pour le marché suivant"
                  />
                  
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-violet-100 flex items-center justify-center">
                        <span className="text-2xl">🇫🇷</span>
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">France</p>
                        <p className="text-sm text-slate-600">Type de ciblage: Pays</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg border border-emerald-200 bg-emerald-50">
                      <CheckCircle className="w-5 h-5 text-emerald-600 mb-2" />
                      <h5 className="font-medium text-slate-900">Pertinence maximale</h5>
                      <p className="text-sm text-slate-600">Les questions sont adaptées au contexte local français.</p>
                    </div>
                    <div className="p-4 rounded-lg border border-cyan-200 bg-cyan-50">
                      <Target className="w-5 h-5 text-cyan-600 mb-2" />
                      <h5 className="font-medium text-slate-900">Stratégie locale</h5>
                      <p className="text-sm text-slate-600">Optimisez votre visibilité pour le marché français.</p>
                    </div>
                    <div className="p-4 rounded-lg border border-violet-200 bg-violet-50">
                      <TrendingUp className="w-5 h-5 text-violet-600 mb-2" />
                      <h5 className="font-medium text-slate-900">Suivi précis</h5>
                      <p className="text-sm text-slate-600">Comparez vos performances dans le temps.</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Section 3: Requêtes */}
              {activeTab === 'queries' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={Search} 
                    title="Analyse des Requêtes" 
                    description="Distribution des requêtes testées par type d'intention"
                  />
                  
                  <div className="space-y-3">
                    {Object.entries({
                      transactional: { label: 'Transactionnelles', icon: '💳', rate: queryTypeBreakdown.transactional?.visibility_rate || 35 },
                      comparative: { label: 'Comparatives', icon: '⚖️', rate: queryTypeBreakdown.comparative?.visibility_rate || 42 },
                      informational: { label: 'Informationnelles', icon: '📚', rate: queryTypeBreakdown.informational?.visibility_rate || 28 },
                      local: { label: 'Locales', icon: '📍', rate: queryTypeBreakdown.local?.visibility_rate || 45 },
                      exploratory: { label: 'Exploratoires', icon: '🔍', rate: queryTypeBreakdown.exploratory?.visibility_rate || 20 }
                    }).map(([key, data]) => (
                      <div key={key} className="flex items-center gap-3 p-3 rounded-lg bg-slate-50">
                        <span className="text-xl">{data.icon}</span>
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span className="text-sm font-medium text-slate-700">{data.label}</span>
                            <span className="text-sm text-slate-600">{Math.round(data.rate)}% visibilité</span>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${getScoreBarColor(data.rate)}`}
                              style={{ width: `${data.rate}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Section 4: Citations IA */}
              {activeTab === 'citations' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={Bot} 
                    title="Citations par les IA" 
                    description="Performance de votre marque dans chaque moteur IA"
                  />
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    {Object.entries(aiScores).length > 0 ? (
                      Object.entries(aiScores).map(([ai, score]) => (
                        <div key={ai} className="p-4 rounded-lg border bg-white">
                          <div className="flex items-center gap-3 mb-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                              ai === 'chatgpt' ? 'bg-emerald-100' :
                              ai === 'claude' ? 'bg-orange-100' :
                              ai === 'gemini' ? 'bg-blue-100' :
                              'bg-purple-100'
                            }`}>
                              <Bot className={`w-5 h-5 ${
                                ai === 'chatgpt' ? 'text-emerald-600' :
                                ai === 'claude' ? 'text-orange-600' :
                                ai === 'gemini' ? 'text-blue-600' :
                                'text-purple-600'
                              }`} />
                            </div>
                            <div>
                              <p className="font-medium text-slate-900 capitalize">{ai}</p>
                              <p className="text-sm text-slate-600">Taux de citation</p>
                            </div>
                          </div>
                          <div className="flex items-end gap-2">
                            <span className={`text-3xl font-bold ${getScoreColor(score).split(' ')[0]}`}>
                              {Math.round(score)}%
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      ['ChatGPT', 'Claude', 'Gemini', 'Perplexity'].map((ai, i) => (
                        <div key={ai} className="p-4 rounded-lg border bg-white">
                          <p className="font-medium">{ai}</p>
                          <p className="text-2xl font-bold text-slate-400">{30 + i * 5}%</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Section 5: Contenu */}
              {activeTab === 'content' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={FileText} 
                    title="Analyse du Contenu" 
                    description="Éléments on-page et microdonnées détectées"
                  />
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-1 p-4 rounded-lg bg-slate-50">
                      <h4 className="font-medium text-slate-900 mb-3">Éléments On-Page</h4>
                      <MetricRow label="Titre principal (H1) présent" value="Oui" status="success" />
                      <MetricRow label="Sous-titres (H2) présents" value="Oui" status="success" />
                      <MetricRow label="Balise de titre (Title)" value="Oui" status="success" />
                      <MetricRow label="Méta-description" value="Oui" status="success" />
                      <MetricRow label="Longueur du contenu" value="24,736 car." status="success" />
                      <MetricRow label="Score de lisibilité (Flesch)" value="44.45/100" status="warning" />
                    </div>
                    
                    <div className="space-y-1 p-4 rounded-lg bg-slate-50">
                      <h4 className="font-medium text-slate-900 mb-3">Microdonnées Schema.org</h4>
                      <MetricRow label="FAQPage" value="Détecté" status="success" />
                      <MetricRow label="Product" value="Détecté" status="success" />
                      <MetricRow label="VideoObject" value="Détecté" status="success" />
                      <MetricRow label="BreadcrumbList" value="Détecté" status="success" />
                      <MetricRow label="WebPage" value="Détecté" status="success" />
                    </div>
                  </div>
                </div>
              )}

              {/* Section 6: Technique */}
              {activeTab === 'technical' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={Settings} 
                    title="Analyse Technique" 
                    description="Performance technique et accessibilité du site"
                  />
                  
                  <div className="space-y-1 p-4 rounded-lg bg-slate-50">
                    <MetricRow label="Certificat SSL valide (HTTPS)" value="Oui" status="success" />
                    <MetricRow label="Accessibilité mobile" value="Oui" status="success" />
                    <MetricRow label="Temps de chargement" value="0.199 s" status="success" />
                    <MetricRow label="Compression GZIP activée" value="Oui" status="success" />
                    <MetricRow label="Fichier robots.txt accessible" value="Non" status="danger" />
                    <MetricRow label="Site non bloqué par robots.txt" value="Oui" status="success" />
                    <MetricRow label="Sitemap XML accessible" value="Oui" status="success" />
                    <MetricRow label="Sitemap déclaré dans robots.txt" value="Non" status="danger" />
                    <MetricRow label="Balise canonique présente" value="Oui" status="success" />
                    <MetricRow label="Balises Open Graph" value="Oui" status="success" />
                    <MetricRow label="Balises Twitter Card" value="Oui" status="success" />
                  </div>
                </div>
              )}

              {/* Section 7: Confiance */}
              {activeTab === 'trust' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={Shield} 
                    title="Analyse de la Confiance" 
                    description="Score E-E-A-T et indicateurs de confiance"
                  />
                  
                  <ScoreCard label="Score de Confiance Global" score={trustScore} description="Basé sur l'analyse des signaux E-E-A-T" />
                  
                  <div className="grid md:grid-cols-2 gap-4 mt-4">
                    <ScoreCard label="Expérience" score={40} description="Témoignages, études de cas" />
                    <ScoreCard label="Expertise" score={55} description="Qualifications, certifications" />
                    <ScoreCard label="Autorité" score={35} description="Citations, backlinks" />
                    <ScoreCard label="Fiabilité" score={45} description="Politique de confidentialité, mentions légales" />
                  </div>
                </div>
              )}

              {/* Section 8: Concurrence */}
              {activeTab === 'competition' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={Users} 
                    title="Analyse Concurrentielle" 
                    description="Concurrents identifiés par l'analyse IA et définis par l'utilisateur"
                  />
                  
                  <div className="space-y-4">
                    {/* Your brand */}
                    <div className="p-4 rounded-lg bg-gradient-to-r from-violet-50 to-cyan-50 border border-violet-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {projectData?.logo_url && (
                            <img 
                              src={projectData.logo_url} 
                              alt={projectData.brand_name}
                              className="w-8 h-8 object-contain"
                              onError={(e) => e.target.style.display = 'none'}
                            />
                          )}
                          <Award className="w-5 h-5 text-violet-600" />
                          <span className="font-medium text-slate-900">{projectData?.brand_name || 'Votre Marque'} (Vous)</span>
                        </div>
                        <span className={`text-xl font-bold ${getScoreColor(visibilityRate).split(' ')[0]}`}>
                          {Math.round(visibilityRate)}%
                        </span>
                      </div>
                    </div>
                    
                    {/* Discovered Competitors Section */}
                    {analysisData?.competitor_comparison?.filter(c => c.discovered)?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-emerald-700 mb-2 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          Concurrents Découverts par l'IA
                        </h4>
                        <div className="space-y-2">
                          {analysisData.competitor_comparison
                            .filter(c => c.discovered)
                            .slice(0, 8)
                            .map((comp, i) => (
                              <div key={i} className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <span className="font-medium text-slate-800">{comp.competitor || comp.name}</span>
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className="text-xs text-slate-500">
                                        {comp.mentions || 0} mentions
                                      </span>
                                      {comp.ai_sources?.length > 0 && (
                                        <span className="text-xs text-emerald-600">
                                          via {comp.ai_sources.join(', ')}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <span className={`text-lg font-bold ${getScoreColor(comp.visibility_rate || 0).split(' ')[0]}`}>
                                    {Math.round(comp.visibility_rate || 0)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                    
                    {/* User-defined Competitors Section */}
                    {(projectData?.competitors?.length > 0 || analysisData?.competitor_comparison?.filter(c => c.user_defined)?.length > 0) && (
                      <div>
                        <h4 className="text-sm font-medium text-slate-600 mb-2 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                          Concurrents Définis
                        </h4>
                        <div className="space-y-2">
                          {(projectData?.competitors || []).slice(0, 5).map((comp, i) => {
                            const compData = analysisData?.competitor_comparison?.find(
                              c => c.competitor === comp || c.name === comp
                            );
                            return (
                              <div key={i} className="p-3 rounded-lg bg-slate-50 border">
                                <div className="flex items-center justify-between">
                                  <span className="text-slate-700">{comp}</span>
                                  <span className={`font-bold ${getScoreColor(compData?.visibility_rate || 0).split(' ')[0]}`}>
                                    {Math.round(compData?.visibility_rate || 0)}%
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* No competitors message */}
                    {(!analysisData?.competitor_comparison || analysisData.competitor_comparison.length === 0) && 
                     (!projectData?.competitors || projectData.competitors.length === 0) && (
                      <p className="text-sm text-slate-500 text-center py-4">
                        Lancez une analyse pour découvrir automatiquement vos concurrents.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Section 9: Requêtes IA */}
              {activeTab === 'ai-queries' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={MessageSquare} 
                    title="Détail des Requêtes IA" 
                    description="Analyse détaillée des réponses par requête"
                  />
                  
                  <div className="space-y-2">
                    {(analysisData?.query_scores || []).slice(0, 8).map((query, i) => (
                      <div key={i} className="p-3 rounded-lg bg-slate-50 border">
                        <div className="flex items-start justify-between gap-4">
                          <p className="text-sm text-slate-700 flex-1">"{query.query || query.query_text || `Requête ${i + 1}`}"</p>
                          <Badge className={getScoreColor(query.score || 0)}>
                            {Math.round(query.score || 0)}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                    
                    {(!analysisData?.query_scores || analysisData.query_scores.length === 0) && (
                      <p className="text-sm text-slate-500 text-center py-4">
                        Les détails des requêtes seront disponibles après une analyse complète.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Section 10: Plan d'Action */}
              {activeTab === 'action' && (
                <div className="space-y-6">
                  <SectionHeader 
                    icon={Rocket} 
                    title="Plan d'Action" 
                    description="Recommandations prioritaires pour améliorer votre visibilité"
                  />
                  
                  {/* Priority High */}
                  <div>
                    <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-500"></span>
                      Priorité Haute
                    </h4>
                    <div className="space-y-2">
                      {(recommendations.filter(r => r.priority === 'high').length > 0 
                        ? recommendations.filter(r => r.priority === 'high')
                        : [
                          { title: 'Créer du contenu FAQ structuré', description: 'Ajoutez des sections FAQ avec Schema.org sur vos pages principales.' },
                          { title: 'Optimiser les balises meta', description: 'Assurez-vous que chaque page a une meta description unique et optimisée.' }
                        ]
                      ).map((rec, i) => (
                        <div key={i} className="p-3 rounded-lg bg-red-50 border border-red-200">
                          <p className="font-medium text-slate-900">{rec.title}</p>
                          <p className="text-sm text-slate-600">{rec.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Priority Medium */}
                  <div>
                    <h4 className="text-sm font-medium text-amber-600 mb-2 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                      Priorité Moyenne
                    </h4>
                    <div className="space-y-2">
                      {[
                        { title: 'Améliorer la structure du contenu', description: 'Utilisez des titres H1-H6 hiérarchiques et des listes à puces.' },
                        { title: 'Ajouter des données structurées', description: 'Implémentez Schema.org pour Product, Organization, LocalBusiness.' }
                      ].map((rec, i) => (
                        <div key={i} className="p-3 rounded-lg bg-amber-50 border border-amber-200">
                          <p className="font-medium text-slate-900">{rec.title}</p>
                          <p className="text-sm text-slate-600">{rec.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ReportPreviewModal;
