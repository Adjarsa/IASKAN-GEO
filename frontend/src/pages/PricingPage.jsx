import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Brain,
  CheckCircle2,
  ArrowLeft,
  Loader2,
  Sparkles,
  Zap,
  Crown
} from "lucide-react";

const PricingPage = () => {
  const { user, subscription, refreshSubscription } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(null);

  useEffect(() => {
    // Check for payment cancelled
    const paymentStatus = searchParams.get("payment");
    if (paymentStatus === "cancelled") {
      toast.info("Paiement annulé");
    }
  }, [searchParams]);

  const handleCheckout = async (plan) => {
    if (!user) {
      navigate("/login");
      return;
    }

    if (subscription?.plan === plan && subscription?.status === "active") {
      toast.info("Vous avez déjà ce plan");
      return;
    }

    setLoading(plan);
    try {
      const response = await axios.post(
        `${API}/checkout/create`,
        {
          plan,
          origin_url: window.location.origin
        },
        { withCredentials: true }
      );

      // Redirect to Stripe
      window.location.href = response.data.url;
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de la création du paiement");
      setLoading(null);
    }
  };

  const plans = [
    {
      id: "starter",
      name: "Starter",
      price: 79,
      icon: Zap,
      queries: "300 requêtes/mois",
      features: [
        "Score GEO basique",
        "ChatGPT uniquement",
        "Rapport standard",
        "1 projet",
        "Support email"
      ],
      popular: false
    },
    {
      id: "pro",
      name: "Pro",
      price: 149,
      icon: Sparkles,
      queries: "600 requêtes/mois",
      features: [
        "Score GEO avancé",
        "Multi-IA (ChatGPT, Claude, Gemini, Perplexity)",
        "Benchmark concurrents",
        "Analyse de stabilité",
        "5 projets",
        "Support prioritaire"
      ],
      popular: true
    },
    {
      id: "business",
      name: "Business",
      price: 349,
      icon: Crown,
      queries: "1500 requêtes/mois",
      features: [
        "Score GEO complet",
        "Toutes les IA",
        "Génération d'articles GEO (20/mois)",
        "Intelligence stratégique",
        "Projets illimités",
        "API access",
        "Support dédié"
      ],
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Background */}
      <div className="absolute inset-0 hero-glow pointer-events-none" />

      {/* Navigation */}
      <nav className="sticky top-0 z-50 glass border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2" data-testid="pricing-logo">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">IAskan</span>
          </Link>

          {user ? (
            <Button variant="ghost" onClick={() => navigate("/dashboard")} data-testid="back-dashboard">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour au dashboard
            </Button>
          ) : (
            <Link to="/login">
              <Button variant="outline" data-testid="pricing-login">
                Connexion
              </Button>
            </Link>
          )}
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-16 relative">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Tarifs simples et transparents
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            7 jours d'essai gratuit sur tous les plans. Annulez à tout moment.
          </p>
        </div>

        {/* Current Plan Info */}
        {user && subscription && (
          <Card className="glass p-4 mb-8 max-w-md mx-auto text-center">
            <p className="text-muted-foreground">
              Votre plan actuel :{" "}
              <span className="text-white font-semibold">
                {subscription.plan?.charAt(0).toUpperCase() + subscription.plan?.slice(1)}
              </span>
              {subscription.status === "trial" && (
                <span className="ml-2 text-warning">(Essai gratuit)</span>
              )}
            </p>
          </Card>
        )}

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => {
            const isCurrentPlan = subscription?.plan === plan.id;
            const Icon = plan.icon;

            return (
              <Card
                key={plan.id}
                className={`relative overflow-hidden ${
                  plan.popular
                    ? "border-primary/50 shadow-[0_0_40px_-10px_rgba(79,70,229,0.4)]"
                    : "glass"
                }`}
              >
                {plan.popular && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-primary to-accent text-white text-xs font-semibold px-4 py-1 rounded-bl-lg">
                    Populaire
                  </div>
                )}

                <div className="p-8">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      plan.popular ? "bg-primary/20" : "bg-white/5"
                    }`}>
                      <Icon className={`w-6 h-6 ${plan.popular ? "text-primary" : "text-muted-foreground"}`} />
                    </div>
                    <h3 className="text-2xl font-bold text-white">{plan.name}</h3>
                  </div>

                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-5xl font-bold text-white">{plan.price}€</span>
                    <span className="text-muted-foreground">/mois</span>
                  </div>

                  <p className="text-muted-foreground mb-6">{plan.queries}</p>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-3 text-muted-foreground">
                        <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    className={`w-full ${plan.popular ? "glow-primary" : ""}`}
                    variant={plan.popular ? "default" : "outline"}
                    disabled={loading !== null || isCurrentPlan}
                    onClick={() => handleCheckout(plan.id)}
                    data-testid={`checkout-${plan.id}`}
                  >
                    {loading === plan.id ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Chargement...
                      </>
                    ) : isCurrentPlan ? (
                      "Plan actuel"
                    ) : (
                      "Choisir ce plan"
                    )}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>

        {/* FAQ / Trust Signals */}
        <div className="mt-20 text-center">
          <p className="text-muted-foreground mb-4">
            Questions ? Contactez-nous à{" "}
            <a href="mailto:contact@iaskan.com" className="text-primary hover:underline">
              contact@iaskan.com
            </a>
          </p>
          <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground">
            <span>Paiement sécurisé par Stripe</span>
            <span>•</span>
            <span>Annulation facile</span>
            <span>•</span>
            <span>Satisfait ou remboursé</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
