import { useState, useEffect } from "react";
import axios from "axios";
import { Calendar, Clock, Mail, Play, Trash2, Settings, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DAYS_OF_WEEK = [
  { value: 0, label: "Lundi" },
  { value: 1, label: "Mardi" },
  { value: 2, label: "Mercredi" },
  { value: 3, label: "Jeudi" },
  { value: 4, label: "Vendredi" },
  { value: 5, label: "Samedi" },
  { value: 6, label: "Dimanche" }
];

const FREQUENCIES = [
  { value: "daily", label: "Quotidien" },
  { value: "weekly", label: "Hebdomadaire" },
  { value: "monthly", label: "Mensuel" }
];

const ScanScheduleConfig = ({ projectId, projectName, onUpdate }) => {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [available, setAvailable] = useState(true);
  const [unavailableReason, setUnavailableReason] = useState("");
  
  const [formData, setFormData] = useState({
    frequency: "weekly",
    day_of_week: 0,
    day_of_month: 1,
    hour: 9,
    minute: 0,
    send_report_email: true,
    report_recipients: ""
  });

  useEffect(() => {
    fetchSchedule();
  }, [projectId]);

  const fetchSchedule = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/schedules/${projectId}`, {
        withCredentials: true
      });
      
      if (response.data.schedule) {
        const sched = response.data.schedule;
        setSchedule(sched);
        setFormData({
          frequency: sched.frequency || "weekly",
          day_of_week: sched.day_of_week || 0,
          day_of_month: sched.day_of_month || 1,
          hour: sched.hour || 9,
          minute: sched.minute || 0,
          send_report_email: sched.send_report_email !== false,
          report_recipients: (sched.report_recipients || []).join(", ")
        });
      }
      setAvailable(true);
    } catch (error) {
      if (error.response?.status === 403) {
        setAvailable(false);
        setUnavailableReason(error.response?.data?.detail || "Plan Pro ou Business requis");
      }
      console.error("Error fetching schedule:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const recipients = formData.report_recipients
        .split(",")
        .map(e => e.trim())
        .filter(e => e && e.includes("@"));

      const payload = {
        project_id: projectId,
        frequency: formData.frequency,
        day_of_week: formData.day_of_week,
        day_of_month: formData.day_of_month,
        hour: formData.hour,
        minute: formData.minute,
        send_report_email: formData.send_report_email,
        report_recipients: recipients
      };

      if (schedule) {
        await axios.put(`${API_URL}/api/schedules/${schedule.schedule_id}`, payload, {
          withCredentials: true
        });
        toast.success("Programmation mise à jour");
      } else {
        const response = await axios.post(`${API_URL}/api/schedules`, payload, {
          withCredentials: true
        });
        setSchedule(response.data.schedule);
        toast.success("Programmation créée");
      }
      
      fetchSchedule();
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleEnabled = async () => {
    if (!schedule) return;
    
    try {
      await axios.put(`${API_URL}/api/schedules/${schedule.schedule_id}`, {
        enabled: !schedule.enabled
      }, { withCredentials: true });
      
      setSchedule(prev => ({ ...prev, enabled: !prev.enabled }));
      toast.success(schedule.enabled ? "Programmation désactivée" : "Programmation activée");
    } catch (error) {
      toast.error("Erreur lors de la mise à jour");
    }
  };

  const handleDelete = async () => {
    if (!schedule || !window.confirm("Supprimer cette programmation ?")) return;
    
    try {
      await axios.delete(`${API_URL}/api/schedules/${schedule.schedule_id}`, {
        withCredentials: true
      });
      setSchedule(null);
      setFormData({
        frequency: "weekly",
        day_of_week: 0,
        day_of_month: 1,
        hour: 9,
        minute: 0,
        send_report_email: true,
        report_recipients: ""
      });
      toast.success("Programmation supprimée");
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const handleRunNow = async () => {
    if (!schedule) return;
    
    try {
      await axios.post(`${API_URL}/api/schedules/${schedule.schedule_id}/run-now`, {}, {
        withCredentials: true
      });
      toast.success("Scan lancé ! Vous serez notifié quand il sera terminé.");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Impossible de lancer le scan");
    }
  };

  const formatNextRun = (isoDate) => {
    if (!isoDate) return "Non planifié";
    const date = new Date(isoDate);
    return date.toLocaleString("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center gap-2 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          Chargement...
        </div>
      </Card>
    );
  }

  if (!available) {
    return (
      <Card className="p-6 bg-slate-50 border-dashed">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-lg bg-violet-100 flex items-center justify-center flex-shrink-0">
            <Calendar className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 mb-1">Scans Programmés</h3>
            <p className="text-slate-600 text-sm mb-3">{unavailableReason}</p>
            <Button variant="outline" size="sm" asChild>
              <a href="/pricing">Passer à Pro ou Business</a>
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6" data-testid="scan-schedule-config">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center">
            <Calendar className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Scan Programmé</h3>
            <p className="text-sm text-slate-500">{projectName}</p>
          </div>
        </div>
        
        {schedule && (
          <div className="flex items-center gap-2">
            <Switch
              checked={schedule.enabled}
              onCheckedChange={handleToggleEnabled}
              data-testid="schedule-toggle"
            />
            <span className={`text-sm ${schedule.enabled ? "text-emerald-600" : "text-slate-500"}`}>
              {schedule.enabled ? "Actif" : "Inactif"}
            </span>
          </div>
        )}
      </div>

      {/* Status */}
      {schedule && (
        <div className={`mb-6 p-4 rounded-xl ${schedule.enabled ? "bg-emerald-50" : "bg-slate-50"}`}>
          <div className="flex items-center gap-2 mb-2">
            {schedule.enabled ? (
              <CheckCircle className="w-5 h-5 text-emerald-600" />
            ) : (
              <AlertCircle className="w-5 h-5 text-slate-400" />
            )}
            <span className={`font-medium ${schedule.enabled ? "text-emerald-700" : "text-slate-600"}`}>
              {schedule.enabled ? "Prochain scan" : "Programmation en pause"}
            </span>
          </div>
          {schedule.enabled && (
            <p className="text-sm text-emerald-600 ml-7">
              {formatNextRun(schedule.next_run)}
            </p>
          )}
        </div>
      )}

      {/* Configuration Form */}
      <div className="space-y-4">
        {/* Frequency */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Fréquence</label>
          <select
            value={formData.frequency}
            onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
          >
            {FREQUENCIES.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        {/* Day Selection */}
        {formData.frequency === "weekly" && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Jour de la semaine</label>
            <select
              value={formData.day_of_week}
              onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
            >
              {DAYS_OF_WEEK.map(d => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
        )}

        {formData.frequency === "monthly" && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Jour du mois</label>
            <select
              value={formData.day_of_month}
              onChange={(e) => setFormData({ ...formData, day_of_month: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
            >
              {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        )}

        {/* Time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Heure</label>
            <select
              value={formData.hour}
              onChange={(e) => setFormData({ ...formData, hour: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
            >
              {Array.from({ length: 24 }, (_, i) => i).map(h => (
                <option key={h} value={h}>{h.toString().padStart(2, "0")}h</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Minute</label>
            <select
              value={formData.minute}
              onChange={(e) => setFormData({ ...formData, minute: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
            >
              {[0, 15, 30, 45].map(m => (
                <option key={m} value={m}>{m.toString().padStart(2, "0")}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Email Options */}
        <div className="pt-4 border-t border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">Envoyer le rapport par email</span>
            </div>
            <Switch
              checked={formData.send_report_email}
              onCheckedChange={(checked) => setFormData({ ...formData, send_report_email: checked })}
            />
          </div>
          
          {formData.send_report_email && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Destinataires additionnels (séparés par des virgules)
              </label>
              <input
                type="text"
                value={formData.report_recipients}
                onChange={(e) => setFormData({ ...formData, report_recipients: e.target.value })}
                placeholder="collegue@exemple.com, manager@exemple.com"
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none text-sm"
              />
              <p className="text-xs text-slate-500 mt-1">
                Le rapport sera envoyé à votre email et aux destinataires listés ci-dessus.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between mt-6 pt-6 border-t border-slate-100">
        <div className="flex items-center gap-2">
          {schedule && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRunNow}
                className="text-violet-600"
              >
                <Play className="w-4 h-4 mr-1" />
                Lancer maintenant
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
        
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-gradient-to-r from-violet-600 to-cyan-600"
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Enregistrement...
            </>
          ) : (
            <>
              <Settings className="w-4 h-4 mr-2" />
              {schedule ? "Mettre à jour" : "Activer la programmation"}
            </>
          )}
        </Button>
      </div>
    </Card>
  );
};

export default ScanScheduleConfig;
