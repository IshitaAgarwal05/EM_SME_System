import { useState, useEffect } from "react";
import { X, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import api from "../lib/api";

type CreateTaskModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
};

type Contractor = { id: string; name: string };
type Transaction = { id: string; description: string; amount: number; transaction_date: string };

export default function CreateTaskModal({ isOpen, onClose, onSuccess }: CreateTaskModalProps) {
    const { register, handleSubmit, reset, formState: { errors } } = useForm();
    const [loading, setLoading] = useState(false);
    const [contractors, setContractors] = useState<Contractor[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    useEffect(() => {
        if (isOpen) {
            fetchOptions();
        }
    }, [isOpen]);

    const fetchOptions = async () => {
        try {
            const [contRes, transRes] = await Promise.all([
                api.get("/financial/contractors"),
                api.get("/financial/transactions?reconciled=false")
            ]);
            setContractors(contRes.data.items || []);
            setTransactions(transRes.data.items || []);
        } catch (e) {
            console.error("Failed to fetch linking options", e);
        }
    };

    const onSubmit = async (data: any) => {
        setLoading(true);
        // Clean up empty optional fields
        const payload = { ...data };
        if (!payload.contractor_id) delete payload.contractor_id;
        if (!payload.transaction_id) delete payload.transaction_id;
        if (!payload.target_role) delete payload.target_role;
        if (!payload.due_date) delete payload.due_date;

        try {
            await api.post("/tasks", payload);
            reset();
            onSuccess();
            onClose();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-lg bg-white shadow-lg overflow-hidden">
                <div className="flex items-center justify-between border-b p-4">
                    <h3 className="text-lg font-semibold">Create New Task</h3>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="p-4 space-y-4 max-h-[80vh] overflow-y-auto">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Title</label>
                        <input
                            {...register("title", { required: "Title is required" })}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            placeholder="Task title"
                        />
                        {errors.title && <span className="text-xs text-red-500">{errors.title.message as string}</span>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Description</label>
                        <textarea
                            {...register("description")}
                            rows={2}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            placeholder="Description"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Priority</label>
                            <select
                                {...register("priority")}
                                defaultValue="medium"
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="urgent">Urgent</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">Due Date</label>
                            <input
                                type="date"
                                {...register("due_date")}
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    <div className="border-t pt-4 mt-4 space-y-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Resource & Finance Linking</h4>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">Linked Contractor</label>
                            <select
                                {...register("contractor_id")}
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                <option value="">No Contractor</option>
                                {contractors.map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">Target Role / Requirement</label>
                            <input
                                {...register("target_role")}
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                placeholder="e.g. Lead Decorator"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">Linked Transaction (optional)</label>
                            <select
                                {...register("transaction_id")}
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                <option value="">No Transaction</option>
                                {transactions.map(t => (
                                    <option key={t.id} value={t.id}>
                                        {t.transaction_date}: {t.description.substring(0, 20)}... (₹{t.amount})
                                    </option>
                                ))}
                            </select>
                            <p className="mt-1 text-[10px] text-gray-400">Linking a transaction helps automate reconciliation.</p>
                        </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-4 border-t">
                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex items-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                        >
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Task
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
