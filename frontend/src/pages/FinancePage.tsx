import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import { format } from "date-fns";
import { PieChartIcon, TrendingUp, Users, Download, Zap, FileText, List as ListIcon, ArrowDownUp } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

type Transaction = {
    id: string;
    transaction_date: string;
    description: string;
    amount: number;
    transaction_type: "credit" | "debit";
    category?: string;
    is_reconciled: boolean;
};

const fmt = (n: number) => `₹${Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const neg = (n: number) => n < 0 ? `(${fmt(n)})` : fmt(n);

export default function FinancePage() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [plData, setPlData] = useState<any>(null);
    const [bsData, setBsData] = useState<any>(null);
    const [cfData, setCfData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [categorizing, setCategorizing] = useState(false);
    const [activeTab, setActiveTab] = useState("txns");
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editValue, setEditValue] = useState("");
    const [contractorSpend, setContractorSpend] = useState<any[]>([]);
    const [savedCategories, setSavedCategories] = useState<any[]>([]);
    const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
    const [newCategoryName, setNewCategoryName] = useState("");
    const [newCategoryType, setNewCategoryType] = useState("expense");
    const [insights, setInsights] = useState<any>(null);
    const [insightsLoading, setInsightsLoading] = useState(false);

    useEffect(() => {
        let cancelled = false;

        const run = async () => {
            // Clear year-scoped data immediately so stale data never shows
            setPlData(null);
            setCfData(null);
            setCategories([]);
            setContractorSpend([]);
            setLoading(true);

            try {
                // Single parallel fetch — year is captured in this closure, never stale
                const [txnsRes, catRes, contRes, savedCatRes, plRes, bsRes, cfRes] = await Promise.all([
                    api.get("/financial/transactions"),
                    api.get(`/analytics/breakdown/category?year=${selectedYear}`),
                    api.get(`/analytics/breakdown/contractors?year=${selectedYear}`),
                    api.get("/categories"),
                    api.get(`/financial/statements/pl?year=${selectedYear}`),
                    api.get(`/financial/statements/bs?year=${selectedYear}`),
                    api.get(`/financial/statements/cf?year=${selectedYear}`),
                ]);

                if (cancelled) return; // year changed again before we finished

                setTransactions(txnsRes.data.items || []);
                setCategories(
                    (catRes.data || []).map((item: any) => ({
                        name: item.category,
                        value: Math.abs(Number(item.amount))
                    })).sort((a: any, b: any) => b.value - a.value)
                );
                setContractorSpend(contRes.data || []);
                setSavedCategories(savedCatRes.data || []);
                setPlData(plRes.data);
                setBsData(bsRes.data);
                setCfData(cfRes.data);
            } catch (e) {
                if (!cancelled) console.error(e);
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        run();
        return () => { cancelled = true; }; // cancel if year changes before request finishes
    }, [selectedYear]);


    const fetchTransactions = async () => {
        try {
            const res = await api.get("/financial/transactions");
            setTransactions(res.data.items || []);
        } catch (e) { console.error(e); }
    };

    const handleCategorize = async () => { setCategorizing(true); setIsCategoryModalOpen(true); };

    const runCategorization = async (cats: string[]) => {
        try {
            const res = await api.post("/financial/transactions/categorize-all", { categories: cats });
            alert(`AI Categorization Complete! ${res.data.categorized_count} transactions updated.`);
            await fetchTransactions();
            setIsCategoryModalOpen(false);
        } catch (e) {
            console.error(e);
            alert("AI Categorization failed. Please check if OpenAI API key is configured.");
        } finally { setCategorizing(false); }
    };

    const handleAddCategory = async () => {
        if (!newCategoryName.trim()) return;
        try {
            const res = await api.post("/categories", { name: newCategoryName.trim(), category_type: newCategoryType });
            setSavedCategories([...savedCategories, res.data]);
            setNewCategoryName("");
        } catch (e: any) { alert(e.response?.data?.detail || "Failed to add category"); }
    };

    const handleUpdateCategory = async (id: string) => {
        try {
            await api.patch(`/financial/transactions/${id}`, { category: editValue });
            setTransactions(transactions.map(t => t.id === id ? { ...t, category: editValue } : t));
            setEditingId(null);
        } catch (e) { console.error(e); alert("Failed to update category"); }
    };

    const handleDownload = async () => {
        try {
            const response = await api.get('/financial/statements/export', { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'financial_statement.xlsx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) { console.error(e); }
    };

    /* ── Reusable statement row ───────────────────────────── */
    const StatRow = ({ label, amount, bold, indent, color, borderTop }: { label: string; amount: number; bold?: boolean; indent?: boolean; color?: string; borderTop?: boolean }) => (
        <div className={`flex justify-between py-1.5 text-sm ${borderTop ? 'border-t mt-2 pt-2' : ''} ${bold ? 'font-bold' : 'font-normal'} ${indent ? 'pl-6 text-gray-600' : ''}`}>
            <span style={color ? { color } : {}}>{label}</span>
            <span style={color ? { color } : {}} className={`font-mono ${bold ? 'font-bold' : ''}`}>{neg(amount)}</span>
        </div>
    );

    const SectionHead = ({ label, color = '#1e40af' }: { label: string; color?: string }) => (
        <div className="uppercase text-[10px] tracking-widest font-bold pb-1 border-b mb-2 mt-4" style={{ color }}>
            {label}
        </div>
    );

    const SubHead = ({ label }: { label: string }) => (
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">{label}</div>
    );

    const TotalRow = ({ label, amount, color }: { label: string; amount: number; color?: string }) => (
        <div className={`flex justify-between py-2 text-sm font-bold border-t-2 mt-1`} style={color ? { color } : {}}>
            <span>{label}</span>
            <span className="font-mono border-b-2 border-current">{neg(amount)}</span>
        </div>
    );

    return (
        <DashboardLayout>
            <div className="flex flex-col gap-6 pt-2">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight">Financial Hub</h2>
                        <p className="text-muted-foreground text-sm">Statements, AI Analysis, and Expenditure Tracking.</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <select
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                            className="text-xs bg-slate-100 border-none rounded-lg px-3 py-2 focus:ring-1 focus:ring-indigo-500 cursor-pointer outline-none font-bold text-slate-700"
                        >
                            {[0, 1, 2, 3, 4].map(offset => {
                                const y = new Date().getFullYear() - offset;
                                return <option key={y} value={y}>{y}</option>;
                            })}
                        </select>
                        <button onClick={handleCategorize} disabled={categorizing} className="flex items-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-bold hover:bg-indigo-100 transition-colors">
                            <Zap className={`h-3 w-3 ${categorizing ? 'animate-pulse' : ''}`} />
                            {categorizing ? "AI Analysis..." : "AI Categorization"}
                        </button>
                        <button onClick={handleDownload} className="flex items-center gap-2 px-3 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800 transition-colors">
                            <Download className="h-3 w-3" /> Export Excel
                        </button>
                    </div>
                </div>

                {/* Sub-tabs */}
                <div className="flex items-center border-b gap-4">
                    {[
                        { id: 'txns', icon: <ListIcon className="h-4 w-4" />, label: 'Transactions' },
                        { id: 'pl', icon: <TrendingUp className="h-4 w-4" />, label: 'Profit & Loss' },
                        { id: 'bs', icon: <FileText className="h-4 w-4" />, label: 'Balance Sheet' },
                        { id: 'cf', icon: <ArrowDownUp className="h-4 w-4" />, label: 'Cash Flow' },
                        { id: 'insights', icon: <Zap className="h-4 w-4" />, label: 'Insights' },
                    ].map(tab => (
                        <button key={tab.id} onClick={() => {
                            setActiveTab(tab.id);
                            if (tab.id === 'insights' && !insights) {
                                setInsightsLoading(true);
                                api.get('/insights/summary')
                                    .then(r => setInsights(r.data))
                                    .catch(console.error)
                                    .finally(() => setInsightsLoading(false));
                            }
                        }}
                            className={`pb-2 text-sm font-medium transition-colors ${activeTab === tab.id ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-900'}`}>
                            <div className="flex items-center gap-1">{tab.icon} {tab.label}</div>
                        </button>
                    ))}
                </div>

                {/* ── TRANSACTIONS TAB ─────────────────────────────────── */}
                {activeTab === 'txns' && (
                    <>
                        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                            <div className="lg:col-span-1 rounded-xl border bg-white p-6 shadow-sm">
                                <div className="flex items-center gap-2 mb-6">
                                    <PieChartIcon className="h-5 w-5 text-blue-500" />
                                    <h3 className="font-semibold text-gray-900">Spending by Category</h3>
                                </div>
                                <div className="h-64 w-full">
                                    {loading ? (
                                        <div className="flex h-full items-center justify-center">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                                        </div>
                                    ) : categories.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie data={categories} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                                                    {categories.map((_, index) => (
                                                        <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]} />
                                                    ))}
                                                </Pie>
                                                <Tooltip formatter={(value: any) => fmt(value)} />
                                                <Legend verticalAlign="bottom" height={36} iconType="circle" />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="flex h-full items-center justify-center text-gray-400 text-sm">No categorical data</div>
                                    )}
                                </div>
                            </div>

                            <div className="lg:col-span-2 rounded-xl border bg-white p-6 shadow-sm overflow-hidden">
                                <div className="flex items-center gap-2 mb-6">
                                    <Users className="h-5 w-5 text-purple-500" />
                                    <h3 className="font-semibold text-gray-900">Contractor Spends</h3>
                                </div>
                                <div className="space-y-4">
                                    {loading ? (
                                        Array(3).fill(0).map((_, i) => <div key={i} className="h-12 bg-gray-50 animate-pulse rounded-lg" />)
                                    ) : contractorSpend.length > 0 ? (
                                        contractorSpend.slice(0, 5).map((cs, idx) => (
                                            <div key={idx} className="flex items-center justify-between border-b border-gray-50 pb-2 last:border-0 last:pb-0 text-sm">
                                                <span className="font-medium text-gray-700">{cs.contractor}</span>
                                                <span className="font-bold text-gray-900">{fmt(cs.amount)}</span>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="flex h-40 items-center justify-center text-gray-400 text-sm italic">Payments show here when contractors are linked to reconciled transactions.</div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="rounded-md border bg-white shadow-sm overflow-hidden">
                            <div className="p-4 border-b bg-slate-50">
                                <h3 className="font-semibold text-sm">Transaction Ledger</h3>
                            </div>
                            <div className="relative w-full overflow-auto">
                                <table className="w-full caption-bottom text-sm">
                                    <thead className="[&_tr]:border-b bg-slate-50/50">
                                        <tr className="border-b">
                                            <th className="h-10 px-4 text-left align-middle font-bold text-slate-500 text-[10px] uppercase">Date</th>
                                            <th className="h-10 px-4 text-left align-middle font-bold text-slate-500 text-[10px] uppercase">Description</th>
                                            <th className="h-10 px-4 text-left align-middle font-bold text-slate-500 text-[10px] uppercase">Category</th>
                                            <th className="h-10 px-4 text-right align-middle font-bold text-slate-500 text-[10px] uppercase">Amount</th>
                                            <th className="h-10 px-4 text-center align-middle font-bold text-slate-500 text-[10px] uppercase">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="[&_tr:last-child]:border-0 font-medium">
                                        {transactions.length === 0 && !loading ? (
                                            <tr><td colSpan={5} className="p-4 text-center text-gray-400">No transactions recorded yet.</td></tr>
                                        ) : (
                                            transactions.map((t) => (
                                                <tr key={t.id} className="border-b transition-colors hover:bg-muted/50">
                                                    <td className="p-4 align-middle text-xs">{format(new Date(t.transaction_date), "MMM d, yyyy")}</td>
                                                    <td className="p-4 align-middle font-bold text-slate-800">{t.description}</td>
                                                    <td className="p-4 align-middle">
                                                        {editingId === t.id ? (
                                                            <div className="flex items-center gap-1">
                                                                <select value={editValue} onChange={(e) => setEditValue(e.target.value)}
                                                                    onKeyDown={(e) => e.key === 'Enter' && handleUpdateCategory(t.id)}
                                                                    className="w-32 px-2 py-1 border rounded text-[10px]" autoFocus>
                                                                    <option value="">Select category</option>
                                                                    {savedCategories.map(cat => (
                                                                        <option key={cat.id} value={cat.name}>{cat.name}</option>
                                                                    ))}
                                                                </select>
                                                                <button onClick={() => handleUpdateCategory(t.id)} className="text-blue-600 text-[10px] font-bold">Save</button>
                                                            </div>
                                                        ) : (
                                                            <span onClick={() => { setEditingId(t.id); setEditValue(t.category || ""); }}
                                                                className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600 cursor-pointer hover:bg-slate-200">
                                                                {t.category || "Uncategorized"}
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className={`p-4 align-middle text-right font-bold font-mono ${t.transaction_type === 'credit' ? 'text-emerald-600' : 'text-rose-600'}`}>
                                                        {t.transaction_type === "credit" ? "+" : "-"}{fmt(t.amount)}
                                                    </td>
                                                    <td className="p-4 align-middle text-center">
                                                        {t.is_reconciled ? (
                                                            <span className="inline-flex items-center rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700">Verified</span>
                                                        ) : (
                                                            <span className="inline-flex items-center rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Pending</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}

                {/* ── P&L TAB ── */}
                {activeTab === 'pl' && (
                    <div className="space-y-4">
                        {plData ? (
                            <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                                <div className="bg-[#cc0000] text-white text-center py-2">
                                    <h3 className="font-bold text-lg tracking-wide">Profit and Loss Statement</h3>
                                </div>
                                <div className="px-6 pt-3 pb-1 text-xs text-gray-600 flex justify-between items-start">
                                    <div>
                                        <div>Name of the Company: <span className="font-semibold">Your Organisation</span></div>
                                        <div>For the year: <span className="font-semibold">{plData.year}</span></div>
                                    </div>
                                    <div className="text-gray-400 italic">₹ in absolute</div>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm border-collapse">
                                        <thead>
                                            <tr className="bg-gray-100 text-gray-700">
                                                <th className="text-left px-4 py-2 border border-gray-200 w-[50%]">Particulars</th>
                                                <th className="text-center px-3 py-2 border border-gray-200 w-[8%]">Note No.</th>
                                                <th className="text-right px-4 py-2 border border-gray-200 w-[21%]">Figures as at the end of Current Reporting Period</th>
                                                <th className="text-right px-4 py-2 border border-gray-200 w-[21%]">Figures as at the end of the Previous Reporting Period</th>
                                            </tr>
                                            <tr className="bg-gray-50 text-xs text-gray-400">
                                                <td className="text-center px-4 py-1 border border-gray-200">1</td>
                                                <td className="text-center px-3 py-1 border border-gray-200">2</td>
                                                <td className="text-center px-4 py-1 border border-gray-200">3</td>
                                                <td className="text-center px-4 py-1 border border-gray-200">4</td>
                                            </tr>
                                        </thead>
                                        <tbody className="text-sm">
                                            {["revenue_from_ops", "other_income"].map(key => {
                                                const r = plData[key];
                                                return r ? (
                                                    <tr key={key} className="hover:bg-gray-50">
                                                        <td className="px-4 py-1.5 border border-gray-100">{r.name}</td>
                                                        <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                        <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                        <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                                    </tr>
                                                ) : null;
                                            })}
                                            {plData.total_revenue && (
                                                <tr className="bg-gray-50 font-bold">
                                                    <td className="px-4 py-2 border border-gray-200">{plData.total_revenue.name}</td>
                                                    <td className="px-3 py-2 border border-gray-200 text-center"></td>
                                                    <td className="px-4 py-2 border-t-2 border-gray-400 text-right font-mono">{fmt(plData.total_revenue.current)}</td>
                                                    <td className="px-4 py-2 border-t-2 border-gray-400 text-right font-mono text-gray-600">{fmt(plData.total_revenue.previous)}</td>
                                                </tr>
                                            )}
                                            <tr className="bg-gray-50">
                                                <td colSpan={4} className="px-4 py-1.5 border border-gray-100 font-semibold text-gray-700">IV. Expenses:</td>
                                            </tr>
                                            {["cost_of_materials", "purchases", "inventory_changes", "employee_expense", "finance_costs", "depreciation", "other_expenses"].map(key => {
                                                const r = plData[key];
                                                return r ? (
                                                    <tr key={key} className="hover:bg-gray-50">
                                                        <td className="px-4 py-1.5 pl-8 border border-gray-100 text-gray-700">{r.name}</td>
                                                        <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                        <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                        <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                                    </tr>
                                                ) : null;
                                            })}
                                            {plData.total_expenses && (
                                                <tr className="bg-gray-50 font-bold">
                                                    <td className="px-4 py-2 border border-gray-200">{plData.total_expenses.name}</td>
                                                    <td className="px-3 py-2 border border-gray-200 text-center"></td>
                                                    <td className="px-4 py-2 border-t-2 border-gray-400 text-right font-mono">{fmt(plData.total_expenses.current)}</td>
                                                    <td className="px-4 py-2 border-t-2 border-gray-400 text-right font-mono text-gray-600">{fmt(plData.total_expenses.previous)}</td>
                                                </tr>
                                            )}
                                            {plData.profit_before_tax && (
                                                <tr className={`font-bold ${plData.profit_before_tax.current >= 0 ? 'bg-emerald-50' : 'bg-rose-50'}`}>
                                                    <td className="px-4 py-2.5 border border-gray-200">{plData.profit_before_tax.name}</td>
                                                    <td className="px-3 py-2.5 border border-gray-200 text-center"></td>
                                                    <td className={`px-4 py-2.5 border-t-2 border-gray-500 text-right font-mono ${plData.profit_before_tax.current >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>{neg(plData.profit_before_tax.current)}</td>
                                                    <td className={`px-4 py-2.5 border-t-2 border-gray-500 text-right font-mono ${plData.profit_before_tax.previous >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>{neg(plData.profit_before_tax.previous)}</td>
                                                </tr>
                                            )}
                                            {plData.tax && (
                                                <tr className="hover:bg-gray-50 text-gray-500">
                                                    <td className="px-4 py-1.5 pl-8 border border-gray-100">{plData.tax.name}</td>
                                                    <td className="px-3 py-1.5 border border-gray-100 text-center"></td>
                                                    <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{plData.tax.current !== 0 ? `(${fmt(plData.tax.current)})` : '—'}</td>
                                                    <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{plData.tax.previous !== 0 ? `(${fmt(plData.tax.previous)})` : '—'}</td>
                                                </tr>
                                            )}
                                            {plData.profit_after_tax && (
                                                <tr className={`font-black text-base ${plData.profit_after_tax.current >= 0 ? 'bg-emerald-100' : 'bg-rose-100'}`}>
                                                    <td className="px-4 py-3 border border-gray-200">{plData.profit_after_tax.name}</td>
                                                    <td className="px-3 py-3 border border-gray-200 text-center"></td>
                                                    <td className={`px-4 py-3 border-t-4 border-double border-gray-600 text-right font-mono ${plData.profit_after_tax.current >= 0 ? 'text-emerald-800' : 'text-rose-800'}`}>{neg(plData.profit_after_tax.current)}</td>
                                                    <td className={`px-4 py-3 border-t-4 border-double border-gray-600 text-right font-mono ${plData.profit_after_tax.previous >= 0 ? 'text-emerald-800' : 'text-rose-800'}`}>{neg(plData.profit_after_tax.previous)}</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-40 text-gray-400">Loading P&L data…</div>
                        )}
                    </div>
                )}


                {/* ── BALANCE SHEET TAB ── */}
                {activeTab === 'bs' && (
                    <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                        <div className="bg-[#cc0000] text-white text-center py-2">
                            <h3 className="font-bold text-lg tracking-wide">Balance Sheet</h3>
                        </div>
                        {bsData && (
                            <div className="px-6 pt-3 pb-1 text-xs text-gray-600 space-y-0.5">
                                <div>Name of the Company: <span className="font-semibold">Your Organisation</span></div>
                                <div>Balance sheet as at: <span className="font-semibold">31 December {bsData.current_year ?? selectedYear}</span></div>
                                <div>Rupees in: <span className="font-semibold">absolute (₹)</span></div>
                            </div>
                        )}
                        {bsData ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm border-collapse">
                                    <thead>
                                        <tr className="bg-gray-100 text-gray-700">
                                            <th className="text-left px-4 py-2 border border-gray-200 w-[50%]">Particulars</th>
                                            <th className="text-center px-3 py-2 border border-gray-200 w-[8%]">Note No.</th>
                                            <th className="text-right px-4 py-2 border border-gray-200 w-[21%]">
                                                Figures as at the end of current reporting period<br />
                                                <span className="font-normal text-xs text-gray-500">{bsData.current_year}</span>
                                            </th>
                                            <th className="text-right px-4 py-2 border border-gray-200 w-[21%]">
                                                Figures as at the end of previous reporting period<br />
                                                <span className="font-normal text-xs text-gray-500">{bsData.previous_year}</span>
                                            </th>
                                        </tr>
                                        <tr className="bg-gray-50 text-xs text-gray-400">
                                            <td className="text-center px-4 py-1 border border-gray-200">1</td>
                                            <td className="text-center px-3 py-1 border border-gray-200">2</td>
                                            <td className="text-center px-4 py-1 border border-gray-200">3</td>
                                            <td className="text-center px-4 py-1 border border-gray-200">4</td>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="bg-[#cc0000] text-white">
                                            <td colSpan={4} className="px-4 py-2 font-bold tracking-wide">I. EQUITY AND LIABILITIES</td>
                                        </tr>
                                        <tr className="bg-gray-50">
                                            <td colSpan={4} className="px-4 py-1.5 font-semibold border border-gray-200">(1) Shareholder's Funds</td>
                                        </tr>
                                        {bsData.shareholder_funds && Object.values(bsData.shareholder_funds).map((r: any, i: number) => (
                                            <tr key={i} className="hover:bg-gray-50">
                                                <td className="px-4 py-1.5 pl-10 border border-gray-100">{r.name}</td>
                                                <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                            </tr>
                                        ))}
                                        <tr className="bg-gray-50">
                                            <td colSpan={4} className="px-4 py-1.5 font-semibold border border-gray-200">(3) Non-current Liabilities</td>
                                        </tr>
                                        {bsData.non_current_liabilities && Object.values(bsData.non_current_liabilities).map((r: any, i: number) => (
                                            <tr key={i} className="hover:bg-gray-50">
                                                <td className="px-4 py-1.5 pl-10 border border-gray-100">{r.name}</td>
                                                <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                            </tr>
                                        ))}
                                        <tr className="bg-gray-50">
                                            <td colSpan={4} className="px-4 py-1.5 font-semibold border border-gray-200">(4) Current Liabilities</td>
                                        </tr>
                                        {bsData.current_liabilities && Object.values(bsData.current_liabilities).map((r: any, i: number) => (
                                            <tr key={i} className="hover:bg-gray-50">
                                                <td className="px-4 py-1.5 pl-10 border border-gray-100">{r.name}</td>
                                                <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                            </tr>
                                        ))}
                                        {bsData.total_equity_liab && (
                                            <tr className="font-bold bg-gray-100 border-t-2 border-gray-400">
                                                <td className="px-4 py-2.5 border border-gray-200">{bsData.total_equity_liab.name}</td>
                                                <td className="px-3 py-2.5 border border-gray-200"></td>
                                                <td className="px-4 py-2.5 border-t-2 border-gray-500 text-right font-mono">{fmt(bsData.total_equity_liab.current)}</td>
                                                <td className="px-4 py-2.5 border-t-2 border-gray-500 text-right font-mono text-gray-600">{fmt(bsData.total_equity_liab.previous)}</td>
                                            </tr>
                                        )}
                                        <tr className="bg-[#cc0000] text-white">
                                            <td colSpan={4} className="px-4 py-2 font-bold tracking-wide">II. ASSETS</td>
                                        </tr>
                                        <tr className="bg-gray-50">
                                            <td colSpan={4} className="px-4 py-1.5 font-semibold border border-gray-200">Non-current Assets</td>
                                        </tr>
                                        <tr className="bg-gray-50/50">
                                            <td colSpan={4} className="px-4 py-1 pl-8 border border-gray-100 font-medium text-gray-600">(1) Fixed Assets</td>
                                        </tr>
                                        {bsData.non_current_assets && Object.values(bsData.non_current_assets).map((r: any, i: number) => (
                                            <tr key={i} className="hover:bg-gray-50">
                                                <td className="px-4 py-1.5 pl-14 border border-gray-100">{r.name}</td>
                                                <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                            </tr>
                                        ))}
                                        <tr className="bg-gray-50">
                                            <td colSpan={4} className="px-4 py-1.5 font-semibold border border-gray-200">(2) Current Assets</td>
                                        </tr>
                                        {bsData.current_assets && Object.values(bsData.current_assets).map((r: any, i: number) => (
                                            <tr key={i} className="hover:bg-gray-50">
                                                <td className="px-4 py-1.5 pl-10 border border-gray-100">{r.name}</td>
                                                <td className="px-3 py-1.5 border border-gray-100 text-center text-gray-400"></td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono">{r.current !== 0 ? fmt(r.current) : '—'}</td>
                                                <td className="px-4 py-1.5 border border-gray-100 text-right font-mono text-gray-500">{r.previous !== 0 ? fmt(r.previous) : '—'}</td>
                                            </tr>
                                        ))}
                                        {bsData.total_assets && (
                                            <tr className="font-bold bg-gray-100 border-t-2 border-gray-400">
                                                <td className="px-4 py-2.5 border border-gray-200">{bsData.total_assets.name}</td>
                                                <td className="px-3 py-2.5 border border-gray-200"></td>
                                                <td className="px-4 py-2.5 border-t-2 border-gray-500 text-right font-mono">{fmt(bsData.total_assets.current)}</td>
                                                <td className="px-4 py-2.5 border-t-2 border-gray-500 text-right font-mono text-gray-600">{fmt(bsData.total_assets.previous)}</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-40 text-gray-400">Loading Balance Sheet…</div>
                        )}
                    </div>
                )}

                {/* ── CASH FLOW TAB ── */}
                {activeTab === 'cf' && (
                    <div className="rounded-xl border bg-white shadow-sm">
                        <div className="p-6 border-b">
                            <h3 className="font-bold text-xl text-center">Statement of Cash Flows</h3>
                            <p className="text-center text-gray-500 text-xs mt-1 italic">For the year ended 31 December {selectedYear}</p>
                        </div>
                        {cfData ? (
                            <div className="p-6 max-w-2xl mx-auto">
                                <SectionHead label="A. Cash Flows from Operating Activities" color="#1d4ed8" />
                                <SubHead label="Cash Inflows" />
                                {(cfData.operating_inflows || []).map((r: any, i: number) => (
                                    <StatRow key={i} label={r.name} amount={r.amount} indent />
                                ))}
                                {(cfData.operating_inflows || []).length === 0 && (
                                    <p className="text-xs text-gray-400 pl-6 py-1 italic">No inflows for {selectedYear}</p>
                                )}
                                <SubHead label="Cash Outflows" />
                                {(cfData.operating_outflows || []).map((r: any, i: number) => (
                                    <StatRow key={i} label={r.name} amount={-r.amount} indent />
                                ))}
                                {(cfData.operating_outflows || []).length === 0 && (
                                    <p className="text-xs text-gray-400 pl-6 py-1 italic">No outflows for {selectedYear}</p>
                                )}
                                <TotalRow label="Net Cash from Operating Activities (A)" amount={cfData.net_operating ?? 0} color="#1d4ed8" />

                                <SectionHead label="B. Cash Flows from Investing Activities" color="#b45309" />
                                <p className="text-xs text-gray-400 pl-6 py-1 italic">No investing activities recorded.</p>
                                <TotalRow label="Net Cash from Investing Activities (B)" amount={0} color="#b45309" />

                                <SectionHead label="C. Cash Flows from Financing Activities" color="#7c3aed" />
                                {(cfData.financing_outflows || []).map((r: any, i: number) => (
                                    <StatRow key={i} label={r.name} amount={-r.amount} indent />
                                ))}
                                {(cfData.financing_outflows || []).length === 0 && (
                                    <p className="text-xs text-gray-400 pl-6 py-1 italic">No financing activities for {selectedYear}.</p>
                                )}
                                <TotalRow label="Net Cash from Financing Activities (C)" amount={cfData.net_financing ?? 0} color="#7c3aed" />

                                <div className="flex justify-between items-center py-3 bg-blue-50 border border-blue-100 rounded-lg px-4 my-4">
                                    <span className="font-bold text-blue-900 text-sm">Net Increase / (Decrease) in Cash (A+B+C)</span>
                                    <span className={`font-bold font-mono ${(cfData.net_change ?? 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>{neg(cfData.net_change ?? 0)}</span>
                                </div>
                                <StatRow label="Cash & Cash Equivalents — Opening Balance" amount={cfData.opening_balance ?? 0} />
                                <div className="flex justify-between items-center py-3 bg-green-50 border-2 border-green-200 rounded-xl px-4 mt-2">
                                    <span className="font-black text-base">Cash & Cash Equivalents — Closing Balance</span>
                                    <span className={`font-black font-mono text-xl ${(cfData.closing_balance ?? 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>{neg(cfData.closing_balance ?? 0)}</span>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-40 text-gray-400">Loading Cash Flow Statement…</div>
                        )}
                    </div>
                )}
            </div>

            {/* ── INSIGHTS TAB ─────────────────────────────────── */}
            {activeTab === 'insights' && (
                <div className="space-y-6">
                    {insightsLoading ? (
                        <div className="flex items-center justify-center h-48 text-gray-400">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3" />
                            Loading insights...
                        </div>
                    ) : !insights ? (
                        <div className="flex items-center justify-center h-48 text-gray-400">No insights available yet. Add invoices and transactions first.</div>
                    ) : (
                        <>
                            {/* Revenue Concentration Risk */}
                            {insights.revenue_concentration && (
                                <div className={`rounded-xl border p-5 ${insights.revenue_concentration.risk === 'HIGH' ? 'bg-rose-50 border-rose-200' :
                                        insights.revenue_concentration.risk === 'MEDIUM' ? 'bg-amber-50 border-amber-200' :
                                            'bg-emerald-50 border-emerald-200'
                                    }`}>
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-semibold text-gray-900">Revenue Concentration Risk</h3>
                                            <p className="text-sm text-gray-600 mt-1">
                                                Top client contributes <strong>{insights.revenue_concentration.top_client_share_pct?.toFixed(1)}%</strong> of total revenue.
                                            </p>
                                        </div>
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${insights.revenue_concentration.risk === 'HIGH' ? 'bg-rose-600 text-white' :
                                                insights.revenue_concentration.risk === 'MEDIUM' ? 'bg-amber-500 text-white' :
                                                    'bg-emerald-600 text-white'
                                            }`}>{insights.revenue_concentration.risk} RISK</span>
                                    </div>
                                </div>
                            )}

                            {/* Month-on-Month Profitability Trend */}
                            {insights.profitability_trend?.length > 0 && (
                                <div className="rounded-xl border bg-white p-6 shadow-sm">
                                    <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                        <TrendingUp className="h-4 w-4 text-blue-500" />
                                        Monthly Net Profit
                                    </h3>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                                        {insights.profitability_trend.slice(-12).map((m: any) => (
                                            <div key={m.month} className={`p-3 rounded-lg border text-center ${m.net_profit >= 0 ? 'bg-emerald-50 border-emerald-100' : 'bg-rose-50 border-rose-100'}`}>
                                                <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wide mb-1">{m.month}</div>
                                                <div className={`text-sm font-bold ${m.net_profit >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                                                    {m.net_profit >= 0 ? '+' : ''}{fmt(m.net_profit)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Top Clients Table */}
                            {insights.client_profitability?.length > 0 && (
                                <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                                    <div className="px-6 py-4 border-b bg-gray-50 font-semibold text-gray-800 flex items-center gap-2">
                                        <Users className="h-4 w-4 text-purple-500" />
                                        Client Revenue Breakdown
                                    </div>
                                    <table className="w-full text-sm">
                                        <thead className="bg-white text-gray-500 text-xs uppercase tracking-wide border-b">
                                            <tr>
                                                <th className="px-6 py-3 text-left">Client</th>
                                                <th className="px-6 py-3 text-right">Revenue</th>
                                                <th className="px-6 py-3 text-right">Share</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {insights.client_profitability.map((c: any, i: number) => (
                                                <tr key={i} className="hover:bg-gray-50/50">
                                                    <td className="px-6 py-3 font-medium text-gray-900">{c.client_name}</td>
                                                    <td className="px-6 py-3 text-right tabular-nums text-gray-700">{fmt(c.total_revenue)}</td>
                                                    <td className="px-6 py-3 text-right">
                                                        <div className="flex items-center justify-end gap-2">
                                                            <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${c.share_pct}%` }} />
                                                            </div>
                                                            <span className="text-xs text-gray-500 font-mono w-10 text-right">{c.share_pct?.toFixed(1)}%</span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {/* Expense Spikes */}
                            {insights.expense_spikes?.length > 0 && (
                                <div className="rounded-xl border bg-amber-50 border-amber-200 p-5">
                                    <h3 className="font-semibold text-amber-900 mb-3">⚡ Expense Spikes Detected</h3>
                                    <div className="space-y-2">
                                        {insights.expense_spikes.map((s: any, i: number) => (
                                            <div key={i} className="flex justify-between text-sm text-amber-800">
                                                <span>{s.category} — {s.month}</span>
                                                <span className="font-bold">+{s.spike_pct?.toFixed(0)}% MoM</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* AI Categorization Modal */}
            {isCategoryModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setIsCategoryModalOpen(false)}>
                    <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
                        <h3 className="text-lg font-bold mb-4">AI Categorization</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Saved Categories</label>
                                <div className="flex flex-wrap gap-2 p-3 bg-slate-50 rounded-lg max-h-32 overflow-y-auto">
                                    {savedCategories.length > 0 ? (
                                        savedCategories.map(cat => (
                                            <span key={cat.id} className="inline-flex items-center px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">{cat.name}</span>
                                        ))
                                    ) : (
                                        <p className="text-sm text-gray-500">No categories yet. Add some below!</p>
                                    )}
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Add New Category</label>
                                <div className="flex gap-2">
                                    <input type="text" value={newCategoryName} onChange={(e) => setNewCategoryName(e.target.value)}
                                        placeholder="e.g., Travel, Food, Office" className="flex-1 px-3 py-2 border rounded-lg text-sm"
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddCategory()} />
                                    <select value={newCategoryType} onChange={(e) => setNewCategoryType(e.target.value)} className="px-3 py-2 border rounded-lg text-sm">
                                        <option value="expense">Expense</option>
                                        <option value="income">Income</option>
                                    </select>
                                    <button onClick={handleAddCategory} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">Add</button>
                                </div>
                            </div>
                            <div className="flex gap-2 pt-4 border-t">
                                <button onClick={() => setIsCategoryModalOpen(false)} className="flex-1 px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50">Cancel</button>
                                <button onClick={() => runCategorization(savedCategories.map(c => c.name))}
                                    disabled={categorizing || savedCategories.length === 0}
                                    className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">
                                    {categorizing ? "Categorizing..." : "Run AI Categorization"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
