"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { useEffect, useState } from "react";
import { AuthService } from "@/services/auth";
import {
  LayoutDashboard,
  Database,
  UploadCloud,
  ClipboardCheck,
  FileText,
  TrendingUp,
  Settings,
  LogOut,
  Menu,
  X,
} from "lucide-react";

export default function UserDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navigation = [
    { name: "Overview", href: "/dashboard/user", icon: LayoutDashboard },
    { name: "My Datasets", href: "/dashboard/user/datasets", icon: Database },
    { name: "Upload File", href: "/dashboard/user/upload", icon: UploadCloud },
    {
      name: "Validation Rules",
      href: "/dashboard/user/rules",
      icon: ClipboardCheck,
    },
    {
      name: "Quality Reports",
      href: "/dashboard/user/reports",
      icon: FileText,
    },
    { name: "Trends", href: "/dashboard/user/trends", icon: TrendingUp },
    { name: "Settings", href: "/dashboard/user/settings", icon: Settings },
  ];

  const [user, setUser] = useState<{ full_name: string; email: string } | null>(
    null
  );

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const userData = await AuthService.getMe(token);
          setUser(userData);
        } catch (err) {
          console.error("Failed to fetch user profile:", err);
        }
      }
    };
    fetchUser();
  }, []);

  const getPageTitle = () => {
    const currentNavItem =
      navigation.find((item) => item.href === pathname) || navigation[0];
    return currentNavItem.name;
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-primary text-white shadow-xl transition-all duration-300 z-50">
        <div className="flex items-center gap-3 p-6 border-b border-white/10">
          <Image
            src="/images/logo.png"
            alt="DataPulse Logo"
            width={32}
            height={32}
            className="flex-shrink-0"
          />
          <span className="text-xl font-bold tracking-wide">DataPulse</span>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? "bg-accent text-white font-medium"
                    : "text-gray-300 hover:bg-white/10 hover:text-white"
                }`}
              >
                <Icon
                  size={20}
                  className={isActive ? "text-white" : "text-gray-400"}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <Link
            href="/login"
            className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors w-full"
          >
            <LogOut size={20} />
            Logout
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white shadow-sm flex items-center justify-between px-4 sm:px-6 lg:px-8 z-40">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="lg:hidden p-2 text-gray-500 hover:bg-gray-100 rounded-md transition-colors"
            >
              <Menu size={24} />
            </button>
            <h1 className="text-xl font-semibold text-primary">
              {getPageTitle()}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-3 mr-4">
              <div className="text-right">
                <p className="text-sm font-medium text-primary leading-tight">
                  {user?.full_name || "User"}
                </p>
                <p className="text-xs text-gray-500">
                  {user?.email || "loading..."}
                </p>
              </div>
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold overflow-hidden border-2 border-accent">
                {user?.full_name?.charAt(0) || "U"}
              </div>
            </div>
          </div>
        </header>

        {/* Mobile Sidebar Overlay */}
        {isMobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-primary/80 backdrop-blur-sm"
              onClick={() => setIsMobileMenuOpen(false)}
            />

            {/* Sidebar content */}
            <aside className="relative flex flex-col w-64 max-w-[80%] h-full bg-primary text-white shadow-2xl animate-in slide-in-from-left">
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <Image
                    src="/images/logo.png"
                    alt="Logo"
                    width={28}
                    height={28}
                  />
                  <span className="font-bold text-lg">DataPulse</span>
                </div>
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <X size={24} />
                </button>
              </div>

              <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
                {navigation.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setIsMobileMenuOpen(false)} // Close on click
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                        isActive
                          ? "bg-accent text-white font-medium"
                          : "text-gray-300 hover:bg-white/10 hover:text-white"
                      }`}
                    >
                      <Icon
                        size={20}
                        className={isActive ? "text-white" : "text-gray-400"}
                      />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>

              <div className="p-4 border-t border-white/10">
                <Link
                  href="/login"
                  className="flex items-center gap-3 px-4 py-3 text-red-300 hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors w-full"
                >
                  <LogOut size={20} />
                  Logout
                </Link>
              </div>
            </aside>
          </div>
        )}

        {/* Child Pages Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-background scroll-smooth">
          <div className="max-w-7xl mx-auto h-full">{children}</div>
        </main>
      </div>
    </div>
  );
}
