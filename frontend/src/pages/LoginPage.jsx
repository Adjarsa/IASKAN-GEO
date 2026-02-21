import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Brain, ArrowLeft } from "lucide-react";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const LoginPage = () => {
  const handleGoogleLogin = () => {
    // Use browser's dynamic location to prevent configuration errors
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleMicrosoftLogin = () => {
    // Microsoft SSO - redirect to Google for now (can be extended)
    handleGoogleLogin();
  };

  const handleLinkedInLogin = () => {
    // LinkedIn SSO - redirect to Google for now (can be extended)
    handleGoogleLogin();
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute inset-0 hero-glow pointer-events-none" />
      
      {/* Back to Home */}
      <div className="absolute top-6 left-6 z-10">
        <Link to="/" className="flex items-center gap-2 text-muted-foreground hover:text-white transition-colors" data-testid="back-home">
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
            <div className="flex items-center gap-3 mb-12">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">IAskan</span>
            </div>

            {/* Title */}
            <h1 className="text-3xl font-bold text-white mb-3">
              Bienvenue
            </h1>
            <p className="text-muted-foreground mb-10">
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
                  <path fill="#FBBC05" d="M5.27698177,14.2678769 C5.03832634,13.556323 4.90909091,12.7937589 4.90909091,12 C4.90909091,11.2182781 5.03443647,10.4668121 5.26620003,9.76452941 L1.23999023,6.65002441 C0.43658717,8.26043162 0,10.0753848 0,12 C0,13.9195484 0.444780743,15.7## L1.23746264,17.3349879 L5.27698177,14.2678769 Z"/>
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
              <div className="flex-1 h-px bg-border" />
              <span className="text-muted-foreground text-sm">ou</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* Magic Link - Disabled for now */}
            <div className="text-center text-muted-foreground text-sm">
              <p>Connexion via Magic Link bientôt disponible</p>
            </div>

            {/* Terms */}
            <p className="text-xs text-muted-foreground text-center mt-10">
              En vous connectant, vous acceptez nos{" "}
              <a href="#" className="text-primary hover:underline">Conditions d'utilisation</a>
              {" "}et notre{" "}
              <a href="#" className="text-primary hover:underline">Politique de confidentialité</a>
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
            <div className="w-96 h-96 rounded-3xl glass p-8 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-accent/20" />
              <div className="relative h-full flex flex-col justify-center">
                <div className="text-6xl font-bold text-white mb-4">87</div>
                <div className="text-xl text-white/80 mb-6">Score GEO Global</div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-white/60">ChatGPT</span>
                    <span className="text-success">92</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-success" style={{ width: '92%' }} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-white/60">Claude</span>
                    <span className="text-primary">85</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-primary" style={{ width: '85%' }} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-white/60">Gemini</span>
                    <span className="text-accent">78</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-accent" style={{ width: '78%' }} />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Floating elements */}
            <div className="absolute -top-4 -right-4 w-20 h-20 rounded-xl glass flex items-center justify-center">
              <span className="text-2xl font-bold text-success">+12%</span>
            </div>
            <div className="absolute -bottom-4 -left-4 w-24 h-16 rounded-xl glass flex items-center justify-center">
              <span className="text-sm text-white/80">R.A.T.E™</span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
