import sys
import os
import shlex
import subprocess
import pathlib
import shutil

from typing import Optional, List
from functools import partial
from distutils.version import StrictVersion

from .log import logger


class KeepassWrapper:

    subprocess_piped = partial(
        subprocess.run, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    @staticmethod
    def verify_binary_exists():
        """Make sure the keepassxc-cli binary exists"""
        if shutil.which("keepassxc-cli") is None:
            logger.critical(
                "Could not find the keepassxc-cli binary. Verify its installed and on your $PATH."
            )
            sys.exit(1)

    @staticmethod
    def version() -> StrictVersion:
        """Returns the KeepassXC Version"""
        version_proc: subprocess.CompletedProcess = KeepassWrapper.subprocess_piped(
            shlex.split("keepassxc-cli --version")
        )
        return StrictVersion(version_proc.stdout.strip())

    @classmethod
    def backwards_compatible_export(cls) -> str:
        """
        In KeepassXC version 2.5.0, the extract command was re-named to export
        Attempt to parse the version number and generate the correct subcommand
        """
        try:
            version: StrictVersion = cls.version()
            if version < StrictVersion("2.5.0"):
                return "extract"
            else:
                return "export"
        except ValueError:
            return "export"

    @classmethod
    def export_database(
        cls,
        database_file: pathlib.Path,
        database_password: str,
        database_keyfile: Optional[pathlib.Path] = None,
    ) -> str:
        """Calls the keepassxc-cli export command, returns the output from the command"""

        command_parts: List[str] = ["keepassxc-cli", cls.backwards_compatible_export()]
        if database_keyfile:
            command_parts.extend(["-k", str(database_keyfile)])
        command_parts.append(str(database_file))

        keepassxc_output: subprocess.CompletedProcess = KeepassWrapper.subprocess_piped(
            shlex.split(" ".join(command_parts)), input=database_password,
        )
        if keepassxc_output.returncode != 0:
            logger.critical(keepassxc_output.stderr)
            sys.exit(1)
        # python doesnt like the version tag, remove the first line
        return keepassxc_output.stdout.split(os.linesep, 2)[-1]


binary_exists = False
if not binary_exists:
    KeepassWrapper.verify_binary_exists()
    binary_exists = True