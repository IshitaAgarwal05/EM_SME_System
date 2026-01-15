import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import {
    Plus, User, Mail, Phone, Building2, Briefcase,
    CreditCard, Loader2, X, Activity, History,
    Users, Search, Filter, SortAsc, MoreVertical,
    Trash2, Edit2, Megaphone, CheckSquare, UserPlus
} from "lucide-react";
import { format } from "date-fns";
import { useAuth } from "../context/AuthContext";
import InviteTeamModal from "../components/InviteTeamModal";

type Contractor = {
    id: string;
    name: string;
    email?: string;
    phone?: string;
    company_name?: string;
    service_type?: string;
    payment_mode?: string;
    is_active: boolean;
};

type TeamMember = {
    id: string;
    full_name: string;
    email: string;
    phone?: string;
    branch?: string;
    position?: string;
    role: string;
    is_active: boolean;
};

export default function TeamPage() {
    const { user: currentUser } = useAuth();
    const isManager = currentUser?.role === 'owner' || currentUser?.role === 'manager';

    const [activeTab, setActiveTab] = useState<"team" | "contractors">("team");
    const [team, setTeam] = useState<TeamMember[]>([]);
    const [contractors, setContractors] = useState<Contractor[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortBy, setSortBy] = useState("name");

    // Modal states
    const [isAddUserOpen, setIsAddUserOpen] = useState(false);
    const [isEditUserOpen, setIsEditUserOpen] = useState(false);
    const [isAddContractorOpen, setIsAddContractorOpen] = useState(false);
    const [isEditContractorOpen, setIsEditContractorOpen] = useState(false);
    const [selectedMember, setSelectedMember] = useState<any>(null);
    const [selectedContractor, setSelectedContractor] = useState<any>(null);
    const [isMemberDetailsOpen, setIsMemberDetailsOpen] = useState(false);
    const [memberDetails, setMemberDetails] = useState<any>(null);
    const [detailsLoading, setDetailsLoading] = useState(false);
    const [formLoading, setFormLoading] = useState(false);
    const [isQuickTaskOpen, setIsQuickTaskOpen] = useState(false);
    const [isQuickAnnounceOpen, setIsQuickAnnounceOpen] = useState(false);
    const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);

    const [isContractorDetailsOpen, setIsContractorDetailsOpen] = useState(false);
    const [contractorDetails, setContractorDetails] = useState<any>(null);

    useEffect(() => {
        fetchAllData();
    }, []);

    const fetchAllData = async () => {
        setLoading(true);
        try {
            const [teamRes, contractorsRes] = await Promise.all([
                api.get("/users"),
                api.get("/financial/contractors")
            ]);
            setTeam(teamRes.data.items || []);
            setContractors(contractorsRes.data.items || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleAddUser = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormLoading(true);
        const formData = new FormData(e.currentTarget);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post("/users", {
                ...data,
                password: "Password123!", // Default password for new members
            });
            setIsAddUserOpen(false);
            fetchAllData();
        } catch (e) {
            alert("Failed to create user");
        } finally {
            setFormLoading(false);
        }
    };

    const handleAddContractor = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormLoading(true);
        const formData = new FormData(e.currentTarget);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post("/financial/contractors", data);
            setIsAddContractorOpen(false);
            fetchAllData();
        } catch (e) {
            alert("Failed to create contractor");
        } finally {
            setFormLoading(false);
        }
    };

    const handleMemberClick = async (member: TeamMember) => {
        setSelectedMember(member);
        setIsMemberDetailsOpen(true);
        setDetailsLoading(true);
        try {
            const res = await api.get(`/users/${member.id}/details`);
            setMemberDetails(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setDetailsLoading(false);
        }
    };

    const handleContractorClick = async (contractor: Contractor) => {
        setSelectedContractor(contractor);
        setIsContractorDetailsOpen(true);
        setDetailsLoading(true);
        try {
            const res = await api.get(`/financial/contractors/${contractor.id}/details`);
            setContractorDetails(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setDetailsLoading(false);
        }
    };


    const handleDeleteUser = async (id: string) => {
        if (!confirm("Are you sure you want to deactivate this user?")) return;
        try {
            await api.delete(`/users/${id}`);
            fetchAllData();
        } catch (e) {
            alert("Failed to deactivate user");
        }
    };

    const handleEditUser = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormLoading(true);
        const formData = new FormData(e.currentTarget);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.patch(`/users/${selectedMember.id}`, data);
            setIsEditUserOpen(false);
            setIsMemberDetailsOpen(false);
            fetchAllData();
        } catch (e) {
            alert("Failed to update user");
        } finally {
            setFormLoading(false);
        }
    };

    const handleEditContractor = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormLoading(true);
        const formData = new FormData(e.currentTarget);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.patch(`/financial/contractors/${selectedContractor.id}`, data);
            setIsEditContractorOpen(false);
            fetchAllData();
        } catch (e) {
            alert("Failed to update contractor");
        } finally {
            setFormLoading(false);
        }
    };

    const handleDeleteContractor = async (id: string) => {
        if (!confirm("Are you sure you want to remove this contractor?")) return;
        try {
            await api.delete(`/financial/contractors/${id}`);
            fetchAllData();
        } catch (e) {
            alert("Failed to delete contractor");
        }
    };

    const handleQuickTask = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormLoading(true);
        const formData = new FormData(e.currentTarget);
        try {
            const taskRes = await api.post("/tasks", {
                title: formData.get("title"),
                description: formData.get("description"),
                due_date: formData.get("due_date"),
                priority: formData.get("priority") || "medium",
            });
            await api.post(`/tasks/${taskRes.data.id}/assign`, {
                user_ids: [selectedMember.id]
            });
            setIsQuickTaskOpen(false);
            if (selectedMember) handleMemberClick(selectedMember);
        } catch (e) {
            alert("Failed to assign task");
        } finally {
            setFormLoading(false);
        }
    };

    const handleQuickAnnounce = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormLoading(true);
        const formData = new FormData(e.currentTarget);
        try {
            await api.post("/announcements", {
                title: formData.get("title"),
                content: formData.get("content"),
            });
            setIsQuickAnnounceOpen(false);
            alert("Announcement posted successfully!");
        } catch (e) {
            alert("Failed to post announcement");
        } finally {
            setFormLoading(false);
        }
    };

    const filteredTeam = team
        .filter(m => m.full_name.toLowerCase().includes(searchQuery.toLowerCase()) || m.position?.toLowerCase().includes(searchQuery.toLowerCase()))
        .sort((a, b) => {
            if (sortBy === "position") return (a.position || "").localeCompare(b.position || "");
            return a.full_name.localeCompare(b.full_name);
        });

    const filteredContractors = contractors.filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.service_type?.toLowerCase().includes(searchQuery.toLowerCase()));

    return (
        <DashboardLayout>
            <div className="flex flex-col gap-8">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Team Hub</h2>
                        <p className="text-slate-500 font-medium">Manage your workforce, partners, and internal communications.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {activeTab === "team" && isManager && (
                            <>
                                <button
                                    onClick={() => setIsInviteModalOpen(true)}
                                    className="inline-flex items-center px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl text-sm font-bold shadow-lg hover:shadow-purple-200 transition-all hover:-translate-y-0.5"
                                >
                                    <UserPlus className="mr-2 h-4 w-4" /> Invite via Email
                                </button>
                                <button
                                    onClick={() => setIsAddUserOpen(true)}
                                    className="inline-flex items-center px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-bold shadow-lg hover:shadow-slate-200 transition-all hover:-translate-y-0.5"
                                >
                                    <Plus className="mr-2 h-4 w-4" /> Add Team Member
                                </button>
                            </>
                        )}
                        {activeTab === "contractors" && isManager && (
                            <button
                                onClick={() => setIsAddContractorOpen(true)}
                                className="inline-flex items-center px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-bold shadow-lg hover:shadow-slate-200 transition-all hover:-translate-y-0.5"
                            >
                                <Plus className="mr-2 h-4 w-4" /> Add Contractor
                            </button>
                        )}
                    </div>
                </div>

                {/* Search & Tabs */}
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div className="flex bg-slate-100 p-1.5 rounded-2xl w-fit">
                        <button
                            onClick={() => setActiveTab("team")}
                            className={`flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === "team" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                                }`}
                        >
                            <Users className="h-4 w-4" /> Our Team
                        </button>
                        <button
                            onClick={() => setActiveTab("contractors")}
                            className={`flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === "contractors" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                                }`}
                        >
                            <Briefcase className="h-4 w-4" /> Contractors
                        </button>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative group flex-1 min-w-[300px]">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-slate-900 transition-colors" />
                            <input
                                type="text"
                                placeholder={`Search ${activeTab === 'team' ? 'employees' : 'partners'}...`}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 rounded-2xl text-sm focus:ring-2 focus:ring-slate-900 outline-none transition-all shadow-sm"
                            />
                        </div>
                        {activeTab === "team" && (
                            <div className="flex items-center gap-2 bg-white border border-slate-200 p-1 rounded-2xl shadow-sm">
                                <span className="text-[10px] uppercase font-bold text-slate-400 px-3">Sort By</span>
                                <button
                                    onClick={() => setSortBy("name")}
                                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${sortBy === 'name' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
                                >
                                    Name
                                </button>
                                <button
                                    onClick={() => setSortBy("position")}
                                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${sortBy === 'position' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
                                >
                                    Position
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Content Area */}
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {loading ? (
                        <div className="col-span-full flex flex-col items-center justify-center py-24 gap-4">
                            <Loader2 className="h-12 w-12 animate-spin text-slate-300" />
                            <p className="text-slate-400 text-sm font-medium">Syncing your team data...</p>
                        </div>
                    ) : activeTab === "team" ? (
                        filteredTeam.length === 0 ? (
                            <div className="col-span-full flex flex-col items-center justify-center py-32 rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50/50">
                                <Users className="h-16 w-16 text-slate-200 mb-4" />
                                <h3 className="text-lg font-bold text-slate-900">No team members found</h3>
                                <p className="text-slate-500">Try adjusting your search or add a new member.</p>
                            </div>
                        ) : (
                            filteredTeam.map((m) => (
                                <div
                                    key={m.id}
                                    onClick={() => handleMemberClick(m)}
                                    className="group relative bg-white rounded-3xl border border-slate-200 p-6 shadow-sm hover:shadow-xl hover:border-slate-900 transition-all cursor-pointer overflow-hidden"
                                >
                                    <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setSelectedMember(m); setIsEditUserOpen(true); }}
                                            className="p-2 hover:bg-slate-50 text-slate-400 hover:text-slate-900 rounded-full transition-colors"
                                        >
                                            <Edit2 className="h-4 w-4" />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteUser(m.id); }}
                                            className="p-2 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-full transition-colors"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>

                                    <div className="flex flex-col items-center text-center gap-4">
                                        <div className="relative">
                                            <div className="h-20 w-20 rounded-full bg-slate-100 flex items-center justify-center border-4 border-white shadow-md group-hover:bg-slate-900 group-hover:text-white transition-all duration-300">
                                                <User className="h-10 w-10" />
                                            </div>
                                            <div className={`absolute bottom-0 right-0 h-5 w-5 rounded-full border-4 border-white ${m.is_active ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                                        </div>
                                        <div>
                                            <h4 className="text-lg font-bold text-slate-900">{m.full_name}</h4>
                                            <p className="text-sm font-bold text-blue-600 uppercase tracking-widest">{m.position || "Staff Member"}</p>
                                        </div>
                                        <div className="w-full grid grid-cols-1 gap-2 text-xs text-slate-500 pt-4 border-t border-slate-50">
                                            <div className="flex items-center gap-2 justify-center">
                                                <Building2 className="h-3 w-3" />
                                                <span>{m.branch || "Headquarters"}</span>
                                            </div>
                                            <div className="flex items-center gap-2 justify-center">
                                                <Mail className="h-3 w-3" />
                                                <span>{m.email}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )
                    ) : (
                        filteredContractors.length === 0 ? (
                            <div className="col-span-full flex flex-col items-center justify-center py-32 rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50/50">
                                <Briefcase className="h-16 w-16 text-slate-200 mb-4" />
                                <h3 className="text-lg font-bold text-slate-900">No contractors found</h3>
                                <p className="text-slate-500">Your vendor list is currently empty.</p>
                            </div>
                        ) : (
                            filteredContractors.map((c) => (
                                <div
                                    key={c.id}
                                    onClick={() => handleContractorClick(c)}
                                    className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm hover:shadow-xl hover:border-slate-900 transition-all cursor-pointer group relative"
                                >
                                    <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 z-10">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setSelectedContractor(c); setIsEditContractorOpen(true); }}
                                            className="p-2 hover:bg-slate-50 text-slate-400 hover:text-slate-900 rounded-full transition-colors"
                                        >
                                            <Edit2 className="h-4 w-4" />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteContractor(c.id); }}
                                            className="p-2 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-full transition-colors"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="h-12 w-12 rounded-2xl bg-blue-50 text-blue-700 flex items-center justify-center group-hover:bg-slate-900 group-hover:text-white transition-all">
                                            <Briefcase className="h-6 w-6" />
                                        </div>
                                        <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {c.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </div>
                                    <h4 className="text-lg font-bold text-slate-900 mb-1">{c.name}</h4>
                                    <p className="text-xs font-bold text-slate-400 uppercase mb-4 tracking-widest">{c.service_type || "Vendor Partner"}</p>

                                    <div className="space-y-3 pt-4 border-t border-slate-50">
                                        {c.company_name && (
                                            <div className="flex items-center gap-3 text-sm text-slate-600">
                                                <Building2 className="h-4 w-4 text-slate-400" />
                                                <span>{c.company_name}</span>
                                            </div>
                                        )}
                                        {c.email && (
                                            <div className="flex items-center gap-3 text-sm text-slate-600">
                                                <Mail className="h-4 w-4 text-slate-400" />
                                                <span>{c.email}</span>
                                            </div>
                                        )}
                                        <div className="mt-4 pt-4 flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase">
                                            <span>Mode: {c.payment_mode || "Bank"}</span>
                                            <ChevronRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                        </div>
                                    </div>
                                </div>
                            ))
                        )
                    )}
                </div>
            </div>

            {/* Member Details Modal */}
            {isMemberDetailsOpen && (
                <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 backdrop-blur-md p-4">
                    <div className="w-full max-w-4xl bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                        <div className="bg-slate-900 p-8 text-white flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="h-20 w-20 rounded-3xl bg-white/10 flex items-center justify-center border border-white/20">
                                    <User className="h-10 w-10 text-white" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-3xl font-extrabold">{selectedMember?.full_name}</h3>
                                    <p className="text-slate-400 font-bold uppercase tracking-[0.2em] text-sm">{selectedMember?.position || "Staff"}</p>
                                </div>
                            </div>
                            <button onClick={() => setIsMemberDetailsOpen(false)} className="p-3 hover:bg-white/10 rounded-full transition-colors self-start">
                                <X className="h-8 w-8" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-10">
                            {detailsLoading ? (
                                <div className="h-full flex flex-col items-center justify-center py-24 gap-4">
                                    <Loader2 className="h-12 w-12 animate-spin text-slate-200" />
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                                    {/* Profile Sidebar */}
                                    <div className="space-y-8">
                                        <section className="space-y-6">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                                <Activity className="h-4 w-4" /> Overview
                                            </h4>
                                            <div className="space-y-4">
                                                <div className="p-4 bg-slate-50 rounded-2xl">
                                                    <p className="text-xs text-slate-400 font-bold uppercase">Role</p>
                                                    <p className="text-slate-900 font-bold capitalize">{selectedMember?.role}</p>
                                                </div>
                                                <div className="p-4 bg-slate-50 rounded-2xl">
                                                    <p className="text-xs text-slate-400 font-bold uppercase">Branch</p>
                                                    <p className="text-slate-900 font-bold">{selectedMember?.branch || "Not Assigned"}</p>
                                                </div>
                                                <div className="p-4 bg-slate-50 rounded-2xl">
                                                    <p className="text-xs text-slate-400 font-bold uppercase">Email</p>
                                                    <p className="text-slate-900 font-bold">{selectedMember?.email}</p>
                                                </div>
                                            </div>
                                        </section>

                                        <section className="space-y-4">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Quick Actions</h4>
                                            <div className="flex flex-col gap-2">
                                                <button
                                                    onClick={() => setIsQuickTaskOpen(true)}
                                                    className="flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-2xl text-sm font-bold shadow-lg shadow-blue-100 hover:shadow-blue-200 transition-all"
                                                >
                                                    <CheckSquare className="h-4 w-4" /> Assign New Task
                                                </button>
                                                <button
                                                    onClick={() => setIsQuickAnnounceOpen(true)}
                                                    className="flex items-center justify-center gap-2 py-3 bg-slate-900 text-white rounded-2xl text-sm font-bold shadow-lg shadow-slate-200 transition-all"
                                                >
                                                    <Megaphone className="h-4 w-4" /> Targeted Announcement
                                                </button>
                                            </div>
                                        </section>
                                    </div>

                                    {/* Main Content Area */}
                                    <div className="lg:col-span-2 space-y-12">
                                        <section className="space-y-6">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center justify-between">
                                                <span>Active Workload</span>
                                                <span className="bg-blue-50 text-blue-600 px-2.5 py-1 rounded-lg">{memberDetails?.tasks?.length || 0} Tasks</span>
                                            </h4>
                                            <div className="space-y-3">
                                                {memberDetails?.tasks?.length > 0 ? memberDetails.tasks.map((t: any) => (
                                                    <div key={t.id} className="group p-5 bg-white border border-slate-100 rounded-3xl hover:border-slate-900 transition-all shadow-sm">
                                                        <div className="flex justify-between items-start">
                                                            <div>
                                                                <p className="font-bold text-slate-900 mb-1">{t.title}</p>
                                                                <p className="text-xs text-slate-400 font-medium">Due: {format(new Date(t.due_date), "MMMM d, yyyy")}</p>
                                                            </div>
                                                            <span className={`px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider ${t.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                                                                {t.status}
                                                            </span>
                                                        </div>
                                                    </div>
                                                )) : (
                                                    <div className="py-12 text-center text-slate-400 italic">No tasks assigned to this member.</div>
                                                )}
                                            </div>
                                        </section>

                                        <section className="space-y-6">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center justify-between">
                                                <span>Upcoming Meetings</span>
                                                <span className="bg-slate-100 text-slate-600 px-2.5 py-1 rounded-lg">{memberDetails?.meetings?.length || 0} Scheduled</span>
                                            </h4>
                                            <div className="space-y-3">
                                                {memberDetails?.meetings?.length > 0 ? memberDetails.meetings.map((m: any) => (
                                                    <div key={m.id} className="p-5 bg-slate-50 rounded-3xl border border-transparent hover:border-slate-200 transition-all">
                                                        <div className="flex items-center gap-4">
                                                            <div className="h-10 w-10 bg-white rounded-2xl flex items-center justify-center text-slate-400 shadow-sm">
                                                                <History className="h-5 w-5" />
                                                            </div>
                                                            <div>
                                                                <p className="font-bold text-slate-900">{m.title}</p>
                                                                <p className="text-xs text-slate-500">{format(new Date(m.start_time), "MMM d, h:mm a")} - {m.location || 'Remote'}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )) : (
                                                    <div className="py-12 text-center text-slate-400 italic">No meetings on the horizon.</div>
                                                )}
                                            </div>
                                        </section>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Modals for Add User/Contractor */}
            {isAddUserOpen && (
                <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/50 p-4">
                    <div className="w-full max-w-lg bg-white rounded-[32px] p-8 shadow-2xl space-y-8">
                        <div>
                            <h3 className="text-2xl font-black text-slate-900">Add Team Member</h3>
                            <p className="text-slate-500 text-sm font-medium">Create a new organizational user account.</p>
                        </div>
                        <form onSubmit={handleAddUser} className="space-y-5">
                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Full Name</label>
                                <input name="full_name" required className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Position</label>
                                    <input name="position" placeholder="e.g. Lead Planner" className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Branch</label>
                                    <input name="branch" placeholder="e.g. Delhi" className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold" />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Work Email</label>
                                <input name="email" type="email" required className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold" />
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setIsAddUserOpen(false)} className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl text-sm font-bold">Cancel</button>
                                <button type="submit" disabled={formLoading} className="flex-[2] py-4 bg-slate-900 text-white rounded-2xl text-sm font-bold flex items-center justify-center shadow-lg">
                                    {formLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Create Account
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {isAddContractorOpen && (
                <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/50 p-4 font-sans">
                    <div className="w-full max-w-lg bg-white rounded-[32px] p-8 shadow-2xl space-y-8">
                        <div>
                            <h3 className="text-2xl font-black text-slate-900">Add Contractor</h3>
                            <p className="text-slate-500 text-sm font-medium">Onboard a new service provider or vendor.</p>
                        </div>
                        <form onSubmit={handleAddContractor} className="space-y-5">
                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Provider Name</label>
                                <input name="name" required className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Service Type</label>
                                    <input name="service_type" placeholder="e.g. Design" className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Payment</label>
                                    <select name="payment_mode" className="w-full px-5 py-3.5 bg-slate-50 border border-transparent rounded-2xl focus:ring-2 focus:ring-slate-900 transition-all outline-none font-bold">
                                        <option value="UPI">UPI</option>
                                        <option value="Bank">Bank Transfer</option>
                                        <option value="Cash">Cash</option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setIsAddContractorOpen(false)} className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl text-sm font-bold">Cancel</button>
                                <button type="submit" disabled={formLoading} className="flex-[2] py-4 bg-slate-900 text-white rounded-2xl text-sm font-bold flex items-center justify-center shadow-lg">
                                    {formLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Add Partner
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
            {/* Edit User Modal */}
            {isEditUserOpen && (
                <div className="fixed inset-0 z-[140] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-md bg-white rounded-[32px] p-8 shadow-2xl space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-xl font-black text-slate-900">Edit Member Details</h3>
                            <button onClick={() => setIsEditUserOpen(false)}><X className="h-5 w-5" /></button>
                        </div>
                        <form onSubmit={handleEditUser} className="space-y-4">
                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Full Name</label>
                                <input name="full_name" defaultValue={selectedMember?.full_name} required className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Position</label>
                                    <input name="position" defaultValue={selectedMember?.position} className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Branch</label>
                                    <input name="branch" defaultValue={selectedMember?.branch} className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold" />
                                </div>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setIsEditUserOpen(false)} className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold">Cancel</button>
                                <button type="submit" disabled={formLoading} className="flex-[2] py-4 bg-slate-900 text-white rounded-2xl font-bold">
                                    {formLoading ? "Saving..." : "Save Changes"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit Contractor Modal */}
            {isEditContractorOpen && (
                <div className="fixed inset-0 z-[140] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-md bg-white rounded-[32px] p-8 shadow-2xl space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-xl font-black text-slate-900">Edit Contractor</h3>
                            <button onClick={() => setIsEditContractorOpen(false)}><X className="h-5 w-5" /></button>
                        </div>
                        <form onSubmit={handleEditContractor} className="space-y-4">
                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Provider Name</label>
                                <input name="name" defaultValue={selectedContractor?.name} required className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Service</label>
                                    <input name="service_type" defaultValue={selectedContractor?.service_type} className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">Payment</label>
                                    <select name="payment_mode" defaultValue={selectedContractor?.payment_mode} className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold">
                                        <option value="UPI">UPI</option>
                                        <option value="Bank">Bank Transfer</option>
                                        <option value="Cash">Cash</option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setIsEditContractorOpen(false)} className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold">Cancel</button>
                                <button type="submit" disabled={formLoading} className="flex-[2] py-4 bg-slate-900 text-white rounded-2xl font-bold">
                                    {formLoading ? "Saving..." : "Save Changes"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
            {isQuickTaskOpen && (
                <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-md bg-white rounded-[32px] p-8 shadow-2xl space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-xl font-black text-slate-900">Quick Assign Task</h3>
                            <button onClick={() => setIsQuickTaskOpen(false)}><X className="h-5 w-5" /></button>
                        </div>
                        <p className="text-sm text-slate-500">Assigning task to <b>{selectedMember?.full_name}</b></p>
                        <form onSubmit={handleQuickTask} className="space-y-4">
                            <input name="title" required placeholder="Task Title" className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none font-bold" />
                            <textarea name="description" placeholder="Short description..." className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none sm:text-sm" rows={3} />
                            <div className="grid grid-cols-2 gap-4">
                                <input name="due_date" type="date" required className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none text-sm" />
                                <select name="priority" className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none text-sm">
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <button type="submit" disabled={formLoading} className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold shadow-lg">
                                {formLoading ? "Assigning..." : "Assign Task"}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {isQuickAnnounceOpen && (
                <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-md bg-white rounded-[32px] p-8 shadow-2xl space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-xl font-black text-slate-900">Quick Announcement</h3>
                            <button onClick={() => setIsQuickAnnounceOpen(false)}><X className="h-5 w-5" /></button>
                        </div>
                        <p className="text-sm text-slate-500">Post a new announcement to the team.</p>
                        <form onSubmit={handleQuickAnnounce} className="space-y-4">
                            <input name="title" required placeholder="Announcement Title" className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none font-bold" />
                            <textarea name="content" required placeholder="Announcement content..." className="w-full px-4 py-3 bg-slate-50 border rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none sm:text-sm" rows={4} />
                            <button type="submit" disabled={formLoading} className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold shadow-lg">
                                {formLoading ? "Posting..." : "Post Announcement"}
                            </button>
                        </form>
                    </div>
                </div>
            )}
            {/* Contractor Details Modal */}
            {isContractorDetailsOpen && (
                <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 backdrop-blur-md p-4">
                    <div className="w-full max-w-4xl bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                        <div className="bg-slate-900 p-8 text-white flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="h-20 w-20 rounded-3xl bg-white/10 flex items-center justify-center border border-white/20">
                                    <Briefcase className="h-10 w-10 text-white" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-3xl font-extrabold">{selectedContractor?.name}</h3>
                                    <p className="text-slate-400 font-bold uppercase tracking-[0.2em] text-sm">{selectedContractor?.service_type || "Vendor Partner"}</p>
                                </div>
                            </div>
                            <button onClick={() => setIsContractorDetailsOpen(false)} className="p-3 hover:bg-white/10 rounded-full transition-colors self-start">
                                <X className="h-8 w-8" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-10">
                            {detailsLoading ? (
                                <div className="h-full flex flex-col items-center justify-center py-24 gap-4">
                                    <Loader2 className="h-12 w-12 animate-spin text-slate-200" />
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                                    {/* Contractor Info Sidebar */}
                                    <div className="space-y-8">
                                        <section className="space-y-6">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                                <Activity className="h-4 w-4" /> Overview
                                            </h4>
                                            <div className="space-y-4">
                                                <div className="p-4 bg-slate-50 rounded-2xl">
                                                    <p className="text-xs text-slate-400 font-bold uppercase">Company</p>
                                                    <p className="text-slate-900 font-bold">{selectedContractor?.company_name || "N/A"}</p>
                                                </div>
                                                <div className="p-4 bg-slate-50 rounded-2xl">
                                                    <p className="text-xs text-slate-400 font-bold uppercase">Payment Mode</p>
                                                    <p className="text-slate-900 font-bold capitalize">{selectedContractor?.payment_mode}</p>
                                                </div>
                                                <div className="p-4 bg-slate-50 rounded-2xl">
                                                    <p className="text-xs text-slate-400 font-bold uppercase">Email</p>
                                                    <p className="text-slate-900 font-bold text-xs truncate">{selectedContractor?.email || "N/A"}</p>
                                                </div>
                                            </div>
                                        </section>
                                    </div>

                                    {/* Main Content Area */}
                                    <div className="lg:col-span-2 space-y-12">
                                        <section className="space-y-6">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center justify-between">
                                                <span>Assigned Tasks</span>
                                                <span className="bg-blue-50 text-blue-600 px-2.5 py-1 rounded-lg">{contractorDetails?.tasks?.length || 0} Tasks</span>
                                            </h4>
                                            <div className="space-y-3">
                                                {contractorDetails?.tasks?.length > 0 ? contractorDetails.tasks.map((t: any) => (
                                                    <div key={t.id} className="p-5 bg-white border border-slate-100 rounded-3xl shadow-sm">
                                                        <div className="flex justify-between items-start">
                                                            <div>
                                                                <p className="font-bold text-slate-900 mb-1">{t.title}</p>
                                                                <p className="text-xs text-slate-400 font-medium whitespace-pre-wrap">{t.description}</p>
                                                            </div>
                                                            <span className={`px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider ${t.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                                                                {t.status}
                                                            </span>
                                                        </div>
                                                    </div>
                                                )) : (
                                                    <div className="py-12 text-center text-slate-400 italic">No tasks linked to this contractor.</div>
                                                )}
                                            </div>
                                        </section>

                                        <section className="space-y-6">
                                            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center justify-between">
                                                <span>Payment History</span>
                                                <span className="bg-slate-100 text-slate-600 px-2.5 py-1 rounded-lg">{contractorDetails?.transactions?.length || 0} Records</span>
                                            </h4>
                                            <div className="space-y-3">
                                                {contractorDetails?.transactions?.length > 0 ? contractorDetails.transactions.map((t: any) => (
                                                    <div key={t.id} className="p-5 bg-slate-50 rounded-3xl border border-transparent">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-4">
                                                                <div className="h-10 w-10 bg-white rounded-2xl flex items-center justify-center text-slate-400 shadow-sm font-bold text-xs uppercase">
                                                                    {t.transaction_type === 'credit' ? 'CR' : 'DB'}
                                                                </div>
                                                                <div>
                                                                    <p className="font-bold text-slate-900">{format(new Date(t.transaction_date), "MMM d, yyyy")}</p>
                                                                    <p className="text-xs text-slate-500 truncate max-w-[200px]">{t.description}</p>
                                                                </div>
                                                            </div>
                                                            <p className={`font-black ${t.transaction_type === 'credit' ? 'text-green-600' : 'text-slate-900'}`}>
                                                                {t.transaction_type === 'credit' ? '+' : '-'} ₹{t.amount.toLocaleString()}
                                                            </p>
                                                        </div>
                                                    </div>
                                                )) : (
                                                    <div className="py-12 text-center text-slate-400 italic">No transaction records found.</div>
                                                )}
                                            </div>
                                        </section>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Invite Team Modal */}
            <InviteTeamModal
                isOpen={isInviteModalOpen}
                onClose={() => setIsInviteModalOpen(false)}
                onInviteSent={fetchAllData}
            />
        </DashboardLayout>
    );
}

function ChevronRight(props: any) {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
            <path d="m9 18 6-6-6-6" />
        </svg>
    );
}
