# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import threading
import time
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'drishti-secret-key'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global data storage (simulating database)
zones_data = {}
agents_status = {
    "camera_surveillance": {"status": "active", "last_update": None},
    "crowd_analytics": {"status": "active", "last_update": None},
    "command_coordination": {"status": "active", "last_update": None},
    "emergency_response": {"status": "standby", "last_update": None},
    "missing_person": {"status": "standby", "last_update": None},
    "drone_control": {"status": "active", "last_update": None}
}

# Initialize zones
def initialize_zones():
    global zones_data
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    for i, row in enumerate(rows):
        for col in range(1, 9):
            zone_id = f"{row}{col}"
            zones_data[zone_id] = {
                "zone_id": zone_id,
                "people_count": random.randint(0, 100),
                "threat_level": get_threat_level(random.randint(0, 100)),
                "confidence": round(random.uniform(0.8, 0.98), 2),
                "timestamp": datetime.now().isoformat(),
                "predictions": {
                    "15_min": random.randint(0, 120),
                    "20_min": random.randint(0, 130)
                },
                "agent_reports": {
                    "camera": f"Zone {zone_id} monitored - {random.randint(0, 100)} people detected",
                    "analytics": f"Flow prediction: {random.choice(['stable', 'increasing', 'decreasing'])}"
                }
            }

def get_threat_level(people_count):
    if people_count < 25: return "low"
    elif people_count < 50: return "medium"
    elif people_count < 75: return "high"
    else: return "critical"

# REST API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "drishti-backend", "agents": 6})

@app.route('/api/zones', methods=['GET'])
def get_all_zones():
    return jsonify(zones_data)

@app.route('/api/zones/<zone_id>', methods=['GET'])
def get_zone(zone_id):
    if zone_id in zones_data:
        return jsonify(zones_data[zone_id])
    return jsonify({"error": "Zone not found"}), 404

@app.route('/api/agents', methods=['GET'])
def get_agents_status():
    return jsonify(agents_status)

@app.route('/api/command', methods=['POST'])
def process_command():
    data = request.get_json()
    command = data.get('command', '')
    
    # Simulate AI command processing
    response = process_voice_command(command)
    
    # Emit to all connected clients
    socketio.emit('command_processed', response)
    
    return jsonify(response)

def process_voice_command(command):
    """Simulate AI processing of voice commands"""
    command_lower = command.lower()
    
    if "move" in command_lower and "to" in command_lower:
        # Extract zone from command (simple parsing)
        zones = ['a1', 'a2', 'b1', 'c6', 'd4', 'e4', 'f6', 'g2', 'h8']
        target_zone = None
        for zone in zones:
            if zone in command_lower:
                target_zone = zone.upper()
                break
        
        if not target_zone:
            target_zone = "C6"  # Default
            
        return {
            "type": "movement_command",
            "original_command": command,
            "parsed_action": "move_team",
            "target_zone": target_zone,
            "team": "Alpha",
            "eta_minutes": random.randint(2, 8),
            "agent_response": f"Command confirmed: Moving Alpha team to zone {target_zone}. ETA {random.randint(2, 8)} minutes.",
            "timestamp": datetime.now().isoformat()
        }
    
    elif "status" in command_lower:
        critical_zones = [k for k, v in zones_data.items() if v['threat_level'] == 'critical']
        return {
            "type": "status_report",
            "original_command": command,
            "critical_zones": critical_zones[:3],
            "total_people": sum(zone['people_count'] for zone in zones_data.values()),
            "agent_response": f"Status report: {len(critical_zones)} critical zones detected. Total crowd: {sum(zone['people_count'] for zone in zones_data.values())} people.",
            "timestamp": datetime.now().isoformat()
        }
    
    else:
        return {
            "type": "general_response",
            "original_command": command,
            "agent_response": "Command received. Available commands: 'Move team to [zone]', 'Status report', 'Emergency evacuation'.",
            "timestamp": datetime.now().isoformat()
        }

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('zones_update', zones_data)
    emit('agents_status', agents_status)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_prediction')
def handle_prediction_request(data):
    zone_id = data.get('zone_id')
    if zone_id in zones_data:
        prediction = generate_zone_prediction(zone_id)
        emit('prediction_response', prediction)

def generate_zone_prediction(zone_id):
    """Generate AI prediction for a zone"""
    current_count = zones_data[zone_id]['people_count']
    
    # Simulate crowd flow prediction
    predictions = []
    for i in range(1, 21):  # Next 20 minutes
        trend = random.uniform(-0.1, 0.2)  # Slight upward trend
        noise = random.uniform(-0.05, 0.05)
        predicted_count = max(0, int(current_count * (1 + trend + noise)))
        
        predictions.append({
            "time_offset": i,
            "predicted_count": predicted_count,
            "confidence": max(0.6, 1 - (i * 0.02))
        })
    
    return {
        "zone_id": zone_id,
        "current_count": current_count,
        "predictions": predictions,
        "risk_assessment": "high" if current_count > 70 else "medium" if current_count > 40 else "low",
        "recommendation": f"Monitor zone {zone_id} closely" if current_count > 70 else "Normal monitoring",
        "timestamp": datetime.now().isoformat()
    }

# Background task to simulate real-time updates
def background_updates():
    """Simulate AI agents updating data in real-time"""
    while True:
        time.sleep(5)  # Update every 5 seconds
        
        # Randomly update 3-5 zones
        zones_to_update = random.sample(list(zones_data.keys()), random.randint(3, 5))
        
        for zone_id in zones_to_update:
            # Simulate crowd movement
            current_count = zones_data[zone_id]['people_count']
            change = random.randint(-10, 15)
            new_count = max(0, min(150, current_count + change))
            
            zones_data[zone_id].update({
                "people_count": new_count,
                "threat_level": get_threat_level(new_count),
                "confidence": round(random.uniform(0.85, 0.98), 2),
                "timestamp": datetime.now().isoformat(),
                "predictions": {
                    "15_min": new_count + random.randint(-20, 30),
                    "20_min": new_count + random.randint(-25, 35)
                }
            })
        
        # Update agent status
        for agent in agents_status:
            agents_status[agent]["last_update"] = datetime.now().isoformat()
        
        # Emit updates to all connected clients
        socketio.emit('zones_update', zones_data)
        socketio.emit('agents_status', agents_status)

if __name__ == '__main__':
    initialize_zones()
    
    # Start background updates in a separate thread
    update_thread = threading.Thread(target=background_updates)
    update_thread.daemon = True
    update_thread.start()
    
    print("🚀 Drishti Backend Server Starting...")
    print("📊 Dashboard: http://localhost:3000")
    print("🔗 API: http://localhost:4000")
    print("🤖 6 AI Agents Simulated")
    print("\n💡 NEXT STEPS:")
    print("1. Keep this terminal running")
    print("2. Open new terminal for frontend")
    print("3. Test API: http://localhost:4000/api/health")
    
    socketio.run(app, host='0.0.0.0', port=4000, debug=True)