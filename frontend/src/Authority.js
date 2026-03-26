import React, { useEffect, useState } from "react";

function Authority() {
  const [reports, setReports] = useState([]);

  useEffect(() => {
  fetch("http://localhost:8000/reports")
    .then((res) => res.json())
    .then((data) => {
      console.log(data); // just to see data
      setReports(data);
    })
    .catch((err) => console.error(err));
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>🚛 Authority Dashboard</h2>

      <iframe
        width="100%"
        height="400"
        style={{ border: "0", borderRadius: "10px" }}
        loading="lazy"
        src="https://www.openstreetmap.org/export/embed.html?bbox=77.19%2C28.59%2C77.23%2C28.63&layer=mapnik"
      ></iframe>

      {reports.map((item) => (
        <div key={item.id} style={{
          background: "white",
          padding: "10px",
          marginTop: "10px",
          borderRadius: "8px"
        }}>
          <p><b>Location:</b> {item.lat}, {item.lng}</p>
          <p>
            <b>Priority:</b>{" "}
            <span style={{
                padding: "5px 10px",
                borderRadius: "8px",
                color: "white",
                backgroundColor:
                    item.level === "High" ? "#ff4d4f" :
                    item.level === "Medium" ? "#faad14" :
                    "#52c41a"
            }}>
                {item.level}
            </span>
          </p>
        </div>
      ))}

    </div>
  );
}

export default Authority;