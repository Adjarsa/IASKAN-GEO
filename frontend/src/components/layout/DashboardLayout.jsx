import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Logo from "@/components/Logo";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  LayoutDashboard,
  BarChart3,
  FolderKanban,
  Target,
  Settings,
  LogOut,
  Menu,
  X,
  CreditCard,
  ChevronDown
} from "lucide-react";

const DashboardLayout = ({ children }) => {
  const { user, subscription, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/analysis", label: "Analyses", icon: BarChart3 },
    { path: "/projects", label: "Projets", icon: FolderKanban },
    { path: "/recommendations", label: "Recommandations", icon: Target },
    { path: "/settings", label: "Paramètres", icon: Settings },
  ];

  const isActive = (path) => {
    if (path === "/dashboard") {
      return location.pathname === "/dashboard";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="dashboard-layout">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 flex items-center justify-between">
            <Link to="/dashboard" data-testid="sidebar-logo">
              <Logo />
            </Link>
            <Button 
              variant="ghost" 
              size="icon" 
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive(item.path)
                    ? 'nav-active bg-violet-50 text-violet-700 font-medium'
                    : 'text-slate-600 hover:text-violet-700 hover:bg-slate-50'
                }`}
                data-testid={`nav-${item.label.toLowerCase()}`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Subscription Info */}
          <div className="p-4">
            <div className="rounded-xl p-4 bg-gradient-to-br from-violet-50 to-cyan-50 border border-violet-100">
              <div className="flex items-center gap-2 mb-2">
                <CreditCard className="w-4 h-4 text-violet-600" />
                <span className="text-sm font-medium text-slate-900">
                  Plan {subscription?.plan?.charAt(0).toUpperCase() + subscription?.plan?.slice(1) || "Starter"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-3">
                {subscription?.queries_used || 0} / {subscription?.queries_limit || 300} requêtes
              </p>
              <Link to="/pricing">
                <Button variant="outline" size="sm" className="w-full border-violet-200 text-violet-700 hover:bg-violet-50" data-testid="sidebar-upgrade">
                  Améliorer
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-content">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-lg border-b border-slate-100">
          <div className="flex items-center justify-between px-6 py-4">
            {/* Mobile menu button */}
            <Button 
              variant="ghost" 
              size="icon" 
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
              data-testid="mobile-menu-btn"
            >
              <Menu className="w-5 h-5" />
            </Button>

            {/* Breadcrumb / Title */}
            <div className="hidden lg:block">
              <h2 className="text-lg font-semibold text-slate-900">
                {navItems.find(item => isActive(item.path))?.label || "Dashboard"}
              </h2>
            </div>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-3" data-testid="user-menu">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback className="bg-gradient-to-br from-violet-500 to-cyan-500 text-white">
                      {user?.name?.charAt(0) || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:block text-slate-700">{user?.name}</span>
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-3 py-2">
                  <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                  <p className="text-xs text-slate-500">{user?.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/settings" data-testid="menu-settings">
                    <Settings className="w-4 h-4 mr-2" />
                    Paramètres
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/pricing" data-testid="menu-subscription">
                    <CreditCard className="w-4 h-4 mr-2" />
                    Abonnement
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600" data-testid="menu-logout">
                  <LogOut className="w-4 h-4 mr-2" />
                  Déconnexion
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
