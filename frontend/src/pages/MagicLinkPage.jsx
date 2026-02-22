import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Logo from "@/components/Logo";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";

const MagicLinkPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  
  const [status, setStatus] = useState("verifying"); // verifying, success, error
  const [error, setError] = useState("");

  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setStatus("error");
        setError("Lien de connexion invalide.");
        return;
      }

      try {
        await axios.get(`${API}/auth/magic-verify?token=${token}`, { withCredentials: true });
        setStatus("success");
        // Redirect after 2 seconds
        setTimeout(() => {
          navigate("/projects");
        }, 2000);
      } catch (err) {
        setStatus("error");
        setError(err.response?.data?.detail || "Ce lien est invalide ou a expiré.");
      }
    };

    verifyToken();
  }, [token, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white relative overflow-hidden flex items-center justify-center px-4">
      {/* Background decorations */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-violet-200/30 to-cyan-200/30 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-cyan-200/30 to-violet-200/30 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full"
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <Logo size="large" />
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100 text-center">
          {status === "verifying" && (
            <>
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-violet-100 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-600 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-3">
                Vérification en cours...
              </h1>
              <p className="text-slate-600">
                Nous vérifions votre lien de connexion.
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-3">
                Connexion réussie !
              </h1>
              <p className="text-slate-600 mb-4">
                Vous allez être redirigé vers votre dashboard...
              </p>
              <div className="w-full bg-slate-200 rounded-full h-1 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-violet-600 to-cyan-600"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 2 }}
                />
              </div>
            </>
          )}

          {status === "error" && (
            <>
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
                <XCircle className="w-8 h-8 text-red-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-3">
                Lien invalide
              </h1>
              <p className="text-slate-600 mb-6">
                {error}
              </p>
              <div className="space-y-3">
                <Button
                  onClick={() => navigate("/login")}
                  className="w-full bg-gradient-to-r from-violet-600 to-cyan-600"
                >
                  Retour à la connexion
                </Button>
              </div>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default MagicLinkPage;
