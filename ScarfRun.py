"""Class to run commands and send/receive files relative to a UUID-ed run directory."""

import logging
import pathlib
import time
import uuid

import paramiko
import scp


class ScarfRun:
    """
    Interface to scarf.

    Remotely the commands are all relative to run_dir - runs/<uuid>.
    """

    def __init__(self, host, username, password):
        """Initialize connection and create run dir."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=host, username=username, password=password)
        self.scp = scp.SCPClient(self.client.get_transport())
        self.run_uuid = str(uuid.uuid4())
        # create the run directory
        self.run_dir = f"runs/{self.run_uuid}/"
        self.client.exec_command(f"mkdir -p {self.run_dir}")
        # avoid scp's "is a directory" error
        time.sleep(1)

    def run(self, cmd):
        """Run a command in the run dir and return code and output."""
        cmd = f"cd {self.run_dir} && {cmd}"
        logging.info(f"running {cmd}")
        stdin, stdout, stderr = self.client.exec_command(cmd)
        stdout_str, stderr_str = stdout.read(), stderr.read()
        retcode = stdout.channel.recv_exit_status()
        logging.debug(f'command "{cmd}" finished')
        logging.debug(f"command retcode: {retcode}")
        logging.debug(f"command stdout: {stdout_str}")
        logging.debug(f"command stderr: {stderr_str}")
        stdin.close()
        stdout.close()
        stderr.close()
        return retcode, stdout_str, stderr_str

    def send(self, files):
        """Send files into the run dir."""
        logging.info("Uploading files:")
        for f in files:
            logging.info(f"- {f}")
        self.scp.put(files, remote_path=self.run_dir)

    def receive_run_dir(self, output_dir):
        """Copy the entire run directory back."""
        logging.info(f"Receiving run dir {self.run_dir}")
        self.scp.get(remote_path=self.run_dir, recursive=True, local_path=output_dir)


def run(
    scarf_host, scarf_username, scarf_password, slurm_job_file, files_in, output_dir
):
    """Send files to scarf, run it and then fetch output files."""
    logging.info("start")

    # find the job file:
    # either the user picked something in the filechooser, or we can find it by looking at
    # the input directory and find a file ending with '.job'. If it doesn't find it or
    # if it finds more than one file, then report an error
    job_file = ""
    if slurm_job_file:
        # if the user selects a file with the filechooser, then we need to remove the path
        job_file = pathlib.Path(slurm_job_file).name
    else:
        indir = pathlib.Path(files_in[0]).parent
        slurm_job_files = list(indir.glob("*.job"))
        logging.info(slurm_job_files)
        if not slurm_job_files:
            raise Exception(
                f"No job file found in {indir}. Please choose the job file you want to use."
            )
        if len(slurm_job_files) > 1:
            raise Exception(
                f"More than 1 job file found in {indir}. Please choose the job file you want to use."
            )
        job_file = pathlib.Path(slurm_job_files[0]).name

    # run stuff:
    # 1. send input files to runs/<uuid>
    # 2. run sbatch on selected job file
    # 3. copy the run directory back to the output_dir
    s = ScarfRun(scarf_host, scarf_username, scarf_password)
    s.send(files_in)
    time.sleep(1)
    code, stdout, stderr = s.run(f"sbatch -W {job_file}")
    if not code == 0:
        logging.error("stdout:")
        logging.error(stdout)
        logging.error("stderr:")
        logging.error(stderr)
        raise Exception("sbatch failed.")
    s.receive_run_dir(output_dir)

    out_dir = output_dir + "/" + s.run_uuid
    logging.info(f"The files are available in the directory {out_dir}")
