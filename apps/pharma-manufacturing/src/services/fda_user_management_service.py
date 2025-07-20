"""
FDA User Management Service
Comprehensive user authentication and role-based authorization per 21 CFR Part 11
"""

import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
from uuid import UUID, uuid4
import logging
import json
import pyotp
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256

from models.fda_compliance import FDAUser, UserRole, UserRole as UserRoleEnum
from services.immutable_audit_service import ImmutableAuditService
from models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class FDAUserManagementService:
    """
    Service for managing FDA-compliant user authentication and authorization
    Implements 21 CFR Part 11 user access controls
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self.session_timeout_minutes = 30
        self.max_failed_attempts = 3
        self.password_history_count = 12  # Remember last 12 passwords
        self.mfa_secret_key = self._get_mfa_secret()
        
    def _get_mfa_secret(self) -> str:
        """Get MFA secret key for TOTP generation"""
        # In production, this should come from secure key management
        return "PHARMA_MFA_SECRET_KEY_CHANGE_IN_PRODUCTION"
    
    async def create_user(
        self,
        username: str,
        email: str,
        full_name: str,
        employee_id: str,
        department: str,
        title: str,
        supervisor_id: Optional[UUID],
        phone: Optional[str],
        initial_roles: List[UserRoleEnum],
        created_by: UUID,
        ip_address: str
    ) -> FDAUser:
        """
        Create new FDA-compliant user account
        """
        try:
            # Validate username uniqueness
            if await self._username_exists(username):
                raise ValueError(f"Username '{username}' already exists")
            
            # Validate email uniqueness
            if await self._email_exists(email):
                raise ValueError(f"Email '{email}' already exists")
            
            # Validate employee ID uniqueness
            if await self._employee_id_exists(employee_id):
                raise ValueError(f"Employee ID '{employee_id}' already exists")
            
            # Generate secure initial password
            initial_password = self._generate_secure_password()
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(initial_password, salt)
            
            # Create user record
            user = FDAUser(
                id=uuid4(),
                username=username,
                email=email,
                full_name=full_name,
                employee_id=employee_id,
                password_hash=password_hash,
                salt=salt,
                department=department,
                title=title,
                supervisor_id=supervisor_id,
                phone=phone,
                is_active=True,
                is_validated=False,  # Requires supervisor validation
                training_complete=False,  # Requires GMP training completion
                password_expires_at=datetime.now(timezone.utc) + timedelta(days=90),
                last_password_change=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
            
            # Store user in database
            await self._store_user(user)
            
            # Assign initial roles
            for role in initial_roles:
                await self.assign_user_role(
                    user_id=user.id,
                    role=role,
                    assigned_by=created_by,
                    assignment_reason=f"Initial role assignment for new user",
                    ip_address=ip_address
                )
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=created_by,
                username=await self._get_username(created_by),
                full_name=await self._get_full_name(created_by),
                action=AuditAction.CREATE,
                action_description=f"Created user account: {username}",
                entity_type="fda_user",
                entity_id=user.id,
                entity_identifier=username,
                new_values={
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "employee_id": employee_id,
                    "department": department,
                    "initial_roles": [role.value for role in initial_roles]
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            # Send initial password securely (implementation dependent)
            await self._send_initial_credentials(user, initial_password)
            
            logger.info(f"FDA user created: {username} ({user.id})")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user {username}: {str(e)}")
            raise
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        mfa_token: Optional[str],
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Authenticate user with multi-factor authentication
        """
        try:
            # Get user from database
            user = await self._get_user_by_username(username)
            if not user:
                await self._log_failed_authentication(username, "user_not_found", ip_address)
                raise ValueError("Invalid credentials")
            
            # Check if account is locked
            if user.account_locked:
                if user.account_locked_until and datetime.now(timezone.utc) < user.account_locked_until:
                    await self._log_failed_authentication(username, "account_locked", ip_address)
                    raise ValueError("Account is locked")
                else:
                    # Unlock account if lock period expired
                    await self._unlock_user_account(user.id)
                    user.account_locked = False
            
            # Check if account is active
            if not user.is_active:
                await self._log_failed_authentication(username, "account_inactive", ip_address)
                raise ValueError("Account is inactive")
            
            # Verify password
            if not self._verify_password(password, user.password_hash, user.salt):
                await self._handle_failed_login(user, ip_address)
                raise ValueError("Invalid credentials")
            
            # Check password expiration
            if user.password_expires_at and datetime.now(timezone.utc) > user.password_expires_at:
                await self._log_failed_authentication(username, "password_expired", ip_address)
                raise ValueError("Password has expired")
            
            # Verify MFA token if required
            if mfa_token:
                if not await self._verify_mfa_token(user, mfa_token):
                    await self._handle_failed_login(user, ip_address)
                    raise ValueError("Invalid MFA token")
            else:
                # MFA should be required for all FDA users
                await self._log_failed_authentication(username, "mfa_required", ip_address)
                raise ValueError("MFA token required")
            
            # Check training and validation status
            if not user.training_complete:
                await self._log_failed_authentication(username, "training_incomplete", ip_address)
                raise ValueError("GMP training not complete")
            
            if not user.is_validated:
                await self._log_failed_authentication(username, "account_not_validated", ip_address)
                raise ValueError("Account not validated by supervisor")
            
            # Reset failed login attempts
            await self._reset_failed_attempts(user.id)
            
            # Update last login
            await self._update_last_login(user.id)
            
            # Create session
            session_id = self._generate_session_id()
            session_data = await self._create_session(user, session_id, ip_address, user_agent)
            
            # Get user roles and permissions
            roles = await self._get_user_roles(user.id)
            permissions = await self._get_user_permissions(roles)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                action=AuditAction.LOGIN,
                action_description="User authentication successful",
                entity_type="fda_user",
                entity_id=user.id,
                entity_identifier=user.username,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                regulatory_event=True
            )
            
            logger.info(f"User authenticated successfully: {username}")
            
            return {
                "authenticated": True,
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "department": user.department,
                    "roles": [role.role for role in roles],
                    "permissions": permissions
                },
                "session": session_data,
                "mfa_verified": True,
                "password_expires_at": user.password_expires_at.isoformat() if user.password_expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Authentication failed for {username}: {str(e)}")
            raise
    
    async def assign_user_role(
        self,
        user_id: UUID,
        role: UserRoleEnum,
        assigned_by: UUID,
        assignment_reason: str,
        effective_from: Optional[datetime] = None,
        effective_until: Optional[datetime] = None,
        ip_address: str = "unknown"
    ) -> UserRole:
        """
        Assign role to user with proper authorization and audit trail
        """
        try:
            # Validate assigning user has permission
            if not await self._can_assign_role(assigned_by, role):
                raise ValueError("Insufficient privileges to assign this role")
            
            # Check if user already has this role
            if await self._user_has_role(user_id, role):
                raise ValueError(f"User already has role: {role}")
            
            # Create role assignment
            user_role = UserRole(
                id=uuid4(),
                user_id=user_id,
                role=role,
                assigned_by=assigned_by,
                assigned_at=datetime.now(timezone.utc),
                effective_from=effective_from or datetime.now(timezone.utc),
                effective_until=effective_until,
                assignment_reason=assignment_reason,
                is_active=True
            )
            
            # Store role assignment
            await self._store_user_role(user_role)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=assigned_by,
                username=await self._get_username(assigned_by),
                full_name=await self._get_full_name(assigned_by),
                action=AuditAction.UPDATE,
                action_description=f"Assigned role {role} to user",
                entity_type="user_role",
                entity_id=user_role.id,
                entity_identifier=f"{await self._get_username(user_id)}:{role}",
                new_values={
                    "user_id": str(user_id),
                    "role": role,
                    "assignment_reason": assignment_reason,
                    "effective_from": user_role.effective_from.isoformat(),
                    "effective_until": user_role.effective_until.isoformat() if user_role.effective_until else None
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Role {role} assigned to user {user_id} by {assigned_by}")
            return user_role
            
        except Exception as e:
            logger.error(f"Failed to assign role {role} to user {user_id}: {str(e)}")
            raise
    
    async def validate_user_access(
        self,
        user_id: UUID,
        required_permissions: List[str],
        resource_type: str,
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate user access to specific resources
        """
        try:
            # Get user
            user = await self._get_user(user_id)
            if not user or not user.is_active:
                return {"authorized": False, "reason": "User not found or inactive"}
            
            # Get user roles
            roles = await self._get_user_roles(user_id)
            if not roles:
                return {"authorized": False, "reason": "No roles assigned"}
            
            # Check if any role is active
            active_roles = [role for role in roles if self._is_role_active(role)]
            if not active_roles:
                return {"authorized": False, "reason": "No active roles"}
            
            # Get permissions for active roles
            user_permissions = await self._get_user_permissions(active_roles)
            
            # Check required permissions
            missing_permissions = []
            for permission in required_permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)
            
            if missing_permissions:
                return {
                    "authorized": False,
                    "reason": "Insufficient permissions",
                    "missing_permissions": missing_permissions
                }
            
            # Additional resource-specific checks
            if resource_type and resource_id:
                resource_access = await self._check_resource_access(
                    user_id, active_roles, resource_type, resource_id
                )
                if not resource_access["allowed"]:
                    return {
                        "authorized": False,
                        "reason": f"No access to {resource_type}:{resource_id}",
                        "details": resource_access
                    }
            
            return {
                "authorized": True,
                "user_roles": [role.role for role in active_roles],
                "user_permissions": user_permissions,
                "access_level": self._determine_access_level(active_roles)
            }
            
        except Exception as e:
            logger.error(f"Failed to validate user access for {user_id}: {str(e)}")
            return {"authorized": False, "reason": f"Access validation error: {str(e)}"}
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
        ip_address: str
    ) -> bool:
        """
        Change user password with validation and audit trail
        """
        try:
            # Get user
            user = await self._get_user(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Verify current password
            if not self._verify_password(current_password, user.password_hash, user.salt):
                await self.audit_service.create_audit_log(
                    user_id=user_id,
                    username=user.username,
                    full_name=user.full_name,
                    action=AuditAction.UPDATE,
                    action_description="Password change failed - invalid current password",
                    entity_type="fda_user",
                    entity_id=user_id,
                    entity_identifier=user.username,
                    ip_address=ip_address,
                    regulatory_event=True
                )
                raise ValueError("Current password is incorrect")
            
            # Validate new password strength
            password_validation = self._validate_password_strength(new_password)
            if not password_validation["valid"]:
                raise ValueError(f"Password validation failed: {password_validation['errors']}")
            
            # Check password history
            if await self._password_in_history(user_id, new_password):
                raise ValueError(f"Password has been used recently. Cannot reuse last {self.password_history_count} passwords.")
            
            # Hash new password
            new_salt = secrets.token_hex(32)
            new_password_hash = self._hash_password(new_password, new_salt)
            
            # Update password in database
            await self._update_user_password(
                user_id=user_id,
                password_hash=new_password_hash,
                salt=new_salt,
                password_expires_at=datetime.now(timezone.utc) + timedelta(days=90)
            )
            
            # Add to password history
            await self._add_to_password_history(user_id, new_password_hash)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=user_id,
                username=user.username,
                full_name=user.full_name,
                action=AuditAction.UPDATE,
                action_description="Password changed successfully",
                entity_type="fda_user",
                entity_id=user_id,
                entity_identifier=user.username,
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Password changed for user {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {str(e)}")
            raise
    
    def _generate_secure_password(self) -> str:
        """Generate secure random password"""
        # Generate 16-character password with mixed case, numbers, and symbols
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(16))
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password using PBKDF2"""
        return base64.b64encode(
            hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000  # iterations
            )
        ).decode()
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash = self._hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)
    
    def _validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password meets FDA compliance requirements"""
        errors = []
        
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if password.lower() in ['password', 'admin', 'user', '123456']:
            errors.append("Password cannot be a common word")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    async def _verify_mfa_token(self, user: FDAUser, token: str) -> bool:
        """Verify TOTP MFA token"""
        try:
            # Generate TOTP secret for user
            user_secret = self._generate_user_mfa_secret(user.username)
            totp = pyotp.TOTP(user_secret)
            
            # Verify token with time window
            return totp.verify(token, valid_window=1)
            
        except Exception as e:
            logger.error(f"MFA verification failed for {user.username}: {str(e)}")
            return False
    
    def _generate_user_mfa_secret(self, username: str) -> str:
        """Generate user-specific MFA secret"""
        combined = f"{self.mfa_secret_key}:{username}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        return base64.b32encode(hash_bytes[:20]).decode()
    
    def _is_role_active(self, role: UserRole) -> bool:
        """Check if role assignment is currently active"""
        now = datetime.now(timezone.utc)
        
        if not role.is_active:
            return False
        
        if role.effective_from and now < role.effective_from:
            return False
        
        if role.effective_until and now > role.effective_until:
            return False
        
        return True
    
    def _determine_access_level(self, roles: List[UserRole]) -> str:
        """Determine user's access level based on roles"""
        role_hierarchy = {
            UserRoleEnum.SYSTEM_ADMINISTRATOR: 10,
            UserRoleEnum.QA_MANAGER: 9,
            UserRoleEnum.PRODUCTION_MANAGER: 8,
            UserRoleEnum.QC_MANAGER: 7,
            UserRoleEnum.REGULATORY_AFFAIRS: 6,
            UserRoleEnum.MAINTENANCE_SUPERVISOR: 5,
            UserRoleEnum.PRODUCTION_SUPERVISOR: 4,
            UserRoleEnum.QC_SUPERVISOR: 3,
            UserRoleEnum.QA_SPECIALIST: 2,
            UserRoleEnum.PRODUCTION_OPERATOR: 1,
            UserRoleEnum.QC_ANALYST: 1,
            UserRoleEnum.MAINTENANCE_TECHNICIAN: 1
        }
        
        max_level = 0
        for role in roles:
            level = role_hierarchy.get(UserRoleEnum(role.role), 0)
            max_level = max(max_level, level)
        
        if max_level >= 9:
            return "executive"
        elif max_level >= 6:
            return "management"
        elif max_level >= 3:
            return "supervisor"
        else:
            return "operator"
    
    # Database operations (these would integrate with actual database)
    async def _username_exists(self, username: str) -> bool:
        """Check if username exists"""
        return False
    
    async def _email_exists(self, email: str) -> bool:
        """Check if email exists"""
        return False
    
    async def _employee_id_exists(self, employee_id: str) -> bool:
        """Check if employee ID exists"""
        return False
    
    async def _store_user(self, user: FDAUser):
        """Store user in database"""
        logger.debug(f"Storing user {user.username} in database")
    
    async def _get_user_by_username(self, username: str) -> Optional[FDAUser]:
        """Get user by username"""
        return None
    
    async def _get_user(self, user_id: UUID) -> Optional[FDAUser]:
        """Get user by ID"""
        return None
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"
    
    async def _store_user_role(self, user_role: UserRole):
        """Store user role assignment"""
        logger.debug(f"Storing user role assignment {user_role.id}")
    
    async def _get_user_roles(self, user_id: UUID) -> List[UserRole]:
        """Get user roles"""
        return []
    
    async def _get_user_permissions(self, roles: List[UserRole]) -> List[str]:
        """Get permissions for roles"""
        return []
    
    async def _user_has_role(self, user_id: UUID, role: UserRoleEnum) -> bool:
        """Check if user has specific role"""
        return False
    
    async def _can_assign_role(self, assigning_user_id: UUID, role: UserRoleEnum) -> bool:
        """Check if user can assign specific role"""
        return True
    
    async def _handle_failed_login(self, user: FDAUser, ip_address: str):
        """Handle failed login attempt"""
        logger.debug(f"Handling failed login for {user.username}")
    
    async def _log_failed_authentication(self, username: str, reason: str, ip_address: str):
        """Log failed authentication attempt"""
        logger.warning(f"Failed authentication for {username}: {reason} from {ip_address}")
    
    async def _unlock_user_account(self, user_id: UUID):
        """Unlock user account"""
        logger.debug(f"Unlocking user account {user_id}")
    
    async def _reset_failed_attempts(self, user_id: UUID):
        """Reset failed login attempts"""
        logger.debug(f"Resetting failed attempts for user {user_id}")
    
    async def _update_last_login(self, user_id: UUID):
        """Update last login timestamp"""
        logger.debug(f"Updating last login for user {user_id}")
    
    async def _create_session(self, user: FDAUser, session_id: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Create user session"""
        return {
            "session_id": session_id,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=self.session_timeout_minutes)).isoformat()
        }
    
    async def _send_initial_credentials(self, user: FDAUser, initial_password: str):
        """Send initial credentials to user"""
        logger.info(f"Initial credentials would be sent to {user.email}")
    
    async def _check_resource_access(self, user_id: UUID, roles: List[UserRole], resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Check access to specific resource"""
        return {"allowed": True}
    
    async def _password_in_history(self, user_id: UUID, password: str) -> bool:
        """Check if password is in history"""
        return False
    
    async def _update_user_password(self, user_id: UUID, password_hash: str, salt: str, password_expires_at: datetime):
        """Update user password"""
        logger.debug(f"Updating password for user {user_id}")
    
    async def _add_to_password_history(self, user_id: UUID, password_hash: str):
        """Add password to history"""
        logger.debug(f"Adding password to history for user {user_id}")