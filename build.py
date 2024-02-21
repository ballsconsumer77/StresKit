import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from glob import glob

import requests


def dl_file(url: str, outfile: str, sha256: str) -> int:
    response = requests.get(url, timeout=5)

    if not response.ok:
        return 1

    # check whether hashes match
    hash_object = hashlib.sha256(response.content)
    file_sha256 = hash_object.hexdigest()

    if file_sha256 != sha256:
        return 1

    with open(outfile, "wb") as fp:
        fp.write(response.content)

    return 0


def patch_linpack(bin_path: str) -> int:
    with open(bin_path, "rb") as file:
        file_bytes = file.read()

    # convert bytes to hex as it's easier to work with
    file_hex_string = file_bytes.hex()

    # the implementation of this may need to change if more patching is required in the future
    matches = [
        (match.start(), match.group()) for match in re.finditer("e8f230", file_hex_string) if match.start() % 2 == 0
    ]

    # there should be one and only one match else quit
    if len(matches) != 1:
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
        help='specify the image version (e.g. 1.0.0 for v1.0.0). \
            version will be "UNKNOWN" if not specified',
        default="UNKNOWN",
    )

    args = parser.parse_args()

    build_directory = "/tmp/building"

    with open("urls.json", encoding="utf-8") as fp:
        urls = json.load(fp)

    # make temp folder for building
    os.makedirs(build_directory)

    # ================================
    # Download and extract Porteus ISO
    # ================================

    # download porteus ISO
    porteus_iso = os.path.join(build_directory, "Porteus.iso")

    if dl_file(urls["porteus"]["url"], porteus_iso, urls["porteus"]["sha256"]) != 0:
        return 1

    # extract ISO contents to iso_contents folder
    iso_contents = os.path.join(build_directory, "iso_contents")

    try:
        subprocess.run(
            [
                "7z",
                "x",
                porteus_iso,
                # don't extract unnecessary files
                "-x!porteus/base/002-xorg.xzm",
                "-x!porteus/base/002-xtra.xzm",
                "-x!porteus/base/003-openbox.xzm",
                f"-o{iso_contents}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        return 1

    # ===========================
    # Modify Porteus ISO contents
    # ===========================

    # merge custom files with extracted iso
    shutil.copytree("porteus", iso_contents, dirs_exist_ok=True)

    tools_folder = os.path.join(iso_contents, "porteus", "rootcopy", "root", "tools")

    # =============
    # Setup Linpack
    # =============

    linpack_tgz = os.path.join(build_directory, "linpack.tgz")

    if dl_file(urls["linpack"]["url"], linpack_tgz, urls["linpack"]["sha256"]) != 0:
        return 1

    linpack_contents = os.path.join(build_directory, "linpack")

    with tarfile.open(linpack_tgz, "r:gz") as tar_file:
        tar_file.extractall(linpack_contents)

    # find benchmarks folder as the folder name (e.g. "benchmarks_2024.0") is dynamic
    benchmarks_folder = glob(os.path.join(linpack_contents, "benchmarks*"))

    if len(benchmarks_folder) != 1:
        return 1

    shutil.copy(
        os.path.join(benchmarks_folder[0], "linux", "share", "mkl", "benchmarks", "linpack", "xlinpack_xeon64"),
        os.path.join(tools_folder, "linpack"),
    )

    if patch_linpack(os.path.join(tools_folder, "linpack", "xlinpack_xeon64")) != 0:
        return 1

    # =============
    # Setup Prime95
    # =============

    prime95_tgz = os.path.join(build_directory, "prime95.tgz")

    if dl_file(urls["prime95"]["url"], prime95_tgz, urls["prime95"]["sha256"]) != 0:
        return 1

    with tarfile.open(prime95_tgz, "r:gz") as tar_file:
        tar_file.extractall(os.path.join(tools_folder, "prime95"))

    # ================
    # Setup y-cruncher
    # ================

    ycruncher_txz = os.path.join(build_directory, "ycruncher.tar.xz")

    if dl_file(urls["ycruncher"]["url"], ycruncher_txz, urls["ycruncher"]["sha256"]) != 0:
        return 1

    ycruncher_contents = os.path.join(build_directory, "ycruncher")

    with tarfile.open(ycruncher_txz, "r:xz") as tar_file:
        tar_file.extractall(ycruncher_contents)

    # version name changes in folder name (e.g. "y-cruncher v0.8.3.9533")
    ycruncher_folder = glob(os.path.join(ycruncher_contents, "y-cruncher*-static"))

    if len(ycruncher_folder) != 1:
        return 1

    shutil.copytree(
        ycruncher_folder[0],
        os.path.join(tools_folder, "ycruncher"),
    )

    # ==================================
    # Setup Intel Memory Latency Checker
    # ==================================

    mlc_tgz = os.path.join(build_directory, "mlc.tgz")

    if dl_file(urls["imlc"]["url"], mlc_tgz, urls["imlc"]["sha256"]) != 0:
        return 1

    imlc_contents = os.path.join(build_directory, "imlc")

    with tarfile.open(mlc_tgz, "r:gz") as tar_file:
        tar_file.extractall(imlc_contents)

    shutil.move(os.path.join(imlc_contents, "Linux", "mlc"), tools_folder)

    # =====================
    # Pack ISO and clean up
    # =====================

    try:
        subprocess.run(
            [
                "bash",
                os.path.join(iso_contents, "porteus", "make_iso.sh"),
                # output ISO path
                os.path.join(os.path.dirname(os.path.abspath(__file__)), f"StresKit-v{args.image_version}-x86_64.iso"),
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        return 1

    shutil.rmtree(build_directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())
