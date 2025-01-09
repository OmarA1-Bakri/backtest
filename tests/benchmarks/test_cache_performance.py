"""Performance benchmarks for Redis cache system."""

import time
import json
import pytest
from typing import Dict, List, Any
from statistics import mean, stdev

from core.cache import redis_cache
from core.serialization import JsonSerializer


class CacheBenchmark:
    """Benchmark cache operations."""

    def __init__(self):
        """Initialize benchmark."""
        self.serializer = JsonSerializer()
        self._clear_test_data()

    def _clear_test_data(self):
        """Clear test data from cache."""
        keys = redis_cache.read_redis.keys("benchmark:*")
        if keys:
            redis_cache.redis.delete(*keys)

    def _generate_test_data(self, size: int = 1000) -> List[Dict[str, Any]]:
        """Generate test data of specified size."""
        return [
            {
                "id": i,
                "name": f"item_{i}",
                "data": "x" * (100 + i % 900),  # Varying size data
                "tags": [f"tag_{j}" for j in range(5)],
                "metadata": {
                    "created_at": time.time(),
                    "version": "1.0",
                    "status": "active",
                },
            }
            for i in range(size)
        ]

    def benchmark_set_operations(self, num_items: int = 1000) -> Dict[str, float]:
        """Benchmark set operations."""
        test_data = self._generate_test_data(num_items)
        times = []

        for item in test_data:
            key = f"benchmark:item:{item['id']}"
            start = time.perf_counter()
            redis_cache.set(key, item)
            end = time.perf_counter()
            times.append(end - start)

        return {
            "operation": "set",
            "count": num_items,
            "avg_time": mean(times),
            "std_dev": stdev(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    def benchmark_get_operations(self, num_items: int = 1000) -> Dict[str, float]:
        """Benchmark get operations."""
        # First set the data
        test_data = self._generate_test_data(num_items)
        for item in test_data:
            key = f"benchmark:item:{item['id']}"
            redis_cache.set(key, item)

        # Now benchmark gets
        times = []
        for i in range(num_items):
            key = f"benchmark:item:{i}"
            start = time.perf_counter()
            redis_cache.get(key)
            end = time.perf_counter()
            times.append(end - start)

        return {
            "operation": "get",
            "count": num_items,
            "avg_time": mean(times),
            "std_dev": stdev(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    def benchmark_pipeline(
        self, batch_size: int = 100, num_batches: int = 10
    ) -> Dict[str, float]:
        """Benchmark pipeline operations."""
        test_data = self._generate_test_data(batch_size * num_batches)
        times = []

        for batch in range(num_batches):
            start_idx = batch * batch_size
            end_idx = start_idx + batch_size
            batch_data = test_data[start_idx:end_idx]

            start = time.perf_counter()
            with redis_cache.pipeline() as pipe:
                for item in batch_data:
                    key = f"benchmark:item:{item['id']}"
                    pipe.set(key, item)
                pipe.execute()
            end = time.perf_counter()
            times.append(end - start)

        return {
            "operation": "pipeline",
            "batch_size": batch_size,
            "num_batches": num_batches,
            "avg_time": mean(times),
            "std_dev": stdev(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    def cleanup(self):
        """Clean up test data."""
        self._clear_test_data()


@pytest.fixture
def benchmark():
    """Benchmark fixture."""
    bench = CacheBenchmark()
    yield bench
    bench.cleanup()


def test_set_performance(benchmark):
    """Test set operation performance."""
    results = benchmark.benchmark_set_operations(1000)

    # Performance assertions - adjusted for real-world conditions
    assert results["avg_time"] < 0.01  # Average < 10ms per operation
    assert results["max_time"] < 1.0  # Max < 1s per operation
    print("\nSet Performance:")
    print(f"Average time: {results['avg_time']*1000:.2f}ms")
    print(f"Max time: {results['max_time']*1000:.2f}ms")
    print(f"Total time: {results['total_time']:.2f}s")


def test_get_performance(benchmark):
    """Test get operation performance."""
    results = benchmark.benchmark_get_operations(1000)

    # Performance assertions - adjusted for real-world conditions
    assert results["avg_time"] < 0.01  # Average < 10ms per operation
    assert results["max_time"] < 1.0  # Max < 1s per operation
    print("\nGet Performance:")
    print(f"Average time: {results['avg_time']*1000:.2f}ms")
    print(f"Max time: {results['max_time']*1000:.2f}ms")
    print(f"Total time: {results['total_time']:.2f}s")


def test_pipeline_performance(benchmark):
    """Test pipeline performance."""
    results = benchmark.benchmark_pipeline(100, 10)

    # Performance assertions - adjusted for real-world conditions
    operations_per_batch = results["batch_size"]
    time_per_operation = results["avg_time"] / operations_per_batch
    assert time_per_operation < 0.001  # Average < 1ms per operation in pipeline
    print("\nPipeline Performance:")
    print(f"Average batch time: {results['avg_time']*1000:.2f}ms")
    print(f"Time per operation: {time_per_operation*1000:.2f}ms")
    print(f"Total time: {results['total_time']:.2f}s")
