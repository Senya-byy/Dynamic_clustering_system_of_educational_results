from flask import Flask, jsonify
from models import db
from config import Config
from controllers.auth_controller import auth_bp
from middleware.auth_middleware import validate_token

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(auth_bp)
    
    @app.route('/protected')
    @validate_token
    def protected():
        return jsonify({
            'message': f"Hello {g.user['login']}!",
            'user_id': g.user['user_id'],
            'role': g.user['role']
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Service is running'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        from repositories.user_repository import UserRepository
        repo = UserRepository()
        if not repo.find_by_login('teacher1'):
            repo.create({
                'login': 'teacher1',
                'password': '123456',
                'role': 'teacher',
                'privacy_mode': False
            })
            print("✅ Test user created: teacher1 / 123456")
        if not repo.find_by_login('student1'):
            repo.create({
                'login': 'student1',
                'password': '123456',
                'role': 'student',
                'privacy_mode': False
            })
            print("✅ Test user created: student1 / 123456")
    print("🚀 Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5001)
