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
    sha256: str


class Urls(TypedDict):
    porteus: Tool
    linpack: Tool
    prime95: Tool
    ycruncher: Tool


def download_file(url: str, out_path: str, expected_sha256: str | None = None) -> int:
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        print(
            f"error: {url} {out_path} download error, status_code {response.status_code}"
        )
        return 1

    if expected_sha256 is not None:
        hash_object = hashlib.sha256(response.content)
        local_sha256 = hash_object.hexdigest()

        if local_sha256 != expected_sha256:
            print("error: hashes do not match")
            print(f"{local_sha256 = }\n{expected_sha256 = }")
            return 1

    with open(out_path, "wb") as file:
        file.write(response.content)

    return 0


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
        args.append("-y")

    process = subprocess.run(args, check=False)

    if process.returncode != 0:
        return 1

    return 0


def setup_linpack(
    url: str, file_name: str, sha256: str, binary_destination: str
) -> int:
    if download_file(url, file_name, sha256) != 0:
        return 1

    if extract(file_name, force=True) != 0:
        print(f"error: failed to extract {file_name}")
        return 1

    # .tgz has .tar with the same file name
    file_name, _ = file_name.rsplit(".tgz")
    tar_file = f"{file_name}.tar"

    # extract inner file to linpack folder
    if extract(tar_file, "linpack", force=True) != 0:
        print(f"error: failed to extract {tar_file}")
        return 1

    # version name changes in folder name (e.g. "benchmarks_2024.0")
    if len(benchmarks_folder := glob("linpack/benchmarks*")) != 1:
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


def setup_prime95(
    url: str, file_name: str, sha256: str, folder_destination: str
) -> int:
    if download_file(url, file_name, sha256) != 0:
        return 1

    if extract(file_name, force=True) != 0:
        print(f"error: failed to extract {file_name}")
        return 1

    # .tgz has .tar with the same file name
    file_name, _ = file_name.rsplit(".tar.gz")
    tar_file = f"{file_name}.tar"

    # extract inner file to prime95 folder
    if extract(tar_file, "prime95", force=True) != 0:
        print(f"error: failed to extract {tar_file}")
        return 1

    # copy folder to folder_destination
    shutil.copytree(
        "prime95",
        folder_destination,
    )

    return 0


def setup_ycruncher(
    url: str, file_name: str, sha256: str, folder_destination: str
) -> int:
    if download_file(url, file_name, sha256) != 0:
        return 1

    if extract(file_name, force=True) != 0:
        print(f"error: failed to extract {file_name}")
        return 1

    # .tgz has .tar with the same file name
    file_name, _ = file_name.rsplit(".tar.xz")
    tar_file = f"{file_name}.tar"

    # extract inner file to ycruncher folder
    if extract(tar_file, force=True) != 0:
        print(f"error: failed to extract {tar_file}")
        return 1

    # version name changes in folder name (e.g. "y-cruncher v0.8.3.9533")
    if len(ycruncher_folder := glob("y-cruncher*-static")) != 1:
        print("error: unable to find correct benchmarks folder")
        return 1

    # copy folder to folder_destination
    shutil.copytree(
        ycruncher_folder[0],
        folder_destination,
    )

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

    bashrc_lines: list[str] = []

    # load urls.json
    with open("urls.json", encoding="utf-8") as file:
        urls: Urls = json.load(file)

    # download ISO file
    if (
        download_file(
            urls["porteus"]["url"],
            urls["porteus"]["file_name"],
            urls["porteus"]["sha256"],
        )
        != 0
    ):
        return 1

    if (
        extract(
            urls["porteus"]["file_name"],
            "extracted_iso",
            # don't extract unnecessary modules
            {
                "porteus/base/002-xorg.xzm",
                "porteus/base/002-xtra.xzm",
                "porteus/base/003-openbox.xzm",
            },
            True,
        )
        != 0
    ):
        print(f"error: failed to extract {urls['porteus']['file_name']}")
        return 1

    # setup linpack
    if (
        setup_linpack(
            urls["linpack"]["url"],
            urls["linpack"]["file_name"],
            urls["linpack"]["sha256"],
            "porteus/porteus/rootcopy/root/linpack",
        )
        != 0
    ):
        print("error: failed to setup linpack")
        return 1

    bashrc_lines.append("alias linpack='(cd /root/linpack && ./runme_xeon64.sh)'")

    # patch linpack binary for AMD
    if patch_linpack("porteus/porteus/rootcopy/root/linpack/xlinpack_xeon64") != 0:
        print("error: failed to patch linpack")
        return 1

    # setup prime95
    if (
        setup_prime95(
            urls["prime95"]["url"],
            urls["prime95"]["file_name"],
            urls["prime95"]["sha256"],
            "porteus/porteus/rootcopy/root/prime95",
        )
        != 0
    ):
        print("error: failed to setup prime95")
        return 1

    bashrc_lines.append("alias prime95='(cd /root/prime95 && ./mprime)'")

    # setup ycruncher
    if (
        setup_ycruncher(
            urls["ycruncher"]["url"],
            urls["ycruncher"]["file_name"],
            urls["ycruncher"]["sha256"],
            "porteus/porteus/rootcopy/root/ycruncher",
        )
        != 0
    ):
        print("error: failed to setup ycruncher")
        return 1

    bashrc_lines.append("alias ycruncher='(cd /root/ycruncher && ./y-cruncher)'")

    # write contents to .bashrc
    with open("porteus/porteus/rootcopy/root/.bashrc", "a", encoding="utf-8") as file:
        for line in bashrc_lines:
            file.write(f"{line}\n")

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
