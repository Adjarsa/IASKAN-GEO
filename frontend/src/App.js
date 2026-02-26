import { useState, useEffect, createContext, useContext, useCallback, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { getFingerprintAsync } from "@/hooks/useFingerprint";

// Initialize portal container for Radix UI components immediately
// This fixes the React 19 + Radix UI "insertBefore" error
if (typeof document !== 'undefined') {
  const existingPortal = document.getElementById('radix-portal-root');
  if (!existingPortal) {
    const portalRoot = document.createElement('div');
    portalRoot.id = 'radix-portal-root';
    portalRoot.setAttribute('data-radix-portal', '');
    document.body.appendChild(portalRoot);
  }
}

// Pages
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import ProjectSelectorPage from "@/pages/ProjectSelectorPage";
import DashboardPage from "@/pages/DashboardPage";
import AnalysisPage from "@/pages/AnalysisPage";
import ProjectsPage from "@/pages/ProjectsPage";
import RecommendationsPage from "@/pages/RecommendationsPage";
import PricingPage from "@/pages/PricingPage";
import SettingsPage from "@/pages/SettingsPage";
import ForgotPasswordPage from "@/pages/ForgotPasswordPage";
import ResetPasswordPage from "@/pages/ResetPasswordPage";
import MagicLinkPage from "@/pages/MagicLinkPage";
import CompetitorComparisonPage from "@/pages/CompetitorComparisonPage";
import HistoryChartsPage from "@/pages/HistoryChartsPage";
import VisibilityPage from "@/pages/VisibilityPage";
import ContentAuditPage from "@/pages/ContentAuditPage";
import ContentGeneratorPage from "@/pages/ContentGeneratorPage";
import VerifyEmailPage from "@/pages/VerifyEmailPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentProject, setCurrentProject] = useState(null);

  const checkAuth = useCallback(async () => {
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true,
        timeout: 5000 // 5 second timeout to prevent infinite loading
      });
      setUser(response.data.user);
      setSubscription(response.data.subscription);
      
      // Restore selected project from localStorage
      const savedProjectId = localStorage.getItem('currentProjectId');
      if (savedProjectId) {
        try {
          const projectResponse = await axios.get(`${API}/projects/${savedProjectId}`, {
            withCredentials: true,
            timeout: 5000
          });
          setCurrentProject(projectResponse.data.project);
        } catch (e) {
          localStorage.removeItem('currentProjectId');
        }
      }
    } catch (error) {
      setUser(null);
      setSubscription(null);
      setCurrentProject(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = (userData, subscriptionData) => {
    setUser(userData);
    setSubscription(subscriptionData);
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      console.error("Logout error:", error);
    }
    setUser(null);
    setSubscription(null);
    setCurrentProject(null);
    localStorage.removeItem('currentProjectId');
  };

  const refreshSubscription = async () => {
    try {
      const response = await axios.get(`${API}/subscription`, { withCredentials: true });
      setSubscription(response.data.subscription);
    } catch (error) {
      console.error("Subscription refresh error:", error);
    }
  };

  const selectProject = (project) => {
    setCurrentProject(project);
    if (project) {
      localStorage.setItem('currentProjectId', project.project_id);
    } else {
      localStorage.removeItem('currentProjectId');
    }
  };

  const clearProject = () => {
    setCurrentProject(null);
    localStorage.removeItem('currentProjectId');
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      subscription, 
      loading, 
      login, 
      logout, 
      checkAuth, 
      refreshSubscription,
      currentProject,
      selectProject,
      clearProject
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Callback Component
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];
        
        try {
          // Get browser fingerprint for anti-abuse tracking
          const fingerprint = await getFingerprintAsync();
          
          const response = await axios.post(
            `${API}/auth/session`,
            { 
              session_id: sessionId,
              fingerprint: fingerprint || "unknown"
            },
            { withCredentials: true }
          );
          
          login(response.data.user, null);
          toast.success("Connexion réussie !");
          navigate("/projects", { replace: true });
        } catch (error) {
          console.error("Auth error:", error);
          
          // Handle temporary email block
          const detail = error.response?.data?.detail;
          if (detail?.error === "temporary_email_blocked") {
            toast.error(detail.message || "Les adresses email temporaires ne sont pas autorisées.");
          } else {
            toast.error("Erreur d'authentification");
          }
          navigate("/login", { replace: true });
        }
      } else {
        navigate("/login", { replace: true });
      }
    };

    processAuth();
  }, [location, login, navigate]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="spinner w-12 h-12 mx-auto mb-4"></div>
        <p className="text-slate-500">Authentification en cours...</p>
      </div>
    </div>
  );
};

// Protected Route - requires auth
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="relative w-16 h-16 mx-auto">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-20"></div>
            <div className="absolute inset-2 rounded-full bg-white flex items-center justify-center shadow-lg">
              <div className="w-6 h-6 rounded-full border-2 border-violet-600 border-t-transparent animate-spin"></div>
            </div>
          </div>
          <p className="text-slate-600 font-medium">Chargement...</p>
          <div className="w-32 mx-auto bg-slate-100 rounded-full h-1 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
          </div>
        </div>
      </div>
    );
  }

  if (location.state?.user) {
    return children;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Project Required Route - requires auth AND selected project
const ProjectRequiredRoute = ({ children }) => {
  const { user, loading, currentProject } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="relative w-16 h-16 mx-auto">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-cyan-600 animate-pulse opacity-20"></div>
            <div className="absolute inset-2 rounded-full bg-white flex items-center justify-center shadow-lg">
              <div className="w-6 h-6 rounded-full border-2 border-violet-600 border-t-transparent animate-spin"></div>
            </div>
          </div>
          <p className="text-slate-600 font-medium">Chargement du projet...</p>
          <div className="w-32 mx-auto bg-slate-100 rounded-full h-1 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 rounded-full animate-loading-bar"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If no project selected, redirect to project selector
  if (!currentProject) {
    return <Navigate to="/projects" replace state={{ from: location }} />;
  }

  return children;
};

// App Router
const AppRouter = () => {
  const location = useLocation();

  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route
        path="/projects"
        element={
          <ProtectedRoute>
            <ProjectSelectorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProjectRequiredRoute>
            <DashboardPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/analysis"
        element={
          <ProjectRequiredRoute>
            <AnalysisPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/analysis/:analysisId"
        element={
          <ProjectRequiredRoute>
            <AnalysisPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/recommendations"
        element={
          <ProjectRequiredRoute>
            <RecommendationsPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/competitors"
        element={
          <ProjectRequiredRoute>
            <CompetitorComparisonPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProjectRequiredRoute>
            <HistoryChartsPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/visibility"
        element={
          <ProjectRequiredRoute>
            <VisibilityPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/content-audit"
        element={
          <ProjectRequiredRoute>
            <ContentAuditPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/content-generator"
        element={
          <ProjectRequiredRoute>
            <ContentGeneratorPage />
          </ProjectRequiredRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      {/* Password Reset & Magic Link Routes */}
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/auth/magic" element={<MagicLinkPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <div className="app-container">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
export { API, BACKEND_URL };
