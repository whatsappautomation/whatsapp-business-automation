from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import json
import requests
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Business configurations - each business can customize these
BUSINESS_CONFIGS = {}

class WhatsAppAutomation:
    def __init__(self, business_id):
        self.business_id = business_id
        self.config = BUSINESS_CONFIGS.get(business_id, {})
        self.conversation_history = {}
        
    def process_message(self, message, phone_number):
        """Process incoming WhatsApp message and generate appropriate response"""
        
        # Store conversation
        if phone_number not in self.conversation_history:
            self.conversation_history[phone_number] = []
        
        self.conversation_history[phone_number].append({
            'timestamp': datetime.now(),
            'message': message,
            'type': 'incoming'
        })
        
        # Check for keywords and generate response
        response = self.generate_response(message, phone_number)
        
        # Store response
        self.conversation_history[phone_number].append({
            'timestamp': datetime.now(),
            'message': response,
            'type': 'outgoing'
        })
        
        return response
    
    def generate_response(self, message, phone_number):
        """Generate automated response based on message content and business rules"""
        
        message_lower = message.lower()
        
        # Check for order inquiries
        if any(word in message_lower for word in ['order', 'booking', 'appointment', 'reservation']):
            return self.config.get('order_response', 
                "Thank you for your inquiry! Please provide your preferred date and time, and we'll get back to you within 2 hours.")
        
        # Check for pricing
        if any(word in message_lower for word in ['price', 'cost', 'rate', 'charge', 'fee']):
            return self.config.get('pricing_response', 
                "Our current rates are available on our website. Would you like me to send you our price list?")
        
        # Check for business hours
        if any(word in message_lower for word in ['hours', 'open', 'close', 'time']):
            return self.config.get('hours_response', 
                "We're open Monday-Friday 9 AM-6 PM, Saturday 10 AM-4 PM. We're closed on Sundays.")
        
        # Check for location
        if any(word in message_lower for word in ['where', 'location', 'address', 'place']):
            return self.config.get('location_response', 
                "We're located at [Your Business Address]. Would you like directions?")
        
        # Check for contact
        if any(word in message_lower for word in ['contact', 'call', 'phone', 'email']):
            return self.config.get('contact_response', 
                "You can reach us at [Phone Number] or email us at [Email]. We typically respond within 2 hours.")
        
        # Default response
        return self.config.get('default_response', 
            "Thank you for your message! A team member will get back to you shortly. In the meantime, is there anything specific I can help you with?")
    
    def get_analytics(self):
        """Get basic analytics for the business"""
        total_conversations = len(self.conversation_history)
        total_messages = sum(len(conv) for conv in self.conversation_history.values())
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'active_customers': len([conv for conv in self.conversation_history.values() if conv and (datetime.now() - conv[-1]['timestamp']).days < 7])
        }

@app.route('/')
def index():
    if 'business_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        business_name = request.form.get('business_name')
        phone = request.form.get('phone')
        
        # Create new business account
        business_id = str(uuid.uuid4())
        BUSINESS_CONFIGS[business_id] = {
            'business_name': business_name,
            'phone': phone,
            'order_response': "Thank you for your inquiry! Please provide your preferred date and time, and we'll get back to you within 2 hours.",
            'pricing_response': "Our current rates are available on our website. Would you like me to send you our price list?",
            'hours_response': "We're open Monday-Friday 9 AM-6 PM, Saturday 10 AM-4 PM. We're closed on Sundays.",
            'location_response': "We're located at [Your Business Address]. Would you like directions?",
            'contact_response': "You can reach us at [Phone Number] or email us at [Email]. We typically respond within 2 hours.",
            'default_response': "Thank you for your message! A team member will get back to you shortly. In the meantime, is there anything specific I can help you with?"
        }
        
        session['business_id'] = business_id
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'business_id' not in session:
        return redirect(url_for('login'))
    
    business_id = session['business_id']
    automation = WhatsAppAutomation(business_id)
    analytics = automation.get_analytics()
    config = BUSINESS_CONFIGS.get(business_id, {})
    
    return render_template('dashboard.html', 
                         business_name=config.get('business_name', 'Your Business'),
                         analytics=analytics,
                         config=config)

@app.route('/customize', methods=['GET', 'POST'])
def customize():
    if 'business_id' not in session:
        return redirect(url_for('login'))
    
    business_id = session['business_id']
    
    if request.method == 'POST':
        # Update business configuration
        BUSINESS_CONFIGS[business_id].update({
            'order_response': request.form.get('order_response'),
            'pricing_response': request.form.get('pricing_response'),
            'hours_response': request.form.get('hours_response'),
            'location_response': request.form.get('location_response'),
            'contact_response': request.form.get('contact_response'),
            'default_response': request.form.get('default_response')
        })
        return redirect(url_for('dashboard'))
    
    config = BUSINESS_CONFIGS.get(business_id, {})
    return render_template('customize.html', config=config)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for WhatsApp messages (simulated for demo)"""
    if 'business_id' not in session:
        return jsonify({'error': 'No business session'}), 400
    
    business_id = session['business_id']
    automation = WhatsAppAutomation(business_id)
    
    # Simulate incoming message
    data = request.get_json()
    message = data.get('message', '')
    phone_number = data.get('phone_number', '')
    
    if message and phone_number:
        response = automation.process_message(message, phone_number)
        return jsonify({
            'response': response,
            'business_id': business_id
        })
    
    return jsonify({'error': 'Invalid message data'}), 400

@app.route('/test_message', methods=['POST'])
def test_message():
    """Test endpoint to simulate message processing"""
    if 'business_id' not in session:
        return jsonify({'error': 'No business session'}), 400
    
    business_id = session['business_id']
    automation = WhatsAppAutomation(business_id)
    
    message = request.form.get('message', '')
    phone_number = request.form.get('phone_number', 'demo')
    
    if message:
        response = automation.process_message(message, phone_number)
        return jsonify({
            'response': response,
            'business_id': business_id
        })
    
    return jsonify({'error': 'No message provided'}), 400

@app.route('/logout')
def logout():
    session.pop('business_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 