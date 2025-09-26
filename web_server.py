from flask import Flask, request, jsonify
import threading
import time
import logging
from typing import Optional
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Define all web routes for the server."""
        
        @self.app.route('/')
        def home():
            """Health check endpoint."""
            return jsonify({
                'status': 'online',
                'service': 'file_renamer_bot',
                'timestamp': time.time()
            })
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time()
            })
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get bot statistics (placeholder - implement as needed)."""
            return jsonify({
                'status': 'running',
                'uptime': 'N/A',  # You can implement uptime tracking
                'users_served': 0,  # Implement your own metrics
                'files_processed': 0,
                'timestamp': time.time()
            })
        
        @self.app.route('/webhook', methods=['POST'])
        def webhook_handler():
            """Webhook endpoint for external services."""
            try:
                data = request.get_json()
                logger.info(f"Received webhook data: {data}")
                
                # Process webhook data here
                # You can add your webhook processing logic
                
                return jsonify({'status': 'webhook received'}), 200
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return jsonify({'error': 'Invalid webhook data'}), 400
        
        @self.app.route('/restart', methods=['POST'])
        def restart_bot():
            """Endpoint to gracefully restart the bot (admin only)."""
            # Add authentication here if needed
            auth_token = request.headers.get('Authorization')
            
            # Simple token check - enhance for production
            if auth_token != 'your-secret-token':  # Change this!
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Implement restart logic here
            logger.info("Restart endpoint called")
            return jsonify({'status': 'restart initiated'}), 200
    
    def start(self, daemon: bool = True):
        """Start the web server in a separate thread."""
        def run_server():
            try:
                logger.info(f"Starting web server on {self.host}:{self.port}")
                self.is_running = True
                self.app.run(
                    host=self.host,
                    port=self.port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                logger.error(f"Web server error: {e}")
                self.is_running = False
        
        self.server_thread = threading.Thread(target=run_server, daemon=daemon)
        self.server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(1)
        return self.is_running
    
    def stop(self):
        """Stop the web server."""
        # Flask development server doesn't have a clean shutdown
        # In production, consider using Waitress or Gunicorn instead
        logger.info("Stopping web server")
        self.is_running = False
        # Note: This won't stop the Flask dev server gracefully
        # For production, you'd need a proper WSGI server

# Singleton instance
web_server = WebServer()

def start_web_server():
    """Convenience function to start the web server."""
    return web_server.start()

def stop_web_server():
    """Convenience function to stop the web server."""
    web_server.stop()

# For standalone execution
if __name__ == '__main__':
    logger.info("Starting web server in standalone mode...")
    server = WebServer()
    
    try:
        # Run in main thread (blocking)
        server.app.run(
            host=server.host,
            port=server.port,
            debug=True
        )
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
