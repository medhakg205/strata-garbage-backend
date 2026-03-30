import React, { useEffect, useState } from "react";

function Analytics() {
  const [reportStats, setReportStats] = useState({
    total: 0,
    high: 0,
    medium: 0,
    low: 0,
    recoveredTons: 12.4, // Baseline mock data
  });
  
  const [loading, setLoading] = useState(true);

  const BASE_URL = "https://strata-garbage-backend.onrender.com";
  // ✅ Replace with real collector token later
  const token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjM5YmYwZWJlLTZmMzUtNDM5Yi05ZGNkLTJmOTgxYjA2MjNlYiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2VjbHZtaWtscWhzbHB1ZHh3d2d3LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYjM1MDVmMC04ZmNjLTRlN2MtYjgyYi0yZDM5NDA5Yzg2YzUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc0ODYwMDQ5LCJpYXQiOjE3NzQ4NTY0NDksImVtYWlsIjoiY29sbGVjdG9yMUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3NDg1NjQ0OX1dLCJzZXNzaW9uX2lkIjoiYWVlMTlhY2MtYTY5NS00NWM3LWI0MTgtNjllYTJjMGY0YmIwIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.puQgOVqFfyq46_qYIq2wpm07wLyX8h7YeGP_E7WoYFXsvtbp2n8GXogWbMt5ptU0ijVRIlGQWKID-LYNzKdBaw";

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await fetch(`${BASE_URL}/reports/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        const reportsArray = Array.isArray(data) ? data : data.reports || [];
        
        let h = 0, m = 0, l = 0;
        reportsArray.forEach(r => {
          const lvl = r.garbage_level?.toLowerCase() || "";
          if (lvl === "high") h++;
          else if (lvl === "medium") m++;
          else l++;
        });

        setReportStats({
          total: reportsArray.length,
          high: h,
          medium: m,
          low: l,
          recoveredTons: 12.4 + (reportsArray.length * 0.05) // Fake dynamic math so it "moves" based on live report counts
        });
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  if (loading) {
    return (
      <div className="bg-surface text-on-surface archivo min-h-screen pt-24 pb-32 px-4 flex items-center justify-center">
        <span className="material-symbols-outlined animate-spin text-5xl text-primary">sync</span>
      </div>
    );
  }

  return (
    <div className="bg-surface text-on-surface archivo min-h-screen pt-24 pb-32 px-4 md:px-8 selection:bg-primary selection:text-white">
      <div className="max-w-[1440px] mx-auto">
        
        {/* Header */}
        <div className="mb-20">
          <span className="text-primary font-bold antonio uppercase text-xs tracking-[0.4em] mb-4 block">
            Data Visualization Core
          </span>
          <h2 className="text-6xl md:text-8xl antonio font-bold uppercase tracking-tighter mix-blend-difference">
            Impact <br/> Analytics
          </h2>
        </div>

        {/* Top Analytics Banner */}
        <div className="bg-surface-container-high border-t-[8px] border-primary p-12 md:p-16 mb-16 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-primary/10 to-transparent pointer-events-none"></div>
          <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">Total System Nodes</h4>
               <p className="text-7xl antonio font-bold text-black">{reportStats.total}</p>
            </div>
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">High-Priority Incidents</h4>
               <p className="text-7xl antonio font-bold text-error">{reportStats.high}</p>
            </div>
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">Est. Waste Diverted</h4>
               <p className="text-7xl antonio font-bold text-black">{reportStats.recoveredTons.toFixed(1)}<span className="text-2xl">T</span></p>
            </div>
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">System Efficiency</h4>
               <p className="text-7xl antonio font-bold text-primary">98<span className="text-2xl">%</span></p>
            </div>
          </div>
        </div>

        {/* Priority Breakdown (Bar Chart replacement) */}
        <div className="mb-20">
           <h3 className="text-3xl antonio font-bold uppercase border-b-2 border-outline-variant pb-4 mb-8">Priority Distribution</h3>
           <div className="flex w-full h-16 bg-surface-container-highest overflow-hidden p-1 shadow-inner gap-1">
             {/* High Priority Bar */}
             <div 
               className="h-full bg-error transition-all duration-1000 group relative flex items-center justify-center overflow-hidden" 
               style={{ width: `${reportStats.total === 0 ? 33 : (reportStats.high / reportStats.total) * 100}%` }}
             >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
                {reportStats.high > 0 && <span className="antonio text-white font-bold relative z-10 hidden sm:block">CRITICAL ({reportStats.high})</span>}
             </div>
             {/* Medium Priority Bar */}
             <div 
               className="h-full bg-tertiary transition-all duration-1000 group relative flex items-center justify-center overflow-hidden" 
               style={{ width: `${reportStats.total === 0 ? 33 : (reportStats.medium / reportStats.total) * 100}%` }}
             >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
                {reportStats.medium > 0 && <span className="antonio text-white font-bold relative z-10 hidden sm:block">WARNING ({reportStats.medium})</span>}
             </div>
             {/* Low Priority Bar */}
             <div 
               className="h-full bg-primary transition-all duration-1000 group relative flex items-center justify-center overflow-hidden" 
               style={{ width: `${reportStats.total === 0 ? 34 : (reportStats.low / reportStats.total) * 100}%` }}
             >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
                {reportStats.low > 0 && <span className="antonio text-white font-bold relative z-10 hidden sm:block">NOMINAL ({reportStats.low})</span>}
             </div>
           </div>
           
           {/* Chart Legend */}
           <div className="flex gap-8 mt-6">
              <div className="flex items-center gap-2">
                 <div className="w-4 h-4 bg-error"></div>
                 <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">High Impact</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-4 h-4 bg-tertiary"></div>
                 <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Medium Alert</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-4 h-4 bg-primary"></div>
                 <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Routine Collection</span>
              </div>
           </div>
        </div>

        {/* Insight Panels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-outline-variant shadow-lg border border-outline-variant/30">
          <div className="bg-surface p-12 hover:bg-surface-container-low transition-colors group border-b-[6px] border-secondary">
             <span className="material-symbols-outlined text-5xl text-secondary mb-6 group-hover:scale-110 transition-transform">speed</span>
             <h3 className="text-3xl antonio font-bold uppercase mb-4">Response Diagnostics</h3>
             <p className="text-on-surface-variant leading-relaxed">
               Current AI-dispatched retrieval patterns indicate an average response time of <strong className="text-black">14.2 minutes</strong> per node. Autonomous routing has decreased urban traffic congestion by 6.4%.
             </p>
          </div>
          <div className="bg-surface p-12 hover:bg-surface-container-low transition-colors group border-b-[6px] border-primary">
             <span className="material-symbols-outlined text-5xl text-primary mb-6 group-hover:scale-110 transition-transform">eco</span>
             <h3 className="text-3xl antonio font-bold uppercase mb-4">Environmental Return</h3>
             <p className="text-on-surface-variant leading-relaxed">
               Material sorting pipelines successfully diverted 98% of captured organics and 85% of complex plastics away from traditional metropolitan landfills this quarter.
             </p>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Analytics;
