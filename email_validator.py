"""
Email domain validation module
Checks if email domains are valid and can receive emails
"""
import re
import socket
import dns.resolver
from typing import Tuple


class EmailDomainValidator:
    """
    Validates email addresses and their domains.
    Checks DNS MX records to ensure domain can receive emails.
    """
    
    # Email format regex
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(self):
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 5
    
    def validate_email_format(self, email: str) -> Tuple[bool, str]:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email or not email.strip():
            return False, "Email address is empty"
        
        email = email.strip()
        
        if not self.EMAIL_REGEX.match(email):
            return False, "Invalid email format"
        
        if len(email) > 254:  # RFC 5321
            return False, "Email address is too long"
        
        local, domain = email.rsplit('@', 1)
        
        if len(local) > 64:  # RFC 5321
            return False, "Email local part is too long"
        
        if len(domain) > 253:  # RFC 1035
            return False, "Email domain is too long"
        
        return True, ""
    
    def validate_domain_exists(self, domain: str) -> Tuple[bool, str]:
        """
        Check if domain exists and has valid DNS records.
        
        Args:
            domain: Domain name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to get A record (domain exists)
            try:
                self.dns_resolver.resolve(domain, 'A')
                return True, ""
            except dns.resolver.NoAnswer:
                # No A record, but might have MX
                pass
            except dns.resolver.NXDOMAIN:
                return False, f"Domain '{domain}' does not exist"
            except dns.resolver.NoNameservers:
                return False, f"No nameservers found for domain '{domain}'"
            
            # Try AAAA record (IPv6)
            try:
                self.dns_resolver.resolve(domain, 'AAAA')
                return True, ""
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
            
            # If no A or AAAA, domain might still be valid if it has MX
            return False, f"Domain '{domain}' has no valid DNS records"
            
        except dns.exception.Timeout:
            return False, f"DNS lookup timeout for domain '{domain}'"
        except Exception as e:
            return False, f"DNS error for domain '{domain}': {str(e)}"
    
    def validate_mx_records(self, domain: str) -> Tuple[bool, str, list]:
        """
        Check if domain has MX records (can receive email).
        
        Args:
            domain: Domain name to check
            
        Returns:
            Tuple of (has_mx, error_message, mx_records)
        """
        try:
            mx_records = self.dns_resolver.resolve(domain, 'MX')
            mx_list = [str(mx.exchange) for mx in mx_records]
            
            if not mx_list:
                return False, f"Domain '{domain}' has no MX records (cannot receive email)", []
            
            return True, "", mx_list
            
        except dns.resolver.NoAnswer:
            return False, f"Domain '{domain}' has no MX records (cannot receive email)", []
        except dns.resolver.NXDOMAIN:
            return False, f"Domain '{domain}' does not exist", []
        except dns.resolver.NoNameservers:
            return False, f"No nameservers found for domain '{domain}'", []
        except dns.exception.Timeout:
            return False, f"DNS lookup timeout for domain '{domain}'", []
        except Exception as e:
            return False, f"MX lookup error for domain '{domain}': {str(e)}", []
    
    def validate_email_deliverable(self, email: str) -> Tuple[bool, str, dict]:
        """
        Complete email validation including format, domain, and MX records.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message, details)
        """
        details = {
            "email": email,
            "format_valid": False,
            "domain_exists": False,
            "has_mx_records": False,
            "mx_records": [],
            "can_receive_email": False
        }
        
        # Step 1: Validate format
        format_valid, format_error = self.validate_email_format(email)
        details["format_valid"] = format_valid
        
        if not format_valid:
            return False, format_error, details
        
        # Extract domain
        domain = email.rsplit('@', 1)[1]
        details["domain"] = domain
        
        # Step 2: Check if domain exists
        domain_exists, domain_error = self.validate_domain_exists(domain)
        details["domain_exists"] = domain_exists
        
        if not domain_exists:
            return False, domain_error, details
        
        # Step 3: Check MX records
        has_mx, mx_error, mx_records = self.validate_mx_records(domain)
        details["has_mx_records"] = has_mx
        details["mx_records"] = mx_records
        
        if not has_mx:
            return False, mx_error, details
        
        # All checks passed
        details["can_receive_email"] = True
        return True, "", details
    
    def quick_validate(self, email: str) -> Tuple[bool, str]:
        """
        Quick validation (format + domain existence only).
        Faster but less thorough than validate_email_deliverable.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate format
        format_valid, format_error = self.validate_email_format(email)
        if not format_valid:
            return False, format_error
        
        # Check domain exists
        domain = email.rsplit('@', 1)[1]
        domain_exists, domain_error = self.validate_domain_exists(domain)
        
        return domain_exists, domain_error


# Singleton instance
_validator_instance = None

def get_validator() -> EmailDomainValidator:
    """Get or create validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = EmailDomainValidator()
    return _validator_instance


def validate_email(email: str, check_mx: bool = True) -> Tuple[bool, str]:
    """
    Convenience function to validate email.
    
    Args:
        email: Email address to validate
        check_mx: Whether to check MX records (slower but more thorough)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    
    if check_mx:
        is_valid, error, _ = validator.validate_email_deliverable(email)
        return is_valid, error
    else:
        return validator.quick_validate(email)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("Email Domain Validator Test")
    print("=" * 70)
    print()
    
    test_emails = [
        "atharvbhardwaj07@gmail.com",  # Valid
        "test@example.com",             # Valid domain, might not have MX
        "invalid@nonexistentdomain12345.com",  # Invalid domain
        "notanemail",                   # Invalid format
        "test@",                        # Invalid format
    ]
    
    validator = EmailDomainValidator()
    
    for email in test_emails:
        print(f"Testing: {email}")
        is_valid, error, details = validator.validate_email_deliverable(email)
        
        if is_valid:
            print(f"  ✓ Valid - Can receive email")
            print(f"    MX Records: {', '.join(details['mx_records'][:3])}")
        else:
            print(f"  ✗ Invalid - {error}")
        print()
