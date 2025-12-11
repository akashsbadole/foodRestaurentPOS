"""
Hardware Binding model for POS MVP application
Handles system fingerprinting for license binding with anti-cracking measures
"""

import os
import platform
import hashlib
import json
import uuid
import subprocess
import re
from typing import Dict, Optional, Any, List
from datetime import datetime

from src.utils.encryption import get_encryption_manager


class HardwareBinding:
    """
    Hardware Binding model for system fingerprinting and license binding
    Implements strong anti-cracking measures with multiple hardware identifiers
    """
    
    # Hardware components to fingerprint
    COMPONENT_CPU = "cpu"
    COMPONENT_MOTHERBOARD = "motherboard"
    COMPONENT_DISK = "disk"
    COMPONENT_MAC = "mac"
    COMPONENT_BIOS = "bios"
    COMPONENT_MEMORY = "memory"
    COMPONENT_GPU = "gpu"
    
    # Fingerprint methods
    METHOD_BASIC = "basic"
    METHOD_ADVANCED = "advanced"
    METHOD_STEALTH = "stealth"
    
    def __init__(self, db_manager=None):
        """Initialize hardware binding model"""
        self.db = db_manager
        self.encryption_manager = get_encryption_manager()
        
        # Hardware fingerprint data
        self._fingerprint_id = None
        self._fingerprint_hash = None
        self._hardware_components = {}
        self._fingerprint_method = None
        self._created_date = None
        self._last_verified = None
        self._verification_count = 0
        self._is_valid = False
        self._binding_signature = None
        self._anti_tamper_hash = None
        
    def generate_fingerprint(self, method: str = METHOD_ADVANCED) -> str:
        """
        Generate hardware fingerprint using specified method
        
        Args:
            method: Fingerprinting method to use
            
        Returns:
            Hardware fingerprint hash
        """
        try:
            self._fingerprint_method = method
            self._created_date = datetime.now()
            
            # Collect hardware components based on method
            if method == self.METHOD_BASIC:
                self._collect_basic_hardware()
            elif method == self.METHOD_ADVANCED:
                self._collect_advanced_hardware()
            elif method == self.METHOD_STEALTH:
                self._collect_stealth_hardware()
            else:
                # Default to advanced
                self._collect_advanced_hardware()
            
            # Generate fingerprint hash
            self._fingerprint_hash = self._generate_fingerprint_hash()
            
            # Generate binding signature
            self._generate_binding_signature()
            
            # Generate anti-tamper hash
            self._generate_anti_tamper_hash()
            
            self._is_valid = True
            return self._fingerprint_hash
        except Exception as e:
            print(f"Error generating hardware fingerprint: {str(e)}")
            return None
    
    def _collect_basic_hardware(self) -> None:
        """Collect basic hardware information"""
        try:
            # CPU information
            cpu_info = self._get_cpu_info()
            self._hardware_components[self.COMPONENT_CPU] = cpu_info
            
            # MAC address
            mac_info = self._get_mac_address()
            self._hardware_components[self.COMPONENT_MAC] = mac_info
            
            # Disk information
            disk_info = self._get_disk_info()
            self._hardware_components[self.COMPONENT_DISK] = disk_info
            
        except Exception as e:
            print(f"Error collecting basic hardware: {str(e)}")
    
    def _collect_advanced_hardware(self) -> None:
        """Collect advanced hardware information"""
        try:
            # Include basic components
            self._collect_basic_hardware()
            
            # Motherboard information
            motherboard_info = self._get_motherboard_info()
            self._hardware_components[self.COMPONENT_MOTHERBOARD] = motherboard_info
            
            # BIOS information
            bios_info = self._get_bios_info()
            self._hardware_components[self.COMPONENT_BIOS] = bios_info
            
            # Memory information
            memory_info = self._get_memory_info()
            self._hardware_components[self.COMPONENT_MEMORY] = memory_info
            
            # GPU information
            gpu_info = self._get_gpu_info()
            self._hardware_components[self.COMPONENT_GPU] = gpu_info
            
        except Exception as e:
            print(f"Error collecting advanced hardware: {str(e)}")
    
    def _collect_stealth_hardware(self) -> None:
        """Collect stealth hardware information (harder to detect)"""
        try:
            # Include advanced components
            self._collect_advanced_hardware()
            
            # Add stealth components
            # System UUID
            system_uuid = self._get_system_uuid()
            if system_uuid:
                self._hardware_components["system_uuid"] = system_uuid
            
            # Windows product ID (if available)
            if platform.system() == "Windows":
                product_id = self._get_windows_product_id()
                if product_id:
                    self._hardware_components["windows_product_id"] = product_id
            
            # Linux machine ID (if available)
            if platform.system() == "Linux":
                machine_id = self._get_linux_machine_id()
                if machine_id:
                    self._hardware_components["linux_machine_id"] = machine_id
            
        except Exception as e:
            print(f"Error collecting stealth hardware: {str(e)}")
    
    def _get_cpu_info(self) -> Dict[str, str]:
        """Get CPU information"""
        try:
            cpu_info = {}
            
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    for processor in c.Win32_Processor():
                        cpu_info["name"] = processor.Name
                        cpu_info["manufacturer"] = processor.Manufacturer
                        cpu_info["processor_id"] = processor.ProcessorId
                        cpu_info["max_clock_speed"] = str(processor.MaxClockSpeed)
                        break
                except ImportError:
                    # Fallback to registry
                    cpu_info = self._get_cpu_from_registry()
            elif platform.system() == "Linux":
                # Read from /proc/cpuinfo
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'model name' in line:
                                cpu_info["name"] = line.split(':')[1].strip()
                            elif 'processor' in line and 'processor_id' not in cpu_info:
                                cpu_info["processor_id"] = line.split(':')[1].strip()
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                # Use system_profiler
                try:
                    result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        output = result.stdout
                        for line in output.split('\n'):
                            if 'Processor Name' in line:
                                cpu_info["name"] = line.split(':')[1].strip()
                            elif 'Processor Speed' in line:
                                cpu_info["speed"] = line.split(':')[1].strip()
                except:
                    pass
            
            return cpu_info
        except Exception as e:
            print(f"Error getting CPU info: {str(e)}")
            return {}
    
    def _get_cpu_from_registry(self) -> Dict[str, str]:
        """Get CPU information from Windows registry"""
        try:
            import winreg
            cpu_info = {}
            
            # Open registry key
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            
            # Read values
            cpu_info["name"] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            cpu_info["vendor"] = winreg.QueryValueEx(key, "VendorIdentifier")[0]
            cpu_info["identifier"] = winreg.QueryValueEx(key, "Identifier")[0]
            
            winreg.CloseKey(key)
            return cpu_info
        except:
            return {}
    
    def _get_mac_address(self) -> str:
        """Get primary MAC address"""
        try:
            import uuid
            # Get MAC address from first available network interface
            mac = uuid.getnode()
            if mac != uuid.getnode():
                return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) 
                                for elements in range(0, 2*6, 2)][::-1])
            
            # Fallback method
            if platform.system() == "Windows":
                result = subprocess.run(['getmac', '/format', 'list'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Physical address' in line and not line.strip().endswith('00-00-00-00-00-00'):
                            mac_addr = line.split(':')[-1].strip()
                            return mac_addr.replace('-', ':')
            elif platform.system() == "Linux":
                try:
                    with open('/sys/class/net/eth0/address', 'r') as f:
                        return f.read().strip()
                except:
                    try:
                        with open('/sys/class/net/enp0s3/address', 'r') as f:
                            return f.read().strip()
                    except:
                        pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['ifconfig', 'en0'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'ether' in line:
                            return line.split('ether')[1].split()[0]
            
            return ""
        except Exception as e:
            print(f"Error getting MAC address: {str(e)}")
            return ""
    
    def _get_disk_info(self) -> Dict[str, str]:
        """Get disk information"""
        try:
            disk_info = {}
            
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    for disk in c.Win32_PhysicalMedia():
                        if disk.SerialNumber:
                            disk_info["serial"] = disk.SerialNumber.strip()
                            break
                    
                    # Fallback to logical disks
                    if not disk_info:
                        for disk in c.Win32_LogicalDisk():
                            if disk.VolumeSerialNumber:
                                disk_info["volume_serial"] = disk.VolumeSerialNumber.strip()
                                break
                except ImportError:
                    # Use subprocess fallback
                    result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip() and 'SerialNumber' not in line:
                                disk_info["serial"] = line.strip()
                                break
            elif platform.system() == "Linux":
                # Read disk serial from /sys/block
                try:
                    import glob
                    for device in glob.glob('/sys/block/sd*'):
                        try:
                            with open(f'{device}/device/serial', 'r') as f:
                                disk_info["serial"] = f.read().strip()
                                break
                        except:
                            pass
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['diskutil', 'info', '/'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Volume UUID' in line:
                            disk_info["volume_uuid"] = line.split(':')[1].strip()
                            break
            
            return disk_info
        except Exception as e:
            print(f"Error getting disk info: {str(e)}")
            return {}
    
    def _get_motherboard_info(self) -> Dict[str, str]:
        """Get motherboard information"""
        try:
            motherboard_info = {}
            
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    for board in c.Win32_BaseBoard():
                        motherboard_info["manufacturer"] = board.Manufacturer
                        motherboard_info["product"] = board.Product
                        motherboard_info["serial_number"] = board.SerialNumber
                        break
                except ImportError:
                    # Use subprocess fallback
                    result = subprocess.run(['wmic', 'baseboard', 'get', 'manufacturer,product,serialnumber'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        if len(lines) >= 2:
                            values = lines[1].strip().split()
                            if len(values) >= 3:
                                motherboard_info["manufacturer"] = values[0]
                                motherboard_info["product"] = values[1]
                                motherboard_info["serial_number"] = values[2]
            elif platform.system() == "Linux":
                # Read from DMI
                try:
                    result = subprocess.run(['dmidecode', '-s', 'baseboard-manufacturer'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        motherboard_info["manufacturer"] = result.stdout.strip()
                    
                    result = subprocess.run(['dmidecode', '-s', 'baseboard-product-name'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        motherboard_info["product"] = result.stdout.strip()
                    
                    result = subprocess.run(['dmidecode', '-s', 'baseboard-serial-number'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        motherboard_info["serial_number"] = result.stdout.strip()
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Model Name' in line:
                            motherboard_info["product"] = line.split(':')[1].strip()
                        elif 'Model Identifier' in line:
                            motherboard_info["model_identifier"] = line.split(':')[1].strip()
            
            return motherboard_info
        except Exception as e:
            print(f"Error getting motherboard info: {str(e)}")
            return {}
    
    def _get_bios_info(self) -> Dict[str, str]:
        """Get BIOS information"""
        try:
            bios_info = {}
            
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    for bios in c.Win32_BIOS():
                        bios_info["manufacturer"] = bios.Manufacturer
                        bios_info["version"] = bios.SMBIOSBIOSVersion
                        bios_info["serial_number"] = bios.SerialNumber
                        bios_info["release_date"] = bios.ReleaseDate
                        break
                except ImportError:
                    # Use subprocess fallback
                    result = subprocess.run(['wmic', 'bios', 'get', 'manufacturer,version,serialnumber,releasedate'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        if len(lines) >= 2:
                            values = lines[1].strip().split()
                            if len(values) >= 4:
                                bios_info["manufacturer"] = values[0]
                                bios_info["version"] = values[1]
                                bios_info["serial_number"] = values[2]
                                bios_info["release_date"] = values[3]
            elif platform.system() == "Linux":
                # Read from DMI
                try:
                    result = subprocess.run(['dmidecode', '-s', 'bios-vendor'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        bios_info["manufacturer"] = result.stdout.strip()
                    
                    result = subprocess.run(['dmidecode', '-s', 'bios-version'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        bios_info["version"] = result.stdout.strip()
                    
                    result = subprocess.run(['dmidecode', '-s', 'bios-release-date'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        bios_info["release_date"] = result.stdout.strip()
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Boot ROM Version' in line:
                            bios_info["version"] = line.split(':')[1].strip()
                        elif 'SMC Version' in line:
                            bios_info["smc_version"] = line.split(':')[1].strip()
            
            return bios_info
        except Exception as e:
            print(f"Error getting BIOS info: {str(e)}")
            return {}
    
    def _get_memory_info(self) -> Dict[str, str]:
        """Get memory information"""
        try:
            memory_info = {}
            
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    total_memory = 0
                    for memory in c.Win32_PhysicalMemory():
                        total_memory += int(memory.Capacity)
                    
                    memory_info["total_capacity"] = str(total_memory)
                    memory_info["capacity_gb"] = str(total_memory // (1024**3))
                except ImportError:
                    # Use subprocess fallback
                    result = subprocess.run(['wmic', 'computersystem', 'get', 'totalphysicalmemory'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip() and 'TotalPhysicalMemory' not in line:
                                memory_info["total_capacity"] = line.strip()
                                break
            elif platform.system() == "Linux":
                # Read from /proc/meminfo
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if 'MemTotal' in line:
                                memory_kb = line.split()[1]
                                memory_info["total_capacity_kb"] = memory_kb
                                memory_info["capacity_gb"] = str(int(memory_kb) // (1024**2))
                                break
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['sysctl', 'hw.memsize'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'hw.memsize' in line:
                            mem_bytes = line.split(':')[1].strip()
                            memory_info["total_capacity"] = mem_bytes
                            memory_info["capacity_gb"] = str(int(mem_bytes) // (1024**3))
                            break
            
            return memory_info
        except Exception as e:
            print(f"Error getting memory info: {str(e)}")
            return {}
    
    def _get_gpu_info(self) -> Dict[str, str]:
        """Get GPU information"""
        try:
            gpu_info = {}
            
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    for gpu in c.Win32_VideoController():
                        gpu_info["name"] = gpu.Name
                        gpu_info["adapter_ram"] = gpu.AdapterRAM
                        break
                except ImportError:
                    # Use subprocess fallback
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip() and 'Name' not in line:
                                gpu_info["name"] = line.strip()
                                break
            elif platform.system() == "Linux":
                # Use lspci
                try:
                    result = subprocess.run(['lspci'], capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'VGA' in line or '3D' in line:
                                gpu_info["name"] = line.split(':')[-1].strip()
                                break
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Chipset Model' in line:
                            gpu_info["name"] = line.split(':')[1].strip()
                            break
            
            return gpu_info
        except Exception as e:
            print(f"Error getting GPU info: {str(e)}")
            return {}
    
    def _get_system_uuid(self) -> str:
        """Get system UUID"""
        try:
            if platform.system() == "Windows":
                # Use WMI on Windows
                try:
                    import wmi
                    c = wmi.WMI()
                    for system in c.Win32_ComputerSystemProduct():
                        return system.UUID
                except ImportError:
                    # Use subprocess fallback
                    result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip() and 'UUID' not in line:
                                return line.strip()
            elif platform.system() == "Linux":
                # Read from DMI
                try:
                    result = subprocess.run(['dmidecode', '-s', 'system-uuid'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Hardware UUID' in line:
                            return line.split(':')[1].strip()
            
            return ""
        except Exception as e:
            print(f"Error getting system UUID: {str(e)}")
            return ""
    
    def _get_windows_product_id(self) -> str:
        """Get Windows product ID"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_id = winreg.QueryValueEx(key, "ProductId")[0]
            winreg.CloseKey(key)
            return product_id
        except:
            return ""
    
    def _get_linux_machine_id(self) -> str:
        """Get Linux machine ID"""
        try:
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        except:
            try:
                with open('/var/lib/dbus/machine-id', 'r') as f:
                    return f.read().strip()
            except:
                return ""
    
    def _generate_fingerprint_hash(self) -> str:
        """Generate fingerprint hash from hardware components"""
        try:
            # Sort components for consistent hash
            sorted_components = json.dumps(self._hardware_components, sort_keys=True)
            
            # Generate SHA-256 hash
            hash_obj = hashlib.sha256(sorted_components.encode())
            return hash_obj.hexdigest()
        except Exception as e:
            print(f"Error generating fingerprint hash: {str(e)}")
            return ""
    
    def _generate_binding_signature(self) -> None:
        """Generate binding signature for anti-tampering"""
        try:
            binding_data = {
                'fingerprint_hash': self._fingerprint_hash,
                'hardware_components': self._hardware_components,
                'fingerprint_method': self._fingerprint_method,
                'created_date': self._created_date.isoformat() if self._created_date else None
            }
            
            binding_json = json.dumps(binding_data, sort_keys=True)
            self._binding_signature = hashlib.sha512(binding_json.encode()).hexdigest()
        except Exception as e:
            print(f"Error generating binding signature: {str(e)}")
    
    def _generate_anti_tamper_hash(self) -> None:
        """Generate anti-tamper hash"""
        try:
            tamper_data = {
                'fingerprint_hash': self._fingerprint_hash,
                'binding_signature': self._binding_signature,
                'fingerprint_method': self._fingerprint_method,
                'created_date': self._created_date.isoformat() if self._created_date else None
            }
            
            tamper_json = json.dumps(tamper_data, sort_keys=True)
            self._anti_tamper_hash = hashlib.sha256(tamper_json.encode()).hexdigest()
        except Exception as e:
            print(f"Error generating anti-tamper hash: {str(e)}")
    
    def get_fingerprint(self) -> str:
        """Get the hardware fingerprint"""
        if not self._fingerprint_hash:
            self.generate_fingerprint()
        return self._fingerprint_hash
    
    def compare_fingerprints(self, fp1: str, fp2: str, tolerance: int = 0) -> bool:
        """
        Compare two fingerprints with tolerance for minor changes
        
        Args:
            fp1: First fingerprint
            fp2: Second fingerprint
            tolerance: Number of characters that can differ
            
        Returns:
            True if fingerprints match within tolerance
        """
        if not fp1 or not fp2:
            return False
        
        if fp1 == fp2:
            return True
        
        # Check tolerance
        if tolerance > 0:
            differences = sum(1 for a, b in zip(fp1, fp2) if a != b)
            return differences <= tolerance
        
        return False
    
    def verify_binding(self) -> bool:
        """Verify hardware binding integrity"""
        try:
            if not self._fingerprint_hash or not self._binding_signature:
                return False
            
            # Regenerate binding signature and compare
            binding_data = {
                'fingerprint_hash': self._fingerprint_hash,
                'hardware_components': self._hardware_components,
                'fingerprint_method': self._fingerprint_method,
                'created_date': self._created_date.isoformat() if self._created_date else None
            }
            
            binding_json = json.dumps(binding_data, sort_keys=True)
            calculated_signature = hashlib.sha512(binding_json.encode()).hexdigest()
            
            return calculated_signature == self._binding_signature
        except Exception as e:
            print(f"Error verifying binding: {str(e)}")
            return False
    
    def verify_anti_tamper(self) -> bool:
        """Verify anti-tamper hash"""
        try:
            if not self._anti_tamper_hash:
                return False
            
            tamper_data = {
                'fingerprint_hash': self._fingerprint_hash,
                'binding_signature': self._binding_signature,
                'fingerprint_method': self._fingerprint_method,
                'created_date': self._created_date.isoformat() if self._created_date else None
            }
            
            tamper_json = json.dumps(tamper_data, sort_keys=True)
            calculated_hash = hashlib.sha256(tamper_json.encode()).hexdigest()
            
            return calculated_hash == self._anti_tamper_hash
        except Exception as e:
            print(f"Error verifying anti-tamper: {str(e)}")
            return False
    
    def get_hardware_components(self) -> Dict[str, Any]:
        """Get hardware components (non-sensitive data)"""
        return {
            'cpu': {
                'name': self._hardware_components.get('cpu', {}).get('name', 'Unknown'),
                'manufacturer': self._hardware_components.get('cpu', {}).get('manufacturer', 'Unknown')
            },
            'motherboard': {
                'manufacturer': self._hardware_components.get('motherboard', {}).get('manufacturer', 'Unknown'),
                'product': self._hardware_components.get('motherboard', {}).get('product', 'Unknown')
            },
            'disk': {
                'serial': self._hardware_components.get('disk', {}).get('serial', 'Unknown')[:8] + '...' if self._hardware_components.get('disk', {}).get('serial') else 'Unknown'
            },
            'mac': {
                'address': self._hardware_components.get('mac', '')[:8] + '...' if self._hardware_components.get('mac') else 'Unknown'
            },
            'memory': {
                'capacity_gb': self._hardware_components.get('memory', {}).get('capacity_gb', 'Unknown')
            },
            'gpu': {
                'name': self._hardware_components.get('gpu', {}).get('name', 'Unknown')
            }
        }
    
    def save_to_database(self) -> bool:
        """Save hardware binding to database with encrypted fields"""
        if not self.db:
            return False
        
        try:
            # Encrypt sensitive hardware data
            encrypted_components = self.encryption_manager.encrypt(json.dumps(self._hardware_components)) if self._hardware_components else None
            
            # Convert dates to strings
            created_date_str = self._created_date.isoformat() if self._created_date else None
            last_verified_str = self._last_verified.isoformat() if self._last_verified else None
            
            query = """
            INSERT OR REPLACE INTO hardware_bindings (
                fingerprint_id, fingerprint_hash, hardware_components, fingerprint_method,
                created_date, last_verified, verification_count, is_valid,
                binding_signature, anti_tamper_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                self._fingerprint_id, self._fingerprint_hash, encrypted_components,
                self._fingerprint_method, created_date_str, last_verified_str,
                self._verification_count, self._is_valid, self._binding_signature,
                self._anti_tamper_hash
            )
            
            self.db.execute_query(query, params)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error saving hardware binding to database: {str(e)}")
            return False
    
    def load_from_database(self, fingerprint_hash: str) -> bool:
        """Load hardware binding from database using fingerprint hash"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM hardware_bindings WHERE fingerprint_hash = ?"
            self.db.execute_query(query, (fingerprint_hash,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._fingerprint_id = result[1]
            self._fingerprint_hash = result[2]
            self._hardware_components = json.loads(self.encryption_manager.decrypt(result[3])) if result[3] else {}
            self._fingerprint_method = result[4]
            self._created_date = datetime.fromisoformat(result[5]) if result[5] else None
            self._last_verified = datetime.fromisoformat(result[6]) if result[6] else None
            self._verification_count = result[7]
            self._is_valid = bool(result[8])
            self._binding_signature = result[9]
            self._anti_tamper_hash = result[10]
            
            return True
        except Exception as e:
            print(f"Error loading hardware binding from database: {str(e)}")
            return False
    
    def export_binding_data(self) -> Dict[str, Any]:
        """Export hardware binding data for backup"""
        return {
            'fingerprint_id': self._fingerprint_id,
            'fingerprint_hash': self._fingerprint_hash,
            'hardware_components': self._hardware_components,
            'fingerprint_method': self._fingerprint_method,
            'created_date': self._created_date.isoformat() if self._created_date else None,
            'last_verified': self._last_verified.isoformat() if self._last_verified else None,
            'verification_count': self._verification_count,
            'is_valid': self._is_valid,
            'binding_signature': self._binding_signature,
            'anti_tamper_hash': self._anti_tamper_hash
        }
    
    def import_binding_data(self, binding_data: Dict[str, Any]) -> bool:
        """Import hardware binding data from backup"""
        try:
            self._fingerprint_id = binding_data.get('fingerprint_id')
            self._fingerprint_hash = binding_data.get('fingerprint_hash')
            self._hardware_components = binding_data.get('hardware_components', {})
            self._fingerprint_method = binding_data.get('fingerprint_method')
            self._created_date = datetime.fromisoformat(binding_data['created_date']) if binding_data.get('created_date') else None
            self._last_verified = datetime.fromisoformat(binding_data['last_verified']) if binding_data.get('last_verified') else None
            self._verification_count = binding_data.get('verification_count', 0)
            self._is_valid = binding_data.get('is_valid', False)
            self._binding_signature = binding_data.get('binding_signature')
            self._anti_tamper_hash = binding_data.get('anti_tamper_hash')
            
            # Verify imported binding
            return self.verify_binding() and self.verify_anti_tamper()
        except Exception as e:
            print(f"Error importing binding data: {str(e)}")
            return False