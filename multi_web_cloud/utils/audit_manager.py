"""
Audit Logging and Monitoring Manager for Flask POS Application
Provides comprehensive audit logging, monitoring, and analytics
"""

import os
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from flask import request, session, g
import logging
from collections import defaultdict, deque
import hashlib

class AuditManager:
    """Comprehensive audit logging and monitoring system"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.audit_db_path = 'audit_logs.db'
        self.max_log_entries = 10000  # Maximum entries to keep in memory
        self.log_retention_days = 90  # Days to retain logs
        
        # In-memory storage for recent logs
        self.recent_logs = deque(maxlen=self.max_log_entries)
        self.log_statistics = defaultdict(int)
        self.alert_thresholds = {
            'failed_logins': 5,        # 5 failed logins in 5 minutes
            'suspicious_activity': 3,   # 3 suspicious activities in 5 minutes
            'high_value_transactions': 10000,  # Transactions above ₹10,000
            'rapid_api_calls': 100,    # 100 API calls in 1 minute
            'database_errors': 10        # 10 database errors in 5 minutes
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize audit manager with Flask app"""
        self.app = app
        self.audit_db_path = os.path.join(app.instance_path, 'audit_logs.db')
        
        # Initialize audit database
        self._init_audit_database()
        
        # Start background thread for log processing
        self._start_log_processor()
        
        self.logger.info("Audit manager initialized")
    
    def _init_audit_database(self):
        """Initialize audit logging database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            # Create audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    endpoint TEXT,
                    method TEXT,
                    details TEXT,
                    severity TEXT DEFAULT 'info',
                    risk_score INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create security events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    ip_address TEXT,
                    details TEXT,
                    severity TEXT DEFAULT 'medium',
                    action_taken TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    response_time REAL,
                    status_code INTEGER,
                    user_id INTEGER,
                    memory_usage REAL,
                    cpu_usage REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create data access log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_access_timestamp ON data_access_log(timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Audit database initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing audit database: {e}")
    
    def _start_log_processor(self):
        """Start background thread for log processing"""
        def process_logs():
            while True:
                try:
                    self._process_alerts()
                    self._cleanup_old_logs()
                    threading.Event().wait(60)  # Process every minute
                except Exception as e:
                    self.logger.error(f"Error in log processor: {e}")
                    threading.Event().wait(60)
        
        processor_thread = threading.Thread(target=process_logs, daemon=True)
        processor_thread.start()
        self.logger.info("Log processor thread started")
    
    def log_event(self, event_type: str, details: Dict[str, Any] = None, 
                  severity: str = 'info', risk_score: int = 0):
        """Log an audit event"""
        try:
            event_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': session.get('user_id'),
                'session_id': session.get('session_id'),
                'ip_address': getattr(g, 'client_ip', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', ''),
                'endpoint': request.endpoint,
                'method': request.method,
                'details': json.dumps(details) if details else None,
                'severity': severity,
                'risk_score': risk_score
            }
            
            # Add to in-memory storage
            self.recent_logs.append(event_data)
            
            # Update statistics
            self.log_statistics[event_type] += 1
            
            # Store in database
            self._store_audit_log(event_data)
            
            # Check for alerts
            self._check_alert_conditions(event_type, event_data)
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
    
    def log_security_event(self, event_type: str, details: Dict[str, Any] = None,
                         severity: str = 'medium', action_taken: str = None):
        """Log a security event"""
        try:
            security_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': session.get('user_id'),
                'ip_address': getattr(g, 'client_ip', request.remote_addr),
                'details': json.dumps(details) if details else None,
                'severity': severity,
                'action_taken': action_taken
            }
            
            # Store in database
            self._store_security_event(security_data)
            
            # Trigger immediate alert for high severity
            if severity in ['high', 'critical']:
                self._trigger_security_alert(security_data)
            
        except Exception as e:
            self.logger.error(f"Error logging security event: {e}")
    
    def log_performance_metric(self, endpoint: str, method: str, response_time: float,
                           status_code: int, memory_usage: float = None, cpu_usage: float = None):
        """Log performance metrics"""
        try:
            performance_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'response_time': response_time,
                'status_code': status_code,
                'user_id': session.get('user_id'),
                'memory_usage': memory_usage,
                'cpu_usage': cpu_usage
            }
            
            # Store in database
            self._store_performance_metric(performance_data)
            
            # Check for performance alerts
            if response_time > 5.0:  # 5 seconds threshold
                self._trigger_performance_alert({
                    'type': 'slow_response',
                    'endpoint': endpoint,
                    'response_time': response_time,
                    'threshold': 5.0
                })
            
            if status_code >= 500:
                self._trigger_performance_alert({
                    'type': 'server_error',
                    'endpoint': endpoint,
                    'status_code': status_code
                })
            
        except Exception as e:
            self.logger.error(f"Error logging performance metric: {e}")
    
    def log_data_access(self, resource_type: str, resource_id: str, action: str,
                      details: Dict[str, Any] = None):
        """Log data access events"""
        try:
            access_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': session.get('user_id'),
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'ip_address': getattr(g, 'client_ip', request.remote_addr),
                'details': json.dumps(details) if details else None
            }
            
            # Store in database
            self._store_data_access_log(access_data)
            
        except Exception as e:
            self.logger.error(f"Error logging data access: {e}")
    
    def _store_audit_log(self, event_data: Dict[str, Any]):
        """Store audit log in database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_logs 
                (timestamp, event_type, user_id, session_id, ip_address, user_agent, 
                 endpoint, method, details, severity, risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_data['timestamp'],
                event_data['event_type'],
                event_data['user_id'],
                event_data['session_id'],
                event_data['ip_address'],
                event_data['user_agent'],
                event_data['endpoint'],
                event_data['method'],
                event_data['details'],
                event_data['severity'],
                event_data['risk_score']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing audit log: {e}")
    
    def _store_security_event(self, security_data: Dict[str, Any]):
        """Store security event in database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_events 
                (timestamp, event_type, user_id, ip_address, details, severity, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                security_data['timestamp'],
                security_data['event_type'],
                security_data['user_id'],
                security_data['ip_address'],
                security_data['details'],
                security_data['severity'],
                security_data['action_taken']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing security event: {e}")
    
    def _store_performance_metric(self, performance_data: Dict[str, Any]):
        """Store performance metric in database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (timestamp, endpoint, method, response_time, status_code, user_id, memory_usage, cpu_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                performance_data['timestamp'],
                performance_data['endpoint'],
                performance_data['method'],
                performance_data['response_time'],
                performance_data['status_code'],
                performance_data['user_id'],
                performance_data['memory_usage'],
                performance_data['cpu_usage']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing performance metric: {e}")
    
    def _store_data_access_log(self, access_data: Dict[str, Any]):
        """Store data access log in database"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_access_log 
                (timestamp, user_id, resource_type, resource_id, action, ip_address, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                access_data['timestamp'],
                access_data['user_id'],
                access_data['resource_type'],
                access_data['resource_id'],
                access_data['action'],
                access_data['ip_address'],
                access_data['details']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing data access log: {e}")
    
    def _check_alert_conditions(self, event_type: str, event_data: Dict[str, Any]):
        """Check if event triggers alert conditions"""
        try:
            now = datetime.utcnow()
            five_minutes_ago = now - timedelta(minutes=5)
            
            # Count recent events of this type
            recent_count = sum(1 for log in self.recent_logs 
                             if log['event_type'] == event_type 
                             and datetime.fromisoformat(log['timestamp']) > five_minutes_ago)
            
            # Check threshold-based alerts
            if event_type == 'login_failed' and recent_count >= self.alert_thresholds['failed_logins']:
                self._trigger_security_alert({
                    'type': 'brute_force_attempt',
                    'event_type': event_type,
                    'count': recent_count,
                    'threshold': self.alert_thresholds['failed_logins'],
                    'time_window': '5 minutes'
                })
            
            elif event_type == 'suspicious_activity' and recent_count >= self.alert_thresholds['suspicious_activity']:
                self._trigger_security_alert({
                    'type': 'repeated_suspicious_activity',
                    'event_type': event_type,
                    'count': recent_count,
                    'threshold': self.alert_thresholds['suspicious_activity'],
                    'time_window': '5 minutes'
                })
            
            # Check high-value transaction alerts
            if event_type == 'payment_completed':
                details = json.loads(event_data.get('details', '{}'))
                amount = details.get('amount', 0)
                if amount >= self.alert_thresholds['high_value_transactions']:
                    self._trigger_security_alert({
                        'type': 'high_value_transaction',
                        'amount': amount,
                        'threshold': self.alert_thresholds['high_value_transactions']
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
    
    def _trigger_security_alert(self, alert_data: Dict[str, Any]):
        """Trigger security alert"""
        try:
            alert = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'security',
                'alert_type': alert_data['type'],
                'data': alert_data,
                'severity': 'high',
                'acknowledged': False
            }
            
            # Log the alert
            self.logger.critical(f"SECURITY ALERT: {json.dumps(alert_data)}")
            
            # Store alert in database (could create alerts table)
            # For now, just log it
            
        except Exception as e:
            self.logger.error(f"Error triggering security alert: {e}")
    
    def _trigger_performance_alert(self, alert_data: Dict[str, Any]):
        """Trigger performance alert"""
        try:
            alert = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'performance',
                'alert_type': alert_data['type'],
                'data': alert_data,
                'severity': 'medium'
            }
            
            # Log the alert
            self.logger.warning(f"PERFORMANCE ALERT: {json.dumps(alert_data)}")
            
        except Exception as e:
            self.logger.error(f"Error triggering performance alert: {e}")
    
    def _process_alerts(self):
        """Process and resolve alerts"""
        try:
            # This could implement alert resolution logic
            # For now, just log that processing occurred
            pass
        except Exception as e:
            self.logger.error(f"Error processing alerts: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.log_retention_days)
            
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            # Clean old audit logs
            cursor.execute('DELETE FROM audit_logs WHERE created_at < ?', (cutoff_date,))
            
            # Clean old security events
            cursor.execute('DELETE FROM security_events WHERE created_at < ?', (cutoff_date,))
            
            # Clean old performance metrics
            cursor.execute('DELETE FROM performance_metrics WHERE created_at < ?', (cutoff_date,))
            
            # Clean old data access logs
            cursor.execute('DELETE FROM data_access_log WHERE created_at < ?', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")
    
    def get_audit_logs(self, event_type: str = None, user_id: int = None,
                     from_date: datetime = None, to_date: datetime = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with filters"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            query = 'SELECT * FROM audit_logs WHERE 1=1'
            params = []
            
            if event_type:
                query += ' AND event_type = ?'
                params.append(event_type)
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if from_date:
                query += ' AND timestamp >= ?'
                params.append(from_date.isoformat())
            
            if to_date:
                query += ' AND timestamp <= ?'
                params.append(to_date.isoformat())
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            logs = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting audit logs: {e}")
            return []
    
    def get_security_events(self, severity: str = None, resolved: bool = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get security events with filters"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            query = 'SELECT * FROM security_events WHERE 1=1'
            params = []
            
            if severity:
                query += ' AND severity = ?'
                params.append(severity)
            
            if resolved is not None:
                query += ' AND resolved = ?'
                params.append(resolved)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            events = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return events
            
        except Exception as e:
            self.logger.error(f"Error getting security events: {e}")
            return []
    
    def get_performance_metrics(self, endpoint: str = None, from_date: datetime = None,
                           to_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get performance metrics with filters"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            query = 'SELECT * FROM performance_metrics WHERE 1=1'
            params = []
            
            if endpoint:
                query += ' AND endpoint = ?'
                params.append(endpoint)
            
            if from_date:
                query += ' AND timestamp >= ?'
                params.append(from_date.isoformat())
            
            if to_date:
                query += ' AND timestamp <= ?'
                params.append(to_date.isoformat())
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            metrics = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return []
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            # Get event type counts
            cursor.execute('''
                SELECT event_type, COUNT(*) as count 
                FROM audit_logs 
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY event_type
            ''')
            event_counts = dict(cursor.fetchall())
            
            # Get security event counts
            cursor.execute('''
                SELECT severity, COUNT(*) as count 
                FROM security_events 
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY severity
            ''')
            security_counts = dict(cursor.fetchall())
            
            # Get performance stats
            cursor.execute('''
                SELECT AVG(response_time) as avg_response, 
                       MAX(response_time) as max_response,
                       COUNT(*) as total_requests
                FROM performance_metrics 
                WHERE timestamp >= datetime('now', '-24 hours')
            ''')
            perf_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'event_counts': event_counts,
                'security_counts': security_counts,
                'performance': {
                    'avg_response_time': perf_stats[0] if perf_stats[0] else 0,
                    'max_response_time': perf_stats[1] if perf_stats[1] else 0,
                    'total_requests': perf_stats[2] if perf_stats[2] else 0
                },
                'log_statistics': dict(self.log_statistics),
                'retention_days': self.log_retention_days,
                'max_entries': self.max_log_entries
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audit statistics: {e}")
            return {}

# Global audit manager instance
audit_manager = AuditManager()

# Decorators for audit logging
def audit_event(event_type: str, severity: str = 'info', risk_score: int = 0):
    """Decorator to audit function calls"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            audit_manager.log_event(event_type, {
                'function': f.__name__,
                'args': str(args)[:200],  # Limit length
                'kwargs': str(kwargs)[:200]
            }, severity, risk_score)
            return f(*args, **kwargs)
        return wrapper

def log_data_access(resource_type: str, resource_id: str, action: str):
    """Decorator to log data access"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            audit_manager.log_data_access(resource_type, resource_id, action)
            return f(*args, **kwargs)
        return wrapper

# Utility functions
def log_audit_event(event_type: str, details: Dict[str, Any] = None,
                  severity: str = 'info', risk_score: int = 0):
    """Log an audit event"""
    audit_manager.log_event(event_type, details, severity, risk_score)

def log_security_event(event_type: str, details: Dict[str, Any] = None,
                    severity: str = 'medium', action_taken: str = None):
    """Log a security event"""
    audit_manager.log_security_event(event_type, details, severity, action_taken)

def log_performance_metric(endpoint: str, method: str, response_time: float,
                       status_code: int, memory_usage: float = None, cpu_usage: float = None):
    """Log performance metrics"""
    audit_manager.log_performance_metric(endpoint, method, response_time, status_code, memory_usage, cpu_usage)

def log_data_access(resource_type: str, resource_id: str, action: str,
                  details: Dict[str, Any] = None):
    """Log data access events"""
    audit_manager.log_data_access(resource_type, resource_id, action, details)

def get_audit_logs(event_type: str = None, user_id: int = None,
                 from_date: datetime = None, to_date: datetime = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
    """Get audit logs with filters"""
    return audit_manager.get_audit_logs(event_type, user_id, from_date, to_date, limit)

def get_security_events(severity: str = None, resolved: bool = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
    """Get security events with filters"""
    return audit_manager.get_security_events(severity, resolved, limit)

def get_performance_metrics(endpoint: str = None, from_date: datetime = None,
                       to_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get performance metrics with filters"""
    return audit_manager.get_performance_metrics(endpoint, from_date, to_date, limit)

def get_audit_statistics() -> Dict[str, Any]:
    """Get audit statistics"""
    return audit_manager.get_audit_statistics()