"use client";
import { useUser } from "@auth0/nextjs-auth0/client";
import Link from "next/link";

export default function Home() {
  const { user, isLoading } = useUser();

  if (isLoading) return <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>;

  return (
    <main className="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-2">🛡️ Vanguard</h1>
        <p className="text-gray-400 text-xl">Secure Execution Gateway for AI Agents</p>
        <p className="text-gray-500 mt-2 text-sm">Okta for Machines — Zero Trust Agent Authorization</p>
      </div>

      {user ? (
        <div className="flex flex-col items-center gap-4">
          <p className="text-green-400">Welcome, {user.name}</p>
          <Link
            href="/dashboard"
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition"
          >
            Open Dashboard →
          </Link>
          <Link href="/api/auth/logout" className="text-gray-500 hover:text-gray-300 text-sm">
            Sign out
          </Link>
        </div>
      ) : (
        <Link
          href="/api/auth/login"
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition"
        >
          Sign in with Auth0
        </Link>
      )}
    </main>
  );
}
