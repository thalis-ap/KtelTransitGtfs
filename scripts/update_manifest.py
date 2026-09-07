import json
import os
import hashlib
from pathlib import Path

MANIFEST_PATH = "manifest.json"
REGIONS_DIR = "regions"

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def bump_version(version):
    parts = version.split('.')
    if len(parts) >= 3:
        parts[2] = str(int(parts[2]) + 1)
    else:
        parts = ['0', '0', '1']
    return '.'.join(parts)

def main():
    # Load existing manifest
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        print(f"Loaded manifest version: {manifest.get('version')}")
    else:
        manifest = {"version": "0.0.0", "regions": {}}
        print("No manifest found, creating new one")

    changed = False
    regions_dir = Path(REGIONS_DIR)

    if not regions_dir.exists():
        print("No regions folder found")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("changed=false\n")
        return

    # Iterate over each region directory
    for region_dir in regions_dir.iterdir():
        if not region_dir.is_dir():
            continue
        region_id = region_dir.name
        zip_file = region_dir / "gtfs.zip"
        if not zip_file.exists():
            print(f"Warning: {region_id} has no gtfs.zip, skipping")
            continue

        # Compute hash and size
        hash_val = compute_sha256(zip_file)
        size = zip_file.stat().st_size
        print(f"Region {region_id}: hash={hash_val[:8]}, size={size}")

        if region_id not in manifest["regions"]:
            # New region
            manifest["regions"][region_id] = {
                "name": region_id.capitalize(),
                "englishName": region_id.capitalize(),
                "center": [0.0, 0.0],
                "defaultZoom": 10.0,
                "hash": hash_val,
                "size": size
            }
            changed = True
            print(f"  New region added: {region_id}")
        else:
            entry = manifest["regions"][region_id]
            old_hash = entry.get("hash")
            old_size = entry.get("size")
            if old_hash != hash_val or old_size != size:
                entry["hash"] = hash_val
                entry["size"] = size
                changed = True
                print(f"  Region {region_id} updated: hash changed? {old_hash != hash_val}, size changed? {old_size != size}")
            else:
                print(f"  Region {region_id} unchanged")

    if changed:
        manifest["version"] = bump_version(manifest["version"])
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Version bumped to {manifest['version']}")
    else:
        print("No changes detected")

    # Set output for GitHub Actions
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"changed={'true' if changed else 'false'}\n")

if __name__ == "__main__":
    main()