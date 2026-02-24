import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Logo from "@/components/Logo";
import { ArrowLeft, Lock, CheckCircle, Loader2, Eye, EyeOff } from "lucide-react";
import { API } from "@/App";
import axios from "axios";
import { toast } from "sonner";

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password.length < 8) {
      toast.error("Le mot de passe doit contenir au moins 8 caractères");
      return;
    }
    
    if (password !== confirmPassword) {
      toast.error("Les mots de passe ne correspondent pas");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: password
      }, { withCredentials: true });
      setSuccess(true);
      toast.success("Mot de passe mis à jour !");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la réinitialisation");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">Lien invalide</h1>
          <p className="text-slate-600 mb-6">Ce lien de réinitialisation est invalide ou a expiré.</p>
          <Link to="/forgot-password">
            <Button>Demander un nouveau lien</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-violet-200/30 to-cyan-200/30 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-cyan-200/30 to-violet-200/30 rounded-full blur-3xl" />
      
      {/* Back to Login */}
      <div className="absolute top-6 left-6 z-10">
        <Link to="/login" className="flex items-center gap-2 text-slate-600 hover:text-violet-600 transition-colors">
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

          {success ? (
            /* Success State */
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100 text-center">
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-3">
                Mot de passe mis à jour !
              </h1>
              <p className="text-slate-600 mb-6">
                Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.
              </p>
              <Button 
                onClick={() => navigate("/login")}
                className="w-full bg-gradient-to-r from-violet-600 to-cyan-600"
                data-testid="go-to-login-btn"
              >
                Se connecter
              </Button>
            </div>
          ) : (
            /* Form State */
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100">
              <h1 className="text-2xl font-bold text-slate-900 mb-3 text-center">
                Nouveau mot de passe
              </h1>
              <p className="text-slate-600 text-center mb-8">
                Choisissez un mot de passe sécurisé.
              </p>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Nouveau mot de passe
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-600" />
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="Minimum 8 caractères"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 pr-10"
                      data-testid="password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-600"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Confirmer le mot de passe
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-600" />
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="Répétez le mot de passe"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="pl-10"
                      data-testid="confirm-password-input"
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
                    <span className="flex items-center">
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Mise à jour...
                    </span>
                  ) : (
                    "Mettre à jour le mot de passe"
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

export default ResetPasswordPage;
