'use client';

import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import type { AuthState } from '@/store/auth';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const isAuthenticated = useAuthStore((state: AuthState) => state.isAuthenticated);
  const logout = useAuthStore((state: AuthState) => state.logout);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link href="/" className="flex items-center">
                <span className="text-xl font-bold text-indigo-600">UNBOUNDED</span>
              </Link>
            </div>
            <div className="flex items-center">
              {isAuthenticated ? (
                <>
                  <Link href="/characters" className="text-gray-700 hover:text-indigo-600 px-3 py-2">
                    Characters
                  </Link>
                  <button
                    onClick={logout}
                    className="text-gray-700 hover:text-indigo-600 px-3 py-2"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link href="/auth/login" className="text-gray-700 hover:text-indigo-600 px-3 py-2">
                    Login
                  </Link>
                  <Link href="/auth/register" className="text-gray-700 hover:text-indigo-600 px-3 py-2">
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
} 