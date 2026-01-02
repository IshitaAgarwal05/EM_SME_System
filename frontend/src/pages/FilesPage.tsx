import { useState, useRef, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import { Upload, FileText, Loader2, CheckCircle2, Clock, CheckCircle, AlertCircle, Calendar, Trash2 } from "lucide-react";
import { format } from "date-fns";

interface FileUpload {
    id: string;
    filename: string;
    file_type: string | null;
    file_size: number | null;
    processing_status: string;
    processed_at: string | null;
    error_message: string | null;
    rows_imported: number | null;
    created_at: string;
}

export default function FilesPage() {
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [files, setFiles] = useState<FileUpload[]>([]);
    const [loading, setLoading] = useState(true);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const fetchFiles = async () => {
        try {
            const response = await api.get("/files");
            setFiles(response.data);
        } catch (err) {
            console.error("Failed to fetch files:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        setUploading(true);
        setSuccess(false);
        try {
            await api.post("/files/import", formData);
            setSuccess(true);
            fetchFiles();
        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.detail || "Upload failed";
            alert(`Upload failed: ${msg}`);
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const handleDelete = async (fileId: string, filename: string) => {
        if (!confirm(`Are you sure you want to delete "${filename}"? This will also remove all transactions imported from this file.`)) {
            return;
        }

        setDeletingId(fileId);
        try {
            await api.delete(`/files/${fileId}`);
            setFiles(prev => prev.filter(f => f.id !== fileId));
        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.detail || "Delete failed";
            alert(`Delete failed: ${msg}`);
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight">Files & Documents</h2>
                        <p className="text-muted-foreground">Upload and manage bank statements and business documents.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                    {/* Upload Section */}
                    <div className="lg:col-span-1">
                        <div className="rounded-xl border bg-white p-6 shadow-sm">
                            <h3 className="text-lg font-semibold mb-4">Bulk Import</h3>
                            <div
                                className="rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-8 text-center hover:bg-gray-100 transition-colors cursor-pointer"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 mb-4">
                                    {uploading ? (
                                        <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
                                    ) : (
                                        <Upload className="h-6 w-6 text-blue-600" />
                                    )}
                                </div>
                                <h4 className="text-sm font-medium text-gray-900">
                                    {uploading ? "Uploading..." : "Click to upload"}
                                </h4>
                                <p className="mt-1 text-xs text-gray-500">Excel or CSV bank statements</p>
                                <input
                                    type="file"
                                    className="hidden"
                                    ref={fileInputRef}
                                    onChange={handleUpload}
                                    accept=".xlsx,.xls,.csv"
                                />
                            </div>

                            {success && (
                                <div className="mt-4 p-3 rounded-lg bg-green-50 flex items-start gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-medium text-green-800">Import successful!</p>
                                        <p className="text-xs text-green-700">Transactions processed and saved.</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Files List Section */}
                    <div className="lg:col-span-2">
                        <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                            <div className="px-6 py-4 border-b flex items-center justify-between bg-gray-50/50">
                                <h3 className="font-semibold text-gray-900">Recent Uploads</h3>
                                <button
                                    onClick={() => fetchFiles()}
                                    className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                                >
                                    Refresh
                                </button>
                            </div>

                            <div className="divide-y divide-gray-100">
                                {loading ? (
                                    <div className="p-12 text-center text-gray-500">
                                        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-400" />
                                        <p className="text-sm">Loading history...</p>
                                    </div>
                                ) : files.length === 0 ? (
                                    <div className="p-12 text-center text-gray-500">
                                        <FileText className="h-12 w-12 mx-auto mb-4 text-gray-200" />
                                        <p className="text-sm font-medium">No files uploaded yet</p>
                                        <p className="text-xs mt-1 text-gray-400">Your history will appear here once you upload.</p>
                                    </div>
                                ) : (
                                    files.map((file) => (
                                        <div key={file.id} className="p-4 hover:bg-gray-50 transition-colors">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-gray-100 rounded-lg">
                                                        <FileText className="h-5 w-5 text-gray-500" />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900 truncate max-w-[200px] md:max-w-md">
                                                            {file.filename}
                                                        </p>
                                                        <div className="flex items-center gap-3 mt-1">
                                                            <div className="flex items-center gap-1 text-[10px] text-gray-400">
                                                                <Calendar className="h-3 w-3" />
                                                                {format(new Date(file.created_at), "MMM d, h:mm a")}
                                                            </div>
                                                            {file.rows_imported !== null && (
                                                                <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-full font-medium">
                                                                    {file.rows_imported} txns
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end gap-1">
                                                    <div className="flex items-center gap-2">
                                                        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border">
                                                            {file.processing_status === "completed" ? (
                                                                <>
                                                                    <CheckCircle className="h-3 w-3 text-green-500" />
                                                                    <span className="text-green-700">Success</span>
                                                                </>
                                                            ) : file.processing_status === "failed" ? (
                                                                <>
                                                                    <AlertCircle className="h-3 w-3 text-red-500" />
                                                                    <span className="text-red-700">Failed</span>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <Clock className="h-3 w-3 text-blue-500 animate-pulse" />
                                                                    <span className="text-blue-700">Processing</span>
                                                                </>
                                                            )}
                                                        </div>
                                                        <button
                                                            onClick={() => handleDelete(file.id, file.filename)}
                                                            disabled={deletingId === file.id}
                                                            className="p-1 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                                                            title="Delete file and associated transactions"
                                                        >
                                                            {deletingId === file.id ? (
                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                            ) : (
                                                                <Trash2 className="h-4 w-4" />
                                                            )}
                                                        </button>
                                                    </div>
                                                    {file.error_message && (
                                                        <p className="text-[10px] text-red-500 max-w-[150px] truncate">
                                                            {file.error_message}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
