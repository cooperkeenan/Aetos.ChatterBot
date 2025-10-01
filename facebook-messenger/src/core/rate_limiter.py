"""Rate limiting functionality to avoid detection."""
import os
import time
import datetime

# Constants for persistent storage
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
REQUEST_LOG = os.path.join(LOG_DIR, "request_log.txt")

class RateLimiter:
    """Controls request frequency to avoid detection."""
    def __init__(self, max_requests_per_day=50, log_file=REQUEST_LOG):
        self.max_requests = max_requests_per_day
        self.request_timestamps = []
        self.log_file = log_file
        self._load_history()
    
    def _load_history(self):
        """Load previous request timestamps if available."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    for line in f:
                        try:
                            timestamp = float(line.strip())
                            self.request_timestamps.append(timestamp)
                        except:
                            pass
                
                # Clean up old entries (older than 24 hours)
                cutoff = time.time() - (24 * 60 * 60)
                self.request_timestamps = [t for t in self.request_timestamps if t > cutoff]
                print(f"[Debug] Loaded {len(self.request_timestamps)} recent requests from history")
        except Exception as e:
            print(f"[Warning] Could not load request history: {e}")
    
    def can_make_request(self):
        """Check if we can make another request within limits."""
        # Clean up old entries
        cutoff = time.time() - (24 * 60 * 60) 
        self.request_timestamps = [t for t in self.request_timestamps if t > cutoff]
        
        # Check if we're under the limit
        if len(self.request_timestamps) < self.max_requests:
            return True
        else:
            print(f"[Warning] Rate limit reached: {len(self.request_timestamps)} requests in last 24h")
            # Calculate time until next slot available
            oldest = min(self.request_timestamps)
            wait_seconds = (oldest + 24*60*60) - time.time()
            readable_time = str(datetime.timedelta(seconds=int(wait_seconds)))
            print(f"[Info] Next request available in: {readable_time}")
            return False
    
    def record_request(self):
        """Record that we made a request."""
        timestamp = time.time()
        self.request_timestamps.append(timestamp)
        
        # Also save to file
        try:
            with open(self.log_file, "a") as f:
                f.write(f"{timestamp}\n")
        except Exception as e:
            print(f"[Warning] Could not save request timestamp: {e}")