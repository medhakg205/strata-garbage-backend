import React, { useState } from "react";
import LandingPage from "./LandingPage";
import Authority from "./Authority";
import Analytics from "./Analytics";

function App() {
  const [page, setPage] = useState("citizen");

  return (
    <div className="app-wrapper bg-surface min-h-screen">
      {/* Custom toggle to switch views smoothly without breaking the layout */}
      <div className="fixed bottom-8 right-8 z-[9999] flex gap-2 p-2 rounded-xl backdrop-blur-md shadow-2xl bg-surface/80 border border-outline-variant/30">
        <button 
  className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded transition-all ${
    page === "citizen" 
      ? 'bg-primary text-white' 
      : 'bg-transparent text-on-surface hover:bg-black/5'
  }`}
  onClick={() => setPage("citizen")}
>
  Citizen View
</button>
<button 
  className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded transition-all ${
    page === "authority" 
      ? 'bg-black text-white'  // Note: you had 'bg-black' here already
      : 'bg-transparent text-on-surface hover:bg-black/5'
  }`}
  onClick={() => setPage("authority")}
>
  Authority View
</button>
      </div>

      {page === "citizen" && <LandingPage onNavigate={setPage} />}
      {page === "authority" && <div className="pt-24"><Authority /></div>}
    </div>
  );
}

export default App;