from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import config

# Import models
from models import db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings

# Import new utilities (without decorators to avoid conflicts)
from utils.session_manager import session_manager
from utils.security_manager import security_manager
from utils.offline_manager import offline_manager
from utils.razorpay_manager import razorpay_manager, process_razorpay_webhook

# Import utilities (avoiding decorators to prevent conflicts)
from utils.session_manager import generate_session_csrf_token
from utils.security_manager import log_security_event
from utils.offline_manager import offline_capable, require_online

# Create Flask app
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # CSRF protection
    csrf = CSRFProtect(app)
    
    # Initialize managers
    session_manager.init_app(app)
    security_manager.init_app(app)
    offline_manager.init_app(app)
    razorpay_manager.init_app(app)
    
    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Create default settings
        Settings.create_defaults()
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User.create_user('admin', 'admin123', 'admin', 'admin@restaurant.com')
            if admin_user:
                print("Default admin user created: username=admin, password=admin123")
    
    # Simple test route first
    @app.route('/simple-test')
    def simple_test():
        return "Simple test working!"
    
    # Register blueprints
    try:
        from routes.auth import auth_bp
        print("Auth blueprint imported successfully")
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("Auth blueprint registered successfully")
    except Exception as e:
        print(f"Error importing/registering auth blueprint: {e}")
        import traceback
        traceback.print_exc()
    
    from routes.dashboard import dashboard_bp
    from routes.orders import orders_bp
    from routes.menu import menu_bp
    from routes.tables import tables_bp
    from routes.inventory import inventory_bp
    from routes.kot import kot_bp
    from routes.reports import reports_bp
    from routes.api import api_bp
    from routes.email import email_bp
    from routes.footer_settings import footer_settings_bp
    from routes.razorpay import razorpay_bp
    from routes.offline_api import offline_api_bp
    
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(menu_bp, url_prefix='/menu')
    app.register_blueprint(tables_bp, url_prefix='/tables')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(kot_bp, url_prefix='/kot')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(email_bp, url_prefix='/email')
    app.register_blueprint(footer_settings_bp, url_prefix='/footer')
    app.register_blueprint(razorpay_bp, url_prefix='/razorpay')
    app.register_blueprint(offline_api_bp, url_prefix='/api/offline')
    
    # Main routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'offline_mode': not offline_manager.is_online,
            'session_valid': session_manager._is_session_valid(),
            'security_status': security_manager.get_security_statistics()
        })
    
    # Context processors
    @app.context_processor
    def inject_settings():
        """Inject global settings into templates"""
        public_settings = Settings.get_public()
        all_settings = Settings.get_all_as_dict()
        return dict(public_settings=public_settings, settings=all_settings)
    
    @app.context_processor
    def inject_user():
        """Inject current user into templates"""
        return dict(current_user=current_user)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {str(error)}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"Forbidden access attempt: {str(error)}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.error(f"Bad request error: {str(error)}")
        app.logger.error(f"Request data: {request.form}")
        app.logger.error(f"Request method: {request.method}")
        app.logger.error(f"Request URL: {request.url}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Bad request', 'details': str(error)}), 400
        return render_template('errors/400.html'), 400
    
    # Template filters
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format amount as currency"""
        try:
            currency_symbol = Settings.get('currency_symbol', '₹')
            decimal_places = int(Settings.get('decimal_places', 2))
            return f"{currency_symbol}{float(amount):.{decimal_places}f}"
        except (ValueError, TypeError):
            return f"₹{amount}"
    
    @app.template_filter('datetime')
    def datetime_filter(dt):
        """Format datetime"""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return dt.strftime('%d %b %Y %I:%M %p') if dt else ''
    
    @app.template_filter('date')
    def date_filter(dt):
        """Format date"""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return dt.strftime('%d %b %Y') if dt else ''
    
    @app.template_filter('time')
    def time_filter(dt):
        """Format time"""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p') if dt else ''
    
    # Razorpay webhook endpoint
    @app.route('/razorpay/webhook', methods=['POST'])
    def razorpay_webhook():
        """Handle Razorpay webhooks"""
        try:
            # Get webhook signature
            webhook_signature = request.headers.get('X-Razorpay-Signature')
            if not webhook_signature:
                log_security_event('MISSING_WEBHOOK_SIGNATURE', 'Webhook missing signature')
                return jsonify({'error': 'Missing signature'}), 400
            
            # Get webhook body
            webhook_body = request.get_data(as_text=True)
            
            # Verify signature
            if not razorpay_manager.verify_webhook_signature(webhook_body, webhook_signature):
                log_security_event('INVALID_WEBHOOK_SIGNATURE', 'Invalid webhook signature')
                return jsonify({'error': 'Invalid signature'}), 400
            
            # Parse webhook data
            webhook_data = request.get_json()
            
            # Process webhook
            success, message, data = process_razorpay_webhook(webhook_data)
            
            if success:
                # Store webhook data for processing
                session['razorpay_webhook_data'] = data
                return jsonify({'status': 'processed'}), 200
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            app.logger.error(f"Error processing Razorpay webhook: {e}")
            return jsonify({'error': 'Webhook processing failed'}), 500
    
    # API endpoints for new features
    @app.route('/api/session/status')
    def session_status():
        """Get current session status"""
        # Inline session validation
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid',
                'redirect': '/auth/login'
            }), 401
        
        return jsonify({
            'success': True,
            'session': session_manager.get_session_info(),
            'csrf_token': generate_session_csrf_token()
        })
    
    @app.route('/api/offline/status')
    def offline_status():
        """Get offline/sync status"""
        return jsonify({
            'success': True,
            'offline': offline_manager.get_sync_status()
        })
    
    @app.route('/api/security/status')
    def security_status():
        """Get security status"""
        return jsonify({
            'success': True,
            'security': security_manager.get_security_statistics()
        })
    
    @app.route('/api/razorpay/config')
    def razorpay_config():
        """Get Razorpay configuration"""
        return jsonify({
            'success': True,
            'razorpay': razorpay_manager.get_configuration_info()
        })
    
    # Force sync endpoint
    @app.route('/api/sync/force', methods=['POST'])
    def force_sync():
        """Force immediate synchronization"""
        # Inline session validation
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid',
                'redirect': '/auth/login'
            }), 401
        
        try:
            success = offline_manager.force_sync()
            return jsonify({
                'success': success,
                'message': 'Sync initiated' if success else 'Sync failed - offline'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
                }), 500
    
    
    # Add CSP headers to allow external resources
    @app.after_request
    def set_security_headers(response):
        """Set security headers including CSP"""
        # Content Security Policy to allow external fonts and stylesheets
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.razorpay.com; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Additional security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    return app

def configure_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configure file handler with rotation
        file_handler = RotatingFileHandler(
            'logs/pos_app.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
        app.logger.addHandler(console_handler)
        
        app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
        app.logger.info('POS application startup')
        
        # Configure encryption logger separately
        encryption_logger = logging.getLogger('web_cloud.utils.encryption')
        encryption_handler = RotatingFileHandler(
            'logs/encryption.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        encryption_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        encryption_handler.setLevel(logging.INFO)
        encryption_logger.addHandler(encryption_handler)
        encryption_logger.setLevel(logging.INFO)
        
        # Prevent encryption logs from propagating to root logger
        encryption_logger.propagate = False

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
