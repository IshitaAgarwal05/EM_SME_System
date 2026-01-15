import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Users, Lock, User, Phone, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';

type InvitationInfo = {
    organization_name: string;
    role: string;
    invited_by_name: string;
    expires_at: string;
    is_valid: boolean;
};

export default function AcceptInvitePage() {
    const { token } = useParams<{ token: string }>();
    const navigate = useNavigate();
    const { login } = useAuth();

    const [inviteInfo, setInviteInfo] = useState<InvitationInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [invalidInvite, setInvalidInvite] = useState(false);

    const [formData, setFormData] = useState({
        full_name: '',
        password: '',
        confirm_password: '',
        phone: '',
    });

    useEffect(() => {
        if (token) {
            fetchInviteInfo();
        }
    }, [token]);

    const fetchInviteInfo = async () => {
        try {
            const response = await api.get(`/invitations/${token}/info`);
            setInviteInfo(response.data);
            if (!response.data.is_valid) {
                setInvalidInvite(true);
            }
        } catch (err: any) {
            console.error('Failed to fetch invitation:', err);
            setInvalidInvite(true);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (formData.password !== formData.confirm_password) {
            setError('Passwords do not match');
            return;
        }

        if (formData.password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        setSubmitting(true);

        try {
            const response = await api.post(`/invitations/${token}/accept`, {
                full_name: formData.full_name,
                password: formData.password,
                phone: formData.phone || null,
            });

            // Auto-login with the returned tokens
            const { access_token, refresh_token, user } = response.data;
            localStorage.setItem('token', access_token);
            localStorage.setItem('refresh_token', refresh_token);

            // Update auth context and redirect
            login(access_token, user);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to accept invitation');
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
            </div>
        );
    }

    if (invalidInvite) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center px-4">
                <div className="max-w-md w-full bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700 text-center">
                    <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <XCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">Invalid Invitation</h1>
                    <p className="text-gray-400 mb-6">
                        This invitation link is invalid or has expired. Please contact your team manager for a new invitation.
                    </p>
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                    >
                        Go to Login
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center px-4 py-12">
            <div className="max-w-md w-full">
                {/* Welcome Card */}
                <div className="bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700 mb-6">
                    <div className="text-center mb-6">
                        <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Users className="w-8 h-8 text-purple-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-2">You're Invited!</h1>
                        <p className="text-gray-400">
                            <strong className="text-white">{inviteInfo?.invited_by_name}</strong> invited you to join{' '}
                            <strong className="text-white">{inviteInfo?.organization_name}</strong> as a{' '}
                            <span className="text-purple-400 capitalize">{inviteInfo?.role}</span>.
                        </p>
                    </div>

                    {/* Registration Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Full Name
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="text"
                                    value={formData.full_name}
                                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    placeholder="Your full name"
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Phone (Optional)
                            </label>
                            <div className="relative">
                                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="tel"
                                    value={formData.phone}
                                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                    placeholder="+91 XXXXX XXXXX"
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="password"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    placeholder="Min. 8 characters"
                                    required
                                    minLength={8}
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Confirm Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="password"
                                    value={formData.confirm_password}
                                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                                    placeholder="Confirm your password"
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={submitting}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    <CheckCircle className="w-4 h-4" />
                                    Accept & Join Team
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer */}
                <p className="text-center text-gray-500 text-sm">
                    Already have an account?{' '}
                    <Link to="/login" className="text-purple-400 hover:text-purple-300 underline">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}
