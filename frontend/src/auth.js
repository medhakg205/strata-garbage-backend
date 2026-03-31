import React, { useState } from "react";
import supabase from "./supabaseClient";

function Auth({ onAuthSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    setLoading(true);
    if (isSignup) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) {
        setLoading(false);
        return alert(error.message);
      }

      if (!data.user) {
        setLoading(false);
        return alert("Signup failed");
      }

      alert("Signup successful. Now login.");
      setIsSignup(false);
    } else {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setLoading(false);
        return alert(error.message);
      }

      onAuthSuccess(data.session);
    }
    setLoading(false);
  };

  return (
    <div className="bg-surface text-on-surface archivo min-h-screen pt-24 pb-32 px-4 md:px-8 selection:bg-primary selection:text-white">
      <div className="max-w-[600px] mx-auto">
        {/* Header Block */}
        <div className="mb-12">
          <span className="text-secondary font-bold antonio uppercase text-xs tracking-[0.2em] mb-4 block">
            System Access Required
          </span>
          <h2 className="text-6xl md:text-7xl antonio font-bold uppercase leading-[0.85] tracking-tighter">
            {isSignup ? "Personnel" : "Collector"}
            <br />
            {isSignup ? "Registration" : "Authentication"}
          </h2>
        </div>

        {/* Auth Form Panel */}
        <div className="bg-surface-container-low p-8 md:p-12 border-l-[6px] border-secondary relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-secondary/5 to-transparent z-0 pointer-events-none"></div>
          
          <div className="relative z-10 space-y-6">
            <div className="space-y-2">
              <label className="antonio uppercase font-bold text-xs tracking-widest text-secondary">
                Security Identifier (Email)
              </label>
              <input
                type="email"
                placeholder="NAME@DOMAIN.COM"
                className="w-full bg-surface border border-on-surface/10 p-4 outline-none focus:border-secondary transition-colors archivo uppercase placeholder:opacity-30"
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="antonio uppercase font-bold text-xs tracking-widest text-secondary">
                Access Phrase (Password)
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full bg-surface border border-on-surface/10 p-4 outline-none focus:border-secondary transition-colors"
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="pt-4 flex flex-col gap-4">
              <button
                className="bg-black text-white px-10 py-5 antonio font-bold uppercase text-lg hover:bg-secondary transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3"
                onClick={handleAuth}
                disabled={loading || !email || !password}
                style={{ borderRadius: "0" }}
              >
                {loading ? (
                  <>
                    <span className="material-symbols-outlined text-xl animate-spin">sync</span>
                    VERIFYING...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-xl">
                      {isSignup ? "person_add" : "login"}
                    </span>
                    {isSignup ? "Create Account" : "Establish Connection"}
                  </>
                )}
              </button>

              <button
                onClick={() => setIsSignup(!isSignup)}
                className="text-on-surface-variant font-bold antonio uppercase text-sm tracking-widest hover:text-secondary transition-colors text-center"
              >
                {isSignup ? "Already Registered? Login" : "New Personnel? Register Here"}
              </button>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-8 opacity-40 text-[10px] uppercase tracking-[0.3em] text-center">
          Terminal ID: {Math.random().toString(36).substr(2, 9).toUpperCase()} // Encrypted Session
        </div>
      </div>
    </div>
  );
}

export default Auth;