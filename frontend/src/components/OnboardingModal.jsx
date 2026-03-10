import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  X, 
  ChevronRight, 
  ChevronLeft,
  Rocket,
  FolderPlus,
  BarChart3,
  Lightbulb,
  Sparkles,
  CheckCircle2,
  Play,
  ArrowRight
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Step configurations with illustrations
const STEP_CONFIG = {
  welcome: {
    icon: Rocket,
    color: "from-violet-500 to-cyan-500",
    illustration: (
      <div className="w-64 h-64 mx-auto relative">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-500/20 to-cyan-500/20 rounded-full animate-pulse"></div>
        <div className="absolute inset-8 bg-gradient-to-br from-violet-500/30 to-cyan-500/30 rounded-full animate-pulse animation-delay-200"></div>
        <div className="absolute inset-16 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-full flex items-center justify-center">
          <Rocket className="w-16 h-16 text-white" />
        </div>
      </div>
    ),
    content: {
      title: "Bienvenue sur IAskan",
      subtitle: "Optimisez votre visibilité dans les réponses IA",
      description: "IAskan analyse comment ChatGPT, Claude, Gemini et Perplexity parlent de votre marque. Découvrez votre score GEO et obtenez des recommandations concrètes pour améliorer votre présence.",
      features: [
        "Analysez votre visibilité sur 4 IA majeures",
        "Obtenez un score GEO précis et actionnable",
        "Recevez des recommandations personnalisées"
      ]
    }
  },
  create_project: {
    icon: FolderPlus,
    color: "from-green-500 to-emerald-500",
    illustration: (
      <div className="w-64 h-64 mx-auto flex items-center justify-center">
        <div className="relative">
          <div className="w-40 h-48 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl shadow-2xl transform -rotate-6"></div>
          <div className="absolute top-4 left-4 w-40 h-48 bg-white rounded-xl shadow-xl flex flex-col p-4">
            <div className="h-4 w-24 bg-slate-200 rounded mb-3"></div>
            <div className="h-3 w-32 bg-slate-100 rounded mb-2"></div>
            <div className="h-3 w-28 bg-slate-100 rounded mb-4"></div>
            <div className="flex-1 bg-gradient-to-br from-green-50 to-emerald-50 rounded"></div>
          </div>
        </div>
      </div>
    ),
    content: {
      title: "Créez votre premier projet",
      subtitle: "Configurez votre marque en 30 secondes",
      description: "Un projet contient votre marque, votre site web et vos concurrents. Toutes vos analyses seront liées à ce projet.",
      features: [
        "Ajoutez votre nom de marque et site web",
        "Définissez jusqu'à 5 concurrents",
        "Le logo est détecté automatiquement"
      ]
    }
  },
  first_scan: {
    icon: BarChart3,
    color: "from-blue-500 to-indigo-500",
    illustration: (
      <div className="w-64 h-64 mx-auto flex items-center justify-center">
        <div className="relative w-full h-full">
          {/* Animated bars */}
          <div className="absolute bottom-0 left-8 w-8 bg-blue-500 rounded-t animate-grow-bar" style={{height: '60%', animationDelay: '0s'}}></div>
          <div className="absolute bottom-0 left-20 w-8 bg-indigo-500 rounded-t animate-grow-bar" style={{height: '80%', animationDelay: '0.2s'}}></div>
          <div className="absolute bottom-0 left-32 w-8 bg-blue-400 rounded-t animate-grow-bar" style={{height: '45%', animationDelay: '0.4s'}}></div>
          <div className="absolute bottom-0 left-44 w-8 bg-indigo-400 rounded-t animate-grow-bar" style={{height: '90%', animationDelay: '0.6s'}}></div>
          {/* Score circle */}
          <div className="absolute top-4 right-4 w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-2xl shadow-lg">
            87
          </div>
        </div>
      </div>
    ),
    content: {
      title: "Lancez votre première analyse",
      subtitle: "Découvrez votre visibilité en quelques minutes",
      description: "Notre moteur GEO interroge les IA avec des centaines de requêtes réalistes et analyse leurs réponses pour calculer votre score de visibilité.",
      features: [
        "Analyse sur 4 IA en parallèle",
        "Jusqu'à 200 requêtes par scan",
        "Résultats détaillés en 2-5 minutes"
      ]
    }
  },
  explore_results: {
    icon: Lightbulb,
    color: "from-amber-500 to-orange-500",
    illustration: (
      <div className="w-64 h-64 mx-auto flex items-center justify-center">
        <div className="relative">
          <Lightbulb className="w-32 h-32 text-amber-500" />
          <div className="absolute -top-2 -right-2 w-6 h-6 bg-amber-400 rounded-full animate-ping"></div>
          <div className="absolute top-8 -left-4 w-4 h-4 bg-orange-400 rounded-full animate-ping animation-delay-300"></div>
          <div className="absolute bottom-4 right-0 w-5 h-5 bg-yellow-400 rounded-full animate-ping animation-delay-600"></div>
        </div>
      </div>
    ),
    content: {
      title: "Explorez vos résultats",
      subtitle: "Comprenez vos scores et agissez",
      description: "Votre rapport contient votre score GEO global, le détail par IA, vos forces, faiblesses et une liste de recommandations actionnables.",
      features: [
        "Score R.A.T.E™ détaillé",
        "Benchmark vs concurrents",
        "Recommandations prioritaires"
      ]
    }
  },
  article_optimizer: {
    icon: Sparkles,
    color: "from-purple-500 to-pink-500",
    illustration: (
      <div className="w-64 h-64 mx-auto flex items-center justify-center">
        <div className="relative">
          <div className="w-48 h-56 bg-white rounded-xl shadow-xl p-4 transform rotate-3">
            <div className="h-3 w-32 bg-purple-200 rounded mb-2"></div>
            <div className="h-2 w-full bg-slate-100 rounded mb-1"></div>
            <div className="h-2 w-full bg-slate-100 rounded mb-1"></div>
            <div className="h-2 w-3/4 bg-slate-100 rounded mb-3"></div>
            <div className="flex gap-2 mb-3">
              <div className="h-6 w-6 bg-green-100 rounded"></div>
              <div className="h-6 w-6 bg-yellow-100 rounded"></div>
              <div className="h-6 w-6 bg-red-100 rounded"></div>
            </div>
            <div className="h-2 w-full bg-slate-100 rounded mb-1"></div>
            <div className="h-2 w-5/6 bg-slate-100 rounded"></div>
          </div>
          <div className="absolute -top-4 -right-4 w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
        </div>
      </div>
    ),
    content: {
      title: "Optimisez vos articles",
      subtitle: "Améliorez la citabilité de votre contenu",
      description: "Notre optimiseur analyse la structure, l'autorité et la citabilité de vos articles pour générer un plan d'action concret.",
      features: [
        "Analyse de n'importe quelle URL",
        "Score de citabilité détaillé",
        "Plan d'action 30/60/90 jours"
      ]
    }
  },
  completed: {
    icon: CheckCircle2,
    color: "from-green-500 to-teal-500",
    illustration: (
      <div className="w-64 h-64 mx-auto flex items-center justify-center">
        <div className="relative">
          <div className="w-32 h-32 bg-gradient-to-br from-green-500 to-teal-500 rounded-full flex items-center justify-center animate-bounce-slow">
            <CheckCircle2 className="w-16 h-16 text-white" />
          </div>
          <div className="absolute -inset-4 bg-gradient-to-br from-green-500/20 to-teal-500/20 rounded-full animate-pulse"></div>
        </div>
      </div>
    ),
    content: {
      title: "Vous êtes prêt !",
      subtitle: "Commencez à optimiser votre visibilité IA",
      description: "Vous maîtrisez maintenant les bases d'IAskan. Lancez votre première analyse et découvrez comment améliorer votre présence dans les réponses générées par l'IA.",
      features: [
        "Accès complet au dashboard",
        "Support par email disponible",
        "Tutoriels avancés dans l'aide"
      ]
    }
  }
};

export default function OnboardingModal({ isOpen, onClose, onComplete }) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState('welcome');
  const [completedSteps, setCompletedSteps] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchOnboardingStatus();
    }
  }, [isOpen]);

  const fetchOnboardingStatus = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/onboarding/status`, {
        withCredentials: true
      });
      setCurrentStep(response.data.onboarding.current_step);
      setCompletedSteps(response.data.onboarding.completed_steps || []);
    } catch (err) {
      console.error('Error fetching onboarding:', err);
    }
  };

  const completeStep = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/onboarding/step/${currentStep}/complete`,
        {},
        { withCredentials: true }
      );
      setCurrentStep(response.data.current_step);
      setCompletedSteps(response.data.completed_steps);
      
      if (response.data.current_step === 'completed') {
        onComplete?.();
      }
    } catch (err) {
      console.error('Error completing step:', err);
    } finally {
      setLoading(false);
    }
  };

  const skipOnboarding = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/onboarding/skip`, {}, { withCredentials: true });
      onClose?.();
    } catch (err) {
      console.error('Error skipping:', err);
    }
  };

  const handleAction = () => {
    // Navigate to relevant page based on step
    const actions = {
      welcome: () => completeStep(),
      create_project: () => { onClose(); navigate('/projects'); },
      first_scan: () => { onClose(); navigate('/analysis'); },
      explore_results: () => { onClose(); navigate('/dashboard'); },
      article_optimizer: () => { onClose(); navigate('/article-optimizer'); },
      completed: () => { onClose(); onComplete?.(); }
    };
    
    actions[currentStep]?.();
  };

  if (!isOpen) return null;

  const stepConfig = STEP_CONFIG[currentStep] || STEP_CONFIG.welcome;
  const steps = ['welcome', 'create_project', 'first_scan', 'explore_results', 'article_optimizer', 'completed'];
  const currentIndex = steps.indexOf(currentStep);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden">
        {/* Header */}
        <div className={`bg-gradient-to-r ${stepConfig.color} p-4 flex items-center justify-between`}>
          <div className="flex items-center gap-3">
            <stepConfig.icon className="w-6 h-6 text-white" />
            <span className="text-white font-semibold">
              Étape {currentIndex + 1} sur {steps.length}
            </span>
          </div>
          <button
            onClick={skipOnboarding}
            className="text-white/80 hover:text-white transition-colors"
            data-testid="skip-onboarding"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 py-4 bg-slate-50">
          {steps.map((step, i) => (
            <div
              key={step}
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                i === currentIndex
                  ? 'bg-violet-500'
                  : completedSteps.includes(step)
                  ? 'bg-green-500'
                  : 'bg-slate-300'
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Illustration */}
          <div className="mb-6">
            {stepConfig.illustration}
          </div>

          {/* Text content */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              {stepConfig.content.title}
            </h2>
            <p className={`text-lg font-medium bg-gradient-to-r ${stepConfig.color} bg-clip-text text-transparent mb-4`}>
              {stepConfig.content.subtitle}
            </p>
            <p className="text-slate-600 max-w-md mx-auto">
              {stepConfig.content.description}
            </p>
          </div>

          {/* Features list */}
          <div className="bg-slate-50 rounded-xl p-4 mb-8">
            <ul className="space-y-2">
              {stepConfig.content.features.map((feature, i) => (
                <li key={i} className="flex items-center gap-3 text-slate-700">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            {currentIndex > 0 && currentStep !== 'completed' && (
              <button
                onClick={() => setCurrentStep(steps[currentIndex - 1])}
                className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-slate-900 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Précédent
              </button>
            )}
            
            <button
              onClick={handleAction}
              disabled={loading}
              className={`flex-1 py-3 rounded-xl font-semibold text-white bg-gradient-to-r ${stepConfig.color} hover:opacity-90 transition-opacity flex items-center justify-center gap-2`}
              data-testid="onboarding-action"
            >
              {currentStep === 'completed' ? (
                <>
                  Commencer
                  <Rocket className="w-5 h-5" />
                </>
              ) : currentStep === 'welcome' ? (
                <>
                  C'est parti !
                  <Play className="w-5 h-5" />
                </>
              ) : (
                <>
                  {['create_project', 'first_scan', 'explore_results', 'article_optimizer'].includes(currentStep) 
                    ? 'Aller à cette section' 
                    : 'Suivant'}
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>

          {/* Skip link */}
          {currentStep !== 'completed' && (
            <button
              onClick={skipOnboarding}
              className="w-full mt-4 text-sm text-slate-400 hover:text-slate-600 transition-colors"
            >
              Passer le tutoriel
            </button>
          )}
        </div>
      </div>

      <style>{`
        @keyframes grow-bar {
          from { height: 0; }
          to { height: var(--target-height, 50%); }
        }
        .animate-grow-bar {
          animation: grow-bar 0.8s ease-out forwards;
        }
        .animation-delay-200 { animation-delay: 0.2s; }
        .animation-delay-300 { animation-delay: 0.3s; }
        .animation-delay-600 { animation-delay: 0.6s; }
        .animate-bounce-slow {
          animation: bounce 2s infinite;
        }
      `}</style>
    </div>
  );
}
