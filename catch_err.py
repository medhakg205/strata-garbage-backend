import subprocess

result = subprocess.run(["npm", "run", "build"], capture_output=True, text=True, cwd="frontend", shell=True)

with open('frontend/full_err.txt', 'w', encoding='utf-8') as f:
    f.write(result.stdout)
    f.write("\n--STDERR--\n")
    f.write(result.stderr)
