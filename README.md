# Drone Intrusion Detection System (Drone IDS)
## PUSHPAK Grand Challenge 2026 - Objective 2

An indigenous, real-time cyber threat detection system for UAV platforms designed for the PUSHPAK Grand Challenge 2026 "Security of Drones" competition.

## System Architecture

```
┌──────────────┐     WIRED (UART/USB)     ┌──────────────────────────────────────┐
│   DRONE      │ ◄──────────────────────► │            DRONE IDS                 │
│              │   over Serial/USB        │  ┌────────────────────────────────┐  │
└──────────────┘                          │  │      MESSAGE BUS (Pub/Sub)     │  │
                                          │  │   (Thread-safe, async)         │  │
                                          │  └──────────────┬─────────────────┘  │
                                          └─────────────────┼────────────────────┘
                                                             │
                    ┌─────────────────────────────────────────┼─────────────────────────────────┐
                    ▼                                         ▼                                 ▼
            ┌───────────────┐                         ┌───────────────┐               ┌───────────────┐
            │   DETECTORS   │                         │   DETECTORS   │               │   DETECTORS   │
            │  (6 modules)  │                         │  (6 modules)  │               │  (6 modules)  │
            └───────┬───────┘                         └───────┬───────┘               └───────┬───────┘
                    │                                         │                                 │
        ┌───────────┼───────────┐                   ┌─────────┼─────────┐           ┌─────────┼─────────┐
        ▼           ▼           ▼           ▼         ▼         ▼         ▼         ▼         ▼         ▼
   ┌────────┐ ┌────────┐ ┌────────┐   ┌────────┐ ┌────────┐   ┌────────┐ ┌────────┐ ┌────────┐
   │ GPS    │ │ MAVLink│ │ Command│   │Telemetry│ │ DoS    │   │Firmware │ │ Alert  │ │ Forensics│
   │ Spoofing│ │ Anomaly│ │ Inject │   │ Manipul │ │ Detector│   │Integrity│ │ Manager│ │ Logger  │
   └────┬───┘ └────┬───┘ └────┬───┘   └────┬───┘ └────┬───┘   └────┬───┘ └────┬───┘ └────┬───┘
        │          │          │            │          │          │          │          │
        └──────────┴──────────┴────────────┴──────────┴──────────┴──────────┴──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
            ┌───────────────┐             ┌───────────────┐
            │  CONSOLE OUT  │             │  FILE LOGS    │
            │  (Colored)    │             │  (JSON)       │
            └───────────────┘             └───────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                        ┌─────────────────────┐
                        │ CHAIN OF CUSTODY    │
                        │ SHA-256 Hash Chain  │
                        │ MITRE ATT&CK Tags   │
                        └─────────────────────┘
```

**Connection Details:**
- **Physical:** UART (TELEM1/TELEM2) or USB (FTDI) cable from drone autopilot to IDS compute module
- **Protocol:** MAVLink v2.0 over serial (57600/115200/921600 baud)
- **Power:** IDS powered from drone's 5V BEC or separate 5V supply
- **Mounting:** IDS compute module (Raspberry Pi CM4 / Jetson Nano / x86 SBC) mounted inside drone chassis

## Overview

This Drone IDS provides comprehensive intrusion detection for UAV platforms:

- **GPS Spoofing Detection** - Position jumps, velocity anomalies, IMU cross-check, EKF innovation
- **MAVLink Communication Anomalies** - Rate analysis, sequence gaps, payload anomalies, heartbeat monitoring
- **Command Injection Detection** - Unauthorized sources, rate limiting, critical parameter tampering, mission injection
- **Telemetry Manipulation** - Impossible attitude rates, position/velocity inconsistency, sensor cross-validation
- **DoS Detection** - Link quality, message flooding, heartbeat loss, RF jamming detection
- **Firmware Integrity** - Boot verification, parameter integrity, reboot monitoring, memory corruption detection

## Installation

```bash
cd drone_ids
pip install -r requirements.txt

# For SITL: install ArduPilot and set ARDUPILOT_SITL env var
```

## Quick Start (SITL Demo)

```bash
# Terminal 1: Start SITL
sim_vehicle.py -v copter -f quad -I0 --console --map

# Terminal 2: Run Drone IDS with SITL
python run_ids.py

# Terminal 3: Run attack simulations
python run_simulate.py
```

## Real Drone Deployment

```bash
# Connect drone via UART/USB
# Configure serial port in config/ids_config.yaml:
sitl:
  connection_string: "serial:///dev/ttyTHS1:921600"  # Jetson UART
  # or
  connection_string: "serial:///dev/ttyUSB0:115200"  # USB

# Run on drone compute module
python run_ids.py
```

## Configuration

Edit `config/ids_config.yaml` for:
- Connection parameters (serial vs UDP)
- Detection thresholds
- Alerting outputs
- Forensics settings

## Output

- Console: Real-time colored alerts
- Logs: `logs/alerts.log`, `logs/evidence.log`
- Chain of Custody: `logs/chain_of_custody.log`

## Detectors

| Detector | Attack Types |
|----------|--------------|
| GPS Spoofing | Position jump, velocity, IMU cross-check |
| MAVLink Anomaly | Rate, sequence, payload anomalies |
| Command Injection | Unauthorized source, rate limit, ACK |
| Telemetry Manipulation | Kinematic, sensor cross-check |
| DoS | Flooding, jamming, heartbeat loss |
| Firmware Integrity | Boot hash, param integrity, reboots |

## Competition Compliance

Addresses all evaluation criteria (Detection Accuracy 20%, FPR 20%, Distance 10%, Latency 10%, Coverage 15%, Efficiency 10%, Integration 5%, Documentation 5%, Future 5%).



## License

MIT License
