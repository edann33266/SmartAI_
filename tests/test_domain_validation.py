"""
Test script for email domain validation
"""
from email_validator import EmailDomainValidator

def test_domain_validation():
    print("=" * 70)
    print("Email Domain Validation Test")
    print("=" * 70)
    print()
    
    validator = EmailDomainValidator()
    
    test_cases = [
        # (email, should_be_valid, description)
        ("atharvbhardwaj07@gmail.com", True, "Valid Gmail address"),
        ("test@yahoo.com", True, "Valid Yahoo address"),
        ("user@outlook.com", True, "Valid Outlook address"),
        ("contact@example.com", True, "Valid example.com (has MX)"),
        ("invalid@nonexistentdomain12345xyz.com", False, "Non-existent domain"),
        ("test@invaliddomain", False, "Invalid TLD"),
        ("notanemail", False, "Not an email format"),
        ("test@", False, "Missing domain"),
        ("@example.com", False, "Missing local part"),
    ]
    
    passed = 0
    failed = 0
    
    for email, should_be_valid, description in test_cases:
        print(f"Testing: {email}")
        print(f"  Description: {description}")
        print(f"  Expected: {'✓ Valid' if should_be_valid else '✗ Invalid'}")
        
        is_valid, error, details = validator.validate_email_deliverable(email)
        
        if is_valid == should_be_valid:
            print(f"  Result: ✅ PASS")
            passed += 1
        else:
            print(f"  Result: ❌ FAIL")
            failed += 1
        
        if is_valid:
            print(f"  ✓ Can receive email")
            if details.get('mx_records'):
                print(f"    MX Records: {', '.join(details['mx_records'][:2])}")
        else:
            print(f"  ✗ {error}")
        
        print()
    
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = test_domain_validation()
        exit(0 if success else 1)
    except ImportError as e:
        print("❌ Error: dnspython not installed")
        print("   Install with: pip install dnspython")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
