"""
Anti-Tamper utility for POS MVP application
Handles code integrity verification and anti-debugging
"""

import os
import sys
import time
import hashlib
import inspect
import ctypes
import threading
from datetime import datetime
from typing import Dict, Optional, Any, List

from src.utils.encryption import get_encryption_manager


class AntiTamper:
    """
    Anti-Tamper utility for code integrity verification
    Implements anti-debugging and anti-reverse engineering techniques
    """
    
    # Tamper detection methods
    METHOD_CHECKSUM = "checksum"
    METHOD_DEBUGGER = "debugger"
    METHOD_VIRTUALIZATION = "virtualization"
    METHOD_TIMING = "timing"
    METHOD_INTEGRITY = "integrity"
    
    # Tamper status
    STATUS_CLEAN = "clean"
    STATUS_TAMPERED = "tampered"
    STATUS_DEBUGGER = "debugger_detected"
    STATUS_VIRTUAL = "virtual_environment"
    STATUS_SUSPICIOUS = "suspicious"
    
    # File extensions to monitor
    MONITORED_EXTENSIONS = ['.py', '.pyc', '.exe', '.dll']
    
    def __init__(self):
        """Initialize anti-tamper utility"""
        self.encryption_manager = get_encryption_manager()
        
        # Integrity data
        self._integrity_hash = None
        self._baseline_hash = None
        self._monitored_files = {}
        self._file_hashes = {}
        
        # Detection state
        self._tamper_detected = False
        self._debugger_detected = False
        self._virtual_environment = False
        self._timing_checks = {}
        self._last_check = None
        
        # Protection mechanisms
        self._protection_active = False
        self._check_thread = None
        self._check_interval = 30  # seconds
        
        # Obfuscation
        self._obfuscation_key = None
        self._init_obfuscation_key()
    
    def _init_obfuscation_key(self) -> None:
        """Initialize obfuscation key from system data"""
        try:
            # Generate obfuscation key from system data
            system_data = f"{os.getcwd()}-{sys.version}-{os.environ.get('USERNAME', '')}"
            self._obfuscation_key = hashlib.sha256(system_data.encode()).digest()[:16]
        except Exception as e:
            print(f"Error initializing obfuscation key: {str(e)}")
            # Fallback to random key
            self._obfuscation_key = os.urandom(16)
    
    def calculate_integrity_hash(self) -> bool:
        """
        Calculate integrity hash of critical files
        
        Returns:
            True if hash calculated successfully, False otherwise
        """
        try:
            # Get current script directory
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Files to monitor for integrity
            critical_files = [
                'main.py',
                'src/app.py',
                'src/utils/license_manager.py',
                'src/utils/license_crypto.py',
                'src/models/license.py'
            ]
            
            combined_hash = ""
            
            for file_name in critical_files:
                file_path = os.path.join(script_dir, file_name)
                if os.path.exists(file_path):
                    # Calculate file hash
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash:
                        self._file_hashes[file_name] = file_hash
                        combined_hash += file_hash
            
            # Calculate combined integrity hash
            if combined_hash:
                self._integrity_hash = hashlib.sha256(combined_hash.encode()).hexdigest()
                self._baseline_hash = self._integrity_hash
                return True
            
            return False
        except Exception as e:
            print(f"Error calculating integrity hash: {str(e)}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of a single file"""
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                hash_obj = hashlib.sha256()
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
                return hash_obj.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash for {file_path}: {str(e)}")
            return ""
    
    def setup_tamper_detection(self) -> bool:
        """
        Set up tamper detection mechanisms
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Start background monitoring thread
            if not self._protection_active:
                self._protection_active = True
                self._check_thread = threading.Thread(
                    target=self._monitoring_worker,
                    daemon=True
                )
                self._check_thread.start()
            
            return True
        except Exception as e:
            print(f"Error setting up tamper detection: {str(e)}")
            return False
    
    def _monitoring_worker(self) -> None:
        """Background monitoring worker thread"""
        while self._protection_active:
            try:
                # Perform tamper checks
                self._perform_tamper_checks()
                
                # Sleep for check interval
                time.sleep(self._check_interval)
            except Exception as e:
                print(f"Error in monitoring worker: {str(e)}")
    
    def _perform_tamper_checks(self) -> None:
        """Perform all tamper detection checks"""
        try:
            # Check file integrity
            if self._check_file_integrity():
                self._tamper_detected = True
            
            # Check for debugger
            if self._check_debugger():
                self._debugger_detected = True
            
            # Check for virtual environment
            if self._check_virtual_environment():
                self._virtual_environment = True
            
            # Check timing anomalies
            if self._check_timing_anomalies():
                self._tamper_detected = True
            
            # Update last check time
            self._last_check = datetime.now()
        except Exception as e:
            print(f"Error performing tamper checks: {str(e)}")
    
    def _check_file_integrity(self) -> bool:
        """Check if files have been modified"""
        try:
            if not self._baseline_hash:
                return False
            
            # Recalculate integrity hash
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            critical_files = [
                'main.py',
                'src/app.py',
                'src/utils/license_manager.py',
                'src/utils/license_crypto.py',
                'src/models/license.py'
            ]
            
            combined_hash = ""
            
            for file_name in critical_files:
                file_path = os.path.join(script_dir, file_name)
                if os.path.exists(file_path):
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash:
                        # Check if file hash has changed
                        if file_name in self._file_hashes:
                            if self._file_hashes[file_name] != file_hash:
                                return True  # File has been modified
                        combined_hash += file_hash
            
            # Check combined hash
            if combined_hash:
                current_hash = hashlib.sha256(combined_hash.encode()).hexdigest()
                return current_hash != self._baseline_hash
            
            return False
        except Exception as e:
            print(f"Error checking file integrity: {str(e)}")
            return False
    
    def _check_debugger(self) -> bool:
        """Check if debugger is attached"""
        try:
            # Check for common debugger indicators
            
            # Check if being debugged (Windows)
            if sys.platform == "win32":
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    return kernel32.IsDebuggerPresent() != 0
                except:
                    pass
            
            # Check for tracing (Linux/Mac)
            if hasattr(sys, 'gettrace') and sys.gettrace():
                return True
            
            # Check for common debugging modules
            for module_name in ['pdb', 'ipdb', 'pudb']:
                if module_name in sys.modules:
                    return True
            
            # Check for debugging environment variables
            debug_vars = ['PYTHONDEBUG', 'DEBUG', 'PDBDEBUG']
            for var in debug_vars:
                if os.environ.get(var):
                    return True
            
            # Check for suspicious parent process
            try:
                import psutil
                parent = psutil.Process().parent()
                if parent and any(name in parent.name().lower() 
                                for name in ['gdb', 'lldb', 'x64dbg', 'ollydbg', 'windbg']):
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            print(f"Error checking debugger: {str(e)}")
            return False
    
    def _check_virtual_environment(self) -> bool:
        """Check if running in virtual environment"""
        try:
            # Check for virtualization indicators
            
            # Check common virtual environment indicators
            virtual_indicators = [
                '/usr/bin/qemu',
                '/usr/bin/virtualbox',
                '/usr/bin/vmware',
                'vbox',
                'vmware',
                'qemu'
            ]
            
            # Check system files
            if sys.platform == "linux":
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read().lower()
                        if any(indicator in cpuinfo for indicator in virtual_indicators):
                            return True
                except:
                    pass
                
                # Check for virtual environment files
                virtual_files = [
                    '/sys/class/dmi/id/product_name',
                    '/sys/class/dmi/id/sys_vendor',
                    '/sys/devices/virtual/dmi/id/product_name'
                ]
                
                for file_path in virtual_files:
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if any(indicator in content for indicator in virtual_indicators):
                                return True
                    except:
                        pass
            
            # Check environment variables
            virtual_env_vars = [
                'VIRTUAL_ENV',
                'CONDA_DEFAULT_ENV',
                'PYTHON_VENV',
                'VBOX'
            ]
            
            for var in virtual_env_vars:
                if os.environ.get(var):
                    return True
            
            # Check for hypervisor presence (Windows)
            if sys.platform == "win32":
                try:
                    import wmi
                    c = wmi.WMI()
                    for system in c.Win32_ComputerSystem():
                        if 'Virtual' in system.Manufacturer or 'VMware' in system.Manufacturer:
                            return True
                except:
                    pass
            
            return False
        except Exception as e:
            print(f"Error checking virtual environment: {str(e)}")
            return False
    
    def _check_timing_anomalies(self) -> bool:
        """Check for timing anomalies that might indicate tampering"""
        try:
            current_time = time.time()
            
            # Initialize timing checks
            if 'execution_start' not in self._timing_checks:
                self._timing_checks['execution_start'] = current_time
                self._timing_checks['last_check'] = current_time
                return False
            
            # Check execution time
            execution_time = current_time - self._timing_checks['execution_start']
            if execution_time < 0.1:  # Suspiciously fast execution
                return True
            
            # Check check interval
            if 'last_check' in self._timing_checks:
                check_interval = current_time - self._timing_checks['last_check']
                if check_interval < self._check_interval * 0.8:  # Too frequent checks
                    return True
            
            # Update timing data
            self._timing_checks['last_check'] = current_time
            
            return False
        except Exception as e:
            print(f"Error checking timing anomalies: {str(e)}")
            return False
    
    def is_tampered(self) -> bool:
        """Check if tampering has been detected"""
        return (self._tamper_detected or 
                self._debugger_detected or 
                self._virtual_environment)
    
    def is_debugger_attached(self) -> bool:
        """Check if debugger is attached"""
        return self._debugger_detected
    
    def is_virtual_environment(self) -> bool:
        """Check if running in virtual environment"""
        return self._virtual_environment
    
    def is_code_injected(self) -> bool:
        """Check for code injection"""
        try:
            # Check for suspicious modules
            suspicious_modules = [
                'inspect', 'types', 'gc', 'sys'
            ]
            
            # Check for monkey patching
            original_len = len(str)
            current_len = len(str)
            
            # Check for code modification
            if current_len != original_len:
                return True
            
            # Check for suspicious function calls
            frame = inspect.currentframe()
            if frame:
                # Check call stack for suspicious patterns
                call_stack = inspect.getouterframes(frame)
                for frame_info in call_stack:
                    filename = frame_info[1]
                    if 'site-packages' in filename and 'license' in filename:
                        return True
            
            return False
        except Exception as e:
            print(f"Error checking code injection: {str(e)}")
            return False
    
    def obfuscate_string(self, input_str: str) -> str:
        """Obfuscate string using XOR cipher"""
        try:
            if not input_str or not self._obfuscation_key:
                return input_str
            
            # Convert to bytes
            input_bytes = input_str.encode('utf-8')
            
            # XOR with obfuscation key
            obfuscated_bytes = bytearray()
            for i, byte in enumerate(input_bytes):
                key_byte = self._obfuscation_key[i % len(self._obfuscation_key)]
                obfuscated_bytes.append(byte ^ key_byte)
            
            # Convert to base64
            import base64
            return base64.b64encode(obfuscated_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error obfuscating string: {str(e)}")
            return input_str
    
    def deobfuscate_string(self, obfuscated_str: str) -> str:
        """Deobfuscate string using XOR cipher"""
        try:
            if not obfuscated_str or not self._obfuscation_key:
                return obfuscated_str
            
            # Convert from base64
            import base64
            obfuscated_bytes = base64.b64decode(obfuscated_str.encode('utf-8'))
            
            # XOR with obfuscation key
            deobfuscated_bytes = bytearray()
            for i, byte in enumerate(obfuscated_bytes):
                key_byte = self._obfuscation_key[i % len(self._obfuscation_key)]
                deobfuscated_bytes.append(byte ^ key_byte)
            
            return deobfuscated_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error deobfuscating string: {str(e)}")
            return obfuscated_str
    
    def get_tamper_status(self) -> Dict[str, Any]:
        """Get current tamper detection status"""
        return {
            'tamper_detected': self._tamper_detected,
            'debugger_detected': self._debugger_detected,
            'virtual_environment': self._virtual_environment,
            'protection_active': self._protection_active,
            'last_check': self._last_check.isoformat() if self._last_check else None,
            'integrity_hash': self._integrity_hash,
            'baseline_hash': self._baseline_hash,
            'monitored_files_count': len(self._file_hashes),
            'check_interval': self._check_interval
        }
    
    def reset_tamper_detection(self) -> None:
        """Reset tamper detection state"""
        self._tamper_detected = False
        self._debugger_detected = False
        self._virtual_environment = False
        self._timing_checks.clear()
        self._last_check = None
    
    def update_baseline(self) -> bool:
        """Update baseline integrity hash"""
        try:
            # Recalculate integrity hash
            if self.calculate_integrity_hash():
                # Reset tamper detection
                self.reset_tamper_detection()
                return True
            return False
        except Exception as e:
            print(f"Error updating baseline: {str(e)}")
            return False
    
    def add_monitored_file(self, file_path: str) -> bool:
        """Add file to monitoring list"""
        try:
            if os.path.exists(file_path):
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    self._file_hashes[file_path] = file_hash
                    return True
            return False
        except Exception as e:
            print(f"Error adding monitored file: {str(e)}")
            return False
    
    def remove_monitored_file(self, file_path: str) -> None:
        """Remove file from monitoring list"""
        if file_path in self._file_hashes:
            del self._file_hashes[file_path]
    
    def set_check_interval(self, interval: int) -> None:
        """Set monitoring check interval"""
        self._check_interval = max(5, interval)  # Minimum 5 seconds
    
    def stop_protection(self) -> None:
        """Stop tamper protection"""
        try:
            self._protection_active = False
            
            # Wait for monitoring thread to finish
            if self._check_thread and self._check_thread.is_alive():
                self._check_thread.join(timeout=5)
        except Exception as e:
            print(f"Error stopping protection: {str(e)}")
    
    def restart_protection(self) -> bool:
        """Restart tamper protection"""
        try:
            self.stop_protection()
            return self.setup_tamper_detection()
        except Exception as e:
            print(f"Error restarting protection: {str(e)}")
            return False
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed tamper detection report"""
        return {
            'status': self.STATUS_TAMPERED if self.is_tampered() else self.STATUS_CLEAN,
            'detection_methods': {
                'file_integrity': self._tamper_detected,
                'debugger': self._debugger_detected,
                'virtualization': self._virtual_environment,
                'timing_anomalies': self._check_timing_anomalies()
            },
            'system_info': {
                'platform': sys.platform,
                'python_version': sys.version,
                'executable': sys.executable,
                'working_directory': os.getcwd()
            },
            'protection_info': {
                'active': self._protection_active,
                'check_interval': self._check_interval,
                'last_check': self._last_check.isoformat() if self._last_check else None,
                'monitored_files': list(self._file_hashes.keys())
            },
            'integrity_info': {
                'current_hash': self._integrity_hash,
                'baseline_hash': self._baseline_hash,
                'hashes_match': self._integrity_hash == self._baseline_hash,
                'monitored_files_count': len(self._file_hashes)
            }
        }