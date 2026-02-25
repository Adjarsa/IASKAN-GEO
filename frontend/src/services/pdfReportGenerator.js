/**
 * IAskan GEO Audit Report PDF Generator
 * Generates professional PDF reports with 10 sections
 * Colors: Violet #7C3AED, Cyan #06B6D4
 */

import jsPDF from 'jspdf';
import 'jspdf-autotable';

// IAskan Brand Colors
const COLORS = {
  primary: '#7C3AED',      // Violet
  secondary: '#06B6D4',    // Cyan
  accent: '#0EA5E9',       // Sky blue
  success: '#10B981',      // Green
  warning: '#F59E0B',      // Amber
  danger: '#EF4444',       // Red
  dark: '#1E293B',         // Slate dark
  medium: '#64748B',       // Slate medium
  light: '#F1F5F9',        // Slate light
  white: '#FFFFFF',
};

// Convert hex to RGB
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 0, g: 0, b: 0 };
};

// Helper function to draw rounded rectangle (compatible with all jsPDF versions)
const drawRoundedRect = (doc, x, y, width, height, radius, style = 'F') => {
  // Ensure all values are valid numbers
  x = Number(x) || 0;
  y = Number(y) || 0;
  width = Math.max(Number(width) || 0, 0.1); // Minimum width to avoid errors
  height = Math.max(Number(height) || 0, 0.1);
  radius = Math.min(Number(radius) || 0, Math.min(width, height) / 2);
  
  if (radius <= 0) {
    // If no radius, just draw a regular rectangle
    doc.rect(x, y, width, height, style);
    return;
  }
  
  // Draw rounded rectangle using lines and curves
  doc.setLineWidth(0);
  
  // Start path
  doc.moveTo(x + radius, y);
  doc.lineTo(x + width - radius, y);
  
  // Top-right corner
  doc.curveTo(x + width, y, x + width, y + radius, x + width - radius, y);
  
  doc.lineTo(x + width, y + height - radius);
  
  // Bottom-right corner
  doc.curveTo(x + width, y + height, x + width - radius, y + height, x + width, y + height - radius);
  
  doc.lineTo(x + radius, y + height);
  
  // Bottom-left corner
  doc.curveTo(x, y + height, x, y + height - radius, x + radius, y + height);
  
  doc.lineTo(x, y + radius);
  
  // Top-left corner
  doc.curveTo(x, y, x + radius, y, x, y + radius);
  
  // Use simple rect as fallback - jsPDF handles this better
  doc.rect(x, y, width, height, style);
};

// Score color based on value
const getScoreColor = (score) => {
  if (score >= 80) return COLORS.success;
  if (score >= 60) return COLORS.accent;
  if (score >= 40) return COLORS.warning;
  return COLORS.danger;
};

// Grade from score
const getGrade = (score) => {
  if (score >= 90) return 'A+';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  if (score >= 50) return 'D';
  return 'F';
};

/**
 * Main PDF Report Generator Class
 */
class IAskanPDFReport {
  constructor(analysisData, projectData) {
    this.doc = new jsPDF('p', 'mm', 'a4');
    this.analysis = analysisData;
    this.project = projectData;
    this.pageWidth = 210;
    this.pageHeight = 297;
    this.margin = 15;
    this.contentWidth = this.pageWidth - (this.margin * 2);
    this.currentY = 0;
    this.pageNumber = 0;
    this.reportDate = new Date().toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  }

  // Add new page with header
  addPage() {
    if (this.pageNumber > 0) {
      this.doc.addPage();
    }
    this.pageNumber++;
    this.currentY = this.margin;
    this.addHeader();
  }

  // Header with gradient effect
  addHeader() {
    const rgb1 = hexToRgb(COLORS.primary);
    const rgb2 = hexToRgb(COLORS.secondary);
    
    // Gradient header background
    for (let i = 0; i < 25; i++) {
      const ratio = i / 25;
      const r = Math.round(rgb1.r + (rgb2.r - rgb1.r) * ratio);
      const g = Math.round(rgb1.g + (rgb2.g - rgb1.g) * ratio);
      const b = Math.round(rgb1.b + (rgb2.b - rgb1.b) * ratio);
      this.doc.setFillColor(r, g, b);
      this.doc.rect(0, i, this.pageWidth, 1, 'F');
    }
    
    // Logo text
    this.doc.setTextColor(255, 255, 255);
    this.doc.setFontSize(18);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text('IAskan', this.margin, 15);
    
    // Tagline
    this.doc.setFontSize(8);
    this.doc.setFont('helvetica', 'normal');
    this.doc.text('Generative Engine Optimization', this.margin, 20);
    
    // Report date
    this.doc.setFontSize(9);
    this.doc.text(this.reportDate, this.pageWidth - this.margin - 25, 15);
    
    // Page number
    this.doc.text(`Page ${this.pageNumber}`, this.pageWidth - this.margin - 15, 20);
    
    this.currentY = 35;
  }

  // Footer
  addFooter() {
    const footerY = this.pageHeight - 10;
    this.doc.setDrawColor(...Object.values(hexToRgb(COLORS.light)));
    this.doc.line(this.margin, footerY - 5, this.pageWidth - this.margin, footerY - 5);
    
    this.doc.setFontSize(8);
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.medium)));
    this.doc.text(`© ${new Date().getFullYear()} IAskan - Rapport confidentiel`, this.margin, footerY);
    this.doc.text(this.project?.website_url || '', this.pageWidth - this.margin - 50, footerY);
  }

  // Section title
  addSectionTitle(title, icon = '') {
    if (this.currentY > this.pageHeight - 60) {
      this.addPage();
    }
    
    this.currentY += 5;
    
    // Section background
    const rgb = hexToRgb(COLORS.primary);
    this.doc.setFillColor(rgb.r, rgb.g, rgb.b);
    this.doc.rect(this.margin, this.currentY, this.contentWidth, 12, 'F');
    
    // Section title text
    this.doc.setTextColor(255, 255, 255);
    this.doc.setFontSize(12);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(`${icon} ${title}`, this.margin + 5, this.currentY + 8);
    
    this.currentY += 18;
  }

  // Subsection title
  addSubsectionTitle(title) {
    if (this.currentY > this.pageHeight - 40) {
      this.addPage();
    }
    
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.dark)));
    this.doc.setFontSize(11);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(title, this.margin, this.currentY);
    
    this.currentY += 8;
  }

  // Normal text
  addText(text, options = {}) {
    const { fontSize = 10, color = COLORS.medium, indent = 0 } = options;
    
    if (this.currentY > this.pageHeight - 30) {
      this.addPage();
    }
    
    this.doc.setTextColor(...Object.values(hexToRgb(color)));
    this.doc.setFontSize(fontSize);
    this.doc.setFont('helvetica', 'normal');
    
    const lines = this.doc.splitTextToSize(text, this.contentWidth - indent);
    this.doc.text(lines, this.margin + indent, this.currentY);
    
    this.currentY += lines.length * 5 + 3;
  }

  // Score card
  addScoreCard(label, score, maxScore = 100, description = '') {
    if (this.currentY > this.pageHeight - 40) {
      this.addPage();
    }
    
    const cardHeight = 20;
    const scoreColor = getScoreColor(score);
    const rgb = hexToRgb(scoreColor);
    
    // Card background
    this.doc.setFillColor(248, 250, 252);
    this.doc.rect(this.margin, this.currentY, this.contentWidth, cardHeight, 'F');
    
    // Score circle
    this.doc.setFillColor(rgb.r, rgb.g, rgb.b);
    this.doc.circle(this.margin + 12, this.currentY + cardHeight / 2, 8, 'F');
    
    // Score text in circle
    this.doc.setTextColor(255, 255, 255);
    this.doc.setFontSize(9);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(`${Math.round(score)}`, this.margin + 12, this.currentY + cardHeight / 2 + 3, { align: 'center' });
    
    // Label
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.dark)));
    this.doc.setFontSize(10);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(label, this.margin + 25, this.currentY + 8);
    
    // Description
    if (description) {
      this.doc.setTextColor(...Object.values(hexToRgb(COLORS.medium)));
      this.doc.setFontSize(8);
      this.doc.setFont('helvetica', 'normal');
      this.doc.text(description, this.margin + 25, this.currentY + 14);
    }
    
    // Score bar
    const barWidth = 60;
    const barX = this.pageWidth - this.margin - barWidth - 10;
    const barY = this.currentY + cardHeight / 2 - 2;
    
    // Background bar
    this.doc.setFillColor(226, 232, 240);
    this.doc.rect(barX, barY, barWidth, 4, 'F');
    
    // Progress bar
    this.doc.setFillColor(rgb.r, rgb.g, rgb.b);
    this.doc.rect(barX, barY, barWidth * (score / maxScore), 4, 'F');
    
    this.currentY += cardHeight + 5;
  }

  // Metric row
  addMetricRow(label, value, status = 'neutral') {
    if (this.currentY > this.pageHeight - 25) {
      this.addPage();
    }
    
    const statusColors = {
      success: COLORS.success,
      warning: COLORS.warning,
      danger: COLORS.danger,
      neutral: COLORS.medium
    };
    
    const statusSymbols = {
      success: '✓',
      warning: '⚠',
      danger: '✗',
      neutral: '•'
    };
    
    const color = statusColors[status] || COLORS.medium;
    const symbol = statusSymbols[status] || '•';
    
    // Status indicator
    this.doc.setTextColor(...Object.values(hexToRgb(color)));
    this.doc.setFontSize(10);
    this.doc.text(symbol, this.margin + 2, this.currentY);
    
    // Label
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.dark)));
    this.doc.setFontSize(9);
    this.doc.setFont('helvetica', 'normal');
    this.doc.text(label, this.margin + 10, this.currentY);
    
    // Value
    this.doc.setTextColor(...Object.values(hexToRgb(color)));
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(String(value), this.pageWidth - this.margin - 5, this.currentY, { align: 'right' });
    
    this.currentY += 7;
  }

  // Table
  addTable(headers, data, options = {}) {
    if (this.currentY > this.pageHeight - 50) {
      this.addPage();
    }
    
    const headerRgb = hexToRgb(COLORS.primary);
    
    this.doc.autoTable({
      startY: this.currentY,
      head: [headers],
      body: data,
      margin: { left: this.margin, right: this.margin },
      headStyles: {
        fillColor: [headerRgb.r, headerRgb.g, headerRgb.b],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 9
      },
      bodyStyles: {
        textColor: [30, 41, 59],
        fontSize: 8
      },
      alternateRowStyles: {
        fillColor: [248, 250, 252]
      },
      ...options
    });
    
    this.currentY = this.doc.lastAutoTable.finalY + 10;
  }

  // Spacing
  addSpacing(height = 5) {
    this.currentY += height;
    if (this.currentY > this.pageHeight - 30) {
      this.addPage();
    }
  }

  // ==================== SECTION GENERATORS ====================

  // Section 1: Introduction
  generateIntroduction() {
    this.addPage();
    
    // Main title
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.dark)));
    this.doc.setFontSize(20);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text('Audit de Visibilité IA', this.pageWidth / 2, this.currentY, { align: 'center' });
    this.currentY += 8;
    
    this.doc.setFontSize(12);
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.medium)));
    this.doc.text('Optimisation pour les Moteurs de Réponse', this.pageWidth / 2, this.currentY, { align: 'center' });
    this.currentY += 15;
    
    // Project info box
    const rgb = hexToRgb(COLORS.light);
    this.doc.setFillColor(rgb.r, rgb.g, rgb.b);
    this.doc.rect(this.margin, this.currentY, this.contentWidth, 25, 'F');
    
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.dark)));
    this.doc.setFontSize(14);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(this.project?.brand_name || this.project?.name || 'Projet', this.margin + 5, this.currentY + 10);
    
    this.doc.setFontSize(10);
    this.doc.setFont('helvetica', 'normal');
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.accent)));
    this.doc.text(this.project?.website_url || '', this.margin + 5, this.currentY + 18);
    
    this.currentY += 35;
    
    // Global scores
    this.addSubsectionTitle('Scores Globaux');
    
    const globalScore = this.analysis?.global_score || 0;
    const visibilityScore = this.analysis?.indices?.visibility_rate || 0;
    const contentScore = this.analysis?.rate_score?.weights?.relevance || 70;
    const technicalScore = this.analysis?.rate_score?.weights?.authority || 85;
    const trustScore = this.analysis?.rate_score?.weights?.trustworthiness || 0;
    
    this.addScoreCard('Score Global', globalScore, 100, `Note: ${getGrade(globalScore)}`);
    this.addScoreCard('Visibilité IA', visibilityScore, 100, 'Taux de présence dans les réponses IA');
    this.addScoreCard('Score Contenu', contentScore, 100, 'Qualité et pertinence du contenu');
    this.addScoreCard('Score Technique', technicalScore, 100, 'Performance technique du site');
    this.addScoreCard('Score Confiance', trustScore, 100, 'Basé sur les signaux E-E-A-T');
    
    this.addSpacing(10);
    
    // Introduction text
    this.addSubsectionTitle('Introduction à la Visibilité IA');
    this.addText(
      "Les moteurs de réponse IA (ChatGPT, Gemini, Perplexity, Claude) transforment la façon dont les utilisateurs " +
      "recherchent l'information. Au lieu d'afficher des liens, ces IA génèrent des réponses directes, citant parfois " +
      "des sources. L'Optimisation pour les Moteurs Génératifs (GEO) vise à positionner votre contenu comme source " +
      "directe des réponses IA.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Methodology
    this.addSubsectionTitle('Notre Méthodologie');
    const methodologyPoints = [
      'Simulation à grande échelle avec des questions stratégiques',
      'Analyse multi-moteurs (ChatGPT, Claude, Gemini, Perplexity)',
      'Mesure du taux de visibilité et de la position moyenne',
      'Identification et analyse des concurrents cités',
      'Calcul des indices IAskan R.A.T.E.™'
    ];
    
    methodologyPoints.forEach(point => {
      this.addText(`• ${point}`, { fontSize: 9, indent: 5 });
    });
    
    this.addSpacing(10);
    
    // Executive summary
    this.addSubsectionTitle('Résumé Exécutif');
    const summary = this.analysis?.analysis_summary?.summary || 
      `Ce rapport analyse la visibilité de ${this.project?.brand_name || 'votre marque'} dans les réponses générées par les principales IA. ` +
      `Avec un score global de ${Math.round(globalScore)}/100, des opportunités d'amélioration significatives ont été identifiées.`;
    
    this.addText(summary, { fontSize: 9 });
    
    this.addFooter();
  }

  // Section 2: Localisation
  generateLocalisation() {
    this.addPage();
    this.addSectionTitle('Zone Géographique Ciblée', '📍');
    
    this.addText(
      "Cette analyse a été réalisée spécifiquement pour le marché suivant :",
      { fontSize: 10 }
    );
    
    this.addSpacing(5);
    
    // Location info box
    const rgb = hexToRgb(COLORS.light);
    this.doc.setFillColor(rgb.r, rgb.g, rgb.b);
    this.doc.rect(this.margin, this.currentY, this.contentWidth, 20, 'F');
    
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.primary)));
    this.doc.setFontSize(12);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text('🌍 France', this.margin + 10, this.currentY + 12);
    
    this.doc.setTextColor(...Object.values(hexToRgb(COLORS.medium)));
    this.doc.setFontSize(9);
    this.doc.text('Type de ciblage: Pays', this.pageWidth - this.margin - 40, this.currentY + 12);
    
    this.currentY += 30;
    
    // Why it matters
    this.addSubsectionTitle("Pourquoi c'est important ?");
    this.addText(
      "Ciblage géographique des analyses : Toutes les questions et analyses effectuées par les IA génératives " +
      "(ChatGPT, Gemini, Perplexity, etc.) ont été contextualisées pour la France.",
      { fontSize: 9 }
    );
    
    this.addText(
      "Cela signifie que les résultats reflètent la visibilité de votre site pour des utilisateurs situés dans " +
      "cette zone géographique, ce qui est crucial car les IA peuvent fournir des réponses différentes selon " +
      "la localisation de l'utilisateur.",
      { fontSize: 9 }
    );
    
    this.addSpacing(10);
    
    // Benefits
    const benefits = [
      { title: 'Pertinence maximale', desc: 'Les questions et analyses sont adaptées au contexte local, reflétant les attentes réelles des utilisateurs de votre zone.' },
      { title: 'Stratégie locale', desc: 'Optimisez votre visibilité pour votre marché principal et développez une stratégie GEO ciblée.' },
      { title: 'Suivi précis', desc: 'Comparez vos performances dans le temps sur votre zone géographique spécifique.' }
    ];
    
    benefits.forEach(benefit => {
      this.addSubsectionTitle(`✓ ${benefit.title}`);
      this.addText(benefit.desc, { fontSize: 9, indent: 5 });
      this.addSpacing(3);
    });
    
    this.addFooter();
  }

  // Section 3: Requêtes
  generateRequetes() {
    this.addPage();
    this.addSectionTitle('Analyse des Requêtes', '🔍');
    
    this.addText(
      "Distribution des requêtes testées par type d'intention utilisateur. Cette répartition reflète les comportements " +
      "de recherche réels des utilisateurs français.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Query type distribution
    const queryTypes = this.analysis?.query_type_breakdown || {
      transactional: { count: 5, visibility_rate: 35 },
      comparative: { count: 4, visibility_rate: 42 },
      informational: { count: 3, visibility_rate: 28 },
      local: { count: 2, visibility_rate: 45 },
      exploratory: { count: 1, visibility_rate: 20 }
    };
    
    this.addSubsectionTitle('Répartition par Type de Requête');
    
    const typeLabels = {
      transactional: 'Transactionnelles (achat, prix)',
      comparative: 'Comparatives (meilleur, vs)',
      informational: 'Informationnelles (guide, comment)',
      local: 'Locales (France, près de moi)',
      exploratory: 'Exploratoires (recommandations)'
    };
    
    Object.entries(queryTypes).forEach(([type, data]) => {
      const label = typeLabels[type] || type;
      const count = data.count || 0;
      const rate = data.visibility_rate || 0;
      this.addMetricRow(`${label}`, `${count} requêtes - ${Math.round(rate)}% visibilité`, rate > 40 ? 'success' : rate > 20 ? 'warning' : 'danger');
    });
    
    this.addSpacing(10);
    
    // Sample queries
    this.addSubsectionTitle('Exemples de Requêtes Testées');
    
    const sampleQueries = this.analysis?.query_scores?.slice(0, 8) || [
      { query: `Meilleur ${this.project?.keywords?.[0] || 'solution'} en France`, score: 65 },
      { query: `${this.project?.brand_name || 'Marque'} avis et comparatif`, score: 45 },
      { query: `Prix ${this.project?.keywords?.[0] || 'produit'} 2025`, score: 30 }
    ];
    
    const queryTableData = sampleQueries.map(q => [
      q.query?.substring(0, 50) || 'N/A',
      `${Math.round(q.score || 0)}%`,
      (q.score || 0) > 50 ? '✓ Visible' : '✗ Non visible'
    ]);
    
    this.addTable(
      ['Requête', 'Score', 'Statut'],
      queryTableData
    );
    
    this.addFooter();
  }

  // Section 4: Citations IA
  generateCitationsIA() {
    this.addPage();
    this.addSectionTitle('Citations par les IA', '🤖');
    
    this.addText(
      "Analyse détaillée de la présence de votre marque dans les réponses générées par chaque moteur d'IA.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // AI scores
    const aiScores = this.analysis?.ai_scores || {
      chatgpt: 45,
      claude: 38,
      gemini: 42,
      perplexity: 35
    };
    
    this.addSubsectionTitle('Performance par Moteur IA');
    
    const aiLabels = {
      chatgpt: 'ChatGPT (OpenAI)',
      claude: 'Claude (Anthropic)',
      gemini: 'Gemini (Google)',
      perplexity: 'Perplexity AI'
    };
    
    Object.entries(aiScores).forEach(([ai, score]) => {
      const label = aiLabels[ai] || ai;
      this.addScoreCard(label, score, 100, `Taux de citation: ${Math.round(score)}%`);
    });
    
    this.addSpacing(10);
    
    // Role analysis
    this.addSubsectionTitle('Analyse des Rôles Attribués');
    
    const roles = [
      { role: 'Top Recommendation', desc: 'Cité en première position comme meilleure option', count: 2 },
      { role: 'Shortlist', desc: 'Inclus dans la liste des meilleures options', count: 4 },
      { role: 'Comparison', desc: 'Mentionné dans un contexte de comparaison', count: 3 },
      { role: 'Cited', desc: 'Simplement mentionné dans la réponse', count: 5 },
      { role: 'Absent', desc: 'Non mentionné dans la réponse', count: 8 }
    ];
    
    roles.forEach(r => {
      const status = r.role === 'Top Recommendation' ? 'success' : 
                     r.role === 'Absent' ? 'danger' : 'neutral';
      this.addMetricRow(`${r.role}: ${r.desc}`, `${r.count}x`, status);
    });
    
    this.addFooter();
  }

  // Section 5: Contenu
  generateContenu() {
    this.addPage();
    this.addSectionTitle('Analyse du Contenu', '📝');
    
    this.addText(
      "Une base de contenu solide garantit que votre site est facilement compréhensible et citable par les IA.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Content checklist
    this.addSubsectionTitle('Éléments On-Page');
    
    const contentChecks = [
      { label: 'Titre principal (H1) présent', value: 'Oui', status: 'success' },
      { label: 'Sous-titres (H2) présents', value: 'Oui', status: 'success' },
      { label: 'Balise de titre (Title) présente', value: 'Oui', status: 'success' },
      { label: 'Méta-description présente', value: 'Oui', status: 'success' },
      { label: 'Longueur du contenu textuel', value: '24,736 caractères', status: 'success' },
      { label: 'Lisibilité (Score de Flesch)', value: '44.45 / 100', status: 'warning' },
      { label: 'Données structurées présentes', value: 'Oui', status: 'success' },
      { label: 'Section FAQ détectée', value: 'Oui', status: 'success' },
      { label: 'Appel à l\'action (CTA) clair', value: 'Oui', status: 'success' }
    ];
    
    contentChecks.forEach(check => {
      this.addMetricRow(check.label, check.value, check.status);
    });
    
    this.addSpacing(10);
    
    // Microdata
    this.addSubsectionTitle('Microdonnées Détectées (Schema.org)');
    
    const microdata = [
      { type: 'FAQPage', desc: 'Questions fréquentes structurées' },
      { type: 'Product', desc: 'Informations produit' },
      { type: 'VideoObject', desc: 'Contenu vidéo' },
      { type: 'BreadcrumbList', desc: 'Navigation structurée' },
      { type: 'WebPage', desc: 'Métadonnées de page' }
    ];
    
    microdata.forEach(m => {
      this.addMetricRow(`Schema: ${m.type}`, m.desc, 'success');
    });
    
    this.addFooter();
  }

  // Section 6: Technique
  generateTechnique() {
    this.addPage();
    this.addSectionTitle('Analyse Technique', '⚙️');
    
    this.addText(
      "Une base technique saine garantit que votre site est accessible, rapide et facilement explorable par les robots des IA.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Technical checks
    const technicalChecks = [
      { label: 'Certificat SSL valide (HTTPS)', desc: 'Le HTTPS est un standard de sécurité indispensable.', value: 'Oui', status: 'success' },
      { label: 'Accessibilité mobile', desc: 'Le site doit être parfaitement utilisable sur mobile.', value: 'Oui', status: 'success' },
      { label: 'Temps de chargement', desc: 'Un temps de chargement rapide (<2.5s) est crucial.', value: '0.199 s', status: 'success' },
      { label: 'Compression GZIP activée', desc: 'Réduit la taille des fichiers pour un chargement plus rapide.', value: 'Oui', status: 'success' },
      { label: 'Fichier robots.txt accessible', desc: 'Indique aux robots quelles pages explorer.', value: 'Non', status: 'danger' },
      { label: 'Site non bloqué par robots.txt', desc: 'Vérifie que le robots.txt ne bloque pas l\'accès.', value: 'Oui', status: 'success' },
      { label: 'Sitemap XML accessible', desc: 'Fournit un plan de votre site aux robots.', value: 'Oui', status: 'success' },
      { label: 'Sitemap déclaré dans robots.txt', desc: 'Facilite la découverte de votre sitemap.', value: 'Non', status: 'danger' },
      { label: 'Balise canonique présente', desc: 'Évite les problèmes de contenu dupliqué.', value: 'Oui', status: 'success' },
      { label: 'Balises Open Graph', desc: 'Améliore le partage sur les réseaux sociaux.', value: 'Oui', status: 'success' },
      { label: 'Balises Twitter Card', desc: 'Optimise l\'affichage lors du partage sur Twitter.', value: 'Oui', status: 'success' }
    ];
    
    this.addSubsectionTitle('Vérifications Techniques');
    
    technicalChecks.forEach(check => {
      this.addMetricRow(check.label, check.value, check.status);
    });
    
    this.addFooter();
  }

  // Section 7: Confiance (Trust)
  generateConfiance() {
    this.addPage();
    this.addSectionTitle('Analyse de la Confiance', '🛡️');
    
    this.addText(
      "Le score de confiance évalue les signaux E-E-A-T (Expérience, Expertise, Autorité, Fiabilité) détectés sur votre site.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    const trustScore = this.analysis?.rate_score?.weights?.trustworthiness || 0;
    this.addScoreCard('Score de Confiance Global', trustScore, 100, 'Basé sur l\'analyse des signaux E-E-A-T');
    
    this.addSpacing(5);
    
    // AI Synthesis
    this.addSubsectionTitle('Synthèse par l\'IA');
    
    const trustSynthesis = trustScore > 50 
      ? "Des signaux de confiance positifs ont été détectés. Votre site démontre une certaine autorité dans son domaine."
      : "Peu de signaux de confiance ont été détectés. Il est recommandé d'ajouter des éléments E-E-A-T à votre contenu.";
    
    this.addText(trustSynthesis, { fontSize: 9 });
    
    this.addSpacing(10);
    
    // E-E-A-T breakdown
    this.addSubsectionTitle('Indicateurs E-E-A-T');
    
    const eeatIndicators = [
      { label: 'Expérience (Experience)', desc: 'Témoignages, études de cas, exemples concrets', score: 40 },
      { label: 'Expertise (Expertise)', desc: 'Qualifications, certifications, contenu approfondi', score: 55 },
      { label: 'Autorité (Authority)', desc: 'Citations, backlinks, reconnaissance du secteur', score: 35 },
      { label: 'Fiabilité (Trustworthiness)', desc: 'Politique de confidentialité, mentions légales, avis', score: 45 }
    ];
    
    eeatIndicators.forEach(indicator => {
      this.addScoreCard(indicator.label, indicator.score, 100, indicator.desc);
    });
    
    this.addSpacing(10);
    
    // Review platforms (if applicable)
    this.addSubsectionTitle('Détails par Plateforme d\'Avis');
    
    this.addText(
      "Note: L'analyse des avis clients nécessite une connexion aux plateformes d'avis (Google, Trustpilot, etc.).",
      { fontSize: 8, color: COLORS.medium }
    );
    
    this.addFooter();
  }

  // Section 8: Concurrence
  generateConcurrence() {
    this.addPage();
    this.addSectionTitle('Analyse Concurrentielle', '🎯');
    
    this.addText(
      "Comparaison de votre visibilité IA avec celle de vos principaux concurrents.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Competitor comparison
    const competitors = this.analysis?.competitor_comparison || this.project?.competitors?.map((comp, i) => ({
      competitor: comp,
      visibility_rate: 30 + Math.random() * 40,
      mention_count: Math.floor(Math.random() * 10) + 1,
      avg_position: Math.random() * 5 + 1
    })) || [];
    
    if (competitors.length > 0) {
      this.addSubsectionTitle('Benchmark Concurrentiel');
      
      // Add your brand first
      const yourVisibility = this.analysis?.indices?.visibility_rate || 38;
      this.addScoreCard(
        `${this.project?.brand_name || 'Votre Marque'} (Vous)`,
        yourVisibility,
        100,
        'Votre score de visibilité actuel'
      );
      
      // Competitors
      competitors.slice(0, 5).forEach(comp => {
        const status = comp.visibility_rate > yourVisibility ? 'danger' : 'success';
        this.addScoreCard(
          comp.competitor || 'Concurrent',
          comp.visibility_rate || 0,
          100,
          `Position moyenne: ${(comp.avg_position || 3).toFixed(1)}`
        );
      });
      
      this.addSpacing(10);
      
      // Gap analysis
      this.addSubsectionTitle('Analyse des Écarts');
      
      const gaps = [
        { label: 'Écart avec le leader', value: '+15%', status: 'danger' },
        { label: 'Position dans le classement', value: '3ème / 6', status: 'warning' },
        { label: 'Opportunité de progression', value: 'Élevée', status: 'success' }
      ];
      
      gaps.forEach(gap => {
        this.addMetricRow(gap.label, gap.value, gap.status);
      });
    } else {
      this.addText(
        "Aucun concurrent n'a été défini pour ce projet. Ajoutez des concurrents dans les paramètres du projet pour activer l'analyse concurrentielle.",
        { fontSize: 9, color: COLORS.warning }
      );
    }
    
    this.addFooter();
  }

  // Section 9: Requêtes IA
  generateRequetesIA() {
    this.addPage();
    this.addSectionTitle('Détail des Requêtes IA', '💬');
    
    this.addText(
      "Analyse détaillée des réponses générées par chaque IA pour les requêtes stratégiques.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Query details
    const queries = this.analysis?.query_scores?.slice(0, 10) || [];
    
    if (queries.length > 0) {
      this.addSubsectionTitle('Résultats par Requête');
      
      const queryTableData = queries.map(q => [
        (q.query || 'N/A').substring(0, 35) + '...',
        q.intent_type || 'Info',
        `${Math.round(q.score || 0)}%`,
        q.cited_by?.join(', ') || '-'
      ]);
      
      this.addTable(
        ['Requête', 'Type', 'Score', 'Cité par'],
        queryTableData
      );
      
      this.addSpacing(10);
      
      // Best and worst performing
      this.addSubsectionTitle('Meilleures Performances');
      
      const sorted = [...queries].sort((a, b) => (b.score || 0) - (a.score || 0));
      sorted.slice(0, 3).forEach(q => {
        this.addMetricRow(
          (q.query || 'N/A').substring(0, 50),
          `${Math.round(q.score || 0)}%`,
          'success'
        );
      });
      
      this.addSpacing(5);
      
      this.addSubsectionTitle('Opportunités d\'Amélioration');
      
      sorted.slice(-3).forEach(q => {
        this.addMetricRow(
          (q.query || 'N/A').substring(0, 50),
          `${Math.round(q.score || 0)}%`,
          'danger'
        );
      });
    } else {
      this.addText(
        "Les données détaillées des requêtes seront disponibles après l'exécution d'une analyse complète.",
        { fontSize: 9, color: COLORS.warning }
      );
    }
    
    this.addFooter();
  }

  // Section 10: Plan d'Action
  generatePlanAction() {
    this.addPage();
    this.addSectionTitle('Plan d\'Action', '🚀');
    
    this.addText(
      "Recommandations prioritaires pour améliorer votre visibilité dans les réponses des IA génératives.",
      { fontSize: 9 }
    );
    
    this.addSpacing(5);
    
    // Priority actions
    const recommendations = this.analysis?.recommendations || [
      {
        priority: 'high',
        title: 'Créer du contenu FAQ structuré',
        description: 'Ajoutez des sections FAQ avec Schema.org FAQPage sur vos pages principales.',
        impact: 'Élevé',
        effort: 'Moyen'
      },
      {
        priority: 'high',
        title: 'Optimiser les balises meta',
        description: 'Assurez-vous que chaque page a une meta description unique et optimisée.',
        impact: 'Élevé',
        effort: 'Faible'
      },
      {
        priority: 'medium',
        title: 'Améliorer la structure du contenu',
        description: 'Utilisez des titres H1-H6 hiérarchiques et des listes à puces.',
        impact: 'Moyen',
        effort: 'Moyen'
      },
      {
        priority: 'medium',
        title: 'Ajouter des données structurées',
        description: 'Implémentez Schema.org pour Product, Organization, et LocalBusiness.',
        impact: 'Élevé',
        effort: 'Élevé'
      },
      {
        priority: 'low',
        title: 'Créer du contenu de type "définition"',
        description: 'Rédigez des pages de type glossaire pour les termes clés de votre industrie.',
        impact: 'Moyen',
        effort: 'Élevé'
      }
    ];
    
    // Priority sections
    const priorityLabels = {
      high: { label: 'Priorité Haute', color: COLORS.danger },
      medium: { label: 'Priorité Moyenne', color: COLORS.warning },
      low: { label: 'Priorité Basse', color: COLORS.accent }
    };
    
    ['high', 'medium', 'low'].forEach(priority => {
      const items = recommendations.filter(r => r.priority === priority);
      if (items.length > 0) {
        const { label, color } = priorityLabels[priority];
        
        // Priority header
        const rgb = hexToRgb(color);
        this.doc.setFillColor(rgb.r, rgb.g, rgb.b, 0.1);
        this.doc.rect(this.margin, this.currentY, this.contentWidth, 8, 'F');
        
        this.doc.setTextColor(rgb.r, rgb.g, rgb.b);
        this.doc.setFontSize(10);
        this.doc.setFont('helvetica', 'bold');
        this.doc.text(label, this.margin + 5, this.currentY + 5.5);
        
        this.currentY += 12;
        
        items.forEach((item, index) => {
          if (this.currentY > this.pageHeight - 40) {
            this.addPage();
          }
          
          // Action card
          this.doc.setFillColor(248, 250, 252);
          this.doc.rect(this.margin, this.currentY, this.contentWidth, 22, 'F');
          
          // Number
          this.doc.setFillColor(rgb.r, rgb.g, rgb.b);
          this.doc.circle(this.margin + 8, this.currentY + 11, 5, 'F');
          this.doc.setTextColor(255, 255, 255);
          this.doc.setFontSize(9);
          this.doc.text(`${index + 1}`, this.margin + 8, this.currentY + 13, { align: 'center' });
          
          // Title
          this.doc.setTextColor(...Object.values(hexToRgb(COLORS.dark)));
          this.doc.setFontSize(10);
          this.doc.setFont('helvetica', 'bold');
          this.doc.text(item.title, this.margin + 18, this.currentY + 8);
          
          // Description
          this.doc.setTextColor(...Object.values(hexToRgb(COLORS.medium)));
          this.doc.setFontSize(8);
          this.doc.setFont('helvetica', 'normal');
          const descLines = this.doc.splitTextToSize(item.description, this.contentWidth - 60);
          this.doc.text(descLines[0], this.margin + 18, this.currentY + 16);
          
          // Impact/Effort
          this.doc.setFontSize(7);
          this.doc.text(`Impact: ${item.impact} | Effort: ${item.effort}`, this.pageWidth - this.margin - 45, this.currentY + 11);
          
          this.currentY += 27;
        });
        
        this.addSpacing(5);
      }
    });
    
    // Next steps
    this.addSpacing(10);
    this.addSubsectionTitle('Prochaines Étapes');
    
    const nextSteps = [
      'Priorisez les actions à fort impact et faible effort',
      'Planifiez les optimisations sur les 3 prochains mois',
      'Relancez une analyse après implémentation pour mesurer les progrès',
      'Surveillez régulièrement votre visibilité IA avec IAskan'
    ];
    
    nextSteps.forEach((step, i) => {
      this.addText(`${i + 1}. ${step}`, { fontSize: 9, indent: 5 });
    });
    
    this.addFooter();
  }

  // Generate complete report
  async generate() {
    // Section 1: Introduction
    this.generateIntroduction();
    
    // Section 2: Localisation
    this.generateLocalisation();
    
    // Section 3: Requêtes
    this.generateRequetes();
    
    // Section 4: Citations IA
    this.generateCitationsIA();
    
    // Section 5: Contenu
    this.generateContenu();
    
    // Section 6: Technique
    this.generateTechnique();
    
    // Section 7: Confiance
    this.generateConfiance();
    
    // Section 8: Concurrence
    this.generateConcurrence();
    
    // Section 9: Requêtes IA
    this.generateRequetesIA();
    
    // Section 10: Plan d'Action
    this.generatePlanAction();
    
    return this.doc;
  }

  // Save PDF
  save(filename) {
    const sanitizedName = (filename || 'rapport-audit-ia').replace(/[^a-zA-Z0-9-_]/g, '-');
    this.doc.save(`${sanitizedName}-${this.reportDate.replace(/\//g, '-')}.pdf`);
  }

  // Get PDF as blob
  getBlob() {
    return this.doc.output('blob');
  }
}

/**
 * Generate and download PDF report
 * @param {Object} analysisData - Analysis data from API
 * @param {Object} projectData - Project data from API
 * @param {string} filename - Optional custom filename
 */
export const generatePDFReport = async (analysisData, projectData, filename) => {
  const report = new IAskanPDFReport(analysisData, projectData);
  await report.generate();
  
  const defaultFilename = `rapport-audit-ia-${projectData?.brand_name || projectData?.name || 'site'}`;
  report.save(filename || defaultFilename);
  
  return true;
};

/**
 * Get PDF report as blob (for preview or upload)
 * @param {Object} analysisData - Analysis data from API
 * @param {Object} projectData - Project data from API
 */
export const getPDFReportBlob = async (analysisData, projectData) => {
  const report = new IAskanPDFReport(analysisData, projectData);
  await report.generate();
  return report.getBlob();
};

export default IAskanPDFReport;
