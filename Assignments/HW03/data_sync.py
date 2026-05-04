from __future__ import annotations

import subprocess
from pathlib import Path


def sync_from_pi(remote: str, local_dir: Path, delete: bool = False) -> None:
    """
    Sync recordings from Raspberry Pi using rsync to use locally.

    remote: e.g. "pi@192.168.1.42:/home/pi/recordings/"
    local_dir: local destination directory
    delete: if True, mirror exactly (removes local files not on remote)
    """
    local_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "rsync",
        "-avz",
    ]

    if delete:
        cmd.append("--delete")

    cmd.extend([remote, str(local_dir)])

    print(f"[sync] {remote} -> {local_dir}")
    subprocess.run(cmd, check=True)