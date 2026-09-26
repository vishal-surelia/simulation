#!/usr/bin/env python3
"""
Drone IDS - Attack Script
Sends attack messages directly to IDS injection port (UDP 14551)
Run this AFTER starting the IDS with: python run_ids.py
"""
import sys
import time
import json
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from drone_ids.core.config import config

def get_time_ms():
    return int(time.time() * 1000) & 0xFFFFFFFF

class AttackSender:
    def __init__(self, host='127.0.0.1', port=14551):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (host, port)
        self.seq = 0
    
    def send(self, msg_dict):
        msg_dict['seq'] = msg_dict.get('seq', self.seq)
        self.seq += 1
        data = json.dumps(msg_dict).encode('utf-8')
        self.sock.sendto(data, self.target)
    
    def close(self):
        self.sock.close()

def get_time_ms():
    return int(time.time() * 1000) & 0xFFFFFFFF

def run_all_attacks(sender):
    print("="*60)
    print("# DRONE IDS - ATTACK DEMONSTRATION (6 ATTACK TYPES)")
    print("="*60)
    
    print("\nWaiting 3s for IDS baseline learning...")
    time.sleep(3)
    
    # ATTACK 1: GPS SPOOFING
    print("\n" + "="*60)
    print("ATTACK 1: GPS SPOOFING (Position Jump + Impossible Velocity)")
    print("="*60)
    
    for i in range(5):
        send_gps(sender, 47.397742 + i*0.00001, 8.545594 + i*0.00001, 500000, 12, 3)
        time.sleep(0.1)
    
    print("Injecting GPS with 1km position jump & 1000 m/s velocity...")
    for i in range(5):
        send_gps(sender, 47.397742 + 0.01, 8.545594 + 0.01, 500000, 12, 3, 1000000)
        time.sleep(0.1)
    time.sleep(1)
    
    # ATTACK 2: TELEMETRY MANIPULATION
    print("\n" + "="*60)
    print("ATTACK 2: TELEMETRY MANIPULATION (Impossible Attitude/Position)")
    print("="*60)
    
    print("Injecting impossible attitude rate (500 deg/s)...")
    for i in range(10):
        send_attitude(sender, 0.0, 0.0, 0.0, 8.72, 0.0, 0.0)
        time.sleep(0.05)
    time.sleep(0.5)
    
    print("Injecting impossible velocity (200 m/s)...")
    for i in range(5):
        send_position(sender, 47.397742, 8.545594, 500000, 20000, 0, 0)
        time.sleep(0.1)
    time.sleep(1)
    
    # ATTACK 3: COMMAND INJECTION & PARAMETER TAMPERING
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
        send_command(sender, cmd_id, params, 99)
        print(f"  Injected {name} from unauthorized source sys=99")
        time.sleep(0.3)
    
    print("\nTampering critical parameters...")
    for param, value in [("SYSID_THISMAV", 999), ("ARMING_CHECK", 0), ("FS_GCS_ENABLE", 0), ("GPS_TYPE", 99)]:
        send_param(sender, param, value)
        print(f"  Set {param} = {value}")
        time.sleep(0.2)
    time.sleep(1)
    
    # ATTACK 4: DoS FLOOD
    print("\n" + "="*60)
    print("ATTACK 4: DoS - MESSAGE FLOOD (>500 msg/s)")
    print("="*60)
    
    print("Flooding with 600 messages in <1 second...")
    start = time.time()
    for i in range(600):
        send_param_request(sender, f"FLOOD_{i}")
    elapsed = time.time() - start
    rate = 600 / elapsed
    print(f"  Sent 600 messages in {elapsed:.3f}s = {rate:.0f} msg/s")
    time.sleep(1)
    
    # ATTACK 5: SEQUENCE GAPS
    print("\n" + "="*60)
    print("ATTACK 5: MAVLink SEQUENCE GAPS")
    print("="*60)
    
    print("Causing sequence gaps...")
    for i in range(50):
        send_statustext(sender, f"GAP_TEST_{i}")
    time.sleep(0.1)
    print("  Caused sequence gap by abrupt stop")
    time.sleep(1)
    
    # ATTACK 6: FIRMWARE INTEGRITY
    print("\n" + "="*60)
    print("ATTACK 6: FIRMWARE INTEGRITY - PARAM INTEGRITY VIOLATION")
    print("="*60)
    
    send_param_value(sender, "SYSID_THISMAV", 999.0)
    print("  Simulated param integrity violation")
    time.sleep(1)
    
    print("\n" + "#"*60)
    print("# DEMONSTRATION COMPLETE - ALL 6 ATTACK TYPES INJECTED")
    print("#"*60)

def send_gps(sender, lat, lon, alt, sats, fix_type, vel=0):
    sender.send({
        'type': 'GPS_RAW_INT',
        'time_usec': int(time.time() * 1e6),
        'lat': int(lat * 1e7),
        'lon': int(lon * 1e7),
        'alt': alt * 1000,
        'eph': 100, 'epv': 150, 'vel': int(vel * 100), 'cog': 0,
        'satellites_visible': sats,
        'fix_type': fix_type,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.1)

def send_attitude(sender, roll, pitch, yaw, rollspeed, pitchspeed, yawspeed):
    sender.send({
        'type': 'ATTITUDE',
        'time_usec': int(time.time() * 1e6),
        'roll': roll, 'pitch': pitch, 'yaw': yaw,
        'rollspeed': rollspeed, 'pitchspeed': pitchspeed, 'yawspeed': yawspeed,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.05)

def send_position(sender, lat, lon, alt, vx, vy, vz):
    sender.send({
        'type': 'GLOBAL_POSITION_INT',
        'time_usec': int(time.time() * 1e6),
        'lat': int(lat * 1e7), 'lon': int(lon * 1e7),
        'alt': alt * 1000, 'relative_alt': alt * 1000,
        'vx': int(vx * 100), 'vy': int(vy * 100), 'vz': int(vz * 100),
        'hdg': 0,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.1)

def send_command(sender, cmd_id, params, src_sys=99):
    sender.send({
        'type': 'COMMAND_LONG',
        'command': cmd_id,
        'param1': params[0], 'param2': params[1], 'param3': params[2],
        'param4': params[3], 'param5': params[4], 'param6': params[5],
        'param7': params[6],
        'target_system': 1, 'target_component': 1,
        'src_sys': src_sys, 'src_comp': 1
    })
    print(f"  Injected {params[6]} from unauthorized source sys={src_sys}")
    time.sleep(0.3)

def send_param(sender, param, value):
    sender.send({
        'type': 'PARAM_VALUE',
        'param_id': param,
        'param_value': float(value),
        'param_type': 9,
        'param_count': 1, 'param_index': 0,
        'src_sys': 1, 'src_comp': 1
    })
    print(f"  Set {param} = {value}")
    time.sleep(0.2)

def send_param_request(sender, param_name):
    sender.send({
        'type': 'PARAM_REQUEST_READ',
        'target_system': 1, 'target_component': 1,
        'param_id': param_name,
        'param_index': -1,
        'src_sys': 1, 'src_comp': 1
    })

def send_statustext(sender, text):
    sender.send({
        'type': 'STATUSTEXT',
        'severity': 6,
        'text': text,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.02)

def send_param_value(sender, param, value):
    sender.send({
        'type': 'PARAM_VALUE',
        'param_id': param,
        'param_value': float(value),
        'param_type': 9,
        'param_count': 1, 'param_index': 0,
        'src_sys': 1, 'src_comp': 1
    })
    print(f"  Set {param} = {value}")
    time.sleep(0.2)

def send_statustext(sender, text):
    sender.send({
        'type': 'STATUSTEXT',
        'severity': 6,
        'text': text,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.02)

def run_all_attacks(sender):
    print("="*60)
    print("# DRONE IDS - ATTACK DEMONSTRATION (6 ATTACK TYPES)")
    print("="*60)
    
    print("\nWaiting 3s for IDS baseline learning...")
    time.sleep(3)
    
    # ATTACK 1: GPS SPOOFING
    print("\n" + "="*60)
    print("ATTACK 1: GPS SPOOFING (Position Jump + Impossible Velocity)")
    print("="*60)
    
    for i in range(5):
        send_gps(sender, 47.397742 + i*0.00001, 8.545594 + i*0.00001, 500000, 12, 3)
        time.sleep(0.1)
    
    print("Injecting GPS with 1km position jump & 1000 m/s velocity...")
    for i in range(5):
        send_gps(sender, 47.397742 + 0.01, 8.545594 + 0.01, 500000, 12, 3, 1000000)
        time.sleep(0.1)
    time.sleep(1)
    
    # ATTACK 2: TELEMETRY MANIPULATION
    print("\n" + "="*60)
    print("ATTACK 2: TELEMETRY MANIPULATION (Impossible Attitude/Position)")
    print("="*60)
    
    print("Injecting impossible attitude rate (500 deg/s)...")
    for i in range(10):
        send_attitude(sender, 0.0, 0.0, 0.0, 8.72, 0.0, 0.0)
        time.sleep(0.05)
    time.sleep(0.5)
    
    print("Injecting impossible velocity (200 m/s)...")
    for i in range(5):
        send_position(sender, 47.397742, 8.545594, 500000, 20000, 0, 0)
        time.sleep(0.1)
    time.sleep(1)
    
    # ATTACK 3: COMMAND INJECTION & PARAMETER TAMPERING
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
        send_command(sender, cmd_id, params, 99)
        print(f"  Injected {name}")
        time.sleep(0.3)
    
    print("\nTampering critical parameters...")
    for param, value in [("SYSID_THISMAV", 999), ("ARMING_CHECK", 0), ("FS_GCS_ENABLE", 0), ("GPS_TYPE", 99)]:
        send_param(sender, param, value)
        print(f"  Setting {param} = {value}")
        time.sleep(0.2)
    time.sleep(1)
    
    # ATTACK 4: DoS FLOOD
    print("\n" + "="*60)
    print("ATTACK 4: DoS - MESSAGE FLOOD (>500 msg/s)")
    print("="*60)
    
    print("Flooding with 600 messages in <1 second...")
    start = time.time()
    for i in range(600):
        send_param_request(sender, f"FLOOD_{i}")
    elapsed = time.time() - start
    rate = 600 / elapsed
    print(f"  Sent 600 messages in {elapsed:.3f}s = {rate:.0f} msg/s")
    time.sleep(1)
    
    # ATTACK 5: SEQUENCE GAPS
    print("\n" + "="*60)
    print("ATTACK 5: MAVLink SEQUENCE GAPS")
    print("="*60)
    
    print("Causing sequence gaps...")
    for i in range(50):
        send_statustext(sender, f"GAP_TEST_{i}")
    time.sleep(0.1)
    print("  Caused sequence gap by abrupt stop")
    time.sleep(1)
    
    # ATTACK 6: FIRMWARE INTEGRITY
    print("\n" + "="*60)
    print("ATTACK 6: FIRMWARE INTEGRITY - PARAM INTEGRITY VIOLATION")
    print("="*60)
    
    send_param_value(sender, "SYSID_THISMAV", 999.0)
    print("  Simulated param integrity violation")
    time.sleep(1)
    
    print("\n" + "#"*60)
    print("# DEMONSTRATION COMPLETE - ALL 6 ATTACK TYPES INJECTED")
    print("#"*60)

def send_gps(sender, lat, lon, alt, sats, fix_type, vel=0):
    sender.send({
        'type': 'GPS_RAW_INT',
        'time_usec': int(time.time() * 1e6),
        'lat': int(lat * 1e7),
        'lon': int(lon * 1e7),
        'alt': alt * 1000,
        'eph': 100, 'epv': 150, 'vel': int(vel * 100), 'cog': 0,
        'satellites_visible': sats,
        'fix_type': fix_type,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.1)

def send_attitude(sender, roll, pitch, yaw, rollspeed, pitchspeed, yawspeed):
    sender.send({
        'type': 'ATTITUDE',
        'time_usec': int(time.time() * 1e6),
        'roll': roll, 'pitch': pitch, 'yaw': yaw,
        'rollspeed': rollspeed, 'pitchspeed': pitchspeed, 'yawspeed': yawspeed,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.05)

def send_position(sender, lat, lon, alt, vx, vy, vz):
    sender.send({
        'type': 'GLOBAL_POSITION_INT',
        'time_usec': int(time.time() * 1e6),
        'lat': int(lat * 1e7), 'lon': int(lon * 1e7),
        'alt': alt * 1000, 'relative_alt': alt * 1000,
        'vx': int(vx * 100), 'vy': int(vy * 100), 'vz': int(vz * 100),
        'hdg': 0,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.1)

def send_command(sender, cmd_id, params, src_sys=99):
    sender.send({
        'type': 'COMMAND_LONG',
        'command': cmd_id,
        'param1': params[0], 'param2': params[1], 'param3': params[2],
        'param4': params[3], 'param5': params[4], 'param5': params[5],
        'param6': params[6],
        'target_system': 1, 'target_component': 1,
        'src_sys': src_sys, 'src_comp': 1
    })
    print(f"  Injected {{params[6]}} from unauthorized source sys={src_sys}")
    time.sleep(0.3)

def send_param(sender, param, value):
    sender.send({
        'type': 'PARAM_VALUE',
        'param_id': param,
        'param_value': float(value),
        'param_type': 9,
        'param_count': 1, 'param_index': 0,
        'src_sys': 1, 'src_comp': 1
    })
    print(f"  Set {param} = {value}")
    time.sleep(0.2)

def send_param_request(sender, param_name):
    sender.send({
        'type': 'PARAM_REQUEST_READ',
        'target_system': 1, 'target_component': 1,
        'param_id': param_name,
        'param_index': -1,
        'src_sys': 1, 'src_comp': 1
    })

def send_statustext(sender, text):
    sender.send({
        'type': 'STATUSTEXT',
        'severity': 6,
        'text': text,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.02)

def send_param_value(sender, param, value):
    sender.send({
        'type': 'PARAM_VALUE',
        'param_id': param,
        'param_value': float(value),
        'param_type': 9,
        'param_count': 1, 'param_index': 0,
        'src_sys': 1, 'src_comp': 1
    })
    print(f"  Set {param} = {value}")
    time.sleep(0.2)

def send_statustext(sender, text):
    sender.send({
        'type': 'STATUSTEXT',
        'severity': 6,
        'text': text,
        'src_sys': 1, 'src_comp': 1
    })
    time.sleep(0.02)

def send_param_value(sender, param, value):
    sender.send({
        'type': 'PARAM_VALUE',
        'param_id': param,
        'param_value': float(value),
        'param_type': 9,
        'param_count': 1, 'param_index': 0,
        'src_sys': 1, 'src_comp': 1
    })
    print(f"  Set {param} = {value}")
    time.sleep(0.2)

def main():
    print("="*60)
    print("DRONE IDS - ATTACK INJECTOR (UDP 14551)")
    print("="*60)
    
    sender = AttackSender('127.0.0.1', 14551)
    
    print("Connecting to IDS injection port 14551...")
    print("Make sure IDS is running: python run_ids.py")
    
    try:
        run_all_attacks(sender)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        sender.close()
        print("Done.")

if __name__ == '__main__':
    main()
