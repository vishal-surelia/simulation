#!/usr/bin/env python3
"""
Drone IDS - Attack Simulation (Direct Injection Mode)
Injects messages DIRECTLY into IDS message bus - all detectors see attacks.
Run this WHILE the IDS is running in another terminal.
"""
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drone_ids.core.config import config
from drone_ids.core.ids_engine import engine
from drone_ids.core.message_bus import message_bus, Message, MessageType
from drone_ids.detectors.gps_spoofing_detector import GPSSpoofingDetector
from drone_ids.detectors.mavlink_anomaly_detector import MAVLinkAnomalyDetector
from drone_ids.detectors.command_injection_detector import CommandInjectionDetector
from drone_ids.detectors.telemetry_manipulation_detector import TelemetryManipulationDetector
from drone_ids.detectors.dos_detector import DoSDetector
from drone_ids.detectors.firmware_integrity_detector import FirmwareIntegrityDetector
from drone_ids.alerting.alert_manager import AlertManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('drone_ids.attack_direct')

def get_time_ms():
    return int(time.time() * 1000) & 0xFFFFFFFF

def inject_message(msg_dict):
    """Inject a message directly into the IDS message bus."""
    msg = Message(
        type=MessageType.MAVLINK_MESSAGE,
        source="attack_simulator",
        data=msg_dict
    )
    message_bus.publish(msg)
    logger.debug("Injected: " + msg_dict.get('type', 'UNKNOWN'))

def inject_gps_spoofing():
    print("\n" + "="*60)
    print("ATTACK 1: GPS SPOOFING (Position Jump + Impossible Velocity)")
    print("="*60)
    
    for i in range(5):
        inject_message({
            'type': 'GPS_RAW_INT',
            'time_usec': int(time.time() * 1e6),
            'lat': int((47.397742 + i * 0.00001) * 1e7),
            'lon': int((8.545594 + i * 0.00001) * 1e7),
            'alt': 500000,
            'eph': 100, 'epv': 150, 'vel': 500, 'cog': 0,
            'satellites_visible': 12,
            'fix_type': 3,
            'src_sys': 1, 'src_comp': 1, 'seq': i
        })
        time.sleep(0.1)
    
    print("Injecting GPS with 1km position jump...")
    for i in range(5):
        inject_message({
            'type': 'GPS_RAW_INT',
            'time_usec': int(time.time() * 1e6),
            'lat': int((47.397742 + 0.01) * 1e7),
            'lon': int((8.545594 + 0.01) * 1e7),
            'alt': 500000,
            'eph': 100, 'epv': 150, 'vel': 1000000,
            'cog': 0,
            'satellites_visible': 12,
            'fix_type': 3,
            'src_sys': 1, 'src_comp': 1, 'seq': 100 + i
        })
        time.sleep(0.1)
    time.sleep(1)

def inject_telemetry_manipulation():
    print("\n" + "="*60)
    print("ATTACK 2: TELEMETRY MANIPULATION (Impossible Attitude/Position)")
    print("="*60)
    
    print("Injecting impossible attitude rate (500 deg/s)...")
    for i in range(10):
        inject_message({
            'type': 'ATTITUDE',
            'time_usec': int(time.time() * 1e6),
            'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
            'rollspeed': 8.72,  # 500 deg/s = 8.72 rad/s - IMPOSSIBLE
            'pitchspeed': 0.0,
            'yawspeed': 0.0,
            'src_sys': 1, 'src_comp': 1, 'seq': 200 + i
        })
        time.sleep(0.05)
    time.sleep(0.5)
    
    print("Injecting impossible velocity (200 m/s)...")
    for i in range(5):
        inject_message({
            'type': 'GLOBAL_POSITION_INT',
            'time_usec': int(time.time() * 1e6),
            'lat': int(47.397742 * 1e7),
            'lon': int(8.545594 * 1e7),
            'alt': 500000,
            'relative_alt': 500000,
            'vx': 20000,  # 200 m/s = 20000 cm/s - IMPOSSIBLE
            'vy': 0, 'vz': 0,
            'hdg': 0,
            'src_sys': 1, 'src_comp': 1, 'seq': 300 + i
        })
        time.sleep(0.1)
    time.sleep(1)

def inject_command_injection():
    print("\n" + "="*60)
    print("ATTACK 3: COMMAND INJECTION & PARAMETER TAMPERING")
    print("="*60)
    
    print("Injecting commands from unauthorized source (sys=99)...")
    for cmd_id, params, name in [
        (400, [1, 0, 0, 0, 0, 0, 0], "ARM"),
        (400, [0, 0, 0, 0, 0, 0, 0], "DISARM"),
        (22, [1, 0, 0, 0, 0, 0, 0], "SET_MODE"),
        (176, [1, 0, 0, 0, 0, 0, 0], "DO_SET_HOME"),
        (21, [0, 0, 0, 0, 0, 0, 0], "PREFLIGHT_CALIBRATION"),
    ]:
        inject_message({
            'type': 'COMMAND_LONG',
            'command': cmd_id,
            'param1': params[0], 'param2': params[1], 'param3': params[2],
            'param4': params[3], 'param5': params[4], 'param6': params[5],
            'param7': params[6],
            'target_system': 1, 'target_component': 1,
            'src_sys': 99,  # UNAUTHORIZED SOURCE!
            'src_comp': 1,
            'seq': 400
        })
        print("  Injected " + name + " from unauthorized source sys=99")
        time.sleep(0.3)
    
    print("\nTampering critical parameters...")
    for param, value in [("SYSID_THISMAV", 999), ("ARMING_CHECK", 0), 
                          ("FS_GCS_ENABLE", 0), ("GPS_TYPE", 99)]:
        inject_message({
            'type': 'PARAM_VALUE',
            'param_id': param,
            'param_value': float(value),
            'param_type': 9,
            'param_count': 1, 'param_index': 0,
            'src_sys': 1, 'src_comp': 1, 'seq': 500
        })
        print("  Set " + param + " = " + str(value))
        time.sleep(0.2)
    time.sleep(1)

def inject_dos_flood():
    print("\n" + "="*60)
    print("ATTACK 4: DoS - MESSAGE FLOOD (>500 msg/s)")
    print("="*60)
    
    print("Flooding with 600 messages in <1 second...")
    start = time.time()
    for i in range(600):
        inject_message({
            'type': 'PARAM_REQUEST_READ',
            'target_system': 1, 'target_component': 1,
            'param_id': ("FLOOD_" + str(i)).encode(),
            'param_index': -1,
            'src_sys': 1, 'src_comp': 1, 'seq': 600 + i
        })
    elapsed = time.time() - start
    rate = 600 / elapsed
    print("  Sent 600 messages in " + "{:.3f}".format(elapsed) + "s = " + "{:.0f}".format(rate) + " msg/s")
    time.sleep(1)

def inject_sequence_gaps():
    print("\n" + "="*60)
    print("ATTACK 5: MAVLink SEQUENCE GAPS")
    print("="*60)
    
    print("Causing sequence gaps...")
    for i in range(50):
        inject_message({
            'type': 'STATUSTEXT',
            'severity': 6,
            'text': ("GAP_TEST_" + str(i)).encode(),
            'src_sys': 1, 'src_comp': 1, 'seq': 700 + i
        })
    time.sleep(0.1)
    print("  Caused sequence gap by abrupt stop")
    time.sleep(1)

def inject_firmware_tampering():
    print("\n" + "="*60)
    print("ATTACK 6: FIRMWARE INTEGRITY - PARAM INTEGRITY VIOLATION")
    print("="*60)
    
    inject_message({
        'type': 'PARAM_VALUE',
        'param_id': 'SYSID_THISMAV',
        'param_value': 999.0,
        'param_type': 9,
        'param_count': 1, 'param_index': 0,
        'src_sys': 1, 'src_comp': 1, 'seq': 800
    })
    print("  Simulated param integrity violation")
    time.sleep(1)

def run_all_attacks():
    print("\n" + "#"*60)
    print("# DRONE IDS - DIRECT INJECTION ATTACK DEMONSTRATION")
    print("#"*60)
    
    print("\nWaiting 3s for baseline learning...")
    time.sleep(3)
    
    inject_gps_spoofing()
    inject_telemetry_manipulation()
    inject_command_injection()
    inject_dos_flood()
    inject_sequence_gaps()
    inject_firmware_tampering()
    
    print("\n" + "#"*60)
    print("# DEMONSTRATION COMPLETE - ALL 6 ATTACK TYPES INJECTED")
    print("#"*60)

def main():
    print("="*60)
    print("DIRECT INJECTION ATTACK SIMULATOR")
    print("Injects attacks DIRECTLY into IDS message bus")
    print("="*60)
    
    config.load()
    
    from drone_ids.detectors.gps_spoofing_detector import GPSSpoofingDetector
    from drone_ids.detectors.mavlink_anomaly_detector import MAVLinkAnomalyDetector
    from drone_ids.detectors.command_injection_detector import CommandInjectionDetector
    from drone_ids.detectors.telemetry_manipulation_detector import TelemetryManipulationDetector
    from drone_ids.detectors.dos_detector import DoSDetector
    from drone_ids.detectors.firmware_integrity_detector import FirmwareIntegrityDetector
    from drone_ids.alerting.alert_manager import AlertManager
    
    print("Initializing IDS engine and detectors...")
    
    detectors = [
        GPSSpoofingDetector(),
        MAVLinkAnomalyDetector(),
        CommandInjectionDetector(),
        TelemetryManipulationDetector(),
        DoSDetector(),
        FirmwareIntegrityDetector()
    ]
    
    for d in detectors:
        engine.add_detector(d)
        print("  Registered: " + d.name)
    
    alert_mgr = AlertManager()
    alert_mgr.start()
    engine.start()
    
    print("\nIDS Engine started. Waiting 3s for baseline learning...")
    time.sleep(3)
    
    print("\n" + "="*60)
    print("STARTING DIRECT ATTACK INJECTION")
    print("="*60)
    
    try:
        run_all_attacks()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        print("\nShutting down...")
        engine.stop()
        alert_mgr.stop()
        print("Done.")

if __name__ == '__main__':
    main()
