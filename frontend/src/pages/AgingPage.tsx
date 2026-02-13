import { useState, useEffect } from "react";
import api from "../lib/api";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { format } from "date-fns";
import { AlertTriangle, Clock } from "lucide-react";

export default function AgingPage() {
    const [agingData, setAgingData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchAging = async () => {
        try {
            const response = await api.get("/aging/receivables");
            setAgingData(response.data);
        } catch (error) {
            console.error("Failed to fetch aging data:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAging();
    }, []);

    const fmt = (val: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(val);
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Receivables Aging</h1>
                    <p className="text-sm text-gray-500 mt-1">Track outstanding invoices grouped by days overdue.</p>
                </div>

                {isLoading ? (
                    <div className="animate-pulse flex space-x-4">
                        <div className="flex-1 space-y-4 py-1">
                            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                            <div className="space-y-2">
                                <div className="h-20 bg-gray-200 rounded"></div>
                            </div>
                        </div>
                    </div>
                ) : agingData ? (
                    <>
                        {/* Summary Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                            <div className="bg-white p-5 py-6 rounded-xl border shadow-sm flex flex-col items-center justify-center text-center">
                                <span className="text-sm font-medium text-gray-500 mb-1">Total Outstanding</span>
                                <span className="text-2xl font-bold text-gray-900">{fmt(agingData.total_outstanding)}</span>
                            </div>
                            <div className="bg-emerald-50 p-5 py-6 rounded-xl border border-emerald-100 flex flex-col items-center justify-center text-center">
                                <span className="text-sm font-medium text-emerald-700 mb-1">Current (0-30 Days)</span>
                                <span className="text-2xl font-bold text-emerald-900">{fmt(agingData.summary.current)}</span>
                            </div>
                            <div className="bg-blue-50 p-5 py-6 rounded-xl border border-blue-100 flex flex-col items-center justify-center text-center">
                                <span className="text-sm font-medium text-blue-700 mb-1">31 - 60 Days</span>
                                <span className="text-2xl font-bold text-blue-900">{fmt(agingData.summary["31_60"])}</span>
                            </div>
                            <div className="bg-amber-50 p-5 py-6 rounded-xl border border-amber-100 flex flex-col items-center justify-center text-center">
                                <span className="text-sm font-medium text-amber-700 mb-1 flex items-center gap-1.5"><Clock className="w-4 h-4" /> 61 - 90 Days</span>
                                <span className="text-2xl font-bold text-amber-900">{fmt(agingData.summary["61_90"])}</span>
                            </div>
                            <div className="bg-rose-50 p-5 py-6 rounded-xl border border-rose-100 flex flex-col items-center justify-center text-center">
                                <span className="text-sm font-medium text-rose-700 mb-1 flex items-center gap-1.5"><AlertTriangle className="w-4 h-4" /> &gt; 90 Days</span>
                                <span className="text-2xl font-bold text-rose-900">{fmt(agingData.summary.over_90)}</span>
                            </div>
                        </div>

                        {/* Client Breakdown Table */}
                        <div className="rounded-xl border bg-white shadow-sm overflow-hidden mt-8">
                            <div className="px-6 py-4 border-b bg-gray-50 flex justify-between items-center">
                                <h2 className="font-semibold text-gray-800">Client Breakdown</h2>
                                <span className="text-xs text-gray-500 font-mono">As of {format(new Date(agingData.as_of_date), "MMM d, yyyy")}</span>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-white text-gray-500 text-xs uppercase tracking-wider border-b">
                                        <tr>
                                            <th className="px-6 py-3">Client</th>
                                            <th className="px-6 py-3 text-right">0-30 Days</th>
                                            <th className="px-6 py-3 text-right">31-60 Days</th>
                                            <th className="px-6 py-3 text-right">61-90 Days</th>
                                            <th className="px-6 py-3 text-right text-rose-600">&gt;90 Days</th>
                                            <th className="px-6 py-3 text-right font-bold text-gray-900">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {agingData.clients.length === 0 ? (
                                            <tr>
                                                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                                                    No outstanding receivables found. Great!
                                                </td>
                                            </tr>
                                        ) : (
                                            agingData.clients.map((client: any, i: number) => (
                                                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                                    <td className="px-6 py-4 font-medium text-gray-900">
                                                        {client.client}
                                                    </td>
                                                    <td className="px-6 py-4 text-right tabular-nums text-gray-600">
                                                        {client.buckets.current > 0 ? fmt(client.buckets.current) : "—"}
                                                    </td>
                                                    <td className="px-6 py-4 text-right tabular-nums text-gray-600">
                                                        {client.buckets["31_60"] > 0 ? fmt(client.buckets["31_60"]) : "—"}
                                                    </td>
                                                    <td className="px-6 py-4 text-right tabular-nums text-amber-600 font-medium">
                                                        {client.buckets["61_90"] > 0 ? fmt(client.buckets["61_90"]) : "—"}
                                                    </td>
                                                    <td className="px-6 py-4 text-right tabular-nums text-rose-600 font-bold">
                                                        {client.buckets.over_90 > 0 ? fmt(client.buckets.over_90) : "—"}
                                                    </td>
                                                    <td className="px-6 py-4 text-right font-bold text-gray-900 tabular-nums bg-gray-50/50">
                                                        {fmt(client.total_outstanding)}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="text-center py-12 text-gray-500 bg-white rounded-xl border">
                        Unable to load aging data.
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
