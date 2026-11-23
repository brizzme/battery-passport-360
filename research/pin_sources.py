"""Write research/calibration.sha256 from the Mendeley public API (checksums published by the host).

Line format: <sha256> <bytes> <local relative path> <url>
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://data.mendeley.com/public-api/datasets/yz4pttm73n"
UA = {"User-Agent": "Mozilla/5.0 (research-client)"}
HUST = ("071d24617153693b0d29059568525e620f6af6512acc9d00c98c7adcf15125db 1188136932 hust/our_data.zip "
        "https://data.mendeley.com/public-files/datasets/nsc7hnsg4s/files/5ca0ac3e-d598-4d07-8dcb-879aa047e98b/file_downloaded")
AGEING_ROUND = "Round10"


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))


def main():
    folders = get(API + "/folders/2")
    byid = {f["id"]: f for f in folders}
    lines = [HUST]
    for folder in sorted(folders, key=lambda f: (byid.get(f.get("parent_id"), {}).get("name", ""), f["name"])):
        cell = byid.get(folder.get("parent_id"), {}).get("name")
        if not cell or not folder["name"].startswith("Round"):
            continue
        for item in get(f"{API}/files?folder_id={folder['id']}&version=2"):
            name = item["filename"]
            if name == "RPT.csv" or (name == "Ageing.csv" and folder["name"] == AGEING_ROUND):
                d = item["content_details"]
                lines.append(f"{d['sha256_hash']} {d['size']} aalborg/{cell}/{folder['name']}/{name} {d['download_url']}")
    (ROOT / "research/calibration.sha256").write_text("\n".join(lines) + "\n")
    print(len(lines) - 1, "files pinned")


if __name__ == "__main__":
    main()
