"""
Latency logging and monitoring utilities
"""

import logging
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional
import statistics

logger = logging.getLogger(__name__)


class LatencyLogger:
    """Comprehensive latency logging and analysis"""
    
    def __init__(self, max_history_per_session: int = 100):
        self.session_latencies: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.max_history = max_history_per_session
        self.session_start_times: Dict[str, float] = {}
    
    def log_latency(self, session_id: str, operation: str, latency_ms: float):
        """Log latency for a specific operation"""
        # Store in session history
        if len(self.session_latencies[session_id][operation]) >= self.max_history:
            self.session_latencies[session_id][operation].popleft()
        
        self.session_latencies[session_id][operation].append({
            "timestamp": time.time(),
            "latency_ms": latency_ms
        })
        
        # Log to console with appropriate level based on latency
        if latency_ms > 5000:  # > 5 seconds
            log_level = logging.ERROR
            emoji = "🐌"
        elif latency_ms > 2000:  # > 2 seconds
            log_level = logging.WARNING
            emoji = "⚠️"
        elif latency_ms > 1000:  # > 1 second
            log_level = logging.INFO
            emoji = "🔶"
        else:
            log_level = logging.DEBUG
            emoji = "✅"
        
        logger.log(
            log_level,
            f"{emoji} [{session_id[:8]}] {operation}: {latency_ms:.2f}ms"
        )
    
    def get_session_stats(self, session_id: str) -> Dict[str, dict]:
        """Get comprehensive latency statistics for a session"""
        if session_id not in self.session_latencies:
            return {}
        
        stats = {}
        
        for operation, latencies in self.session_latencies[session_id].items():
            if not latencies:
                continue
            
            latency_values = [l["latency_ms"] for l in latencies]
            
            stats[operation] = {
                "count": len(latency_values),
                "min": min(latency_values),
                "max": max(latency_values),
                "mean": statistics.mean(latency_values),
                "median": statistics.median(latency_values),
                "p95": self._percentile(latency_values, 95),
                "p99": self._percentile(latency_values, 99),
                "recent_5": latency_values[-5:] if len(latency_values) >= 5 else latency_values
            }
        
        return stats
    
    def get_global_stats(self) -> Dict[str, dict]:
        """Get global latency statistics across all sessions"""
        global_stats = defaultdict(list)
        
        # Collect all latencies by operation
        for session_latencies in self.session_latencies.values():
            for operation, latencies in session_latencies.items():
                latency_values = [l["latency_ms"] for l in latencies]
                global_stats[operation].extend(latency_values)
        
        # Calculate statistics
        stats = {}
        for operation, latencies in global_stats.items():
            if latencies:
                stats[operation] = {
                    "total_samples": len(latencies),
                    "min": min(latencies),
                    "max": max(latencies),
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "p95": self._percentile(latencies, 95),
                    "p99": self._percentile(latencies, 99)
                }
        
        return stats
    
    def log_session_start(self, session_id: str):
        """Log the start of a session"""
        self.session_start_times[session_id] = time.time()
        logger.info(f"📊 Latency tracking started for session: {session_id}")
    
    def log_session_end(self, session_id: str):
        """Log the end of a session and provide summary"""
        if session_id not in self.session_latencies:
            return
        
        session_duration = None
        if session_id in self.session_start_times:
            session_duration = time.time() - self.session_start_times[session_id]
            del self.session_start_times[session_id]
        
        stats = self.get_session_stats(session_id)
        
        logger.info(f"📊 Session summary for {session_id}:")
        if session_duration:
            logger.info(f"   Duration: {session_duration:.2f}s")
        
        for operation, stat in stats.items():
            logger.info(
                f"   {operation}: {stat['count']} ops, "
                f"avg: {stat['mean']:.2f}ms, "
                f"p95: {stat['p95']:.2f}ms"
            )
        
        # Clean up old session data
        del self.session_latencies[session_id]
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        
        return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
    
    def get_recent_latencies(self, session_id: str, operation: str, count: int = 10) -> List[dict]:
        """Get recent latency measurements for an operation"""
        if session_id not in self.session_latencies:
            return []
        
        if operation not in self.session_latencies[session_id]:
            return []
        
        latencies = list(self.session_latencies[session_id][operation])
        return latencies[-count:] if len(latencies) >= count else latencies
    
    def clear_session_data(self, session_id: str):
        """Clear all data for a session"""
        if session_id in self.session_latencies:
            del self.session_latencies[session_id]
        
        if session_id in self.session_start_times:
            del self.session_start_times[session_id]
        
        logger.debug(f"🧹 Cleared latency data for session: {session_id}")