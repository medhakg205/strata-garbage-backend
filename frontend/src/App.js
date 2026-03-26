import React, { useState } from "react";
import Authority from "./Authority";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState(null);

  const handleUpload = () => {
    if (!file) {
      alert("Please upload an image");
      return;
    }

    setLoading(true);

    // simulate AI delay
    setTimeout(() => {
      setResult(2);
      setLoading(false);
    }, 1500);
  };
  const getLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        });
      },
      () => {
        alert("Location access denied");
      }
    );
  };

  return (
    <>
    {/*}
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "100vh",
      background: "#506944",
      fontFamily: "Arial"
    }}>

      <div style={{
        background: "#9bb48e",
        padding: "35px",
        borderRadius: "20px",
        boxShadow: "0 15px 40px rgba(0,0,0,0.2)",
        textAlign: "center",
        width: "360px"
      }}>

        <h2 style={{ marginBottom: "10px" }}>
          🚮 Smart Waste Detection
        </h2>

        <p style={{ color: "gray", fontSize: "14px" }}>
          Upload an image to detect garbage level
        </p>

        <br />

        <input
          type="file"
          onChange={(e) => {
            setFile(e.target.files[0]);
            setResult(null);
          }}
        />

        <br /><br />

        {file && (
          <img
            src={URL.createObjectURL(file)}
            alt="preview"
            width="220"
            style={{
              borderRadius: "12px",
              boxShadow: "0 5px 15px rgba(0,0,0,0.2)"
            }}
          />
        )}

        <br /><br />

        <button onClick={getLocation}>
          📍 Get Location
        </button>

        <br /><br />

        {location && (
          <p>
            Location: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
          </p>
        )}
        <br />

        <button
          onClick={handleUpload}
          style={{
            padding: "12px 25px",
            border: "none",
            borderRadius: "10px",
            background: "linear-gradient(to right, #667eea, #764ba2)",
            color: "white",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "0.3s"
          }}
        >
          Submit Complaint
        </button>

        <br /><br />

        {loading && <p style={{ color: "#555" }}>Analyzing image... 🤖</p>}

        {result !== null && !loading && (
          <h3
            style={{ color: "green" }}>
            Complaint submitted successfully ✅
          </h3>
        )}

      </div>
    </div>
    */}
    <Authority />;
    </>
  );
}

export default App;