import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Logo from "@/components/Logo";
import {
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
        `${API}/checkout/session`,
        {
          plan,
          success_url: `${window.location.origin}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
          cancel_url: `${window.location.origin}/pricing?payment=cancelled`
        },
        { withCredentials: true }
      );

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
      queries: "1 500 requêtes/mois",
      features: [
        "10 scans/mois",
        "50 prompts/scan",
        "150 requêtes/scan (50×3×1)",
        "1 500 requêtes/mois",
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
      queries: "80 000 requêtes/mois",
      features: [
        "50 scans/mois",
        "100 prompts/scan",
        "4 runs/requête",
        "1 600 requêtes/scan (100×4×4)",
        "80 000 requêtes/mois",
        "4 IA (ChatGPT, Claude, Gemini, Perplexity)",
        "Benchmark concurrents",
        "Analyse de stabilité",
        "Scans programmés + rapport par email",
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
      queries: "600 000 requêtes/mois",
      features: [
        "150 scans/mois",
        "200 prompts/scan",
        "5 runs/requête",
        "4 000 requêtes/scan (200×5×4)",
        "600 000 requêtes/mois",
        "4 IA (ChatGPT, Claude, Gemini, Perplexity)",
        "Génération d'articles GEO",
        "Intelligence stratégique",
        "Scans programmés + rapport par email",
        "Projets illimités",
        "Support dédié"
      ],
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to={user ? "/dashboard" : "/"} data-testid="pricing-logo">
            <Logo />
          </Link>

          {user ? (
            <Button variant="ghost" onClick={() => navigate("/dashboard")} className="text-slate-600" data-testid="back-dashboard">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour au dashboard
            </Button>
          ) : (
            <Link to="/login">
              <Button variant="outline" className="border-slate-200" data-testid="pricing-login">
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
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Tarifs simples et transparents
          </h1>
          <p className="text-xl text-slate-700 max-w-2xl mx-auto">
            Choisissez le plan adapté à vos besoins. 1 scan gratuit pour démarrer.
          </p>
        </div>

        {/* Current Plan Info */}
        {user && subscription && (
          <Card className="p-4 mb-8 max-w-md mx-auto text-center bg-violet-50 border-violet-100">
            <p className="text-slate-700">
              Votre plan actuel :{" "}
              <span className="text-violet-700 font-semibold">
                {subscription.plan?.charAt(0).toUpperCase() + subscription.plan?.slice(1)}
              </span>
              {subscription.plan === "free" && (
                <span className="ml-2 text-emerald-600">(1 scan gratuit)</span>
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
                className={`relative overflow-hidden bg-white ${
                  plan.popular
                    ? "border-violet-300 shadow-xl shadow-violet-500/10"
                    : "border-slate-100"
                }`}
              >
                {plan.popular && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-violet-600 to-cyan-600 text-white text-xs font-semibold px-4 py-1 rounded-bl-lg">
                    Populaire
                  </div>
                )}
                
                {plan.badge && (
                  <div className="absolute top-0 left-0 bg-emerald-500 text-white text-xs font-semibold px-4 py-1 rounded-br-lg">
                    {plan.badge}
                  </div>
                )}

                <div className="p-8">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      plan.popular ? "bg-gradient-to-br from-violet-100 to-cyan-100" : "bg-slate-100"
                    }`}>
                      <Icon className={`w-6 h-6 ${plan.popular ? "text-violet-600" : "text-slate-600"}`} />
                    </div>
                    <h3 className="text-2xl font-bold text-slate-900">{plan.name}</h3>
                  </div>

                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-5xl font-bold text-slate-900">{plan.price}€</span>
                    <span className="text-slate-600">/mois</span>
                  </div>

                  <p className="text-slate-600 mb-6">{plan.queries}</p>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-3 text-slate-600">
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    className={`w-full rounded-full ${plan.popular ? "bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700 shadow-lg shadow-violet-500/25" : "border-slate-200"}`}
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
          <p className="text-slate-600 mb-4">
            Questions ? Contactez-nous à{" "}
            <a href="mailto:contact@iaskan.com" className="text-violet-600 hover:underline">
              contact@iaskan.com
            </a>
          </p>
          <div className="flex items-center justify-center gap-8 text-sm text-slate-600">
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
