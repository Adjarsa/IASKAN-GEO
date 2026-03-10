import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { useAuth, BACKEND_URL } from "@/App";
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
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  XCircle
} from "lucide-react";

const SettingsPage = () => {
  const { user, subscription, logout, refreshSubscription } = useAuth();
  const navigate = useNavigate();
  const [cancelling, setCancelling] = useState(false);
  const [reactivating, setReactivating] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/");
    toast.success("Déconnexion réussie");
  };

  const handleCancelSubscription = async () => {
    setCancelling(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/subscription/cancel`,
        {},
        { withCredentials: true }
      );
      toast.success(response.data.message);
      setShowCancelConfirm(false);
      if (refreshSubscription) refreshSubscription();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'annulation");
    } finally {
      setCancelling(false);
    }
  };

  const handleReactivateSubscription = async () => {
    setReactivating(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/subscription/reactivate`,
        {},
        { withCredentials: true }
      );
      toast.success(response.data.message);
      if (refreshSubscription) refreshSubscription();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la réactivation");
    } finally {
      setReactivating(false);
    }
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

                {/* Subscription Status */}
                {subscription?.status === "cancelled" && subscription?.cancellation_effective_date && (
                  <div className="p-4 rounded-lg bg-orange-50 border border-orange-200">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-orange-800 font-medium">Abonnement annulé</p>
                        <p className="text-orange-700 text-sm mt-1">
                          Votre abonnement sera actif jusqu'au{" "}
                          {new Date(subscription.cancellation_effective_date).toLocaleDateString("fr-FR")}
                        </p>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="mt-3 border-orange-300 text-orange-700 hover:bg-orange-100"
                          onClick={handleReactivateSubscription}
                          disabled={reactivating}
                        >
                          {reactivating ? (
                            <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Réactivation...</>
                          ) : (
                            "Réactiver mon abonnement"
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Cancel Subscription */}
                {subscription?.plan && subscription.plan !== "free" && subscription?.status !== "cancelled" && (
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-slate-700 font-medium">Annuler l'abonnement</p>
                        <p className="text-sm text-slate-500">Vous conserverez l'accès jusqu'à la fin de la période</p>
                      </div>
                      {!showCancelConfirm ? (
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="text-slate-600"
                          onClick={() => setShowCancelConfirm(true)}
                          data-testid="cancel-subscription-btn"
                        >
                          Annuler
                        </Button>
                      ) : (
                        <div className="flex gap-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setShowCancelConfirm(false)}
                          >
                            Non
                          </Button>
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={handleCancelSubscription}
                            disabled={cancelling}
                          >
                            {cancelling ? (
                              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Annulation...</>
                            ) : (
                              "Oui, annuler"
                            )}
                          </Button>
                        </div>
                      )}
                    </div>
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
