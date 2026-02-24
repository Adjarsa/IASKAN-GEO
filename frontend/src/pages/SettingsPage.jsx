import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/App";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  User,
  CreditCard,
  Bell,
  Shield,
  LogOut,
  ExternalLink
} from "lucide-react";

const SettingsPage = () => {
  const { user, subscription, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
    toast.success("Déconnexion réussie");
  };

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="settings-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Paramètres</h1>
          <p className="text-slate-700">
            Gérez votre compte et vos préférences
          </p>
        </div>

        <Tabs defaultValue="account" className="space-y-6">
          <TabsList className="bg-slate-100">
            <TabsTrigger value="account">
              <User className="w-4 h-4 mr-2" />
              Compte
            </TabsTrigger>
            <TabsTrigger value="subscription">
              <CreditCard className="w-4 h-4 mr-2" />
              Abonnement
            </TabsTrigger>
            <TabsTrigger value="security">
              <Shield className="w-4 h-4 mr-2" />
              Sécurité
            </TabsTrigger>
          </TabsList>

          {/* Account Tab */}
          <TabsContent value="account" className="space-y-6">
            <Card className="p-6 bg-white border-slate-100">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Informations du profil</h3>
              
              <div className="flex items-start gap-6 mb-6">
                <Avatar className="w-20 h-20">
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback className="bg-violet-600 text-white text-2xl">
                    {user?.name?.charAt(0) || "U"}
                  </AvatarFallback>
                </Avatar>
                
                <div className="flex-1 space-y-4">
                  <div className="space-y-2">
                    <Label>Nom</Label>
                    <Input value={user?.name || ""} disabled className="bg-slate-50" data-testid="user-name" />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input value={user?.email || ""} disabled className="bg-slate-50" data-testid="user-email" />
                  </div>
                </div>
              </div>

              <p className="text-sm text-slate-600">
                Les informations de profil sont gérées via votre compte Google.
              </p>
            </Card>
          </TabsContent>

          {/* Subscription Tab */}
          <TabsContent value="subscription" className="space-y-6">
            <Card className="p-6 bg-white border-slate-100">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Votre abonnement</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50">
                  <div>
                    <p className="text-slate-900 font-medium">
                      Plan {subscription?.plan?.charAt(0).toUpperCase() + subscription?.plan?.slice(1) || "Starter"}
                    </p>
                    <p className="text-sm text-slate-600">
                      {subscription?.status === "trial" ? "Essai gratuit" : "Actif"}
                    </p>
                  </div>
                  <Button variant="outline" onClick={() => navigate("/pricing")} data-testid="change-plan-btn">
                    Changer de plan
                  </Button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-slate-50">
                    <p className="text-slate-600 text-sm">Requêtes utilisées</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {subscription?.queries_used || 0} / {subscription?.queries_limit || 300}
                    </p>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-slate-50">
                    <p className="text-slate-600 text-sm">Prochaine facturation</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {subscription?.current_period_end 
                        ? new Date(subscription.current_period_end).toLocaleDateString("fr-FR")
                        : "-"}
                    </p>
                  </div>
                </div>

                {subscription?.trial_ends_at && (
                  <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                    <p className="text-amber-700">
                      Votre essai gratuit se termine le{" "}
                      {new Date(subscription.trial_ends_at).toLocaleDateString("fr-FR")}
                    </p>
                  </div>
                )}
              </div>
            </Card>

            <Card className="p-6 bg-white border-slate-100">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Historique de facturation</h3>
              <p className="text-slate-600">
                Vos factures seront disponibles ici une fois votre abonnement actif.
              </p>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-6">
            <Card className="p-6 bg-white border-slate-100">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Session</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50">
                  <div>
                    <p className="text-slate-900 font-medium">Session active</p>
                    <p className="text-sm text-slate-600">
                      Connecté via Google SSO
                    </p>
                  </div>
                  <Button variant="destructive" onClick={handleLogout} data-testid="logout-btn">
                    <LogOut className="w-4 h-4 mr-2" />
                    Déconnexion
                  </Button>
                </div>
              </div>
            </Card>

            <Card className="p-6 bg-white border-slate-100">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Données personnelles</h3>
              <p className="text-slate-600 mb-4">
                Vous pouvez demander l'export ou la suppression de vos données à tout moment.
              </p>
              <div className="flex gap-3">
                <Button variant="outline" size="sm">
                  Exporter mes données
                </Button>
                <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                  Supprimer mon compte
                </Button>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default SettingsPage;
