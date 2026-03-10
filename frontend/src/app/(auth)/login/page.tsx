"use client";

import Image from "next/image";
import Link from "next/link";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthService } from "@/services/auth";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await AuthService.login(email, password);
      if (data?.access_token) {
        localStorage.setItem("token", data.access_token);

        // Fetch user profile to get role
        try {
          const userProfile = await AuthService.getMe(data.access_token);
          if (userProfile?.role === "ADMIN") {
            router.push("/dashboard/admin");
          } else {
            router.push("/dashboard/user"); // Standard user dashboard
          }
        } catch (e) {
          // Fallback if profile fetch fails
          router.push("/dashboard/user");
        }
      } else {
        router.push("/");
      }
    } catch (err: any) {
      setError(err.message || "Failed to login. Please check your credentials.");
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
              width={100}
              height={100}
              className="object-contain"
            />
          </div>

          <div className="mb-8 text-center lg:text-left">
            <h1 className="text-2xl font-bold text-primary mb-1">Welcome to login system</h1>
            <p className="text-sm text-gray-500">Sign in by entering the information below</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 text-red-500 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Email Field */}
            <div className="relative group">
              <label className="sr-only">Email</label>
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
                placeholder="********"
                className="block w-full pl-12 pr-12 py-3 bg-[#F4F6F8] border-none rounded-xl focus:ring-2 focus:ring-accent outline-none transition-all placeholder:text-gray-400"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-accent transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 bg-accent hover:opacity-90 text-white font-bold rounded-xl transition-all shadow-lg shadow-accent/20 active:scale-95 disabled:opacity-50"
              >
                {loading ? "Logging in..." : "Login"}
              </button>
              <Link
                href="/register"
                className="flex-1 py-3 border border-gray-200 hover:border-accent hover:text-accent text-center font-bold rounded-xl transition-all active:scale-95 flex items-center justify-center"
              >
                Sign up
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
