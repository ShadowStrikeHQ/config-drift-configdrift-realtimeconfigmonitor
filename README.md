# config-drift-configdrift-RealtimeConfigMonitor
A tool that monitors system configuration files in real-time and alerts on any unexpected changes, using file system events (e.g., via `watchdog`). - Focused on Detects unauthorized or unexpected changes to system configurations. Compares current configuration files against known good baselines and reports any deviations. Supports version control integration for historical analysis and rollback.

## Install
`git clone https://github.com/ShadowStrikeHQ/config-drift-configdrift-realtimeconfigmonitor`

## Usage
`./config-drift-configdrift-realtimeconfigmonitor [params]`

## Parameters
- `-h`: Show help message and exit
- `-c`: No description provided
- `-n`: No description provided
- `-b`: No description provided
- `-i`: The time interval in seconds to check for changes.
- `--version-control`: No description provided
- `--debug`: Enable debug logging.

## License
Copyright (c) ShadowStrikeHQ
