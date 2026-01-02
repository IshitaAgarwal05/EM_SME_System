import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
    LayoutDashboard,
    CheckSquare,
    Wallet,
    Calendar,
    FileSpreadsheet,
    Bot,
    LogOut,
    ShieldCheck,
    Users
} from "lucide-react";
import { cn } from "../../lib/utils";

const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Tasks", href: "/dashboard/tasks", icon: CheckSquare },
    { name: "Finance", href: "/dashboard/finance", icon: Wallet },
    { name: "Meetings", href: "/dashboard/meetings", icon: Calendar },
    { name: "Team", href: "/dashboard/team", icon: Users },
    { name: "Files", href: "/dashboard/files", icon: FileSpreadsheet },
    { name: "AI Assistant", href: "/dashboard/ai", icon: Bot },
    { name: "Legal", href: "/dashboard/legal", icon: ShieldCheck },
];

export function Sidebar() {
    const { pathname } = useLocation();
    const { logout } = useAuth();

    return (
        <div className="flex h-screen w-64 flex-col border-r bg-white">
            <div className="flex h-16 items-center px-6 border-b">
                <h1 className="text-xl font-bold text-gray-900">Event OS</h1>
            </div>

            <div className="flex-1 flex flex-col gap-1 p-4">
                {navigation.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.name}
                            to={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-slate-100 text-slate-900"
                                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                            )}
                        >
                            <Icon className="h-4 w-4" />
                            {item.name}
                        </Link>
                    );
                })}
            </div>

            <div className="border-t p-4">
                <button
                    onClick={logout}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
                >
                    <LogOut className="h-4 w-4" />
                    Sign out
                </button>
            </div>
        </div>
    );
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user } = useAuth();

    return (
        <div className="flex h-screen bg-gray-50">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="flex h-16 items-center justify-between border-b bg-white px-6">
                    <h2 className="text-lg font-medium text-gray-900">
                        Welcome back, {user?.full_name?.split(" ")[0]}
                    </h2>
                    <div className="flex items-center gap-4">
                        <AnnouncementSidebar />
                        <div
                            className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium cursor-pointer hover:ring-2 hover:ring-blue-200"
                            onClick={() => alert("Profile settings coming soon!")}
                        >
                            {user?.full_name?.charAt(0)}
                        </div>
                    </div>
                </header>
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}

import { Megaphone, X as CloseIcon, Plus as PlusIcon } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../../lib/api";
import { format } from "date-fns";

function AnnouncementSidebar() {
    const [isOpen, setIsOpen] = useState(false);
    const [announcements, setAnnouncements] = useState<any[]>([]);
    const [isCreating, setIsCreating] = useState(false);
    const { user } = useAuth();
    const isLeader = user?.role === 'owner' || user?.role === 'manager';

    const fetchAnnouncements = async () => {
        try {
            const res = await api.get("/announcements");
            setAnnouncements(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        if (isOpen) fetchAnnouncements();
    }, [isOpen]);

    const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        try {
            await api.post("/announcements", {
                title: formData.get("title"),
                content: formData.get("content"),
            });
            setIsCreating(false);
            fetchAnnouncements();
        } catch (e) {
            alert("Failed to create announcement");
        }
    };

    return (
        <>
            <button
                className="text-gray-500 hover:text-gray-700 hover:bg-gray-100 p-2 rounded-full transition-colors relative"
                onClick={() => setIsOpen(true)}
            >
                <Megaphone className="h-5 w-5" />
                {announcements.length > 0 && (
                    <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500 border-2 border-white"></span>
                )}
            </button>

            {isOpen && (
                <div className="fixed inset-0 z-[100] overflow-hidden">
                    <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setIsOpen(false)}></div>
                    <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-2xl flex flex-col transform transition-transform duration-300">
                        <div className="p-6 border-b flex items-center justify-between bg-slate-900 text-white">
                            <h3 className="text-xl font-bold flex items-center gap-2">
                                <Megaphone className="h-5 w-5" /> Announcements
                            </h3>
                            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/10 rounded-full">
                                <CloseIcon className="h-6 w-6" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {isLeader && !isCreating && (
                                <button
                                    onClick={() => setIsCreating(true)}
                                    className="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed border-slate-200 rounded-xl text-slate-500 hover:border-slate-900 hover:text-slate-900 transition-all font-medium"
                                >
                                    <PlusIcon className="h-4 w-4" /> New Announcement
                                </button>
                            )}

                            {isCreating && (
                                <form onSubmit={handleCreate} className="space-y-4 p-4 bg-slate-50 rounded-xl border">
                                    <input name="title" required placeholder="Announcement Title" className="w-full p-2 rounded-lg border focus:ring-1 focus:ring-slate-900 outline-none sm:text-sm" />
                                    <textarea name="content" required placeholder="Details..." rows={3} className="w-full p-2 rounded-lg border focus:ring-1 focus:ring-slate-900 outline-none sm:text-sm" />
                                    <div className="flex gap-2">
                                        <button type="submit" className="flex-1 bg-slate-900 text-white py-2 rounded-lg text-sm font-bold">Post</button>
                                        <button type="button" onClick={() => setIsCreating(false)} className="px-4 py-2 border rounded-lg text-sm font-bold">Cancel</button>
                                    </div>
                                </form>
                            )}

                            <div className="space-y-4">
                                {announcements.length === 0 ? (
                                    <p className="text-center text-slate-400 py-12 italic">No announcements yet.</p>
                                ) : (
                                    announcements.map((a) => (
                                        <div key={a.id} className="p-4 rounded-xl border bg-white shadow-sm hover:shadow-md transition-shadow group">
                                            <div className="flex justify-between items-start mb-2 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                                <span>{format(new Date(a.created_at), "MMM d, h:mm a")}</span>
                                                <span className="bg-slate-100 px-1.5 py-0.5 rounded group-hover:bg-slate-900 group-hover:text-white transition-colors">Pinned</span>
                                            </div>
                                            <h4 className="font-bold text-slate-900 mb-1">{a.title}</h4>
                                            <p className="text-sm text-slate-600 line-clamp-3">{a.content}</p>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
