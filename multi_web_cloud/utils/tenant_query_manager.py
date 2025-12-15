"""
Tenant Query Manager
Provides tenant-aware query methods for multi-tenant architecture
"""

from flask import g
from models import db

class TenantQueryManager:
    """Manager for tenant-aware database queries"""
    
    @staticmethod
    def get_tenant_query(model, tenant_id=None):
        """Get query filtered by tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if tenant_id:
            return model.query.filter(model.tenant_id == tenant_id)
        return model.query
    
    @staticmethod
    def check_tenant_access(resource_id, model, tenant_id=None):
        """Check if resource belongs to tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if not tenant_id:
            return False
        
        resource = model.query.filter_by(
            id=resource_id,
            tenant_id=tenant_id
        ).first()
        
        return resource is not None
    
    @staticmethod
    def create_tenant_resource(data, model, tenant_id=None):
        """Create resource with tenant context"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if tenant_id:
            data['tenant_id'] = tenant_id
        
        return model(**data)
    
    @staticmethod
    def get_tenant_resources(model, tenant_id=None, **filters):
        """Get resources filtered by tenant and additional filters"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.all()
    
    @staticmethod
    def get_tenant_resource_by_id(model, resource_id, tenant_id=None):
        """Get resource by ID within tenant context"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        return query.filter_by(id=resource_id).first()
    
    @staticmethod
    def update_tenant_resource(resource_id, model, update_data, tenant_id=None):
        """Update resource within tenant context"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        resource = TenantQueryManager.get_tenant_resource_by_id(model, resource_id, tenant_id)
        
        if not resource:
            return None
        
        for key, value in update_data.items():
            if hasattr(resource, key):
                setattr(resource, key, value)
        
        db.session.commit()
        return resource
    
    @staticmethod
    def delete_tenant_resource(resource_id, model, tenant_id=None):
        """Delete resource within tenant context"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        resource = TenantQueryManager.get_tenant_resource_by_id(model, resource_id, tenant_id)
        
        if not resource:
            return False
        
        db.session.delete(resource)
        db.session.commit()
        return True
    
    @staticmethod
    def get_tenant_count(model, tenant_id=None, **filters):
        """Get count of resources filtered by tenant and additional filters"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.count()
    
    @staticmethod
    def get_tenant_paginated_resources(model, tenant_id=None, page=1, per_page=20, **filters):
        """Get paginated resources filtered by tenant"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    @staticmethod
    def search_tenant_resources(model, search_term, search_fields, tenant_id=None):
        """Search resources within tenant context"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(model, field):
                    field_attr = getattr(model, field)
                    search_conditions.append(field_attr.ilike(f'%{search_term}%'))
            
            if search_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*search_conditions))
        
        return query.all()
    
    @staticmethod
    def get_tenant_aggregate_data(model, aggregate_func, tenant_id=None, **filters):
        """Get aggregate data for tenant resources"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.with_entities(aggregate_func).scalar()
    
    @staticmethod
    def validate_tenant_isolation(model, tenant_id=None):
        """Validate that all queries are properly isolated by tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if not tenant_id:
            return False, "No tenant context found"
        
        # Check if model has tenant_id column
        if not hasattr(model, 'tenant_id'):
            return False, f"Model {model.__name__} does not have tenant_id column"
        
        # Check if query includes tenant filter
        query = model.query
        query_str = str(query.statement.compile(db.engine))
        
        if 'tenant_id' not in query_str:
            return False, f"Query for {model.__name__} does not include tenant_id filter"
        
        return True, "Tenant isolation validated"


class TenantScopedQuery:
    """Helper class for tenant-scoped queries"""
    
    def __init__(self, model, tenant_id=None):
        self.model = model
        self.tenant_id = tenant_id or getattr(g, 'tenant_id', None)
        self.query = model.query
        
        if self.tenant_id:
            self.query = self.query.filter(model.tenant_id == self.tenant_id)
    
    def filter_by(self, **kwargs):
        """Add additional filters to query"""
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                self.query = self.query.filter(getattr(self.model, key) == value)
        return self
    
    def search(self, search_term, fields):
        """Add search to query"""
        if search_term and fields:
            search_conditions = []
            for field in fields:
                if hasattr(self.model, field):
                    field_attr = getattr(self.model, field)
                    search_conditions.append(field_attr.ilike(f'%{search_term}%'))
            
            if search_conditions:
                from sqlalchemy import or_
                self.query = self.query.filter(or_(*search_conditions))
        
        return self
    
    def order_by(self, *criteria):
        """Add ordering to query"""
        self.query = self.query.order_by(*criteria)
        return self
    
    def limit(self, limit):
        """Add limit to query"""
        self.query = self.query.limit(limit)
        return self
    
    def offset(self, offset):
        """Add offset to query"""
        self.query = self.query.offset(offset)
        return self
    
    def first(self):
        """Get first result"""
        return self.query.first()
    
    def all(self):
        """Get all results"""
        return self.query.all()
    
    def count(self):
        """Get count of results"""
        return self.query.count()
    
    def paginate(self, page=1, per_page=20):
        """Get paginated results"""
        return self.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )


def tenant_scoped(model, tenant_id=None):
    """Create a tenant-scoped query for the given model"""
    return TenantScopedQuery(model, tenant_id)


def get_current_tenant_id():
    """Get current tenant ID from request context"""
    return getattr(g, 'tenant_id', None)


def set_tenant_context(tenant_id):
    """Set tenant context in Flask g object"""
    g.tenant_id = tenant_id


def clear_tenant_context():
    """Clear tenant context from Flask g object"""
    if hasattr(g, 'tenant_id'):
        delattr(g, 'tenant_id')