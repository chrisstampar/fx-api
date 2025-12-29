"""
Enhanced input validation utilities.

Provides validation for Ethereum addresses, amounts, and other common inputs.
"""

import re
from typing import Optional
from web3 import Web3


def is_valid_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format.
    
    Args:
        address: Address string to validate
        
    Returns:
        True if valid, False otherwise
        
    Note:
        This validates the format only. Invalid checksums are still considered
        valid addresses (they can be corrected via checksumming).
    """
    if not address or not isinstance(address, str):
        return False
    
    # Check basic format (0x + 40 hex characters)
    # This is sufficient - checksum validation is separate
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))


def validate_and_checksum_address(address: str) -> str:
    """
    Validate and convert address to checksum format.
    
    Args:
        address: Address string to validate and checksum
        
    Returns:
        Checksummed address
        
    Raises:
        ValueError: If address is invalid
    """
    if not is_valid_ethereum_address(address):
        raise ValueError(f"Invalid Ethereum address format: {address}")
    
    try:
        return Web3.to_checksum_address(address)
    except Exception as e:
        raise ValueError(f"Failed to checksum address: {e}")


def is_valid_amount(amount: str, allow_zero: bool = True, max_decimals: Optional[int] = None) -> bool:
    """
    Validate amount string.
    
    Args:
        amount: Amount string to validate
        allow_zero: Whether zero amounts are allowed
        max_decimals: Maximum number of decimal places (None for no limit)
        
    Returns:
        True if valid, False otherwise
    """
    if not amount or not isinstance(amount, str):
        return False
    
    # Check for 'max' special value
    if amount.lower() == 'max':
        return True
    
    # Check for valid decimal number
    try:
        # Remove leading/trailing whitespace
        amount = amount.strip()
        
        # Check format (optional sign, digits, optional decimal point, optional digits)
        if not re.match(r'^-?\d+(\.\d+)?$', amount):
            return False
        
        # Convert to float to validate
        value = float(amount)
        
        # Check if zero is allowed
        if not allow_zero and value == 0:
            return False
        
        # Check if negative
        if value < 0:
            return False
        
        # Check decimal places
        if max_decimals is not None:
            if '.' in amount:
                decimal_part = amount.split('.')[1]
                if len(decimal_part) > max_decimals:
                    return False
        
        return True
    except (ValueError, AttributeError):
        return False


def validate_amount(amount: str, allow_zero: bool = True, max_decimals: Optional[int] = None) -> str:
    """
    Validate and normalize amount string.
    
    Args:
        amount: Amount string to validate
        allow_zero: Whether zero amounts are allowed
        max_decimals: Maximum number of decimal places (None for no limit)
        
    Returns:
        Normalized amount string
        
    Raises:
        ValueError: If amount is invalid
    """
    if not is_valid_amount(amount, allow_zero, max_decimals):
        error_msg = f"Invalid amount: {amount}"
        if not allow_zero:
            error_msg += " (zero not allowed)"
        if max_decimals is not None:
            error_msg += f" (max {max_decimals} decimals)"
        raise ValueError(error_msg)
    
    return amount.strip()


def is_valid_hex_string(hex_str: str, prefix_required: bool = True) -> bool:
    """
    Validate hex string format.
    
    Args:
        hex_str: Hex string to validate
        prefix_required: Whether '0x' prefix is required
        
    Returns:
        True if valid, False otherwise
    """
    if not hex_str or not isinstance(hex_str, str):
        return False
    
    if prefix_required:
        if not hex_str.startswith('0x'):
            return False
        pattern = r'^0x[a-fA-F0-9]+$'
    else:
        pattern = r'^[a-fA-F0-9]+$'
    
    return bool(re.match(pattern, hex_str))


def validate_hex_string(hex_str: str, prefix_required: bool = True) -> str:
    """
    Validate and normalize hex string.
    
    Args:
        hex_str: Hex string to validate
        prefix_required: Whether '0x' prefix is required
        
    Returns:
        Normalized hex string
        
    Raises:
        ValueError: If hex string is invalid
    """
    if not is_valid_hex_string(hex_str, prefix_required):
        error_msg = f"Invalid hex string: {hex_str}"
        if prefix_required:
            error_msg += " (must start with '0x')"
        raise ValueError(error_msg)
    
    return hex_str.lower()


def is_valid_token_name(token_name: str) -> bool:
    """
    Validate token name format.
    
    Args:
        token_name: Token name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not token_name or not isinstance(token_name, str):
        return False
    
    # Token names should be lowercase alphanumeric (with optional underscores)
    return bool(re.match(r'^[a-z0-9_]+$', token_name.lower()))


def validate_token_name(token_name: str) -> str:
    """
    Validate and normalize token name.
    
    Args:
        token_name: Token name to validate
        
    Returns:
        Normalized (lowercase) token name
        
    Raises:
        ValueError: If token name is invalid
    """
    if not is_valid_token_name(token_name):
        raise ValueError(f"Invalid token name: {token_name}")
    
    return token_name.lower()

