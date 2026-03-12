"use client";

import Link from "next/link";
import Image from "next/image";
import { ArrowUpRight } from "lucide-react";

export default function MinimalistLanding() {
  return (
    <div className="flex flex-col min-h-screen bg-[#FDFDFD] font-sans selection:bg-accent/30">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
        <Link href="/" className="flex items-center gap-2 group cursor-pointer">
          <Image
            src="/images/logo.png"
            alt="DataPulse Logo"
            width={96}
            height={96}
            className="h-24 w-auto object-contain"
            priority
          />
        </Link>

        <div className="flex items-center gap-6">
          <Link
            href="/login"
            className="text-[13px] font-bold text-[#08293c] hover:opacity-70 transition-opacity"
          >
            Log In
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 bg-[#ff5a00] text-white text-[13px] font-bold rounded-lg hover:shadow-lg hover:shadow-[#ff5a00]/20 transition-all font-sans"
          >
            Try for free
          </Link>
        </div>
      </nav>

      <main className="flex-1 flex flex-col items-center">
        {/* Hero Section */}
        <section className="pt-24 pb-12 px-6 text-center max-w-4xl mx-auto">
          <h1 className="text-3xl md:text-5xl font-extrabold text-[#08293c] tracking-tight mb-4 leading-[1.15]">
            Data quality, <br />
            <span className="text-gray-400 font-bold">made simple.</span>
          </h1>
          <p className="text-xs md:text-sm text-gray-400 font-medium max-w-lg mx-auto mb-10 leading-relaxed overflow-hidden">
            DataPulse is the simplest way to validate, monitor and track{" "}
            <br className="hidden md:block" />
            the health of your CSV and JSON datasets.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-24 font-bold">
            <Link
              href="/register"
              className="px-10 py-3.5 bg-[#ff5a00] text-white rounded-full hover:shadow-xl hover:shadow-[#ff5a00]/20 transition-all flex items-center gap-2"
            >
              Try for free
            </Link>
            <Link
              href="/login"
              className="px-10 py-3.5 bg-white border border-gray-100 text-[#08293c] rounded-full hover:bg-gray-50 transition-all flex items-center gap-2"
            >
              Try the demo <ArrowUpRight size={16} className="text-gray-300" />
            </Link>
          </div>

          {/* Screenshot Area */}
          <div className="relative w-full max-w-4xl px-4">
            <div className="rounded-[32px] border-[10px] border-white shadow-[0_30px_80px_-15px_rgba(0,0,0,0.08)] overflow-hidden bg-white">
              <div className="bg-gray-50 border-b border-gray-100 px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-200"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-orange-200"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-200"></div>
                </div>
                <div className="flex-1 max-w-xs mx-auto bg-white rounded-md py-1 border border-gray-100 text-[9px] text-gray-400 text-center font-mono tracking-wider">
                  datapulse/dashboard/user
                </div>
              </div>
              <div className="aspect-[16/10] relative bg-white flex items-center justify-center overflow-hidden">
                <Image
                  src="/images/dashboard_mockup.png"
                  alt="Dashboard Preview"
                  fill
                  className="object-cover scale-[1.02] transform transition-transform duration-1000"
                  unoptimized
                />
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-16 flex flex-col items-center">
        <div className="w-full h-px bg-gradient-to-r from-transparent via-gray-100 to-transparent mb-10 max-w-4xl"></div>
        <p className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.25em]">
          DataPulse © 2026 Team 9
        </p>
      </footer>
    </div>
  );
}
