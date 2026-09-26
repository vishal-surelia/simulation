"""
Drone IDS - MAVLink Interface (Part 1)
"""
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

try:
    from pymavlink import mavutil
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False
    mavutil = None

from ..core.message_bus import message_bus, Message, MessageType
from ..core.config import config


@dataclass
class ConnectionStatus:
    connected: bool = False
    last_heartbeat: float = 0
    messages_received: int = 0
    messages_sent: int = 0
    errors: int = 0
    link_quality: float = 0.0


class MAVLinkInterface:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or config.get('sitl.connection_string')
        self.source_system = config.get('sitl.source_system', 255)
        self.source_component = config.get('sitl.source_component', 190)
        
        self.master = None
        self.status = ConnectionStatus()
        self._running = False
        self._receive_thread = None
        self._heartbeat_thread = None
        self._message_callback = None
        
        self.logger = logging.getLogger('drone_ids.mavlink')
        self.logger.setLevel(logging.INFO)
    
    def connect(self) -> bool:
        if not MAVLINK_AVAILABLE:
            self.logger.error("pymavlink not available. Install: pip install pymavlink")
            return False
        
        try:
            self.logger.info(f"Connecting to {self.connection_string}...")
            self.master = mavutil.mavlink_connection(
                self.connection_string,
                source_system=self.source_system,
                source_component=self.source_component,
                autoreconnect=True
            )
            
            self.logger.info("Waiting for heartbeat...")
            self.master.wait_heartbeat(timeout=config.get('sitl.heartbeat_timeout', 5.0))
            
            self.status.connected = True
            self.status.last_heartbeat = time.time()
            self.logger.info(f"Connected to system {self.master.target_system}")
            
            self._running = True
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.status.errors += 1
            return False
    
    def disconnect(self) -> None:
        self._running = False
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=2.0)
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)
        if self.master:
            self.master.close()
            self.master = None
        self.status.connected = False
        self.logger.info("Disconnected")
    
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._message_callback = callback
    
    def _receive_loop(self) -> None:
        while self._running and self.master:
            try:
                msg = self.master.recv_match(blocking=True, timeout=1.0)
                if msg:
                    self._process_message(msg)
            except Exception as e:
                self.logger.error(f"Receive error: {e}")
                self.status.errors += 1
                time.sleep(0.1)
    
    def _process_message(self, msg) -> None:
        self.status.messages_received += 1
        self.status.last_heartbeat = time.time()
        
        msg_dict = msg.to_dict()
        msg_dict['type'] = msg.get_type()
        msg_dict['src_sys'] = msg.get_srcSystem()
        msg_dict['src_comp'] = msg.get_srcComponent()
        msg_dict['seq'] = msg.get_seq()
        
        message_bus.publish(Message(
            type=MessageType.MAVLINK_MESSAGE,
            source="mavlink_interface",
            data=msg_dict
        ))
        
        if self._message_callback:
            try:
                self._message_callback(msg_dict)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def _heartbeat_loop(self) -> None:
        while self._running and self.master:
            try:
                self.master.mav.heartbeat_send(
                    mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                    0, 0, 0
                )
                self.status.messages_sent += 1
                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                self.status.errors += 1
                time.sleep(1.0)
    
    def send_command(self, command: int, params: list = None,
                     target_system: int = None, target_component: int = 1,
                     confirmation: int = 0) -> bool:
        if not self.master or not self.status.connected:
            return False
        try:
            params = params or [0]*7
            self.master.mav.command_long_send(
                target_system or self.master.target_system,
                target_component,
                command,
                confirmation,
                *params
            )
            self.status.messages_sent += 1
            return True
        except Exception as e:
            self.logger.error(f"Command send error: {e}")
            return False
    
    def request_data_stream(self, stream_id: int, rate: int = 10) -> bool:
        if not self.master:
            return False
        try:
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                stream_id,
                rate,
                1
            )
            return True
        except Exception as e:
            self.logger.error(f"Data stream request error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'connected': self.status.connected,
            'last_heartbeat': self.status.last_heartbeat,
            'messages_received': self.status.messages_received,
            'messages_sent': self.status.messages_sent,
            'errors': self.status.errors,
            'connection_string': self.connection_string
        }