# facebook-messenger/src/api/server.py
"""
Simple Flask API for receiving camera match leads
"""

import os
from flask import Flask, request, jsonify
from .repository import LeadRepository

app = Flask(__name__)
repo = LeadRepository()

# Optional auth - can disable if on private network
AUTH_ENABLED = os.getenv("API_AUTH_ENABLED", "false").lower() == "true"
AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")


def check_auth():
    """Simple token auth - optional for private networks"""
    if not AUTH_ENABLED:
        return True
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return token == AUTH_TOKEN


def print_matches(leads):
    """Pretty print received matches for testing"""
    print("\n" + "="*80)
    print(f"🎯 RECEIVED {len(leads)} CAMERA MATCHES FROM SCRAPER")
    print("="*80)
    
    for i, lead in enumerate(leads, 1):
        price_str = f"£{lead.get('price'):.0f}" if lead.get('price') else "Price unknown"
        savings_str = f" (save £{lead.get('savings', 0):.0f})" if lead.get('savings', 0) > 0 else ""
        
        print(f"\n{i}. {lead['camera_name']}")
        print(f"   💰 {price_str}{savings_str}")
        print(f"   📊 {lead['confidence']:.0%} confidence")
        print(f"   📝 {lead['title'][:60]}...")
        print(f"   🔗 {lead['url']}")
    
    print("\n" + "="*80 + "\n")


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/leads", methods=["POST"])
def create_lead():
    """Create single lead (legacy endpoint)"""
    if not check_auth():
        return {"error": "unauthorized"}, 401
    
    data = request.json
    required = ["session_id", "camera_id", "camera_name", "url", "title", "confidence"]
    if not all(k in data for k in required):
        return {"error": "missing required fields"}, 400
    
    # Print single match
    print("\n" + "="*80)
    print(f"🎯 RECEIVED SINGLE MATCH: {data['camera_name']}")
    print("="*80)
    print(f"💰 Price: £{data.get('price', 0):.0f}")
    print(f"📊 Confidence: {data['confidence']:.0%}")
    print(f"🔗 URL: {data['url']}")
    print("="*80 + "\n")
    
    order_id = repo.create(data)
    if order_id is None:
        return {"status": "duplicate"}, 200
    
    return {"status": "created", "order_id": order_id}, 201


@app.route("/leads/batch", methods=["POST"])
def create_batch():
    """Create multiple leads in one request"""
    if not check_auth():
        return {"error": "unauthorized"}, 401
    
    data = request.json
    if not data or "leads" not in data:
        return {"error": "leads array required"}, 400
    
    leads = data["leads"]
    if not isinstance(leads, list) or not leads:
        return {"error": "leads must be non-empty array"}, 400
    
    # Validate all leads have required fields
    required = ["session_id", "camera_id", "camera_name", "url", "title", "confidence"]
    for lead in leads:
        if not all(k in lead for k in required):
            return {"error": "missing required fields in one or more leads"}, 400
    
    # PRINT MATCHES FOR TESTING
    print_matches(leads)
    
    # Save to database
    result = repo.create_batch(leads)
    
    # Print summary
    print(f"✅ Saved to database: {result['created']} created, {result['duplicates']} duplicates\n")
    
    return {
        "status": "completed",
        "created": result["created"],
        "duplicates": result["duplicates"],
        "total": len(leads)
    }, 201


@app.route("/leads")
def get_leads():
    """Get pending leads"""
    if not check_auth():
        return {"error": "unauthorized"}, 401
    
    limit = request.args.get("limit", 10, type=int)
    leads = repo.get_pending(limit)
    return {"leads": leads}


@app.route("/leads/<int:order_id>/status", methods=["PUT"])
def update_status(order_id):
    """Update lead status"""
    if not check_auth():
        return {"error": "unauthorized"}, 401
    
    status = request.json.get("status")
    if not status:
        return {"error": "status required"}, 400
    
    success = repo.update_status(order_id, status)
    return {"updated": success}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)