"""Download the Jigsaw Toxic Comment Classification dataset from Hugging Face."""

import os
import urllib.request
import ssl

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset", "raw")
BASE_URL = (
    "https://huggingface.co/datasets/thesofakillers/"
    "jigsaw-toxic-comment-classification-challenge/resolve/main/"
)
FILES = ["train.csv", "test.csv", "test_labels.csv"]


def download() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    ssl._create_default_https_context = ssl._create_unverified_context
    for name in FILES:
        dest = os.path.join(RAW_DIR, name)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            print(f"Already present: {dest}")
            continue
        url = BASE_URL + name
        print(f"Downloading {name} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as response, open(dest, "wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        print(f"  saved {dest} ({os.path.getsize(dest)} bytes)")


if __name__ == "__main__":
    download()
