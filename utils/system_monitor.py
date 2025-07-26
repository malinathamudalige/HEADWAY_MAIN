# utils/system_monitor.py
import psutil
import time
import os
import datetime
from pymongo import MongoClient
from bson import ObjectId
import logging
from collections import deque
import threading
import json


class SystemMonitor:
    def __init__(self, mongo_uri=None, db_name=None):
        self.start_time = time.time()
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.active_sessions = {}
        self.system_logs = deque(maxlen=1000)  # Keep last 1000 logs
        self.setup_logging()

    def setup_logging(self):
        """Setup logging to capture system events"""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system.log'),
                logging.StreamHandler()
            ]
        )

        # Custom handler to capture logs for dashboard
        class DashboardLogHandler(logging.Handler):
            def __init__(self, system_monitor):
                super().__init__()
                self.system_monitor = system_monitor

            def emit(self, record):
                log_entry = {
                    'timestamp': datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'module': record.module.upper(),
                    'message': record.getMessage(),
                    'ip': '127.0.0.1'  # Default to localhost, can be enhanced
                }
                self.system_monitor.system_logs.append(log_entry)

        # Add custom handler
        dashboard_handler = DashboardLogHandler(self)
        logging.getLogger().addHandler(dashboard_handler)

    def get_system_uptime(self):
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600
            uptime_days = uptime_hours / 24

            if uptime_days >= 1:
                return f"{uptime_days:.1f} days"
            else:
                return f"{uptime_hours:.1f} hours"
        except:
            return "Unknown"

    def get_app_uptime(self):
        """Get Flask application uptime"""
        app_uptime_seconds = time.time() - self.start_time
        uptime_hours = app_uptime_seconds / 3600

        if uptime_hours >= 24:
            uptime_days = uptime_hours / 24
            return f"{uptime_days:.1f} days"
        elif uptime_hours >= 1:
            return f"{uptime_hours:.1f} hours"
        else:
            uptime_minutes = app_uptime_seconds / 60
            return f"{uptime_minutes:.1f} minutes"

    def get_cpu_usage(self):
        """Get CPU usage percentage"""
        try:
            return f"{psutil.cpu_percent(interval=1):.1f}%"
        except:
            return "Unknown"

    def get_memory_usage(self):
        """Get memory usage details"""
        try:
            memory = psutil.virtual_memory()
            return {
                'percent': f"{memory.percent:.1f}%",
                'used': f"{memory.used / (1024 ** 3):.1f} GB",
                'total': f"{memory.total / (1024 ** 3):.1f} GB",
                'available': f"{memory.available / (1024 ** 3):.1f} GB"
            }
        except:
            return {
                'percent': "Unknown",
                'used': "Unknown",
                'total': "Unknown",
                'available': "Unknown"
            }

    def get_disk_usage(self):
        """Get disk usage for the current directory"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'percent': f"{(disk.used / disk.total) * 100:.1f}%",
                'used': f"{disk.used / (1024 ** 3):.1f} GB",
                'total': f"{disk.total / (1024 ** 3):.1f} GB",
                'free': f"{disk.free / (1024 ** 3):.1f} GB"
            }
        except:
            return {
                'percent': "Unknown",
                'used': "Unknown",
                'total': "Unknown",
                'free': "Unknown"
            }

    def get_network_stats(self):
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': f"{net_io.bytes_sent / (1024 ** 2):.1f} MB",
                'bytes_recv': f"{net_io.bytes_recv / (1024 ** 2):.1f} MB",
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except:
            return {
                'bytes_sent': "Unknown",
                'bytes_recv': "Unknown",
                'packets_sent': "Unknown",
                'packets_recv': "Unknown"
            }

    def get_database_stats(self):
        """Get MongoDB database statistics"""
        try:
            if not self.mongo_uri or not self.db_name:
                return {
                    'size': "Not configured",
                    'collections': "Unknown",
                    'documents': "Unknown"
                }

            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            stats = db.command("dbstats")

            return {
                'size': f"{stats['dataSize'] / (1024 ** 2):.1f} MB",
                'collections': stats['collections'],
                'documents': stats['objects'],
                'indexes': stats['indexes'],
                'storage_size': f"{stats['storageSize'] / (1024 ** 2):.1f} MB"
            }
        except Exception as e:
            logging.error(f"Failed to get database stats: {e}")
            return {
                'size': "Error",
                'collections': "Error",
                'documents': "Error"
            }

    def get_process_info(self):
        """Get current process information"""
        try:
            process = psutil.Process()
            return {
                'pid': process.pid,
                'memory_percent': f"{process.memory_percent():.1f}%",
                'cpu_percent': f"{process.cpu_percent():.1f}%",
                'threads': process.num_threads(),
                'connections': len(process.connections()),
                'create_time': datetime.datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')
            }
        except:
            return {
                'pid': "Unknown",
                'memory_percent': "Unknown",
                'cpu_percent': "Unknown",
                'threads': "Unknown",
                'connections': "Unknown",
                'create_time': "Unknown"
            }

    def track_session(self, session_id, user_id, ip_address=None):
        """Track active session"""
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'ip_address': ip_address or '127.0.0.1',
            'start_time': datetime.datetime.now(),
            'last_activity': datetime.datetime.now()
        }
        logging.info(f"Session started: {session_id} for user {user_id}")

    def update_session_activity(self, session_id):
        """Update session last activity"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_activity'] = datetime.datetime.now()

    def remove_session(self, session_id):
        """Remove session"""
        if session_id in self.active_sessions:
            user_id = self.active_sessions[session_id]['user_id']
            del self.active_sessions[session_id]
            logging.info(f"Session ended: {session_id} for user {user_id}")

    def cleanup_inactive_sessions(self, timeout_minutes=30):
        """Remove inactive sessions"""
        current_time = datetime.datetime.now()
        inactive_sessions = []

        for session_id, session_data in self.active_sessions.items():
            last_activity = session_data['last_activity']
            if (current_time - last_activity).total_seconds() > (timeout_minutes * 60):
                inactive_sessions.append(session_id)

        for session_id in inactive_sessions:
            self.remove_session(session_id)

        return len(inactive_sessions)

    def get_active_sessions(self):
        """Get active sessions count and details"""
        self.cleanup_inactive_sessions()
        return {
            'count': len(self.active_sessions),
            'sessions': list(self.active_sessions.values())
        }

    def get_system_metrics(self):
        """Get comprehensive system metrics"""
        memory = self.get_memory_usage()
        disk = self.get_disk_usage()
        network = self.get_network_stats()
        database = self.get_database_stats()
        process = self.get_process_info()
        sessions = self.get_active_sessions()

        return {
            'system_uptime': self.get_system_uptime(),
            'app_uptime': self.get_app_uptime(),
            'cpu_usage': self.get_cpu_usage(),
            'memory_usage': memory['percent'],
            'memory_details': memory,
            'disk_usage': disk['percent'],
            'disk_details': disk,
            'network_stats': network,
            'database_stats': database,
            'process_info': process,
            'active_sessions': sessions['count'],
            'session_details': sessions['sessions']
        }

    def get_recent_logs(self, limit=50):
        """Get recent system logs"""
        return list(self.system_logs)[-limit:]

    def log_system_event(self, level, module, message, ip='127.0.0.1'):
        """Log a system event"""
        if level.upper() == 'INFO':
            logging.info(f"{module}: {message}")
        elif level.upper() == 'WARNING':
            logging.warning(f"{module}: {message}")
        elif level.upper() == 'ERROR':
            logging.error(f"{module}: {message}")
        else:
            logging.info(f"{module}: {message}")


# Global system monitor instance
system_monitor = None


def initialize_system_monitor(mongo_uri=None, db_name=None):
    """Initialize the global system monitor"""
    global system_monitor
    system_monitor = SystemMonitor(mongo_uri, db_name)
    return system_monitor


def get_system_monitor():
    """Get the global system monitor instance"""
    global system_monitor
    if system_monitor is None:
        system_monitor = SystemMonitor()
    return system_monitor