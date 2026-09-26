# Drone Intrusion Detection System (Drone IDS)
## PUSHPAK Grand Challenge 2026 - Objective 2: Security of Drones

An indigenous, real-time cyber threat detection system for UAV platforms designed for the PUSHPAK Grand Challenge 2026 "Security of Drones" competition.

## System Architecture

```
┌──────────────┐     WIRED (UART/USB)     ┌──────────────────────────────────────┐
│   REAL DRONE │ ◄──────────────────────► │          DRONE IDS                 │
│  (Autopilot) │      MAVLink v2.0       │                                    │
│  (sys=1)     │   over Serial/USB       │  ┌────────────────────────────────┐  │
└──────────────┘                           │  │      MESSAGE BUS (Pub/Sub)     │  │
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

## Features

- **Real-time Detection** - Multi-threaded pipeline processing MAVLink messages at 100+ Hz
- **6 Independent Detectors** - Modular, pluggable architecture
- **Forensic Evidence Chain** - SHA-256 hash chaining, MITRE ATT&CK tags, evidence hashes
- **Dual-Mode Operation** - SITL monitoring (UDP 14550) + Attack injection (UDP 14551)
- **Forensic Evidence Chain** - SHA-256 hash chaining, MITRE ATT&CK tags, chain-of-custody log
- **Configurable Thresholds** - All detection thresholds externalized in YAML config

## Quick Start (SITL Demo)

```bash
# Terminal 1: Start ArduPilot SITL
sim_vehicle.py -v copter -f quad -I0 --console --map

# Terminal 2: Run Drone IDS (connects to SITL on UDP 14550 + injection port 14551)
cd drone_ids
python run_ids.py

# Terminal 3: Inject attacks (run after IDS says "Running indefinitely...")
python run_attack.py
```
## Installation

```bash
cd drone_ids
pip install -r requirements.txt

# For SITL: install ArduPilot and set ARDUPILOT_SITL env var
```

## Configuration

Edit `config/ids_config.yaml` for:
- Connection parameters (serial vs UDP)
- Detection thresholds
- Alerting outputs
- Forensics settings

## Output

- **Console**: Real-time colored alerts
- **Logs**: `logs/alerts.log`, `logs/evidence.log`
- **Chain of Custody**: `logs/chain_of_custody.log`

## Detectors

| Detector | Attack Types | MITRE ATT&CK |
|----------|--------------|--------------|
| **GPS Spoofing** | Position jumps, velocity anomalies, IMU cross-check, EKF innovation | T1557 (MITM) |
| **MAVLink Anomaly** | Rate analysis, sequence gaps, payload anomalies, heartbeat monitoring | T1499 (DoS), T1557 (MITM) |
| **Command Injection** | Unauthorized sources, rate limiting, critical parameter tampering, mission injection | T1021 (Remote Services), T1562 (Impair Defenses) |
| **Telemetry Manipulation** | Impossible attitude rates, position/velocity inconsistency, sensor cross-validation | T1557 (MITM) |
| **DoS Detection** | Link quality, message flooding, heartbeat loss, RF jamming detection | T1499 (DoS) |
| **Firmware Integrity** | Boot verification, parameter integrity, reboot monitoring, memory corruption detection | T1542 (Pre-OS Boot), T1562 (Impair Defenses) |

## Forensic Capabilities

- **SHA-256 Hash Chaining** - Tamper-evident evidence log
- **MITRE ATT&CK Mapping** - Every alert tagged with technique ID
- **Evidence Hashes** - Per-alert SHA-256 for integrity verification
- **Chain of Custody** - Cryptographic hash chain for court-admissible evidence

## Competition Compliance

Addresses all evaluation criteria:
- Detection Accuracy 20%, False Positive Rate 20%, Distance 10%, Latency 10%
- Coverage 15%, Efficiency 10%, Integration 5%, Documentation 5%, Future 5%

## Demo Commands

```bash
# Terminal 1: Start ArduPilot SITL
sim_vehicle.py -v copter -f quad -I0 --console --map

# Terminal 2: Run Drone IDS (connects to SITL on UDP 14550 + injection port 14551)
python run_ids.py

# Terminal 3: Inject attacks (run after IDS says "Running indefinitely...")
python run_attack.py

# Optional: Simulated demo without SITL
python run_simulate.py
```

## Project Structure

```
drone_ids/
├── run_ids.py              # Main IDS entry point
├── run_attack.py           # Attack injection script
├── run_simulate.py         # Simulated demo (no SITL needed)
├── config/ids_config.yaml  # All thresholds & settings
├── requirements.txt        # Python dependencies
├── src/drone_ids/
│   ├── core/               # Engine, config, message bus
│   ├── detectors/          # 6 independent detectors
│   ├── interfaces/         # MAVLink, SITL interfaces
│   └── alerting/           # Console, file, forensic logging
└── logs/                   # Runtime evidence (auto-created)
```

## License

MIT License
