"""Namd run daaas scarf demo."""

import logging
import pathlib
import time

import gooey

import ScarfRun

logging.basicConfig(level=logging.INFO)


@gooey.Gooey()
def main():
    """Provide gui."""
    parser = gooey.GooeyParser(description="Run stuff on scarf")

    parser.add_argument(
        "scarf_host",
        help="Scarf SSH hostname",
        default="ui1.scarf.rl.ac.uk",
    )
    parser.add_argument(
        "scarf_username",
        help="Scarf SSH username",
        default="scarf1123",
    )
    parser.add_argument(
        "--scarf_password",
        help="Scarf SSH password",
        default="",
    )
    parser.add_argument(
        "input_files",
        help="Input files",
        widget="MultiFileChooser",
        nargs="*",
    )
    parser.add_argument(
        "--slurm_job_file",
        help="SLURM job file",
        widget="FileChooser",
        default="",
    )
    parser.add_argument(
        "output_dir",
        help="Output directory",
        widget="DirChooser",
    )

    args = parser.parse_args()
    ScarfRun.run(
        args.scarf_host,
        args.scarf_username,
        args.scarf_password,
        args.slurm_job_file,
        args.input_files,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
