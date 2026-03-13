import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { useAuth, API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Logo from "@/components/Logo";
import {
  CheckCircle2,
  Loader2,
  Sparkles,
  ArrowRight,
  XCircle,
  RefreshCw
} from "lucide-react";

const CheckoutSuccessPage = () => {
  const { user, refreshSubscription } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("loading"); // loading, success, error
  const [message, setMessage] = useState("");
  const [planName, setPlanName] = useState("");

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    
    if (sessionId) {
      verifyPayment(sessionId);
    } else {
      setStatus("error");
      setMessage("Session de paiement non trouvée");
    }
  }, [searchParams]);

  const verifyPayment = async (sessionId) => {
    try {
      const response = await axios.get(
        `${API}/checkout/status/${sessionId}`,
        { withCredentials: true }
      );

      if (response.data.status === "complete" || response.data.payment_status === "paid") {
        setStatus("success");
        setMessage("Votre paiement a été confirmé !");
        
        // Refresh subscription to get updated plan
        if (refreshSubscription) {
          await refreshSubscription();
        }
        
        // Try to get plan name from response
        setPlanName(response.data.plan || "Pro");
      } else if (response.data.payment_status === "unpaid") {
        setStatus("loading");
        setMessage("Paiement en cours de traitement...");
        // Retry after 3 seconds
        setTimeout(() => verifyPayment(sessionId), 3000);
      } else {
        setStatus("error");
        setMessage("Le paiement n'a pas pu être vérifié");
      }
    } catch (error) {
      console.error("Payment verification error:", error);
      setStatus("error");
      setMessage(error.response?.data?.detail || "Erreur lors de la vérification du paiement");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex flex-col">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" data-testid="checkout-logo">
            <Logo />
          </Link>
        </div>
      </nav>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <Card className="max-w-lg w-full p-8 text-center">
          {status === "loading" && (
            <>
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-violet-100 flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-violet-600 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-2">
                Vérification du paiement...
              </h1>
              <p className="text-slate-600">
                {message || "Merci de patienter quelques instants"}
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-emerald-100 to-cyan-100 flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-emerald-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-2">
                Paiement réussi !
              </h1>
              <p className="text-slate-600 mb-2">
                {message}
              </p>
              {planName && (
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-violet-100 text-violet-700 rounded-full mb-6">
                  <Sparkles className="w-4 h-4" />
                  <span className="font-semibold">Plan {planName} activé</span>
                </div>
              )}
              
              <div className="space-y-4 mt-6">
                <div className="p-4 bg-slate-50 rounded-lg text-left">
                  <h3 className="font-semibold text-slate-900 mb-2">Prochaines étapes :</h3>
                  <ul className="space-y-2 text-sm text-slate-600">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span>Votre quota a été mis à jour</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span>Accès à toutes les fonctionnalités du plan</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span>Un email de confirmation vous a été envoyé</span>
                    </li>
                  </ul>
                </div>

                <Button
                  onClick={() => navigate("/dashboard")}
                  className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
                  data-testid="go-dashboard-btn"
                >
                  Accéder au dashboard
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </>
          )}

          {status === "error" && (
            <>
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
                <XCircle className="w-10 h-10 text-red-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-2">
                Erreur de paiement
              </h1>
              <p className="text-slate-600 mb-6">
                {message}
              </p>
              
              <div className="space-y-3">
                <Button
                  onClick={() => navigate("/pricing")}
                  variant="outline"
                  className="w-full"
                  data-testid="retry-payment-btn"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Réessayer
                </Button>
                <Button
                  onClick={() => navigate("/dashboard")}
                  variant="ghost"
                  className="w-full"
                >
                  Retour au dashboard
                </Button>
              </div>

              <p className="mt-6 text-sm text-slate-500">
                Besoin d'aide ?{" "}
                <a href="mailto:support@iaskan.com" className="text-violet-600 hover:underline">
                  Contactez le support
                </a>
              </p>
            </>
          )}
        </Card>
      </div>
    </div>
  );
};

export default CheckoutSuccessPage;
