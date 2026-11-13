# usage: python3 check_setup.py [--install]
# Checks every tool market-motion needs. With --install it installs what is missing:
#   macOS: Homebrew packages (ffmpeg, node, whisper-cpp)   Linux: apt/dnf packages + whisper.cpp built from source
# and downloads the Whisper model (~550 MB). Then it warms up Hyperframes (the renderer downloads itself via npx).
import os, platform, shutil, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools  # noqa: E402

SYS = platform.system()
INSTALL = "--install" in sys.argv
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin"


def sh(c, **kw):
    print("  $ " + " ".join(c))
    return subprocess.run(c, **kw)


def ver(cmd):
    p = tools.find(cmd[0])
    if not p:
        return None
    try:
        r = subprocess.run([p] + cmd[1:], capture_output=True, text=True, timeout=60)
        return ((r.stdout or r.stderr).strip().splitlines() or ["?"])[0][:60]
    except Exception:
        return None


def status():
    node = ver(["node", "--version"])
    rows = [("Python 3.9+", sys.version_info >= (3, 9), sys.version.split()[0]),
            ("ffmpeg + ffprobe", bool(tools.find("ffmpeg") and tools.find("ffprobe")), ver(["ffmpeg", "-version"])),
            ("Node.js 18+ (npx)", bool(node) and int(node.lstrip("v").split(".")[0]) >= 18 and bool(tools.find("npx")), node),
            ("whisper-cli (whisper.cpp)", bool(tools.find("whisper-cli", [os.path.join(tools.TOOLS_DIR, "whisper.cpp", "build", "bin")])), None),
            ("Whisper model large-v3-turbo", os.path.exists(tools.MODEL), tools.MODEL)]
    return rows


def show(rows):
    for n, ok, info in rows:
        print(f"{'OK     ' if ok else 'MISSING'}  {n:30} {info or ''}")
    return [n for n, ok, _ in rows if not ok]


def install_mac(missing):
    if not shutil.which("brew"):
        sys.exit("Homebrew is needed on macOS. Install it from https://brew.sh (one command, asks for your password), then run this again.")
    pk = {"ffmpeg + ffprobe": "ffmpeg", "Node.js 18+ (npx)": "node", "whisper-cli (whisper.cpp)": "whisper-cpp"}
    todo = [pk[n] for n in missing if n in pk]
    if todo:
        sh(["brew", "install", *todo])


def install_linux(missing):
    pm = "apt-get" if shutil.which("apt-get") else ("dnf" if shutil.which("dnf") else None)
    sudo = [] if os.geteuid() == 0 else ["sudo"]
    pk = []
    if "ffmpeg + ffprobe" in missing:
        pk.append("ffmpeg")
    if "Node.js 18+ (npx)" in missing:
        pk += ["nodejs", "npm"]
    if "whisper-cli (whisper.cpp)" in missing:
        pk += ["git", "cmake", "build-essential" if pm == "apt-get" else "gcc-c++"]
    if pk:
        if not pm:
            sys.exit("Install these with your package manager, then run again: " + " ".join(pk))
        if pm == "apt-get":
            sh(sudo + ["apt-get", "update"])
        sh(sudo + [pm, "install", "-y", *pk])
    if "whisper-cli (whisper.cpp)" in missing:
        d = os.path.join(tools.TOOLS_DIR, "whisper.cpp")
        os.makedirs(tools.TOOLS_DIR, exist_ok=True)
        if not os.path.exists(d):
            sh(["git", "clone", "--depth", "1", "https://github.com/ggml-org/whisper.cpp", d], check=True)
        sh(["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=Release"], cwd=d, check=True)
        sh(["cmake", "--build", "build", "-j", "--config", "Release"], cwd=d, check=True)
    node = ver(["node", "--version"])
    if node and int(node.lstrip("v").split(".")[0]) < 18:
        print("Your distro's Node.js is older than 18. Install a newer one from https://nodejs.org (or nvm), then run again.")


def main():
    print("market-motion setup check\n")
    missing = show(status())
    if missing and INSTALL:
        print("\ninstalling: " + ", ".join(missing))
        if SYS == "Darwin":
            install_mac(missing)
        elif SYS == "Linux":
            install_linux(missing)
        else:
            sys.exit("Windows: run this inside WSL (Ubuntu), or install ffmpeg, Node.js 18+ and whisper.cpp by hand.")
        if not os.path.exists(tools.MODEL):
            os.makedirs(os.path.dirname(tools.MODEL), exist_ok=True)
            print(f"downloading the Whisper model to {tools.MODEL} (~550 MB) ...")
            urllib.request.urlretrieve(MODEL_URL, tools.MODEL + ".part")
            os.replace(tools.MODEL + ".part", tools.MODEL)
        import importlib
        importlib.reload(tools)
        print()
        missing = show(status())
    if not missing and INSTALL:
        print("\nwarming up Hyperframes (first run downloads the renderer and its browser) ...")
        sh([tools.find("npx") or "npx", "--yes", "hyperframes@0.9.7", "--version"])
    if missing:
        print("\nStill missing: " + ", ".join(missing) + ("" if INSTALL else "\nRun with --install to install them."))
        sys.exit(1)
    print("\nAll set. In Claude Code, share a raw video or voiceover and say: \"edit this in market motion style\".")


if __name__ == "__main__":
    main()
