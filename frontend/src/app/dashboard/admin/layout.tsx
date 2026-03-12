"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { useEffect, useState } from "react";
import { AuthService } from "@/services/auth";
import { getUsers } from "@/services/user";
import {
  LayoutDashboard,
  Database,
  UploadCloud,
  Users,
  ClipboardCheck,
  FileText,
  TrendingUp,
  Settings,
  LogOut,
  Menu,
  X,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export default function AdminDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [hasUsers, setHasUsers] = useState(true); // Default to true to avoid flicker

  const navigation = [
    { name: "Dashboard", href: "/dashboard/admin", icon: LayoutDashboard },
    { name: "All Datasets", href: "/dashboard/admin/datasets", icon: Database },
    { name: "Upload File", href: "/dashboard/admin/upload", icon: UploadCloud },
    { name: "Users", href: "/dashboard/admin/users", icon: Users },
    {
      name: "Validation Rules",
      href: "/dashboard/admin/rules",
      icon: ClipboardCheck,
    },
    {
      name: "Quality Reports",
      href: "/dashboard/admin/reports",
      icon: FileText,
    },
    { name: "Trends", href: "/dashboard/admin/trends", icon: TrendingUp },
    {
      name: "System Settings",
      href: "/dashboard/admin/settings",
      icon: Settings,
    },
  ].filter((item) => item.name !== "Users" || hasUsers);

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

          // Also check for users to toggle navigation
          const users = await getUsers();
          setHasUsers(users.length > 0);
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
      <aside
        className={`hidden lg:flex flex-col bg-[#08293c] text-white shadow-xl transition-all duration-300 z-50 overflow-hidden h-full ${
          isCollapsed ? "w-20" : "w-64"
        }`}
      >
        <div
          className={`flex ${isCollapsed ? "flex-col justify-center py-2 gap-1.5" : "flex-row justify-between px-5"} items-center border-b border-white/5 h-20 min-h-[5rem]`}
        >
          <Link href="/" className="flex items-center justify-center">
            <img
              src="/images/logo.png"
              alt="DataPulse Logo"
              className={`${isCollapsed ? "h-6" : "h-7"} w-auto object-contain flex-shrink-0 transition-all`}
            />
          </Link>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors"
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight size={16} />
            ) : (
              <ChevronLeft size={18} />
            )}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1.5 sidebar-scrollbar scroll-smooth">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-3 rounded-xl transition-all relative group ${
                  isActive
                    ? "bg-[#ff5a00] text-white shadow-lg shadow-[#ff5a00]/20"
                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                <Icon
                  size={20}
                  className={`flex-shrink-0 transition-colors ${isActive ? "text-white" : "group-hover:text-white"}`}
                />
                {!isCollapsed && (
                  <span className="text-[13px] font-bold truncate animate-in fade-in slide-in-from-left-1">
                    {item.name}
                  </span>
                )}
                {isCollapsed && (
                  <div className="absolute left-full ml-4 px-2 py-1 bg-[#08293c] text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-[100] whitespace-nowrap shadow-xl border border-white/10 uppercase tracking-widest">
                    {item.name}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/5">
          <Link
            href="/login"
            className="flex items-center gap-3 px-3.5 py-3 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all w-full group overflow-hidden"
          >
            <LogOut size={20} className="flex-shrink-0" />
            {!isCollapsed && (
              <span className="text-[11px] font-bold uppercase tracking-widest truncate">
                Logout
              </span>
            )}
            {isCollapsed && (
              <div className="absolute left-full ml-4 px-2 py-1 bg-[#08293c] text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-[100] whitespace-nowrap shadow-xl border border-white/10 uppercase tracking-widest">
                Logout
              </div>
            )}
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
            <h1 className="text-sm font-black text-[#08293c] uppercase tracking-[0.2em]">
              {getPageTitle()}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-3 mr-4 border-l border-gray-200 pl-6">
              <div className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <span className="bg-primary/10 text-primary text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded-full flex items-center gap-1 border border-primary/20">
                    <ShieldCheck size={10} /> Admin
                  </span>
                  <p className="text-sm font-medium text-primary leading-tight">
                    {user?.full_name || "Admin"}
                  </p>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {user?.email || "loading..."}
                </p>
              </div>
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold overflow-hidden border-2 border-primary">
                {user?.full_name?.charAt(0) || "A"}
              </div>
            </div>
          </div>
        </header>

        {/* Mobile Sidebar Overlay */}
        {isMobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex">
            <div
              className="fixed inset-0 bg-primary/80 backdrop-blur-sm"
              onClick={() => setIsMobileMenuOpen(false)}
            />

            <aside className="relative flex flex-col w-64 max-w-[80%] h-full bg-primary text-white shadow-2xl animate-in slide-in-from-left">
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <Image
                    src="/images/logo.png"
                    alt="Logo"
                    width={28}
                    height={28}
                  />
                  <div className="flex flex-col">
                    <span className="font-bold text-lg leading-none">
                      DataPulse
                    </span>
                    <span className="text-[10px] text-accent font-semibold tracking-wider uppercase mt-1">
                      Admin Panel
                    </span>
                  </div>
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
                      onClick={() => setIsMobileMenuOpen(false)}
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
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-background scroll-smooth custom-scrollbar">
          <div className="max-w-7xl mx-auto h-full">{children}</div>
        </main>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.05);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.1);
        }

        .sidebar-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .sidebar-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .sidebar-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
}
