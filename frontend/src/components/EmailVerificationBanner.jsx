/**
 * Email Verification Banner
 * Shows when user's email is not verified
 */

import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Mail, AlertTriangle, Loader2, CheckCircle, X } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const EmailVerificationBanner = ({ user, onVerified }) => {
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Don't show if already verified or dismissed
  if (!user || user.email_verified || dismissed) {
    return null;
  }

  const resendVerification = async () => {
    setSending(true);
    try {
      await axios.post(
        `${API}/auth/resend-verification`,
        {},
        { withCredentials: true }
      );
      setSent(true);
      toast.success("Email de vérification envoyé !");
    } catch (error) {
      console.error("Resend error:", error);
      if (error.response?.status === 429) {
        toast.error("Trop de demandes. Veuillez attendre avant de réessayer.");
      } else {
        toast.error("Erreur lors de l'envoi. Veuillez réessayer.");
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-full bg-amber-100">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-amber-900">
            Vérifiez votre adresse email
          </h3>
          <p className="text-sm text-amber-800 mt-1">
            Pour accéder à votre essai gratuit, veuillez confirmer votre adresse email : <strong>{user.email}</strong>
          </p>
          <p className="text-xs text-amber-600 mt-2">
            Un email de vérification a été envoyé lors de votre inscription. Vérifiez votre boîte de réception (et les spams).
          </p>
          
          <div className="flex items-center gap-3 mt-4">
            {sent ? (
              <div className="flex items-center gap-2 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Email envoyé ! Vérifiez votre boîte de réception.</span>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={resendVerification}
                disabled={sending}
                className="border-amber-300 text-amber-700 hover:bg-amber-100"
              >
                {sending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Envoi...
                  </>
                ) : (
                  <>
                    <Mail className="w-4 h-4 mr-2" />
                    Renvoyer l'email
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="p-1 rounded hover:bg-amber-100 text-amber-600"
          title="Masquer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default EmailVerificationBanner;
