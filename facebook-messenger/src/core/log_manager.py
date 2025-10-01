#!/usr/bin/env python3
"""
Log Manager - Redirects stdout/stderr to dated log files
File: src/core/log_manager.py
FIXED VERSION with better error handling and debugging
"""

import os
import sys
import datetime
import glob
from pathlib import Path
from typing import Optional, TextIO


class TeeOutput:
    """
    Tee class that writes to both original output and log file
    """
    def __init__(self, original_stream: TextIO, log_file: TextIO):
        self.original = original_stream
        self.log_file = log_file
    
    def write(self, data: str):
        """Write to both streams"""
        self.original.write(data)
        self.original.flush()
        try:
            self.log_file.write(data)
            self.log_file.flush()
        except Exception as e:
            # If log file write fails, at least show in console
            self.original.write(f"[LogManager] Error writing to log file: {e}\n")
            self.original.flush()
    
    def flush(self):
        """Flush both streams"""
        self.original.flush()
        try:
            self.log_file.flush()
        except Exception:
            pass  # Ignore flush errors
    
    def __getattr__(self, name):
        """Delegate other attributes to original stream"""
        return getattr(self.original, name)


class LogManager:
    """
    Manages command line output logging with incremental daily filenames
    FIXED VERSION with better error handling
    """
    
    def __init__(self, logs_dir: str = None):
        # Auto-detect logs directory based on environment
        if logs_dir is None:
            # Try different locations in order of preference
            possible_dirs = [
                "/app/logs",                    # Container environment
                "logs",                         # Local development
                os.path.join(os.getcwd(), "logs"),  # Explicit current directory
                os.path.expanduser("~/logs"),   # User home directory
                "/tmp/logs"                     # Fallback to temp
            ]
            
            self.logs_dir = None
            for dir_path in possible_dirs:
                try:
                    # Try to create directory
                    os.makedirs(dir_path, exist_ok=True)
                    
                    # Test write permissions
                    test_file = os.path.join(dir_path, "test_write.tmp")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    
                    # If we get here, this directory works
                    self.logs_dir = dir_path
                    print(f"[LogManager] Using logs directory: {self.logs_dir}")
                    break
                    
                except Exception as e:
                    print(f"[LogManager] Cannot use {dir_path}: {e}")
                    continue
            
            if self.logs_dir is None:
                print("[LogManager] ERROR: No writable logs directory found!")
                # Use current directory as last resort
                self.logs_dir = os.getcwd()
        else:
            self.logs_dir = logs_dir
        
        # Ensure logs directory exists and is writable
        try:
            Path(self.logs_dir).mkdir(parents=True, exist_ok=True)
            print(f"[LogManager] Logs directory confirmed: {self.logs_dir}")
        except Exception as e:
            print(f"[LogManager] ERROR creating logs directory {self.logs_dir}: {e}")
        
        self.log_file = None
        self.original_stdout = None
        self.original_stderr = None
    
    def get_next_log_filename(self) -> str:
        """
        Generate the next incremental log filename for today
        Format: {increment}_{dd.mm.yy}
        Example: 1_11.07.25, 2_11.07.25, etc.
        """
        # Get today's date in dd.mm.yy format
        today = datetime.date.today()
        date_str = today.strftime("%d.%m.%y")
        
        # Find existing log files for today
        pattern = os.path.join(self.logs_dir, f"*_{date_str}.log")
        try:
            existing_files = glob.glob(pattern)
        except Exception as e:
            print(f"[LogManager] Error finding existing logs: {e}")
            existing_files = []
        
        # Extract increment numbers from existing files
        increments = []
        for file_path in existing_files:
            filename = os.path.basename(file_path)
            try:
                # Extract increment from filename like "1_11.07.25.log"
                increment_str = filename.split('_')[0]
                increments.append(int(increment_str))
            except (ValueError, IndexError):
                continue
        
        # Get next increment number
        next_increment = max(increments) + 1 if increments else 1
        
        # Generate filename
        filename = f"{next_increment}_{date_str}.log"
        return os.path.join(self.logs_dir, filename)
    
    def start_logging(self) -> str:
        """
        Start redirecting stdout and stderr to log file
        Returns the log filename
        """
        if self.log_file is not None:
            print("[LogManager] Warning: Logging already started")
            return self.log_file.name
        
        # Generate log filename
        log_filepath = self.get_next_log_filename()
        
        print(f"[LogManager] Attempting to create log file: {log_filepath}")
        
        # Open log file with error handling
        try:
            self.log_file = open(log_filepath, 'w', encoding='utf-8')
            print(f"[LogManager] ✅ Log file created successfully: {log_filepath}")
        except Exception as e:
            print(f"[LogManager] ❌ ERROR: Could not create log file {log_filepath}: {e}")
            print(f"[LogManager] Directory permissions for {self.logs_dir}:")
            try:
                import stat
                dir_stat = os.stat(self.logs_dir)
                print(f"   Directory exists: {os.path.exists(self.logs_dir)}")
                print(f"   Directory writable: {os.access(self.logs_dir, os.W_OK)}")
                print(f"   Directory permissions: {oct(dir_stat.st_mode)}")
            except Exception as perm_e:
                print(f"   Could not check permissions: {perm_e}")
            
            # Continue without logging to file
            print("[LogManager] ⚠️ Continuing without file logging")
            return "ERROR: Could not create log file"
        
        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Create tee outputs that write to both console and log
        sys.stdout = TeeOutput(self.original_stdout, self.log_file)
        sys.stderr = TeeOutput(self.original_stderr, self.log_file)
        
        # Write header to log file
        header = f"""
{'='*80}
Facebook Camera Scraper - Session Log
Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Log File: {os.path.basename(log_filepath)}
Logs Directory: {self.logs_dir}
Current Working Directory: {os.getcwd()}
User: {os.getenv('USER', 'unknown')}
{'='*80}

"""
        print(header)
        
        print(f"[LogManager] ✅ Started logging to: {log_filepath}")
        return log_filepath
    
    def stop_logging(self):
        """
        Stop logging and restore original stdout/stderr
        """
        if self.log_file is None:
            return
        
        # Write footer
        footer = f"""

{'='*80}
Session completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Log saved to: {os.path.basename(self.log_file.name)}
{'='*80}
"""
        print(footer)
        
        # Restore original streams
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # Close log file
        log_filename = self.log_file.name
        try:
            self.log_file.close()
            print(f"[LogManager] ✅ Stopped logging. Log saved to: {log_filename}")
        except Exception as e:
            print(f"[LogManager] ⚠️ Error closing log file: {e}")
        
        self.log_file = None
    
    def __enter__(self):
        """Context manager entry"""
        return self.start_logging()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_logging()
    
    def get_today_logs(self) -> list:
        """Get all log files from today"""
        try:
            today = datetime.date.today()
            date_str = today.strftime("%d.%m.%y")
            pattern = os.path.join(self.logs_dir, f"*_{date_str}.log")
            return sorted(glob.glob(pattern))
        except Exception as e:
            print(f"[LogManager] Error getting today's logs: {e}")
            return []
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove log files older than specified days"""
        try:
            cutoff_date = datetime.date.today() - datetime.timedelta(days=days_to_keep)
            
            removed_count = 0
            pattern = os.path.join(self.logs_dir, "*_*.log")
            
            for log_file in glob.glob(pattern):
                try:
                    # Extract date from filename
                    filename = os.path.basename(log_file)
                    if '_' in filename and filename.endswith('.log'):
                        date_part = filename.split('_')[1].replace('.log', '')
                        
                        # Parse date (dd.mm.yy format)
                        try:
                            file_date = datetime.datetime.strptime(date_part, "%d.%m.%y").date()
                            
                            if file_date < cutoff_date:
                                os.remove(log_file)
                                removed_count += 1
                                print(f"[LogManager] Removed old log: {filename}")
                        except ValueError:
                            # Skip files that don't match our date format
                            continue
                            
                except (OSError) as e:
                    print(f"[LogManager] Error processing {log_file}: {e}")
            
            if removed_count > 0:
                print(f"[LogManager] Cleaned up {removed_count} old log files")
        except Exception as e:
            print(f"[LogManager] Error during cleanup: {e}")


# Global instance for easy access
log_manager = LogManager()


def setup_logging(logs_dir: str = None) -> str:
    """
    Convenience function to start logging
    Returns the log filename
    """
    global log_manager
    if logs_dir:
        log_manager = LogManager(logs_dir)
    return log_manager.start_logging()


def stop_logging():
    """Convenience function to stop logging"""
    global log_manager
    log_manager.stop_logging()


# Example usage and test
if __name__ == "__main__":
    # Test the logging functionality
    print("🧪 Testing Log Manager...")
    
    with LogManager() as log_file:
        print("This is a test message that should appear in both console and log file")
        print("Testing multiple lines...")
        print("With different types of output")
        
        # Test error output
        print("This is an error message", file=sys.stderr)
        
        # Test some formatting
        print("\n" + "="*50)
        print("FORMATTED SECTION")
        print("="*50)
        print("Content here...")
        
        print(f"Log file created: {log_file}")
    
    print("✅ Logging test completed")