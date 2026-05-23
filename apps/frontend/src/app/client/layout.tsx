"use client";

import Link from "next/link";
import { Toaster } from "@/components/ui/sonner";
import { useState, useEffect, Suspense } from "react";
import { Menu, X } from "lucide-react";
import { UsernameModal } from "@/components/username-modal";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [currentUsername, setCurrentUsername] = useState<string | null>(null);

  // İlk yüklemede username kontrolü
  useEffect(() => {
    const username = localStorage.getItem("appq_username");
    if (!username) {
      setShowModal(true);
    } else {
      setCurrentUsername(username);
    }
  }, []);

  function handleLogout() {
    localStorage.removeItem("appq_username");
    window.location.href = "/";
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col md:flex-row">

      {/* Username Modal — ilk girişte göster */}
      {showModal && (
        <Suspense>
          <UsernameModal onComplete={(username) => {
            setCurrentUsername(username);
            setShowModal(false);
          }} />
        </Suspense>
      )}

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between p-4 border-b border-border bg-sidebar">
        <Link href="/" className="flex items-center gap-2">
          <img src="/logo.png" alt="Clarere" className="h-8 w-auto object-contain" />
          <span className="font-semibold tracking-tight text-lg">Clarere</span>
        </Link>
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 border border-border rounded-md hover:bg-sidebar-accent transition-colors"
          aria-label="Toggle menu"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Sidebar - Desktop & Mobile Drawer */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 border-r border-border bg-sidebar p-6 flex flex-col gap-8 transition-transform duration-300 md:translate-x-0 md:static md:z-auto
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <img src="/logo.png" alt="Clarere" className="h-8 w-auto object-contain" />
            <span className="font-semibold tracking-tight text-lg">Clarere</span>
          </Link>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1 border border-border rounded-md hover:bg-sidebar-accent transition-colors"
            aria-label="Close menu"
          >
            <X size={16} />
          </button>
        </div>
        
        <nav className="flex flex-col gap-2 flex-1">
          <Link 
            href="/client" 
            onClick={() => setSidebarOpen(false)}
            className="px-3 py-2 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground text-sm font-medium transition-colors"
          >
            Dashboard
          </Link>
        </nav>

        <div className="mt-auto border-t border-border pt-4">
          <p className="text-xs text-muted-foreground">
            {currentUsername ? (
              <span>👤 <strong>{currentUsername}</strong></span>
            ) : (
              "Oturum: Client"
            )}
          </p>
          <button
            onClick={handleLogout}
            className="text-xs text-accent hover:underline mt-1 inline-block bg-transparent border-none p-0 cursor-pointer"
          >
            Çıkış Yap
          </button>
        </div>
      </aside>

      {/* Backdrop for mobile */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 md:hidden animate-in fade-in"
        />
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
      <Toaster />
    </div>
  );
}
