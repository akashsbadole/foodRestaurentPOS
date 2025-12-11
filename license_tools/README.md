# POS MVP License Tools

A comprehensive license key generation and validation system for the POS MVP application. This toolkit provides secure, cryptographically-signed license management with support for multiple license types, hardware binding, and both online/offline validation.

## Features

- **Cryptographic Security**: RSA-4096/ECC signature support with white-box cryptography
- **Multiple License Types**: Trial, Standard, Professional, and Enterprise licenses
- **Hardware Binding**: Optional hardware fingerprint binding for enhanced security
- **Batch Generation**: Efficient bulk license generation with multiple export formats
- **Comprehensive Validation**: Multi-layered validation with detailed reporting
- **License Server**: Optional REST API server for online validation
- **Command-Line Tools**: Easy-to-use CLI for all operations
- **Export Formats**: JSON, CSV, text, and encrypted binary formats

## Installation

### Prerequisites

- Python 3.8 or higher
- Required packages (install via pip):
  ```bash
  pip install cryptography flask flask-cors requests
  ```

### Setup

1. Clone or download the license tools
2. Ensure the POS MVP application is in the parent directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Generate a Single License

```bash
# Generate a professional license
python license_key_generator.py \
  --type professional \
  --name "John Doe" \
  --email "john@example.com" \
  --company "Acme Restaurant" \
  --hardware-binding \
  --output my_license.json
```

### Validate a License

```bash
# Validate with detailed output
python license_validator_cli.py \
  ABCD-1234-EFGH-5678 \
  --detailed \
  --level advanced
```

### Start License Server

```bash
# Start the license server
python license_server.py \
  --host 0.0.0.0 \
  --port 8080 \
  --database licenses.db
```

## Components

### License Key Generator (`license_key_generator.py`)

The main utility for generating cryptographically secure license keys.

#### Command-Line Options

```
usage: license_key_generator.py [-h] --type {trial,standard,professional,enterprise}
                              [--name NAME] [--email EMAIL] [--company COMPANY]
                              [--phone PHONE] [--batch BATCH]
                              [--output OUTPUT] [--format {json,csv,text,binary}]
                              [--algorithm {RSA,ECC}] [--hardware-binding]
                              [--expiry-days EXPIRY_DAYS]
                              [--max-activations MAX_ACTIVATIONS]
                              [--activation-code ACTIVATION_CODE]
                              [--custom-features CUSTOM_FEATURES]
                              [--list-templates] [--validate VALIDATE]
```

#### Examples

**Generate a trial license:**
```bash
python license_key_generator.py \
  --type trial \
  --name "Trial User" \
  --email "trial@example.com" \
  --hardware-binding \
  --expiry-days 30
```

**Generate licenses from CSV file:**
```bash
python license_key_generator.py \
  --type professional \
  --batch customers.csv \
  --output licenses.json \
  --format json \
  --hardware-binding
```

**Generate with custom features:**
```bash
python license_key_generator.py \
  --type standard \
  --name "Custom User" \
  --email "custom@example.com" \
  --custom-features "orders.create,orders.view,menu.view,reports.basic"
```

### License Validator CLI (`license_validator_cli.py`)

Command-line tool for comprehensive license validation.

#### Command-Line Options

```
usage: license_validator_cli.py [-h] [license_key] [--activation-id ACTIVATION_ID]
                              [--hardware-fingerprint HARDWARE_FINGERPRINT]
                              [--server-url SERVER_URL]
                              [--mode {online,offline,hybrid}]
                              [--level {basic,standard,advanced,stealth}]
                              [--online] [--detailed] [--batch BATCH]
                              [--output OUTPUT] [--format {json,text}]
                              [--blacklist-check] [--heartbeat]
                              [--status] [--usage-data USAGE_DATA]
```

#### Examples

**Basic validation:**
```bash
python license_validator_cli.py ABCD-1234-EFGH-5678
```

**Advanced validation with details:**
```bash
python license_validator_cli.py ABCD-1234-EFGH-5678 \
  --level advanced \
  --detailed \
  --online
```

**Batch validation:**
```bash
python license_validator_cli.py \
  --batch licenses.txt \
  --output validation_report.json \
  --format json
```

**Check blacklist status:**
```bash
python license_validator_cli.py ABCD-1234-EFGH-5678 \
  --blacklist-check
```

### License Server (`license_server.py`)

Optional REST API server for online license validation.

#### Command-Line Options

```
usage: license_server.py [-h] [--host HOST] [--port PORT]
                        [--database DATABASE] [--debug] [--init-db]
```

#### API Endpoints

**Validate License**
```
POST /api/v1/validate
Content-Type: application/json

{
  "license_key": "ABCD-1234-EFGH-5678",
  "activation_id": "ACT_001",
  "hardware_fingerprint": "a1b2c3d4...",
  "signature": "base64_signature"
}
```

**Activate License**
```
POST /api/v1/activate
Content-Type: application/json

{
  "license_key": "ABCD-1234-EFGH-5678",
  "activation_code": "optional_code",
  "hardware_fingerprint": "a1b2c3d4...",
  "signature": "base64_signature"
}
```

**Send Heartbeat**
```
POST /api/v1/heartbeat
Content-Type: application/json

{
  "license_key": "ABCD-1234-EFGH-5678",
  "activation_id": "ACT_001",
  "usage_data": {
    "app_version": "1.0.0",
    "usage_hours": 24
  },
  "signature": "base64_signature"
}
```

**Check Blacklist**
```
POST /api/v1/blacklist
Content-Type: application/json

{
  "license_key": "ABCD-1234-EFGH-5678",
  "hardware_fingerprint": "a1b2c3d4...",
  "signature": "base64_signature"
}
```

## License Types

### Trial License
- **Duration**: 30 days
- **Max Activations**: 1
- **Offline Grace Period**: 7 days
- **Features**: Basic POS functionality
  - orders.create, orders.view, orders.edit
  - menu.view, menu.edit
  - inventory.view
  - reports.basic
  - tables.manage

### Standard License
- **Duration**: 365 days (renewable)
- **Max Activations**: 3
- **Offline Grace Period**: 30 days
- **Features**: Standard POS functionality
  - orders.create, orders.view, orders.edit, orders.delete
  - menu.view, menu.edit, menu.create
  - inventory.view, inventory.edit
  - reports.basic
  - tables.manage
  - users.create, users.edit

### Professional License
- **Duration**: 365 days (renewable)
- **Max Activations**: 5
- **Offline Grace Period**: 45 days
- **Features**: Professional POS functionality
  - orders.create, orders.view, orders.edit, orders.delete
  - menu.view, menu.edit, menu.create, menu.delete
  - inventory.view, inventory.edit, inventory.manage
  - reports.basic, reports.advanced
  - tables.manage
  - users.create, users.edit, users.manage
  - export.data, import.data
  - backup.create, backup.restore

### Enterprise License
- **Duration**: 365 days (renewable)
- **Max Activations**: 10
- **Offline Grace Period**: 60 days
- **Features**: Full enterprise functionality
  - All Professional features
  - api.access, multi_branch
  - advanced_analytics, priority_support

## Examples

The `examples/` directory contains comprehensive example scripts:

### `generate_keys.py`
Demonstrates various license generation scenarios:
- Single license generation
- Different license types
- Batch generation
- Export formats
- Validation of generated licenses

### `validate_licenses.py`
Demonstrates various validation scenarios:
- Single license validation
- Batch validation
- Blacklist checking
- Heartbeat functionality
- Different validation levels

### `batch_generation.py`
Demonstrates large-scale license generation:
- Bulk license generation
- CSV/JSON input processing
- Custom feature sets
- Performance testing

## Security Features

### Cryptographic Security
- **RSA-4096/ECC**: Industry-standard asymmetric cryptography
- **Digital Signatures**: All licenses are cryptographically signed
- **Integrity Hashes**: Tamper detection with SHA-256 hashes
- **White-Box Cryptography**: Protection against reverse engineering

### Hardware Binding
- **Advanced Fingerprinting**: Multi-component hardware identification
- **Anti-Tampering**: Detection of hardware changes
- **Tolerance Levels**: Configurable sensitivity for hardware changes

### Validation Layers
1. **Basic**: License format and signature verification
2. **Standard**: Hardware binding and expiry checks
3. **Advanced**: Integrity verification and activation limits
4. **Stealth**: Anti-debugging and virtualization detection

## Configuration

### Environment Variables

- `LICENSE_SERVER_ADMIN_KEY`: Admin key for server management
- `LICENSE_SERVER_HOST`: Default server host (0.0.0.0)
- `LICENSE_SERVER_PORT`: Default server port (8080)

### Configuration Files

License keys and cryptographic materials are stored in:
```
src/config/license_keys/
├── license_private_rsa.pem
├── license_public_rsa.pem
├── license_private_ecc.pem
└── license_public_ecc.pem
```

## Integration

### Client Integration

```python
from src.utils.license_manager import LicenseManager

# Initialize license manager
license_manager = LicenseManager(db_manager)

# Activate license
result = license_manager.activate_license(
    "ABCD-1234-EFGH-5678",
    activation_code="optional_code"
)

if result['success']:
    print("License activated successfully!")
    license_info = result['license_info']
else:
    print(f"Activation failed: {result['message']}")

# Check feature access
feature_result = license_manager.check_feature_access("orders.create")
if feature_result['allowed']:
    print("Feature available")
else:
    print(f"Feature not available: {feature_result['reason']}")
```

### Server Integration

```python
from license_server import LicenseServer

# Initialize server
server = LicenseServer(
    database_path="licenses.db",
    host="0.0.0.0",
    port=8080
)

# Start server
server.run()
```

## Troubleshooting

### Common Issues

**License validation fails:**
1. Check license key format (XXXX-XXXX-XXXX-XXXX)
2. Verify system clock is correct
3. Ensure cryptographic keys are available
4. Check internet connection for online validation

**Hardware binding issues:**
1. Run with `--detailed` validation to see specific failures
2. Check for hardware changes
3. Consider tolerance levels for minor hardware changes

**Server connection issues:**
1. Verify server URL is correct
2. Check firewall settings
3. Ensure server is running and accessible
4. Validate SSL certificates

### Debug Mode

Enable debug output for troubleshooting:

```bash
# Generator debug
python license_key_generator.py --type trial --name "Debug User" --debug

# Validator debug
python license_validator_cli.py ABCD-1234-EFGH-5678 --detailed --level stealth

# Server debug
python license_server.py --debug --port 8080
```

### Log Files

Check these locations for log files:
- Application logs: `logs/`
- Server logs: Server console output
- Validation logs: Database audit tables

## Performance Considerations

### Batch Generation
- Use ECC for faster key generation
- Process in smaller batches for memory efficiency
- Consider parallel processing for very large batches

### Validation Performance
- Cache validation results when appropriate
- Use appropriate validation levels
- Implement graceful degradation for network issues

### Server Scaling
- Use connection pooling for database
- Implement caching for frequent validations
- Consider load balancing for high-traffic deployments

## Security Best Practices

### Key Management
- Store private keys securely
- Rotate keys periodically
- Use hardware security modules when possible
- Backup keys in secure locations

### License Distribution
- Use secure channels for license delivery
- Encrypt license files during transport
- Implement license activation codes
- Track license distribution

### Server Security
- Use HTTPS for all communications
- Implement rate limiting
- Monitor for abuse patterns
- Regular security audits

## API Reference

### License Generator Class

```python
class LicenseKeyGenerator:
    def __init__(self, algorithm: str = "RSA")
    def generate_license_key(self, license_type: str, customer_data: dict,
                          hardware_binding: bool = False, 
                          custom_features: list = None,
                          expiry_days: int = None, 
                          activation_code: str = None) -> dict
    def generate_batch_keys(self, license_type: str, customer_list: list,
                         hardware_binding: bool = False, 
                         custom_features: list = None,
                         expiry_days: int = None, 
                         activation_code: str = None) -> list
    def export_licenses(self, licenses: list, output_file: str, 
                       format_type: str = "json") -> bool
```

### License Validator Class

```python
class LicenseValidatorCLI:
    def __init__(self, server_url: str = None, mode: str = "hybrid")
    def validate_license_key(self, license_key: str, activation_id: str = None,
                           hardware_fingerprint: str = None, 
                           validation_level: str = "advanced",
                           online: bool = False, 
                           detailed: bool = False) -> dict
    def check_blacklist(self, license_key: str = None, 
                       hardware_fingerprint: str = None) -> dict
    def send_heartbeat(self, license_key: str, activation_id: str,
                      usage_data: dict = None) -> dict
```

### License Server Class

```python
class LicenseServer:
    def __init__(self, database_path: str = "license_server.db", 
                 host: str = "0.0.0.0", port: int = 8080, 
                 debug: bool = False)
    def run(self) -> None
```

## License

This license management system is part of the POS MVP application and is subject to the same license terms and conditions.

## Support

For support and documentation:
- Check the main POS MVP documentation
- Review the example scripts in the `examples/` directory
- Examine the source code for detailed implementation information
- Check the troubleshooting section for common issues

## Version History

- **v1.0.0**: Initial release with comprehensive license management
  - RSA-4096/ECC cryptographic support
  - Hardware fingerprint binding
  - Multi-level validation
  - REST API server
  - Batch generation capabilities
  - Multiple export formats