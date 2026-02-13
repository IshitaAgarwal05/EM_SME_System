import { useState, useEffect } from "react";
import api from "../lib/api";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { format } from "date-fns";
import { Bell, Check, CheckCircle2 } from "lucide-react";

export default function NotificationsPage() {
    const [notifications, setNotifications] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchNotifications = async () => {
        try {
            const response = await api.get("/notifications");
            setNotifications(response.data);
        } catch (error) {
            console.error("Failed to fetch notifications:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
    }, []);

    const markAsRead = async (id: string) => {
        try {
            await api.post(`/notifications/${id}/read`);
            setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
        } catch (error) {
            console.error("Failed to mark as read:", error);
        }
    };

    const markAllAsRead = async () => {
        try {
            await api.post("/notifications/read-all");
            setNotifications(notifications.map(n => ({ ...n, is_read: true })));
        } catch (error) {
            console.error("Failed to mark all as read:", error);
        }
    };

    const unreadCount = notifications.filter(n => !n.is_read).length;

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                            <Bell className="w-6 h-6 text-slate-700" />
                            Notifications
                        </h1>
                        <p className="text-sm text-gray-500 mt-1">Invoice alerts, payments, and system updates.</p>
                    </div>
                    {unreadCount > 0 && (
                        <button
                            onClick={markAllAsRead}
                            className="flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 transition-colors"
                        >
                            <CheckCircle2 className="h-4 w-4" />
                            Mark all as read
                        </button>
                    )}
                </div>

                <div className="rounded-xl border bg-white shadow-sm overflow-hidden divide-y divide-gray-100">
                    {isLoading ? (
                        <div className="p-8 text-center text-gray-500">Loading notifications...</div>
                    ) : notifications.length === 0 ? (
                        <div className="p-12 text-center flex flex-col items-center">
                            <Bell className="w-12 h-12 text-gray-300 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900">All caught up</h3>
                            <p className="text-gray-500 mt-1">You have no new notifications.</p>
                        </div>
                    ) : (
                        notifications.map((notif) => (
                            <div
                                key={notif.id}
                                className={`p-5 flex items-start gap-4 transition-colors ${notif.is_read ? 'bg-white' : 'bg-blue-50/30'}`}
                            >
                                <div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${notif.is_read ? 'bg-transparent' : 'bg-[#cc0000]'}`} />
                                <div className="flex-1">
                                    <p className={`text-sm ${notif.is_read ? 'text-gray-600' : 'text-gray-900 font-medium'}`}>
                                        {notif.message}
                                    </p>
                                    <p className="text-xs text-gray-400 mt-1.5 font-medium">
                                        {format(new Date(notif.date), "MMM d, yyyy • h:mm a")}
                                    </p>
                                </div>
                                {!notif.is_read && (
                                    <button
                                        onClick={() => markAsRead(notif.id)}
                                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                        title="Mark as read"
                                    >
                                        <Check className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
