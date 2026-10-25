from __future__ import annotations
import asyncio, csv, os, re, signal, socket, time
from dataclasses import dataclass
from pathlib import Path
import psutil


@dataclass
class Result:
    stdout: str = ""
    error: str = ""
    code: int = 0


async def run(*argv: str, timeout: float = 8, c_locale: bool = False) -> Result:
    """Subprocesses never block the UI; timeouts also terminate shell children."""
    env = os.environ.copy()
    if c_locale:
        env["LC_ALL"] = "C"
    try:
        proc = await asyncio.create_subprocess_exec(*argv, stdout=asyncio.subprocess.PIPE,
                   stderr=asyncio.subprocess.PIPE, env=env, start_new_session=True)
    except OSError as exc:
        return Result(error=f"{argv[0]}: {exc.strerror}", code=127)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        return Result(stdout.decode(errors="replace"), stderr.decode(errors="replace").strip(), proc.returncode or 0)
    except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await proc.communicate()
        if isinstance(exc, asyncio.CancelledError):
            raise
        return Result(error=f"{argv[0]} timed out after {timeout:g}s", code=124)


def read_text(path: Path) -> str:
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return ""


def uptime_seconds() -> float:
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return max(0, time.time() - psutil.boot_time())


def duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 86400}d {seconds % 86400 // 3600:02d}h {seconds % 3600 // 60:02d}m {seconds % 60:02d}s"


def gib(value: float) -> str:
    return f"{value / 2**30:.1f} GiB"


def rate(value: float) -> str:
    value = max(0, value)
    for unit in ("B/s", "KiB/s", "MiB/s", "GiB/s"):
        if value < 1024 or unit == "GiB/s":
            return f"{value:.1f} {unit}"
        value /= 1024
    return "0 B/s"


def parse_tuptime(output: str) -> int | None:
    # -s emits seconds, usually after a percentage and '='. Never treat the
    # percentage or a human-readable duration as the accumulated seconds.
    match = re.search(
        r"^[ \t]*System uptime:[ \t]*(?:[\d.]+%[ \t]*=[ \t]*)?"
        r"([\d,]+)(?:\.\d+)?[ \t]*(?:seconds?|s)?[ \t]*$",
        output, re.M,
    )
    return int(match[1].replace(",", "")) if match else None


def cpu_temperature() -> str:
    try:
        sensors = psutil.sensors_temperatures()
    except (OSError, AttributeError):
        return "temperature unavailable"
    for group in ("k10temp", "zenpower", "coretemp", "cpu_thermal"):
        entries = sensors.get(group, [])
        preferred = [x for x in entries if x.label.lower() in ("tctl", "tdie", "package id 0", "cpu")]
        if preferred or entries:
            return f"{(preferred or entries)[0].current:.0f}°C"
    return "temperature unavailable"


def local_ips() -> list[str]:
    values = []
    try:
        interfaces = psutil.net_if_addrs()
    except OSError:
        return ["Interface addresses unavailable"]
    for name, addresses in interfaces.items():
        for addr in addresses:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                values.append(f"{name}: {addr.address}")
    return values or ["No IPv4 connection"]


def default_interfaces() -> list[str]:
    routes = read_text(Path("/proc/net/route")).splitlines()[1:]
    return list(dict.fromkeys(row.split()[0] for row in routes if len(row.split()) > 3
                             and row.split()[1] == "00000000" and int(row.split()[3], 16) & 1))


def amd_gpus() -> tuple[list[str], list[str]]:
    names, values = [], []
    for path in sorted(Path("/sys/class/drm").glob("card[0-9]*/device")):
        if read_text(path / "vendor") != "0x1002":
            continue
        load = read_text(path / "gpu_busy_percent")
        used, total = read_text(path / "mem_info_vram_used"), read_text(path / "mem_info_vram_total")
        temp_files = list(path.glob("hwmon/hwmon*/temp1_input"))
        temp = read_text(temp_files[0]) if temp_files else ""
        bits = [f"{load}%" if load.isdigit() else "load unavailable"]
        if temp.lstrip("-").isdigit():
            bits.append(f"{int(temp) / 1000:.0f}°C")
        if used.isdigit() and total.isdigit():
            bits.append(f"{gib(int(used))} / {gib(int(total))} VRAM")
        names.append(f"AMD ({path.parent.name})")
        values.append(" • ".join(bits))
    return names, values


def parse_nvidia(output: str) -> tuple[list[str], list[str]]:
    names, values = [], []
    for fields in csv.reader(output.splitlines(), skipinitialspace=True):
        if len(fields) != 5:
            continue
        name, load, temp, used, total = (x.strip() for x in fields)
        bits = [f"{load}%" if load.replace(".", "", 1).isdigit() else "load unavailable",
                f"{temp}°C" if temp.replace(".", "", 1).isdigit() else "temperature unavailable"]
        try:
            bits.append(f"{float(used)/1024:.1f} / {float(total)/1024:.1f} GiB VRAM")
        except ValueError:
            pass
        names.append(name)
        values.append(" • ".join(bits))
    return names, values
