import React, { useEffect, useState, useCallback } from 'react';

import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';


export default function LandingPage({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Realtime Analytics States
  const [reportStats, setReportStats] = useState({
    total: 0,
    high: 0,
    medium: 0,
    low: 0,
    recoveredTons: 12.4,
  });

  const BASE_URL = "https://strata-garbage-backend.onrender.com";
  // ✅ Replace with real collector token later
  const token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjM5YmYwZWJlLTZmMzUtNDM5Yi05ZGNkLTJmOTgxYjA2MjNlYiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2VjbHZtaWtscWhzbHB1ZHh3d2d3LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYjM1MDVmMC04ZmNjLTRlN2MtYjgyYi0yZDM5NDA5Yzg2YzUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc0Nzk2MDQ5LCJpYXQiOjE3NzQ3OTI0NDksImVtYWlsIjoiY29sbGVjdG9yMUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3NDc5MjQ0OX1dLCJzZXNzaW9uX2lkIjoiNDFmOTlkMTgtNjMwYy00MGM5LTljZWItYTk5Y2U1M2FiY2Q5IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.EcdfSf1DZuIXLwiUb1BqhsmxmKEn0pJLjUd4hyMQPXTDtNP5IGzpXOfSFiZ8JLcinK2l7YA2ZoKleE5vU5eTew";

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      toast.success("Image selected successfully!");
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: { 'image/*': [] },
    multiple: false 
  });

  const getLocation = (e) => {
    e.preventDefault();
    const locToast = toast.loading("Fetching GPS coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        toast.success("Location Synced! 📍", { id: locToast });
      },
      () => toast.error("Location access denied or failed.", { id: locToast })
    );
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !location) {
      toast.error("Please provide both an image and your location.");
      return;
    }
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lat", location.lat);
    formData.append("lng", location.lng);

    const uploadToast = toast.loading("Analyzing image with AI...");
    try {
      setLoading(true);
      const res = await fetch(`${BASE_URL}/reports/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      setLoading(false);

      if (!res.ok) {
        let msg = "Request failed";
        if (Array.isArray(data.detail)) {
          msg = data.detail.map(e => e.msg).join(", ");
        } else if (typeof data.detail === "string") {
          msg = data.detail;
        }
        toast.error(`❌ ${msg}`, { id: uploadToast });
        return;
      }

      if (data.level) {
        toast.success(`Report submitted! Priority: ${data.level.toUpperCase()}`, { id: uploadToast, duration: 5000 });
        setFile(null);
        setLocation(null);
      } else if (data.message === "Not garbage ❌") {
        toast.error("AI determined this is not garbage. Rejected.", { id: uploadToast, duration: 4000 });
      } else {
        toast.success("Report submitted successfully!", { id: uploadToast });
        setFile(null);
        setLocation(null);
      }
    } catch (err) {
      console.error(err);
      setLoading(false);
      toast.error("Network error. Upload failed.", { id: uploadToast });
    }
  };

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
          recoveredTons: 12.4 + (reportsArray.length * 0.05) 
        });
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      }
    };

    fetchReports();
  }, [BASE_URL, token]);


  return (
    <div className="bg-surface text-on-surface archivo selection:bg-primary selection:text-white">
<nav className="fixed top-0 w-full z-50 bg-surface/80 dark:bg-black/80 backdrop-blur-xl border-b border-black/5">
<div className="flex justify-between items-center px-8 py-4 max-w-[1440px] mx-auto">
<div className="text-2xl font-bold tracking-tighter uppercase text-black dark:text-white antonio">
            STRATA GARBAGE
        </div>
<div className="hidden md:flex items-center gap-12">
<a className="text-green-600 dark:text-green-500 font-bold border-b-2 border-green-600 transition-colors duration-300 antonio uppercase text-sm tracking-wider" href="/#">Systems</a>
<button onClick={() => document.getElementById('analytics')?.scrollIntoView({behavior: 'smooth'})} className="text-black/60 dark:text-white/60 font-medium hover:text-green-600 dark:hover:text-green-400 transition-colors duration-300 antonio uppercase text-sm tracking-wider uppercase">Impact</button>
<button onClick={() => document.getElementById('analytics')?.scrollIntoView({behavior: 'smooth'})} className="text-black/60 dark:text-white/60 font-medium hover:text-green-600 dark:hover:text-green-400 transition-colors duration-300 antonio uppercase text-sm tracking-wider uppercase">Analytics</button>
<a className="text-black/60 dark:text-white/60 font-medium hover:text-green-600 dark:hover:text-green-400 transition-colors duration-300 antonio uppercase text-sm tracking-wider" href="/#">Network</a>
</div>
<div className="flex items-center gap-4">
<button onClick={() => onNavigate("authority")} className="px-6 py-2 border border-black/10 dark:border-white/10 antonio uppercase text-xs font-bold hover:bg-black hover:text-white transition-all active:scale-95">
                Dashboard
            </button>
<button onClick={() => window.scrollTo({top: window.innerHeight, behavior: "smooth"})} className="px-6 py-2 bg-primary text-on-primary antonio uppercase text-xs font-bold hover:bg-primary-container transition-all active:scale-95">
                Report Waste
            </button>
</div>
</div>
</nav>
<main>
{/* Section 1: Static Hero Container */}
<div className="relative h-screen w-full flex flex-col justify-center items-center bg-surface overflow-hidden px-4">
  {/* Dark Brutalist Gradient Background instead of images */}
  <div className="absolute inset-0 bg-gradient-to-b from-[#112217] via-surface to-surface-container-low opacity-60 z-0"></div>
  <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,107,44,0.15)_0%,transparent_50%)] z-0"></div>
  
  {/* Foreground Content */}
  <div className="relative z-10 text-center max-w-5xl mt-24">
    <p className="text-primary font-bold tracking-[0.4em] mb-4 text-xs antonio uppercase">Civic Intelligence Layer 01</p>
    <h1 className="text-7xl md:text-9xl antonio font-bold leading-[0.85] tracking-[-0.05em] uppercase mb-8 text-on-surface">
        CLEAN CITY.<br/>SMART FUTURE.
    </h1>
    <p className="text-xl md:text-2xl max-w-2xl mx-auto mb-10 text-on-surface-variant font-medium bg-surface/40 backdrop-blur-sm p-4 border border-outline-variant/30">
        AI-powered waste detection and reporting system designed for high-performance urban maintenance.
    </p>
    <div className="flex flex-col md:flex-row items-center justify-center gap-6">
        <button onClick={() => window.scrollTo({top: window.innerHeight, behavior: "smooth"})} className="bg-primary text-white px-12 py-5 text-xl antonio uppercase font-bold hover:bg-primary-container transition-colors w-full md:w-auto shadow-xl hover:scale-105 active:scale-95 duration-300">
            Report Waste
        </button>
        <button onClick={() => document.getElementById('analytics')?.scrollIntoView({behavior: 'smooth'})} className="border border-outline-variant bg-surface/80 text-on-surface px-12 py-5 text-xl antonio uppercase font-bold hover:bg-surface-container transition-colors w-full md:w-auto backdrop-blur-md hover:scale-105 active:scale-95 duration-300">
            View Analytics
        </button>
    </div>
  </div>
</div>
{/* Section 2: Report Waste (Functional Shell) */}
<section className="bg-surface-container-low py-32 px-8">
<div className="max-w-[1440px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
<div className="sticky top-32">
<span className="text-primary font-bold antonio uppercase text-xs tracking-widest mb-4 block">Deployment Stage 01</span>
<h2 className="text-6xl antonio font-bold uppercase leading-none mb-8">Immediate<br/>Reporting Hub</h2>
<p className="text-xl text-on-surface-variant mb-12 max-w-md">Our neural network identifies waste types in milliseconds, prioritizing critical sanitation alerts for municipal rapid-response teams.</p>
<div className="space-y-6">
<div className="flex items-center gap-6 p-6 bg-surface-container-highest">
<span className="material-symbols-outlined text-primary text-4xl">add_a_photo</span>
<div>
<h4 className="antonio font-bold uppercase">Visual Capture</h4>
<p className="text-sm opacity-70">Automatic categorization via computer vision.</p>
</div>
</div>
<div className="flex items-center gap-6 p-6 bg-surface-container-highest">
<span className="material-symbols-outlined text-secondary text-4xl">location_on</span>
<div>
<h4 className="antonio font-bold uppercase">Geospatial Tagging</h4>
<p className="text-sm opacity-70">Precise GPS coordinates for infrastructure routing.</p>
</div>
</div>
</div>
</div>
<div className="bg-surface-bright p-12 shadow-2xl">

<div {...getRootProps()} className={`border-2 border-dashed h-80 flex flex-col items-center justify-center text-center p-8 mb-8 hover:border-primary transition-colors cursor-pointer ${isDragActive ? 'border-primary bg-primary-fixed-dim/20' : 'border-outline-variant bg-surface-bright'}`}>
<input {...getInputProps()} />
<span className="material-symbols-outlined text-6xl text-outline mb-4">{isDragActive ? 'download' : 'cloud_upload'}</span>
<h3 className="antonio font-bold uppercase text-2xl">{file ? file.name : 'Upload Visual Data'}</h3>
<p className="text-sm text-on-surface-variant mt-2">Drag and drop high-resolution imagery or select file</p>
</div>


<form className="space-y-8" onSubmit={handleUpload}>
<div>
  <label className="block text-[10px] antonio font-bold uppercase text-primary mb-2">Location Context (Auto-Fetched Data)</label>
  <div className="flex gap-4 mb-4">
    <input value={location ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` : ''} readOnly className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary px-4 py-4 focus:ring-0 transition-all outline-none" placeholder="Detecting current coordinates..." type="text"/>
    <button type="button" onClick={getLocation} className="px-6 bg-surface-container-highest border-b-2 border-outline-variant hover:border-primary uppercase text-xs font-bold antonio shadow-sm active:scale-95 transition-all">SYNC GPS</button>
  </div>
  {location && (
    <div className="w-full h-40 overflow-hidden mb-4 border border-outline-variant/30">
      <iframe
        title="map"
        width="100%"
        height="100%"
        style={{ border: 0 }}
        src={`https://www.openstreetmap.org/export/embed.html?bbox=${location.lng - 0.005}%2C${location.lat - 0.005}%2C${location.lng + 0.005}%2C${location.lat + 0.005}&layer=mapnik&marker=${location.lat}%2C${location.lng}`}
      ></iframe>
    </div>
  )}
</div>
<div>
  <label className="block text-[10px] antonio font-bold uppercase text-primary mb-2">Report Description</label>
  <textarea className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary px-4 py-4 focus:ring-0 transition-all outline-none" placeholder="Additional metadata for waste classification..." rows={3}></textarea>
</div>
<button type="submit" disabled={loading} className="w-full bg-black text-white py-6 antonio font-bold uppercase text-xl hover:bg-primary transition-all active:scale-95 disabled:opacity-50">
  {loading ? "Processing AI Analysis..." : "Submit to Strata Network"}
</button>
</form>

</div>
</div>
</section>
{/* Section 3: How It Works (Linear Flow) */}
<section className="py-32 px-8 bg-surface">
<div className="max-w-[1440px] mx-auto">
<div className="flex flex-col md:flex-row justify-between items-end mb-24 gap-8">
<h2 className="text-7xl antonio font-bold uppercase leading-[0.85] tracking-tighter">The System<br/>Process</h2>
<p className="max-w-xs text-sm font-semibold uppercase opacity-60">Architectural breakdown of real-time waste management logistics and AI verification loops.</p>
</div>
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-outline-variant/20">
<div className="bg-surface p-10 hover:bg-surface-container-low transition-colors group">
<span className="text-5xl font-bold antonio text-primary/20 group-hover:text-primary transition-colors">01</span>
<h3 className="text-2xl antonio font-bold uppercase mt-8 mb-4">Upload Image</h3>
<p className="text-on-surface-variant leading-relaxed">High-fidelity visual intake via citizen or autonomous drone reporting modules.</p>
</div>
<div className="bg-surface p-10 hover:bg-surface-container-low transition-colors group">
<span className="text-5xl font-bold antonio text-primary/20 group-hover:text-primary transition-colors">02</span>
<h3 className="text-2xl antonio font-bold uppercase mt-8 mb-4">AI Detects Waste</h3>
<p className="text-on-surface-variant leading-relaxed">Neural analysis identifies volume, material type, and chemical hazard levels.</p>
</div>
<div className="bg-surface p-10 hover:bg-surface-container-low transition-colors group">
<span className="text-5xl font-bold antonio text-primary/20 group-hover:text-primary transition-colors">03</span>
<h3 className="text-2xl antonio font-bold uppercase mt-8 mb-4">Assign Priority</h3>
<p className="text-on-surface-variant leading-relaxed">Algorithmic sorting based on environmental impact and urban traffic density.</p>
</div>
<div className="bg-surface p-10 hover:bg-surface-container-low transition-colors group">
<span className="text-5xl font-bold antonio text-primary/20 group-hover:text-primary transition-colors">04</span>
<h3 className="text-2xl antonio font-bold uppercase mt-8 mb-4">Notify Authority</h3>
<p className="text-on-surface-variant leading-relaxed">Direct dispatching to the nearest available high-performance recovery unit.</p>
</div>
</div>
</div>
</section>
      {/* Integrated Analytics & Impact Section */}
      <section id="analytics" className="py-32 px-4 md:px-8 bg-surface-container-high border-t-[8px] border-primary relative overflow-hidden">
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-primary/5 to-transparent pointer-events-none"></div>
        <div className="max-w-[1440px] mx-auto relative z-10">
          <div className="mb-20">
            <span className="text-primary font-bold antonio uppercase text-xs tracking-[0.4em] mb-4 block">
              Data Visualization Core
            </span>
            <h2 className="text-6xl md:text-8xl antonio font-bold uppercase tracking-tighter">
              Live Network <br/> Analytics
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-20 bg-surface/50 p-12 shadow-inner border border-outline-variant/30 backdrop-blur-sm">
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">Total System Nodes</h4>
               <p className="text-7xl antonio font-bold text-on-surface">{reportStats.total}</p>
            </div>
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">High-Priority Incidents</h4>
               <p className="text-7xl antonio font-bold text-error">{reportStats.high}</p>
            </div>
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">Est. Waste Diverted</h4>
               <p className="text-7xl antonio font-bold text-on-surface">{reportStats.recoveredTons.toFixed(1)}<span className="text-2xl">T</span></p>
            </div>
            <div>
               <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">System Efficiency</h4>
               <p className="text-7xl antonio font-bold text-primary">98<span className="text-2xl">%</span></p>
            </div>
          </div>

          {/* Priority Breakdown (Bar Chart replacement) */}
          <div className="mb-24">
             <h3 className="text-3xl antonio font-bold uppercase border-b-2 border-outline-variant pb-4 mb-8">Priority Distribution Volume</h3>
             <div className="flex w-full h-20 bg-surface-container-highest overflow-hidden p-1 shadow-inner gap-1">
               <div 
                 className="h-full bg-error transition-all duration-1000 group relative flex items-center justify-center overflow-hidden" 
                 style={{ width: `${reportStats.total === 0 ? 33 : (reportStats.high / reportStats.total) * 100}%` }}
               >
                  <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
                  {reportStats.high > 0 && <span className="antonio text-on-error font-bold relative z-10 hidden sm:block">CRITICAL ({reportStats.high})</span>}
               </div>
               <div 
                 className="h-full bg-tertiary transition-all duration-1000 group relative flex items-center justify-center overflow-hidden" 
                 style={{ width: `${reportStats.total === 0 ? 33 : (reportStats.medium / reportStats.total) * 100}%` }}
               >
                  <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
                  {reportStats.medium > 0 && <span className="antonio text-on-tertiary font-bold relative z-10 hidden sm:block">WARNING ({reportStats.medium})</span>}
               </div>
               <div 
                 className="h-full bg-primary transition-all duration-1000 group relative flex items-center justify-center overflow-hidden" 
                 style={{ width: `${reportStats.total === 0 ? 34 : (reportStats.low / reportStats.total) * 100}%` }}
               >
                  <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
                  {reportStats.low > 0 && <span className="antonio text-on-primary font-bold relative z-10 hidden sm:block">NOMINAL ({reportStats.low})</span>}
               </div>
             </div>
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

          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-outline-variant shadow-lg border border-outline-variant/30">
            <div className="bg-surface p-12 hover:bg-surface-container-low transition-colors group border-b-[6px] border-secondary">
               <span className="material-symbols-outlined text-5xl text-secondary mb-6 group-hover:scale-110 transition-transform">speed</span>
               <h3 className="text-3xl antonio font-bold uppercase mb-4">Response Diagnostics</h3>
               <p className="text-on-surface-variant leading-relaxed">
                 Current AI-dispatched retrieval patterns indicate an average response time of <strong className="text-black">14.2 minutes</strong> per node. Autonomous routing has decreased urban traffic congestion.
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
      </section>
{/* Section 6: Cinematic Banner */}
<section className="relative h-[870px] flex items-center overflow-hidden">
<div className="absolute inset-0">
<div className="w-full h-full bg-surface-container-highest animate-pulse"></div>
<div className="absolute inset-0 bg-black/60 backdrop-brightness-75"></div>
</div>
<div className="relative z-10 px-8 w-full">
<div className="max-w-[1440px] mx-auto">
<h2 className="text-white text-[12vw] antonio font-bold uppercase leading-[0.8] tracking-tighter">
                    FROM WASTE<br/>TO WONDER
                </h2>
<div className="mt-12 flex items-center gap-8">
<div className="h-px flex-grow bg-white/30"></div>
<button className="bg-white text-black px-10 py-5 antonio font-bold uppercase text-lg hover:bg-primary hover:text-white transition-all">
                        Join the Initiative
                    </button>
</div>
</div>
</div>
</section>
{/* Section 7: Categorized Grid */}
<section className="py-32 px-8 bg-surface">
<div className="max-w-[1440px] mx-auto">
<div className="flex justify-between items-baseline mb-16 border-b border-outline-variant pb-8">
<h2 className="text-5xl antonio font-bold uppercase">Sector Coverage</h2>
<span className="text-sm font-bold antonio uppercase opacity-40">Universal Urban Access</span>
</div>
<div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-outline-variant">
<div className="group relative aspect-[4/5] bg-surface-bright overflow-hidden">
<div className="w-full h-full bg-surface-container-highest animate-pulse"></div>
<div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end p-10">
<h3 className="text-white text-4xl antonio font-bold uppercase mb-4">Streets</h3>
<p className="text-white/70 mb-8 max-w-xs">High-traffic arterial corridors managed with precision logistics.</p>
<button className="w-fit border border-white/30 text-white px-6 py-2 antonio font-bold uppercase text-xs hover:bg-white hover:text-black transition-all">Deploy Units</button>
</div>
</div>
<div className="group relative aspect-[4/5] bg-surface-bright overflow-hidden">
<div className="w-full h-full bg-surface-container-highest animate-pulse"></div>
<div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end p-10">
<h3 className="text-white text-4xl antonio font-bold uppercase mb-4">Public Areas</h3>
<p className="text-white/70 mb-8 max-w-xs">Parks and plazas monitored for community well-being.</p>
<button onClick={() => document.getElementById('analytics')?.scrollIntoView({behavior: 'smooth'})} className="w-fit border border-white/30 text-white px-6 py-2 antonio font-bold uppercase text-xs hover:bg-white hover:text-black transition-all">View Analytics</button>
</div>
</div>
<div className="group relative aspect-[4/5] bg-surface-bright overflow-hidden">
<div className="w-full h-full bg-surface-container-highest animate-pulse"></div>
<div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end p-10">
<h3 className="text-white text-4xl antonio font-bold uppercase mb-4">Residential</h3>
<p className="text-white/70 mb-8 max-w-xs">Smart collection routes for high-density living zones.</p>
<button className="w-fit border border-white/30 text-white px-6 py-2 antonio font-bold uppercase text-xs hover:bg-white hover:text-black transition-all">Connect Hub</button>
</div>
</div>
</div>
</div>
</section>
</main>
{/* Footer Component */}
<footer className="bg-stone-100 dark:bg-stone-900 border-t border-black/5">
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 px-12 py-24 max-w-[1440px] mx-auto">
<div className="col-span-1 lg:col-span-1">
<div className="text-xl font-bold tracking-tighter uppercase text-black dark:text-white antonio mb-8">
                STRATA GARBAGE
            </div>
<p className="text-black/60 dark:text-white/40 text-sm max-w-xs leading-relaxed">
                Developing the next generation of civic infrastructure through neural-mapped sanitation networks.
            </p>
</div>
<div className="flex flex-col gap-4">
<h5 className="text-[10px] font-bold uppercase antonio tracking-widest text-primary mb-4">Core Systems</h5>
<a className="text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors text-sm" href="/#">Infrastructure</a>
<a className="text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors text-sm" href="/#">Real-time Data</a>
<a className="text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors text-sm" href="/#">API Docs</a>
</div>
<div className="flex flex-col gap-4">
<h5 className="text-[10px] font-bold uppercase antonio tracking-widest text-primary mb-4">Impact Layer</h5>
<a className="text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors text-sm" href="/#">Environmental Impact</a>
<a className="text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors text-sm" href="/#">System Status</a>
<a className="text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors text-sm" href="/#">Privacy Policy</a>
</div>
<div className="flex flex-col gap-6">
<h5 className="text-[10px] font-bold uppercase antonio tracking-widest text-primary mb-4">Command Terminal</h5>
<div className="relative group">
<input className="bg-transparent border-b border-black/10 dark:border-white/10 w-full py-2 text-xs focus:ring-0 focus:border-primary outline-none transition-all uppercase antonio" placeholder="NETWORK UPDATES" type="email"/>
<button className="absolute right-0 top-1/2 -translate-y-1/2">
<span className="material-symbols-outlined text-sm">arrow_forward</span>
</button>
</div>
</div>
</div>
<div className="px-12 py-8 border-t border-black/5 flex flex-col md:flex-row justify-between items-center gap-4">
<p className="text-[10px] font-bold uppercase antonio tracking-[0.2em] text-black/40 dark:text-white/40">
            © 2024 STRATA GARBAGE. HIGH-PERFORMANCE CIVIC INFRASTRUCTURE.
        </p>
<div className="flex gap-8">
<span className="text-[10px] font-bold uppercase antonio tracking-widest opacity-30">Status: Operational</span>
<span className="text-[10px] font-bold uppercase antonio tracking-widest opacity-30">Network: Global-Core</span>
</div>
</div>
</footer>
    </div>
  );
}
