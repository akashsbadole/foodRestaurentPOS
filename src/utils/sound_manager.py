"""
Sound Manager for POS System
Provides cross-platform sound notifications for kitchen operations
"""

import platform
import threading
import time
from typing import Optional

class SoundManager:
    """Manages sound notifications for the POS system"""
    
    def __init__(self):
        self.enabled = True
        self.system = platform.system()
        self._init_sound_system()
    
    def _init_sound_system(self):
        """Initialize sound system based on platform"""
        try:
            if self.system == 'Windows':
                import winsound
                self.winsound = winsound
            elif self.system == 'Darwin':  # macOS
                try:
                    import os
                    self.os = os
                except ImportError:
                    print("Warning: os module not available for macOS sounds")
            elif self.system == 'Linux':
                try:
                    import os
                    self.os = os
                except ImportError:
                    print("Warning: os module not available for Linux sounds")
        except ImportError as e:
            print(f"Warning: Sound system initialization failed: {e}")
    
    def play_notification_sound(self, sound_type: str = 'default'):
        """Play notification sound based on type"""
        if not self.enabled:
            return
        
        try:
            if sound_type == 'urgent':
                self._play_urgent_sound()
            elif sound_type == 'new_order':
                self._play_new_order_sound()
            else:
                self._play_default_sound()
        except Exception as e:
            print(f"Error playing sound: {e}")
    
    def _play_default_sound(self):
        """Play default notification sound"""
        if self.system == 'Windows':
            try:
                # Windows system notification sound
                self.winsound.MessageBeep(self.winsound.MB_ICONEXCLAMATION)
            except:
                # Fallback to simple beep
                self.winsound.Beep(800, 200)
        elif self.system == 'Darwin':
            # macOS - use afplay for system sounds
            try:
                self.os.system('afplay /System/Library/Sounds/Glass.aiff')
            except:
                self.os.system('afplay /System/Library/Sounds/Ping.aiff')
        elif self.system == 'Linux':
            # Linux - use aplay for system sounds
            try:
                self.os.system('aplay /usr/share/sounds/alsa/Front_Left.wav')
            except:
                # Fallback to system bell
                print('\a')
    
    def _play_urgent_sound(self):
        """Play urgent notification sound"""
        if self.system == 'Windows':
            try:
                # Windows critical stop sound
                self.winsound.MessageBeep(self.winsound.MB_ICONHAND)
            except:
                # Fallback to urgent beep
                for _ in range(3):
                    self.winsound.Beep(1000, 150)
                    time.sleep(0.1)
        elif self.system == 'Darwin':
            # macOS - use sosumi sound for urgent
            try:
                self.os.system('afplay /System/Library/Sounds/Sosumi.aiff')
            except:
                # Fallback to multiple beeps
                for _ in range(3):
                    self.os.system('afplay /System/Library/Sounds/Ping.aiff')
                    time.sleep(0.1)
        elif self.system == 'Linux':
            # Linux - urgent sound
            try:
                for _ in range(3):
                    self.os.system('aplay /usr/share/sounds/alsa/Front_Center.wav')
                    time.sleep(0.1)
            except:
                # Fallback to system bell
                for _ in range(3):
                    print('\a')
                    time.sleep(0.1)
    
    def _play_new_order_sound(self):
        """Play new order notification sound"""
        if self.system == 'Windows':
            try:
                # Windows asterisk sound (new notification)
                self.winsound.MessageBeep(self.winsound.MB_ICONASTERISK)
            except:
                # Fallback to pleasant beep
                self.winsound.Beep(600, 300)
        elif self.system == 'Darwin':
            # macOS - use pop sound for new orders
            try:
                self.os.system('afplay /System/Library/Sounds/Pop.aiff')
            except:
                self.os.system('afplay /System/Library/Sounds/Glass.aiff')
        elif self.system == 'Linux':
            # Linux - new order sound
            try:
                self.os.system('aplay /usr/share/sounds/alsa/Front_Right.wav')
            except:
                # Fallback to system bell
                print('\a')
    
    def play_error_sound(self):
        """Play error notification sound"""
        if not self.enabled:
            return
        
        try:
            if self.system == 'Windows':
                # Windows error sound
                self.winsound.MessageBeep(self.winsound.MB_ICONHAND)
            elif self.system == 'Darwin':
                # macOS - use basso sound for errors
                try:
                    self.os.system('afplay /System/Library/Sounds/Basso.aiff')
                except:
                    self.os.system('afplay /System/Library/Sounds/Sosumi.aiff')
            elif self.system == 'Linux':
                # Linux - error sound
                try:
                    self.os.system('aplay /usr/share/sounds/alsa/Noise.wav')
                except:
                    # Fallback to system bell
                    print('\a')
        except Exception as e:
            print(f"Error playing error sound: {e}")
    
    def play_success_sound(self):
        """Play success notification sound"""
        if not self.enabled:
            return
        
        try:
            if self.system == 'Windows':
                # Windows exclamation sound for success
                self.winsound.MessageBeep(self.winsound.MB_ICONEXCLAMATION)
            elif self.system == 'Darwin':
                # macOS - use hero sound for success
                try:
                    self.os.system('afplay /System/Library/Sounds/Hero.aiff')
                except:
                    self.os.system('afplay /System/Library/Sounds/Glass.aiff')
            elif self.system == 'Linux':
                # Linux - success sound
                try:
                    self.os.system('aplay /usr/share/sounds/alsa/Front_Left.wav')
                except:
                    # Fallback to system bell
                    print('\a')
        except Exception as e:
            print(f"Error playing success sound: {e}")
    
    def test_sounds(self):
        """Test all available sounds"""
        print("Testing sound notifications...")
        
        print("1. Default notification sound:")
        self.play_notification_sound('default')
        time.sleep(1)
        
        print("2. New order sound:")
        self.play_notification_sound('new_order')
        time.sleep(1)
        
        print("3. Urgent sound:")
        self.play_notification_sound('urgent')
        time.sleep(1)
        
        print("4. Success sound:")
        self.play_success_sound()
        time.sleep(1)
        
        print("5. Error sound:")
        self.play_error_sound()
        time.sleep(1)
        
        print("Sound test completed!")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable sound notifications"""
        self.enabled = enabled
        print(f"Sound notifications {'enabled' if enabled else 'disabled'}")
    
    def is_enabled(self) -> bool:
        """Check if sound notifications are enabled"""
        return self.enabled

# Global sound manager instance
sound_manager = SoundManager()

# Convenience functions for backward compatibility
def play_notification_sound(sound_type: str = 'default'):
    """Play notification sound"""
    sound_manager.play_notification_sound(sound_type)

def play_urgent_sound():
    """Play urgent notification sound"""
    sound_manager.play_notification_sound('urgent')

def play_new_order_sound():
    """Play new order sound"""
    sound_manager.play_notification_sound('new_order')

def play_error_sound():
    """Play error sound"""
    sound_manager.play_error_sound()

def play_success_sound():
    """Play success sound"""
    sound_manager.play_success_sound()

def set_sound_enabled(enabled: bool):
    """Enable or disable sound notifications"""
    sound_manager.set_enabled(enabled)

def is_sound_enabled() -> bool:
    """Check if sound notifications are enabled"""
    return sound_manager.is_enabled()