# profiling/performance_profiler.py
import cProfile
import pstats
import io
import time
import functools
import threading
from memory_profiler import profile as memory_profile
import logging
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """
    Performance tracking tools for GestureDrive.
    Provides CPU profiling, timing analysis, and memory usage tracking.
    """
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.timing_data = {}
        self.lock = threading.Lock()
        
    def cpu_profile(self, output_file=None):
        """
        Decorator for CPU profiling a function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                    
                # Create profiler
                profiler = cProfile.Profile()
                profiler.enable()
                
                # Run the function
                result = func(*args, **kwargs)
                
                # Disable profiler and print stats
                profiler.disable()
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                ps.print_stats(20)  # Print top 20 time-consuming functions
                
                # Output to file or log
                if output_file:
                    ps.dump_stats(output_file)
                
                logger.debug(f"PROFILE: {func.__name__}\n{s.getvalue()}")
                return result
            return wrapper
        return decorator
    
    def time_it(self, category=None):
        """
        Decorator to time a function and collect statistics
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                # Store the execution time
                category_name = category or func.__name__
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Update timing statistics thread-safely
                with self.lock:
                    if category_name not in self.timing_data:
                        self.timing_data[category_name] = {
                            'count': 0,
                            'total_time': 0,
                            'min_time': float('inf'),
                            'max_time': 0,
                            'times': []
                        }
                    
                    stats = self.timing_data[category_name]
                    stats['count'] += 1
                    stats['total_time'] += execution_time
                    stats['min_time'] = min(stats['min_time'], execution_time)
                    stats['max_time'] = max(stats['max_time'], execution_time)
                    stats['times'].append(execution_time)
                    
                    # Keep only the last 1000 measurements to avoid memory growth
                    if len(stats['times']) > 1000:
                        stats['times'] = stats['times'][-1000:]
                
                return result
            return wrapper
        return decorator
    
    def get_timing_stats(self, category=None):
        """Get timing statistics for a category or all categories"""
        with self.lock:
            if category:
                if category not in self.timing_data:
                    return None
                    
                stats = self.timing_data[category].copy()
                times = stats['times']
                if times:
                    stats['avg_time'] = stats['total_time'] / stats['count']
                    stats['median_time'] = np.median(times)
                    stats['std_dev'] = np.std(times)
                    stats['percentile_95'] = np.percentile(times, 95)
                return stats
            else:
                # Return stats for all categories
                result = {}
                for cat, data in self.timing_data.items():
                    stats = data.copy()
                    times = stats['times']
                    if times:
                        stats['avg_time'] = stats['total_time'] / stats['count']
                        stats['median_time'] = np.median(times)
                        stats['std_dev'] = np.std(times)
                        stats['percentile_95'] = np.percentile(times, 95)
                    result[cat] = stats
                return result
    
    def reset_stats(self, category=None):
        """Reset timing statistics for a category or all categories"""
        with self.lock:
            if category:
                if category in self.timing_data:
                    self.timing_data[category] = {
                        'count': 0,
                        'total_time': 0,
                        'min_time': float('inf'),
                        'max_time': 0,
                        'times': []
                    }
            else:
                self.timing_data = {}
    
    @staticmethod
    def memory_profile(func):
        """Decorator to profile memory usage of a function"""
        return memory_profile(func)


# Create global instance
performance_tracker = PerformanceTracker()