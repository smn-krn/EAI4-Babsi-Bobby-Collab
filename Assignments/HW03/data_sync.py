from __future__ import annotations

import subprocess
from pathlib import Path


def sync_from_pi(remote: str, local_dir: Path, delete: bool = False) -> None:
    """
    Sync recordings from Raspberry Pi using rsync to use them locally

    remote: kit-18@10.42.0.1:/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW03/recordings_clean/ ./recordings_clean/
    local_dir: recordings_clean/
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