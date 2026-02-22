import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Logo from "@/components/Logo";
import { ArrowLeft, Mail, Loader2, CheckCircle } from "lucide-react";
import { API } from "@/App";
import { toast } from "sonner";
import axios from "axios";

// Magic Link Form Component
const MagicLinkForm = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error("Veuillez entrer votre email");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/magic-link`, { email }, { withCredentials: true });
      setSent(true);
      toast.success("Lien de connexion envoyé !");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'envoi");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="bg-emerald-50 rounded-lg p-4 text-center">
        <CheckCircle className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
        <p className="text-emerald-700 text-sm">
          Lien de connexion envoyé à <strong>{email}</strong>
        </p>
        <p className="text-emerald-600 text-xs mt-1">
          Vérifiez votre boîte mail.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative">
        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          type="email"
          placeholder="Connexion par email (Magic Link)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="pl-10 h-11"
          data-testid="magic-link-email"
        />
      </div>
      <Button
        type="submit"
        variant="outline"
        disabled={loading}
        className="w-full"
        data-testid="magic-link-submit"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Envoi...
          </>
        ) : (
          "Recevoir un lien de connexion"
        )}
      </Button>
    </form>
  );
};

const LoginPage = () => {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const error = searchParams.get("error");
    if (error) {
      const errorMessages = {
        "microsoft_auth_failed": "Échec de l'authentification Microsoft",
        "linkedin_auth_failed": "Échec de l'authentification LinkedIn",
        "invalid_state": "Session de connexion invalide. Veuillez réessayer.",
        "token_exchange_failed": "Erreur lors de l'échange de token",
        "user_info_failed": "Impossible de récupérer les informations utilisateur"
      };
      toast.error(errorMessages[error] || "Erreur de connexion");
    }
  }, [searchParams]);

  const handleGoogleLogin = () => {
    // Redirect to projects page after auth (user must select project first)
    const redirectUrl = window.location.origin + '/projects';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleMicrosoftLogin = () => {
    // Redirect to Microsoft OAuth endpoint
    window.location.href = `${API}/auth/microsoft/login`;
  };

  const handleLinkedInLogin = () => {
    // Redirect to LinkedIn OAuth endpoint
    window.location.href = `${API}/auth/linkedin/login`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-violet-200/30 to-cyan-200/30 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-cyan-200/30 to-violet-200/30 rounded-full blur-3xl" />
      
      {/* Back to Home */}
      <div className="absolute top-6 left-6 z-10">
        <Link to="/" className="flex items-center gap-2 text-slate-500 hover:text-violet-600 transition-colors" data-testid="back-home">
          <ArrowLeft className="w-4 h-4" />
          Retour
        </Link>
      </div>

      <div className="auth-container">
        {/* Login Form Side */}
        <div className="auth-form-side">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-md mx-auto w-full"
          >
            {/* Logo */}
            <div className="mb-12">
              <Logo size="large" />
            </div>

            {/* Title */}
            <h1 className="text-3xl font-bold text-slate-900 mb-3">
              Bienvenue
            </h1>
            <p className="text-slate-600 mb-10">
              Connectez-vous pour accéder à votre dashboard GEO
            </p>

            {/* SSO Buttons */}
            <div className="space-y-4">
              <Button 
                className="sso-button google"
                onClick={handleGoogleLogin}
                data-testid="login-google"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#EA4335" d="M5.26620003,9.76452941 C6.19878754,6.93863203 8.85444915,4.90909091 12,4.90909091 C13.6909091,4.90909091 15.2181818,5.50909091 16.4181818,6.49090909 L19.9090909,3 C17.7818182,1.14545455 15.0545455,0 12,0 C7.27006974,0 3.1977497,2.69829785 1.23999023,6.65002441 L5.26620003,9.76452941 Z"/>
                  <path fill="#34A853" d="M16.0407269,18.0125889 C14.9509167,18.7163016 13.5660892,19.0909091 12,19.0909091 C8.86648613,19.0909091 6.21911939,17.076871 5.27698177,14.2678769 L1.23746264,17.3349879 C3.19279051,21.2936293 7.26500293,24 12,24 C14.9328362,24 17.7353462,22.9573905 19.834192,20.9995801 L16.0407269,18.0125889 Z"/>
                  <path fill="#4A90E2" d="M19.834192,20.9995801 C22.0291676,18.9520994 23.4545455,15.903663 23.4545455,12 C23.4545455,11.2909091 23.3454545,10.5272727 23.1818182,9.81818182 L12,9.81818182 L12,14.4545455 L18.4363636,14.4545455 C18.1187732,16.013626 17.2662994,17.2212117 16.0407269,18.0125889 L19.834192,20.9995801 Z"/>
                  <path fill="#FBBC05" d="M5.27698177,14.2678769 C5.03832634,13.556323 4.90909091,12.7937589 4.90909091,12 C4.90909091,11.2182781 5.03443647,10.4668121 5.26620003,9.76452941 L1.23999023,6.65002441 C0.43658717,8.26043162 0,10.0753848 0,12 C0,13.9195484 0.444780743,15.7301709 1.23746264,17.3349879 L5.27698177,14.2678769 Z"/>
                </svg>
                Continuer avec Google
              </Button>

              <Button 
                className="sso-button microsoft"
                onClick={handleMicrosoftLogin}
                data-testid="login-microsoft"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#F25022" d="M0 0h11.377v11.377H0z"/>
                  <path fill="#00A4EF" d="M0 12.623h11.377V24H0z"/>
                  <path fill="#7FBA00" d="M12.623 0H24v11.377H12.623z"/>
                  <path fill="#FFB900" d="M12.623 12.623H24V24H12.623z"/>
                </svg>
                Continuer avec Microsoft
              </Button>

              <Button 
                className="sso-button linkedin"
                onClick={handleLinkedInLogin}
                data-testid="login-linkedin"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#0A66C2">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                Continuer avec LinkedIn
              </Button>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-4 my-8">
              <div className="flex-1 h-px bg-slate-200" />
              <span className="text-slate-400 text-sm">ou</span>
              <div className="flex-1 h-px bg-slate-200" />
            </div>

            {/* Magic Link */}
            <MagicLinkForm />

            {/* Forgot Password Link */}
            <div className="text-center mt-4">
              <Link 
                to="/forgot-password" 
                className="text-sm text-violet-600 hover:text-violet-700 hover:underline"
                data-testid="forgot-password-link"
              >
                Mot de passe oublié ?
              </Link>
            </div>

            {/* Terms */}
            <p className="text-xs text-slate-400 text-center mt-10">
              En vous connectant, vous acceptez nos{" "}
              <a href="#" className="text-violet-600 hover:underline">Conditions d'utilisation</a>
              {" "}et notre{" "}
              <a href="#" className="text-violet-600 hover:underline">Politique de confidentialité</a>
            </p>
          </motion.div>
        </div>

        {/* Visual Side */}
        <div className="auth-visual-side hidden lg:flex">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="relative"
          >
            <div className="w-96 h-96 rounded-3xl bg-white shadow-2xl shadow-violet-500/10 p-8 relative overflow-hidden border border-slate-100">
              <div className="absolute inset-0 bg-gradient-to-br from-violet-50 to-cyan-50" />
              <div className="relative h-full flex flex-col justify-center">
                <div className="text-6xl font-bold text-gradient mb-4">87</div>
                <div className="text-xl text-slate-700 mb-6">Score GEO Global</div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">ChatGPT</span>
                    <span className="text-emerald-600 font-semibold">92</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-emerald-500" style={{ width: '92%' }} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Claude</span>
                    <span className="text-violet-600 font-semibold">85</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-violet-500" style={{ width: '85%' }} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Gemini</span>
                    <span className="text-cyan-600 font-semibold">78</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-cyan-500" style={{ width: '78%' }} />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Floating elements */}
            <div className="absolute -top-4 -right-4 w-20 h-20 rounded-xl bg-white shadow-lg border border-slate-100 flex items-center justify-center">
              <span className="text-2xl font-bold text-emerald-600">+12%</span>
            </div>
            <div className="absolute -bottom-4 -left-4 w-24 h-16 rounded-xl bg-white shadow-lg border border-slate-100 flex items-center justify-center">
              <span className="text-sm text-violet-600 font-semibold">R.A.T.E™</span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
