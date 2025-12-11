"""
Hardware Fingerprint utility for POS MVP application
Handles system identification with anti-tampering measures
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


class HardwareFingerprint:
    """
    Hardware Fingerprint utility for system identification
    Implements robust fingerprinting with anti-tampering measures
    """
    
    # Fingerprint components
    COMPONENT_CPU = "cpu"
    COMPONENT_MOTHERBOARD = "motherboard"
    COMPONENT_DISK = "disk"
    COMPONENT_MAC = "mac"
    COMPONENT_BIOS = "bios"
    COMPONENT_MEMORY = "memory"
    COMPONENT_GPU = "gpu"
    COMPONENT_SYSTEM = "system"
    
    # Fingerprint methods
    METHOD_BASIC = "basic"
    METHOD_ADVANCED = "advanced"
    METHOD_STEALTH = "stealth"
    METHOD_OBFUSCATED = "obfuscated"
    
    # Obfuscation methods
    OBFUSCATION_XOR = "xor"
    OBFUSCATION_SUBSTITUTION = "substitution"
    OBFUSCATION_REVERSE = "reverse"
    OBFUSCATION_BASE64 = "base64"
    
    def __init__(self):
        """Initialize hardware fingerprint utility"""
        self.encryption_manager = get_encryption_manager()
        self._fingerprint_cache = {}
        self._obfuscation_key = None
        self._init_obfuscation_key()
    
    def _init_obfuscation_key(self) -> None:
        """Initialize obfuscation key from system data"""
        try:
            # Generate obfuscation key from system data
            system_data = f"{platform.system()}-{platform.machine()}-{platform.processor()}"
            self._obfuscation_key = hashlib.sha256(system_data.encode()).digest()[:16]
        except Exception as e:
            print(f"Error initializing obfuscation key: {str(e)}")
            # Fallback to random key
            self._obfuscation_key = os.urandom(16)
    
    def generate_fingerprint(self, method: str = METHOD_ADVANCED, 
                          obfuscation: str = None) -> Dict[str, Any]:
        """
        Generate hardware fingerprint using specified method
        
        Args:
            method: Fingerprinting method to use
            obfuscation: Obfuscation method to apply
            
        Returns:
            Dictionary with fingerprint data
        """
        try:
            fingerprint_data = {
                'method': method,
                'timestamp': datetime.now().isoformat(),
                'components': {},
                'hash': None,
                'obfuscated_hash': None
            }
            
            # Collect hardware components based on method
            if method == self.METHOD_BASIC:
                self._collect_basic_components(fingerprint_data['components'])
            elif method == self.METHOD_ADVANCED:
                self._collect_advanced_components(fingerprint_data['components'])
            elif method == self.METHOD_STEALTH:
                self._collect_stealth_components(fingerprint_data['components'])
            elif method == self.METHOD_OBFUSCATED:
                self._collect_obfuscated_components(fingerprint_data['components'])
            else:
                # Default to advanced
                self._collect_advanced_components(fingerprint_data['components'])
            
            # Generate fingerprint hash
            fingerprint_data['hash'] = self._generate_fingerprint_hash(fingerprint_data['components'])
            
            # Apply obfuscation if specified
            if obfuscation:
                fingerprint_data['obfuscated_hash'] = self._obfuscate_hash(
                    fingerprint_data['hash'], obfuscation
                )
            
            # Cache fingerprint
            cache_key = f"{method}_{obfuscation or 'none'}"
            self._fingerprint_cache[cache_key] = fingerprint_data
            
            return fingerprint_data
        except Exception as e:
            print(f"Error generating fingerprint: {str(e)}")
            return {}
    
    def _collect_basic_components(self, components: Dict[str, Any]) -> None:
        """Collect basic hardware components"""
        try:
            # CPU information
            cpu_info = self._get_cpu_info()
            if cpu_info:
                components[self.COMPONENT_CPU] = cpu_info
            
            # MAC address
            mac_info = self._get_mac_address()
            if mac_info:
                components[self.COMPONENT_MAC] = mac_info
            
            # Disk information
            disk_info = self._get_disk_info()
            if disk_info:
                components[self.COMPONENT_DISK] = disk_info
            
        except Exception as e:
            print(f"Error collecting basic components: {str(e)}")
    
    def _collect_advanced_components(self, components: Dict[str, Any]) -> None:
        """Collect advanced hardware components"""
        try:
            # Include basic components
            self._collect_basic_components(components)
            
            # Motherboard information
            motherboard_info = self._get_motherboard_info()
            if motherboard_info:
                components[self.COMPONENT_MOTHERBOARD] = motherboard_info
            
            # BIOS information
            bios_info = self._get_bios_info()
            if bios_info:
                components[self.COMPONENT_BIOS] = bios_info
            
            # Memory information
            memory_info = self._get_memory_info()
            if memory_info:
                components[self.COMPONENT_MEMORY] = memory_info
            
            # GPU information
            gpu_info = self._get_gpu_info()
            if gpu_info:
                components[self.COMPONENT_GPU] = gpu_info
            
            # System information
            system_info = self._get_system_info()
            if system_info:
                components[self.COMPONENT_SYSTEM] = system_info
            
        except Exception as e:
            print(f"Error collecting advanced components: {str(e)}")
    
    def _collect_stealth_components(self, components: Dict[str, Any]) -> None:
        """Collect stealth hardware components"""
        try:
            # Include advanced components
            self._collect_advanced_components(components)
            
            # Add stealth components
            # System UUID
            system_uuid = self._get_system_uuid()
            if system_uuid:
                components['system_uuid'] = system_uuid
            
            # Windows product ID (if available)
            if platform.system() == "Windows":
                product_id = self._get_windows_product_id()
                if product_id:
                    components['windows_product_id'] = product_id
            
            # Linux machine ID (if available)
            if platform.system() == "Linux":
                machine_id = self._get_linux_machine_id()
                if machine_id:
                    components['linux_machine_id'] = machine_id
            
            # MAC address variations
            mac_variations = self._get_mac_variations()
            if mac_variations:
                components['mac_variations'] = mac_variations
            
        except Exception as e:
            print(f"Error collecting stealth components: {str(e)}")
    
    def _collect_obfuscated_components(self, components: Dict[str, Any]) -> None:
        """Collect obfuscated hardware components"""
        try:
            # Collect advanced components first
            self._collect_advanced_components(components)
            
            # Obfuscate sensitive data
            for key, value in components.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and len(sub_value) > 8:
                            # Obfuscate string values longer than 8 characters
                            components[key][sub_key] = self._obfuscate_string(sub_value)
                elif isinstance(value, str) and len(value) > 8:
                    # Obfuscate string values longer than 8 characters
                    components[key] = self._obfuscate_string(value)
            
        except Exception as e:
            print(f"Error collecting obfuscated components: {str(e)}")
    
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
                        cpu_info["cores"] = str(processor.NumberOfCores)
                        cpu_info["logical_processors"] = str(processor.NumberOfLogicalProcessors)
                        break
                except ImportError:
                    # Fallback to registry
                    cpu_info = self._get_cpu_from_registry()
            elif platform.system() == "Linux":
                # Read from /proc/cpuinfo
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpu_lines = f.readlines()
                        for line in cpu_lines:
                            if 'model name' in line:
                                cpu_info["name"] = line.split(':')[1].strip()
                            elif 'processor' in line and 'processor_id' not in cpu_info:
                                cpu_info["processor_id"] = line.split(':')[1].strip()
                            elif 'cpu cores' in line:
                                cpu_info["cores"] = line.split(':')[1].strip()
                            elif 'siblings' in line:
                                cpu_info["logical_processors"] = line.split(':')[1].strip()
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
                            elif 'Number of Cores' in line:
                                cpu_info["cores"] = line.split(':')[1].strip()
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
                # Try multiple interfaces
                interfaces = ['eth0', 'enp0s3', 'wlan0', 'en0']
                for interface in interfaces:
                    try:
                        with open(f'/sys/class/net/{interface}/address', 'r') as f:
                            return f.read().strip()
                    except:
                        continue
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
    
    def _get_mac_variations(self) -> List[str]:
        """Get variations of MAC addresses"""
        try:
            mac_addresses = []
            
            if platform.system() == "Windows":
                result = subprocess.run(['getmac'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '-' in line and not line.strip().endswith('00-00-00-00-00-00'):
                            mac_addr = line.strip().split()[0]
                            mac_addresses.append(mac_addr.replace('-', ':'))
            elif platform.system() == "Linux":
                # Get all network interfaces
                try:
                    result = subprocess.run(['ip', 'link', 'show'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'link/ether' in line:
                                mac_addr = line.split('link/ether')[1].split()[0]
                                if mac_addr not in mac_addresses:
                                    mac_addresses.append(mac_addr)
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['ifconfig', '-a'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'ether' in line:
                            mac_addr = line.split('ether')[1].split()[0]
                            if mac_addr not in mac_addresses:
                                mac_addresses.append(mac_addr)
            
            return mac_addresses
        except Exception as e:
            print(f"Error getting MAC variations: {str(e)}")
            return []
    
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
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information"""
        try:
            system_info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0],
                'hostname': platform.node()
            }
            
            return system_info
        except Exception as e:
            print(f"Error getting system info: {str(e)}")
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
    
    def _generate_fingerprint_hash(self, components: Dict[str, Any]) -> str:
        """Generate fingerprint hash from components"""
        try:
            # Sort components for consistent hash
            sorted_components = json.dumps(components, sort_keys=True)
            
            # Generate SHA-256 hash
            hash_obj = hashlib.sha256(sorted_components.encode())
            return hash_obj.hexdigest()
        except Exception as e:
            print(f"Error generating fingerprint hash: {str(e)}")
            return ""
    
    def _obfuscate_string(self, input_str: str) -> str:
        """Obfuscate string using XOR with obfuscation key"""
        try:
            if not input_str or not self._obfuscation_key:
                return input_str
            
            # Convert to bytes
            input_bytes = input_str.encode('utf-8')
            
            # XOR with obfuscation key (repeated as needed)
            obfuscated_bytes = bytearray()
            for i, byte in enumerate(input_bytes):
                key_byte = self._obfuscation_key[i % len(self._obfuscation_key)]
                obfuscated_bytes.append(byte ^ key_byte)
            
            # Convert to base64
            return base64.b64encode(obfuscated_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error obfuscating string: {str(e)}")
            return input_str
    
    def _obfuscate_hash(self, hash_str: str, method: str) -> str:
        """Obfuscate hash using specified method"""
        try:
            if not hash_str:
                return hash_str
            
            if method == self.OBFUSCATION_XOR:
                return self._obfuscate_string(hash_str)
            elif method == self.OBFUSCATION_REVERSE:
                return hash_str[::-1]
            elif method == self.OBFUSCATION_BASE64:
                return base64.b64encode(hash_str.encode()).decode('utf-8')
            elif method == self.OBFUSCATION_SUBSTITUTION:
                # Simple substitution cipher
                substitution_map = {
                    '0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E',
                    '5': 'F', '6': 'G', '7': 'H', '8': 'I', '9': 'J',
                    'a': 'K', 'b': 'L', 'c': 'M', 'd': 'N', 'e': 'O',
                    'f': 'P'
                }
                return ''.join([substitution_map.get(c, c) for c in hash_str])
            else:
                return hash_str
        except Exception as e:
            print(f"Error obfuscating hash: {str(e)}")
            return hash_str
    
    def get_fingerprint(self, method: str = METHOD_ADVANCED) -> str:
        """Get hardware fingerprint hash"""
        try:
            cache_key = f"{method}_none"
            if cache_key in self._fingerprint_cache:
                return self._fingerprint_cache[cache_key]['hash']
            
            fingerprint_data = self.generate_fingerprint(method)
            return fingerprint_data.get('hash', '')
        except Exception as e:
            print(f"Error getting fingerprint: {str(e)}")
            return ""
    
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
    
    def verify_fingerprint_integrity(self, fingerprint_data: Dict[str, Any]) -> bool:
        """Verify fingerprint integrity"""
        try:
            if not fingerprint_data or 'hash' not in fingerprint_data or 'components' not in fingerprint_data:
                return False
            
            # Recalculate hash from components
            calculated_hash = self._generate_fingerprint_hash(fingerprint_data['components'])
            
            # Compare with stored hash
            return calculated_hash == fingerprint_data['hash']
        except Exception as e:
            print(f"Error verifying fingerprint integrity: {str(e)}")
            return False
    
    def get_cached_fingerprint(self, method: str = METHOD_ADVANCED, 
                           obfuscation: str = None) -> Dict[str, Any]:
        """Get cached fingerprint if available"""
        cache_key = f"{method}_{obfuscation or 'none'}"
        return self._fingerprint_cache.get(cache_key, {})
    
    def clear_cache(self) -> None:
        """Clear fingerprint cache"""
        self._fingerprint_cache.clear()
    
    def get_fingerprint_summary(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of fingerprint data (non-sensitive)"""
        try:
            components = fingerprint_data.get('components', {})
            summary = {
                'method': fingerprint_data.get('method', 'unknown'),
                'timestamp': fingerprint_data.get('timestamp', ''),
                'hash': fingerprint_data.get('hash', ''),
                'obfuscated_hash': fingerprint_data.get('obfuscated_hash', ''),
                'components_count': len(components),
                'components': {}
            }
            
            # Add non-sensitive component info
            for key, value in components.items():
                if isinstance(value, dict):
                    summary['components'][key] = {
                        'fields': list(value.keys()),
                        'has_data': bool(value)
                    }
                else:
                    summary['components'][key] = {
                        'type': type(value).__name__,
                        'has_data': bool(value)
                    }
            
            return summary
        except Exception as e:
            print(f"Error getting fingerprint summary: {str(e)}")
            return {}