from flask import Blueprint, jsonify, request

device_bp = Blueprint('device', __name__)


@device_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Device blueprint working'}), 200


@device_bp.route('/list', methods=['GET', 'OPTIONS'])
def list_devices():
    """List user devices"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        return jsonify({
            'devices': [],
            'message': 'Device management coming soon'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
