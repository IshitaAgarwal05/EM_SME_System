import { useState, useEffect } from "react";
import api from "../lib/api";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { format } from "date-fns";
import { Plus, Download, FileText, CheckCircle2, AlertCircle, Clock, X, Trash2 } from "lucide-react";

type LineItem = {
    description: string;
    quantity: number;
    unit_price: number;
    cgst_rate: number;
    sgst_rate: number;
    igst_rate: number;
    item_id?: string;
};

const emptyLine = (): LineItem => ({
    description: "",
    quantity: 1,
    unit_price: 0,
    cgst_rate: 9,
    sgst_rate: 9,
    igst_rate: 0,
    item_id: undefined,
});

export default function InvoicesPage() {
    const [invoices, setInvoices] = useState<any[]>([]);
    const [inventoryItems, setInventoryItems] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Form state
    const [clientName, setClientName] = useState("");
    const [clientEmail, setClientEmail] = useState("");
    const [clientGstin, setClientGstin] = useState("");
    const [issueDate, setIssueDate] = useState(format(new Date(), "yyyy-MM-dd"));
    const [dueDate, setDueDate] = useState("");
    const [notes, setNotes] = useState("");
    const [lineItems, setLineItems] = useState<LineItem[]>([emptyLine()]);

    const fetchInvoices = async () => {
        try {
            const response = await api.get("/invoices");
            setInvoices(response.data.items || response.data || []);
        } catch (error) {
            console.error("Failed to fetch invoices:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchInvoices();
        api.get("/inventory/items").then(r => setInventoryItems(r.data || [])).catch(() => { });
    }, []);

    const selectInventoryItem = (idx: number, itemId: string) => {
        const inv = inventoryItems.find((i: any) => i.id === itemId);
        if (!inv) return;
        setLineItems(lines => lines.map((l, i) => i === idx ? {
            ...l,
            item_id: inv.id,
            description: inv.name,
            unit_price: inv.sale_price,
            cgst_rate: inv.cgst_rate,
            sgst_rate: inv.sgst_rate,
            igst_rate: inv.igst_rate,
        } : l));
    };

    const updateLine = (idx: number, field: keyof LineItem, value: string | number) => {
        setLineItems(lines =>
            lines.map((l, i) => i === idx ? { ...l, [field]: typeof value === "string" ? value : Number(value) } : l)
        );
    };

    const removeLine = (idx: number) => setLineItems(lines => lines.filter((_, i) => i !== idx));

    const lineTotal = (l: LineItem) => {
        const subtotal = l.quantity * l.unit_price;
        return subtotal + subtotal * (l.cgst_rate + l.sgst_rate + l.igst_rate) / 100;
    };

    const grandTotal = lineItems.reduce((s, l) => s + lineTotal(l), 0);

    const resetForm = () => {
        setClientName(""); setClientEmail(""); setClientGstin("");
        setIssueDate(format(new Date(), "yyyy-MM-dd")); setDueDate(""); setNotes("");
        setLineItems([emptyLine()]);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!clientName.trim() || lineItems.some(l => !l.description.trim())) {
            alert("Fill in client name and all line item descriptions.");
            return;
        }
        setSubmitting(true);
        try {
            await api.post("/invoices", {
                client_name: clientName.trim(),
                client_email: clientEmail.trim() || null,
                client_gstin: clientGstin.trim() || null,
                issue_date: issueDate,
                due_date: dueDate || null,
                notes: notes.trim() || null,
                line_items: lineItems,
            });
            setShowModal(false);
            resetForm();
            await fetchInvoices();
        } catch (err: any) {
            alert(err.response?.data?.detail || "Failed to create invoice.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDownloadPdf = async (invoiceId: string, invoiceNumber: string) => {
        try {
            const response = await api.get(`/invoices/${invoiceId}/pdf`, { responseType: "blob" });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", `invoice-${invoiceNumber}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
        } catch {
            alert("PDF failed. Install: pip install reportlab");
        }
    };

    const getStatusConfig = (status: string) => {
        switch (status) {
            case "paid": return { color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2, label: "Paid" };
            case "partial": return { color: "bg-amber-100 text-amber-700", icon: Clock, label: "Partial" };
            case "sent": return { color: "bg-blue-100 text-blue-700", icon: FileText, label: "Sent" };
            case "void": return { color: "bg-gray-100 text-gray-700", icon: AlertCircle, label: "Voided" };
            default: return { color: "bg-slate-100 text-slate-700", icon: FileText, label: "Draft" };
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
                        <p className="text-sm text-gray-500 mt-1">Create GST invoices, track payments, generate PDFs.</p>
                    </div>
                    <button
                        onClick={() => setShowModal(true)}
                        className="flex items-center gap-2 rounded-lg bg-[#cc0000] px-4 py-2 text-sm font-medium text-white hover:bg-[#aa0000] transition-colors shadow-sm"
                    >
                        <Plus className="h-4 w-4" /> Create Invoice
                    </button>
                </div>

                <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-gray-50 text-gray-600 font-medium border-b">
                                <tr>
                                    <th className="px-6 py-4">Invoice No.</th>
                                    <th className="px-6 py-4">Client</th>
                                    <th className="px-6 py-4">Issue Date</th>
                                    <th className="px-6 py-4">Due Date</th>
                                    <th className="px-6 py-4 text-right">Amount</th>
                                    <th className="px-6 py-4 text-right">Balance</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {isLoading ? (
                                    <tr><td colSpan={8} className="px-6 py-12 text-center text-gray-500">Loading…</td></tr>
                                ) : invoices.length === 0 ? (
                                    <tr>
                                        <td colSpan={8} className="px-6 py-16 text-center">
                                            <div className="flex flex-col items-center gap-3 text-gray-400">
                                                <FileText className="w-10 h-10" />
                                                <p className="font-medium">No invoices yet</p>
                                                <button onClick={() => setShowModal(true)} className="text-sm text-[#cc0000] hover:underline">
                                                    Create your first invoice →
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    invoices.map((inv) => {
                                        const status = getStatusConfig(inv.status);
                                        const StatusIcon = status.icon;
                                        const outstanding = (inv.total_amount ?? 0) - (inv.paid_amount ?? 0);
                                        return (
                                            <tr key={inv.id} className="hover:bg-gray-50/50 transition-colors">
                                                <td className="px-6 py-4 font-medium">{inv.invoice_number}</td>
                                                <td className="px-6 py-4 text-gray-700">
                                                    {inv.client_name}
                                                    {inv.client_email && <div className="text-xs text-gray-400">{inv.client_email}</div>}
                                                </td>
                                                <td className="px-6 py-4 text-gray-600">{format(new Date(inv.issue_date), "MMM d, yyyy")}</td>
                                                <td className="px-6 py-4 text-gray-600">{inv.due_date ? format(new Date(inv.due_date), "MMM d, yyyy") : "—"}</td>
                                                <td className="px-6 py-4 text-right font-medium">₹{(inv.total_amount ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                                                <td className="px-6 py-4 text-right text-gray-600">₹{outstanding.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.color}`}>
                                                        <StatusIcon className="h-3.5 w-3.5" />{status.label}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button onClick={() => handleDownloadPdf(inv.id, inv.invoice_number)}
                                                        className="p-2 text-gray-400 hover:text-[#cc0000] hover:bg-red-50 rounded-lg transition-colors">
                                                        <Download className="h-4 w-4" />
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* ── Create Invoice Modal ── */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
                    onClick={() => { setShowModal(false); resetForm(); }}>
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
                        onClick={e => e.stopPropagation()}>

                        <div className="flex items-center justify-between px-6 py-4 border-b sticky top-0 bg-white z-10">
                            <h2 className="text-lg font-bold text-gray-900">New Invoice</h2>
                            <button onClick={() => { setShowModal(false); resetForm(); }}
                                className="p-1.5 hover:bg-gray-100 rounded-lg">
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-6">
                            {/* Client */}
                            <div>
                                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Client Details</p>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                    <div className="sm:col-span-1">
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Client Name *</label>
                                        <input required value={clientName} onChange={e => setClientName(e.target.value)}
                                            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#cc0000] outline-none"
                                            placeholder="Acme Corp" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                                        <input type="email" value={clientEmail} onChange={e => setClientEmail(e.target.value)}
                                            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#cc0000] outline-none"
                                            placeholder="client@email.com" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">GSTIN</label>
                                        <input value={clientGstin} onChange={e => setClientGstin(e.target.value)}
                                            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#cc0000] outline-none font-mono"
                                            placeholder="29AAAAA0000A1Z5" />
                                    </div>
                                </div>
                            </div>

                            {/* Dates */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Issue Date *</label>
                                    <input required type="date" value={issueDate} onChange={e => setIssueDate(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#cc0000] outline-none" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Due Date</label>
                                    <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#cc0000] outline-none" />
                                </div>
                            </div>

                            {/* Line Items */}
                            <div>
                                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Line Items</p>
                                <div className="space-y-3">
                                    {lineItems.map((line, idx) => (
                                        <div key={idx} className="rounded-lg border bg-gray-50 p-4 space-y-3">
                                            {/* Product picker */}
                                            <div className="flex items-start gap-3">
                                                <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">
                                                            Pick from Inventory
                                                        </label>
                                                        <select
                                                            value={line.item_id || ""}
                                                            onChange={e => e.target.value ? selectInventoryItem(idx, e.target.value) : updateLine(idx, "item_id" as keyof LineItem, "")}
                                                            className="w-full border rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-[#cc0000] outline-none"
                                                        >
                                                            <option value="">— Custom / Manual —</option>
                                                            {inventoryItems.map((inv: any) => (
                                                                <option key={inv.id} value={inv.id}>
                                                                    [{inv.sku}] {inv.name} — ₹{inv.sale_price}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">Description *</label>
                                                        <input required value={line.description} onChange={e => updateLine(idx, "description", e.target.value)}
                                                            className="w-full border rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-[#cc0000] outline-none"
                                                            placeholder="Service / Product" />
                                                    </div>
                                                </div>
                                                {lineItems.length > 1 && (
                                                    <button type="button" onClick={() => removeLine(idx)}
                                                        className="mt-5 p-2 text-red-400 hover:bg-red-50 rounded-lg">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </div>
                                            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                                                {([
                                                    ["Qty", "quantity", "0.01"],
                                                    ["Unit Price (₹)", "unit_price", "0.01"],
                                                    ["CGST %", "cgst_rate", "0.5"],
                                                    ["SGST %", "sgst_rate", "0.5"],
                                                    ["IGST %", "igst_rate", "0.5"],
                                                ] as [string, keyof LineItem, string][]).map(([label, field, step]) => (
                                                    <div key={field}>
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
                                                        <input type="number" min="0" step={step}
                                                            value={line[field] as number}
                                                            onChange={e => updateLine(idx, field, e.target.value)}
                                                            className="w-full border rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-[#cc0000] outline-none" />
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="text-right text-sm font-semibold text-gray-700">
                                                Line Total: ₹{lineTotal(line).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <button type="button" onClick={() => setLineItems(l => [...l, emptyLine()])}
                                    className="mt-3 flex items-center gap-2 text-sm text-[#cc0000] hover:underline font-medium">
                                    <Plus className="w-4 h-4" /> Add Line Item
                                </button>
                            </div>

                            {/* Notes */}
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">Notes / Terms</label>
                                <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2}
                                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#cc0000] outline-none resize-none"
                                    placeholder="Payment terms, bank details…" />
                            </div>

                            {/* Footer */}
                            <div className="flex items-center justify-between pt-4 border-t">
                                <div>
                                    <div className="text-xs text-gray-500">Grand Total (incl. GST)</div>
                                    <div className="text-2xl font-bold text-gray-900">
                                        ₹{grandTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                                    </div>
                                </div>
                                <div className="flex gap-3">
                                    <button type="button" onClick={() => { setShowModal(false); resetForm(); }}
                                        className="px-5 py-2.5 border rounded-xl text-sm font-medium hover:bg-gray-50">
                                        Cancel
                                    </button>
                                    <button type="submit" disabled={submitting}
                                        className="px-5 py-2.5 bg-[#cc0000] text-white rounded-xl text-sm font-medium hover:bg-[#aa0000] disabled:opacity-50 flex items-center gap-2">
                                        {submitting
                                            ? <><div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Saving…</>
                                            : "Create Invoice"}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
