import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from glob import glob
from typing import TypedDict

import requests


class Tool(TypedDict):
    url: str
    file_name: str


class Urls(TypedDict):
    linpack: Tool


def fetch_sha256(source: str, target_file_name: str) -> str:
    response = requests.get(source, timeout=5)
    data = response.text.split("\n")

    for line in data:
        hash_value, file_name = line.split()

        if file_name == target_file_name:
            return hash_value

    return ""


def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def extract(
    file_path: str,
    out_path: str | None = None,
    exclude_files: set[str] | None = None,
    force: bool = False,
) -> int:
    args = ["7z", "x", file_path]

    if out_path is not None:
        args.append(f"-o{out_path}")

    if exclude_files is not None:
        args.extend(f"-x!{file}" for file in exclude_files)

    if force:
        args.extend("-y")

    process = subprocess.run(args, check=False)

    if process.returncode != 0:
        return process.returncode

    return 0


def setup_linpack(url: str, file_name: str, binary_destination: str) -> int:
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        print(f"error: {file_name} download error, status_code {response.status_code}")
        return 1

    with open(file_name, "wb") as file:
        file.write(response.content)

    if extract(file_name, force=True) != 0:
        print(f"error: failed to extract {file_name}")
        return 1

    # extract inner file to linpack folder
    if extract("linpack.tar", "linpack", force=True) != 0:
        print("error: failed to extract linpack.tar")
        return 1

    # version name changes in folder name (e.g. "benchmarks_2024.0")
    benchmarks_folder = glob("linpack/benchmarks*")

    if len(benchmarks_folder) != 1:
        print("error: unable to find correct benchmarks folder")
        return 1

    # copy binary to binary_destination
    shutil.copy(
        f"{benchmarks_folder[0]}/linux/share/mkl/benchmarks/linpack/xlinpack_xeon64",
        binary_destination,
    )

    return 0


def patch_linpack(bin_path: str) -> int:
    with open(bin_path, "rb") as file:
        file_bytes = file.read()

    # convert bytes to hex as it's easier to work with
    file_hex_string = file_bytes.hex()

    # the implementation of this may need to change if more patching is required in the future
    matches = [
        (match.start(), match.group())
        for match in re.finditer("e8f230", file_hex_string)
        if match.start() % 2 == 0
    ]

    # there should be one and only one match else quit
    if len(matches) != 1:
        print("error: more than one hex pattern match")
        return 1

    file_hex_string = file_hex_string.replace("e8f230", "b80100")
    # convert hex string back to bytes
    file_bytes = bytes.fromhex(file_hex_string)

    # save changes
    with open(bin_path, "wb") as file:
        file.write(file_bytes)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image_version",
        metavar="<version>",
        type=str,
        help='specify the image version (e.g. 1.0.0 for v1.0.0). version will be "UNKNOWN" if not specified',
        default="UNKNOWN",
    )
    args = parser.parse_args()

    # load urls.json
    with open("urls.json", encoding="utf-8") as file:
        urls: Urls = json.load(file)

    # http://porteus.org/porteus-mirrors.html
    src = "http://ftp.vim.org/ftp/os/Linux/distr/porteus/x86_64/Porteus-v5.01"
    file_name = "Porteus-OPENBOX-v5.01-x86_64.iso"

    # download ISO file
    response = requests.get(f"{src}/{file_name}", timeout=5)

    if response.status_code != 200:
        print(f"error: {file_name} download error, status_code {response.status_code}")
        return 1

    with open(file_name, "wb") as file:
        file.write(response.content)

    # get local SHA256
    local_sha256 = calculate_sha256(file_name)
    # get remote SHA256
    remote_sha256 = fetch_sha256(f"{src}/sha256sums.txt", file_name)

    # check if hashes match
    if local_sha256 != remote_sha256:
        print("error: hashes do not match")
        print(f"{local_sha256 = }\n{remote_sha256 = }")
        return 1

    if (
        extract(
            file_name,
            "extracted_iso",
            # don't extract unnecessary modules
            {
                "-x!porteus/base/002-xorg.xzm",
                "-x!porteus/base/002-xtra.xzm",
                "-x!porteus/base/003-openbox.xzm",
            },
            True,
        )
        != 0
    ):
        print(f"error: failed to extract {file_name}")
        return 1

    # setup linpack
    if (
        setup_linpack(
            urls["linpack"]["url"],
            urls["linpack"]["file_name"],
            "porteus/porteus/rootcopy/root/linpack",
        )
        != 0
    ):
        print("error: failed to setup linpack")
        return 1

    # patch linpack binary for AMD
    if patch_linpack("porteus/porteus/rootcopy/root/linpack/xlinpack_xeon64") != 0:
        print("error: failed to patch linpack")
        return 1

    # merge custom files with extracted iso
    shutil.copytree("porteus", "extracted_iso", dirs_exist_ok=True)

    process = subprocess.run(
        [
            "bash",
            "extracted_iso/porteus/make_iso.sh",
            f"StresKit-v{args.image_version}-x86_64.iso",
        ],
        check=False,
    )

    if process.returncode != 0:
        print("error: make_iso.sh failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
