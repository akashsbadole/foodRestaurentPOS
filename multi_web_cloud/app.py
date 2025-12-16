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

# Import tenant middleware and utilities
from middleware.tenant_middleware import TenantMiddleware, tenant_required, tenant_optional
from utils.tenant_query_manager import TenantQueryManager, tenant_scoped, get_current_tenant_id

# Import feature management system
from utils.feature_flag_manager import feature_manager
from utils.dynamic_model_loader import get_model_loader
from utils.dynamic_route_registry import get_route_registry
from utils.api_feature_manager import get_api_feature_manager
from utils.retail_type_manager import get_retail_type_manager

# Import adaptive UI systems
from utils.adaptive_ui_manager import get_adaptive_ui_manager
from utils.template_engine import get_template_engine
from utils.adaptive_navigation import get_navigation_manager
from utils.dynamic_forms import get_form_manager
from utils.dynamic_dashboard import get_dashboard_manager
from utils.adaptive_components import get_component_manager
from utils.mobile_optimization import get_mobile_manager
from utils.accessibility import get_accessibility_manager
from utils.performance_optimization import get_performance_optimizer
from utils.user_experience import get_ux_manager

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
    
    # Initialize tenant middleware
    tenant_middleware = TenantMiddleware(app)
    
    # Initialize feature management system
    feature_manager.initialize()
    model_loader = get_model_loader(feature_manager)
    model_loader.initialize()
    route_registry = get_route_registry(app)
    route_registry.initialize()
    api_manager = get_api_feature_manager(feature_manager)
    api_manager.initialize()
    retail_manager = get_retail_type_manager(feature_manager)
    retail_manager.initialize()
    
    # Initialize adaptive UI systems
    adaptive_ui_manager = get_adaptive_ui_manager(feature_manager)
    adaptive_ui_manager.initialize()
    
    # Initialize individual UI managers
    template_engine = get_template_engine(app)
    template_engine.init_app(app)
    
    navigation_manager = get_navigation_manager(feature_manager)
    navigation_manager.initialize()
    
    form_manager = get_form_manager(feature_manager)
    form_manager.initialize()
    
    dashboard_manager = get_dashboard_manager(feature_manager)
    dashboard_manager.initialize()
    
    component_manager = get_component_manager(feature_manager)
    component_manager.initialize()
    
    mobile_manager = get_mobile_manager(feature_manager)
    mobile_manager.initialize()
    
    accessibility_manager = get_accessibility_manager(feature_manager)
    accessibility_manager.initialize()
    
    performance_optimizer = get_performance_optimizer(feature_manager)
    performance_optimizer.initialize()
    
    ux_manager = get_ux_manager(feature_manager)
    ux_manager.initialize()
    
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
        # Load user within tenant context
        tenant_id = get_current_tenant_id()
        if tenant_id:
            return User.query.filter_by(id=int(user_id), tenant_id=tenant_id).first()
        return User.query.get(int(user_id))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Initialize session database tables
        session_manager._init_session_database()
        
        # Initialize feature management tables
        try:
            from models.feature_flag import FeatureDefinition, FeatureDependency, FeatureConflict, RetailTypePreset
            db.create_all()
            print("Feature management tables created successfully")
        except Exception as e:
            print(f"Warning: Could not create feature management tables: {e}")
            db.session.rollback()
        
        # Create default tenant if it doesn't exist
        from models.tenant import Tenant
        try:
            default_tenant = Tenant.query.filter_by(id='default').first()
            if not default_tenant:
                default_tenant = Tenant(
                    name='Default Restaurant',
                    subdomain='default',
                    status='active'
                )
                default_tenant.id = 'default'  # Set ID explicitly
                db.session.add(default_tenant)
                db.session.flush()  # Flush to get the ID assigned
                db.session.commit()
                print("Default tenant created successfully")
                
                # Apply default retail type preset
                retail_manager.apply_retail_type_preset('default', 'restaurant')
        except Exception as e:
            print(f"Warning: Could not create default tenant: {e}")
            db.session.rollback()
        
        # Create default settings after tables are created
        try:
            from models.settings import Settings
            Settings.create_defaults('default')
        except Exception as e:
            print(f"Warning: Could not create default settings: {e}")
            print("This is likely due to missing tenant_id column. Please run init_db.py separately.")
        
        # Initialize feature definitions and presets
        try:
            from models.feature_flag import FeatureDefinition, RetailTypePreset
            from utils.environment_flag_parser import EnvironmentFlagParser
            
            parser = EnvironmentFlagParser()
            feature_definitions = parser._load_feature_definitions()
            
            # Create feature definitions in database
            for feature_name, definition in feature_definitions.items():
                existing = FeatureDefinition.query.filter_by(name=feature_name).first()
                if not existing:
                    feature_def = FeatureDefinition(
                        name=feature_name,
                        display_name=definition.get('display_name', feature_name),
                        description=definition.get('description', ''),
                        category=definition.get('category', 'core'),
                        feature_type=definition.get('type', 'boolean'),
                        default_value=definition.get('default', False),
                        is_required=definition.get('is_required', False),
                        is_experimental=definition.get('is_experimental', False),
                        supported_retail_types=definition.get('supported_retail_types'),
                        required_retail_types=definition.get('required_retail_types')
                    )
                    db.session.add(feature_def)
            
            # Create default retail type presets
            for retail_type, config in retail_manager.retail_types.items():
                existing = RetailTypePreset.query.filter_by(retail_type=retail_type).first()
                if not existing:
                    preset = RetailTypePreset(
                        retail_type=retail_type,
                        name=f"{config['name']} Default",
                        description=f"Default preset for {config['name']}",
                        feature_flags=config.get('default_features', {})
                    )
                    db.session.add(preset)
            
            db.session.commit()
            print("Feature definitions and presets initialized successfully")
            
        except Exception as e:
            print(f"Warning: Could not initialize feature definitions: {e}")
            db.session.rollback()
        
        # Create default admin user if not exists
        try:
            # Use direct SQL to check and create admin user with tenant_id
            from werkzeug.security import generate_password_hash
            existing_user = db.session.execute(
                "SELECT id FROM users WHERE username = :username",
                {'username': 'admin'}
            ).fetchone()
            
            if not existing_user:
                password_hash = generate_password_hash('admin123')
                db.session.execute(
                    "INSERT INTO users (username, email, password_hash, role, is_active, tenant_id, created_at) "
                    "VALUES (:username, :email, :password_hash, :role, :is_active, :tenant_id, datetime('now'))",
                    {
                        'username': 'admin',
                        'email': 'admin@restaurant.com',
                        'password_hash': password_hash,
                        'role': 'admin',
                        'is_active': True,
                        'tenant_id': 'default'
                    }
                )
                db.session.commit()
                print("Default admin user created: username=admin, password=admin123")
        except Exception as e:
            print(f"Warning: Could not create default admin user: {e}")
            db.session.rollback()
    
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
    from routes.crm import crm_bp
    from routes.loyalty import loyalty_bp
    from routes.validation import validation_bp
    from routes.tenant import tenant_bp
    
    # Import new API blueprints
    from routes.validation_api import validation_api_bp
    from routes.session_api import session_api_bp
    from routes.offline_api import offline_api_bp
    from routes.security_api import security_api_bp
    from routes.payment_api import payment_api_bp
    from routes.dashboard_api import dashboard_api_bp
    from routes.config_api import config_api_bp
    
    # Import retail module blueprints
    from routes.restaurant import restaurant_bp
    from routes.apparel_footwear import apparel_footwear_bp
    from routes.books_office import books_office_bp
    from routes.food_confectionery import food_confectionery_bp
    from routes.hypermarket_departmental import hypermarket_departmental_bp
    from routes.supermarket_groceries import supermarket_groceries_bp
    from routes.specialized_retail import specialized_retail_bp
    from routes.payment_settlement import payment_settlement_bp
    from routes.discounts_promotions import discounts_promotions_bp
    from routes.returns_exchanges import returns_exchanges_bp
    from routes.reporting_analytics import reporting_analytics_bp
    from routes.multi_store_franchise import multi_store_franchise_bp
    from routes.online_integration import online_integration_bp
    
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
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(loyalty_bp, url_prefix='/loyalty')
    app.register_blueprint(validation_bp, url_prefix='/api/validation')
    app.register_blueprint(tenant_bp)
    
    # Register new API blueprints
    app.register_blueprint(validation_api_bp, url_prefix='/api')
    app.register_blueprint(session_api_bp, url_prefix='/api')
    app.register_blueprint(offline_api_bp, url_prefix='/api')
    app.register_blueprint(security_api_bp, url_prefix='/api')
    app.register_blueprint(payment_api_bp, url_prefix='/api')
    app.register_blueprint(dashboard_api_bp, url_prefix='/api')
    app.register_blueprint(config_api_bp, url_prefix='/api')
    
    # Register retail module blueprints
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(apparel_footwear_bp)
    app.register_blueprint(books_office_bp)
    app.register_blueprint(food_confectionery_bp)
    app.register_blueprint(hypermarket_departmental_bp)
    app.register_blueprint(supermarket_groceries_bp)
    app.register_blueprint(specialized_retail_bp)
    app.register_blueprint(payment_settlement_bp)
    app.register_blueprint(discounts_promotions_bp)
    app.register_blueprint(returns_exchanges_bp)
    app.register_blueprint(reporting_analytics_bp)
    app.register_blueprint(multi_store_franchise_bp)
    app.register_blueprint(online_integration_bp)
    
    # Main routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    @app.route('/health')
    def health_check():
        from middleware.tenant_middleware import TenantContext
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'offline_mode': not offline_manager.is_online,
            'session_valid': session_manager._is_session_valid(),
            'security_status': security_manager.get_security_statistics(),
            'tenant_id': TenantContext.get_current_tenant_id(),
            'tenant_context': TenantContext.is_tenant_context()
        })
    
    # Context processors
    @app.context_processor
    def inject_settings():
        """Inject global settings into templates"""
        from models.settings import Settings
        try:
            # Return empty settings for now to avoid errors
            return dict(public_settings={}, settings={})
        except:
            return dict(public_settings={}, settings={})
    
    @app.context_processor
    def inject_user():
        """Inject current user into templates"""
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_tenant():
        """Inject tenant context into templates"""
        from middleware.tenant_middleware import TenantContext
        tenant = TenantContext.get_current_tenant()
        tenant_settings = TenantContext.get_tenant_settings()
        return dict(tenant=tenant, tenant_settings=tenant_settings)
    
    @app.context_processor
    def inject_features():
        """Inject feature context into templates"""
        tenant_id = get_current_tenant_id()
        if tenant_id:
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            feature_context = {
                'enabled_features': list(enabled_features),
                'feature_count': len(enabled_features),
                'retail_type': retail_type
            }
            return dict(features=feature_context)
        return dict(features={})
    
    @app.context_processor
    def inject_adaptive_ui():
        """Inject adaptive UI context into templates"""
        tenant_id = get_current_tenant_id()
        if tenant_id:
            try:
                # Get adaptive UI manager
                adaptive_ui = get_adaptive_ui_manager(feature_manager)
                
                # Get all UI contexts
                ui_context = adaptive_ui.get_full_ui_context(tenant_id)
                
                return dict(ui=ui_context)
            except Exception as e:
                app.logger.error(f"Error injecting adaptive UI context: {e}")
                return dict(ui={})
        return dict(ui={})
    
    @app.template_filter('feature_enabled')
    def feature_enabled_filter(feature_name):
        """Template filter to check if feature is enabled"""
        tenant_id = get_current_tenant_id()
        return feature_manager.is_enabled(feature_name, tenant_id)
    
    @app.template_filter('retail_type_is')
    def retail_type_filter(retail_type):
        """Template filter to check retail type"""
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return False
        current_type = feature_manager.get_tenant_retail_type(tenant_id)
        return current_type == retail_type
    
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
    
    # API-specific error handlers
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        app.logger.warning(f"Rate limit exceeded: {str(error)}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests, please try again later',
                'retry_after': getattr(error, 'retry_after', 60)
            }), 429
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.warning(f"Unauthorized access attempt: {str(error)}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }), 401
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(422)
    def unprocessable_entity_error(error):
        app.logger.error(f"Unprocessable entity error: {str(error)}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({
                'error': 'Unprocessable entity',
                'message': 'The request was well-formed but unable to be followed due to semantic errors'
            }), 422
        return render_template('errors/422.html'), 422
    
    # Template filters
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format amount as currency"""
        try:
            currency_symbol = '₹'  # Default currency symbol
            decimal_places = 2  # Default decimal places
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
    
    # Feature management API endpoints
    @app.route('/api/features/status')
    def features_status():
        """Get current feature status"""
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return jsonify({
                'success': False,
                'error': 'Tenant context required'
            }), 400
        
        try:
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            stats = feature_manager.get_feature_statistics(tenant_id)
            
            return jsonify({
                'success': True,
                'tenant_id': tenant_id,
                'retail_type': retail_type,
                'enabled_features': list(enabled_features),
                'feature_count': len(enabled_features),
                'statistics': stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/features/available')
    def available_features():
        """Get all available features and their status"""
        tenant_id = get_current_tenant_id()
        try:
            all_features = {}
            for feature_name, feature_def in feature_manager.feature_validators.items():
                is_enabled = feature_manager.is_enabled(feature_name, tenant_id)
                all_features[feature_name] = {
                    'name': feature_def.display_name,
                    'description': feature_def.description,
                    'category': feature_def.category,
                    'enabled': is_enabled,
                    'required': feature_def.is_required,
                    'experimental': feature_def.is_experimental,
                    'supported_retail_types': feature_def.supported_retail_types
                }
            
            return jsonify({
                'success': True,
                'features': all_features
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/routes/available')
    def available_routes():
        """Get available routes for current tenant"""
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return jsonify({
                'success': False,
                'error': 'Tenant context required'
            }), 400
        
        try:
            available_routes = route_registry.get_available_routes(tenant_id)
            available_endpoints = api_manager.get_available_endpoints(tenant_id)
            
            return jsonify({
                'success': True,
                'tenant_id': tenant_id,
                'routes': available_routes,
                'endpoints': available_endpoints
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
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
app = create_app('development')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
