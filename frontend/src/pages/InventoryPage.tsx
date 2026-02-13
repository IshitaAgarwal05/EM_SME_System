import { useState, useEffect } from "react";
import api from "../lib/api";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { format } from "date-fns";
import { Plus, AlertTriangle, X, TrendingUp, BarChart3 } from "lucide-react";

export default function InventoryPage() {
    const [items, setItems] = useState<any[]>([]);
    const [lowStock, setLowStock] = useState<any[]>([]);
    const [sales, setSales] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"catalog" | "low-stock" | "sales">("catalog");
    const [showModal, setShowModal] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Form state
    const [name, setName] = useState("");
    const [sku, setSku] = useState("");
    const [unit, setUnit] = useState("pcs");
    const [costPrice, setCostPrice] = useState("");
    const [salePrice, setSalePrice] = useState("");
    const [openingQty, setOpeningQty] = useState("0");
    const [reorderLevel, setReorderLevel] = useState("10");
    const [cgstRate, setCgstRate] = useState("9");
    const [sgstRate, setSgstRate] = useState("9");
    const [igstRate, setIgstRate] = useState("0");

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [itemsRes, lowRes, salesRes] = await Promise.all([
                api.get("/inventory/items"),
                api.get("/inventory/low-stock"),
                api.get("/inventory/sales-summary"),
            ]);
            setItems(itemsRes.data || []);
            setLowStock(lowRes.data || []);
            setSales(salesRes.data || []);
        } catch (error) {
            console.error("Failed to fetch inventory:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const resetForm = () => {
        setName(""); setSku(""); setUnit("pcs");
        setCostPrice(""); setSalePrice(""); setOpeningQty("0");
        setReorderLevel("10"); setCgstRate("9"); setSgstRate("9"); setIgstRate("0");
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim() || !costPrice || !salePrice) {
            alert("Name, cost price, and sale price are required.");
            return;
        }
        setSubmitting(true);
        try {
            const item = await api.post("/inventory/items", {
                name: name.trim(),
                sku: sku.trim() || `ITEM-${Date.now()}`,
                unit: unit.trim() || "pcs",
                cost_price: parseFloat(costPrice),
                sale_price: parseFloat(salePrice),
                reorder_level: parseInt(reorderLevel) || 0,
                cgst_rate: parseFloat(cgstRate) || 0,
                sgst_rate: parseFloat(sgstRate) || 0,
                igst_rate: parseFloat(igstRate) || 0,
            });
            // Set opening stock
            if (parseInt(openingQty) > 0) {
                await api.post("/inventory/movements", {
                    item_id: item.data.id,
                    movement_type: "adjustment",
                    qty: parseInt(openingQty),
                    movement_date: format(new Date(), "yyyy-MM-dd"),
                    notes: "Opening stock",
                });
            }
            setShowModal(false);
            resetForm();
            await fetchData();
        } catch (err: any) {
            alert(err.response?.data?.detail || "Failed to add item.");
        } finally {
            setSubmitting(false);
        }
    };

    const fmt = (val: number) =>
        new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(val);

    const totalSalesValue = sales.reduce((s, r) => s + r.total_sale_value, 0);
    const totalSoldQty = sales.reduce((s, r) => s + r.total_sold_qty, 0);

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
                        <p className="text-sm text-gray-500 mt-1">Track products, stock levels, and sales performance.</p>
                    </div>
                    <button
                        onClick={() => setShowModal(true)}
                        className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 transition-colors shadow-sm"
                    >
                        <Plus className="h-4 w-4" /> Add Item
                    </button>
                </div>

                {/* Summary Cards for Sales tab */}
                {activeTab === "sales" && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <div className="bg-white border rounded-xl p-5 shadow-sm">
                            <div className="text-xs font-medium text-gray-500 mb-1">Total Sales Value</div>
                            <div className="text-2xl font-bold text-gray-900">{fmt(totalSalesValue)}</div>
                        </div>
                        <div className="bg-white border rounded-xl p-5 shadow-sm">
                            <div className="text-xs font-medium text-gray-500 mb-1">Units Sold</div>
                            <div className="text-2xl font-bold text-gray-900">{totalSoldQty.toLocaleString("en-IN")}</div>
                        </div>
                        <div className="bg-white border rounded-xl p-5 shadow-sm">
                            <div className="text-xs font-medium text-gray-500 mb-1">Products with Sales</div>
                            <div className="text-2xl font-bold text-gray-900">{sales.filter(s => s.total_sold_qty > 0).length}</div>
                        </div>
                    </div>
                )}

                {/* Tabs */}
                <div className="border-b border-gray-200 flex gap-8">
                    <button onClick={() => setActiveTab("catalog")}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${activeTab === "catalog" ? "border-slate-900 text-slate-900" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
                        Product Catalog ({items.length})
                    </button>
                    <button onClick={() => setActiveTab("low-stock")}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${activeTab === "low-stock" ? "border-rose-500 text-rose-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
                        {lowStock.length > 0 && <AlertTriangle className="h-3.5 w-3.5" />}
                        Low Stock {lowStock.length > 0 ? `(${lowStock.length})` : ""}
                    </button>
                    <button onClick={() => setActiveTab("sales")}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${activeTab === "sales" ? "border-emerald-600 text-emerald-700" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
                        <TrendingUp className="h-3.5 w-3.5" />
                        Sales Performance
                    </button>
                </div>

                {/* Catalog / Low-Stock Table */}
                {activeTab !== "sales" && (
                    <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-gray-50 text-gray-600 font-medium border-b">
                                    <tr>
                                        <th className="px-6 py-4">SKU</th>
                                        <th className="px-6 py-4">Name</th>
                                        <th className="px-6 py-4 text-right">Cost</th>
                                        <th className="px-6 py-4 text-right">Sale Price</th>
                                        <th className="px-6 py-4 text-center">GST</th>
                                        <th className="px-6 py-4 text-right">Stock</th>
                                        <th className="px-6 py-4 text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {isLoading ? (
                                        <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-500">Loading…</td></tr>
                                    ) : (activeTab === "catalog" ? items : lowStock).length === 0 ? (
                                        <tr>
                                            <td colSpan={7} className="px-6 py-16 text-center text-gray-500">
                                                {activeTab === "low-stock"
                                                    ? "✅ All stock levels are healthy."
                                                    : <span>No items yet. <button onClick={() => setShowModal(true)} className="text-slate-800 underline font-medium">Add your first item →</button></span>}
                                            </td>
                                        </tr>
                                    ) : (
                                        (activeTab === "catalog" ? items : lowStock).map((item) => {
                                            const totalGst = (item.cgst_rate ?? 0) + (item.sgst_rate ?? 0) + (item.igst_rate ?? 0);
                                            const isLow = item.current_qty <= item.reorder_level;
                                            const isOut = item.current_qty <= 0;
                                            return (
                                                <tr key={item.id} className="hover:bg-gray-50/50 transition-colors">
                                                    <td className="px-6 py-4 font-mono text-xs text-slate-500">{item.sku || "—"}</td>
                                                    <td className="px-6 py-4 font-medium text-gray-900">{item.name}</td>
                                                    <td className="px-6 py-4 text-right text-slate-600">{fmt(item.cost_price)}</td>
                                                    <td className="px-6 py-4 text-right font-medium">{fmt(item.sale_price)}</td>
                                                    <td className="px-6 py-4 text-center text-slate-500">{totalGst}%</td>
                                                    <td className={`px-6 py-4 text-right font-bold ${isOut ? "text-red-700" : isLow ? "text-rose-600" : "text-emerald-600"}`}>
                                                        {item.current_qty} {item.unit}
                                                        {isLow && !isOut && <AlertTriangle className="inline w-3.5 h-3.5 ml-1.5 -mt-0.5" />}
                                                        {isOut && <span className="ml-1 text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">OUT</span>}
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium border ${item.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-gray-100 text-gray-600 border-gray-200"}`}>
                                                            {item.is_active ? "Active" : "Inactive"}
                                                        </span>
                                                    </td>
                                                </tr>
                                            );
                                        })
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Sales Performance Tab */}
                {activeTab === "sales" && (
                    <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b bg-gray-50 flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-emerald-600" />
                            <span className="font-semibold text-gray-800">Sales by Product</span>
                            <span className="text-xs text-gray-400 ml-auto">Derived from invoiced sale movements</span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-white text-gray-500 text-xs uppercase tracking-wide border-b">
                                    <tr>
                                        <th className="px-6 py-3">SKU</th>
                                        <th className="px-6 py-3">Product</th>
                                        <th className="px-6 py-3 text-right">Qty Sold</th>
                                        <th className="px-6 py-3 text-right">Sale Value</th>
                                        <th className="px-6 py-3 text-right">Stock Left</th>
                                        <th className="px-6 py-3 text-right">Last Sale</th>
                                        <th className="px-6 py-3">Revenue Bar</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {isLoading ? (
                                        <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-500">Loading…</td></tr>
                                    ) : sales.length === 0 ? (
                                        <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-500">No sales data yet. Create invoices linked to inventory items to see data here.</td></tr>
                                    ) : (
                                        sales.map((s) => {
                                            const maxVal = sales[0]?.total_sale_value || 1;
                                            const barPct = Math.round((s.total_sale_value / maxVal) * 100);
                                            return (
                                                <tr key={s.item_id} className="hover:bg-gray-50/50 transition-colors">
                                                    <td className="px-6 py-4 font-mono text-xs text-slate-400">{s.sku}</td>
                                                    <td className="px-6 py-4 font-medium text-gray-900">{s.name}</td>
                                                    <td className="px-6 py-4 text-right font-bold text-gray-800 tabular-nums">
                                                        {s.total_sold_qty > 0 ? `${s.total_sold_qty} ${s.unit}` : <span className="text-gray-300">—</span>}
                                                    </td>
                                                    <td className="px-6 py-4 text-right font-bold text-emerald-700 tabular-nums">
                                                        {s.total_sale_value > 0 ? fmt(s.total_sale_value) : <span className="text-gray-300">—</span>}
                                                    </td>
                                                    <td className={`px-6 py-4 text-right tabular-nums font-medium ${s.current_stock <= 0 ? "text-red-600" : s.current_stock <= 5 ? "text-amber-600" : "text-gray-600"}`}>
                                                        {s.current_stock} {s.unit}
                                                    </td>
                                                    <td className="px-6 py-4 text-right text-gray-400 text-xs">
                                                        {s.last_sale_date ? format(new Date(s.last_sale_date), "MMM d, yyyy") : "—"}
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center gap-2">
                                                            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                                                                <div
                                                                    className="h-full bg-emerald-500 rounded-full transition-all"
                                                                    style={{ width: `${barPct}%` }}
                                                                />
                                                            </div>
                                                            <span className="text-xs text-gray-400 w-8 text-right">{barPct}%</span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            {/* ── Add Item Modal ── */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
                    onClick={() => { setShowModal(false); resetForm(); }}>
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
                        onClick={e => e.stopPropagation()}>

                        <div className="flex items-center justify-between px-6 py-4 border-b sticky top-0 bg-white z-10">
                            <h2 className="text-lg font-bold text-gray-900">Add Inventory Item</h2>
                            <button onClick={() => { setShowModal(false); resetForm(); }} className="p-1.5 hover:bg-gray-100 rounded-lg">
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-5">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Item Name *</label>
                                    <input required value={name} onChange={e => setName(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none"
                                        placeholder="e.g. Office Chair" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">SKU / Code</label>
                                    <input value={sku} onChange={e => setSku(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-slate-900 outline-none"
                                        placeholder="ITEM-001" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Unit</label>
                                    <select value={unit} onChange={e => setUnit(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none">
                                        {["pcs", "kg", "litre", "box", "set", "hour", "day", "month", "plate"].map(u => (
                                            <option key={u} value={u}>{u}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Cost Price (₹) *</label>
                                    <input required type="number" min="0" step="0.01" value={costPrice} onChange={e => setCostPrice(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none" placeholder="0.00" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Sale Price (₹) *</label>
                                    <input required type="number" min="0" step="0.01" value={salePrice} onChange={e => setSalePrice(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none" placeholder="0.00" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Opening Stock</label>
                                    <input type="number" min="0" value={openingQty} onChange={e => setOpeningQty(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Reorder Level</label>
                                    <input type="number" min="0" value={reorderLevel} onChange={e => setReorderLevel(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none" />
                                </div>
                            </div>

                            <div>
                                <p className="text-xs font-medium text-gray-600 mb-2">GST Rates</p>
                                <div className="grid grid-cols-3 gap-3">
                                    {([["CGST %", cgstRate, setCgstRate], ["SGST %", sgstRate, setSgstRate], ["IGST %", igstRate, setIgstRate]] as [string, string, (v: string) => void][]).map(([label, val, setter]) => (
                                        <div key={label}>
                                            <label className="block text-xs text-gray-500 mb-1">{label}</label>
                                            <input type="number" min="0" step="0.5" value={val} onChange={e => setter(e.target.value)}
                                                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 outline-none" />
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="flex gap-3 pt-2 border-t">
                                <button type="button" onClick={() => { setShowModal(false); resetForm(); }}
                                    className="flex-1 px-4 py-2.5 border rounded-xl text-sm font-medium hover:bg-gray-50">
                                    Cancel
                                </button>
                                <button type="submit" disabled={submitting}
                                    className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-2">
                                    {submitting ? <><div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Saving…</> : "Add Item"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
