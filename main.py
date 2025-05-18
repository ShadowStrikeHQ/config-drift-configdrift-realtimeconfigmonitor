import argparse
import logging
import os
import sys
import time
from typing import Dict, Optional

import yaml
from deepdiff import DeepDiff
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ConfigChangeHandler(FileSystemEventHandler):
    """Handles file system events for configuration files."""

    def __init__(
        self,
        config_files: Dict[str, str],
        baseline_dir: str,
        version_control: bool = False,
    ) -> None:
        """
        Initializes the ConfigChangeHandler.

        Args:
            config_files: A dictionary mapping configuration file paths to their names.
            baseline_dir: The directory containing baseline configuration files.
            version_control: Whether to integrate with version control (not implemented).
        """
        super().__init__()
        self.config_files = config_files
        self.baseline_dir = baseline_dir
        self.version_control = version_control  # Placeholder
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        """
        Called when a file or directory is modified.

        Args:
            event: The event object describing the change.
        """
        if event.is_directory:
            return
        filepath = event.src_path
        if filepath in self.config_files:
            self.check_config_drift(filepath)

    def check_config_drift(self, filepath: str):
        """
        Compares the current configuration file with its baseline.

        Args:
            filepath: The path to the configuration file.
        """
        try:
            config_name = self.config_files[filepath]
            baseline_path = os.path.join(self.baseline_dir, f"{config_name}.yaml")

            if not os.path.exists(baseline_path):
                self.logger.error(f"Baseline file not found: {baseline_path}")
                return

            with open(filepath, "r") as f:
                current_config = yaml.safe_load(f)
            with open(baseline_path, "r") as f:
                baseline_config = yaml.safe_load(f)

            diff = DeepDiff(baseline_config, current_config, ignore_order=True)

            if diff:
                self.logger.warning(
                    f"Configuration drift detected in {config_name} ({filepath}):\n{diff}"
                )
                # Further actions could include:
                # - Alerting via email, Slack, etc.
                # - Attempting rollback (if version control is implemented)
            else:
                self.logger.info(f"No configuration drift detected in {config_name}.")

        except Exception as e:
            self.logger.error(
                f"Error checking configuration drift for {filepath}: {e}",
                exc_info=True,  # Include traceback for debugging
            )


def setup_argparse():
    """Sets up the argument parser."""
    parser = argparse.ArgumentParser(
        description="Real-time Configuration Monitor for detecting configuration drift."
    )
    parser.add_argument(
        "-c",
        "--config-files",
        nargs="+",
        required=True,
        help="List of configuration files to monitor (e.g., /etc/app.conf /opt/settings.yaml).",
    )
    parser.add_argument(
        "-n",
        "--config-names",
        nargs="+",
        required=True,
        help="List of names corresponding to the config files, for proper baseline match.  Must be in the same order as config files (e.g., app_config settings).",
    )
    parser.add_argument(
        "-b",
        "--baseline-dir",
        required=True,
        help="Directory containing baseline configuration files (YAML format).",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=1,
        help="The time interval in seconds to check for changes.",
    )

    parser.add_argument(
        "--version-control",
        action="store_true",
        help="Enable version control integration (Not implemented)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging."
    )

    return parser


def validate_input(args):
    """Validates the input arguments."""
    if len(args.config_files) != len(args.config_names):
        raise ValueError(
            "Number of configuration files and configuration names must be the same."
        )

    if not os.path.isdir(args.baseline_dir):
        raise ValueError(f"Baseline directory '{args.baseline_dir}' does not exist.")

    for config_file in args.config_files:
        if not os.path.isfile(config_file):
            raise ValueError(f"Configuration file '{config_file}' does not exist.")


def main():
    """Main function to run the configuration monitor."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        validate_input(args)
    except ValueError as e:
        logging.error(f"Input validation error: {e}")
        sys.exit(1)

    config_files_dict = dict(zip(args.config_files, args.config_names))

    event_handler = ConfigChangeHandler(
        config_files_dict, args.baseline_dir, args.version_control
    )
    observer = Observer()

    # Watch the parent directory of each config file
    watched_directories = set()
    for config_file in args.config_files:
        directory = os.path.dirname(os.path.abspath(config_file))
        if directory not in watched_directories:
            observer.schedule(event_handler, directory, recursive=False)
            watched_directories.add(directory)
            logging.info(f"Watching directory: {directory}")

    observer.start()
    logging.info("Configuration monitor started.")

    try:
        while True:
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Configuration monitor stopped by user.")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    # Example usage:
    # Create baseline files:
    #   mkdir baseline
    #   echo "{'setting1': 'value1'}" > baseline/app_config.yaml
    #   echo "{'db_host': 'localhost'}" > baseline/settings.yaml
    # Create config files (initially matching baselines):
    #   echo "{'setting1': 'value1'}" > app.conf
    #   echo "{'db_host': 'localhost'}" > settings.yaml
    # Run:
    #   python main.py -c app.conf settings.yaml -n app_config settings -b baseline -i 1

    # Simulate changes:
    #   echo "{'setting1': 'value2'}" > app.conf  # This will trigger drift detection.
    main()