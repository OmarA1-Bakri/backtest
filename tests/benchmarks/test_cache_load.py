"""Load testing and distributed operations benchmarking for Redis cache system."""

import time
import threading
import multiprocessing
import pytest
from typing import Dict, List, Any
from statistics import mean, stdev
import psutil
import os

from core.cache import redis_cache
from core.serialization import JsonSerializer


class LoadTest:
    """Load test for cache operations."""

    def __init__(self):
        """Initialize load test."""
        self.serializer = JsonSerializer()
        self._clear_test_data()
        self.process = psutil.Process(os.getpid())

    def _clear_test_data(self):
        """Clear test data from cache."""
        keys = redis_cache.read_redis.keys("loadtest:*")
        if keys:
            redis_cache.redis.delete(*keys)

    def _generate_test_data(self, size: int = 1000) -> List[Dict[str, Any]]:
        """Generate test data of specified size."""
        return [
            {
                "id": i,
                "name": f"item_{i}",
                "data": "x" * (100 + i % 900),
                "tags": [f"tag_{j}" for j in range(5)],
                "metadata": {
                    "created_at": time.time(),
                    "version": "1.0",
                    "status": "active",
                },
            }
            for i in range(size)
        ]

    def _worker_function(self, worker_id: int, num_operations: int, results: List):
        """Worker function for concurrent operations."""
        times = []
        for i in range(num_operations):
            key = f"loadtest:worker:{worker_id}:item:{i}"
            data = {"worker_id": worker_id, "operation_id": i, "timestamp": time.time()}

            start = time.perf_counter()
            redis_cache.set(key, data)
            redis_cache.get(key)
            end = time.perf_counter()

            times.append(end - start)

        results.append(
            {
                "worker_id": worker_id,
                "avg_time": mean(times),
                "std_dev": stdev(times),
                "min_time": min(times),
                "max_time": max(times),
            }
        )

    def concurrent_operations(self, num_workers: int, ops_per_worker: int) -> Dict:
        """Run concurrent operations using multiple threads."""
        threads = []
        results = []

        start_time = time.perf_counter()

        # Create and start threads
        for i in range(num_workers):
            thread = threading.Thread(
                target=self._worker_function, args=(i, ops_per_worker, results)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Calculate aggregate statistics
        avg_times = [r["avg_time"] for r in results]
        max_times = [r["max_time"] for r in results]

        return {
            "num_workers": num_workers,
            "ops_per_worker": ops_per_worker,
            "total_operations": num_workers * ops_per_worker,
            "total_time": total_time,
            "operations_per_second": (num_workers * ops_per_worker) / total_time,
            "avg_operation_time": mean(avg_times),
            "max_operation_time": max(max_times),
            "memory_usage": self.process.memory_info().rss / 1024 / 1024,  # MB
        }

    def memory_usage_test(self, num_items: int, item_size_kb: int) -> Dict:
        """Test memory usage with different data sizes."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # Generate and store data
        data = "x" * (item_size_kb * 1024)  # Convert KB to bytes
        for i in range(num_items):
            key = f"loadtest:memory:{i}"
            redis_cache.set(key, data)

        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_info = redis_cache.redis.info("memory")

        return {
            "num_items": num_items,
            "item_size_kb": item_size_kb,
            "total_data_size_mb": (num_items * item_size_kb) / 1024,
            "process_memory_increase_mb": final_memory - initial_memory,
            "redis_used_memory_mb": memory_info["used_memory"] / 1024 / 1024,
            "redis_peak_memory_mb": memory_info["used_memory_peak"] / 1024 / 1024,
        }

    def cleanup(self):
        """Clean up test data."""
        self._clear_test_data()


@pytest.fixture
def load_test():
    """Load test fixture."""
    test = LoadTest()
    yield test
    test.cleanup()


def test_concurrent_operations(load_test):
    """Test concurrent operations performance."""
    results = load_test.concurrent_operations(num_workers=10, ops_per_worker=1000)

    # Performance assertions
    assert results["operations_per_second"] > 1000  # At least 1000 ops/sec
    assert results["avg_operation_time"] < 0.01  # Average < 10ms
    print("\nConcurrent Operations Performance:")
    print(f"Operations per second: {results['operations_per_second']:.2f}")
    print(f"Average operation time: {results['avg_operation_time']*1000:.2f}ms")
    print(f"Maximum operation time: {results['max_operation_time']*1000:.2f}ms")
    print(f"Total time: {results['total_time']:.2f}s")
    print(f"Memory usage: {results['memory_usage']:.2f}MB")


def test_memory_usage(load_test):
    """Test memory usage with different data sizes."""
    results = load_test.memory_usage_test(num_items=1000, item_size_kb=10)

    print("\nMemory Usage Test:")
    print(f"Total data size: {results['total_data_size_mb']:.2f}MB")
    print(f"Process memory increase: {results['process_memory_increase_mb']:.2f}MB")
    print(f"Redis used memory: {results['redis_used_memory_mb']:.2f}MB")
    print(f"Redis peak memory: {results['redis_peak_memory_mb']:.2f}MB")

    # Memory usage assertions
    assert (
        results["process_memory_increase_mb"] < 100
    )  # Process memory increase < 100MB
    assert results["redis_used_memory_mb"] < 1024  # Redis memory < 1GB
