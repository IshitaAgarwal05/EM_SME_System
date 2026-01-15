import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Loader2, Eye, EyeOff } from "lucide-react";

export default function RegisterPage() {
    const { register, handleSubmit, setError, formState: { errors } } = useForm();
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const onSubmit = async (data: any) => {
        setLoading(true);
        try {
            // 1. Register
            // API expects: email, password, full_name, organization_name
            await api.post("/auth/register", data);

            // 2. Auto login
            const res = await api.post("/auth/login", {
                email: data.email,
                password: data.password
            });
            const { access_token } = res.data;

            localStorage.setItem("token", access_token);
            const userRes = await api.get("/users/me");

            login(access_token, userRes.data);
            navigate("/dashboard");

        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail;
            const message = Array.isArray(detail)
                ? detail[0].msg
                : (detail || "Registration failed");

            setError("root", { message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
            <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-8 shadow-md">
                <div className="text-center">
                    <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Create account</h2>
                    <p className="mt-2 text-sm text-gray-600">
                        Or <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">sign in to existing account</Link>
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
                    {errors.root && (
                        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
                            {errors.root.message as string}
                        </div>
                    )}

                    <div className="space-y-4 rounded-md shadow-sm">
                        <div>
                            <label htmlFor="full_name" className="sr-only">Full Name</label>
                            <input
                                id="full_name"
                                type="text"
                                required
                                className="relative block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 pl-3"
                                placeholder="Full Name"
                                {...register("full_name", { required: true })}
                            />
                        </div>
                        <div>
                            <label htmlFor="organization_name" className="sr-only">Organization Name</label>
                            <input
                                id="organization_name"
                                type="text"
                                required
                                className="relative block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 pl-3"
                                placeholder="Organization Name"
                                {...register("organization_name", { required: true })}
                            />
                        </div>
                        <div>
                            <label htmlFor="email" className="sr-only">Email address</label>
                            <input
                                id="email"
                                type="email"
                                required
                                className="relative block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 pl-3"
                                placeholder="Email address"
                                {...register("email", { required: true })}
                            />
                        </div>
                        <div className="relative">
                            <label htmlFor="password" className="sr-only">Password</label>
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                required
                                className="relative block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 pl-3 pr-10"
                                placeholder="Password"
                                {...register("password", { required: true, minLength: 8 })}
                            />
                            <button
                                type="button"
                                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-70"
                        >
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Account
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
