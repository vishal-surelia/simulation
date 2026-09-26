"""Integration test for detection capabilities."""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_gps_spoofing_detection():
    """Test GPS spoofing detection with simulated messages."""
    from drone_ids.core.config import config
    from drone_ids.core.ids_engine import engine
    from drone_ids.core.message_bus import message_bus, Message, MessageType
    from drone_ids.detectors.gps_spoofing_detector import GPSSpoofingDetector
    from drone_ids.alerting.alert_manager import AlertManager
    
    config.load()
    
    # Create detector
    gps_detector = GPSSpoofingDetector()
    engine.add_detector(gps_detector)
    
    # Capture alerts
    alerts = []
    def capture_alert(msg):
        alerts.append(msg.data)
    
    message_bus.subscribe(MessageType.ALERT, capture_alert)
    
    # Start engine
    engine.start()
    
    # Send normal GPS messages first
    base_time = time.time()
    for i in range(5):
        msg = Message(
            type=MessageType.MAVLINK_MESSAGE,
            source="test",
            data={
                'type': 'GPS_RAW_INT',
                'lat': int((47.397742 + i * 0.0001) * 1e7),
                'lon': int((8.545594 + i * 0.0001) * 1e7),
                'alt': int((500 + i) * 1000),
                'satellites_visible': 10,
                'eph': 100,
                'epv': 150,
                'fix_type': 3,
                'time_usec': int((base_time + i) * 1e6),
                'src_sys': 1,
                'src_comp': 1,
                'seq': i
            }
        )
        message_bus.publish(msg)
        time.sleep(0.1)
    
    # Send spoofed GPS (large position jump)
    spoofed_msg = Message(
        type=MessageType.MAVLINK_MESSAGE,
        source="test",
        data={
            'type': 'GPS_RAW_INT',
            'lat': int((47.397742 + 0.01) * 1e7),  # ~1km jump
            'lon': int((8.545594 + 0.01) * 1e7),
            'alt': int(500 * 1000),
            'satellites_visible': 10,
            'eph': 100,
            'epv': 150,
            'fix_type': 3,
            'time_usec': int((base_time + 5) * 1e6),
            'src_sys': 1,
            'src_comp': 1,
            'seq': 5
        }
    )
    message_bus.publish(spoofed_msg)
    time.sleep(0.5)
    
    # Check alerts
    gps_alerts = [a for a in alerts if 'gps' in a.get('alert_type', '').lower() or 'position' in a.get('alert_type', '').lower()]
    
    engine.stop()
    
    print(f"Total alerts: {len(alerts)}")
    print(f"GPS alerts: {len(gps_alerts)}")
    for a in gps_alerts:
        print(f"  - {a.get('alert_type')}: {a.get('description')}")
    
    # Should detect position jump
    assert len(gps_alerts) > 0, "Should detect GPS position jump"
    print("✓ GPS spoofing detection test passed")


def test_command_injection_detection():
    """Test command injection detection."""
    from drone_ids.core.config import config
    from drone_ids.core.ids_engine import engine
    from drone_ids.core.message_bus import message_bus, Message, MessageType
    from drone_ids.detectors.command_injection_detector import CommandInjectionDetector
    
    # Create new engine instance for clean test
    from drone_ids.core.ids_engine import IDSEngine
    test_engine = IDSEngine()
    
    cmd_detector = CommandInjectionDetector()
    test_engine.add_detector(cmd_detector)
    
    alerts = []
    def capture_alert(msg):
        alerts.append(msg.data)
    
    message_bus.subscribe(MessageType.ALERT, capture_alert)
    
    test_engine.start()
    
    # Send command from unauthorized source
    cmd_msg = Message(
        type=MessageType.MAVLINK_MESSAGE,
        source="test",
        data={
            'type': 'COMMAND_LONG',
            'command': 400,  # ARM
            'param1': 1,
            'src_sys': 99,  # Unauthorized source
            'src_comp': 1,
            'seq': 1
        }
    )
    message_bus.publish(cmd_msg)
    time.sleep(0.2)
    
    # Check alerts
    cmd_alerts = [a for a in alerts if 'command' in a.get('alert_type', '').lower() or 'unauthorized' in a.get('alert_type', '').lower()]
    
    test_engine.stop()
    
    print(f"Total alerts: {len(alerts)}")
    print(f"Command alerts: {len(cmd_alerts)}")
    for a in cmd_alerts:
        print(f"  - {a.get('alert_type')}: {a.get('description')}")
    
    assert len(cmd_alerts) > 0, "Should detect unauthorized command source"
    print("✓ Command injection detection test passed")


if __name__ == '__main__':
    test_gps_spoofing_detection()
    test_command_injection_detection()
    print("\n✅ All detection tests passed!")