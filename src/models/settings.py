from datetime import datetime

class Settings:
    """Settings model for application settings management"""
    
    def __init__(self, db):
        self.db = db
        self._ensure_default_export_settings()
    
    def get_all(self):
        """Get all settings as dictionary"""
        query = "SELECT key, value FROM settings"
        self.db.execute_query(query)
        results = self.db.fetch_all()
        
        settings = {}
        for row in results:
            settings[row[0]] = row[1]
        
        return settings
    
    def get(self, key, default=None):
        """Get a specific setting value"""
        query = "SELECT value FROM settings WHERE key = ?"
        self.db.execute_query(query, (key,))
        result = self.db.fetch_one()
        
        return result[0] if result else default
    
    def update(self, key, value):
        """Update a setting value"""
        query = """
        UPDATE settings SET value = ?, updated_at = ? WHERE key = ?
        """
        self.db.execute(query, (value, datetime.now(), key))
        self.db.commit()
    
    def create(self, key, value):
        """Create a new setting"""
        query = """
        INSERT INTO settings (key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute(query, (key, value, datetime.now(), datetime.now()))
        self.db.commit()
    
    def ensure_exists(self, key, default_value):
        """Ensure a setting exists, create with default if not"""
        if not self.get(key):
            self.create(key, default_value)
    
    def get_footer_settings(self):
        """Get all footer-related settings"""
        footer_keys = [
            'footer_enabled', 'footer_template', 'footer_show_user_name', 'footer_show_receipt_info',
            'footer_show_business_info', 'footer_custom_text', 'footer_font_size', 'footer_alignment',
            'footer_show_logo', 'footer_logo_path', 'footer_different_receipts', 'footer_invoice_template',
            'footer_receipt_template', 'footer_multiline', 'footer_line1', 'footer_line2', 'footer_line3'
        ]
        footer_settings = {}
        for key in footer_keys:
            footer_settings[key] = self.get(key)
        return footer_settings
    
    def update_footer_settings(self, settings_dict):
        """Update multiple footer settings"""
        for key, value in settings_dict.items():
            if key.startswith('footer_'):
                self.update(key, str(value))
    
    def _ensure_default_export_settings(self):
        """Ensure default export settings exist"""
        # Export settings
        self.ensure_exists('export_after_payment', 'false')
        self.ensure_exists('default_export_format', 'none')  # Options: 'pdf', 'text', 'both', 'none'
        self.ensure_exists('show_export_dialog', 'true')
        self.ensure_exists('auto_open_exported_files', 'false')
        
        # Footer settings
        self.ensure_exists('footer_enabled', 'true')
        self.ensure_exists('footer_template', 'default')
        self.ensure_exists('footer_show_user_name', 'true')
        self.ensure_exists('footer_show_receipt_info', 'true')
        self.ensure_exists('footer_show_business_info', 'true')
        self.ensure_exists('footer_custom_text', 'Thank you for your business!')
        self.ensure_exists('footer_font_size', '10')
        self.ensure_exists('footer_alignment', 'center')
        self.ensure_exists('footer_show_logo', 'false')
        self.ensure_exists('footer_logo_path', '')
        self.ensure_exists('footer_different_receipts', 'false')
        self.ensure_exists('footer_invoice_template', 'default')
        self.ensure_exists('footer_receipt_template', 'default')
        self.ensure_exists('footer_multiline', 'false')
        self.ensure_exists('footer_line1', '')
        self.ensure_exists('footer_line2', '')
        self.ensure_exists('footer_line3', '')
