import { useState, useEffect } from 'react';
import { X, Mail, UserPlus, Loader2, Copy, Check, Trash2, Clock, Users } from 'lucide-react';
import api from '../lib/api';

type Invitation = {
    id: string;
    email: string;
    role: string;
    status: string;
    expires_at: string;
    created_at: string;
};

interface InviteTeamModalProps {
    isOpen: boolean;
    onClose: () => void;
    onInviteSent?: () => void;
}

export default function InviteTeamModal({ isOpen, onClose, onInviteSent }: InviteTeamModalProps) {
    const [email, setEmail] = useState('');
    const [role, setRole] = useState('employee');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [invitations, setInvitations] = useState<Invitation[]>([]);
    const [loadingInvitations, setLoadingInvitations] = useState(false);
    const [copiedToken, setCopiedToken] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            fetchPendingInvitations();
        }
    }, [isOpen]);

    const fetchPendingInvitations = async () => {
        setLoadingInvitations(true);
        try {
            const response = await api.get('/invitations');
            setInvitations(response.data || []);
        } catch (e) {
            console.error('Failed to fetch invitations:', e);
        } finally {
            setLoadingInvitations(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            await api.post('/invitations', { email, role });
            setSuccess(`Invitation sent to ${email}!`);
            setEmail('');
            fetchPendingInvitations();
            onInviteSent?.();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to send invitation');
        } finally {
            setLoading(false);
        }
    };

    const handleRevoke = async (invitationId: string) => {
        try {
            await api.delete(`/invitations/${invitationId}`);
            setInvitations(prev => prev.filter(inv => inv.id !== invitationId));
        } catch (err) {
            console.error('Failed to revoke invitation:', err);
        }
    };

    const copyInviteLink = async (token: string) => {
        const link = `${window.location.origin}/accept-invite/${token}`;
        await navigator.clipboard.writeText(link);
        setCopiedToken(token);
        setTimeout(() => setCopiedToken(null), 2000);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        });
    };

    const isExpired = (expiresAt: string) => {
        return new Date(expiresAt) < new Date();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
                <div className="fixed inset-0 bg-black/60 transition-opacity" onClick={onClose} />

                <div className="relative inline-block w-full max-w-lg p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-gray-900 shadow-xl rounded-2xl border border-gray-700">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-500/20 rounded-lg">
                                <UserPlus className="w-5 h-5 text-purple-400" />
                            </div>
                            <h3 className="text-lg font-semibold text-white">Invite Team Member</h3>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-white transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Invite Form */}
                    <form onSubmit={handleSubmit} className="space-y-4 mb-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Email Address
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="colleague@company.com"
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Role
                            </label>
                            <select
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            >
                                <option value="employee">Employee</option>
                                <option value="manager">Manager</option>
                                <option value="contractor">Contractor</option>
                            </select>
                        </div>

                        {error && (
                            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {success && (
                            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
                                {success}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || !email}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Sending...
                                </>
                            ) : (
                                <>
                                    <Mail className="w-4 h-4" />
                                    Send Invitation
                                </>
                            )}
                        </button>
                    </form>

                    {/* Pending Invitations */}
                    <div className="border-t border-gray-700 pt-4">
                        <div className="flex items-center gap-2 mb-3">
                            <Users className="w-4 h-4 text-gray-400" />
                            <h4 className="text-sm font-medium text-gray-300">Pending Invitations</h4>
                        </div>

                        {loadingInvitations ? (
                            <div className="flex justify-center py-4">
                                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                            </div>
                        ) : invitations.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-4">
                                No pending invitations
                            </p>
                        ) : (
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                {invitations.map((inv) => (
                                    <div
                                        key={inv.id}
                                        className={`flex items-center justify-between p-3 rounded-lg ${isExpired(inv.expires_at)
                                                ? 'bg-red-500/10 border border-red-500/20'
                                                : 'bg-gray-800/50 border border-gray-700'
                                            }`}
                                    >
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-white truncate">{inv.email}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-xs text-gray-400 capitalize">{inv.role}</span>
                                                <span className="text-xs text-gray-600">•</span>
                                                <span className={`text-xs ${isExpired(inv.expires_at) ? 'text-red-400' : 'text-gray-400'}`}>
                                                    <Clock className="w-3 h-3 inline mr-1" />
                                                    {isExpired(inv.expires_at) ? 'Expired' : `Expires ${formatDate(inv.expires_at)}`}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-1 ml-2">
                                            <button
                                                onClick={() => copyInviteLink((inv as any).token)}
                                                className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
                                                title="Copy invite link"
                                            >
                                                {copiedToken === (inv as any).token ? (
                                                    <Check className="w-4 h-4 text-green-400" />
                                                ) : (
                                                    <Copy className="w-4 h-4" />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => handleRevoke(inv.id)}
                                                className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded transition-colors"
                                                title="Revoke invitation"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
