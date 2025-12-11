"""
Lazy Loading System for Desktop POS Application
Implements lazy loading for images, menu items, and data
"""

import threading
import time
import hashlib
import os
from typing import Dict, List, Any, Optional, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import logging
from PIL import Image, ImageTk
import io
import base64
from queue import Queue, Empty
import tkinter as tk
from tkinter import ttk

from src.utils.performance_utils import PerformanceConfig

T = TypeVar('T')

class ResourceType(Enum):
    """Resource types for lazy loading"""
    IMAGE = "image"
    MENU_ITEM = "menu_item"
    DATA = "data"
    CONFIG = "config"

class LoadPriority(Enum):
    """Load priority levels"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class ResourceInfo:
    """Resource information"""
    resource_id: str
    resource_type: ResourceType
    data: Any
    size: int
    load_time: float
    last_accessed: float
    access_count: int
    priority: LoadPriority
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type.value,
            'size': self.size,
            'load_time': self.load_time,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'priority': self.priority.value,
            'metadata': self.metadata
        }

class LazyLoadTask:
    """Lazy loading task"""
    
    def __init__(self, resource_id: str, resource_type: ResourceType, 
                 priority: LoadPriority, callback: Callable, metadata: Dict[str, Any] = None):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.priority = priority
        self.callback = callback
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.error = None

class LazyResourceLoader(Generic[T]):
    """Generic lazy resource loader"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Resource cache
        self.resource_cache: Dict[str, ResourceInfo] = {}
        self.resource_cache_lock = threading.RLock()
        
        # Loading state
        self.loading_tasks: Dict[str, LazyLoadTask] = {}
        self.loading_lock = threading.RLock()
        
        # Task queue
        self.task_queue = Queue()
        self.priority_queue = []
        self.queue_lock = threading.RLock()
        
        # Background loading thread
        self.background_thread = None
        self.background_loading = True
        
        # Loaders registry
        self.loaders = {}
        self.loaders_lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'total_loaded': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'load_times': [],
            'errors': []
        }
        
        # Initialize
        self._initialize_loader()
    
    def _initialize_loader(self):
        """Initialize lazy loader"""
        # Start background loading thread
        self.background_thread = threading.Thread(target=self._background_loading_loop, daemon=True)
        self.background_thread.start()
        
        # Start cache cleanup thread
        cleanup_thread = threading.Thread(target=self._cache_cleanup_loop, daemon=True)
        cleanup_thread.start()
        
        self.logger.info("Lazy resource loader initialized")
    
    def _background_loading_loop(self):
        """Background loading loop"""
        while self.background_loading:
            try:
                # Get next task
                task = self._get_next_task()
                
                if task:
                    # Process task
                    self._process_task(task)
                
                # Sleep briefly
                time.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Background loading error: {e}")
                time.sleep(0.1)
    
    def _cache_cleanup_loop(self):
        """Cache cleanup loop"""
        while self.background_loading:
            try:
                # Clean up old resources
                self._cleanup_cache()
                
                # Sleep for cleanup interval
                time.sleep(self.config.cache_cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
                time.sleep(5)
    
    def _get_next_task(self) -> Optional[LazyLoadTask]:
        """Get next task from queue"""
        try:
            # Try to get from priority queue first
            with self.queue_lock:
                if self.priority_queue:
                    return self.priority_queue.pop(0)
            
            # Try to get from regular queue
            try:
                return self.task_queue.get_nowait()
            except Empty:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting next task: {e}")
            return None
    
    def _process_task(self, task: LazyLoadTask):
        """Process loading task"""
        try:
            # Mark task as started
            task.started_at = time.time()
            
            # Load resource
            start_time = time.time()
            resource_data = self._load_resource(task)
            load_time = time.time() - start_time
            
            # Create resource info
            resource_info = ResourceInfo(
                resource_id=task.resource_id,
                resource_type=task.resource_type,
                data=resource_data,
                size=len(str(resource_data)) if resource_data else 0,
                load_time=load_time,
                last_accessed=time.time(),
                access_count=1,
                priority=task.priority,
                metadata=task.metadata
            )
            
            # Store in cache
            with self.resource_cache_lock:
                self.resource_cache[task.resource_id] = resource_info
            
            # Update statistics
            self.stats['total_loaded'] += 1
            self.stats['load_times'].append(load_time)
            
            # Keep only last 1000 load times
            if len(self.stats['load_times']) > 1000:
                self.stats['load_times'] = self.stats['load_times'][-1000:]
            
            # Mark task as completed
            task.completed_at = time.time()
            
            # Trigger callback
            if task.callback:
                task.callback(resource_info)
            
        except Exception as e:
            # Mark task as failed
            task.error = str(e)
            task.completed_at = time.time()
            
            # Update statistics
            self.stats['errors'].append({
                'resource_id': task.resource_id,
                'error': str(e),
                'timestamp': time.time()
            })
            
            # Keep only last 100 errors
            if len(self.stats['errors']) > 100:
                self.stats['errors'] = self.stats['errors'][-100:]
            
            self.logger.error(f"Failed to load resource {task.resource_id}: {e}")
    
    def _load_resource(self, task: LazyLoadTask) -> T:
        """Load resource"""
        try:
            # Get loader for resource type
            loader = self._get_loader(task.resource_type)
            
            if loader:
                return loader.load(task.resource_id, task.metadata)
            else:
                raise ValueError(f"No loader registered for resource type: {task.resource_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to load resource {task.resource_id}: {e}")
            raise
    
    def _get_loader(self, resource_type: ResourceType) -> Optional[Callable]:
        """Get loader for resource type"""
        with self.loaders_lock:
            return self.loaders.get(resource_type)
    
    def register_loader(self, resource_type: ResourceType, loader: Callable):
        """Register resource loader"""
        with self.loaders_lock:
            self.loaders[resource_type] = loader
        
        self.logger.info(f"Registered loader for {resource_type.value}")
    
    def load_resource(self, resource_id: str, resource_type: ResourceType, 
                     callback: Callable = None, priority: LoadPriority = LoadPriority.MEDIUM,
                     metadata: Dict[str, Any] = None) -> Optional[ResourceInfo]:
        """Load resource with lazy loading"""
        try:
            # Check cache first
            cached_info = self._get_cached_resource(resource_id)
            if cached_info:
                self.stats['cache_hits'] += 1
                cached_info.last_accessed = time.time()
                cached_info.access_count += 1
                
                if callback:
                    callback(cached_info)
                
                return cached_info
            
            self.stats['cache_misses'] += 1
            
            # Create task
            task = LazyLoadTask(
                resource_id=resource_id,
                resource_type=resource_type,
                priority=priority,
                callback=callback,
                metadata=metadata
            )
            
            # Add to queue
            if priority == LoadPriority.CRITICAL:
                with self.queue_lock:
                    self.priority_queue.insert(0, task)
            else:
                self.task_queue.put(task)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load resource {resource_id}: {e}")
            raise
    
    def preload_resource(self, resource_id: str, resource_type: ResourceType,
                        priority: LoadPriority = LoadPriority.LOW,
                        metadata: Dict[str, Any] = None):
        """Preload resource in background"""
        try:
            # Create task
            task = LazyLoadTask(
                resource_id=resource_id,
                resource_type=resource_type,
                priority=priority,
                callback=None,
                metadata=metadata
            )
            
            # Add to priority queue
            with self.queue_lock:
                self.priority_queue.append(task)
                self.priority_queue.sort(key=lambda x: x.priority.value)
                
        except Exception as e:
            self.logger.error(f"Failed to preload resource {resource_id}: {e}")
    
    def get_resource(self, resource_id: str) -> Optional[ResourceInfo]:
        """Get resource from cache"""
        return self._get_cached_resource(resource_id)
    
    def _get_cached_resource(self, resource_id: str) -> Optional[ResourceInfo]:
        """Get cached resource"""
        with self.resource_cache_lock:
            resource_info = self.resource_cache.get(resource_id)
            if resource_info:
                resource_info.last_accessed = time.time()
                resource_info.access_count += 1
            return resource_info
    
    def _cleanup_cache(self):
        """Clean up old resources"""
        try:
            current_time = time.time()
            max_age = self.config.cache_max_age
            
            with self.resource_cache_lock:
                # Remove old resources
                resources_to_remove = []
                for resource_id, resource_info in self.resource_cache.items():
                    if current_time - resource_info.last_accessed > max_age:
                        resources_to_remove.append(resource_id)
                
                # Remove resources
                for resource_id in resources_to_remove:
                    del self.resource_cache[resource_id]
                    self.logger.debug(f"Removed old resource from cache: {resource_id}")
                
                # Limit cache size
                if len(self.resource_cache) > self.config.cache_size:
                    # Sort by access count and last accessed time
                    sorted_resources = sorted(
                        self.resource_cache.items(),
                        key=lambda x: (x[1].access_count, x[1].last_accessed)
                    )
                    
                    # Remove least used resources
                    resources_to_remove = sorted_resources[:len(self.resource_cache) - self.config.cache_size]
                    for resource_id, _ in resources_to_remove:
                        del self.resource_cache[resource_id]
                        self.logger.debug(f"Removed least used resource from cache: {resource_id}")
        
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.resource_cache_lock:
            return {
                'cached_resources': len(self.resource_cache),
                'cache_size': sum(info.size for info in self.resource_cache.values()),
                'stats': self.stats.copy(),
                'queue_size': self.task_queue.qsize(),
                'priority_queue_size': len(self.priority_queue)
            }
    
    def clear_cache(self):
        """Clear resource cache"""
        with self.resource_cache_lock:
            self.resource_cache.clear()
        
        with self.queue_lock:
            self.priority_queue.clear()
        
        # Clear task queue
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except Empty:
                break
        
        self.logger.info("Resource cache cleared")
    
    def stop_background_loading(self):
        """Stop background loading"""
        self.background_loading = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        
        self.logger.info("Background loading stopped")

class LazyImageLoader:
    """Lazy image loader for Tkinter"""
    
    def __init__(self, lazy_loader: LazyResourceLoader):
        self.lazy_loader = lazy_loader
        self.logger = logging.getLogger(__name__)
        
        # Image cache
        self.image_cache = {}
        self.image_cache_lock = threading.RLock()
        
        # Loaders
        self.register_loaders()
    
    def register_loaders(self):
        """Register image loaders"""
        # Register image loader
        self.lazy_loader.register_loader(ResourceType.IMAGE, self._load_image)
    
    def _load_image(self, image_path: str, metadata: Dict[str, Any]) -> Image.Image:
        """Load image from path"""
        try:
            # Load image
            img = Image.open(image_path)
            
            # Resize if specified
            if 'max_width' in metadata or 'max_height' in metadata:
                max_width = metadata.get('max_width', None)
                max_height = metadata.get('max_height', None)
                
                if max_width or max_height:
                    img.thumbnail((max_width or img.width, max_height or img.height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            return img
            
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {e}")
            raise
    
    def get_image(self, image_path: str, callback: Callable = None, 
                 max_width: int = None, max_height: int = None) -> Optional[ImageTk.PhotoImage]:
        """Get image with lazy loading"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(image_path, max_width, max_height)
            
            with self.image_cache_lock:
                if cache_key in self.image_cache:
                    return self.image_cache[cache_key]
            
            # Load image
            metadata = {}
            if max_width:
                metadata['max_width'] = max_width
            if max_height:
                metadata['max_height'] = max_height
            
            resource_info = self.lazy_loader.get_resource(image_path)
            if resource_info:
                img = resource_info.data
                photo_img = ImageTk.PhotoImage(img)
                
                # Cache image
                with self.image_cache_lock:
                    self.image_cache[cache_key] = photo_img
                
                return photo_img
            
            # Load asynchronously
            if callback:
                def image_callback(resource_info: ResourceInfo):
                    img = resource_info.data
                    photo_img = ImageTk.PhotoImage(img)
                    
                    # Cache image
                    with self.image_cache_lock:
                        self.image_cache[cache_key] = photo_img
                    
                    callback(photo_img)
                
                self.lazy_loader.load_resource(
                    image_path, ResourceType.IMAGE, 
                    callback=image_callback,
                    priority=LoadPriority.HIGH,
                    metadata=metadata
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get image {image_path}: {e}")
            return None
    
    def _get_cache_key(self, image_path: str, max_width: int = None, max_height: int = None) -> str:
        """Generate cache key"""
        key_parts = [image_path]
        if max_width:
            key_parts.append(f"w{max_width}")
        if max_height:
            key_parts.append(f"h{max_height}")
        return "_".join(key_parts)
    
    def preload_image(self, image_path: str, max_width: int = None, max_height: int = None):
        """Preload image"""
        metadata = {}
        if max_width:
            metadata['max_width'] = max_width
        if max_height:
            metadata['max_height'] = max_height
        
        self.lazy_loader.preload_resource(
            image_path, ResourceType.IMAGE,
            priority=LoadPriority.MEDIUM,
            metadata=metadata
        )
    
    def clear_image_cache(self):
        """Clear image cache"""
        with self.image_cache_lock:
            self.image_cache.clear()
        
        self.logger.info("Image cache cleared")

class LazyMenuLoader:
    """Lazy menu item loader"""
    
    def __init__(self, lazy_loader: LazyResourceLoader):
        self.lazy_loader = lazy_loader
        self.logger = logging.getLogger(__name__)
        
        # Register loader
        self.lazy_loader.register_loader(ResourceType.MENU_ITEM, self._load_menu_item)
    
    def _load_menu_item(self, menu_item_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Load menu item"""
        try:
            # This would load from database in a real implementation
            # For now, return a mock menu item
            return {
                'id': menu_item_id,
                'name': f"Menu Item {menu_item_id}",
                'price': 10.99,
                'category': metadata.get('category', 'General'),
                'description': "Sample menu item",
                'image_path': metadata.get('image_path', ''),
                'available': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load menu item {menu_item_id}: {e}")
            raise
    
    def get_menu_item(self, menu_item_id: str, callback: Callable = None, 
                     category: str = None) -> Optional[Dict[str, Any]]:
        """Get menu item with lazy loading"""
        try:
            metadata = {'category': category} if category else {}
            
            return self.lazy_loader.load_resource(
                menu_item_id, ResourceType.MENU_ITEM,
                callback=callback,
                priority=LoadPriority.HIGH,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get menu item {menu_item_id}: {e}")
            return None
    
    def preload_menu_items(self, menu_item_ids: List[str], category: str = None):
        """Preload menu items"""
        metadata = {'category': category} if category else {}
        
        for menu_item_id in menu_item_ids:
            self.lazy_loader.preload_resource(
                menu_item_id, ResourceType.MENU_ITEM,
                priority=LoadPriority.MEDIUM,
                metadata=metadata
            )

class LazyDataLoader:
    """Lazy data loader"""
    
    def __init__(self, lazy_loader: LazyResourceLoader):
        self.lazy_loader = lazy_loader
        self.logger = logging.getLogger(__name__)
        
        # Register loader
        self.lazy_loader.register_loader(ResourceType.DATA, self._load_data)
    
    def _load_data(self, data_key: str, metadata: Dict[str, Any]) -> Any:
        """Load data"""
        try:
            # This would load from database or file in a real implementation
            # For now, return mock data
            return {
                'key': data_key,
                'data': f"Sample data for {data_key}",
                'timestamp': time.time(),
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load data {data_key}: {e}")
            raise
    
    def get_data(self, data_key: str, callback: Callable = None, 
                metadata: Dict[str, Any] = None) -> Optional[Any]:
        """Get data with lazy loading"""
        try:
            return self.lazy_loader.load_resource(
                data_key, ResourceType.DATA,
                callback=callback,
                priority=LoadPriority.MEDIUM,
                metadata=metadata or {}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get data {data_key}: {e}")
            return None
    
    def preload_data(self, data_keys: List[str], metadata: Dict[str, Any] = None):
        """Preload data"""
        for data_key in data_keys:
            self.lazy_loader.preload_resource(
                data_key, ResourceType.DATA,
                priority=LoadPriority.LOW,
                metadata=metadata or {}
            )

class LazyLoadUIHelper:
    """Helper class for lazy loading in Tkinter UI"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.lazy_loader = LazyResourceLoader(config)
        self.image_loader = LazyImageLoader(self.lazy_loader)
        self.menu_loader = LazyMenuLoader(self.lazy_loader)
        self.data_loader = LazyDataLoader(self.lazy_loader)
        self.logger = logging.getLogger(__name__)
    
    def create_lazy_image_label(self, parent: tk.Widget, image_path: str, 
                              width: int = None, height: int = None,
                              loading_text: str = "Loading...") -> ttk.Label:
        """Create lazy loading image label"""
        label = ttk.Label(parent, text=loading_text)
        
        def on_image_loaded(photo_img: ImageTk.PhotoImage):
            label.config(image=photo_img, text="")
            label.image = photo_img  # Keep reference
        
        # Load image
        self.image_loader.get_image(
            image_path, 
            callback=on_image_loaded,
            max_width=width,
            max_height=height
        )
        
        return label
    
    def create_lazy_menu_item(self, parent: tk.Widget, menu_item_id: str,
                            on_load: Callable = None) -> ttk.Frame:
        """Create lazy loading menu item widget"""
        frame = ttk.Frame(parent)
        
        # Create loading label
        loading_label = ttk.Label(frame, text="Loading menu item...")
        loading_label.pack(pady=10)
        
        def on_menu_item_loaded(menu_item: Dict[str, Any]):
            # Remove loading label
            loading_label.destroy()
            
            # Create menu item UI
            name_label = ttk.Label(frame, text=menu_item['name'], font=('Arial', 12, 'bold'))
            name_label.pack()
            
            price_label = ttk.Label(frame, text=f"${menu_item['price']:.2f}")
            price_label.pack()
            
            # Add image if available
            if menu_item.get('image_path'):
                image_label = self.create_lazy_image_label(
                    frame, 
                    menu_item['image_path'],
                    width=100,
                    height=100
                )
                image_label.pack(pady=5)
            
            # Trigger callback
            if on_load:
                on_load(menu_item)
        
        # Load menu item
        self.menu_loader.get_menu_item(
            menu_item_id,
            callback=on_menu_item_loaded
        )
        
        return frame
    
    def preload_menu_items(self, menu_item_ids: List[str]):
        """Preload menu items"""
        self.menu_loader.preload_menu_items(menu_item_ids)
    
    def preload_images(self, image_paths: List[str]):
        """Preload images"""
        for image_path in image_paths:
            self.image_loader.preload_image(image_path)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.lazy_loader.get_cache_stats()
    
    def clear_cache(self):
        """Clear all caches"""
        self.lazy_loader.clear_cache()
        self.image_loader.clear_image_cache()

# Global lazy loader instance
_lazy_load_helper = None

def get_lazy_load_helper() -> LazyLoadUIHelper:
    """Get global lazy load helper instance"""
    global _lazy_load_helper
    if _lazy_load_helper is None:
        config = PerformanceConfig()
        _lazy_load_helper = LazyLoadUIHelper(config)
    return _lazy_load_helper