"""
Tenant Management Routes
Handles tenant creation, configuration, and management for multi-tenant architecture
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from flask_login import login_required, current_user
from models import db
from models.tenant import Tenant, TenantSettings, SubscriptionPlan, TenantSubscription, TenantFeatureFlag
from models.user import User
from middleware.tenant_middleware import tenant_required, require_tenant_plan, TenantContext
from utils.tenant_query_manager import TenantQueryManager
from datetime import datetime, timedelta
import uuid

tenant_bp = Blueprint('tenant', __name__, url_prefix='/tenant')


@tenant_bp.route('/select')
@login_required
def select_tenant():
    """Select tenant for users with access to multiple tenants"""
    # Get all tenants the user has access to
    if current_user.is_super_admin:
        tenants = Tenant.query.filter_by(is_active=True).all()
    else:
        # Get tenants where user is a member
        tenants = db.session.query(Tenant).join(User).filter(
            User.id == current_user.id,
            Tenant.is_active == True
        ).all()
    
    if len(tenants) == 1:
        # If only one tenant, redirect to it
        TenantContext.set_tenant_context(tenants[0].id)
        return redirect(url_for('dashboard.index'))
    
    return render_template('tenant/select.html', tenants=tenants)


@tenant_bp.route('/switch/<int:tenant_id>')
@login_required
def switch_tenant(tenant_id):
    """Switch to a different tenant"""
    # Verify user has access to this tenant
    if not current_user.is_super_admin:
        user_tenant = User.query.filter_by(
            id=current_user.id,
            tenant_id=tenant_id
        ).first()
        
        if not user_tenant:
            flash('You do not have access to this tenant', 'error')
            return redirect(url_for('tenant.select_tenant'))
    
    # Verify tenant exists and is active
    tenant = Tenant.query.get(tenant_id)
    if not tenant or not tenant.is_active:
        flash('Tenant not found or inactive', 'error')
        return redirect(url_for('tenant.select_tenant'))
    
    # Set tenant context
    TenantContext.set_tenant_context(tenant_id)
    
    flash(f'Switched to tenant: {tenant.name}', 'success')
    return redirect(url_for('dashboard.index'))


@tenant_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_tenant():
    """Create a new tenant (super admin only)"""
    if not current_user.is_super_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'identifier', 'admin_email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if identifier already exists
        if Tenant.query.filter_by(identifier=data['identifier']).first():
            return jsonify({
                'success': False,
                'message': 'Tenant identifier already exists'
            }), 400
        
        try:
            # Create tenant
            tenant = Tenant(
                name=data['name'],
                identifier=data['identifier'],
                subdomain=data.get('subdomain', data['identifier']),
                domain=data.get('domain'),
                contact_email=data['admin_email'],
                phone=data.get('phone'),
                address=data.get('address'),
                is_active=True
            )
            
            db.session.add(tenant)
            db.session.flush()  # Get tenant ID
            
            # Create tenant settings
            settings = TenantSettings(
                tenant_id=tenant.id,
                timezone=data.get('timezone', 'UTC'),
                currency=data.get('currency', 'USD'),
                date_format=data.get('date_format', '%Y-%m-%d'),
                time_format=data.get('time_format', '%H:%M'),
                theme=data.get('theme', 'default'),
                language=data.get('language', 'en')
            )
            
            db.session.add(settings)
            
            # Create admin user for tenant
            admin_user = User(
                username=data.get('admin_username', f"{data['identifier']}_admin"),
                email=data['admin_email'],
                first_name=data.get('admin_first_name', 'Admin'),
                last_name=data.get('admin_last_name', 'User'),
                tenant_id=tenant.id,
                is_tenant_admin=True,
                is_active=True
            )
            admin_user.set_password(data.get('admin_password', 'admin123'))
            
            db.session.add(admin_user)
            
            # Assign subscription plan
            plan_id = data.get('subscription_plan_id', 1)  # Default to basic plan
            subscription = TenantSubscription(
                tenant_id=tenant.id,
                plan_id=plan_id,
                status='active',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)  # 30 days trial
            )
            
            db.session.add(subscription)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Tenant created successfully',
                'tenant_id': tenant.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error creating tenant: {str(e)}'
            }), 500
    
    # GET request - show create form
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('tenant/create.html', plans=plans)


@tenant_bp.route('/manage')
@login_required
@tenant_required
def manage_tenant():
    """Manage current tenant settings"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        flash('No tenant context', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get tenant subscription
    subscription = tenant.active_subscription()
    
    # Get tenant usage statistics
    from models.tenant import TenantUsage
    today = datetime.utcnow().date()
    usage_today = TenantUsage.query.filter_by(
        tenant_id=tenant.id,
        usage_date=today
    ).first()
    
    # Get monthly usage
    month_start = today.replace(day=1)
    monthly_usage = TenantUsage.query.filter(
        TenantUsage.tenant_id == tenant.id,
        TenantUsage.usage_date >= month_start
    ).all()
    
    # Calculate totals
    total_api_calls = sum(u.api_calls for u in monthly_usage)
    total_orders = sum(u.orders_count for u in monthly_usage)
    total_users = sum(u.active_users for u in monthly_usage)
    
    return render_template('tenant/manage.html',
                         tenant=tenant,
                         subscription=subscription,
                         usage_today=usage_today,
                         monthly_stats={
                             'api_calls': total_api_calls,
                             'orders': total_orders,
                             'users': total_users
                         })


@tenant_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@tenant_required
def tenant_settings():
    """Manage tenant settings"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'success': False, 'message': 'No tenant context'}), 400
    
    if request.method == 'POST':
        data = request.get_json()
        
        try:
            # Update tenant basic info
            if 'name' in data:
                tenant.name = data['name']
            if 'contact_email' in data:
                tenant.contact_email = data['contact_email']
            if 'phone' in data:
                tenant.phone = data['phone']
            if 'address' in data:
                tenant.address = data['address']
            
            # Update tenant settings
            settings = tenant.settings.first()
            if not settings:
                settings = TenantSettings(tenant_id=tenant.id)
                db.session.add(settings)
            
            setting_fields = ['timezone', 'currency', 'date_format', 'time_format', 'theme', 'language']
            for field in setting_fields:
                if field in data:
                    setattr(settings, field, data[field])
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error updating settings: {str(e)}'
            }), 500
    
    # GET request - return current settings
    settings = tenant.settings.first()
    return jsonify({
        'success': True,
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'identifier': tenant.identifier,
            'subdomain': tenant.subdomain,
            'domain': tenant.domain,
            'contact_email': tenant.contact_email,
            'phone': tenant.phone,
            'address': tenant.address
        },
        'settings': {
            'timezone': settings.timezone if settings else 'UTC',
            'currency': settings.currency if settings else 'USD',
            'date_format': settings.date_format if settings else '%Y-%m-%d',
            'time_format': settings.time_format if settings else '%H:%M',
            'theme': settings.theme if settings else 'default',
            'language': settings.language if settings else 'en'
        }
    })


@tenant_bp.route('/subscription')
@login_required
@tenant_required
def subscription():
    """View tenant subscription details"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'success': False, 'message': 'No tenant context'}), 400
    
    # Get current subscription
    current_subscription = tenant.active_subscription()
    
    # Get all available plans
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    
    # Get subscription history
    subscription_history = TenantSubscription.query.filter_by(
        tenant_id=tenant.id
    ).order_by(TenantSubscription.created_at.desc()).all()
    
    return render_template('tenant/subscription.html',
                         tenant=tenant,
                         current_subscription=current_subscription,
                         plans=plans,
                         subscription_history=subscription_history)


@tenant_bp.route('/subscription/change', methods=['POST'])
@login_required
@tenant_required
def change_subscription():
    """Change tenant subscription plan"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'success': False, 'message': 'No tenant context'}), 400
    
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    if not plan_id:
        return jsonify({'success': False, 'message': 'Plan ID required'}), 400
    
    # Validate plan exists
    plan = SubscriptionPlan.query.get(plan_id)
    if not plan or not plan.is_active:
        return jsonify({'success': False, 'message': 'Invalid plan'}), 400
    
    try:
        # Deactivate current subscription
        current_subscription = tenant.active_subscription()
        if current_subscription:
            current_subscription.status = 'cancelled'
            current_subscription.end_date = datetime.utcnow()
        
        # Create new subscription
        new_subscription = TenantSubscription(
            tenant_id=tenant.id,
            plan_id=plan_id,
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)  # Monthly billing
        )
        
        db.session.add(new_subscription)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Subscription changed to {plan.name}',
            'subscription': {
                'id': new_subscription.id,
                'plan_name': plan.name,
                'status': new_subscription.status,
                'start_date': new_subscription.start_date.isoformat(),
                'end_date': new_subscription.end_date.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error changing subscription: {str(e)}'
        }), 500


@tenant_bp.route('/users')
@login_required
@tenant_required
def manage_users():
    """Manage tenant users"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'success': False, 'message': 'No tenant context'}), 400
    
    # Get tenant users
    users = User.query.filter_by(tenant_id=tenant.id).all()
    
    return render_template('tenant/users.html', users=users, tenant=tenant)


@tenant_bp.route('/users/create', methods=['POST'])
@login_required
@tenant_required
def create_user():
    """Create a new user for the tenant"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'success': False, 'message': 'No tenant context'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        # Check if username already exists for this tenant
        existing_user = User.query.filter_by(
            username=data['username'],
            tenant_id=tenant.id
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username already exists for this tenant'
            }), 400
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            tenant_id=tenant.id,
            phone=data.get('phone'),
            role=data.get('role', 'staff'),
            is_tenant_admin=data.get('is_tenant_admin', False),
            is_active=True
        )
        
        # Set password
        password = data.get('password', 'password123')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating user: {str(e)}'
        }), 500


@tenant_bp.route('/api/tenants')
@login_required
def list_tenants():
    """API endpoint to list available tenants"""
    if current_user.is_super_admin:
        tenants = Tenant.query.filter_by(is_active=True).all()
    else:
        tenants = db.session.query(Tenant).join(User).filter(
            User.id == current_user.id,
            Tenant.is_active == True
        ).all()
    
    return jsonify({
        'success': True,
        'tenants': [
            {
                'id': t.id,
                'name': t.name,
                'identifier': t.identifier,
                'subdomain': t.subdomain,
                'domain': t.domain
            }
            for t in tenants
        ]
    })


@tenant_bp.route('/api/current')
@tenant_required
def current_tenant():
    """API endpoint to get current tenant information"""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'success': False, 'message': 'No tenant context'}), 400
    
    subscription = tenant.active_subscription()
    settings = tenant.settings.first()
    
    return jsonify({
        'success': True,
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'identifier': tenant.identifier,
            'subdomain': tenant.subdomain,
            'domain': tenant.domain,
            'contact_email': tenant.contact_email,
            'created_at': tenant.created_at.isoformat()
        },
        'subscription': {
            'plan_name': subscription.plan.name if subscription and subscription.plan else None,
            'status': subscription.status if subscription else None,
            'end_date': subscription.end_date.isoformat() if subscription else None
        },
        'settings': {
            'timezone': settings.timezone if settings else 'UTC',
            'currency': settings.currency if settings else 'USD',
            'theme': settings.theme if settings else 'default'
        }
    })