import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { 
  Brain, 
  BarChart3, 
  Target, 
  Zap, 
  Shield, 
  Globe2, 
  CheckCircle2, 
  ArrowRight,
  Sparkles,
  TrendingUp,
  Users,
  Award
} from "lucide-react";

const LandingPage = () => {
  const [email, setEmail] = useState("");

  const handleWaitlist = (e) => {
    e.preventDefault();
    // Handle waitlist signup
    alert(`Merci ! ${email} a été ajouté à la liste d'attente.`);
    setEmail("");
  };

  const features = [
    {
      icon: Brain,
      title: "Score R.A.T.E™ Propriétaire",
      description: "Notre algorithme exclusif mesure Relevance, Authority, Truthfulness et Endorsement pour un score GEO précis."
    },
    {
      icon: Globe2,
      title: "Analyse Multi-IA",
      description: "Interrogez ChatGPT, Claude, Gemini et Perplexity simultanément pour une vue complète de votre visibilité."
    },
    {
      icon: Target,
      title: "Benchmark Concurrentiel",
      description: "Comparez vos performances avec vos concurrents et identifiez les opportunités de domination."
    },
    {
      icon: Sparkles,
      title: "Recommandations Actionnables",
      description: "Recevez des actions prioritaires avec estimation d'impact pour améliorer votre score GEO."
    },
    {
      icon: BarChart3,
      title: "Rapports Détaillés",
      description: "Générez des rapports exécutifs et audits techniques pour vos équipes et clients."
    },
    {
      icon: Zap,
      title: "Intelligence Stratégique",
      description: "Détectez les tendances émergentes et les opportunités invisibles avant vos concurrents."
    }
  ];

  const plans = [
    {
      name: "Starter",
      price: "79",
      queries: "300",
      features: [
        "Score GEO basique",
        "ChatGPT uniquement",
        "Rapport standard",
        "Support email"
      ],
      popular: false
    },
    {
      name: "Pro",
      price: "149",
      queries: "600",
      features: [
        "Score GEO avancé",
        "Multi-IA (4 moteurs)",
        "Benchmark concurrents",
        "Analyse de stabilité",
        "Support prioritaire"
      ],
      popular: true
    },
    {
      name: "Business",
      price: "349",
      queries: "1500",
      features: [
        "Score GEO complet",
        "Toutes les IA",
        "Génération d'articles GEO",
        "Intelligence stratégique",
        "API access",
        "Support dédié"
      ],
      popular: false
    }
  ];

  const stats = [
    { value: "98%", label: "Précision du score" },
    { value: "4+", label: "Moteurs IA analysés" },
    { value: "24h", label: "Premiers résultats" },
    { value: "40%", label: "Amélioration moyenne" }
  ];

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Hero Background Glow */}
      <div className="absolute inset-0 hero-glow pointer-events-none" />
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">IAskan</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-muted-foreground hover:text-white transition-colors">Fonctionnalités</a>
            <a href="#pricing" className="text-muted-foreground hover:text-white transition-colors">Tarifs</a>
            <Link to="/login" className="text-muted-foreground hover:text-white transition-colors" data-testid="nav-login">Connexion</Link>
            <Link to="/login">
              <Button className="rounded-full glow-primary" data-testid="nav-cta">
                Essai Gratuit
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-4xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-8">
              <Sparkles className="w-4 h-4" />
              La première plateforme GEO pour l'Europe
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold text-white leading-tight mb-6">
              Dominez les réponses<br />
              <span className="text-gradient">de l'Intelligence Artificielle</span>
            </h1>
            
            <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
              IAskan analyse votre visibilité dans ChatGPT, Claude, Gemini et Perplexity. 
              Optimisez votre présence pour être recommandé par les IA.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/login">
                <Button size="lg" className="rounded-full px-8 glow-primary text-lg h-14" data-testid="hero-cta">
                  Commencer Gratuitement
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="rounded-full px-8 text-lg h-14" data-testid="hero-demo">
                Voir une démo
              </Button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20"
          >
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Problem/Solution Section */}
      <section className="py-20 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="glass rounded-2xl p-8">
              <div className="text-destructive text-sm font-semibold mb-4">AVANT</div>
              <h3 className="text-2xl font-bold text-white mb-4">SEO Classique</h3>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <span className="text-destructive">✗</span>
                  Optimisation pour Google uniquement
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-destructive">✗</span>
                  Invisible dans les réponses IA
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-destructive">✗</span>
                  Perte de trafic vers ChatGPT
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-destructive">✗</span>
                  Aucune mesure de visibilité IA
                </li>
              </ul>
            </div>
            
            <div className="glass rounded-2xl p-8 border-primary/30">
              <div className="text-success text-sm font-semibold mb-4">APRÈS</div>
              <h3 className="text-2xl font-bold text-white mb-4">GEO avec IAskan</h3>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
                  Visibilité sur tous les moteurs IA
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
                  Recommandé dans les réponses IA
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
                  Score GEO mesurable et actionnable
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
                  Avantage concurrentiel stratégique
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              La plateforme GEO complète
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Tout ce dont vous avez besoin pour dominer la visibilité IA
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="glass p-6 h-full card-hover">
                  <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Comment ça marche</h2>
            <p className="text-xl text-muted-foreground">3 étapes pour dominer les IA</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "1", title: "Analysez", description: "Lancez une analyse de votre marque sur tous les moteurs IA", icon: BarChart3 },
              { step: "2", title: "Optimisez", description: "Suivez les recommandations prioritaires pour améliorer votre score", icon: TrendingUp },
              { step: "3", title: "Dominez", description: "Devenez la référence recommandée par les IA", icon: Award }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center mx-auto mb-6">
                  <item.icon className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">{item.title}</h3>
                <p className="text-muted-foreground">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Tarifs simples et transparents</h2>
            <p className="text-xl text-muted-foreground">7 jours d'essai gratuit sur tous les plans</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans.map((plan, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className={`pricing-card h-full ${plan.popular ? 'featured' : ''}`}>
                  {plan.popular && <div className="pricing-badge">Populaire</div>}
                  
                  <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-5xl font-bold text-white">{plan.price}€</span>
                    <span className="text-muted-foreground">/mois</span>
                  </div>
                  <p className="text-muted-foreground mb-6">{plan.queries} requêtes/mois</p>
                  
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, fIndex) => (
                      <li key={fIndex} className="flex items-start gap-3 text-muted-foreground">
                        <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  
                  <Link to="/login">
                    <Button 
                      className={`w-full rounded-full ${plan.popular ? 'glow-primary' : ''}`}
                      variant={plan.popular ? 'default' : 'outline'}
                      data-testid={`pricing-${plan.name.toLowerCase()}-cta`}
                    >
                      Commencer l'essai gratuit
                    </Button>
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="glass rounded-3xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-accent/20 pointer-events-none" />
            <div className="relative">
              <h2 className="text-4xl font-bold text-white mb-4">
                Prêt à dominer les réponses IA ?
              </h2>
              <p className="text-xl text-muted-foreground mb-8">
                Rejoignez les entreprises qui optimisent leur visibilité GEO
              </p>
              <Link to="/login">
                <Button size="lg" className="rounded-full px-10 glow-primary text-lg h-14" data-testid="cta-final">
                  Démarrer Maintenant
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-border">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-white">IAskan</span>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <a href="#" className="hover:text-white transition-colors">Mentions légales</a>
              <a href="#" className="hover:text-white transition-colors">Politique de confidentialité</a>
              <a href="#" className="hover:text-white transition-colors">CGV</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
            
            <div className="text-sm text-muted-foreground">
              © 2025 IAskan. Tous droits réservés.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
