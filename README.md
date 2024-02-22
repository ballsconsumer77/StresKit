# StresKit

[![Downloads](https://img.shields.io/github/downloads/amitxv/StresKit/total.svg)](https://github.com/amitxv/StresKit/releases)

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/amitxv)

Lightweight bootable ISO based on [Porteus](https://www.porteus.org) containing a compendium of stress-testing related tools and utilities.

## Usage

1. Download the latest [StresKit](https://github.com/amitxv/StresKit/releases) ISO and burn it to a USB with [Rufus](https://rufus.ie/en) then boot to it through UEFI. [Ventoy](https://www.ventoy.net/en/index.html) (use grub2 mode if normal mode doesn't work) is another popular option
2. The login username is ``root`` and the password is ``toor``
3. After logging in, you can use the tools packaged in StresKit. See [What's Included?](#whats-included) for the available tools
4. While any given test is running, you can switch to a different TTY to carry out other tasks such as viewing sensors. As an example, press ``Ctrl+Alt+F2`` to switch to TTY 2 and ``Ctrl+Alt+F1`` to switch back to TTY 1

## Viewing Large Outputs

Scrolling in Porteus is a bit tedious. For this reason, you can write stdout to a file while viewing the output simultaneously with the ``tee`` command. This also allows you to backup the output on a USB drive if needed which can be useful for other purposes.

```sh
<command> | tee -a output.txt
```

Learn the basic syntax of ``vi`` by watching [this video](https://www.youtube.com/watch?v=vo2FXvPkcEA). Use ``vi output.txt`` to view the ``output.txt`` file at any given time.

## What's Included?

- [Help Message](#help-message)
- [Temperature Sensor](#temperature-sensor)
- [Linpack](#linpack)
- [Prime95](#prime95)
- [y-cruncher](#y-cruncher)
- [Intel® Memory Latency Checker (Intel® MLC)](#intel®-memory-latency-checker-intel®-mlc)

## Help Message

Display the pre-login help message containing an overview of commands.

Usage:

```
skhelp
```

## Temperature Sensor

View temperature of each CPU in the system. This is simply an alias for ``watch -n 1 sensors coretemp-isa-0000``.

Usage:

```
cputemp
```

## [Linpack](https://en.wikipedia.org/wiki/LINPACK_benchmarks)

Linpack is a stress-test based on the [Intel Math Kernel Library](https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html#gs.4kgof5) which solves a dense system of linear equations. The binary has been openly patched to run on AMD CPUs.

Usage:

```
linpack [-m <gb>] [-s <samples>]
```

- ``-m`` is the memory size in gigabytes. If not specified, free memory minus 100mb will be used
- ``-s`` is the number of trials to run. If not specified, 100 trials will be executed

## [Prime95](https://www.mersenne.org/download)

Usage:

```
prime95
```

## [y-cruncher](http://www.numberworld.org/y-cruncher)

Usage:

```
ycruncher
```

## [Intel® Memory Latency Checker (Intel® MLC)](https://www.intel.com/content/www/us/en/developer/articles/tool/intelr-memory-latency-checker.html)

Usage:

```
mlc
```

## Building

The ``build.py`` script can be used to build the ISO. It is designed to run on [ubuntu-latest](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#choosing-github-hosted-runners) for GitHub actions, but you can use a Linux distro of your choice.

```bash
git clone https://github.com/amitxv/StresKit.git
cd StresKit/
python build.py
```
