from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import os

service_b = Flask(__name__)
CORS(service_b)

# Create instance directory if it doesn't exist
instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# Configure database to use instance directory
db_path = os.path.join(instance_dir, 'tasks.db')
service_b.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
service_b.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(service_b)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

@service_b.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('user_id'):
        return jsonify({'error': 'Datos inválidos'}), 400
    try:
        user_check = requests.get(f'http://localhost:5001/users/{data["user_id"]}')
    except Exception as e:
        return jsonify({'error': f'Error de conexión al verificar usuario: {str(e)}'}), 500

    if user_check.status_code != 200:
        return jsonify({'error': 'ID de usuario inválido'}), 400

    task = Task(title=data['title'], user_id=data['user_id'])
    db.session.add(task)
    db.session.commit()
    return jsonify({'id': task.id, 'title': task.title, 'user_id': task.user_id}), 201

@service_b.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([{'id': t.id, 'title': t.title, 'user_id': t.user_id} for t in tasks])

@service_b.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': f'Task {task_id} deleted successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

@service_b.route('/tasks/cleanup', methods=['DELETE'])
def cleanup_tasks():
    """Delete all tasks - for testing purposes only"""
    try:
        num_deleted = Task.query.delete()
        db.session.commit()
        return jsonify({'message': f'Deleted {num_deleted} tasks'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@service_b.route('/tasks/cleanup-specific', methods=['DELETE'])
def cleanup_specific_tasks():
    """Delete specific tasks by IDs - used for targeted test cleanup"""
    try:
        data = request.get_json()
        if not data or 'task_ids' not in data:
            return jsonify({'error': 'task_ids list is required'}), 400
        
        task_ids = data['task_ids']
        if not isinstance(task_ids, list):
            return jsonify({'error': 'task_ids must be a list'}), 400
        
        deleted_count = 0
        for task_id in task_ids:
            task = Task.query.get(task_id)
            if task:
                db.session.delete(task)
                deleted_count += 1
        
        db.session.commit()
        return jsonify({'message': f'Deleted {deleted_count} specific tasks'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@service_b.route('/tasks/stats', methods=['GET'])
def get_task_stats():
    """Get task statistics - useful for system monitoring and dashboards"""
    try:
        from datetime import datetime
        from collections import Counter
        
        total_tasks = Task.query.count()
        
        # Get all tasks for analysis
        all_tasks = Task.query.all()
        tasks_data = [{'id': t.id, 'title': t.title, 'user_id': t.user_id} for t in all_tasks]
        
        # Count tasks per user
        user_task_counts = Counter(task.user_id for task in all_tasks)
        users_with_tasks = len(user_task_counts)
        
        # Get recent tasks (last 5)
        recent_tasks = Task.query.order_by(Task.id.desc()).limit(5).all()
        recent_tasks_data = [{'id': t.id, 'title': t.title, 'user_id': t.user_id} for t in recent_tasks]
        
        # Try to get user information
        user_service_stats = {'total_users': 0, 'error': None}
        try:
            users_response = requests.get('http://localhost:5001/users', timeout=2)
            if users_response.status_code == 200:
                users_data = users_response.json()
                user_service_stats['total_users'] = len(users_data)
        except Exception as e:
            user_service_stats['error'] = f'User service unavailable: {str(e)}'
        
        # Calculate productivity metrics
        productivity_metrics = {}
        if user_service_stats['total_users'] > 0 and total_tasks > 0:
            productivity_metrics['avg_tasks_per_user'] = round(total_tasks / user_service_stats['total_users'], 2)
        else:
            productivity_metrics['avg_tasks_per_user'] = 0
        
        if users_with_tasks > 0:
            productivity_metrics['avg_tasks_per_active_user'] = round(total_tasks / users_with_tasks, 2)
        else:
            productivity_metrics['avg_tasks_per_active_user'] = 0
        
        # Most productive users (top 3)
        top_users = []
        for user_id, task_count in user_task_counts.most_common(3):
            top_users.append({'user_id': user_id, 'task_count': task_count})
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'tasks': {
                'total_tasks': total_tasks,
                'users_with_tasks': users_with_tasks,
                'recent_tasks': recent_tasks_data,
                'top_productive_users': top_users
            },
            'users': user_service_stats,
            'productivity_metrics': productivity_metrics,
            'system': {
                'status': 'healthy' if user_service_stats['error'] is None else 'partial',
                'services': {
                    'task_service': 'online',
                    'user_service': 'online' if user_service_stats['error'] is None else 'offline'
                }
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get task statistics: {str(e)}'}), 500

if __name__ == '__main__':
    with service_b.app_context():
        db.create_all()
    service_b.run(port=5002)
