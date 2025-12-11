"""
Pagination Manager for Desktop POS Application
Handles efficient pagination of large datasets with caching and background loading
"""

import threading
import time
import math
from typing import Dict, List, Any, Optional, Callable, Tuple, TypeVar, Generic
from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging

from src.utils.performance_utils import PerformanceConfig, get_performance_manager

T = TypeVar('T')

class SortDirection(Enum):
    """Sort direction enumeration"""
    ASC = "asc"
    DESC = "desc"

@dataclass
class PaginationConfig:
    """Pagination configuration"""
    page_size: int = 50
    max_page_size: int = 200
    cache_size: int = 10  # Number of pages to cache
    background_loading: bool = True
    preload_pages: int = 1  # Number of pages to preload
    sort_column: Optional[str] = None
    sort_direction: SortDirection = SortDirection.ASC
    filter_callback: Optional[Callable] = None

class PaginatedDataLoader(Generic[T]):
    """Generic paginated data loader"""
    
    def __init__(self, config: PaginationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Performance manager
        self.perf_manager = get_performance_manager()
        
        # Data storage
        self.total_items = 0
        self.total_pages = 0
        self.current_page = 1
        self.page_cache = {}
        self.cache_lock = threading.RLock()
        
        # Loading state
        self.loading = False
        self.loading_lock = threading.RLock()
        
        # Background loading
        self.background_thread = None
        self.background_queue = deque()
        self.background_loading_enabled = config.background_loading
        
        # Event callbacks
        self.page_loaded_callbacks = []
        self.loading_started_callbacks = []
        self.loading_completed_callbacks = []
        
        # Initialize background loading
        if self.background_loading_enabled:
            self._start_background_loading()
    
    def load_page(self, page: int, force_refresh: bool = False) -> List[T]:
        """Load a specific page"""
        with self.loading_lock:
            if self.loading:
                self.logger.warning("Already loading, please wait")
                return []
            
            self.loading = True
        
        try:
            # Check cache first
            if not force_refresh and page in self.page_cache:
                return self.page_cache[page]
            
            # Load data
            start_time = time.time()
            data = self._load_page_data(page)
            load_time = time.time() - start_time
            
            # Update cache
            with self.cache_lock:
                self.page_cache[page] = data
                
                # Limit cache size
                if len(self.page_cache) > self.config.cache_size:
                    # Remove oldest page
                    oldest_page = min(self.page_cache.keys())
                    del self.page_cache[oldest_page]
            
            # Update current page
            self.current_page = page
            
            # Log performance
            self.logger.info(f"Loaded page {page} with {len(data)} items in {load_time:.2f}s")
            
            # Trigger callbacks
            self._trigger_page_loaded(page, data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading page {page}: {e}")
            return []
        
        finally:
            self.loading = False
            self._trigger_loading_completed()
    
    def _load_page_data(self, page: int) -> List[T]:
        """Load data for specific page (to be overridden)"""
        raise NotImplementedError("Subclasses must implement _load_page_data")
    
    def _start_background_loading(self):
        """Start background loading thread"""
        def background_worker():
            while self.background_loading_enabled:
                try:
                    if self.background_queue:
                        page = self.background_queue.popleft()
                        if page not in self.page_cache:
                            self.load_page(page)
                    
                    time.sleep(0.1)  # Small delay to prevent CPU usage
                    
                except Exception as e:
                    self.logger.error(f"Background loading error: {e}")
                    time.sleep(1)
        
        self.background_thread = threading.Thread(target=background_worker, daemon=True)
        self.background_thread.start()
    
    def preload_pages(self):
        """Preload adjacent pages"""
        if not self.background_loading_enabled:
            return
        
        with self.cache_lock:
            # Preload previous page
            if self.current_page > 1:
                prev_page = self.current_page - 1
                if prev_page not in self.page_cache:
                    self.background_queue.append(prev_page)
            
            # Preload next page
            if self.current_page < self.total_pages:
                next_page = self.current_page + 1
                if next_page not in self.page_cache:
                    self.background_queue.append(next_page)
            
            # Preload additional pages if configured
            for i in range(2, self.config.preload_pages + 1):
                if self.current_page - i > 0:
                    page = self.current_page - i
                    if page not in self.page_cache:
                        self.background_queue.append(page)
                
                if self.current_page + i <= self.total_pages:
                    page = self.current_page + i
                    if page not in self.page_cache:
                        self.background_queue.append(page)
    
    def get_page(self, page: int, force_refresh: bool = False) -> List[T]:
        """Get page data"""
        if page < 1 or page > self.total_pages:
            return []
        
        return self.load_page(page, force_refresh)
    
    def get_current_page(self) -> List[T]:
        """Get current page data"""
        return self.get_page(self.current_page)
    
    def next_page(self) -> List[T]:
        """Load next page"""
        if self.current_page < self.total_pages:
            return self.get_page(self.current_page + 1)
        return []
    
    def previous_page(self) -> List[T]:
        """Load previous page"""
        if self.current_page > 1:
            return self.get_page(self.current_page - 1)
        return []
    
    def go_to_page(self, page: int) -> List[T]:
        """Go to specific page"""
        return self.get_page(page)
    
    def set_page_size(self, page_size: int):
        """Set page size"""
        if page_size < 1:
            page_size = self.config.page_size
        elif page_size > self.config.max_page_size:
            page_size = self.config.max_page_size
        
        self.config.page_size = page_size
        
        # Recalculate total pages
        self.total_pages = math.ceil(self.total_items / page_size)
        
        # Clear cache as page size has changed
        self.clear_cache()
    
    def set_sorting(self, column: str, direction: SortDirection):
        """Set sorting configuration"""
        self.config.sort_column = column
        self.config.sort_direction = direction
        
        # Clear cache as sorting has changed
        self.clear_cache()
    
    def set_filter(self, filter_callback: Callable):
        """Set filter callback"""
        self.config.filter_callback = filter_callback
        
        # Clear cache as filter has changed
        self.clear_cache()
    
    def clear_cache(self):
        """Clear page cache"""
        with self.cache_lock:
            self.page_cache.clear()
        
        self.logger.info("Page cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            return {
                'cache_size': len(self.page_cache),
                'cached_pages': list(self.page_cache.keys()),
                'memory_usage': len(str(self.page_cache)) / 1024  # KB
            }
    
    def add_page_loaded_callback(self, callback: Callable):
        """Add page loaded callback"""
        self.page_loaded_callbacks.append(callback)
    
    def add_loading_started_callback(self, callback: Callable):
        """Add loading started callback"""
        self.loading_started_callbacks.append(callback)
    
    def add_loading_completed_callback(self, callback: Callable):
        """Add loading completed callback"""
        self.loading_completed_callbacks.append(callback)
    
    def _trigger_page_loaded(self, page: int, data: List[T]):
        """Trigger page loaded callbacks"""
        for callback in self.page_loaded_callbacks:
            try:
                callback(page, data)
            except Exception as e:
                self.logger.error(f"Page loaded callback error: {e}")
    
    def _trigger_loading_started(self):
        """Trigger loading started callbacks"""
        for callback in self.loading_started_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Loading started callback error: {e}")
    
    def _trigger_loading_completed(self):
        """Trigger loading completed callbacks"""
        for callback in self.loading_completed_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Loading completed callback error: {e}")
    
    def stop_background_loading(self):
        """Stop background loading"""
        self.background_loading_enabled = False
        if self.background_thread:
            self.background_thread.join(timeout=5)

class PaginationManager(Generic[T]):
    """Main pagination manager"""
    
    def __init__(self, config: PaginationConfig = None):
        self.config = config or PaginationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Performance manager
        self.perf_manager = get_performance_manager()
        
        # Data loaders
        self.loaders = {}
        self.loaders_lock = threading.RLock()
        
        # Pagination state
        self.current_loader_id = None
        self.pagination_history = []
        
        # UI state
        self.ui_state = {
            'visible_pages': [],
            'current_page': 1,
            'total_pages': 0,
            'page_size': self.config.page_size,
            'total_items': 0
        }
    
    def register_loader(self, loader_id: str, loader: PaginatedDataLoader[T]):
        """Register a data loader"""
        with self.loaders_lock:
            self.loaders[loader_id] = loader
            loader.add_page_loaded_callback(self._on_page_loaded)
            loader.add_loading_started_callback(self._on_loading_started)
            loader.add_loading_completed_callback(self._on_loading_completed)
    
    def get_loader(self, loader_id: str) -> Optional[PaginatedDataLoader[T]]:
        """Get data loader by ID"""
        with self.loaders_lock:
            return self.loaders.get(loader_id)
    
    def set_active_loader(self, loader_id: str):
        """Set active loader"""
        with self.loaders_lock:
            if loader_id in self.loaders:
                self.current_loader_id = loader_id
                
                # Update UI state
                loader = self.loaders[loader_id]
                self.ui_state.update({
                    'current_page': loader.current_page,
                    'total_pages': loader.total_pages,
                    'total_items': loader.total_items,
                    'page_size': loader.config.page_size
                })
                
                # Add to history
                self.pagination_history.append({
                    'loader_id': loader_id,
                    'timestamp': time.time(),
                    'page': loader.current_page
                })
                
                # Limit history size
                if len(self.pagination_history) > 50:
                    self.pagination_history = self.pagination_history[-50:]
    
    def get_current_data(self) -> List[T]:
        """Get current page data"""
        if not self.current_loader_id:
            return []
        
        loader = self.get_loader(self.current_loader_id)
        if loader:
            return loader.get_current_page()
        
        return []
    
    def navigate_to_page(self, page: int, loader_id: str = None) -> List[T]:
        """Navigate to specific page"""
        target_loader_id = loader_id or self.current_loader_id
        
        if not target_loader_id:
            return []
        
        loader = self.get_loader(target_loader_id)
        if loader:
            data = loader.go_to_page(page)
            
            # Update UI state
            self.ui_state.update({
                'current_page': loader.current_page,
                'total_pages': loader.total_pages,
                'total_items': loader.total_items
            })
            
            return data
        
        return []
    
    def next_page(self, loader_id: str = None) -> List[T]:
        """Go to next page"""
        target_loader_id = loader_id or self.current_loader_id
        
        if not target_loader_id:
            return []
        
        loader = self.get_loader(target_loader_id)
        if loader:
            data = loader.next_page()
            
            # Update UI state
            self.ui_state.update({
                'current_page': loader.current_page,
                'total_pages': loader.total_pages,
                'total_items': loader.total_items
            })
            
            return data
        
        return []
    
    def previous_page(self, loader_id: str = None) -> List[T]:
        """Go to previous page"""
        target_loader_id = loader_id or self.current_loader_id
        
        if not target_loader_id:
            return []
        
        loader = self.get_loader(target_loader_id)
        if loader:
            data = loader.previous_page()
            
            # Update UI state
            self.ui_state.update({
                'current_page': loader.current_page,
                'total_pages': loader.total_pages,
                'total_items': loader.total_items
            })
            
            return data
        
        return []
    
    def set_page_size(self, page_size: int, loader_id: str = None):
        """Set page size"""
        target_loader_id = loader_id or self.current_loader_id
        
        if not target_loader_id:
            return
        
        loader = self.get_loader(target_loader_id)
        if loader:
            loader.set_page_size(page_size)
            
            # Update UI state
            self.ui_state.update({
                'page_size': page_size,
                'total_pages': loader.total_pages
            })
    
    def get_pagination_info(self, loader_id: str = None) -> Dict[str, Any]:
        """Get pagination information"""
        target_loader_id = loader_id or self.current_loader_id
        
        if not target_loader_id:
            return {}
        
        loader = self.get_loader(target_loader_id)
        if loader:
            return {
                'current_page': loader.current_page,
                'total_pages': loader.total_pages,
                'total_items': loader.total_items,
                'page_size': loader.config.page_size,
                'has_previous': loader.current_page > 1,
                'has_next': loader.current_page < loader.total_pages,
                'cache_stats': loader.get_cache_stats()
            }
        
        return {}
    
    def get_ui_state(self) -> Dict[str, Any]:
        """Get UI state"""
        return self.ui_state.copy()
    
    def _on_page_loaded(self, page: int, data: List[T]):
        """Handle page loaded event"""
        # Update visible pages
        visible_pages = [page]
        
        # Add adjacent pages
        if page > 1:
            visible_pages.append(page - 1)
        if page < self.ui_state['total_pages']:
            visible_pages.append(page + 1)
        
        self.ui_state['visible_pages'] = visible_pages
        
        # Log performance
        self.logger.debug(f"Page {page} loaded with {len(data)} items")
    
    def _on_loading_started(self):
        """Handle loading started event"""
        self.ui_state['loading'] = True
        self.logger.debug("Loading started")
    
    def _on_loading_completed(self):
        """Handle loading completed event"""
        self.ui_state['loading'] = False
        self.logger.debug("Loading completed")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report"""
        report = {
            'active_loader': self.current_loader_id,
            'ui_state': self.ui_state,
            'loaders': {}
        }
        
        with self.loaders_lock:
            for loader_id, loader in self.loaders.items():
                report['loaders'][loader_id] = {
                    'stats': loader.get_cache_stats(),
                    'total_items': loader.total_items,
                    'total_pages': loader.total_pages,
                    'current_page': loader.current_page
                }
        
        return report

class PaginationUIHelper:
    """Helper class for pagination UI components"""
    
    def __init__(self, pagination_manager: PaginationManager):
        self.pagination_manager = pagination_manager
        self.logger = logging.getLogger(__name__)
        
        # UI state
        self.ui_components = {}
        self.update_callbacks = []
    
    def create_page_selector(self, parent, loader_id: str = None):
        """Create page selector UI component"""
        # This would create actual UI components in a real implementation
        # For now, we'll return a mock component
        return {
            'type': 'page_selector',
            'loader_id': loader_id,
            'current_page': self.pagination_manager.ui_state['current_page'],
            'total_pages': self.pagination_manager.ui_state['total_pages'],
            'has_previous': self.pagination_manager.ui_state['current_page'] > 1,
            'has_next': self.pagination_manager.ui_state['current_page'] < self.pagination_manager.ui_state['total_pages']
        }
    
    def create_page_size_selector(self, parent, loader_id: str = None):
        """Create page size selector UI component"""
        return {
            'type': 'page_size_selector',
            'loader_id': loader_id,
            'current_page_size': self.pagination_manager.ui_state['page_size'],
            'available_sizes': [25, 50, 100, 200]
        }
    
    def create_pagination_info(self, parent, loader_id: str = None):
        """Create pagination info UI component"""
        info = self.pagination_manager.get_pagination_info(loader_id)
        
        return {
            'type': 'pagination_info',
            'loader_id': loader_id,
            'current_page': info.get('current_page', 1),
            'total_pages': info.get('total_pages', 1),
            'total_items': info.get('total_items', 0),
            'page_size': info.get('page_size', 50)
        }
    
    def update_ui(self, loader_id: str = None):
        """Update UI components"""
        # This would update actual UI components in a real implementation
        info = self.pagination_manager.get_pagination_info(loader_id)
        
        # Trigger update callbacks
        for callback in self.update_callbacks:
            try:
                callback(info)
            except Exception as e:
                self.logger.error(f"UI update callback error: {e}")
    
    def add_update_callback(self, callback: Callable):
        """Add UI update callback"""
        self.update_callbacks.append(callback)

# Global pagination manager instance
_pagination_manager = None

def get_pagination_manager() -> PaginationManager:
    """Get global pagination manager instance"""
    global _pagination_manager
    if _pagination_manager is None:
        _pagination_manager = PaginationManager()
    return _pagination_manager