import re
import sys


def main():
    with open(sys.argv[1], "rb") as file:
        byte_array = file.read()

    hex_string = byte_array.hex()
    matches = [
        (match.start(), match.group())
        for match in re.finditer("e8f230", hex_string)
        if match.start() % 2 == 0
    ]

    if len(matches) != 1:
        return 1

    hex_string = hex_string.replace("e8f230", "b80100")
    byte_array = bytes.fromhex(hex_string)

    with open(sys.argv[1], "wb") as file:
        file.write(byte_array)

    return 0


if __name__ == "__main__":
    sys.exit(main())
