"""Distributed operations benchmarking for Redis cache system."""

import time
import pytest
from typing import Dict, List, Any
from statistics import mean, stdev

from core.cache import redis_cache
from core.cache_cluster import RedisClusterManager
from core.serialization import JsonSerializer


class DistributedBenchmark:
    """Benchmark distributed cache operations."""

    def __init__(self):
        """Initialize benchmark."""
        self.serializer = JsonSerializer()
        self.cluster_manager = RedisClusterManager()
        self._clear_test_data()

    def _clear_test_data(self):
        """Clear test data from cache."""
        keys = redis_cache.read_redis.keys("distbench:*")
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

    def benchmark_distributed_writes(self, num_items: int = 1000) -> Dict[str, float]:
        """Benchmark write operations in distributed mode."""
        test_data = self._generate_test_data(num_items)
        times = []

        # Get master for writes
        master = self.cluster_manager.get_master_for_write()

        for item in test_data:
            key = f"distbench:item:{item['id']}"
            start = time.perf_counter()
            master.set(key, self.serializer.serialize(item))
            end = time.perf_counter()
            times.append(end - start)

        return {
            "operation": "distributed_write",
            "count": num_items,
            "avg_time": mean(times),
            "std_dev": stdev(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    def benchmark_distributed_reads(self, num_items: int = 1000) -> Dict[str, float]:
        """Benchmark read operations in distributed mode."""
        # First write the data
        test_data = self._generate_test_data(num_items)
        master = self.cluster_manager.get_master_for_write()
        for item in test_data:
            key = f"distbench:item:{item['id']}"
            master.set(key, self.serializer.serialize(item))

        # Get replica for reads
        replica = self.cluster_manager.get_slave_for_read()

        # Now benchmark reads
        times = []
        for i in range(num_items):
            key = f"distbench:item:{i}"
            start = time.perf_counter()
            replica.get(key)
            end = time.perf_counter()
            times.append(end - start)

        return {
            "operation": "distributed_read",
            "count": num_items,
            "avg_time": mean(times),
            "std_dev": stdev(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    def benchmark_replication_lag(self, num_items: int = 100) -> Dict[str, float]:
        """Benchmark replication lag between master and replicas."""
        test_data = self._generate_test_data(num_items)
        master = self.cluster_manager.get_master_for_write()
        replica = self.cluster_manager.get_slave_for_read()

        lag_times = []
        for item in test_data:
            key = f"distbench:lag:{item['id']}"

            # Write to master
            start = time.perf_counter()
            master.set(key, self.serializer.serialize(item))

            # Keep checking replica until data appears
            while True:
                if replica.get(key):
                    end = time.perf_counter()
                    lag_times.append(end - start)
                    break
                time.sleep(0.001)  # Small sleep to prevent tight loop

        return {
            "operation": "replication_lag",
            "count": num_items,
            "avg_lag": mean(lag_times),
            "std_dev": stdev(lag_times),
            "min_lag": min(lag_times),
            "max_lag": max(lag_times),
        }

    def cleanup(self):
        """Clean up test data."""
        self._clear_test_data()


@pytest.fixture
def distributed_benchmark():
    """Distributed benchmark fixture."""
    bench = DistributedBenchmark()
    yield bench
    bench.cleanup()


def test_distributed_write_performance(distributed_benchmark):
    """Test distributed write performance."""
    results = distributed_benchmark.benchmark_distributed_writes(1000)

    # Performance assertions
    assert results["avg_time"] < 0.01  # Average < 10ms per operation
    assert results["max_time"] < 0.1  # Max < 100ms per operation
    print("\nDistributed Write Performance:")
    print(f"Average time: {results['avg_time']*1000:.2f}ms")
    print(f"Max time: {results['max_time']*1000:.2f}ms")
    print(f"Total time: {results['total_time']:.2f}s")


def test_distributed_read_performance(distributed_benchmark):
    """Test distributed read performance."""
    results = distributed_benchmark.benchmark_distributed_reads(1000)

    # Performance assertions
    assert results["avg_time"] < 0.01  # Average < 10ms per operation
    assert results["max_time"] < 0.1  # Max < 100ms per operation
    print("\nDistributed Read Performance:")
    print(f"Average time: {results['avg_time']*1000:.2f}ms")
    print(f"Max time: {results['max_time']*1000:.2f}ms")
    print(f"Total time: {results['total_time']:.2f}s")


def test_replication_lag(distributed_benchmark):
    """Test replication lag."""
    results = distributed_benchmark.benchmark_replication_lag(100)

    # Performance assertions
    assert results["avg_lag"] < 0.1  # Average lag < 100ms
    assert results["max_lag"] < 0.5  # Max lag < 500ms
    print("\nReplication Lag:")
    print(f"Average lag: {results['avg_lag']*1000:.2f}ms")
    print(f"Max lag: {results['max_lag']*1000:.2f}ms")
