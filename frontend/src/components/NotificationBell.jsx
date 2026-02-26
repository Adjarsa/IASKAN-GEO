import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Bell, Check, CheckCheck, Trash2, AlertTriangle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const NotificationBell = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/notifications?limit=10`, {
        withCredentials: true,
      });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchNotifications();
    
    // Poll every 30 seconds for new notifications
    const interval = setInterval(fetchNotifications, 30000);
    
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Refresh when dropdown opens
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);

  const markAsRead = async (notificationId) => {
    try {
      await axios.post(
        `${API_URL}/api/notifications/${notificationId}/read`,
        {},
        { withCredentials: true }
      );
      setNotifications((prev) =>
        prev.map((n) =>
          n.notification_id === notificationId ? { ...n, read: true } : n
        )
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  const markAllAsRead = async () => {
    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/notifications/read-all`,
        {},
        { withCredentials: true }
      );
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error("Error marking all notifications as read:", error);
    }
    setLoading(false);
  };

  const deleteNotification = async (e, notificationId) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_URL}/api/notifications/${notificationId}`, {
        withCredentials: true,
      });
      setNotifications((prev) =>
        prev.filter((n) => n.notification_id !== notificationId)
      );
      // Update unread count if deleted notification was unread
      const notification = notifications.find(
        (n) => n.notification_id === notificationId
      );
      if (notification && !notification.read) {
        setUnreadCount((prev) => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error("Error deleting notification:", error);
    }
  };

  const handleNotificationClick = (notification) => {
    // Mark as read
    if (!notification.read) {
      markAsRead(notification.notification_id);
    }

    // Navigate based on notification type
    if (notification.type === "scan_complete" && notification.data?.analysis_id) {
      navigate(`/analysis/${notification.data.analysis_id}`);
      setIsOpen(false);
    } else if (notification.type === "scan_failed" && notification.data?.project_id) {
      navigate(`/analysis`);
      setIsOpen(false);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case "scan_complete":
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case "scan_failed":
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <Bell className="w-4 h-4 text-violet-500" />;
    }
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "À l'instant";
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    return date.toLocaleDateString("fr-FR");
  };

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          data-testid="notification-bell"
        >
          <Bell className="w-5 h-5 text-slate-600" />
          {unreadCount > 0 && (
            <span
              className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full"
              data-testid="notification-badge"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 max-h-[400px] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b">
          <span className="text-sm font-semibold text-slate-900">
            Notifications
          </span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-violet-600 hover:text-violet-700"
              onClick={markAllAsRead}
              disabled={loading}
              data-testid="mark-all-read-btn"
            >
              <CheckCheck className="w-3 h-3 mr-1" />
              Tout marquer lu
            </Button>
          )}
        </div>

        {/* Notifications List */}
        {notifications.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-slate-500">
            <Bell className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            Aucune notification
          </div>
        ) : (
          notifications.map((notification) => (
            <DropdownMenuItem
              key={notification.notification_id}
              className={`flex items-start gap-3 px-3 py-3 cursor-pointer ${
                !notification.read ? "bg-violet-50/50" : ""
              }`}
              onClick={() => handleNotificationClick(notification)}
              data-testid={`notification-item-${notification.notification_id}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getNotificationIcon(notification.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p
                    className={`text-sm ${
                      !notification.read
                        ? "font-medium text-slate-900"
                        : "text-slate-700"
                    }`}
                  >
                    {notification.title}
                  </p>
                  {!notification.read && (
                    <span className="flex-shrink-0 w-2 h-2 mt-1.5 bg-violet-500 rounded-full" />
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                  {notification.message}
                </p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] text-slate-400">
                    {formatTime(notification.created_at)}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-slate-400 hover:text-red-500"
                    onClick={(e) => deleteNotification(e, notification.notification_id)}
                    data-testid={`delete-notification-${notification.notification_id}`}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </DropdownMenuItem>
          ))
        )}

        {/* Footer */}
        {notifications.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <div className="px-3 py-2 text-center">
              <span className="text-xs text-slate-500">
                {unreadCount > 0
                  ? `${unreadCount} notification${unreadCount > 1 ? "s" : ""} non lue${unreadCount > 1 ? "s" : ""}`
                  : "Toutes les notifications sont lues"}
              </span>
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default NotificationBell;
