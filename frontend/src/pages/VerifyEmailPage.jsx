/**
 * Email Verification Page
 * Handles email verification token validation
 */

import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  CheckCircle,
  XCircle,
  Loader2,
  Mail,
  ArrowRight,
  RefreshCw
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  
  const [status, setStatus] = useState("loading"); // loading, success, error
  const [errorMessage, setErrorMessage] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMessage("Lien de vérification invalide. Aucun token trouvé.");
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await axios.post(
          `${API}/auth/verify-email`,
          { token },
          { withCredentials: true }
        );
        
        setEmail(response.data.email);
        setStatus("success");
        toast.success("Email vérifié avec succès !");
      } catch (error) {
        console.error("Verification error:", error);
        setStatus("error");
        setErrorMessage(
          error.response?.data?.detail || 
          "Erreur lors de la vérification. Le lien est peut-être expiré."
        );
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="max-w-md w-full p-8">
        {/* Loading State */}
        {status === "loading" && (
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-violet-100 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-violet-600 animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">
              Vérification en cours...
            </h1>
            <p className="text-slate-600">
              Veuillez patienter pendant que nous vérifions votre adresse email.
            </p>
          </div>
        )}

        {/* Success State */}
        {status === "success" && (
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-emerald-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">
              Email Vérifié !
            </h1>
            <p className="text-slate-600 mb-2">
              Votre adresse email a été vérifiée avec succès.
            </p>
            {email && (
              <p className="text-sm text-violet-600 font-medium mb-6">
                {email}
              </p>
            )}
            <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200 mb-6">
              <p className="text-sm text-emerald-800">
                🎉 Vous pouvez maintenant utiliser votre <strong>essai gratuit</strong> pour analyser votre site !
              </p>
            </div>
            <Button
              onClick={() => navigate("/projects")}
              className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
            >
              Accéder à IAskan
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        )}

        {/* Error State */}
        {status === "error" && (
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
              <XCircle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">
              Vérification échouée
            </h1>
            <p className="text-slate-600 mb-6">
              {errorMessage}
            </p>
            <div className="space-y-3">
              <Button
                onClick={() => navigate("/login")}
                className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
              >
                Se connecter
              </Button>
              <p className="text-sm text-slate-500">
                Connectez-vous pour demander un nouveau lien de vérification.
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-slate-200 text-center">
          <Link to="/" className="text-sm text-slate-500 hover:text-violet-600">
            ← Retour à l'accueil
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default VerifyEmailPage;
