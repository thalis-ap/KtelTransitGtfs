import json
import os
import re
import hashlib
from pathlib import Path

MANIFEST_PATH = "manifest.json"
REGIONS_DIR = "regions"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def bump_version(version: str) -> str:
    """Increment the patch version: 1.0.1 -> 1.0.2"""
    parts = version.split('.')
    if len(parts) >= 3:
        parts[2] = str(int(parts[2]) + 1)
    else:
        # fallback: treat as 0.0.0
        parts = ['0', '0', '1']
    return '.'.join(parts)

def main():
    # Load existing manifest if it exists
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "version": "0.0.0",
            "regions": {}
        }

    changed = False

    # Iterate over each region directory
    regions_dir = Path(REGIONS_DIR)
    for region_dir in regions_dir.iterdir():
        if not region_dir.is_dir():
            continue
        region_id = region_dir.name
        zip_file = region_dir / "gtfs.zip"
        if not zip_file.exists():
            # If region directory exists but no zip, skip
            continue

        # Compute hash and size
        hash_val = compute_sha256(zip_file)
        size = zip_file.stat().st_size

        # Ensure region entry exists
        if region_id not in manifest["regions"]:
            # New region – we need to provide default name/center/zoom
            # You might want to fail or prompt to fill these manually.
            # For automation, we'll leave them as placeholders and print a warning.
            print(f"Warning: region '{region_id}' is new; please add name, englishName, center, defaultZoom manually.")
            # Add minimal entry
            manifest["regions"][region_id] = {
                "name": region_id.capitalize(),
                "englishName": region_id.capitalize(),
                "center": [0.0, 0.0],
                "defaultZoom": 10.0,
                "hash": hash_val,
                "size": size
            }
            changed = True
        else:
            # Update existing entry
            region_entry = manifest["regions"][region_id]
            if region_entry.get("hash") != hash_val or region_entry.get("size") != size:
                region_entry["hash"] = hash_val
                region_entry["size"] = size
                changed = True

    # If any changes, bump version
    if changed:
        manifest["version"] = bump_version(manifest["version"])

        # Write updated manifest
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)
        # Set output for GitHub Actions
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("changed=true\n")
        print(f"Manifest updated to version {manifest['version']}")
    else:
        print("No changes detected.")

if __name__ == "__main__":
    main()