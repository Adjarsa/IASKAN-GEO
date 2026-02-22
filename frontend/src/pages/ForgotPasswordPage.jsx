import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Logo from "@/components/Logo";
import { ArrowLeft, Mail, CheckCircle, Loader2 } from "lucide-react";
import { API } from "@/App";
import axios from "axios";
import { toast } from "sonner";

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error("Veuillez entrer votre adresse email");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/forgot-password`, { email }, { withCredentials: true });
      setSent(true);
      toast.success("Email envoyé !");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'envoi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-violet-200/30 to-cyan-200/30 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-cyan-200/30 to-violet-200/30 rounded-full blur-3xl" />
      
      {/* Back to Login */}
      <div className="absolute top-6 left-6 z-10">
        <Link to="/login" className="flex items-center gap-2 text-slate-500 hover:text-violet-600 transition-colors" data-testid="back-login">
          <ArrowLeft className="w-4 h-4" />
          Retour à la connexion
        </Link>
      </div>

      <div className="flex items-center justify-center min-h-screen px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-md w-full"
        >
          {/* Logo */}
          <div className="mb-8 text-center">
            <Logo size="large" />
          </div>

          {sent ? (
            /* Success State */
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100 text-center">
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-3">
                Email envoyé !
              </h1>
              <p className="text-slate-600 mb-6">
                Si un compte existe avec l'adresse <strong>{email}</strong>, vous recevrez un lien de réinitialisation dans quelques minutes.
              </p>
              <p className="text-sm text-slate-500 mb-6">
                N'oubliez pas de vérifier vos spams.
              </p>
              <Link to="/login">
                <Button variant="outline" className="w-full" data-testid="back-to-login-btn">
                  Retour à la connexion
                </Button>
              </Link>
            </div>
          ) : (
            /* Form State */
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100">
              <h1 className="text-2xl font-bold text-slate-900 mb-3 text-center">
                Mot de passe oublié ?
              </h1>
              <p className="text-slate-600 text-center mb-8">
                Entrez votre email pour recevoir un lien de réinitialisation.
              </p>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Adresse email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <Input
                      type="email"
                      placeholder="vous@exemple.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10"
                      data-testid="email-input"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-700 hover:to-cyan-700"
                  data-testid="submit-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Envoi en cours...
                    </>
                  ) : (
                    "Envoyer le lien"
                  )}
                </Button>
              </form>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
