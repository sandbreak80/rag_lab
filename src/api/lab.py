"""
Lab API routes
"""
from flask import Blueprint, request, jsonify
import json
import os

bp = Blueprint('lab', __name__)

# In-memory storage for lab progress (in production, use a database)
PROGRESS_FILE = '/tmp/lab_progress.json'

def load_progress():
    """Load lab progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_progress(progress):
    """Save lab progress to file"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f)
    except:
        pass

@bp.route('/lab/progress', methods=['GET'])
def get_progress():
    """Get lab progress"""
    try:
        progress = load_progress()
        return jsonify({'progress': progress})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/lab/progress', methods=['POST'])
def update_progress():
    """Update lab progress"""
    try:
        data = request.json
        exercise_id = data.get('exercise_id')
        completed = data.get('completed', False)
        
        if not exercise_id:
            return jsonify({'error': 'exercise_id is required'}), 400
        
        progress = load_progress()
        progress[exercise_id] = completed
        save_progress(progress)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback"""
    try:
        data = request.json
        
        # Validate required fields
        rating = data.get('rating')
        if rating is None:
            return jsonify({'error': 'Rating is required'}), 400
        
        # In production, save to database
        # For now, just log it
        print(f"📝 Feedback received: {data}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
