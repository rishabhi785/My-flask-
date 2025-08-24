from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Device Verification Backend is running on Pella!"

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"})

@app.route('/verify', methods=['POST', 'OPTIONS'])
def verify_device():
    try:
        if request.method == 'OPTIONS':
            return '', 200
            
        data = request.get_json()
        print("📨 Received verification request:", data)
        
        # Simple verification logic
        user_id = data.get('user_id')
        if user_id:
            return jsonify({
                'status': 'success', 
                'message': 'Device verification successful!',
                'user_id': user_id
            })
        else:
            return jsonify({
                'status': 'failed', 
                'message': 'User ID missing!'
            })
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
