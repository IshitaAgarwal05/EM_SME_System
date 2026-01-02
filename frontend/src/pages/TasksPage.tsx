import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import type { Task } from "../types";
import { Plus, Search } from "lucide-react";
import { format } from "date-fns";
import CreateTaskModal from "../components/CreateTaskModal";

export default function TasksPage() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState<string>("all");
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    useEffect(() => {
        fetchTasks();
    }, [filterStatus]);

    const handleStatusChange = async (taskId: string, newStatus: string) => {
        try {
            await api.patch(`/tasks/${taskId}`, { status: newStatus });
            setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t));
        } catch (err) {
            console.error("Failed to update status", err);
        }
    };

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const params = filterStatus !== "all" ? { status: filterStatus } : {};
            // In a real app we might want to include assignments.user relation
            const res = await api.get("/tasks", { params });
            setTasks(res.data.items || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight">Tasks</h2>
                        <p className="text-muted-foreground">Manage your team's tasks and projects.</p>
                    </div>
                    <button
                        className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-slate-900 text-slate-50 hover:bg-slate-900/90 h-10 px-4 py-2"
                        onClick={() => setIsCreateModalOpen(true)}
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        New Task
                    </button>
                </div>

                <CreateTaskModal
                    isOpen={isCreateModalOpen}
                    onClose={() => setIsCreateModalOpen(false)}
                    onSuccess={fetchTasks}
                />

                <div className="flex items-center gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <input
                            placeholder="Search tasks..."
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-8"
                        />
                    </div>
                    <select
                        className="flex h-10 items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 w-[180px]"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                    >
                        <option value="all">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                    </select>
                </div>

                <div className="rounded-md border bg-white">
                    <div className="relative w-full overflow-auto">
                        <table className="w-full caption-bottom text-sm">
                            <thead className="[&_tr]:border-b">
                                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Title</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Priority</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Contractor / Role</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Due Date</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Links</th>
                                </tr>
                            </thead>
                            <tbody className="[&_tr:last-child]:border-0">
                                {tasks.length === 0 && !loading ? (
                                    <tr>
                                        <td colSpan={6} className="p-4 text-center text-muted-foreground">No tasks found</td>
                                    </tr>
                                ) : (
                                    tasks.map((task) => (
                                        <tr key={task.id} className="border-b transition-colors hover:bg-muted/50">
                                            <td className="p-4 align-middle font-medium">
                                                <div className="flex flex-col">
                                                    <span>{task.title}</span>
                                                    {task.description && <span className="text-[10px] text-gray-400 truncate max-w-[200px]">{task.description}</span>}
                                                </div>
                                            </td>
                                            <td className="p-4 align-middle">
                                                <select
                                                    value={task.status}
                                                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                                                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border-0 cursor-pointer focus:ring-2 focus:ring-ring
                                                    ${task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                            task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                                                task.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                                    'bg-slate-100 text-slate-800'}`}
                                                >
                                                    <option value="pending">Pending</option>
                                                    <option value="in_progress">In Progress</option>
                                                    <option value="review">Review</option>
                                                    <option value="completed">Completed</option>
                                                    <option value="cancelled">Cancelled</option>
                                                    <option value="on_hold">On Hold</option>
                                                </select>
                                            </td>
                                            <td className="p-4 align-middle capitalize">
                                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${task.priority === 'urgent' ? 'bg-red-100 text-red-700' : task.priority === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 text-slate-700'}`}>
                                                    {task.priority}
                                                </span>
                                            </td>
                                            <td className="p-4 align-middle">
                                                <div className="flex flex-col">
                                                    <span className="font-medium text-slate-700">{task.contractor_id ? "Linked Partner" : "-"}</span>
                                                    {task.target_role && <span className="text-[10px] text-slate-400 capitalize">{task.target_role}</span>}
                                                </div>
                                            </td>
                                            <td className="p-4 align-middle whitespace-nowrap">
                                                {task.due_date ? format(new Date(task.due_date), "MMM d, yyyy") : "-"}
                                            </td>
                                            <td className="p-4 align-middle">
                                                <div className="flex items-center gap-2">
                                                    {task.transaction_id && (
                                                        <div className="h-6 w-6 rounded-full bg-green-50 flex items-center justify-center text-green-600" title="Linked to Transaction">
                                                            <Plus className="h-3 w-3 rotate-45" />
                                                        </div>
                                                    )}
                                                    <div className="flex -space-x-2">
                                                        {task.assignments?.map((a, i) => (
                                                            <div key={i} className="h-6 w-6 rounded-full bg-slate-200 border border-white flex items-center justify-center text-[10px]" title={a.user?.full_name}>
                                                                {a.user?.full_name?.charAt(0)}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
