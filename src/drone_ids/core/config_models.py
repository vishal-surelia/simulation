"""
Drone IDS - Configuration Data Models
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SITLConfig:
    connection_string: str = "udp:127.0.0.1:14550"
    heartbeat_timeout: float = 5.0
    reconnect_attempts: int = 3
    reconnect_delay: float = 2.0
    source_system: int = 255
    source_component: int = 190


@dataclass
class EngineConfig:
    processing_interval: float = 0.1
    message_buffer_size: int = 10000
    alert_cooldown: float = 1.0
    max_alerts_per_second: int = 50
    enable_statistics: bool = True
    statistics_interval: float = 30.0


@dataclass
class GPSSpoofingConfig:
    enabled: bool = True
    max_position_jump_meters: float = 50.0
    max_velocity_mps: float = 100.0
    min_satellites: int = 6
    max_hdop: float = 5.0
    max_vdop: float = 5.0
    enable_imu_cross_check: bool = True
    max_imu_gps_discrepancy_meters: float = 10.0
    innovation_threshold: float = 3.0
    check_absolute_timing: bool = True
    check_relative_timing: bool = True
    check_signal_power_consistency: bool = True


@dataclass
class MAVLinkAnomalyConfig:
    enabled: bool = True
    learning_window: int = 300
    rate_deviation_threshold: float = 3.0
    max_sequence_gap: int = 10
    enable_sequence_check: bool = True
    monitored_message_types: List[str] = None
    enable_payload_analysis: bool = True
    payload_anomaly_threshold: float = 0.95
    
    def __post_init__(self):
        if self.monitored_message_types is None:
            self.monitored_message_types = [
                "HEARTBEAT", "SYS_STATUS", "ATTITUDE", "GLOBAL_POSITION_INT",
                "GPS_RAW_INT", "VFR_HUD", "COMMAND_ACK", "MISSION_ITEM",
                "PARAM_VALUE", "STATUSTEXT"
            ]


@dataclass
class CommandInjectionConfig:
    enabled: bool = True
    allowed_command_sources: List[int] = None
    blocked_commands: List[int] = None
    max_commands_per_second: int = 20
    command_burst_threshold: int = 50
    monitor_param_changes: bool = True
    critical_params: List[str] = None
    validate_mission_items: bool = True
    max_waypoint_distance_km: float = 100.0
    expect_command_ack: bool = True
    ack_timeout: float = 5.0
    
    def __post_init__(self):
        if self.allowed_command_sources is None:
            self.allowed_command_sources = [1, 255]
        if self.blocked_commands is None:
            self.blocked_commands = []
        if self.critical_params is None:
            self.critical_params = [
                "SYSID_THISMAV", "SYSID_MYGCS", "ARMING_CHECK",
                "FS_GCS_ENABLE", "FS_EKF_THRESH", "GPS_TYPE", "EK2_ENABLE"
            ]


@dataclass
class TelemetryManipulationConfig:
    enabled: bool = True
    max_attitude_rate_dps: float = 300.0
    max_acceleration_g: float = 10.0
    max_position_rate_mps: float = 100.0
    max_velocity_change_mps2: float = 50.0
    enable_baro_gps_cross_check: bool = True
    max_altitude_discrepancy_meters: float = 20.0
    enable_compass_cross_check: bool = True
    max_heading_discrepancy_deg: float = 30.0
    monitor_power_system: bool = True
    max_voltage_jump_v: float = 2.0
    max_current_jump_a: float = 10.0
    check_message_crc: bool = True
    check_signatures: bool = True


@dataclass
class DoSConfig:
    enabled: bool = True
    monitor_link_quality: bool = True
    min_rssi_dbm: float = -90.0
    max_packet_loss_percent: float = 10.0
    max_messages_per_second: int = 500
    flood_window: float = 1.0
    heartbeat_timeout: float = 3.0
    max_heartbeat_interval: float = 2.0
    monitor_cpu_memory: bool = True
    max_cpu_percent: float = 90.0
    max_memory_percent: float = 85.0
    detect_jamming: bool = True
    rssi_drop_threshold_dbm: float = 20.0
    snr_drop_threshold_db: float = 15.0


@dataclass
class FirmwareIntegrityConfig:
    enabled: bool = True
    verify_boot_hash: bool = True
    expected_firmware_hash: str = ""
    monitor_param_integrity: bool = True
    critical_param_hashes: Dict[str, str] = None
    detect_memory_corruption: bool = True
    check_stack_canaries: bool = False
    monitor_unexpected_reboots: bool = True
    max_reboots_per_hour: int = 2
    verify_secure_boot: bool = False
    
    def __post_init__(self):
        if self.critical_param_hashes is None:
            self.critical_param_hashes = {}


@dataclass
class AlertingConfig:
    console_output: bool = True
    file_output: bool = True
    syslog_output: bool = False
    network_output: bool = False
    alert_log_path: str = "logs/alerts.log"
    evidence_log_path: str = "logs/evidence.log"
    max_log_size_mb: int = 100
    max_log_files: int = 10
    include_timestamp: bool = True
    include_gps_location: bool = True
    include_message_raw: bool = False
    min_severity_console: str = "WARNING"
    min_severity_file: str = "INFO"
    network_host: str = "127.0.0.1"
    network_port: int = 5140
    network_protocol: str = "UDP"


@dataclass
class StorageConfig:
    database_path: str = "data/ids.db"
    evidence_retention_days: int = 90
    alert_retention_days: int = 365
    statistics_retention_days: int = 30
    enable_compression: bool = True
    backup_interval_hours: int = 24


@dataclass
class ReportingConfig:
    generate_periodic_reports: bool = True
    report_interval_hours: int = 24
    report_output_dir: str = "reports/"
    include_charts: bool = True
    executive_summary: bool = True


@dataclass
class ForensicsConfig:
    enable_hash_chaining: bool = True
    hash_algorithm: str = "SHA256"
    sign_evidence: bool = False
    evidence_encryption: bool = False
    chain_of_custody_log: str = "logs/chain_of_custody.log"