import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import supabase from "./supabaseClient";

// Fix default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

function Authority() {
  const [reports, setReports] = useState([]);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(null);
  const BASE_URL = "https://strata-garbage-backend.onrender.com";

  // 🔐 GET SESSION TOKEN & LISTEN TO CHANGES
  useEffect(() => {
    const fetchSession = async () => {
      const { data } = await supabase.auth.getSession();
      if (data?.session?.access_token) {
        setToken(data.session.access_token);
        console.log("TOKEN:", data.session.access_token);
      }
    };

    fetchSession();

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (session?.access_token) {
          setToken(session.access_token);
          console.log("TOKEN UPDATED:", session.access_token);
        } else {
          setToken(null);
        }
      }
    );

    return () => listener.subscription.unsubscribe();
  }, []);

  // 🔄 FETCH REPORTS
  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await fetch(`${BASE_URL}/reports/`);
        const data = await res.json();
        const reportsArray = Array.isArray(data) ? data : data.reports || [];
        setReports(reportsArray);
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      }
    };

    fetchReports();
  }, []);

  // 🚀 OPTIMIZE ROUTE
  const handleOptimize = async () => {
    if (!token) {
      alert("Authentication required. Please log in.");
      console.error("No auth token");
      return;
    }

    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/optimize-route/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        console.error("Optimize route error:", errData);
        alert(
          errData.detail || "Failed to optimize route. Check console for details."
        );
        setLoading(false);
        return;
      }

      const data = await res.json();
      console.log("Route:", data);
      setRoute(data);
      setLoading(false);
    } catch (err) {
      console.error("Optimize route failed:", err);
      alert("Failed to optimize route. Check console for details.");
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
            Logistics
            <br />
            Command Core
          </h2>
        </div>

        {/* Action Panel */}
        <div className="bg-surface-container-low p-8 md:p-12 mb-16 border-l-[6px] border-secondary relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-secondary/5 to-transparent z-0 pointer-events-none"></div>
          <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-8">
            <div className="max-w-xl">
              <h3 className="text-3xl antonio font-bold uppercase mb-4 text-on-surface">
                Route Optimization Matrix
              </h3>
              <p className="text-on-surface-variant font-medium leading-relaxed">
                Compute the most efficient metropolitan collection pathing using
                high-fidelity spatial telemetry from active civic nodes.
              </p>
            </div>
            <button
              className="bg-black text-white px-10 py-5 antonio font-bold uppercase text-lg hover:bg-secondary hover:text-white transition-all w-full md:w-auto active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3 border-none"
              onClick={handleOptimize}
              disabled={loading || !token}
              style={{ borderRadius: "0" }}
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined text-xl animate-spin">
                    sync
                  </span>{" "}
                  PROCESSING VECTOR...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-xl">route</span>{" "}
                  INITIALIZE PATH
                </>
              )}
            </button>
          </div>
        </div>

        {/* MAP */}
        {route?.path && (
          <div className="mb-24 space-y-8">
            <MapContainer
              center={route?.path?.[0] || [13.08, 80.27]}
              zoom={11}
              style={{ height: "480px", borderRadius: "12px", width: "100%" }}
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {route.path.length > 1 && <Polyline positions={route.path} />}
              {route.path.map((coord, index) => (
                <Marker key={index} position={coord}>
                  <Popup>Stop {index + 1}</Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}

        {/* REPORTS */}
        <div className="mt-6">
          <h2>Reports ({reports.length})</h2>
          {reports.map((r) => (
            <div key={r.id}>
              {r.lat}, {r.lng} - {r.garbage_level}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Authority;