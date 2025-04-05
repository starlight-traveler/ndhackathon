from flask import Blueprint, jsonify, current_app as app

another_bp = Blueprint('another', __name__)

@another_bp.route('/example', methods=['GET'])
def example():
    app.logger.info("Example route accessed")
    return jsonify({'message': 'This is another route!'}), 200
