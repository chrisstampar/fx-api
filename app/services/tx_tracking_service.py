"""
Transaction tracking service.

Tracks broadcasted transactions and their status.
Uses in-memory storage (can be extended to use Redis).
"""

import time
from typing import Dict, Optional, Any
from datetime import datetime
from app.config import settings

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except Exception:
    pass


class TransactionStatus:
    """Transaction status constants."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class TransactionTracker:
    """
    In-memory transaction tracker.
    
    Tracks broadcasted transactions and their status.
    Can be extended to use Redis for persistence.
    """
    
    def __init__(self):
        """Initialize transaction tracker."""
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._max_age = 3600 * 24  # 24 hours
    
    def track_transaction(self, tx_hash: str, from_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Track a new transaction.
        
        Args:
            tx_hash: Transaction hash
            from_address: Address that sent the transaction (optional)
            
        Returns:
            Transaction tracking info
        """
        tx_info = {
            "tx_hash": tx_hash,
            "from_address": from_address,
            "status": TransactionStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "block_number": None,
            "confirmations": 0,
            "error": None
        }
        
        self._transactions[tx_hash.lower()] = tx_info
        
        if logger:
            logger.info(f"Tracking transaction: {tx_hash}")
        
        return tx_info
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction status.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction info or None if not found
        """
        return self._transactions.get(tx_hash.lower())
    
    def update_transaction(
        self,
        tx_hash: str,
        status: Optional[str] = None,
        block_number: Optional[int] = None,
        confirmations: Optional[int] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update transaction status.
        
        Args:
            tx_hash: Transaction hash
            status: New status
            block_number: Block number where transaction was included
            confirmations: Number of confirmations
            error: Error message if failed
            
        Returns:
            Updated transaction info or None if not found
        """
        tx_info = self._transactions.get(tx_hash.lower())
        if not tx_info:
            return None
        
        if status:
            tx_info["status"] = status
        if block_number is not None:
            tx_info["block_number"] = block_number
        if confirmations is not None:
            tx_info["confirmations"] = confirmations
        if error:
            tx_info["error"] = error
        
        tx_info["updated_at"] = datetime.utcnow().isoformat()
        
        return tx_info
    
    def cleanup_old_transactions(self) -> int:
        """
        Remove old transactions from tracking.
        
        Returns:
            Number of transactions removed
        """
        current_time = time.time()
        removed = 0
        
        for tx_hash, tx_info in list(self._transactions.items()):
            created_time = datetime.fromisoformat(tx_info["created_at"]).timestamp()
            age = current_time - created_time
            
            if age > self._max_age:
                self._transactions.pop(tx_hash, None)
                removed += 1
        
        if logger and removed > 0:
            logger.info(f"Cleaned up {removed} old transactions")
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracking statistics.
        
        Returns:
            Dictionary with stats
        """
        status_counts = {}
        for tx_info in self._transactions.values():
            status = tx_info.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tracked": len(self._transactions),
            "status_counts": status_counts,
            "max_age_seconds": self._max_age
        }


# Global tracker instance
_tx_tracker = TransactionTracker()


def get_tx_tracker() -> TransactionTracker:
    """Get the global transaction tracker instance."""
    return _tx_tracker

