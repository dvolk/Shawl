"""Namd run daaas scarf demo."""

import uuid
import logging

import gooey
import paramiko
import scp

logging.basicConfig(level=logging.DEBUG)


class ScarfRun:
    """
    Interface to scarf.

    Remotely the commands are all relative to run_dir - runs/<uuid>.
    """

    def __init__(self, host, username):
        """Initialize connection and create run dir."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=host, username=username)
        self.scp = scp.SCPClient(self.client.get_transport())
        self.run_uuid = str(uuid.uuid4())
        self.run_dir = f"runs/{self.run_uuid}/"
        self.client.exec_command(f"mkdir -p {self.run_dir}")

    def run(self, cmd):
        """Run a command in the run dir."""
        cmd = f"cd {self.run_dir} && {cmd}"
        logging.info(f"running {cmd}")
        return self.client.exec_command(cmd)

    def send(self, files):
        """Send files into the run dir."""
        logging.info(f"Uploading {files}")
        self.scp.put(files, remote_path=self.run_dir)

    def receive_run_dir(self, output_dir):
        """Copy the entire run directory back."""
        logging.info(f"Receiving run dir {self.run_dir}")
        self.scp.get(remote_path=self.run_dir, recursive=True, local_path=output_dir)


def run(scarf_host, scarf_username, files_in, output_dir):
    """Send files to scarf, run it and then fetch output files."""
    logging.info("start")
    s = ScarfRun(scarf_host, scarf_username)
    s.send(files_in)
    s.run("cd ..; ls *")
    s.run("srun sbatch.job")
    s.receive_run_dir(output_dir)


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
        "input_files",
        help="Input files",
        widget="MultiFileChooser",
        nargs="*",
    )
    parser.add_argument(
        "output_dir",
        help="Output directory",
        widget="DirChooser",
    )

    args = parser.parse_args()
    run(
        args.scarf_host,
        args.scarf_username,
        args.input_files,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
