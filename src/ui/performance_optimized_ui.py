"""
Performance Optimized UI Components for Desktop POS Application
Implements virtual scrolling, widget reuse, and efficient UI rendering
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import logging
from queue import Queue, Empty
import weakref

from src.config.performance_config import PerformanceConfig
from src.utils.lazy_loader import get_lazy_load_helper, ResourceType, LoadPriority

T = TypeVar('T')

class ScrollDirection(Enum):
    """Scroll direction"""
    UP = "up"
    DOWN = "down"
    NONE = "none"

@dataclass
class UIComponent:
    """UI component information"""
    component_id: str
    component_type: str
    created_at: float
    last_used: float
    usage_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

class VirtualScrollableFrame(ttk.Frame):
    """Virtual scrollable frame for efficient large list rendering"""
    
    def __init__(self, parent, item_height: int = 50, visible_items: int = 10, 
                 on_item_select: Callable = None, on_scroll: Callable = None):
        super().__init__(parent)
        
        self.item_height = item_height
        self.visible_items = visible_items
        self.on_item_select = on_item_select
        self.on_scroll = on_scroll
        
        # Data
        self.items = []
        self.visible_range = (0, 0)
        
        # UI components
        self.canvas = None
        self.scrollbar = None
        self.inner_frame = None
        self.item_widgets = {}
        
        # State
        self.selected_index = -1
        self.scroll_direction = ScrollDirection.NONE
        
        # Performance tracking
        self.render_times = []
        self.scroll_times = []
        
        # Initialize UI
        self._setup_ui()
        
        # Bind events
        self._bind_events()
    
    def _setup_ui(self):
        """Setup UI components"""
        # Create main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(container, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._on_scroll)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create inner frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)
        
        # Configure canvas
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _bind_events(self):
        """Bind event handlers"""
        # Mouse wheel
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)  # Linux
        self.canvas.bind('<Button-5>', self._on_mousewheel)  # Linux
        
        # Canvas scroll
        self.canvas.bind('<B1-Motion>', self._on_canvas_scroll)
        self.canvas.bind('<ButtonPress-1>', self._on_canvas_press)
        
        # Frame configure
        self.inner_frame.bind('<Configure>', self._on_inner_frame_configure)
    
    def set_items(self, items: List[T]):
        """Set items to display"""
        start_time = time.time()
        
        self.items = items
        self._update_visible_range()
        self._render_visible_items()
        
        # Track render time
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Keep only last 100 render times
        if len(self.render_times) > 100:
            self.render_times = self.render_times[-100:]
        
        # Update scrollable region
        self._update_scrollable_region()
    
    def _update_visible_range(self):
        """Update visible range based on canvas height"""
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1:
            return
        
        # Calculate visible range
        visible_height = canvas_height
        max_visible = min(len(self.items), self.visible_items)
        
        # Adjust visible items based on performance
        avg_render_time = sum(self.render_times[-10:]) / len(self.render_times[-10:]) if self.render_times else 0.01
        if avg_render_time > 0.1:  # If rendering is slow, reduce visible items
            max_visible = min(max_visible, max(5, int(self.visible_items * 0.5)))
        
        # Calculate range
        total_height = len(self.items) * self.item_height
        scroll_percentage = self.canvas.yview()[0] if self.canvas.yview() else 0
        
        start_item = int(scroll_percentage * total_height / self.item_height)
        end_item = min(start_item + max_visible, len(self.items))
        
        self.visible_range = (start_item, end_item)
    
    def _render_visible_items(self):
        """Render only visible items"""
        start_time = time.time()
        
        # Clear existing widgets
        for widget in self.item_widgets.values():
            try:
                widget.destroy()
            except:
                pass
        
        self.item_widgets.clear()
        
        # Render visible items
        start_idx, end_idx = self.visible_range
        
        for i in range(start_idx, end_idx):
            if i < len(self.items):
                item = self.items[i]
                widget = self._create_item_widget(i, item)
                self.item_widgets[i] = widget
        
        # Track render time
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Trigger scroll callback
        if self.on_scroll:
            self.on_scroll(self.visible_range)
    
    def _create_item_widget(self, index: int, item: T) -> ttk.Frame:
        """Create item widget"""
        frame = ttk.Frame(self.inner_frame, height=self.item_height)
        frame.pack(fill=tk.X, pady=1)
        
        # Bind click event
        frame.bind('<Button-1>', lambda e: self._on_item_click(index))
        
        # Create item content based on item type
        if isinstance(item, dict):
            self._render_dict_item(frame, index, item)
        else:
            self._render_simple_item(frame, index, item)
        
        return frame
    
    def _render_dict_item(self, frame: ttk.Frame, index: int, item: Dict[str, Any]):
        """Render dictionary item"""
        # Create labels based on available keys
        if 'name' in item:
            name_label = ttk.Label(frame, text=item['name'], font=('Arial', 10, 'bold'))
            name_label.pack(anchor=tk.W, padx=5, pady=2)
        
        if 'description' in item:
            desc_label = ttk.Label(frame, text=item['description'], font=('Arial', 9))
            desc_label.pack(anchor=tk.W, padx=5, pady=1)
        
        if 'price' in item:
            price_label = ttk.Label(frame, text=f"${item['price']:.2f}", font=('Arial', 9, 'bold'))
            price_label.pack(anchor=tk.E, padx=5, pady=2)
    
    def _render_simple_item(self, frame: ttk.Frame, index: int, item: Any):
        """Render simple item"""
        item_label = ttk.Label(frame, text=str(item), font=('Arial', 10))
        item_label.pack(anchor=tk.W, padx=5, pady=10)
    
    def _on_item_click(self, index: int):
        """Handle item click"""
        self.selected_index = index
        
        # Update selection visual
        for i, widget in self.item_widgets.items():
            if i == index:
                widget.configure(style='Selected.TFrame')
            else:
                widget.configure(style='TFrame')
        
        # Trigger callback
        if self.on_item_select:
            self.on_item_select(index, self.items[index])
    
    def _on_scroll(self, *args):
        """Handle scroll"""
        start_time = time.time()
        
        if args:
            # Scrollbar event
            self.canvas.yview(*args)
        else:
            # Manual scroll
            pass
        
        # Update visible range
        self._update_visible_range()
        self._render_visible_items()
        
        # Track scroll time
        scroll_time = time.time() - start_time
        self.scroll_times.append(scroll_time)
        
        # Keep only last 100 scroll times
        if len(self.scroll_times) > 100:
            self.scroll_times = self.scroll_times[-100:]
        
        # Trigger scroll callback
        if self.on_scroll:
            self.on_scroll(self.visible_range)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel"""
        # Determine scroll direction
        if event.delta:
            # Windows
            scroll_amount = event.delta
        else:
            # Linux
            scroll_amount = 120 if event.num == 4 else -120
        
        # Scroll
        self.canvas.yview_scroll(int(-scroll_amount / 120), "units")
    
    def _on_canvas_scroll(self, event):
        """Handle canvas scroll"""
        # Calculate scroll delta
        delta = event.y - getattr(self, '_last_y', event.y)
        self._last_y = event.y
        
        # Scroll
        if abs(delta) > 5:  # Minimum threshold
            self.canvas.yview_scroll(int(-delta / 10), "units")
    
    def _on_canvas_press(self, event):
        """Handle canvas press"""
        self._last_y = event.y
    
    def _on_canvas_configure(self, event):
        """Handle canvas configure"""
        # Update visible range when canvas size changes
        self._update_visible_range()
        self._render_visible_items()
        self._update_scrollable_region()
    
    def _on_inner_frame_configure(self, event):
        """Handle inner frame configure"""
        # Update scrollable region
        self._update_scrollable_region()
    
    def _update_scrollable_region(self):
        """Update scrollable region"""
        if self.inner_frame.winfo_height() > 0:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def get_selected_item(self) -> Optional[T]:
        """Get selected item"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_items': len(self.items),
            'visible_items': len(self.item_widgets),
            'visible_range': self.visible_range,
            'avg_render_time': sum(self.render_times) / len(self.render_times) if self.render_times else 0,
            'avg_scroll_time': sum(self.scroll_times) / len(self.scroll_times) if self.scroll_times else 0,
            'render_times': self.render_times[-10:],  # Last 10 render times
            'scroll_times': self.scroll_times[-10:]   # Last 10 scroll times
        }

class LazyLoadingListbox(ttk.Frame):
    """Lazy loading listbox for progressive data loading"""
    
    def __init__(self, parent, item_height: int = 25, visible_items: int = 10,
                 on_item_select: Callable = None, on_scroll: Callable = None,
                 data_loader: Callable = None):
        super().__init__(parent)
        
        self.item_height = item_height
        self.visible_items = visible_items
        self.on_item_select = on_item_select
        self.on_scroll = on_scroll
        self.data_loader = data_loader
        
        # Data
        self.items = []
        self.visible_range = (0, 0)
        self.loading = False
        
        # UI components
        self.canvas = None
        self.scrollbar = None
        self.inner_frame = None
        self.item_labels = {}
        
        # State
        self.selected_index = -1
        
        # Performance tracking
        self.load_times = []
        self.render_times = []
        
        # Lazy loading helper
        self.lazy_helper = get_lazy_load_helper()
        
        # Initialize UI
        self._setup_ui()
        
        # Bind events
        self._bind_events()
        
        # Start background loading
        self._start_background_loading()
    
    def _setup_ui(self):
        """Setup UI components"""
        # Create main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(container, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._on_scroll)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create inner frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)
        
        # Configure canvas
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _bind_events(self):
        """Bind event handlers"""
        # Mouse wheel
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)  # Linux
        self.canvas.bind('<Button-5>', self._on_mousewheel)  # Linux
        
        # Canvas scroll
        self.canvas.bind('<B1-Motion>', self._on_canvas_scroll)
        self.canvas.bind('<ButtonPress-1>', self._on_canvas_press)
        
        # Frame configure
        self.inner_frame.bind('<Configure>', self._on_inner_frame_configure)
    
    def set_items(self, items: List[T]):
        """Set items to display"""
        start_time = time.time()
        
        self.items = items
        self._update_visible_range()
        self._render_visible_items()
        
        # Track render time
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Keep only last 100 render times
        if len(self.render_times) > 100:
            self.render_times = self.render_times[-100:]
        
        # Update scrollable region
        self._update_scrollable_region()
    
    def _start_background_loading(self):
        """Start background loading"""
        def background_worker():
            while True:
                try:
                    # Check if we need to load more items
                    self._check_and_load_items()
                    
                    # Sleep briefly
                    time.sleep(0.1)
                    
                except Exception as e:
                    logging.error(f"Background loading error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
    
    def _check_and_load_items(self):
        """Check and load more items if needed"""
        if not self.data_loader or self.loading:
            return
        
        # Check if we're near the end of visible items
        start_idx, end_idx = self.visible_range
        buffer_items = 5  # Number of items to load ahead
        
        if end_idx + buffer_items >= len(self.items) and end_idx < 1000:  # Limit total items
            self._load_more_items()
    
    def _load_more_items(self):
        """Load more items"""
        if not self.data_loader:
            return
        
        try:
            self.loading = True
            
            # Load more items
            new_items = self.data_loader(len(self.items), 20)  # Load 20 more items
            
            if new_items:
                self.items.extend(new_items)
                self._update_visible_range()
                self._render_visible_items()
                self._update_scrollable_region()
            
        except Exception as e:
            logging.error(f"Error loading more items: {e}")
        
        finally:
            self.loading = False
    
    def _update_visible_range(self):
        """Update visible range based on canvas height"""
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1:
            return
        
        # Calculate visible range
        visible_height = canvas_height
        max_visible = min(len(self.items), self.visible_items)
        
        # Adjust visible items based on performance
        avg_render_time = sum(self.render_times[-10:]) / len(self.render_times[-10:]) if self.render_times else 0.01
        if avg_render_time > 0.1:  # If rendering is slow, reduce visible items
            max_visible = min(max_visible, max(5, int(self.visible_items * 0.5)))
        
        # Calculate range
        total_height = len(self.items) * self.item_height
        scroll_percentage = self.canvas.yview()[0] if self.canvas.yview() else 0
        
        start_item = int(scroll_percentage * total_height / self.item_height)
        end_item = min(start_item + max_visible, len(self.items))
        
        self.visible_range = (start_item, end_item)
    
    def _render_visible_items(self):
        """Render only visible items"""
        start_time = time.time()
        
        # Clear existing labels
        for label in self.item_labels.values():
            try:
                label.destroy()
            except:
                pass
        
        self.item_labels.clear()
        
        # Render visible items
        start_idx, end_idx = self.visible_range
        
        for i in range(start_idx, end_idx):
            if i < len(self.items):
                item = self.items[i]
                label = self._create_item_label(i, item)
                self.item_labels[i] = label
        
        # Track render time
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Trigger scroll callback
        if self.on_scroll:
            self.on_scroll(self.visible_range)
    
    def _create_item_label(self, index: int, item: T) -> ttk.Label:
        """Create item label"""
        # Format item text
        if isinstance(item, dict):
            text = item.get('name', str(item))
        else:
            text = str(item)
        
        label = ttk.Label(
            self.inner_frame,
            text=text,
            height=1,
            anchor=tk.W,
            padding=(5, 2)
        )
        label.pack(fill=tk.X, pady=1)
        
        # Bind click event
        label.bind('<Button-1>', lambda e: self._on_item_click(index))
        
        return label
    
    def _on_item_click(self, index: int):
        """Handle item click"""
        self.selected_index = index
        
        # Update selection visual
        for i, label in self.item_labels.items():
            if i == index:
                label.configure(style='Selected.TLabel')
            else:
                label.configure(style='TLabel')
        
        # Trigger callback
        if self.on_item_select:
            self.on_item_select(index, self.items[index])
    
    def _on_scroll(self, *args):
        """Handle scroll"""
        if args:
            # Scrollbar event
            self.canvas.yview(*args)
        else:
            # Manual scroll
            pass
        
        # Update visible range
        self._update_visible_range()
        self._render_visible_items()
        
        # Trigger scroll callback
        if self.on_scroll:
            self.on_scroll(self.visible_range)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel"""
        # Determine scroll direction
        if event.delta:
            # Windows
            scroll_amount = event.delta
        else:
            # Linux
            scroll_amount = 120 if event.num == 4 else -120
        
        # Scroll
        self.canvas.yview_scroll(int(-scroll_amount / 120), "units")
    
    def _on_canvas_scroll(self, event):
        """Handle canvas scroll"""
        # Calculate scroll delta
        delta = event.y - getattr(self, '_last_y', event.y)
        self._last_y = event.y
        
        # Scroll
        if abs(delta) > 5:  # Minimum threshold
            self.canvas.yview_scroll(int(-delta / 10), "units")
    
    def _on_canvas_press(self, event):
        """Handle canvas press"""
        self._last_y = event.y
    
    def _on_canvas_configure(self, event):
        """Handle canvas configure"""
        # Update visible range when canvas size changes
        self._update_visible_range()
        self._render_visible_items()
        self._update_scrollable_region()
    
    def _on_inner_frame_configure(self, event):
        """Handle inner frame configure"""
        # Update scrollable region
        self._update_scrollable_region()
    
    def _update_scrollable_region(self):
        """Update scrollable region"""
        if self.inner_frame.winfo_height() > 0:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def get_selected_item(self) -> Optional[T]:
        """Get selected item"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_items': len(self.items),
            'visible_items': len(self.item_labels),
            'visible_range': self.visible_range,
            'loading': self.loading,
            'avg_render_time': sum(self.render_times) / len(self.render_times) if self.render_times else 0,
            'render_times': self.render_times[-10:],  # Last 10 render times
            'total_loads': len(self.load_times),
            'avg_load_time': sum(self.load_times) / len(self.load_times) if self.load_times else 0
        }

class PerformanceOptimizedTreeview(ttk.Treeview):
    """Performance optimized treeview with caching and virtual scrolling"""
    
    def __init__(self, parent, columns: List[str], show: str = 'tree headings',
                 on_item_select: Callable = None, on_scroll: Callable = None):
        super().__init__(parent, columns=columns, show=show)
        
        self.on_item_select = on_item_select
        self.on_scroll = on_scroll
        
        # Data cache
        self.data_cache = {}
        self.cache_lock = threading.RLock()
        
        # Virtual scrolling
        self.visible_range = (0, 0)
        self.item_height = 20
        self.visible_items = 50
        
        # Performance tracking
        self.render_times = []
        self.scroll_times = []
        
        # Bind events
        self._bind_events()
    
    def _bind_events(self):
        """Bind event handlers"""
        # Selection
        self.bind('<<TreeviewSelect>>', self._on_item_select)
        
        # Scroll
        self.bind('<MouseWheel>', self._on_mousewheel)
        self.bind('<Button-4>', self._on_mousewheel)  # Linux
        self.bind('<Button-5>', self._on_mousewheel)  # Linux
    
    def set_data(self, data: List[Dict[str, Any]]):
        """Set data to display"""
        start_time = time.time()
        
        # Clear existing data
        self.delete(*self.get_children())
        
        # Cache data
        with self.cache_lock:
            self.data_cache = {i: item for i, item in enumerate(data)}
        
        # Update visible range
        self._update_visible_range()
        
        # Render visible items
        self._render_visible_items()
        
        # Track render time
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Keep only last 100 render times
        if len(self.render_times) > 100:
            self.render_times = self.render_times[-100:]
    
    def _update_visible_range(self):
        """Update visible range"""
        canvas_height = self.winfo_height()
        if canvas_height <= 1:
            return
        
        # Calculate visible range
        max_visible = min(len(self.data_cache), self.visible_items)
        
        # Adjust visible items based on performance
        avg_render_time = sum(self.render_times[-10:]) / len(self.render_times[-10:]) if self.render_times else 0.01
        if avg_render_time > 0.1:  # If rendering is slow, reduce visible items
            max_visible = min(max_visible, max(20, int(self.visible_items * 0.5)))
        
        # Calculate range
        scroll_percentage = self.yview()[0] if self.yview() else 0
        canvas_height = self.winfo_height()
        
        start_item = int(scroll_percentage * len(self.data_cache))
        end_item = min(start_item + max_visible, len(self.data_cache))
        
        self.visible_range = (start_item, end_item)
    
    def _render_visible_items(self):
        """Render only visible items"""
        start_time = time.time()
        
        # Clear visible items
        visible_items = self.get_children()
        if visible_items:
            self.delete(*visible_items)
        
        # Render visible items
        start_idx, end_idx = self.visible_range
        
        for i in range(start_idx, end_idx):
            if i in self.data_cache:
                item = self.data_cache[i]
                values = [str(item.get(col, '')) for col in self['columns']]
                self.insert('', 'end', iid=str(i), values=values)
        
        # Track render time
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Trigger scroll callback
        if self.on_scroll:
            self.on_scroll(self.visible_range)
    
    def _on_item_select(self, event):
        """Handle item selection"""
        selection = self.selection()
        if selection:
            item_id = selection[0]
            if item_id in self.data_cache:
                item = self.data_cache[item_id]
                if self.on_item_select:
                    self.on_item_select(int(item_id), item)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel"""
        # Determine scroll direction
        if event.delta:
            # Windows
            scroll_amount = event.delta
        else:
            # Linux
            scroll_amount = 120 if event.num == 4 else -120
        
        # Scroll
        self.yview_scroll(int(-scroll_amount / 120), "units")
        
        # Update visible range
        self._update_visible_range()
        self._render_visible_items()
    
    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """Get selected item"""
        selection = self.selection()
        if selection:
            item_id = selection[0]
            if item_id in self.data_cache:
                return self.data_cache[item_id]
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_items': len(self.data_cache),
            'visible_items': len(self.get_children()),
            'visible_range': self.visible_range,
            'avg_render_time': sum(self.render_times) / len(self.render_times) if self.render_times else 0,
            'render_times': self.render_times[-10:]  # Last 10 render times
        }

class DebouncedEntry(ttk.Entry):
    """Debounced entry widget for efficient input handling"""
    
    def __init__(self, parent, debounce_time: float = 0.3, on_change: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.debounce_time = debounce_time
        self.on_change = on_change
        
        # State
        self._after_id = None
        self._last_value = ''
        
        # Bind events
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_key_release(self, event):
        """Handle key release with debouncing"""
        # Cancel existing debounce
        if self._after_id:
            self.after_cancel(self._after_id)
        
        # Schedule new debounce
        self._after_id = self.after(int(self.debounce_time * 1000), self._debounced_change)
    
    def _on_focus_out(self, event):
        """Handle focus out"""
        # Cancel existing debounce
        if self._after_id:
            self.after_cancel(self._after_id)
        
        # Trigger immediate change
        self._debounced_change()
    
    def _debounced_change(self):
        """Handle debounced change"""
        current_value = self.get()
        
        if current_value != self._last_value:
            self._last_value = current_value
            
            if self.on_change:
                self.on_change(current_value)
        
        self._after_id = None
    
    def get_debounced_value(self) -> str:
        """Get current debounced value"""
        return self._last_value

class ObjectPool:
    """Generic object pool for reusing expensive objects"""
    
    def __init__(self, factory: Callable, max_size: int = 10, reset_func: Callable = None):
        self.factory = factory
        self.max_size = max_size
        self.reset_func = reset_func
        
        # Pool
        self.pool = []
        self.in_use = set()
        
        # Lock
        self.lock = threading.RLock()
        
        # Statistics
        self.created = 0
        self.reused = 0
        self.returned = 0
    
    def get(self) -> Any:
        """Get object from pool"""
        with self.lock:
            # Try to get from pool
            if self.pool:
                obj = self.pool.pop()
                self.in_use.add(id(obj))
                self.reused += 1
                return obj
            
            # Create new object
            obj = self.factory()
            self.in_use.add(id(obj))
            self.created += 1
            return obj
    
    def return_object(self, obj: Any):
        """Return object to pool"""
        with self.lock:
            obj_id = id(obj)
            
            if obj_id in self.in_use:
                self.in_use.remove(obj_id)
                
                # Reset object if provided
                if self.reset_func:
                    try:
                        self.reset_func(obj)
                    except Exception as e:
                        logging.error(f"Error resetting object: {e}")
                        return
                
                # Add to pool if space available
                if len(self.pool) < self.max_size:
                    self.pool.append(obj)
                else:
                    # Pool is full, discard object
                    pass
                
                self.returned += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            return {
                'pool_size': len(self.pool),
                'in_use': len(self.in_use),
                'max_size': self.max_size,
                'created': self.created,
                'reused': self.reused,
                'returned': self.returned,
                'hit_rate': self.reused / (self.created + self.reused) if (self.created + self.reused) > 0 else 0
            }
    
    def clear(self):
        """Clear pool"""
        with self.lock:
            self.pool.clear()
            self.in_use.clear()
            self.created = 0
            self.reused = 0
            self.returned = 0

# Global object pools
_widget_pool = None
_image_pool = None

def get_widget_pool() -> ObjectPool:
    """Get global widget pool"""
    global _widget_pool
    if _widget_pool is None:
        _widget_pool = ObjectPool(
            factory=lambda: ttk.Frame(None),
            max_size=20,
            reset_func=lambda widget: widget.configure(children=[])
        )
    return _widget_pool

def get_image_pool() -> ObjectPool:
    """Get global image pool"""
    global _image_pool
    if _image_pool is None:
        _image_pool = ObjectPool(
            factory=lambda: None,  # PIL images don't need pooling
            max_size=10
        )
    return _image_pool