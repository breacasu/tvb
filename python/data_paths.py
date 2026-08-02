#!/usr/bin/env python3
"""Resolve shared and local runtime data locations."""

import os
from pathlib import Path


def shared_data_candidates():
    home = Path.home()
    return (
        home / "SynologyDrive" / "SharedRepoDocuments" / "tvb",
        home / "Synology Drive" / "SharedRepoDocuments" / "tvb",
    )


def resolve_data_dir() -> Path:
    configured = os.environ.get("TVB_DATA_DIR")
    if configured:
        return Path(configured).expanduser()

    for candidate in shared_data_candidates():
        if candidate.is_dir():
            return candidate

    return Path.cwd()
