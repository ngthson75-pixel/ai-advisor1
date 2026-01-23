#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLEANUP API ENDPOINT - For automated cleanup via webhook/cron

Add this to your backend_api.py or admin_api.py

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from signal_cleanup import SignalCleanupManager

cleanup_bp = Blueprint('cleanup', __name__)


@cleanup_bp.route('/api/cleanup/signals', methods=['POST'])
def cleanup_signals_endpoint():
    """
    Automated cleanup endpoint
    
    Can be called by:
    - Cron job
    - External monitoring service (UptimeRobot, etc.)
    - Manual trigger
    
    POST /api/cleanup/signals
    
    Optional JSON body:
    {
        "aggressive": true,      // Use 3-day retention instead of 7-day
        "dry_run": false,        // If true, only preview changes
        "secret": "your_secret"  // Optional security token
    }
    """
    
    # Optional: Add authentication
    data = request.json or {}
    secret = data.get('secret')
    
    # Check secret if configured
    import os
    expected_secret = os.getenv('CLEANUP_SECRET')
    if expected_secret and secret != expected_secret:
        return jsonify({
            'success': False,
            'error': 'Invalid secret'
        }), 401
    
    # Get parameters
    aggressive = data.get('aggressive', False)
    dry_run = data.get('dry_run', False)
    
    # Run cleanup
    try:
        manager = SignalCleanupManager(dry_run=dry_run)
        
        deleted = manager.full_cleanup(aggressive=aggressive)
        stats = manager.get_stats()
        
        manager.close()
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'remaining': stats['total'],
            'by_state': stats['by_state'],
            'dry_run': dry_run,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cleanup_bp.route('/api/cleanup/stats', methods=['GET'])
def cleanup_stats():
    """
    Get database statistics
    
    GET /api/cleanup/stats
    """
    try:
        manager = SignalCleanupManager()
        stats = manager.get_stats()
        manager.close()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# INTEGRATION INSTRUCTIONS
# ============================================================================

"""
To integrate into your backend_api.py or admin_api.py:

1. Add this import at the top:
   from cleanup_endpoints import cleanup_bp

2. Register the blueprint:
   app.register_blueprint(cleanup_bp)

3. Set environment variable (optional):
   CLEANUP_SECRET=your_random_secret_here

4. Test endpoints:
   # Get stats
   curl https://ai-advisor1-backend.onrender.com/api/cleanup/stats
   
   # Dry run cleanup
   curl -X POST https://ai-advisor1-backend.onrender.com/api/cleanup/signals \
     -H "Content-Type: application/json" \
     -d '{"dry_run": true}'
   
   # Real cleanup
   curl -X POST https://ai-advisor1-backend.onrender.com/api/cleanup/signals \
     -H "Content-Type: application/json" \
     -d '{"secret": "your_secret"}'
   
   # Aggressive cleanup
   curl -X POST https://ai-advisor1-backend.onrender.com/api/cleanup/signals \
     -H "Content-Type: application/json" \
     -d '{"aggressive": true, "secret": "your_secret"}'

5. Setup automated trigger with UptimeRobot or similar:
   - Create a monitor
   - URL: https://ai-advisor1-backend.onrender.com/api/cleanup/signals
   - Method: POST
   - Interval: Daily
   - Body: {"secret": "your_secret"}
"""
