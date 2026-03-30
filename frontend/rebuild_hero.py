import re

# 1. Update index.css to remove GSAP Specific styles
with open('src/index.css', 'r', encoding='utf-8') as f:
    css = f.read()

css = re.sub(r'/\* Scrollytelling Custom Styles \*/.*?/\* -------------------------------', '/* -------------------------------', css, flags=re.DOTALL)

with open('src/index.css', 'w', encoding='utf-8') as f:
    f.write(css)

# 2. Update LandingPage.js
with open('src/LandingPage.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Remove GSAP imports
js = js.replace("import { gsap } from 'gsap';\nimport { ScrollTrigger } from 'gsap/ScrollTrigger';", "")
js = js.replace("gsap.registerPlugin(ScrollTrigger);\n", "")

# Remove the huge useEffect for Canvas
js = re.sub(r'  useEffect\(\(\) => \{\n    const mainCanvas = document\.getElementById.*?  \}, \[\]\);\n', '', js, flags=re.DOTALL)

# Build a clean static hero replacement
hero_static = """{/* Section 1: Static Hero Container */}
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
        <button onClick={() => window.scrollTo({top: window.innerHeight * 2, behavior: "smooth"})} className="border border-outline-variant bg-surface/80 text-on-surface px-12 py-5 text-xl antonio uppercase font-bold hover:bg-surface-container transition-colors w-full md:w-auto backdrop-blur-md hover:scale-105 active:scale-95 duration-300">
            View Analytics
        </button>
    </div>
  </div>
</div>"""

# Replace the specific old scrolly container
js = re.sub(r'\{/\* Section 1: Scrollytelling Hero Container \*/\}.*?(?=\{/\* Section 2: Report Waste)', hero_static + '\n', js, flags=re.DOTALL)

# Strip out external placeholder images in other sections that user might mistake as the "garbage pictures"
js = re.sub(r'<img [^>]*src="https://lh3.googleusercontent.com/aida-public/[^>]*/>', '<div className="w-full h-full bg-surface-container-highest animate-pulse"></div>', js)

with open('src/LandingPage.js', 'w', encoding='utf-8') as f:
    f.write(js)
