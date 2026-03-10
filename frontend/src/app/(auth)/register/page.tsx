"use client";

import Image from "next/image";
import Link from "next/link";
import { User, Lock, Mail, Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthService } from "@/services/auth";

export default function RegisterPage() {
    const [showPassword, setShowPassword] = useState(false);
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const validateForm = () => {
        if (password.length < 8) return "Password must be at least 8 characters long.";
        if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter.";
        if (!/[a-z]/.test(password)) return "Password must contain at least one lowercase letter.";
        if (!/[0-9]/.test(password)) return "Password must contain at least one digit.";
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) return "Password must contain at least one special character.";
        return null;
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        const validationError = validateForm();
        if (validationError) {
            setError(validationError);
            return;
        }

        setLoading(true);

        try {
            await AuthService.register(fullName, email, password);
            router.push("/login"); // Redirect to login upon successful registration
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : "Failed to create account. Please try again.";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="flex lg:flex-row-reverse min-h-screen bg-background text-foreground overflow-hidden">
            {/* Right Section - Form */}
            <div className="flex-[0.8] lg:flex-[1] flex flex-col justify-center items-center p-6 sm:p-8 lg:p-12 bg-white z-30 shadow-[-20px_0_40px_-20px_rgba(0,0,0,0.1)]">
                <div className="w-full max-w-md">
                    {/* Logo */}
                    <div className="flex items-center justify-center mb-6">
                        <Image
                            src="/images/logo.png"
                            alt="DataPulse Logo"
                            width={60}
                            height={60}
                            className="object-contain"
                        />
                    </div>

                    <div className="mb-6 text-center lg:text-left">
                        <h1 className="text-2xl font-bold text-primary mb-1">Create an account</h1>
                        <p className="text-sm text-gray-500">Sign up to get started with DataPulse</p>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 rounded-xl bg-red-50 text-red-500 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleRegister} className="space-y-4">
                        {/* Full Name Field */}
                        <div className="relative group">
                            <label className="sr-only">Full Name</label>
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
                                <User size={20} />
                            </div>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                required
                                placeholder="Full Name"
                                className="block w-full pl-12 pr-4 py-3 bg-[#F4F6F8] border-none rounded-xl focus:ring-2 focus:ring-accent outline-none transition-all placeholder:text-gray-400"
                            />
                        </div>

                        {/* Email Field */}
                        <div className="relative group">
                            <label className="sr-only">Email Address</label>
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
                                <Mail size={20} />
                            </div>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                placeholder="Email Address"
                                className="block w-full pl-12 pr-4 py-3 bg-[#F4F6F8] border-none rounded-xl focus:ring-2 focus:ring-accent outline-none transition-all placeholder:text-gray-400"
                            />
                        </div>

                        {/* Password Field */}
                        <div className="relative group">
                            <label className="sr-only">Password</label>
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
                                <Lock size={20} />
                            </div>
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                placeholder="Password"
                                className="block w-full pl-12 pr-12 py-3 bg-[#F4F6F8] border-none rounded-xl focus:ring-2 focus:ring-accent outline-none transition-all placeholder:text-gray-400"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-accent transition-colors"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-3 pt-2">
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex-1 py-3 bg-accent hover:opacity-90 text-white font-bold rounded-xl transition-all shadow-lg shadow-accent/20 active:scale-95 disabled:opacity-50"
                            >
                                {loading ? "Creating..." : "Create Account"}
                            </button>
                            <Link
                                href="/login"
                                className="flex-1 py-3 border border-gray-200 hover:border-accent hover:text-accent text-center font-bold rounded-xl transition-all active:scale-95 flex items-center justify-center"
                            >
                                Back to Login
                            </Link>
                        </div>
                    </form>
                </div>
            </div>

            {/* Left Section - Decorative Graphic */}
            <div className="hidden lg:flex flex-1 relative bg-white overflow-hidden justify-start items-end pt-12 pr-12">
                {/* Geometric layered shapes matching the reference design */}
                <div className="absolute top-[5%] left-0 bottom-0 w-[94%] bg-[#F4F6F8] rounded-tr-[130px] z-0"></div>
                <div className="absolute top-[12%] left-0 bottom-0 w-[88%] bg-[#E2E8F0] rounded-tr-[130px] z-10"></div>

                {/* Main Primary Layer */}
                <div className="absolute top-[19%] left-0 bottom-0 w-[82%] bg-primary rounded-tr-[130px] flex flex-col items-center justify-center p-12 shadow-2xl overflow-hidden z-20">

                    {/* Subtle interior glow/gradients */}
                    <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] bg-accent rounded-full blur-[120px] opacity-20 transform rotate-45"></div>
                    <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-[#0ea5e9] rounded-full blur-[100px] opacity-10"></div>

                    <div className="relative z-30 w-full max-w-2xl transform hover:scale-105 transition-transform duration-700">
                        <Image
                            src="/images/datapulse-graphic.png"
                            alt="DataPulse Analytics Visualization"
                            width={1200}
                            height={800}
                            className="w-full h-auto drop-shadow-2xl object-contain"
                            priority
                        />
                    </div>
                </div>
            </div>
        </main>
    );
}
