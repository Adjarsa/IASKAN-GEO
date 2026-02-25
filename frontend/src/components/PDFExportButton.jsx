/**
 * PDF Export Button Component
 * Triggers PDF report generation for GEO audit
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FileDown, Loader2, FileText, CheckCircle } from 'lucide-react';
import { generatePDFReport } from '@/services/pdfReportGenerator';
import { toast } from 'sonner';

const PDFExportButton = ({ 
  analysisData, 
  projectData, 
  variant = 'default',
  size = 'default',
  className = '',
  disabled = false
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const handleExport = async () => {
    if (!analysisData || !projectData) {
      toast.error('Données insuffisantes pour générer le rapport');
      return;
    }

    setIsGenerating(true);
    setIsComplete(false);

    try {
      await generatePDFReport(analysisData, projectData);
      setIsComplete(true);
      toast.success('Rapport PDF téléchargé avec succès !');
      
      // Reset complete state after 3 seconds
      setTimeout(() => setIsComplete(false), 3000);
    } catch (error) {
      console.error('PDF generation error:', error);
      toast.error('Erreur lors de la génération du PDF');
    } finally {
      setIsGenerating(false);
    }
  };

  const getIcon = () => {
    if (isGenerating) return <Loader2 className="h-4 w-4 animate-spin" />;
    if (isComplete) return <CheckCircle className="h-4 w-4 text-green-500" />;
    return <FileDown className="h-4 w-4" />;
  };

  const getText = () => {
    if (isGenerating) return 'Génération...';
    if (isComplete) return 'Téléchargé !';
    return 'Exporter PDF';
  };

  return (
    <Button
      onClick={handleExport}
      variant={variant}
      size={size}
      className={className}
      disabled={disabled || isGenerating || !analysisData}
      data-testid="pdf-export-button"
    >
      {getIcon()}
      <span className="ml-2">{getText()}</span>
    </Button>
  );
};

/**
 * Compact PDF Export Button for use in cards/tables
 */
export const PDFExportIconButton = ({ 
  analysisData, 
  projectData,
  className = ''
}) => {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleExport = async () => {
    if (!analysisData || !projectData) {
      toast.error('Données insuffisantes');
      return;
    }

    setIsGenerating(true);

    try {
      await generatePDFReport(analysisData, projectData);
      toast.success('Rapport téléchargé !');
    } catch (error) {
      toast.error('Erreur de génération');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Button
      onClick={handleExport}
      variant="ghost"
      size="icon"
      className={className}
      disabled={isGenerating || !analysisData}
      title="Télécharger le rapport PDF"
      data-testid="pdf-export-icon-button"
    >
      {isGenerating ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <FileText className="h-4 w-4" />
      )}
    </Button>
  );
};

/**
 * Full-featured PDF Export Card
 */
export const PDFExportCard = ({ 
  analysisData, 
  projectData 
}) => {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleExport = async () => {
    if (!analysisData || !projectData) {
      toast.error('Veuillez d\'abord lancer une analyse');
      return;
    }

    setIsGenerating(true);

    try {
      await generatePDFReport(analysisData, projectData);
      toast.success('Rapport PDF téléchargé avec succès !');
    } catch (error) {
      console.error('PDF generation error:', error);
      toast.error('Erreur lors de la génération du PDF');
    } finally {
      setIsGenerating(false);
    }
  };

  const hasData = analysisData && analysisData.status === 'completed';

  return (
    <div 
      className="bg-gradient-to-br from-violet-50 to-cyan-50 border border-violet-100 rounded-xl p-6"
      data-testid="pdf-export-card"
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-white rounded-lg shadow-sm">
          <FileText className="h-6 w-6 text-violet-600" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-800 mb-1">
            Rapport d'Audit PDF
          </h3>
          <p className="text-sm text-slate-600 mb-4">
            Générez un rapport professionnel complet avec toutes les analyses, 
            scores et recommandations au format PDF.
          </p>
          
          {/* Report sections preview */}
          <div className="flex flex-wrap gap-2 mb-4">
            {[
              'Introduction',
              'Localisation', 
              'Requêtes',
              'Citations IA',
              'Contenu',
              'Technique',
              'Confiance',
              'Concurrence',
              'Requêtes IA',
              'Plan d\'Action'
            ].map((section, i) => (
              <span 
                key={i}
                className="text-xs px-2 py-1 bg-white/70 rounded-full text-slate-600 border border-slate-200"
              >
                {section}
              </span>
            ))}
          </div>

          <Button
            onClick={handleExport}
            disabled={!hasData || isGenerating}
            className="bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 text-white"
            data-testid="pdf-export-card-button"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Génération en cours...
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4 mr-2" />
                Télécharger le rapport PDF
              </>
            )}
          </Button>

          {!hasData && (
            <p className="text-xs text-amber-600 mt-2">
              Lancez une analyse pour générer le rapport
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFExportButton;
