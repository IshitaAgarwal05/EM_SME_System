import { useAuth } from "../context/AuthContext";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { User, Mail, Building, Shield } from "lucide-react";

export default function ProfilePage() {
    const { user } = useAuth();

    if (!user) return null;

    return (
        <DashboardLayout>
            <div className="max-w-2xl mx-auto space-y-6">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Profile Settings</h2>
                    <p className="text-muted-foreground">Manage your account information.</p>
                </div>

                <div className="bg-white shadow rounded-lg overflow-hidden border">
                    <div className="px-4 py-5 sm:px-6 bg-gray-50 border-b">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">User Information</h3>
                    </div>
                    <div className="px-4 py-5 sm:p-6 space-y-6">

                        <div className="flex items-center gap-4">
                            <div className="h-20 w-20 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-3xl font-bold">
                                {user.full_name?.charAt(0)}
                            </div>
                            <div>
                                <h4 className="text-xl font-bold text-gray-900">{user.full_name}</h4>
                                <p className="text-gray-500">{user.email}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                            <div className="col-span-2 sm:col-span-1">
                                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                                <div className="mt-1 flex rounded-md shadow-sm">
                                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
                                        <User className="h-4 w-4" />
                                    </span>
                                    <input
                                        type="text"
                                        disabled
                                        className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 bg-gray-100 sm:text-sm"
                                        value={user.full_name}
                                    />
                                </div>
                            </div>

                            <div className="col-span-2 sm:col-span-1">
                                <label className="block text-sm font-medium text-gray-700">Email Address</label>
                                <div className="mt-1 flex rounded-md shadow-sm">
                                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
                                        <Mail className="h-4 w-4" />
                                    </span>
                                    <input
                                        type="text"
                                        disabled
                                        className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 bg-gray-100 sm:text-sm"
                                        value={user.email}
                                    />
                                </div>
                            </div>

                            <div className="col-span-2 sm:col-span-1">
                                <label className="block text-sm font-medium text-gray-700">Organization ID</label>
                                <div className="mt-1 flex rounded-md shadow-sm">
                                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
                                        <Building className="h-4 w-4" />
                                    </span>
                                    <input
                                        type="text"
                                        disabled
                                        className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 bg-gray-100 sm:text-sm"
                                        value={user.organization_id}
                                    />
                                </div>
                            </div>

                            <div className="col-span-2 sm:col-span-1">
                                <label className="block text-sm font-medium text-gray-700">Role</label>
                                <div className="mt-1 flex rounded-md shadow-sm">
                                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">
                                        <Shield className="h-4 w-4" />
                                    </span>
                                    <input
                                        type="text"
                                        disabled
                                        className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 bg-gray-100 sm:text-sm capitalize"
                                        value={user.role}
                                    />
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
