import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  X, 
  ChevronRight,
  Rocket,
  Search,
  Zap,
  CheckCircle2,
  ArrowRight,
  Sparkles
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Quick Onboarding Modal - Sprint E
 * Simplified 3-step onboarding process
 * 
 * Step 1: Welcome + Quick value proposition
 * Step 2: Create project (or skip to existing)
 * Step 3: Launch first analysis
 */

const QUICK_STEPS = [
  {
    id: 'welcome',
    icon: Rocket,
    color: 'from-violet-500 to-cyan-500',
    title: 'Bienvenue sur IAskan',
    subtitle: 'Votre visibilité IA en 3 clics',
    description: 'Découvrez comment ChatGPT, Claude, Gemini et Perplexity parlent de votre marque.',
    features: [
      '4 IA analysées simultanément',
      'Score GEO instantané',
      'Recommandations actionnables'
    ],
    buttonText: "C'est parti !",
    buttonIcon: ArrowRight
  },
  {
    id: 'project',
    icon: Search,
    color: 'from-emerald-500 to-teal-500',
    title: 'Configurez votre marque',
    subtitle: '30 secondes chrono',
    description: 'Entrez simplement le nom de votre marque et votre site web. On s\'occupe du reste.',
    features: [
      'Logo détecté automatiquement',
      'Concurrents suggérés par IA',
      'Projet créé instantanément'
    ],
    buttonText: 'Créer mon projet',
    buttonIcon: ArrowRight,
    action: 'projects'
  },
  {
    id: 'analyze',
    icon: Zap,
    color: 'from-violet-500 to-purple-500',
    title: 'Lancez votre analyse',
    subtitle: 'Résultats en 2 minutes',
    description: 'Notre moteur GEO interroge les IA et calcule votre score de visibilité.',
    features: [
      'Analyse en temps réel',
      'Score R.A.T.E™ détaillé',
      'Plan d\'action priorisé'
    ],
    buttonText: 'Analyser ma visibilité',
    buttonIcon: Sparkles,
    action: 'analysis'
  }
];

export default function QuickOnboardingModal({ isOpen, onClose, onComplete }) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
    }
  }, [isOpen]);

  const handleNext = async () => {
    const step = QUICK_STEPS[currentStep];
    
    if (step.action) {
      // Navigate to the action page
      onClose?.();
      navigate(`/${step.action}`);
      if (currentStep === QUICK_STEPS.length - 1) {
        onComplete?.();
      }
      return;
    }

    if (currentStep < QUICK_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleSkip = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/onboarding/skip`, {}, { withCredentials: true });
    } catch (err) {
      console.error('Error skipping onboarding:', err);
    }
    onClose?.();
    onComplete?.();
  };

  if (!isOpen) return null;

  const step = QUICK_STEPS[currentStep];
  const StepIcon = step.icon;
  const ButtonIcon = step.buttonIcon;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header with gradient */}
        <div className={`bg-gradient-to-r ${step.color} p-6 relative`}>
          <button
            onClick={handleSkip}
            className="absolute top-4 right-4 text-white/80 hover:text-white transition-colors"
            data-testid="skip-onboarding"
          >
            <X className="w-5 h-5" />
          </button>
          
          {/* Step indicator */}
          <div className="flex items-center gap-2 mb-4">
            {QUICK_STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  i <= currentStep ? 'bg-white' : 'bg-white/30'
                }`}
              />
            ))}
          </div>
          
          {/* Icon */}
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mb-4">
            <StepIcon className="w-8 h-8 text-white" />
          </div>
          
          {/* Title */}
          <h2 className="text-2xl font-bold text-white mb-1">{step.title}</h2>
          <p className="text-white/90 font-medium">{step.subtitle}</p>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-slate-600 mb-6">{step.description}</p>
          
          {/* Features */}
          <div className="space-y-3 mb-8">
            {step.features.map((feature, i) => (
              <div key={i} className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <span className="text-slate-700">{feature}</span>
              </div>
            ))}
          </div>
          
          {/* Action button */}
          <button
            onClick={handleNext}
            disabled={loading}
            className={`w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r ${step.color} hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-lg`}
            data-testid="onboarding-next"
          >
            {step.buttonText}
            <ButtonIcon className="w-5 h-5" />
          </button>
          
          {/* Skip link */}
          <button
            onClick={handleSkip}
            className="w-full mt-4 text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            Passer l'introduction
          </button>
        </div>
      </div>
    </div>
  );
}
