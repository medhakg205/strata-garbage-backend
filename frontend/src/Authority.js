import React, { useEffect, useState } from "react";

function Authority() {
  const [reports, setReports] = useState([]);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);

  const BASE_URL = "https://strata-garbage-backend.onrender.com";

  // ✅ Collector token (works in Postman)
  const token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjM5YmYwZWJlLTZmMzUtNDM5Yi05ZGNkLTJmOTgxYjA2MjNlYiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2VjbHZtaWtscWhzbHB1ZHh3d2d3LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYjM1MDVmMC04ZmNjLTRlN2MtYjgyYi0yZDM5NDA5Yzg2YzUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc0ODYwMDQ5LCJpYXQiOjE3NzQ4NTY0NDksImVtYWlsIjoiY29sbGVjdG9yMUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3NDg1NjQ0OX1dLCJzZXNzaW9uX2lkIjoiYWVlMTlhY2MtYTY5NS00NWM3LWI0MTgtNjllYTJjMGY0YmIwIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.puQgOVqFfyq46_qYIq2wpm07wLyX8h7YeGP_E7WoYFXsvtbp2n8GXogWbMt5ptU0ijVRIlGQWKID-LYNzKdBaw";

  // Fetch all active reports on mount
  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await fetch(`${BASE_URL}/reports/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        const reportsArray = Array.isArray(data) ? data : data.reports || [];
        setReports(reportsArray);
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      }
    };

    fetchReports();
  }, []);

  // Optimize route handler
  const handleOptimize = async () => {
    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/optimize-route/`, {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const errData = await res.json();
        console.error("Optimize route error:", errData);
        setLoading(false);
        return;
      }

      const data = await res.json();
      console.log("Route:", data);
      setRoute(data);
      setLoading(false);
    } catch (err) {
      console.error("Optimize route failed:", err);
      setLoading(false);
    }
  };

  return (
    <div className="bg-surface text-on-surface archivo min-h-screen pt-24 pb-32 px-4 md:px-8 selection:bg-primary selection:text-white">
      <div className="max-w-[1440px] mx-auto">
        
        {/* Header Block */}
        <div className="mb-16">
          <span className="text-secondary font-bold antonio uppercase text-xs tracking-[0.2em] mb-4 block">
            Command Terminal Active
          </span>
          <h2 className="text-6xl md:text-8xl antonio font-bold uppercase leading-[0.85] tracking-tighter">
            Logistics<br/>Command Core
          </h2>
        </div>

        {/* Action Panel */}
        <div className="bg-surface-container-low p-8 md:p-12 mb-16 border-l-[6px] border-secondary relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-secondary/5 to-transparent z-0 pointer-events-none"></div>
          <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-8">
            <div className="max-w-xl">
              <h3 className="text-3xl antonio font-bold uppercase mb-4 text-on-surface">Route Optimization Matrix</h3>
              <p className="text-on-surface-variant font-medium leading-relaxed">
                Compute the most efficient metropolitan collection pathing using high-fidelity spatial telemetry from active civic nodes.
              </p>
            </div>
            <button
              className="bg-black text-white px-10 py-5 antonio font-bold uppercase text-lg hover:bg-secondary hover:text-white transition-all w-full md:w-auto active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3 border-none"
              onClick={handleOptimize}
              disabled={loading}
              style={{ borderRadius: "0" }} // Strictly enforcing the zero-border-radius design spec
            >
              {loading ? (
                <><span className="material-symbols-outlined text-xl animate-spin">sync</span> PROCESSING VECTOR...</>
              ) : (
                <><span className="material-symbols-outlined text-xl">route</span> INITIALIZE PATH</>
              )}
            </button>
          </div>
        </div>

        {/* Optimized Route Display */}
        {route && (
          <div className="mb-24 animate-slide-up">
            <div className="flex justify-between items-end border-b-2 border-outline-variant pb-6 mb-8">
               <h3 className="text-4xl antonio font-bold uppercase">Optimal Vector</h3>
               <span className="text-sm font-bold antonio uppercase bg-surface-container-highest px-4 py-2 border border-outline-variant tracking-wider">
                 Total Stops: <span className="text-secondary ml-2 text-xl">{route.total_spots}</span>
               </span>
            </div>
            
            {/* Using a 1px gap on a dark background to create 1px borders seamlessly */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-outline-variant">
              {route.optimized_path?.map((coord, index) => (
                <div key={index} className="bg-surface p-8 hover:bg-surface-container-low transition-colors group">
                  <div className="flex justify-between items-start mb-12">
                     <span className="text-6xl font-bold antonio text-secondary/20 group-hover:text-secondary transition-colors leading-none">
                       {String(index + 1).padStart(2, '0')}
                     </span>
                     <span className="material-symbols-outlined text-on-surface-variant group-hover:text-secondary opacity-50 group-hover:opacity-100 transition-opacity">
                       location_on
                     </span>
                  </div>
                  <div>
                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">Waypoint</h4>
                    <p className="text-2xl antonio font-bold text-on-surface">
                       {coord[1].toFixed(4)}<br/>
                       <span className="text-on-surface-variant/70">{coord[0].toFixed(4)}</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active Reports Block */}
        <div className="border-t-[8px] border-primary pt-16 mt-16">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-6">
            <div>
               <span className="text-primary font-bold antonio uppercase text-xs tracking-[0.2em] mb-4 block">
                 System Telemetry
               </span>
               <h3 className="text-5xl md:text-6xl antonio font-bold uppercase tracking-tighter">
                 Active Incident Nodes
               </h3>
            </div>
            <div className="bg-primary text-on-primary px-6 py-3 shrink-0 flex items-center">
               <span className="text-5xl font-bold antonio">{reports.length}</span>
               <span className="text-[10px] font-bold uppercase tracking-widest ml-3 opacity-90 leading-tight">Total<br/>Nodes</span>
            </div>
          </div>

          {reports.length === 0 ? (
            <div className="bg-surface-container-highest p-16 text-center border border-outline-variant/30">
               <span className="material-symbols-outlined text-6xl text-outline mb-4">check_circle</span>
               <h4 className="text-2xl antonio font-bold uppercase text-on-surface-variant mb-2">Systems Nominal</h4>
               <p className="text-sm font-medium text-on-surface-variant/70 max-w-sm mx-auto">
                 Zero active incident parameters detected across the metropolitan sensor grid.
               </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-outline-variant shadow-lg">
              {reports.map((r) => {
                 const lvl = r.garbage_level?.toLowerCase() || "unknown";
                 const isHigh = lvl === "high";
                 const isMedium = lvl === "medium";
                 
                 // Apply functional brutalism colors based on priority severity
                 // Using native tailwind classes from the Design System configuration
                 const levelStyles = isHigh 
                    ? "bg-error text-on-error" 
                    : isMedium 
                       ? "bg-tertiary text-on-tertiary" 
                       : "bg-primary text-on-primary";
                 
                 return (
                   <div key={r.id} className="bg-surface p-8 hover:bg-surface-container-highest transition-colors flex flex-col justify-between aspect-square group relative overflow-hidden">
                     {/* Decorative subtle pulse if high priority */}
                     {isHigh && <div className="absolute inset-0 bg-error/5 group-hover:bg-error/10 animate-pulse pointer-events-none"></div>}
                     
                     <div className="relative z-10 flex justify-between items-start mb-8">
                        <span className="material-symbols-outlined text-on-surface-variant group-hover:text-black transition-colors opacity-50 group-hover:opacity-100">
                          satellite_alt
                        </span>
                        <span className={`px-3 py-1 font-bold antonio uppercase text-[10px] tracking-widest ${levelStyles}`}>
                           {lvl}
                        </span>
                     </div>
                     <div className="relative z-10 mt-auto">
                       <p className="text-[10px] uppercase font-bold text-on-surface-variant tracking-widest mb-3 border-b border-black/10 pb-2">
                         Geospatial Anchor
                       </p>
                       <p className="text-3xl md:text-4xl antonio font-bold text-on-surface group-hover:text-black transition-colors leading-[1]">
                         {r.location?.lat?.toFixed(5)}<br/>
                         {r.location?.lng?.toFixed(5)}
                       </p>
                     </div>
                   </div>
                 );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default Authority;
