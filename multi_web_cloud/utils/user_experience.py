"""
User Experience Enhancements
Provides progressive disclosure, contextual help, and guided workflows
"""

from typing import Dict, List, Optional, Any, Set, Callable
from flask import current_app, request, session
from datetime import datetime
import json
from utils.feature_flag_manager import feature_manager


class UXEnhancement:
    """
    Represents a user experience enhancement
    """
    
    def __init__(self, enhancement_id: str, **kwargs):
        self.enhancement_id = enhancement_id
        self.name = kwargs.get('name', enhancement_id.title())
        self.description = kwargs.get('description', '')
        self.enhancement_type = kwargs.get('enhancement_type', 'general')  # help, guide, feedback, preference
        self.required_features = kwargs.get('required_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.trigger_conditions = kwargs.get('trigger_conditions', [])
        self.display_rules = kwargs.get('display_rules', {})
        self.content = kwargs.get('content', {})
        self.interactions = kwargs.get('interactions', {})
        self.user_preferences = kwargs.get('user_preferences', {})
        self.analytics_events = kwargs.get('analytics_events', [])
        self.priority = kwargs.get('priority', 'medium')
        self.frequency = kwargs.get('frequency', 'once')  # once, daily, weekly, always
        self.duration = kwargs.get('duration', None)  # seconds, None = indefinite
        self.dismissible = kwargs.get('dismissible', True)
        self.css_classes = kwargs.get('css_classes', [])
        self.template = kwargs.get('template', f'ux/{enhancement_id}.html')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert enhancement to dictionary"""
        return {
            'id': self.enhancement_id,
            'name': self.name,
            'description': self.description,
            'type': self.enhancement_type,
            'required_features': self.required_features,
            'retail_types': self.retail_types,
            'trigger_conditions': self.trigger_conditions,
            'display_rules': self.display_rules,
            'content': self.content,
            'interactions': self.interactions,
            'user_preferences': self.user_preferences,
            'analytics_events': self.analytics_events,
            'priority': self.priority,
            'frequency': self.frequency,
            'duration': self.duration,
            'dismissible': self.dismissible,
            'css_classes': self.css_classes,
            'template': self.template
        }


class GuidedWorkflow:
    """
    Represents a guided workflow for users
    """
    
    def __init__(self, workflow_id: str, **kwargs):
        self.workflow_id = workflow_id
        self.name = kwargs.get('name', workflow_id.title())
        self.description = kwargs.get('description', '')
        self.retail_types = kwargs.get('retail_types', [])
        self.required_features = kwargs.get('required_features', [])
        self.target_users = kwargs.get('target_users', [])  # new, returning, specific_roles
        self.steps = kwargs.get('steps', [])
        self.conditions = kwargs.get('conditions', {})
        self.progress_tracking = kwargs.get('progress_tracking', True)
        self.allow_skip = kwargs.get('allow_skip', True)
        self.allow_resume = kwargs.get('allow_resume', True)
        self.completion_rewards = kwargs.get('completion_rewards', [])
        self.analytics_events = kwargs.get('analytics_events', [])
        self.css_classes = kwargs.get('css_classes', [])
        self.template = kwargs.get('template', f'ux/workflows/{workflow_id}.html')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            'id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'retail_types': self.retail_types,
            'required_features': self.required_features,
            'target_users': self.target_users,
            'steps': self.steps,
            'conditions': self.conditions,
            'progress_tracking': self.progress_tracking,
            'allow_skip': self.allow_skip,
            'allow_resume': self.allow_resume,
            'completion_rewards': self.completion_rewards,
            'analytics_events': self.analytics_events,
            'css_classes': self.css_classes,
            'template': self.template
        }


class ContextualHelp:
    """
    Represents contextual help content
    """
    
    def __init__(self, help_id: str, **kwargs):
        self.help_id = help_id
        self.title = kwargs.get('title', help_id.title())
        self.description = kwargs.get('description', '')
        self.help_type = kwargs.get('help_type', 'tooltip')  # tooltip, modal, sidebar, video
        self.context = kwargs.get('context', {})  # page, element, user_action
        self.content = kwargs.get('content', {})
        self.media = kwargs.get('media', [])  # images, videos, documents
        self.related_topics = kwargs.get('related_topics', [])
        self.search_keywords = kwargs.get('search_keywords', [])
        self.trigger_events = kwargs.get('trigger_events', ['hover', 'focus', 'click'])
        self.display_delay = kwargs.get('display_delay', 500)  # milliseconds
        self.auto_hide = kwargs.get('auto_hide', True)
        self.hide_delay = kwargs.get('hide_delay', 3000)  # milliseconds
        self.positioning = kwargs.get('positioning', {'placement': 'top', 'alignment': 'center'})
        self.css_classes = kwargs.get('css_classes', [])
        self.template = kwargs.get('template', f'ux/help/{help_id}.html')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert help to dictionary"""
        return {
            'id': self.help_id,
            'title': self.title,
            'description': self.description,
            'type': self.help_type,
            'context': self.context,
            'content': self.content,
            'media': self.media,
            'related_topics': self.related_topics,
            'search_keywords': self.search_keywords,
            'trigger_events': self.trigger_events,
            'display_delay': self.display_delay,
            'auto_hide': self.auto_hide,
            'hide_delay': self.hide_delay,
            'positioning': self.positioning,
            'css_classes': self.css_classes,
            'template': self.template
        }


class UserPreference:
    """
    Represents a user preference setting
    """
    
    def __init__(self, preference_id: str, **kwargs):
        self.preference_id = preference_id
        self.name = kwargs.get('name', preference_id.title())
        self.description = kwargs.get('description', '')
        self.preference_type = kwargs.get('preference_type', 'boolean')  # boolean, select, number, text
        self.default_value = kwargs.get('default_value', None)
        self.options = kwargs.get('options', [])  # For select type
        self.validation = kwargs.get('validation', {})
        self.category = kwargs.get('category', 'general')
        self.required_features = kwargs.get('required_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.user_interface = kwargs.get('user_interface', 'both')  # desktop, mobile, both
        self.persistence = kwargs.get('persistence', 'permanent')  # session, permanent
        self.affects_ui = kwargs.get('affects_ui', True)
        self.affects_behavior = kwargs.get('affects_behavior', False)
        self.css_classes = kwargs.get('css_classes', [])
        self.template = kwargs.get('template', f'ux/preferences/{preference_id}.html')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preference to dictionary"""
        return {
            'id': self.preference_id,
            'name': self.name,
            'description': self.description,
            'type': self.preference_type,
            'default_value': self.default_value,
            'options': self.options,
            'validation': self.validation,
            'category': self.category,
            'required_features': self.required_features,
            'retail_types': self.retail_types,
            'user_interface': self.user_interface,
            'persistence': self.persistence,
            'affects_ui': self.affects_ui,
            'affects_behavior': self.affects_behavior,
            'css_classes': self.css_classes,
            'template': self.template
        }


class UXEnhancementManager:
    """
    Manages user experience enhancements
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.enhancements = {}
        self.workflows = {}
        self.help_content = {}
        self.preferences = {}
        self.user_progress = {}
        self.user_dismissals = {}
        self.analytics_events = []
        self.personalization_engine = None
        self._initialized = False
    
    def initialize(self):
        """Initialize UX enhancement manager"""
        if self._initialized:
            return
        
        self._load_default_enhancements()
        self._load_guided_workflows()
        self._load_contextual_help()
        self._load_user_preferences()
        self._initialize_personalization()
        self._initialized = True
    
    def _load_default_enhancements(self):
        """Load default UX enhancements"""
        enhancements = [
            # Progressive disclosure enhancements
            UXEnhancement(
                'progressive_disclosure',
                name='Progressive Feature Disclosure',
                description='Gradually reveal features as users become more comfortable',
                enhancement_type='help',
                trigger_conditions=[
                    {'event': 'user_session_count', 'operator': '>', 'value': 1},
                    {'event': 'feature_completed', 'operator': '>=', 'value': 3}
                ],
                content={
                    'title': 'Discover Advanced Features',
                    'message': 'You\'re doing great! Here are some advanced features you might find useful.',
                    'features': ['advanced_reporting', 'bulk_operations', 'automation']
                },
                display_rules={
                    'position': 'bottom_right',
                    'animation': 'slide_in',
                    'timing': 'after_page_load',
                    'delay': 2000
                },
                frequency='daily',
                dismissible=True,
                css_classes=['progressive-disclosure']
            ),
            UXEnhancement(
                'feature_highlights',
                name='Feature Highlights',
                description='Highlight new or underutilized features',
                enhancement_type='help',
                trigger_conditions=[
                    {'event': 'new_feature_enabled', 'operator': 'exists'},
                    {'event': 'feature_usage_low', 'operator': 'exists'}
                ],
                content={
                    'title': 'Try This Feature',
                    'message': 'Discover this powerful feature to improve your workflow.',
                    'highlight_duration': 5000
                },
                display_rules={
                    'position': 'feature_context',
                    'animation': 'pulse',
                    'timing': 'on_element_hover'
                },
                frequency='weekly',
                dismissible=True,
                css_classes=['feature-highlight']
            ),
            # Contextual help enhancements
            UXEnhancement(
                'smart_tooltips',
                name='Smart Tooltips',
                description='Context-aware tooltips that adapt to user behavior',
                enhancement_type='help',
                trigger_conditions=[
                    {'event': 'element_hover', 'operator': 'duration', 'value': 1000},
                    {'event': 'element_focus', 'operator': 'exists'}
                ],
                content={
                    'adaptive': True,
                    'learning_enabled': True,
                    'context_aware': True
                },
                display_rules={
                    'position': 'smart',
                    'animation': 'fade',
                    'timing': 'intelligent'
                },
                frequency='always',
                dismissible=False,
                css_classes=['smart-tooltips']
            ),
            UXEnhancement(
                'interactive_tours',
                name='Interactive Tours',
                description='Step-by-step interactive tours for complex features',
                enhancement_type='guide',
                trigger_conditions=[
                    {'event': 'first_visit', 'operator': 'equals', 'value': True},
                    {'event': 'feature_first_use', 'operator': 'exists'}
                ],
                content={
                    'interactive': True,
                    'step_by_step': True,
                    'highlight_elements': True,
                    'allow_skip': True
                },
                display_rules={
                    'position': 'overlay',
                    'animation': 'fade',
                    'timing': 'on_page_load'
                },
                frequency='once',
                dismissible=True,
                css_classes=['interactive-tour']
            ),
            # Feedback enhancements
            UXEnhancement(
                'micro_feedback',
                name='Micro Feedback',
                description='Subtle feedback for user actions',
                enhancement_type='feedback',
                trigger_conditions=[
                    {'event': 'user_action', 'operator': 'exists'}
                ],
                content={
                    'success_animations': ['checkmark', 'confetti', 'pulse'],
                    'error_animations': ['shake', 'highlight', 'fade'],
                    'loading_animations': ['spinner', 'progress', 'skeleton']
                },
                display_rules={
                    'position': 'action_context',
                    'animation': 'subtle',
                    'timing': 'immediate'
                },
                frequency='always',
                dismissible=False,
                css_classes=['micro-feedback']
            ),
            UXEnhancement(
                'achievement_system',
                name='Achievement System',
                description='Gamification through achievements and milestones',
                enhancement_type='feedback',
                trigger_conditions=[
                    {'event': 'milestone_reached', 'operator': 'exists'},
                    {'event': 'goal_completed', 'operator': 'exists'}
                ],
                content={
                    'achievements': ['first_order', 'hundred_orders', 'perfect_day'],
                    'milestones': ['daily_target', 'weekly_target', 'monthly_target'],
                    'rewards': ['badges', 'points', 'recognition']
                },
                display_rules={
                    'position': 'notification_center',
                    'animation': 'celebration',
                    'timing': 'on_event'
                },
                frequency='always',
                dismissible=True,
                css_classes=['achievement-system']
            )
        ]
        
        for enhancement in enhancements:
            self.enhancements[enhancement.enhancement_id] = enhancement
    
    def _load_guided_workflows(self):
        """Load guided workflows"""
        workflows = [
            # Restaurant workflows
            GuidedWorkflow(
                'restaurant_first_order',
                name='First Order Workflow',
                description='Guide for processing first restaurant order',
                retail_types=['restaurant'],
                required_features=['FEATURE_SALES_PROCESSING'],
                target_users=['new'],
                steps=[
                    {
                        'id': 'select_table',
                        'title': 'Select Table',
                        'description': 'Choose the table for this order',
                        'element': '#table-selector',
                        'action': 'click_table',
                        'validation': 'table_selected'
                    },
                    {
                        'id': 'add_items',
                        'title': 'Add Menu Items',
                        'description': 'Add items from the menu to the order',
                        'element': '#menu-grid',
                        'action': 'add_items',
                        'validation': 'items_added'
                    },
                    {
                        'id': 'review_order',
                        'title': 'Review Order',
                        'description': 'Review the order before sending to kitchen',
                        'element': '#order-summary',
                        'action': 'review_order',
                        'validation': 'order_reviewed'
                    },
                    {
                        'id': 'send_to_kitchen',
                        'title': 'Send to Kitchen',
                        'description': 'Send the order to the kitchen display',
                        'element': '#send-kitchen-btn',
                        'action': 'send_order',
                        'validation': 'order_sent'
                    },
                    {
                        'id': 'process_payment',
                        'title': 'Process Payment',
                        'description': 'Complete the payment process',
                        'element': '#payment-panel',
                        'action': 'process_payment',
                        'validation': 'payment_processed'
                    }
                ],
                conditions={
                    'user_type': 'new',
                    'order_count': 0,
                    'session_age': '< 1 hour'
                },
                allow_skip=True,
                allow_resume=True,
                completion_rewards=['first_order_badge', 'tutorial_complete_points'],
                css_classes=['restaurant-first-order']
            ),
            # Retail workflows
            GuidedWorkflow(
                'retail_quick_sale',
                name='Quick Sale Workflow',
                description='Guide for processing quick retail sale',
                retail_types=['retail'],
                required_features=['FEATURE_SALES_PROCESSING'],
                target_users=['new'],
                steps=[
                    {
                        'id': 'scan_product',
                        'title': 'Scan Product',
                        'description': 'Scan the product barcode or search for it',
                        'element': '#barcode-scanner',
                        'action': 'scan_product',
                        'validation': 'product_scanned'
                    },
                    {
                        'id': 'add_to_cart',
                        'title': 'Add to Cart',
                        'description': 'Add the product to the cart',
                        'element': '#add-to-cart',
                        'action': 'add_to_cart',
                        'validation': 'item_added'
                    },
                    {
                        'id': 'customer_info',
                        'title': 'Customer Information',
                        'description': 'Add customer details if needed',
                        'element': '#customer-info',
                        'action': 'add_customer',
                        'validation': 'customer_added',
                        'optional': True
                    },
                    {
                        'id': 'process_payment',
                        'title': 'Process Payment',
                        'description': 'Complete the payment process',
                        'element': '#payment-panel',
                        'action': 'process_payment',
                        'validation': 'payment_processed'
                    }
                ],
                conditions={
                    'user_type': 'new',
                    'sale_count': 0
                },
                allow_skip=True,
                allow_resume=True,
                completion_rewards=['quick_sale_badge', 'tutorial_complete_points'],
                css_classes=['retail-quick-sale']
            ),
            # Apparel workflows
            GuidedWorkflow(
                'apparel_variant_selection',
                name='Variant Selection Workflow',
                description='Guide for selecting product variants',
                retail_types=['apparel'],
                required_features=['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS'],
                target_users=['new'],
                steps=[
                    {
                        'id': 'select_size',
                        'title': 'Select Size',
                        'description': 'Choose the appropriate size',
                        'element': '#size-selector',
                        'action': 'select_size',
                        'validation': 'size_selected'
                    },
                    {
                        'id': 'select_color',
                        'title': 'Select Color',
                        'description': 'Choose the desired color',
                        'element': '#color-selector',
                        'action': 'select_color',
                        'validation': 'color_selected'
                    },
                    {
                        'id': 'check_availability',
                        'title': 'Check Availability',
                        'description': 'Verify the selected combination is available',
                        'element': '#availability-check',
                        'action': 'check_availability',
                        'validation': 'availability_checked'
                    }
                ],
                conditions={
                    'user_type': 'new',
                    'variant_selection_count': 0
                },
                allow_skip=True,
                allow_resume=True,
                completion_rewards=['variant_master_badge'],
                css_classes=['apparel-variant-selection']
            )
        ]
        
        for workflow in workflows:
            self.workflows[workflow.workflow_id] = workflow
    
    def _load_contextual_help(self):
        """Load contextual help content"""
        help_content = [
            # General help
            ContextualHelp(
                'navigation_help',
                title='Navigation Help',
                description='Learn how to navigate the interface',
                help_type='sidebar',
                context={'page': 'all', 'element': 'navigation'},
                content={
                    'sections': [
                        {'title': 'Main Menu', 'content': 'Use the main menu to access different modules'},
                        {'title': 'Quick Actions', 'content': 'Quick actions provide fast access to common tasks'},
                        {'title': 'Search', 'content': 'Use search to quickly find items or information'}
                    ]
                },
                trigger_events=['click', 'keyboard_shortcut'],
                positioning={'placement': 'right', 'alignment': 'top'},
                css_classes=['navigation-help']
            ),
            ContextualHelp(
                'order_help',
                title='Order Help',
                description='Learn how to process orders',
                help_type='modal',
                context={'page': 'orders', 'element': 'order_form'},
                content={
                    'steps': [
                        {'title': 'Select Customer/Table', 'content': 'Choose customer or table for the order'},
                        {'title': 'Add Items', 'content': 'Add products or menu items to the order'},
                        {'title': 'Review', 'content': 'Review order details and totals'},
                        {'title': 'Process Payment', 'content': 'Complete the payment process'}
                    ]
                },
                media=[
                    {'type': 'video', 'url': '/help/videos/order_process.mp4', 'title': 'Order Process Video'},
                    {'type': 'document', 'url': '/help/docs/order_guide.pdf', 'title': 'Order Guide PDF'}
                ],
                trigger_events=['focus', 'help_button'],
                positioning={'placement': 'center', 'alignment': 'center'},
                css_classes=['order-help']
            ),
            # Feature-specific help
            ContextualHelp(
                'barcode_scanner_help',
                title='Barcode Scanner Help',
                description='Learn how to use the barcode scanner',
                help_type='tooltip',
                context={'page': 'orders', 'element': 'barcode_scanner'},
                content={
                    'quick_tips': [
                        'Position barcode properly in scanner view',
                        'Ensure good lighting conditions',
                        'Hold steady until scan completes',
                        'Manual entry available as backup'
                    ]
                },
                trigger_events=['hover', 'focus'],
                display_delay=500,
                auto_hide=True,
                hide_delay=3000,
                positioning={'placement': 'bottom', 'alignment': 'center'},
                css_classes=['barcode-scanner-help']
            ),
            ContextualHelp(
                'table_management_help',
                title='Table Management Help',
                description='Learn how to manage restaurant tables',
                help_type='tooltip',
                context={'page': 'tables', 'element': 'table_grid'},
                content={
                    'quick_tips': [
                        'Click table to select it',
                        'Drag to reorganize layout',
                        'Right-click for table options',
                        'Double-click for quick order'
                    ]
                },
                trigger_events=['hover', 'focus'],
                display_delay=500,
                auto_hide=True,
                hide_delay=3000,
                positioning={'placement': 'top', 'alignment': 'left'},
                css_classes=['table-management-help']
            )
        ]
        
        for help_item in help_content:
            self.help_content[help_item.help_id] = help_item
    
    def _load_user_preferences(self):
        """Load user preference definitions"""
        preferences = [
            # Interface preferences
            UserPreference(
                'theme_selection',
                name='Theme Selection',
                description='Choose your preferred interface theme',
                preference_type='select',
                default_value='default',
                options=[
                    {'value': 'default', 'label': 'Default'},
                    {'value': 'dark', 'label': 'Dark'},
                    {'value': 'light', 'label': 'Light'},
                    {'value': 'high_contrast', 'label': 'High Contrast'}
                ],
                category='interface',
                affects_ui=True,
                css_classes=['theme-preference']
            ),
            UserPreference(
                'language_selection',
                name='Language Selection',
                description='Choose your preferred language',
                preference_type='select',
                default_value='en',
                options=[
                    {'value': 'en', 'label': 'English'},
                    {'value': 'es', 'label': 'Español'},
                    {'value': 'fr', 'label': 'Français'},
                    {'value': 'de', 'label': 'Deutsch'},
                    {'value': 'hi', 'label': 'हिंदी'}
                ],
                category='interface',
                affects_ui=True,
                css_classes=['language-preference']
            ),
            UserPreference(
                'auto_save_interval',
                name='Auto-Save Interval',
                description='How often to auto-save your work',
                preference_type='number',
                default_value=300,
                validation={'min': 60, 'max': 3600},
                category='behavior',
                affects_behavior=True,
                css_classes=['auto-save-preference']
            ),
            UserPreference(
                'notification_preferences',
                name='Notification Preferences',
                description='Choose which notifications to receive',
                preference_type='boolean',
                default_value=True,
                category='notifications',
                affects_behavior=True,
                css_classes=['notification-preference']
            ),
            UserPreference(
                'keyboard_shortcuts_enabled',
                name='Enable Keyboard Shortcuts',
                description='Enable keyboard shortcuts for common actions',
                preference_type='boolean',
                default_value=True,
                category='accessibility',
                affects_behavior=True,
                css_classes=['keyboard-shortcuts-preference']
            ),
            UserPreference(
                'animation_preferences',
                name='Enable Animations',
                description='Enable interface animations and transitions',
                preference_type='boolean',
                default_value=True,
                category='interface',
                affects_ui=True,
                css_classes=['animation-preference']
            ),
            # Retail-specific preferences
            UserPreference(
                'default_order_type',
                name='Default Order Type',
                description='Default order type for new orders',
                preference_type='select',
                default_value='dine_in',
                options=[
                    {'value': 'dine_in', 'label': 'Dine In'},
                    {'value': 'takeaway', 'label': 'Takeaway'},
                    {'value': 'delivery', 'label': 'Delivery'}
                ],
                retail_types=['restaurant'],
                required_features=['FEATURE_SALES_PROCESSING'],
                category='workflow',
                affects_behavior=True,
                css_classes=['order-type-preference']
            ),
            UserPreference(
                'barcode_auto_focus',
                name='Auto-Focus Barcode Scanner',
                description='Automatically focus barcode scanner on order page',
                preference_type='boolean',
                default_value=True,
                retail_types=['retail', 'grocery'],
                required_features=['FEATURE_BARCODE_SCANNING'],
                category='workflow',
                affects_behavior=True,
                css_classes=['barcode-focus-preference']
            ),
            UserPreference(
                'show_variant_images',
                name='Show Variant Images',
                description='Display images for product variants',
                preference_type='boolean',
                default_value=True,
                retail_types=['apparel'],
                required_features=['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS'],
                category='interface',
                affects_ui=True,
                css_classes=['variant-images-preference']
            )
        ]
        
        for preference in preferences:
            self.preferences[preference.preference_id] = preference
    
    def _initialize_personalization(self):
        """Initialize the personalization engine"""
        self.personalization_engine = {
            'user_behavior_tracking': True,
            'preference_learning': True,
            'adaptive_content': True,
            'personalization_rules': {
                'new_user_simplification': True,
                'power_user_features': True,
                'usage_based_prioritization': True,
                'time_based_adaptation': True
            }
        }
    
    def get_ux_config(self, tenant_id: Optional[str] = None, 
                      user_id: Optional[str] = None, 
                      user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get UX configuration for user
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get user context
        user_context = user_context or self._get_user_context(user_id)
        
        # Get applicable enhancements
        enhancements = self._get_applicable_enhancements(enabled_features, retail_type, user_context)
        
        # Get available workflows
        workflows = self._get_available_workflows(enabled_features, retail_type, user_context)
        
        # Get relevant help content
        help_content = self._get_relevant_help(enabled_features, retail_type, user_context)
        
        # Get user preferences
        preferences = self._get_user_preferences(enabled_features, retail_type, user_context)
        
        # Get personalization data
        personalization = self._get_personalization_data(user_id, user_context)
        
        return {
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'user_context': user_context,
            'enhancements': [enh.to_dict() for enh in enhancements],
            'workflows': [workflow.to_dict() for workflow in workflows],
            'help_content': [help.to_dict() for help in help_content],
            'preferences': [pref.to_dict() for pref in preferences],
            'personalization': personalization,
            'user_progress': self._get_user_progress(user_id),
            'analytics_events': self.analytics_events
        }
    
    def _get_user_context(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Get user context information"""
        if not user_id:
            return {}
        
        # This would typically fetch from database
        return {
            'user_id': user_id,
            'session_count': 5,  # Example
            'last_login': '2023-12-15T10:30:00Z',
            'total_orders': 25,
            'feature_usage': {
                'barcode_scanner': 15,
                'table_management': 8,
                'kitchen_display': 12
            },
            'completed_workflows': ['restaurant_first_order'],
            'dismissed_enhancements': ['feature_highlights'],
            'preferences': {
                'theme': 'default',
                'language': 'en',
                'notifications': True
            },
            'user_type': 'returning',  # new, returning, power_user
            'device_type': 'desktop',
            'time_of_day': 'morning'
        }
    
    def _get_applicable_enhancements(self, enabled_features: Set[str], retail_type: str, 
                                  user_context: Dict[str, Any]) -> List[UXEnhancement]:
        """Get applicable UX enhancements"""
        applicable_enhancements = []
        
        for enhancement in self.enhancements.values():
            # Check required features
            if enhancement.required_features:
                if not all(feature in enabled_features for feature in enhancement.required_features):
                    continue
            
            # Check retail type compatibility
            if enhancement.retail_types and retail_type not in enhancement.retail_types:
                continue
            
            # Check trigger conditions
            if not self._check_trigger_conditions(enhancement.trigger_conditions, user_context):
                continue
            
            # Check if enhancement has been dismissed
            if enhancement.enhancement_id in user_context.get('dismissed_enhancements', []):
                continue
            
            applicable_enhancements.append(enhancement)
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        applicable_enhancements.sort(key=lambda e: priority_order.get(e.priority, 0), reverse=True)
        
        return applicable_enhancements
    
    def _get_available_workflows(self, enabled_features: Set[str], retail_type: str, 
                              user_context: Dict[str, Any]) -> List[GuidedWorkflow]:
        """Get available guided workflows"""
        available_workflows = []
        
        for workflow in self.workflows.values():
            # Check required features
            if workflow.required_features:
                if not all(feature in enabled_features for feature in workflow.required_features):
                    continue
            
            # Check retail type compatibility
            if workflow.retail_types and retail_type not in workflow.retail_types:
                continue
            
            # Check target users
            if workflow.target_users:
                user_type = user_context.get('user_type', 'new')
                if user_type not in workflow.target_users:
                    continue
            
            # Check conditions
            if not self._check_workflow_conditions(workflow.conditions, user_context):
                continue
            
            # Check if workflow already completed
            if workflow.workflow_id in user_context.get('completed_workflows', []):
                continue
            
            available_workflows.append(workflow)
        
        return available_workflows
    
    def _get_relevant_help(self, enabled_features: Set[str], retail_type: str, 
                           user_context: Dict[str, Any]) -> List[ContextualHelp]:
        """Get relevant help content"""
        relevant_help = []
        
        for help_item in self.help_content.values():
            # Check retail type compatibility
            if hasattr(help_item, 'retail_types') and help_item.retail_types:
                if retail_type not in help_item.retail_types:
                    continue
            
            # Check if help is relevant to current context
            current_page = user_context.get('current_page', '')
            if help_item.context.get('page') and help_item.context['page'] != 'all':
                if help_item.context['page'] != current_page:
                    continue
            
            relevant_help.append(help_item)
        
        return relevant_help
    
    def _get_user_preferences(self, enabled_features: Set[str], retail_type: str, 
                             user_context: Dict[str, Any]) -> List[UserPreference]:
        """Get user preferences"""
        available_preferences = []
        
        for preference in self.preferences.values():
            # Check required features
            if preference.required_features:
                if not all(feature in enabled_features for feature in preference.required_features):
                    continue
            
            # Check retail type compatibility
            if preference.retail_types and retail_type not in preference.retail_types:
                continue
            
            # Check user interface compatibility
            device_type = user_context.get('device_type', 'desktop')
            if preference.user_interface != 'both' and preference.user_interface != device_type:
                continue
            
            available_preferences.append(preference)
        
        # Sort by category
        available_preferences.sort(key=lambda p: p.category)
        
        return available_preferences
    
    def _get_personalization_data(self, user_id: Optional[str], 
                                user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalization data"""
        if not self.personalization_engine:
            return {}
        
        return {
            'behavior_tracking': self.personalization_engine.get('user_behavior_tracking', False),
            'preference_learning': self.personalization_engine.get('preference_learning', False),
            'adaptive_content': self.personalization_engine.get('adaptive_content', False),
            'personalization_rules': self.personalization_engine.get('personalization_rules', {}),
            'learned_preferences': self._get_learned_preferences(user_id),
            'usage_patterns': self._get_usage_patterns(user_id)
        }
    
    def _get_user_progress(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Get user progress information"""
        if not user_id or user_id not in self.user_progress:
            return {}
        
        return self.user_progress[user_id]
    
    def _check_trigger_conditions(self, conditions: List[Dict], user_context: Dict[str, Any]) -> bool:
        """Check if trigger conditions are met"""
        if not conditions:
            return True
        
        for condition in conditions:
            event = condition.get('event')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if event == 'user_session_count':
                session_count = user_context.get('session_count', 0)
                if operator == '>' and session_count > value:
                    return True
            elif event == 'feature_completed':
                completed_features = user_context.get('completed_features', [])
                if operator == '>=' and len(completed_features) >= value:
                    return True
            elif event == 'new_feature_enabled':
                # This would check against actual feature flags
                return True
            elif event == 'feature_usage_low':
                feature_usage = user_context.get('feature_usage', {})
                for feature, usage in feature_usage.items():
                    if usage < 5:  # Low usage threshold
                        return True
            elif event == 'first_visit':
                if user_context.get('session_count', 0) == 1:
                    return True
            elif event == 'feature_first_use':
                feature_usage = user_context.get('feature_usage', {})
                for feature, usage in feature_usage.items():
                    if usage == 1:
                        return True
        
        return False
    
    def _check_workflow_conditions(self, conditions: Dict[str, Any], user_context: Dict[str, Any]) -> bool:
        """Check if workflow conditions are met"""
        if not conditions:
            return True
        
        for condition_key, condition_value in conditions.items():
            if condition_key == 'user_type':
                if user_context.get('user_type') != condition_value:
                    return False
            elif condition_key == 'order_count':
                if user_context.get('total_orders', 0) != condition_value:
                    return False
            elif condition_key == 'session_age':
                # This would check actual session age
                pass
        
        return True
    
    def _get_learned_preferences(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Get learned preferences from user behavior"""
        # This would analyze user behavior and learn preferences
        return {
            'preferred_features': ['barcode_scanner', 'quick_sale'],
            'common_workflows': ['retail_quick_sale'],
            'peak_usage_times': ['morning', 'evening'],
            'preferred_interface_elements': ['keyboard_shortcuts', 'quick_actions']
        }
    
    def _get_usage_patterns(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Get usage patterns for personalization"""
        # This would analyze usage patterns
        return {
            'daily_usage': [2, 5, 3, 8, 12, 6, 4],  # Orders per day
            'feature_frequency': {
                'barcode_scanner': 0.8,
                'customer_search': 0.6,
                'table_management': 0.3
            },
            'workflow_completion': {
                'retail_quick_sale': 0.9,
                'customer_management': 0.4
            },
            'error_patterns': {
                'barcode_scan_failures': 0.1,
                'payment_errors': 0.05
            }
        }
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def record_user_progress(self, user_id: str, workflow_id: str, step_id: str, 
                           progress_data: Dict[str, Any]):
        """Record user progress in workflows"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                'workflows': {},
                'achievements': [],
                'preferences': {},
                'last_updated': datetime.utcnow()
            }
        
        if workflow_id not in self.user_progress[user_id]['workflows']:
            self.user_progress[user_id]['workflows'][workflow_id] = {
                'started_at': datetime.utcnow(),
                'completed_steps': [],
                'current_step': None,
                'completed_at': None
            }
        
        workflow_progress = self.user_progress[user_id]['workflows'][workflow_id]
        workflow_progress['completed_steps'].append(step_id)
        workflow_progress['current_step'] = step_id
        workflow_progress['last_updated'] = datetime.utcnow()
        
        # Add progress data
        if 'data' not in workflow_progress:
            workflow_progress['data'] = {}
        workflow_progress['data'][step_id] = progress_data
    
    def complete_workflow(self, user_id: str, workflow_id: str, 
                        completion_data: Optional[Dict] = None):
        """Mark workflow as completed"""
        if user_id in self.user_progress and workflow_id in self.user_progress[user_id]['workflows']:
            workflow_progress = self.user_progress[user_id]['workflows'][workflow_id]
            workflow_progress['completed_at'] = datetime.utcnow()
            workflow_progress['completion_data'] = completion_data or {}
            
            # Add to completed workflows list
            if 'completed_workflows' not in self.user_progress[user_id]:
                self.user_progress[user_id]['completed_workflows'] = []
            self.user_progress[user_id]['completed_workflows'].append(workflow_id)
    
    def dismiss_enhancement(self, user_id: str, enhancement_id: str):
        """Dismiss an enhancement for user"""
        if user_id not in self.user_dismissals:
            self.user_dismissals[user_id] = []
        
        self.user_dismissals[user_id].append({
            'enhancement_id': enhancement_id,
            'dismissed_at': datetime.utcnow()
        })
    
    def track_analytics_event(self, event_name: str, event_data: Dict[str, Any]):
        """Track analytics event"""
        self.analytics_events.append({
            'event': event_name,
            'data': event_data,
            'timestamp': datetime.utcnow()
        })
        
        # Keep only last 1000 events
        if len(self.analytics_events) > 1000:
            self.analytics_events = self.analytics_events[-1000:]
    
    def register_enhancement(self, enhancement: UXEnhancement):
        """Register a UX enhancement"""
        self.enhancements[enhancement.enhancement_id] = enhancement
    
    def register_workflow(self, workflow: GuidedWorkflow):
        """Register a guided workflow"""
        self.workflows[workflow.workflow_id] = workflow
    
    def register_help_content(self, help_content: ContextualHelp):
        """Register contextual help content"""
        self.help_content[help_content.help_id] = help_content
    
    def register_preference(self, preference: UserPreference):
        """Register a user preference"""
        self.preferences[preference.preference_id] = preference


# Global UX enhancement manager instance
ux_manager = None


def get_ux_manager(feature_manager=None) -> UXEnhancementManager:
    """Get or create global UX enhancement manager instance"""
    global ux_manager
    if ux_manager is None:
        ux_manager = UXEnhancementManager(feature_manager)
    return ux_manager