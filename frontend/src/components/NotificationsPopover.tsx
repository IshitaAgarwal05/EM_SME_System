import { useState, useEffect, useRef } from "react";
import api from "../lib/api";
import { Reminder } from "../types";
import { Bell, Check, Loader2 } from "lucide-react";
import { format } from "date-fns";

export default function NotificationsPopover() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Reminder[]>([]);
    const [loading, setLoading] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [wrapperRef]);

    useEffect(() => {
        if (isOpen) {
            fetchNotifications();
        }
    }, [isOpen]);

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const res = await api.get("/reminders");
            setNotifications(res.data.items || []);
        } catch (err) {
            console.error("Failed to fetch notifications", err);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.post(`/reminders/${id}/dismiss`);
            setNotifications(notifications.filter(n => n.id !== id));
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="relative" ref={wrapperRef}>
            <button
                className={`relative p-2 rounded-full transition-colors ${isOpen ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <Bell className="h-5 w-5" />
                {notifications.length > 0 && !loading && (
                    <span className="absolute top-1 right-1 h-2.5 w-2.5 rounded-full bg-red-600 border-2 border-white" />
                )}
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                    <div className="px-4 py-2 border-b flex justify-between items-center">
                        <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
                        <button
                            onClick={fetchNotifications}
                            className="text-xs text-blue-600 hover:text-blue-500"
                        >
                            Refresh
                        </button>
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                        {loading ? (
                            <div className="flex justify-center p-4">
                                <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
                            </div>
                        ) : notifications.length === 0 ? (
                            <div className="px-4 py-6 text-center text-sm text-gray-500">
                                No new notifications
                            </div>
                        ) : (
                            notifications.map((notification) => (
                                <div key={notification.id} className="px-4 py-3 hover:bg-gray-50 border-b last:border-0 relative group">
                                    <div className="pr-6">
                                        <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                                        <p className="text-xs text-gray-500 mt-0.5">{notification.message}</p>
                                        <p className="text-[10px] text-gray-400 mt-1">
                                            {format(new Date(notification.scheduled_for), "MMM d, h:mm a")}
                                        </p>
                                    </div>
                                    <button
                                        className="absolute top-3 right-3 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-green-600 transition-opacity"
                                        onClick={(e) => markAsRead(notification.id, e)}
                                        title="Mark as read"
                                    >
                                        <Check className="h-4 w-4" />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
