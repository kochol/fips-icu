"""Build and embed ICU data using native tools from the same checkout."""
import argparse
import os
from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import sys


def main():
    """Generate data in the build tree without modifying the source checkout."""
    parser = argparse.ArgumentParser()
    for name in ("source", "output", "tools", "config", "major"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    tools = Path(args.tools).resolve()
    suffix = ".exe" if os.name == "nt" else ""

    def tool(name):
        """Locate the native tool for this build configuration."""
        return str(tools / name / args.config / (name + suffix))

    # Relative paths avoid unquoted spaces in upstream's command templates.
    # Execute argument lists directly, avoiding shell command-length limits.
    sys.path.insert(0, str(source / "python"))
    from icutools.databuilder.renderers import common_exec

    def run_command(command_line, platform, verbose):
        """Run a generated ICU command without involving a platform shell."""
        command = shlex.split(command_line)
        if os.name == "nt":
            command[0] += ".exe"
        return subprocess.call(command)

    common_exec.run_shell_command = run_command
    stage = output / "tools"
    stage.mkdir(exist_ok=True)
    for name in ("genbrk", "gencfu", "gencnval", "gendict", "genrb", "gensprep", "icupkg", "makeconv"):
        shutil.copy2(tool(name), stage / (name + suffix))
    data_source = output / "source"
    if data_source.exists():
        if data_source.is_symlink() or data_source.resolve().parent != output:
            raise RuntimeError("Refusing to replace data outside the generated output directory")
        shutil.rmtree(data_source)
    shutil.copytree(source / "data", data_source)

    package = "icudt" + args.major + ("b" if sys.byteorder == "big" else "l")
    os.chdir(output)
    sys.argv = ["icutools.databuilder", "--mode=unix-exec", "--src_dir=source",
                "--out_dir=data/" + package, "--tmp_dir=tmp", "--tool_dir=tools"]
    try:
        runpy.run_module("icutools.databuilder", run_name="__main__")
    except SystemExit as error:
        if error.code not in (None, 0):
            raise

    subprocess.run([tool("icupkg"), "-a", "tmp/icudata.lst", "-s", "data/" + package,
                    "new", package + ".dat"], check=True)
    subprocess.run([tool("genccode"), "-e", "icudt" + args.major, "-f", "icudata",
                    "-d", ".", package + ".dat"], check=True)


if __name__ == "__main__":
    main()
