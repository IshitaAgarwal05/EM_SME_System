import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import { format } from "date-fns";
import { PieChartIcon, TrendingUp, Users, Download, Zap, FileText, List as ListIcon } from "lucide-react";
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

export default function FinancePage() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [plData, setPlData] = useState<any>(null);
    const [bsData, setBsData] = useState<any>(null);
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

    const fetchStatements = async (year: number) => {
        try {
            const [plRes, bsRes] = await Promise.all([
                api.get(`/financial/statements/pl?year=${year}`),
                api.get("/financial/statements/bs")
            ]);
            setPlData(plRes.data);
            setBsData(bsRes.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        const fetchAllData = async () => {
            setLoading(true);
            try {
                const [txnsRes, catRes, contRes, savedCatRes] = await Promise.all([
                    api.get("/financial/transactions"),
                    api.get(`/analytics/breakdown/category`), // All-time by default
                    api.get(`/analytics/breakdown/contractors?year=${selectedYear}`),
                    api.get("/categories")
                ]);
                setTransactions(txnsRes.data.items || []);

                // Process categories for pie chart
                const catData = (catRes.data || []).map((item: any) => ({
                    name: item.category,
                    value: Math.abs(Number(item.amount))
                })).sort((a: any, b: any) => b.value - a.value);
                setCategories(catData);

                setContractorSpend(contRes.data || []);
                setSavedCategories(savedCatRes.data || []);
                await fetchStatements(selectedYear);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchAllData();
    }, [selectedYear]);

    const fetchTransactions = async () => {
        try {
            const res = await api.get("/financial/transactions");
            setTransactions(res.data.items || []);
        } catch (e) {
            console.error(e);
        }
    };

    const handleCategorize = async () => {
        setCategorizing(true);
        setIsCategoryModalOpen(true);
    };

    const runCategorization = async (categories: string[]) => {
        try {
            const res = await api.post("/financial/transactions/categorize-all", { categories });
            alert(`AI Categorization Complete! ${res.data.categorized_count} transactions updated.`);
            await fetchTransactions();
            setIsCategoryModalOpen(false);
        } catch (e) {
            console.error(e);
            alert("AI Categorization failed. Please check if OpenAI API key is configured.");
        } finally {
            setCategorizing(false);
        }
    };

    const handleAddCategory = async () => {
        if (!newCategoryName.trim()) return;

        try {
            const res = await api.post("/categories", {
                name: newCategoryName.trim(),
                category_type: newCategoryType
            });
            setSavedCategories([...savedCategories, res.data]);
            setNewCategoryName("");
        } catch (e: any) {
            alert(e.response?.data?.detail || "Failed to add category");
        }
    };

    const handleUpdateCategory = async (id: string) => {
        try {
            await api.patch(`/financial/transactions/${id}`, { category: editValue });
            setTransactions(transactions.map(t => t.id === id ? { ...t, category: editValue } : t));
            setEditingId(null);
        } catch (e) {
            console.error(e);
            alert("Failed to update category");
        }
    };

    const handleDownload = async () => {
        try {
            const response = await api.get('/financial/statements/export', {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'financial_statement.xlsx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <DashboardLayout>
            <div className="flex flex-col gap-6 pt-2">
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
                                return <option key={y} value={y}>{y}</option>
                            })}
                        </select>
                        <button
                            onClick={handleCategorize}
                            disabled={categorizing}
                            className="flex items-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-bold hover:bg-indigo-100 transition-colors"
                        >
                            <Zap className={`h-3 w-3 ${categorizing ? 'animate-pulse' : ''}`} />
                            {categorizing ? "AI Analysis..." : "AI Categorization"}
                        </button>
                        <button
                            onClick={handleDownload}
                            className="flex items-center gap-2 px-3 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800 transition-colors"
                        >
                            <Download className="h-3 w-3" />
                            Export Excel
                        </button>
                    </div>
                </div>

                {/* Sub-tabs Navigation */}
                <div className="flex items-center border-b gap-4">
                    <button
                        onClick={() => setActiveTab("txns")}
                        className={`pb-2 text-sm font-medium transition-colors ${activeTab === 'txns' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-900'}`}
                    >
                        <div className="flex items-center gap-1">
                            <ListIcon className="h-4 w-4" /> Transactions
                        </div>
                    </button>
                    <button
                        onClick={() => setActiveTab("pl")}
                        className={`pb-2 text-sm font-medium transition-colors ${activeTab === 'pl' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-900'}`}
                    >
                        <div className="flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" /> Profit & Loss
                        </div>
                    </button>
                    <button
                        onClick={() => setActiveTab("bs")}
                        className={`pb-2 text-sm font-medium transition-colors ${activeTab === 'bs' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-900'}`}
                    >
                        <div className="flex items-center gap-1">
                            <FileText className="h-4 w-4" /> Balance Sheet
                        </div>
                    </button>
                </div>

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
                                                <Pie
                                                    data={categories}
                                                    innerRadius={60}
                                                    outerRadius={80}
                                                    paddingAngle={5}
                                                    dataKey="value"
                                                >
                                                    {categories.map((_, index) => (
                                                        <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]} />
                                                    ))}
                                                </Pie>
                                                <Tooltip formatter={(value: any) => `\u20b9${(value || 0).toLocaleString()}`} />
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
                                                <span className="font-bold text-gray-900">\u20b9{cs.amount?.toLocaleString()}</span>
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
                                        <tr className="border-b transition-colors hover:bg-muted/50">
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
                                                                <select
                                                                    value={editValue}
                                                                    onChange={(e) => setEditValue(e.target.value)}
                                                                    onKeyDown={(e) => e.key === 'Enter' && handleUpdateCategory(t.id)}
                                                                    className="w-32 px-2 py-1 border rounded text-[10px]"
                                                                    autoFocus
                                                                >
                                                                    <option value="">Select category</option>
                                                                    {savedCategories.map(cat => (
                                                                        <option key={cat.id} value={cat.name}>{cat.name}</option>
                                                                    ))}
                                                                </select>
                                                                <button onClick={() => handleUpdateCategory(t.id)} className="text-blue-600 text-[10px] font-bold">Save</button>
                                                            </div>
                                                        ) : (
                                                            <span
                                                                onClick={() => { setEditingId(t.id); setEditValue(t.category || ""); }}
                                                                className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600 cursor-pointer hover:bg-slate-200"
                                                            >
                                                                {t.category || "Uncategorized"}
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className={`p-4 align-middle text-right font-bold ${t.transaction_type === 'credit' ? 'text-emerald-600' : 'text-rose-600'}`}>
                                                        {t.transaction_type === "credit" ? "+" : "-"}\u20b9{t.amount.toLocaleString()}
                                                    </td>
                                                    <td className="p-4 align-middle text-center">
                                                        {t.is_reconciled ? (
                                                            <span className="inline-flex items-center rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700">Verified</span>
                                                        ) : (
                                                            <span className="inline-flex items-center rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Audit Req.</span>
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

                {activeTab === 'pl' && plData && (
                    <div className="space-y-6">
                        <div className="rounded-xl border bg-white p-6 shadow-sm">
                            <h3 className="font-bold text-lg mb-4">Profit & Loss Statement ({plData.year})</h3>
                            <div className="h-64 w-full mb-8">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={plData.expenses}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis dataKey="category" tick={{ fontSize: 10 }} />
                                        <YAxis tick={{ fontSize: 10 }} />
                                        <Tooltip />
                                        <Bar dataKey="amount" fill="#ef4444" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="space-y-2 border-t pt-4">
                                <div className="flex justify-between font-bold py-2 border-b">
                                    <span>Operating Income</span>
                                    <span>\u20b9{plData.total_income.toLocaleString()}</span>
                                </div>
                                {plData.income.map((item: any, idx: number) => (
                                    <div key={idx} className="flex justify-between text-sm py-1 border-b text-gray-600">
                                        <span>{item.category}</span>
                                        <span>\u20b9{item.amount.toLocaleString()}</span>
                                    </div>
                                ))}
                                <div className="flex justify-between font-bold py-2 mt-4 text-emerald-600 border-t">
                                    <span>Gross Profit</span>
                                    <span>\u20b9{plData.gross_profit.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between font-bold py-2 text-rose-600">
                                    <span>Total Expenses</span>
                                    <span>-\u20b9{plData.total_expense.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between font-bold py-4 text-xl border-t-2">
                                    <span>Net Operating Income</span>
                                    <span className={plData.net_profit >= 0 ? "text-emerald-700" : "text-rose-700"}>
                                        \u20b9{plData.net_profit.toLocaleString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'bs' && bsData && (
                    <div className="rounded-xl border bg-white p-8 shadow-sm">
                        <div className="max-w-2xl mx-auto">
                            <h3 className="font-bold text-2xl text-center mb-2">Statement of Financial Position</h3>
                            <p className="text-center text-gray-500 text-sm mb-8 italic">As of {format(new Date(), "MMMM d, yyyy")}</p>

                            <div className="space-y-4">
                                <div>
                                    <h4 className="font-bold text-blue-600 border-b pb-1 mb-2 uppercase text-xs tracking-wider">ASSETS</h4>
                                    <div className="space-y-2 text-sm">
                                        {bsData.assets.map((a: any, i: number) => (
                                            <div key={i} className="flex justify-between">
                                                <span>{a.name}</span>
                                                <span className="font-bold">\u20b9{a.amount.toLocaleString()}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="flex justify-between font-bold pt-2 mt-1 border-t">
                                        <span>Total Assets</span>
                                        <span>\u20b9{bsData.total_assets.toLocaleString()}</span>
                                    </div>
                                </div>
                                <div className="pt-4">
                                    <h4 className="font-bold text-rose-600 border-b pb-1 mb-2 uppercase text-xs tracking-wider">LIABILITIES & EQUITY</h4>
                                    <div className="space-y-2 text-sm">
                                        {bsData.liabilities.map((l: any, i: number) => (
                                            <div key={i} className="flex justify-between">
                                                <span>{l.name}</span>
                                                <span className="font-bold">\u20b9{l.amount.toLocaleString()}</span>
                                            </div>
                                        ))}
                                        <div className="flex justify-between pt-2 border-t font-medium">
                                            <span>Retained Earnings / Equity</span>
                                            <span className="font-bold">\u20b9{bsData.equity.toLocaleString()}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="pt-8 flex justify-between border-t-2 font-bold text-lg">
                                    <span>TOTAL LIABILITIES & EQUITY</span>
                                    <span className="text-indigo-600">\u20b9{bsData.total_liabilities_equity.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

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
                                            <span key={cat.id} className="inline-flex items-center px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">
                                                {cat.name}
                                            </span>
                                        ))
                                    ) : (
                                        <p className="text-sm text-gray-500">No categories yet. Add some below!</p>
                                    )}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">Add New Category</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={newCategoryName}
                                        onChange={(e) => setNewCategoryName(e.target.value)}
                                        placeholder="e.g., Travel, Food, Office"
                                        className="flex-1 px-3 py-2 border rounded-lg text-sm"
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddCategory()}
                                    />
                                    <select
                                        value={newCategoryType}
                                        onChange={(e) => setNewCategoryType(e.target.value)}
                                        className="px-3 py-2 border rounded-lg text-sm"
                                    >
                                        <option value="expense">Expense</option>
                                        <option value="income">Income</option>
                                    </select>
                                    <button
                                        onClick={handleAddCategory}
                                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
                                    >
                                        Add
                                    </button>
                                </div>
                            </div>

                            <div className="flex gap-2 pt-4 border-t">
                                <button
                                    onClick={() => setIsCategoryModalOpen(false)}
                                    className="flex-1 px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => runCategorization(savedCategories.map(c => c.name))}
                                    disabled={categorizing || savedCategories.length === 0}
                                    className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
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
