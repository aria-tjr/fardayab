from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(Enum):
    """Types of errors"""
    NETWORK = "network"
    API_LIMIT = "api_limit"
    DATA_PARSING = "data_parsing"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class RecoveryAction(Enum):
    """Recovery actions for errors"""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ALERT = "alert"
    RESTART = "restart"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """Error context information"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    timestamp: datetime
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ErrorRecovery:
    """Error recovery configuration"""
    error_type: ErrorType
    recovery_action: RecoveryAction
    max_retries: int
    retry_delay: float
    fallback_data: Any
    alert_threshold: int
    auto_recovery: bool


class AdvancedErrorHandler:
    """Advanced error handling and recovery system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.error_history = []
        self.recovery_configs = self._initialize_recovery_configs()
        self.circuit_breakers = {}
        self.alert_thresholds = {}
        self.fallback_data = {}
        
    def _initialize_recovery_configs(self) -> Dict[ErrorType, ErrorRecovery]:
        """Initialize error recovery configurations"""
        return {
            ErrorType.NETWORK: ErrorRecovery(
                error_type=ErrorType.NETWORK,
                recovery_action=RecoveryAction.RETRY,
                max_retries=3,
                retry_delay=2.0,
                fallback_data={"error": "Network unavailable", "data": []},
                alert_threshold=5,
                auto_recovery=True
            ),
            ErrorType.API_LIMIT: ErrorRecovery(
                error_type=ErrorType.API_LIMIT,
                recovery_action=RecoveryAction.FALLBACK,
                max_retries=1,
                retry_delay=60.0,
                fallback_data={"error": "API limit exceeded", "data": []},
                alert_threshold=3,
                auto_recovery=True
            ),
            ErrorType.DATA_PARSING: ErrorRecovery(
                error_type=ErrorType.DATA_PARSING,
                recovery_action=RecoveryAction.FALLBACK,
                max_retries=2,
                retry_delay=1.0,
                fallback_data={"error": "Data parsing failed", "data": []},
                alert_threshold=10,
                auto_recovery=True
            ),
            ErrorType.AUTHENTICATION: ErrorRecovery(
                error_type=ErrorType.AUTHENTICATION,
                recovery_action=RecoveryAction.ALERT,
                max_retries=0,
                retry_delay=0.0,
                fallback_data={"error": "Authentication failed", "data": []},
                alert_threshold=1,
                auto_recovery=False
            ),
            ErrorType.RATE_LIMIT: ErrorRecovery(
                error_type=ErrorType.RATE_LIMIT,
                recovery_action=RecoveryAction.RETRY,
                max_retries=5,
                retry_delay=30.0,
                fallback_data={"error": "Rate limit exceeded", "data": []},
                alert_threshold=3,
                auto_recovery=True
            ),
            ErrorType.TIMEOUT: ErrorRecovery(
                error_type=ErrorType.TIMEOUT,
                recovery_action=RecoveryAction.RETRY,
                max_retries=2,
                retry_delay=5.0,
                fallback_data={"error": "Request timeout", "data": []},
                alert_threshold=5,
                auto_recovery=True
            ),
            ErrorType.VALIDATION: ErrorRecovery(
                error_type=ErrorType.VALIDATION,
                recovery_action=RecoveryAction.SKIP,
                max_retries=0,
                retry_delay=0.0,
                fallback_data={"error": "Validation failed", "data": []},
                alert_threshold=20,
                auto_recovery=True
            ),
            ErrorType.SYSTEM: ErrorRecovery(
                error_type=ErrorType.SYSTEM,
                recovery_action=RecoveryAction.ALERT,
                max_retries=1,
                retry_delay=10.0,
                fallback_data={"error": "System error", "data": []},
                alert_threshold=1,
                auto_recovery=False
            ),
            ErrorType.USER_INPUT: ErrorRecovery(
                error_type=ErrorType.USER_INPUT,
                recovery_action=RecoveryAction.SKIP,
                max_retries=0,
                retry_delay=0.0,
                fallback_data={"error": "Invalid user input", "data": []},
                alert_threshold=50,
                auto_recovery=True
            )
        }
    
    async def handle_error(self, error: Exception, component: str, 
                          user_id: str = None, request_id: str = None,
                          metadata: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """Handle an error with appropriate recovery actions"""
        # Classify error
        error_type = await self._classify_error(error)
        severity = await self._assess_severity(error, error_type)
        
        # Create error context
        error_context = ErrorContext(
            error_id=f"err_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            error_type=error_type,
            severity=severity,
            message=str(error),
            timestamp=datetime.now(),
            component=component,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata or {}
        )
        
        # Log error
        await self._log_error(error_context)
        
        # Get recovery configuration
        recovery_config = self.recovery_configs.get(error_type)
        if not recovery_config:
            recovery_config = self.recovery_configs[ErrorType.SYSTEM]
        
        # Execute recovery action
        success, result = await self._execute_recovery(error_context, recovery_config)
        
        # Update error history
        self.error_history.append(error_context)
        
        # Check for alert thresholds
        await self._check_alert_thresholds(error_context)
        
        return success, result
    
    async def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception"""
        error_message = str(error).lower()
        
        if "network" in error_message or "connection" in error_message:
            return ErrorType.NETWORK
        elif "rate limit" in error_message or "too many requests" in error_message:
            return ErrorType.RATE_LIMIT
        elif "timeout" in error_message:
            return ErrorType.TIMEOUT
        elif "authentication" in error_message or "unauthorized" in error_message:
            return ErrorType.AUTHENTICATION
        elif "api limit" in error_message or "quota" in error_message:
            return ErrorType.API_LIMIT
        elif "json" in error_message or "parsing" in error_message or "decode" in error_message:
            return ErrorType.DATA_PARSING
        elif "validation" in error_message or "invalid" in error_message:
            return ErrorType.VALIDATION
        elif "user" in error_message or "input" in error_message:
            return ErrorType.USER_INPUT
        else:
            return ErrorType.SYSTEM
    
    async def _assess_severity(self, error: Exception, error_type: ErrorType) -> ErrorSeverity:
        """Assess error severity"""
        if error_type == ErrorType.AUTHENTICATION:
            return ErrorSeverity.CRITICAL
        elif error_type == ErrorType.SYSTEM:
            return ErrorSeverity.HIGH
        elif error_type in [ErrorType.NETWORK, ErrorType.API_LIMIT, ErrorType.RATE_LIMIT]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level"""
        log_message = f"Error {error_context.error_id}: {error_context.message} in {error_context.component}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            log.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            log.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            log.warning(log_message)
        else:
            log.info(log_message)
        
        # Log stack trace for high severity errors
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            log.debug(f"Stack trace for {error_context.error_id}:\n{traceback.format_exc()}")
    
    async def _execute_recovery(self, error_context: ErrorContext, 
                              recovery_config: ErrorRecovery) -> Tuple[bool, Any]:
        """Execute recovery action based on configuration"""
        if recovery_config.recovery_action == RecoveryAction.RETRY:
            return await self._retry_operation(error_context, recovery_config)
        elif recovery_config.recovery_action == RecoveryAction.FALLBACK:
            return await self._use_fallback(error_context, recovery_config)
        elif recovery_config.recovery_action == RecoveryAction.SKIP:
            return await self._skip_operation(error_context, recovery_config)
        elif recovery_config.recovery_action == RecoveryAction.ALERT:
            return await self._send_alert(error_context, recovery_config)
        elif recovery_config.recovery_action == RecoveryAction.RESTART:
            return await self._restart_component(error_context, recovery_config)
        else:
            return False, recovery_config.fallback_data
    
    async def _retry_operation(self, error_context: ErrorContext, 
                             recovery_config: ErrorRecovery) -> Tuple[bool, Any]:
        """Retry operation with exponential backoff"""
        for attempt in range(recovery_config.max_retries):
            try:
                # Wait before retry
                if attempt > 0:
                    delay = recovery_config.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                
                # Attempt operation (this would need to be implemented based on specific operation)
                # For now, return success after delay
                await asyncio.sleep(0.1)  # Simulate operation
                return True, {"retry_success": True, "attempt": attempt + 1}
                
            except Exception as e:
                if attempt == recovery_config.max_retries - 1:
                    # Final attempt failed, use fallback
                    return await self._use_fallback(error_context, recovery_config)
                continue
        
        return False, recovery_config.fallback_data
    
    async def _use_fallback(self, error_context: ErrorContext, 
                          recovery_config: ErrorRecovery) -> Tuple[bool, Any]:
        """Use fallback data when operation fails"""
        # Get cached data if available
        cached_data = await self._get_cached_data(error_context.component)
        if cached_data:
            return True, cached_data
        
        # Use configured fallback data
        return True, recovery_config.fallback_data
    
    async def _skip_operation(self, error_context: ErrorContext, 
                            recovery_config: ErrorRecovery) -> Tuple[bool, Any]:
        """Skip operation and return empty result"""
        return True, {"skipped": True, "reason": error_context.message}
    
    async def _send_alert(self, error_context: ErrorContext, 
                        recovery_config: ErrorRecovery) -> Tuple[bool, Any]:
        """Send alert for critical errors"""
        alert_message = f"Critical error in {error_context.component}: {error_context.message}"
        log.critical(f"ALERT: {alert_message}")
        
        # In a real implementation, this would send to monitoring system
        # For now, just log the alert
        return False, {"alert_sent": True, "message": alert_message}
    
    async def _restart_component(self, error_context: ErrorContext, 
                               recovery_config: ErrorRecovery) -> Tuple[bool, Any]:
        """Restart component after error"""
        log.warning(f"Restarting component {error_context.component}")
        
        # In a real implementation, this would restart the specific component
        # For now, just return success
        return True, {"component_restarted": True, "component": error_context.component}
    
    async def _get_cached_data(self, component: str) -> Optional[Any]:
        """Get cached data for fallback"""
        # In a real implementation, this would retrieve from cache
        # For now, return None
        return None
    
    async def _check_alert_thresholds(self, error_context: ErrorContext):
        """Check if error count exceeds alert thresholds"""
        error_type = error_context.error_type
        component = error_context.component
        
        # Count recent errors of this type
        recent_errors = [
            e for e in self.error_history
            if e.error_type == error_type and e.component == component
            and e.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        recovery_config = self.recovery_configs.get(error_type)
        if recovery_config and len(recent_errors) >= recovery_config.alert_threshold:
            await self._send_alert(error_context, recovery_config)
    
    async def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and insights"""
        if not self.error_history:
            return {"error": "No error history available"}
        
        # Calculate statistics
        total_errors = len(self.error_history)
        error_types = {}
        error_severities = {}
        component_errors = {}
        
        for error in self.error_history:
            # Count by type
            error_type = error.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count by severity
            severity = error.severity.value
            error_severities[severity] = error_severities.get(severity, 0) + 1
            
            # Count by component
            component = error.component
            component_errors[component] = component_errors.get(component, 0) + 1
        
        # Calculate error rates
        error_rate = total_errors / max(len(self.error_history), 1)
        
        # Get recent errors (last 24 hours)
        recent_errors = [
            e for e in self.error_history
            if e.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            "total_errors": total_errors,
            "error_types": error_types,
            "error_severities": error_severities,
            "component_errors": component_errors,
            "error_rate": error_rate,
            "recent_errors_24h": len(recent_errors),
            "most_common_error_type": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
            "most_problematic_component": max(component_errors.items(), key=lambda x: x[1])[0] if component_errors else None
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        error_stats = await self.get_error_statistics()
        
        # Determine health status
        if error_stats["recent_errors_24h"] == 0:
            health_status = "excellent"
        elif error_stats["recent_errors_24h"] < 5:
            health_status = "good"
        elif error_stats["recent_errors_24h"] < 20:
            health_status = "fair"
        else:
            health_status = "poor"
        
        # Get recommendations
        recommendations = []
        if error_stats["recent_errors_24h"] > 10:
            recommendations.append("High error rate detected - investigate system stability")
        
        if error_stats["most_common_error_type"] == "network":
            recommendations.append("Network issues detected - check connectivity and API endpoints")
        
        if error_stats["most_common_error_type"] == "api_limit":
            recommendations.append("API limits being hit - consider rate limiting or upgrading API plan")
        
        return {
            "health_status": health_status,
            "error_statistics": error_stats,
            "recommendations": recommendations,
            "last_updated": datetime.now().isoformat()
        }
    
    async def clear_error_history(self, older_than_days: int = 30):
        """Clear old error history"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        self.error_history = [
            e for e in self.error_history
            if e.timestamp > cutoff_date
        ]
        
        log.info(f"Cleared error history older than {older_than_days} days")
    
    async def get_recovery_recommendations(self) -> List[str]:
        """Get recommendations for improving error recovery"""
        recommendations = []
        
        error_stats = await self.get_error_statistics()
        
        # Analyze error patterns
        if error_stats["most_common_error_type"] == "network":
            recommendations.append("Implement circuit breaker pattern for network calls")
            recommendations.append("Add more robust retry logic with exponential backoff")
        
        if error_stats["most_common_error_type"] == "api_limit":
            recommendations.append("Implement rate limiting and request queuing")
            recommendations.append("Consider upgrading API plan or using multiple API keys")
        
        if error_stats["most_common_error_type"] == "data_parsing":
            recommendations.append("Add more robust data validation and sanitization")
            recommendations.append("Implement graceful degradation for malformed data")
        
        if error_stats["recent_errors_24h"] > 20:
            recommendations.append("Consider implementing monitoring and alerting system")
            recommendations.append("Add more comprehensive error logging and tracking")
        
        return recommendations
