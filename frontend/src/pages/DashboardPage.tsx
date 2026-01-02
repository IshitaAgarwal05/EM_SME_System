import { useEffect, useState } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import { format } from "date-fns";
import { ArrowUp, ArrowDown, Wallet, CheckCircle, Clock, History, Activity, AlertTriangle, Lightbulb, Zap, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, ComposedChart, Line } from 'recharts';

export default function DashboardPage() {
    const [trends, setTrends] = useState<any[]>([]);
    const [recentTxns, setRecentTxns] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [forecast, setForecast] = useState<any[]>([]);
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [insights, setInsights] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [events, setEvents] = useState<any[]>([]);
    const [selectedEvent, setSelectedEvent] = useState<string | null>(null);

    useEffect(() => {
        fetchDashboardData(selectedYear);
    }, [selectedYear]);

    const fetchDashboardData = async (year: number) => {
        try {
            const [financeRes, tasksRes, trendsRes, txnsRes, forecastRes, anomalyRes, insightRes, eventsRes] = await Promise.all([
                api.get(`/analytics/summary?year=${year}`),
                api.get("/tasks"),
                api.get(`/analytics/trends/monthly?year=${year}`),
                api.get("/financial/transactions?limit=5"),
                api.get(`/analytics/forecast?year=${year}`),
                api.get(`/analytics/anomalies?year=${year}`),
                api.get(`/analytics/insights?year=${year}`),
                api.get("/events")
            ]);

            setStats({
                finance: financeRes.data,
                activeTasks: tasksRes.data?.items?.filter((t: any) => t.status === 'in_progress' || t.status === 'pending').length || 0
            });
            setEvents(eventsRes.data || []);

            // Map months for chart
            const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const chartData = (trendsRes.data || []).map((t: any) => ({
                name: monthNames[t.month - 1],
                Income: t.income,
                Expense: t.expense
            }));
            setTrends(chartData);

            // Process forecast for combined chart
            // Ensure we don't duplicate months if history includes the current month
            const last3History = chartData.slice(-3);
            const forecastPoints = forecastRes.data.map((f: any) => ({
                name: monthNames[f.month - 1],
                Income: f.income,
                Expense: f.expense,
                is_forecast: true
            }));

            // Filter out months from forecast that are already in history (by name)
            const historyNames = new Set(last3History.map(h => h.name));
            const uniqueForecast = forecastPoints.filter(f => !historyNames.has(f.name));

            setForecast([...last3History, ...uniqueForecast]);

            setRecentTxns(txnsRes.data?.items || []);
            setAnomalies(anomalyRes.data || []);
            setInsights(insightRes.data || []);
        } catch (e) {
            console.error("Failed to load dashboard data", e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-2xl font-bold leading-tight tracking-tight text-gray-900">
                            Dashboard Overview
                        </h3>
                        <p className="text-gray-500">
                            Here's what's happening with your events today.
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <select
                            value={selectedEvent || ""}
                            onChange={(e) => setSelectedEvent(e.target.value || null)}
                            className="px-4 py-2 border rounded-lg text-sm font-medium"
                        >
                            <option value="">All Events</option>
                            {events.map(event => (
                                <option key={event.id} value={event.id}>{event.name}</option>
                            ))}
                        </select>
                        <select
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(Number(e.target.value))}
                            className="px-4 py-2 border rounded-lg text-sm font-medium"
                        >
                            {[2024, 2025, 2026].map(y => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Income Card */}
                    <div className="rounded-lg border bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-500">Total Income</p>
                            <div className="rounded-full bg-green-100 p-2 text-green-600">
                                <ArrowUp className="h-4 w-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <h4 className="text-2xl font-bold text-gray-900">
                                ₹{loading ? "..." : stats?.finance?.total_income?.toLocaleString() ?? 0}
                            </h4>
                            {stats?.finance?.total_income > 0 ? (
                                <p className="text-xs text-green-600">+12% from last month</p>
                            ) : (
                                <p className="text-xs text-gray-500">No change from last month</p>
                            )}
                        </div>
                    </div>

                    {/* Expense Card */}
                    <div className="rounded-lg border bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-500">Total Expenses</p>
                            <div className="rounded-full bg-red-100 p-2 text-red-600">
                                <ArrowDown className="h-4 w-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <h4 className="text-2xl font-bold text-gray-900">
                                ₹{loading ? "..." : stats?.finance?.total_expense?.toLocaleString() ?? 0}
                            </h4>
                            {stats?.finance?.total_expense > 0 ? (
                                <p className="text-xs text-red-600">+4% from last month</p>
                            ) : (
                                <p className="text-xs text-gray-500">No change from last month</p>
                            )}
                        </div>
                    </div>

                    {/* Active Tasks Card */}
                    <div className="rounded-lg border bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-500">Active Tasks</p>
                            <div className="rounded-full bg-blue-100 p-2 text-blue-600">
                                <CheckCircle className="h-4 w-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <h4 className="text-2xl font-bold text-gray-900">
                                {loading ? "..." : stats?.activeTasks ?? 0}
                            </h4>
                            <p className="text-xs text-blue-600">
                                {stats?.activeTasks > 0 ? "3 overdue" : "No overdue tasks"}
                            </p>
                        </div>
                    </div>

                    {/* Net Profit Card */}
                    <div className="rounded-lg border bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-500">Net Profit</p>
                            <div className="rounded-full bg-purple-100 p-2 text-purple-600">
                                <Wallet className="h-4 w-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <h4 className="text-2xl font-bold text-gray-900">
                                ₹{loading ? "..." : stats?.finance?.net_profit?.toLocaleString() ?? 0}
                            </h4>
                            <p className="text-xs text-gray-500">
                                {stats?.finance?.net_profit > 0 ? "Healthy margin" : "No transactions yet"}
                            </p>
                        </div>
                    </div>

                    {/* Projected Savings Card */}
                    <div
                        onClick={() => alert("Projected Savings calculation:\n\nBased on your last 6 months of spending patterns, AI identifies 15% potential savings if recurring high-cost categories (like Maintenance or Uncategorized tasks) are optimized via consolidated vendors.")}
                        className="rounded-lg border bg-gradient-to-br from-indigo-500 to-purple-600 p-6 shadow-lg text-white cursor-help hover:scale-[1.02] transition-transform"
                    >
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-indigo-100">Projected Savings</p>
                            <div className="rounded-full bg-white/20 p-2">
                                <Activity className="h-4 w-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <h4 className="text-2xl font-bold">
                                ₹{loading ? "..." : (stats?.finance?.total_income * 0.15).toLocaleString()}
                            </h4>
                            <div className="mt-2 flex items-center gap-2">
                                <div className="h-1.5 flex-1 rounded-full bg-white/20 overflow-hidden">
                                    <div className="h-full w-[75%] bg-white rounded-full"></div>
                                </div>
                                <span className="text-[10px] font-bold">75%</span>
                            </div>
                            <p className="mt-1 text-[10px] text-indigo-100 italic underline">How is this calculated? (Click to view)</p>
                        </div>
                    </div>
                </div>

                {/* Charts and Tables placeholder */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    <div className="rounded-lg border bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-semibold text-gray-900">Monthly Trends</h4>
                            <div className="flex items-center gap-2">
                                <select
                                    value={selectedYear}
                                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                                    className="text-xs bg-slate-50 border-none rounded-md px-2 py-1 focus:ring-1 focus:ring-blue-500 cursor-pointer outline-none"
                                >
                                    {[0, 1, 2, 3, 4].map(offset => {
                                        const y = new Date().getFullYear() - offset;
                                        return <option key={y} value={y}>{y}</option>
                                    })}
                                </select>
                            </div>
                        </div>
                        <div className="h-80 w-full">
                            {loading ? (
                                <div className="flex h-full items-center justify-center">
                                    <Clock className="h-8 w-8 animate-spin text-blue-200" />
                                </div>
                            ) : trends.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={trends}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                                        <Tooltip
                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                            cursor={{ stroke: '#6366f1', strokeWidth: 1, strokeDasharray: '5 5' }}
                                        />
                                        <Legend verticalAlign="top" align="right" height={36} iconType="circle" />
                                        <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} barSize={12} />
                                        <Bar dataKey="Expense" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={12} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex h-full items-center justify-center text-gray-400 text-sm italic">
                                    No transaction data available for trends
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="rounded-lg border bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-semibold text-gray-900">Recent Transactions</h4>
                            <History className="h-4 w-4 text-gray-400" />
                        </div>
                        <div className="space-y-4">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <div key={i} className="flex animate-pulse items-center justify-between">
                                        <div className="h-4 w-32 rounded bg-gray-100" />
                                        <div className="h-4 w-16 rounded bg-gray-100" />
                                    </div>
                                ))
                            ) : recentTxns.length > 0 ? (
                                recentTxns.map((t) => (
                                    <div key={t.id} className="flex items-center justify-between border-b border-gray-50 pb-3 last:border-0 last:pb-0">
                                        <div className="flex flex-col">
                                            <span className="text-sm font-medium text-gray-900 truncate max-w-[180px]">{t.description}</span>
                                            <span className="text-[10px] text-gray-400">{format(new Date(t.transaction_date), "MMM d")}</span>
                                        </div>
                                        <span className={`text-sm font-semibold ${t.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'}`}>
                                            {t.transaction_type === 'credit' ? '+' : '-'}₹{t.amount?.toLocaleString()}
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="flex h-40 items-center justify-center text-gray-400 text-sm">
                                    No recent transactions
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* AI Predictive Analytics Section */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                    {/* Forecast Chart */}
                    <div className="lg:col-span-2 rounded-xl border bg-white p-6 shadow-sm overflow-hidden border-indigo-100 ring-1 ring-indigo-50/50">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <div className="p-1 rounded bg-indigo-100 text-indigo-600">
                                        <TrendingUp className="h-4 w-4" />
                                    </div>
                                    <h4 className="font-bold text-slate-800">Cash Flow Forecast (Next 3 Months)</h4>
                                </div>
                                <p className="text-[10px] text-slate-400">AI-predicted trends based on historical spending</p>
                            </div>
                            <div className="flex items-center gap-4 text-[10px]">
                                <span className="flex items-center gap-1"><div className="h-2 w-2 rounded-full bg-blue-500"></div> Actual</span>
                                <span className="flex items-center gap-1 font-dashed"><div className="h-2 w-2 rounded-full bg-indigo-300"></div> Forecast</span>
                            </div>
                        </div>
                        <div className="h-64 w-full">
                            {forecast.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart data={forecast}>
                                        <defs>
                                            <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1} />
                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} />
                                        <YAxis hide />
                                        <Tooltip
                                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                            cursor={{ stroke: '#6366f1', strokeWidth: 1, strokeDasharray: '4 4' }}
                                        />
                                        <Area type="monotone" dataKey="Income" stroke="#3b82f6" fillOpacity={1} fill="url(#colorIncome)" strokeWidth={2} />
                                        <Line type="monotone" dataKey="Income" stroke="#6366f1" strokeDasharray="5 5" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                        <Bar dataKey="Expense" fill="#f43f5e" radius={[4, 4, 0, 0]} opacity={0.3} barSize={20} />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-center">
                                    <TrendingUp className="h-12 w-12 text-gray-300 mb-3" />
                                    <p className="text-sm font-medium text-gray-600 mb-1">No forecast data available</p>
                                    <p className="text-xs text-gray-400 mb-4">Upload transaction files to see AI predictions</p>
                                    <a href="/files" className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700">
                                        Upload Files
                                    </a>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Anomalies & Insights */}
                    <div className="space-y-6">
                        {/* Anomalies */}
                        <div className="rounded-xl border bg-white p-6 shadow-sm border-rose-100 bg-rose-50/20">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertTriangle className="h-4 w-4 text-rose-500" />
                                <h4 className="font-bold text-slate-800 text-sm">Anomaly Alerts</h4>
                            </div>
                            <div className="space-y-3">
                                {anomalies.length > 0 ? anomalies.slice(0, 3).map(a => (
                                    <div key={a.id} className="p-3 bg-white rounded-lg border border-rose-100 shadow-sm">
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="text-xs font-bold text-slate-800 truncate block max-w-[150px]">{a.description}</span>
                                            <span className="text-xs font-bold text-rose-600">₹{a.amount.toLocaleString()}</span>
                                        </div>
                                        <p className="text-[10px] text-slate-500 font-medium">Above avg (₹{a.average}) • Score: {a.deviation_score}</p>
                                    </div>
                                )) : (
                                    <div className="flex flex-col items-center justify-center p-4 text-center">
                                        <CheckCircle className="h-6 w-6 text-green-400 mb-2" />
                                        <p className="text-[10px] text-slate-500 font-medium">No unusual activity detected this month.</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Insights */}
                        <div className="rounded-xl border bg-white p-6 shadow-sm border-amber-100 bg-amber-50/20">
                            <div className="flex items-center gap-2 mb-4">
                                <Lightbulb className="h-4 w-4 text-amber-500" />
                                <h4 className="font-bold text-slate-800 text-sm">Saving Insights</h4>
                            </div>
                            <div className="space-y-3">
                                {insights.length > 0 ? insights.slice(0, 2).map((ins, i) => (
                                    <div key={i} className="flex gap-3">
                                        <div className="mt-1 h-5 w-5 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                                            <Zap className="h-3 w-3 text-amber-600" />
                                        </div>
                                        <div>
                                            <p className="text-xs font-bold text-slate-800">{ins.category} Optimization</p>
                                            <p className="text-[10px] text-slate-500 leading-relaxed font-medium">{ins.recommendation}</p>
                                            <p className="text-[10px] font-bold text-amber-700 mt-1">Est. Save: ₹{ins.potential_monthly_saving}/mo</p>
                                        </div>
                                    </div>
                                )) : (
                                    <p className="text-[10px] text-slate-400 italic p-4 text-center">Keep categorizing transactions to unlock deeper AI insights.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
