import re

with open('tmp_screen1.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract from <nav to </footer>
start = html.find('<nav class="fixed')
end = html.find('</footer>') + len('</footer>')
fragment = html[start:end]

# Replacements for React JSX
fragment = fragment.replace('class=', 'className=')
fragment = fragment.replace('for=', 'htmlFor=')
fragment = fragment.replace('tabindex=', 'tabIndex=')
fragment = fragment.replace('rows="3"', 'rows={3}')

# Self-closing tags
fragment = re.sub(r'<img([^>]+?)(?<!/)>', r'<img\1/>', fragment)
fragment = re.sub(r'<input([^>]+?)(?<!/)>', r'<input\1/>', fragment)
fragment = fragment.replace('<!--', '{/*').replace('-->', '*/}')

# Inject Dropzone UI
dropzone_html = """
<div {...getRootProps()} className={`border-2 border-dashed h-80 flex flex-col items-center justify-center text-center p-8 mb-8 hover:border-primary transition-colors cursor-pointer ${isDragActive ? 'border-primary bg-primary-fixed-dim/20' : 'border-outline-variant bg-surface-bright'}`}>
<input {...getInputProps()} />
<span className="material-symbols-outlined text-6xl text-outline mb-4">{isDragActive ? 'download' : 'cloud_upload'}</span>
<h3 className="antonio font-bold uppercase text-2xl">{file ? file.name : 'Upload Visual Data'}</h3>
<p className="text-sm text-on-surface-variant mt-2">Drag and drop high-resolution imagery or select file</p>
</div>
"""
fragment = re.sub(r'<div className="border-2 border-dashed.*?</div>', dropzone_html, fragment, flags=re.DOTALL)

# Inject Form UI and Handlers
form_html = """
<form className="space-y-8" onSubmit={handleUpload}>
<div>
  <label className="block text-[10px] antonio font-bold uppercase text-primary mb-2">Location Context (Auto-Fetched Data)</label>
  <div className="flex gap-4">
    <input value={location ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` : ''} readOnly className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary px-4 py-4 focus:ring-0 transition-all outline-none" placeholder="Detecting current coordinates..." type="text"/>
    <button type="button" onClick={getLocation} className="px-6 bg-surface-container-highest border-b-2 border-outline-variant hover:border-primary uppercase text-xs font-bold antonio">SYNC GPS</button>
  </div>
</div>
<div>
  <label className="block text-[10px] antonio font-bold uppercase text-primary mb-2">Report Description</label>
  <textarea className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary px-4 py-4 focus:ring-0 transition-all outline-none" placeholder="Additional metadata for waste classification..." rows={3}></textarea>
</div>
<button type="submit" disabled={loading} className="w-full bg-black text-white py-6 antonio font-bold uppercase text-xl hover:bg-primary transition-all active:scale-95 disabled:opacity-50">
  {loading ? "Processing AI Analysis..." : "Submit to Strata Network"}
</button>
</form>
"""
fragment = re.sub(r'<form className="space-y-8">.*?</form>', form_html, fragment, flags=re.DOTALL)

# Hook up navigation and dynamic data
fragment = fragment.replace('1,482', '{reportCount}')
fragment = fragment.replace(
    '<button className="px-6 py-2 border border-black/10 dark:border-white/10 antonio uppercase text-xs font-bold hover:bg-black hover:text-white transition-all active:scale-95">\n                    Dashboard\n                </button>', 
    '<button onClick={() => onNavigate("authority")} className="px-6 py-2 border border-black/10 dark:border-white/10 antonio uppercase text-xs font-bold hover:bg-black hover:text-white transition-all active:scale-95">\n                    Dashboard\n                </button>'
)
# Scroll jump for Report waste button in Nav
fragment = fragment.replace(
    '<button className="px-6 py-2 bg-primary text-on-primary antonio uppercase text-xs font-bold hover:bg-primary-container transition-all active:scale-95">\n                    Report Waste\n                </button>',
    '<button onClick={() => window.scrollTo({top: window.innerHeight * 8, behavior: "smooth"})} className="px-6 py-2 bg-primary text-on-primary antonio uppercase text-xs font-bold hover:bg-primary-container transition-all active:scale-95">\n                    Report Waste\n                </button>'
)

final_code = f"""import React, {{ useEffect, useState, useCallback }} from 'react';
import {{ gsap }} from 'gsap';
import {{ ScrollTrigger }} from 'gsap/ScrollTrigger';
import {{ useDropzone }} from 'react-dropzone';
import toast from 'react-hot-toast';

gsap.registerPlugin(ScrollTrigger);

export default function LandingPage({{ onNavigate }}) {{
  const [file, setFile] = useState(null);
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Realtime Analytics States
  const [reportCount, setReportCount] = useState(0);

  const BASE_URL = "https://strata-garbage-backend.onrender.com";

  const onDrop = useCallback(acceptedFiles => {{
    if (acceptedFiles && acceptedFiles.length > 0) {{
      setFile(acceptedFiles[0]);
      toast.success("Image selected successfully!");
    }}
  }}, []);

  const {{ getRootProps, getInputProps, isDragActive }} = useDropzone({{ 
    onDrop,
    accept: {{ 'image/*': [] }},
    multiple: false 
  }});

  const getLocation = (e) => {{
    e.preventDefault();
    const locToast = toast.loading("Fetching GPS coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {{
        setLocation({{ lat: pos.coords.latitude, lng: pos.coords.longitude }});
        toast.success("Location Synced! 📍", {{ id: locToast }});
      }},
      () => toast.error("Location access denied or failed.", {{ id: locToast }})
    );
  }};

  const handleUpload = async (e) => {{
    e.preventDefault();
    if (!file || !location) {{
      toast.error("Please provide both an image and your location.");
      return;
    }}
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lat", location.lat);
    formData.append("lng", location.lng);

    const uploadToast = toast.loading("Analyzing image with AI...");
    try {{
      setLoading(true);
      // NOTE: Temporarily use relative local if no proxy, but BASE_URL is explicit here
      const res = await fetch(`${{BASE_URL}}/reports/`, {{
        method: "POST",
        body: formData,
      }});
      const data = await res.json();
      setLoading(false);

      if (data.level) {{
        toast.success(`Report submitted! Priority: ${{data.level.toUpperCase()}}`, {{ id: uploadToast, duration: 5000 }});
        setFile(null);
        setLocation(null);
      }} else if (data.message === "Not garbage ❌") {{
        toast.error("AI determined this is not garbage. Rejected.", {{ id: uploadToast, duration: 4000 }});
      }} else {{
        toast.success("Report submitted successfully!", {{ id: uploadToast }});
        setFile(null);
        setLocation(null);
      }}
    }} catch (err) {{
      console.error(err);
      setLoading(false);
      toast.error("Network error. Upload failed.", {{ id: uploadToast }});
    }}
  }};

  useEffect(() => {{
    // Simulating fetching active reports
    fetch(`${{BASE_URL}}/reports/`)
      .then(r => r.json())
      .then(data => {{
         if(Array.isArray(data)) setReportCount(data.length); 
      }}).catch(e => console.error(e));
  }}, []);

  useEffect(() => {{
    const mainCanvas = document.getElementById('waste-canvas');
    if(!mainCanvas) return;
    const ambientCanvas = document.getElementById('ambient-canvas');
    const mainCtx = mainCanvas.getContext('2d');
    const ambientCtx = ambientCanvas.getContext('2d');

    const frameImages = [
      '/frames/anim_1.jpg',
      '/frames/anim_2.jpg',
      '/frames/anim_3.jpg',
      '/frames/anim_4.jpg'
    ];
    const frameCount = frameImages.length;
    
    const images = [];
    const sequence = {{ frame: 0 }};

    frameImages.forEach((src) => {{
      const img = new Image();
      img.src = src;
      images.push(img);
    }});

    function resizeCanvases() {{
      const sc = document.getElementById('scrolly-container');
      if(!sc) return;
      mainCanvas.width = window.innerWidth;
      mainCanvas.height = window.innerHeight;
      ambientCanvas.width = window.innerWidth;
      ambientCanvas.height = window.innerHeight;
      render();
    }}

    function render() {{
      if(!mainCtx || !ambientCtx) return;
      mainCtx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
      ambientCtx.clearRect(0, 0, ambientCanvas.width, ambientCanvas.height);

      const frameIndex = Math.floor(sequence.frame);
      const img1 = images[frameIndex];
      const img2 = images[Math.min(frameIndex + 1, frameCount - 1)];
      const blend = sequence.frame - frameIndex;

      if (!img1 || !img1.complete) return;

      mainCtx.globalAlpha = 1;
      ambientCtx.globalAlpha = 1;

      // Draw Ambient
      const aScale = Math.max(ambientCanvas.width / img1.width, ambientCanvas.height / img1.height);
      const ax = (ambientCanvas.width - img1.width * aScale) / 2;
      const ay = (ambientCanvas.height - img1.height * aScale) / 2;
      ambientCtx.drawImage(img1, ax, ay, img1.width * aScale, img1.height * aScale);

      // Draw Main
      const mScale = Math.min((mainCanvas.width * 0.9) / img1.width, (mainCanvas.height * 0.8) / img1.height);
      const mx = (mainCanvas.width - img1.width * mScale) / 2;
      const my = (mainCanvas.height - img1.height * mScale) / 2;
      mainCtx.drawImage(img1, mx, my, img1.width * mScale, img1.height * mScale);

      if (blend > 0 && img2 && img2.complete) {{
          mainCtx.globalAlpha = blend;
          ambientCtx.globalAlpha = blend;
          ambientCtx.drawImage(img2, ax, ay, img2.width * aScale, img2.height * aScale);
          mainCtx.drawImage(img2, mx, my, img2.width * mScale, img2.height * mScale);
      }}
    }}

    let trigger1 = gsap.to(sequence, {{
        frame: frameCount - 1,
        snap: "frame",
        ease: "none",
        scrollTrigger: {{
            trigger: "#scrolly-container",
            start: "top top",
            end: "bottom bottom",
            scrub: 0.5,
        }},
        onUpdate: render
    }});

    let trigger2 = gsap.to(".scrolly-overlay", {{
        opacity: 0,
        y: -100,
        scrollTrigger: {{
            trigger: "#scrolly-container",
            start: "10% top",
            end: "30% top",
            scrub: true
        }}
    }});

    window.addEventListener('resize', resizeCanvases);
    setTimeout(resizeCanvases, 500);
    // Initial loop
    const id = setInterval(render, 100);
    setTimeout(() => clearInterval(id), 2000);

    return () => {{
      if(trigger1.scrollTrigger) trigger1.scrollTrigger.kill();
      if(trigger2.scrollTrigger) trigger2.scrollTrigger.kill();
      window.removeEventListener('resize', resizeCanvases);
    }};
  }}, []);

  return (
    <div className="bg-surface text-on-surface archivo selection:bg-primary selection:text-white">
{fragment}
    </div>
  );
}}
"""

with open('frontend/src/LandingPage.js', 'w', encoding='utf-8') as f:
    f.write(final_code)
