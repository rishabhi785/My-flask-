from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict
import os
import time
import json

app = Flask(__name__)
CORS(app)

# Device registry
device_registry = defaultdict(dict)
user_devices = defaultdict(list)

def verify_device_data(user_id, device_data):
    """
    Advanced device verification with duplicate detection
    """
    fingerprint = device_data.get('fingerprint')
    ip_address = device_data.get('ip')
    user_agent = device_data.get('browser', '') or device_data.get('userAgent', '')
    timezone = device_data.get('timezone')

    if not all([fingerprint, ip_address]):
        return False, "Missing device information"

    # Create unique device signature
    device_signature = f"{fingerprint}-{ip_address}-{user_agent}-{timezone}"

    # Check if this device is already registered
    if device_signature in device_registry:
        registered_user = device_registry[device_signature].get('user_id')
        registered_time = device_registry[device_signature].get('timestamp')

        # Same device, different user - POTENTIAL FRAUD
        if registered_user != user_id:
            time_diff = time.time() - registered_time
            hours_diff = time_diff / 3600

            # Allow if registered more than 24 hours ago (maybe family device)
            if hours_diff < 24:
                return False, f"This device was recently used by another user (within {int(hours_diff)} hours)"
            else:
                # Old registration, allow but update registry
                device_registry[device_signature] = {
                    'user_id': user_id,
                    'timestamp': time.time(),
                    'device_data': device_data
                }
                return True, "Device verification successful (updated old registration)"

        # Same device, same user - ALLOW
        return True, "Device verification successful"

    # Check if user has too many devices
    user_device_count = len(user_devices.get(user_id, []))
    if user_device_count >= 3:  # Maximum 3 devices per user
        return False, "Maximum device limit reached (3 devices per user)"

    # New device - REGISTER
    device_registry[device_signature] = {
        'user_id': user_id,
        'timestamp': time.time(),
        'device_data': device_data
    }

    # Add to user's device list
    user_devices[user_id].append(device_signature)

    return True, "New device registered successfully"

@app.route('/')
def home():
    return "✅ Device Verification Backend is running!"

@app.route('/verify', methods=['POST', 'OPTIONS'])
def verify_device():
    try:
        if request.method == 'OPTIONS':
            return '', 200

        data = request.get_json()
        print("📨 Received data:", data)

        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400

        user_id = data.get('user_id')
        device_data = data.get('device_data', {})

        # Ensure device_data is dictionary
        if isinstance(device_data, str):
            try:
                device_data = json.loads(device_data)
            except json.JSONDecodeError:
                device_data = {}

        if not user_id:
            return jsonify({'status': 'error', 'message': 'User ID required'}), 400

        print(f"🔍 Verifying device for user: {user_id}")
        print(f"📱 Fingerprint: {device_data.get('fingerprint')}")
        print(f"🌐 IP: {device_data.get('ip')}")

        # Verify device with advanced detection
        is_verified, message = verify_device_data(user_id, device_data)

        if is_verified:
            print(f"✅ Verification successful for user {user_id}")
            return jsonify({
                'status': 'success', 
                'message': message,
                'user_id': user_id
            })
        else:
            print(f"❌ Verification failed for user {user_id}: {message}")
            return jsonify({
                'status': 'failed', 
                'message': message,
                'user_id': user_id
            })

    except Exception as e:
        print(f"💥 Error in verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get verification statistics"""
    return jsonify({
        'total_devices_registered': len(device_registry),
        'total_users': len(user_devices),
        'timestamp': time.time()
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Device Verification Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
