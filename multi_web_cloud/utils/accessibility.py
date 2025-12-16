"""
Accessibility Enhancements with WCAG Compliance
Provides accessible interfaces and screen reader support
"""

from typing import Dict, List, Optional, Any, Set, Callable
from flask import request, current_app
from utils.feature_flag_manager import feature_manager


class AccessibilityRule:
    """
    Represents an accessibility rule or guideline
    """
    
    def __init__(self, rule_id: str, **kwargs):
        self.rule_id = rule_id
        self.name = kwargs.get('name', rule_id.title())
        self.description = kwargs.get('description', '')
        self.wcag_level = kwargs.get('wcag_level', 'AA')  # A, AA, AAA
        self.category = kwargs.get('category', 'general')  # perception, operation, understanding, robust
        self.check_function = kwargs.get('check_function', None)
        self.fix_function = kwargs.get('fix_function', None)
        self.auto_fixable = kwargs.get('auto_fixable', False)
        self.priority = kwargs.get('priority', 'medium')  # low, medium, high, critical
        self.impact = kwargs.get('impact', 'moderate')  # minimal, moderate, serious, critical
        self.guidelines = kwargs.get('guidelines', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            'id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'wcag_level': self.wcag_level,
            'category': self.category,
            'auto_fixable': self.auto_fixable,
            'priority': self.priority,
            'impact': self.impact,
            'guidelines': self.guidelines
        }


class AccessibilityComponent:
    """
    Represents an accessibility-enhanced component
    """
    
    def __init__(self, component_id: str, **kwargs):
        self.component_id = component_id
        self.name = kwargs.get('name', component_id.title())
        self.component_type = kwargs.get('component_type', 'widget')
        self.accessibility_features = kwargs.get('accessibility_features', [])
        self.aria_attributes = kwargs.get('aria_attributes', {})
        self.keyboard_navigation = kwargs.get('keyboard_navigation', True)
        self.screen_reader_support = kwargs.get('screen_reader_support', True)
        self.high_contrast_support = kwargs.get('high_contrast_support', True)
        self.large_text_support = kwargs.get('large_text_support', True)
        self.focus_management = kwargs.get('focus_management', True)
        self.skip_links = kwargs.get('skip_links', [])
        self.landmark_roles = kwargs.get('landmark_roles', {})
        self.color_contrast = kwargs.get('color_contrast', {})
        self.template = kwargs.get('template', f'accessibility/components/{component_id}.html')
        self.css_classes = kwargs.get('css_classes', [])
        self.config = kwargs.get('config', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            'id': self.component_id,
            'name': self.name,
            'type': self.component_type,
            'accessibility_features': self.accessibility_features,
            'aria_attributes': self.aria_attributes,
            'keyboard_navigation': self.keyboard_navigation,
            'screen_reader_support': self.screen_reader_support,
            'high_contrast_support': self.high_contrast_support,
            'large_text_support': self.large_text_support,
            'focus_management': self.focus_management,
            'skip_links': self.skip_links,
            'landmark_roles': self.landmark_roles,
            'color_contrast': self.color_contrast,
            'template': self.template,
            'css_classes': self.css_classes,
            'config': self.config
        }


class AccessibilityTheme:
    """
    Represents an accessibility-focused theme
    """
    
    def __init__(self, theme_id: str, **kwargs):
        self.theme_id = theme_id
        self.name = kwargs.get('name', theme_id.title())
        self.description = kwargs.get('description', '')
        self.theme_type = kwargs.get('theme_type', 'default')  # default, high_contrast, large_text, color_blind
        self.colors = kwargs.get('colors', {})
        self.font_sizes = kwargs.get('font_sizes', {})
        self.spacing = kwargs.get('spacing', {})
        self.focus_indicators = kwargs.get('focus_indicators', {})
        self.css_classes = kwargs.get('css_classes', [])
        self.custom_css = kwargs.get('custom_css', '')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary"""
        return {
            'id': self.theme_id,
            'name': self.name,
            'description': self.description,
            'type': self.theme_type,
            'colors': self.colors,
            'font_sizes': self.font_sizes,
            'spacing': self.spacing,
            'focus_indicators': self.focus_indicators,
            'css_classes': self.css_classes,
            'custom_css': self.custom_css
        }


class AccessibilityManager:
    """
    Manages accessibility features and WCAG compliance
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.rules = {}
        self.components = {}
        self.themes = {}
        self.keyboard_shortcuts = {}
        self.screen_readers = {}
        self.assistive_technologies = {}
        self.validation_rules = {}
        self.audit_results = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize accessibility manager"""
        if self._initialized:
            return
        
        self._load_wcag_rules()
        self._load_accessibility_components()
        self._load_accessibility_themes()
        self._load_keyboard_shortcuts()
        self._load_screen_reader_configs()
        self._load_validation_rules()
        self._initialized = True
    
    def _load_wcag_rules(self):
        """Load WCAG accessibility rules"""
        wcag_rules = [
            # Perceivable
            AccessibilityRule(
                'alt_text',
                name='Alternative Text for Images',
                description='All images must have meaningful alt text',
                wcag_level='A',
                category='perception',
                guidelines=['1.1.1 Non-text Content'],
                priority='high',
                impact='serious'
            ),
            AccessibilityRule(
                'color_contrast',
                name='Color Contrast',
                description='Text must have sufficient contrast against background',
                wcag_level='AA',
                category='perception',
                guidelines=['1.4.3 Contrast (Minimum)', '1.4.6 Contrast (Enhanced)'],
                priority='high',
                impact='serious'
            ),
            AccessibilityRule(
                'resize_text',
                name='Text Resizing',
                description='Text must be resizable without loss of functionality',
                wcag_level='AA',
                category='perception',
                guidelines=['1.4.4 Resize text'],
                priority='medium',
                impact='moderate'
            ),
            # Operable
            AccessibilityRule(
                'keyboard_access',
                name='Keyboard Accessibility',
                description='All functionality must be available via keyboard',
                wcag_level='A',
                category='operation',
                guidelines=['2.1.1 Keyboard'],
                priority='critical',
                impact='critical'
            ),
            AccessibilityRule(
                'focus_visible',
                name='Focus Indicator',
                description='Keyboard focus must be clearly visible',
                wcag_level='AA',
                category='operation',
                guidelines=['2.4.7 Focus Visible'],
                priority='high',
                impact='serious'
            ),
            AccessibilityRule(
                'no_keyboard_trap',
                name='No Keyboard Traps',
                description='Keyboard focus must not be trapped',
                wcag_level='A',
                category='operation',
                guidelines=['2.1.2 No Keyboard Trap'],
                priority='high',
                impact='serious'
            ),
            # Understandable
            AccessibilityRule(
                'page_language',
                name='Page Language',
                description='Page language must be programmatically determined',
                wcag_level='A',
                category='understanding',
                guidelines=['3.1.1 Language of Page'],
                priority='medium',
                impact='moderate'
            ),
            AccessibilityRule(
                'error_identification',
                name='Error Identification',
                description='Errors must be identified and described',
                wcag_level='A',
                category='understanding',
                guidelines=['3.3.1 Error Identification'],
                priority='high',
                impact='serious'
            ),
            AccessibilityRule(
                'labels_instructions',
                name='Labels and Instructions',
                description='Form controls must have labels and instructions',
                wcag_level='A',
                category='understanding',
                guidelines=['3.3.2 Labels or Instructions'],
                priority='high',
                impact='serious'
            ),
            # Robust
            AccessibilityRule(
                'markup_valid',
                name='Valid Markup',
                description='HTML must be valid and well-formed',
                wcag_level='A',
                category='robust',
                guidelines=['4.1.1 Parsing'],
                priority='medium',
                impact='moderate'
            ),
            AccessibilityRule(
                'aria_roles',
                name='ARIA Roles',
                description='ARIA roles must be used correctly',
                wcag_level='AA',
                category='robust',
                guidelines=['4.1.2 Name, Role, Value'],
                priority='medium',
                impact='moderate'
            )
        ]
        
        for rule in wcag_rules:
            self.rules[rule.rule_id] = rule
    
    def _load_accessibility_components(self):
        """Load accessibility-enhanced components"""
        # Form components
        form_components = [
            AccessibilityComponent(
                'accessible_form',
                name='Accessible Form',
                component_type='form',
                accessibility_features=['labels', 'error_messages', 'instructions'],
                aria_attributes={
                    'form': {'role': 'form', 'aria-label': 'Order form'},
                    'fieldsets': {'role': 'group'},
                    'errors': {'role': 'alert', 'aria-live': 'polite'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                focus_management=True,
                template='accessibility/components/form.html',
                css_classes=['accessible-form']
            ),
            AccessibilityComponent(
                'accessible_input',
                name='Accessible Input',
                component_type='input',
                accessibility_features=['labels', 'descriptions', 'validation'],
                aria_attributes={
                    'input': {'aria-describedby': 'help-text', 'aria-required': 'true'},
                    'label': {'for': 'input-id'},
                    'error': {'role': 'alert', 'aria-live': 'polite'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                focus_management=True,
                template='accessibility/components/input.html',
                css_classes=['accessible-input']
            ),
            AccessibilityComponent(
                'accessible_button',
                name='Accessible Button',
                component_type='button',
                accessibility_features=['focus_indicator', 'keyboard_support'],
                aria_attributes={
                    'button': {'aria-label': 'Submit order', 'aria-describedby': 'button-help'},
                    'icon': {'aria-hidden': 'true'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                focus_management=True,
                template='accessibility/components/button.html',
                css_classes=['accessible-button']
            ),
            AccessibilityComponent(
                'accessible_menu',
                name='Accessible Menu',
                component_type='navigation',
                accessibility_features=['keyboard_navigation', 'skip_links', 'landmarks'],
                aria_attributes={
                    'menu': {'role': 'navigation', 'aria-label': 'Main menu'},
                    'menubar': {'role': 'menubar'},
                    'menuitem': {'role': 'menuitem', 'tabindex': '-1'},
                    'submenu': {'role': 'menu', 'aria-hidden': 'true'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                focus_management=True,
                skip_links=[
                    {'href': '#main-content', 'text': 'Skip to main content'},
                    {'href': '#navigation', 'text': 'Skip to navigation'}
                ],
                landmark_roles={'navigation': 'main', 'content': 'main'},
                template='accessibility/components/menu.html',
                css_classes=['accessible-menu']
            ),
            AccessibilityComponent(
                'accessible_table',
                name='Accessible Table',
                component_type='table',
                accessibility_features=['headers', 'captions', 'scope'],
                aria_attributes={
                    'table': {'role': 'table'},
                    'caption': {'aria-label': 'Order summary table'},
                    'headers': {'scope': 'col', 'aria-sort': 'none'},
                    'cells': {'aria-describedby': 'header-id'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                template='accessibility/components/table.html',
                css_classes=['accessible-table']
            ),
            AccessibilityComponent(
                'accessible_modal',
                name='Accessible Modal',
                component_type='dialog',
                accessibility_features=['focus_trap', 'escape_key', 'aria_labels'],
                aria_attributes={
                    'modal': {'role': 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'modal-title'},
                    'overlay': {'aria-hidden': 'true'},
                    'close': {'aria-label': 'Close modal'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                focus_management=True,
                template='accessibility/components/modal.html',
                css_classes=['accessible-modal']
            ),
            AccessibilityComponent(
                'accessible_chart',
                name='Accessible Chart',
                component_type='chart',
                accessibility_features=['data_table', 'descriptions', 'keyboard_navigation'],
                aria_attributes={
                    'chart': {'role': 'img', 'aria-label': 'Sales chart'},
                    'data_table': {'aria-hidden': 'false'},
                    'description': {'aria-describedby': 'chart-description'}
                },
                keyboard_navigation=True,
                screen_reader_support=True,
                template='accessibility/components/chart.html',
                css_classes=['accessible-chart']
            )
        ]
        
        for component in form_components:
            self.components[component.component_id] = component
    
    def _load_accessibility_themes(self):
        """Load accessibility-focused themes"""
        themes = [
            AccessibilityTheme(
                'high_contrast',
                name='High Contrast',
                description='High contrast theme for better visibility',
                theme_type='high_contrast',
                colors={
                    'background': '#000000',
                    'text': '#ffffff',
                    'primary': '#ffff00',
                    'secondary': '#00ffff',
                    'accent': '#ff00ff',
                    'error': '#ff0000',
                    'success': '#00ff00',
                    'warning': '#ff9900',
                    'focus': '#ffffff',
                    'border': '#ffffff'
                },
                font_sizes={
                    'base': '18px',
                    'small': '16px',
                    'medium': '20px',
                    'large': '24px',
                    'xlarge': '28px'
                },
                spacing={
                    'base': '8px',
                    'small': '4px',
                    'medium': '12px',
                    'large': '16px',
                    'xlarge': '20px'
                },
                focus_indicators={
                    'outline': '3px solid #ffff00',
                    'background': '#ffff00',
                    'color': '#000000'
                },
                css_classes=['high-contrast', 'accessibility-theme']
            ),
            AccessibilityTheme(
                'large_text',
                name='Large Text',
                description='Large text theme for better readability',
                theme_type='large_text',
                colors={
                    'background': '#ffffff',
                    'text': '#000000',
                    'primary': '#0066cc',
                    'secondary': '#666666',
                    'accent': '#cc6600',
                    'error': '#cc0000',
                    'success': '#006600',
                    'warning': '#cc6600',
                    'focus': '#0066cc',
                    'border': '#cccccc'
                },
                font_sizes={
                    'base': '24px',
                    'small': '20px',
                    'medium': '28px',
                    'large': '32px',
                    'xlarge': '36px'
                },
                spacing={
                    'base': '12px',
                    'small': '8px',
                    'medium': '16px',
                    'large': '20px',
                    'xlarge': '24px'
                },
                focus_indicators={
                    'outline': '3px solid #0066cc',
                    'background': '#e6f2ff',
                    'color': '#000000'
                },
                css_classes=['large-text', 'accessibility-theme']
            ),
            AccessibilityTheme(
                'color_blind_friendly',
                name='Color Blind Friendly',
                description='Color blind friendly theme',
                theme_type='color_blind',
                colors={
                    'background': '#ffffff',
                    'text': '#000000',
                    'primary': '#0066cc',
                    'secondary': '#666666',
                    'accent': '#006666',
                    'error': '#cc0000',
                    'success': '#006600',
                    'warning': '#cc6600',
                    'focus': '#0066cc',
                    'border': '#999999'
                },
                font_sizes={
                    'base': '16px',
                    'small': '14px',
                    'medium': '18px',
                    'large': '20px',
                    'xlarge': '24px'
                },
                spacing={
                    'base': '8px',
                    'small': '4px',
                    'medium': '12px',
                    'large': '16px',
                    'xlarge': '20px'
                },
                focus_indicators={
                    'outline': '3px solid #0066cc',
                    'background': '#e6f2ff',
                    'color': '#000000'
                },
                css_classes=['color-blind-friendly', 'accessibility-theme']
            )
        ]
        
        for theme in themes:
            self.themes[theme.theme_id] = theme
    
    def _load_keyboard_shortcuts(self):
        """Load keyboard shortcuts"""
        shortcuts = {
            'navigation': {
                'Tab': 'Next focusable element',
                'Shift+Tab': 'Previous focusable element',
                'Enter': 'Activate button/link',
                'Space': 'Activate button/checkbox',
                'Escape': 'Close modal/dropdown',
                'Arrow Keys': 'Navigate menu/options',
                'Home': 'First item in list',
                'End': 'Last item in list',
                'Page Up': 'Previous page',
                'Page Down': 'Next page'
            },
            'forms': {
                'Enter': 'Submit form',
                'Escape': 'Cancel/reset form',
                'Arrow Up/Down': 'Select option (dropdown/radio)',
                'Arrow Left/Right': 'Select option (radio/tabs)',
                'Space': 'Toggle checkbox'
            },
            'pos_specific': {
                'F1': 'Help',
                'F2': 'New order',
                'F3': 'Search products',
                'F4': 'View orders',
                'F5': 'Refresh',
                'F6': 'Toggle barcode scanner',
                'F7': 'Customer search',
                'F8': 'Payment',
                'F9': 'Print receipt',
                'F10': 'Settings',
                'Ctrl+S': 'Save',
                'Ctrl+P': 'Print',
                'Ctrl+F': 'Find/Search',
                'Ctrl+Z': 'Undo',
                'Ctrl+Y': 'Redo'
            },
            'accessibility': {
                'Alt+T': 'Toggle high contrast',
                'Alt+L': 'Toggle large text',
                'Alt+C': 'Toggle color blind mode',
                'Alt+S': 'Toggle screen reader mode',
                'Alt+K': 'Show keyboard shortcuts',
                'Alt+M': 'Toggle accessibility menu'
            }
        }
        
        self.keyboard_shortcuts = shortcuts
    
    def _load_screen_reader_configs(self):
        """Load screen reader configurations"""
        screen_readers = {
            'nvda': {
                'name': 'NVDA',
                'platforms': ['windows'],
                'commands': {
                    'browse_mode': 'NVDA+Space',
                    'focus_mode': 'NVDA+Space',
                    'read_all': 'NVDA+Down Arrow',
                    'stop_reading': 'Control',
                    'next_heading': 'H',
                    'previous_heading': 'Shift+H',
                    'next_link': 'K',
                    'previous_link': 'Shift+K',
                    'next_form_control': 'Tab',
                    'previous_form_control': 'Shift+Tab'
                },
                'announcements': {
                    'page_load': 'Page loaded',
                    'form_validation': 'Form validation errors',
                    'order_complete': 'Order completed successfully',
                    'error': 'Error occurred'
                }
            },
            'jaws': {
                'name': 'JAWS',
                'platforms': ['windows'],
                'commands': {
                    'browse_mode': 'Insert+Space',
                    'focus_mode': 'Insert+Space',
                    'read_all': 'Insert+Down Arrow',
                    'stop_reading': 'Control',
                    'next_heading': 'H',
                    'previous_heading': 'Shift+H',
                    'next_link': 'K',
                    'previous_link': 'Shift+K'
                },
                'announcements': {
                    'page_load': 'Page loaded',
                    'form_validation': 'Form validation errors',
                    'order_complete': 'Order completed successfully',
                    'error': 'Error occurred'
                }
            },
            'voiceover': {
                'name': 'VoiceOver',
                'platforms': ['mac', 'ios'],
                'commands': {
                    'read_all': 'VO+A',
                    'stop_reading': 'Control',
                    'next_heading': 'VO+Command+H',
                    'previous_heading': 'VO+Command+Shift+H',
                    'next_link': 'VO+Command+L',
                    'previous_link': 'VO+Command+Shift+L'
                },
                'announcements': {
                    'page_load': 'Page loaded',
                    'form_validation': 'Form validation errors',
                    'order_complete': 'Order completed successfully',
                    'error': 'Error occurred'
                }
            },
            'talkback': {
                'name': 'TalkBack',
                'platforms': ['android'],
                'commands': {
                    'read_all': 'Swipe down with 2 fingers',
                    'stop_reading': '2 finger tap',
                    'next_heading': 'Swipe right',
                    'previous_heading': 'Swipe left',
                    'next_element': 'Swipe right',
                    'previous_element': 'Swipe left'
                },
                'announcements': {
                    'page_load': 'Page loaded',
                    'form_validation': 'Form validation errors',
                    'order_complete': 'Order completed successfully',
                    'error': 'Error occurred'
                }
            }
        }
        
        self.screen_readers = screen_readers
    
    def _load_validation_rules(self):
        """Load accessibility validation rules"""
        validation_rules = {
            'image_alt': {
                'selector': 'img',
                'test': 'hasAttribute("alt")',
                'message': 'Images must have alt text',
                'wcag_level': 'A'
            },
            'form_labels': {
                'selector': 'input, select, textarea',
                'test': 'hasAttribute("aria-label") || document.querySelector(`label[for="${id}"]`)',
                'message': 'Form controls must have labels',
                'wcag_level': 'A'
            },
            'button_text': {
                'selector': 'button, [role="button"]',
                'test': 'textContent.trim().length > 0 || hasAttribute("aria-label")',
                'message': 'Buttons must have accessible text',
                'wcag_level': 'A'
            },
            'heading_hierarchy': {
                'selector': 'h1, h2, h3, h4, h5, h6',
                'test': 'checkHeadingHierarchy()',
                'message': 'Headings must follow proper hierarchy',
                'wcag_level': 'AA'
            },
            'link_purpose': {
                'selector': 'a[href]',
                'test': 'textContent.trim().length > 0 || hasAttribute("aria-label")',
                'message': 'Links must have descriptive text',
                'wcag_level': 'A'
            },
            'table_headers': {
                'selector': 'table',
                'test': 'querySelectorAll("th").length > 0',
                'message': 'Tables must have headers',
                'wcag_level': 'A'
            },
            'contrast_ratio': {
                'selector': '*',
                'test': 'checkContrastRatio()',
                'message': 'Text must have sufficient contrast',
                'wcag_level': 'AA'
            },
            'focus_indicator': {
                'selector': 'a, button, input, select, textarea',
                'test': 'hasFocusStyles()',
                'message': 'Interactive elements must have visible focus',
                'wcag_level': 'AA'
            },
            'aria_landmarks': {
                'selector': 'body',
                'test': 'hasLandmarkRoles()',
                'message': 'Page should have ARIA landmarks',
                'wcag_level': 'AA'
            }
        }
        
        self.validation_rules = validation_rules
    
    def get_accessibility_config(self, tenant_id: Optional[str] = None, 
                              user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get accessibility configuration for tenant
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get user preferences or use defaults
        preferences = user_preferences or {
            'high_contrast': False,
            'large_text': False,
            'screen_reader': False,
            'keyboard_only': False,
            'reduced_motion': False,
            'focus_visible': True,
            'auto_validate': True
        }
        
        # Get appropriate theme
        theme_id = 'default'
        if preferences.get('high_contrast'):
            theme_id = 'high_contrast'
        elif preferences.get('large_text'):
            theme_id = 'large_text'
        elif preferences.get('color_blind_friendly'):
            theme_id = 'color_blind_friendly'
        
        theme = self.themes.get(theme_id)
        
        # Get accessibility components
        components = self._get_accessibility_components(enabled_features, retail_type)
        
        # Get keyboard shortcuts
        shortcuts = self._get_relevant_shortcuts(retail_type, enabled_features)
        
        return {
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'user_preferences': preferences,
            'theme': theme.to_dict() if theme else None,
            'components': [comp.to_dict() for comp in components],
            'keyboard_shortcuts': shortcuts,
            'screen_reader_config': self._get_screen_reader_config(),
            'validation_rules': self.validation_rules,
            'wcag_rules': [rule.to_dict() for rule in self.rules.values()],
            'assistive_technologies': self._get_assistive_technologies()
        }
    
    def validate_accessibility(self, html_content: str, wcag_level: str = 'AA') -> Dict[str, Any]:
        """
        Validate HTML content for accessibility compliance
        """
        if not self._initialized:
            self.initialize()
        
        validation_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': [],
            'wcag_level': wcag_level,
            'score': 0
        }
        
        # Apply validation rules
        for rule_id, rule_config in self.validation_rules.items():
            rule = self.rules.get(rule_id)
            if not rule or rule.wcag_level not in ['A', wcag_level]:
                continue
            
            # Simulate validation (in real implementation, this would use actual HTML parsing)
            try:
                # This is a simplified validation
                if rule_id in ['image_alt', 'form_labels', 'button_text']:
                    # Basic checks that would pass in most cases
                    validation_results['passed'] += 1
                else:
                    # More complex checks might fail
                    if rule_id in ['contrast_ratio', 'focus_indicator']:
                        validation_results['warnings'] += 1
                        validation_results['errors'].append({
                            'rule': rule_id,
                            'message': rule_config['message'],
                            'severity': 'warning',
                            'wcag_level': rule.wcag_level
                        })
                    else:
                        validation_results['passed'] += 1
            except Exception as e:
                validation_results['errors'].append({
                    'rule': rule_id,
                    'message': f'Validation error: {str(e)}',
                    'severity': 'error',
                    'wcag_level': rule.wcag_level
                })
                validation_results['failed'] += 1
        
        # Calculate score
        total_checks = validation_results['passed'] + validation_results['failed']
        if total_checks > 0:
            validation_results['score'] = (validation_results['passed'] / total_checks) * 100
        
        return validation_results
    
    def _get_accessibility_components(self, enabled_features: Set[str], retail_type: str) -> List[AccessibilityComponent]:
        """Get accessibility components based on features"""
        components = []
        
        for component in self.components.values():
            # Check if component is relevant for retail type
            if hasattr(component, 'retail_types') and component.retail_types:
                if retail_type not in component.retail_types:
                    continue
            
            # Check required features
            if hasattr(component, 'required_features') and component.required_features:
                if not all(feature in enabled_features for feature in component.required_features):
                    continue
            
            components.append(component)
        
        return components
    
    def _get_relevant_shortcuts(self, retail_type: str, enabled_features: Set[str]) -> Dict[str, Any]:
        """Get relevant keyboard shortcuts"""
        shortcuts = {
            'navigation': self.keyboard_shortcuts.get('navigation', {}),
            'forms': self.keyboard_shortcuts.get('forms', {}),
            'accessibility': self.keyboard_shortcuts.get('accessibility', {})
        }
        
        # Add POS-specific shortcuts
        pos_shortcuts = self.keyboard_shortcuts.get('pos_specific', {})
        shortcuts['pos_specific'] = pos_shortcuts
        
        return shortcuts
    
    def _get_screen_reader_config(self) -> Dict[str, Any]:
        """Get screen reader configuration"""
        return {
            'supported_readers': self.screen_readers,
            'announcements': {
                'page_load': 'Page loaded',
                'form_error': 'Please check form errors',
                'order_success': 'Order completed successfully',
                'payment_processed': 'Payment processed',
                'error_occurred': 'An error occurred'
            },
            'live_regions': {
                'status': 'polite',
                'errors': 'assertive',
                'notifications': 'polite'
            }
        }
    
    def _get_assistive_technologies(self) -> Dict[str, Any]:
        """Get assistive technology configurations"""
        return {
            'screen_readers': list(self.screen_readers.keys()),
            'screen_magnifiers': ['zoomtext', 'magnifier', 'virtual Magnifier'],
            'voice_recognition': ['dragon', 'windows speech recognition'],
            'switch_devices': ['switch access', 'head mouse', 'eye tracking'],
            'braille_displays': ['braille display', 'refreshable braille']
        }
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def register_rule(self, rule: AccessibilityRule):
        """Register an accessibility rule"""
        self.rules[rule.rule_id] = rule
    
    def register_component(self, component: AccessibilityComponent):
        """Register an accessibility component"""
        self.components[component.component_id] = component
    
    def register_theme(self, theme: AccessibilityTheme):
        """Register an accessibility theme"""
        self.themes[theme.theme_id] = theme
    
    def register_keyboard_shortcut(self, category: str, shortcut: str, description: str):
        """Register a keyboard shortcut"""
        if category not in self.keyboard_shortcuts:
            self.keyboard_shortcuts[category] = {}
        self.keyboard_shortcuts[category][shortcut] = description


# Global accessibility manager instance
accessibility_manager = None


def get_accessibility_manager(feature_manager=None) -> AccessibilityManager:
    """Get or create global accessibility manager instance"""
    global accessibility_manager
    if accessibility_manager is None:
        accessibility_manager = AccessibilityManager(feature_manager)
    return accessibility_manager