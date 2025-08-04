"""
Latency logging and monitoring utilities for Pipecat Voice Agent
"""

import logging
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional
import statistics

logger = logging.getLogger(__name__)


class LatencyLogger:
    """Comprehensive latency logging and analysis for Pipecat pipelines"""
    
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
            f"{emoji} [PIPECAT-{session_id[:8]}] {operation}: {latency_ms:.2f}ms"
        )
    
    def log_pipeline_latency(self, session_id: str, stage: str, latency_ms: float):
        """Log latency for a specific pipeline stage"""
        self.log_latency(session_id, f"pipeline_{stage}", latency_ms)
    
    def log_service_latency(self, session_id: str, service: str, latency_ms: float):
        """Log latency for a specific service (Groq, Google TTS, Google STT)"""
        self.log_latency(session_id, f"service_{service}", latency_ms)
    
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
    
    def get_pipeline_stats(self, session_id: str) -> Dict[str, dict]:
        """Get pipeline-specific statistics"""
        if session_id not in self.session_latencies:
            return {}
        
        pipeline_stats = {}
        for operation, latencies in self.session_latencies[session_id].items():
            if operation.startswith("pipeline_"):
                stage = operation.replace("pipeline_", "")
                latency_values = [l["latency_ms"] for l in latencies]
                
                if latency_values:
                    pipeline_stats[stage] = {
                        "count": len(latency_values),
                        "mean": statistics.mean(latency_values),
                        "min": min(latency_values),
                        "max": max(latency_values),
                        "p95": self._percentile(latency_values, 95)
                    }
        
        return pipeline_stats
    
    def get_service_stats(self, session_id: str) -> Dict[str, dict]:
        """Get service-specific statistics"""
        if session_id not in self.session_latencies:
            return {}
        
        service_stats = {}
        for operation, latencies in self.session_latencies[session_id].items():
            if operation.startswith("service_"):
                service = operation.replace("service_", "")
                latency_values = [l["latency_ms"] for l in latencies]
                
                if latency_values:
                    service_stats[service] = {
                        "count": len(latency_values),
                        "mean": statistics.mean(latency_values),
                        "min": min(latency_values),
                        "max": max(latency_values),
                        "p95": self._percentile(latency_values, 95)
                    }
        
        return service_stats
    
    def log_session_start(self, session_id: str):
        """Log the start of a session"""
        self.session_start_times[session_id] = time.time()
        logger.info(f"📊 Pipecat latency tracking started for session: {session_id}")
    
    def log_session_end(self, session_id: str):
        """Log the end of a session and provide summary"""
        if session_id not in self.session_latencies:
            return
        
        session_duration = None
        if session_id in self.session_start_times:
            session_duration = time.time() - self.session_start_times[session_id]
            del self.session_start_times[session_id]
        
        stats = self.get_session_stats(session_id)
        pipeline_stats = self.get_pipeline_stats(session_id)
        service_stats = self.get_service_stats(session_id)
        
        logger.info(f"📊 Pipecat session summary for {session_id}:")
        if session_duration:
            logger.info(f"   Duration: {session_duration:.2f}s")
        
        # Log overall stats
        for operation, stat in stats.items():
            if not operation.startswith(("pipeline_", "service_")):
                logger.info(
                    f"   {operation}: {stat['count']} ops, "
                    f"avg: {stat['mean']:.2f}ms, "
                    f"p95: {stat['p95']:.2f}ms"
                )
        
        # Log pipeline stats
        if pipeline_stats:
            logger.info("   Pipeline stages:")
            for stage, stat in pipeline_stats.items():
                logger.info(f"     {stage}: avg {stat['mean']:.2f}ms")
        
        # Log service stats
        if service_stats:
            logger.info("   Service performance:")
            for service, stat in service_stats.items():
                logger.info(f"     {service}: avg {stat['mean']:.2f}ms")
        
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
    
    def get_performance_summary(self) -> dict:
        """Get overall performance summary across all sessions"""
        global_stats = self.get_global_stats()
        
        summary = {
            "total_sessions": len(self.session_latencies),
            "services": {},
            "pipeline_stages": {},
            "overall": {}
        }
        
        for operation, stats in global_stats.items():
            if operation.startswith("service_"):
                service = operation.replace("service_", "")
                summary["services"][service] = {
                    "avg_latency": stats["mean"],
                    "p95_latency": stats["p95"],
                    "total_calls": stats["total_samples"]
                }
            elif operation.startswith("pipeline_"):
                stage = operation.replace("pipeline_", "")
                summary["pipeline_stages"][stage] = {
                    "avg_latency": stats["mean"],
                    "p95_latency": stats["p95"],
                    "total_calls": stats["total_samples"]
                }
            else:
                summary["overall"][operation] = {
                    "avg_latency": stats["mean"],
                    "p95_latency": stats["p95"],
                    "total_calls": stats["total_samples"]
                }
        
        return summary