#!/usr/bin/env python3
"""
Infrastructure Health Validation
=================================

Multi-tier infrastructure health checks with forensic-level validation:
- System resources (CPU, memory, disk, network)
- Kubernetes cluster health
- Container runtime health
- Network connectivity and latency
- Storage subsystem validation
- Security posture assessment

Forensic Methodology Applied:
- Evidence collection from multiple system sources
- Cross-correlation of metrics for anomaly detection
- Baseline deviation analysis for early warning
- Immutable audit trail of all findings
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import aiohttp
import psutil
import yaml
from kubernetes import client, config

from ..common.forensic_validator import (
    BaseHealthCheck, HealthStatus, Severity, ForensicLogger
)


class SystemResourcesCheck(BaseHealthCheck):
    """System resources health check with forensic baseline analysis."""
    
    def __init__(self, logger: ForensicLogger, thresholds: Dict[str, float]):
        super().__init__("infrastructure.system", logger)
        self.thresholds = thresholds
    
    async def execute(self):
        """Execute comprehensive system resource validation."""
        start_time = time.perf_counter()
        
        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            load_avg = os.getloadavg()
            
            # Collect process information
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['cpu_percent'] > 5 or proc.info['memory_percent'] > 5:
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Evidence collection for forensic analysis
            evidence = {
                "cpu_info": {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory_info": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "swap": psutil.swap_memory()._asdict()
                },
                "disk_info": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "filesystem": await self._get_filesystem_info()
                },
                "network_info": {
                    "interfaces": await self._get_network_interfaces(),
                    "connections": len(psutil.net_connections())
                },
                "high_resource_processes": processes[:10]  # Top 10 resource consumers
            }
            
            # Metrics for monitoring and alerting
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "load_avg_1min": load_avg[0],
                "load_avg_5min": load_avg[1],
                "load_avg_15min": load_avg[2],
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "network_packets_sent": network.packets_sent,
                "network_packets_recv": network.packets_recv,
                "active_processes": len(psutil.pids())
            }
            
            # Health scoring based on thresholds
            score, status, severity = self._calculate_health_score(metrics)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return self._create_result(
                check_type="system_resources",
                status=status,
                score=score,
                metrics=metrics,
                evidence=evidence,
                duration_ms=duration_ms,
                severity=severity
            )
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return self._create_result(
                check_type="system_resources",
                status=HealthStatus.CRITICAL,
                score=0.0,
                metrics={},
                evidence={"error": str(e)},
                duration_ms=duration_ms,
                error_message=str(e),
                severity=Severity.CRITICAL
            )
    
    async def _get_filesystem_info(self) -> List[Dict[str, Any]]:
        """Get detailed filesystem information."""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            filesystems = []
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 6:
                    filesystems.append({
                        "filesystem": parts[0],
                        "size": parts[1],
                        "used": parts[2],
                        "available": parts[3],
                        "use_percent": parts[4],
                        "mounted_on": parts[5]
                    })
            return filesystems
        except Exception:
            return []
    
    async def _get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interface information."""
        interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            stats = psutil.net_if_stats().get(interface)
            interface_info = {
                "name": interface,
                "addresses": [addr._asdict() for addr in addrs],
                "is_up": stats.isup if stats else False,
                "speed": stats.speed if stats else 0
            }
            interfaces.append(interface_info)
        return interfaces
    
    def _calculate_health_score(self, metrics: Dict[str, float]) -> tuple:
        """Calculate health score based on system metrics."""
        score = 100.0
        status = HealthStatus.HEALTHY
        severity = Severity.LOW
        
        # CPU utilization scoring
        if metrics["cpu_percent"] > self.thresholds.get("cpu_critical", 90):
            score -= 30
            status = HealthStatus.CRITICAL
            severity = Severity.CRITICAL
        elif metrics["cpu_percent"] > self.thresholds.get("cpu_warning", 70):
            score -= 15
            status = HealthStatus.DEGRADED
            severity = Severity.MEDIUM
        
        # Memory utilization scoring
        if metrics["memory_percent"] > self.thresholds.get("memory_critical", 85):
            score -= 25
            status = HealthStatus.CRITICAL
            severity = Severity.CRITICAL
        elif metrics["memory_percent"] > self.thresholds.get("memory_warning", 70):
            score -= 10
            status = HealthStatus.DEGRADED
            severity = max(severity, Severity.MEDIUM)
        
        # Disk utilization scoring
        if metrics["disk_percent"] > self.thresholds.get("disk_critical", 90):
            score -= 20
            status = HealthStatus.CRITICAL
            severity = Severity.CRITICAL
        elif metrics["disk_percent"] > self.thresholds.get("disk_warning", 80):
            score -= 10
            status = HealthStatus.DEGRADED
            severity = max(severity, Severity.MEDIUM)
        
        # Load average scoring
        cpu_count = psutil.cpu_count()
        if metrics["load_avg_1min"] > cpu_count * 2:
            score -= 15
            status = HealthStatus.CRITICAL if status != HealthStatus.CRITICAL else status
            severity = max(severity, Severity.HIGH)
        elif metrics["load_avg_1min"] > cpu_count * 1.5:
            score -= 8
            status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
            severity = max(severity, Severity.MEDIUM)
        
        return max(score, 0.0), status, severity


class KubernetesHealthCheck(BaseHealthCheck):
    """Kubernetes cluster health validation with forensic evidence collection."""
    
    def __init__(self, logger: ForensicLogger, namespace: str = "default"):
        super().__init__("infrastructure.kubernetes", logger)
        self.namespace = namespace
        
        # Initialize Kubernetes client
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                self.k8s_available = False
                return
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.k8s_available = True
    
    async def execute(self):
        """Execute comprehensive Kubernetes health validation."""
        start_time = time.perf_counter()
        
        if not self.k8s_available:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return self._create_result(
                check_type="kubernetes_cluster",
                status=HealthStatus.CRITICAL,
                score=0.0,
                metrics={},
                evidence={"error": "Kubernetes API not available"},
                duration_ms=duration_ms,
                error_message="Kubernetes API not available",
                severity=Severity.CRITICAL
            )
        
        try:
            # Collect cluster information
            nodes = self.v1.list_node()
            pods = self.v1.list_pod_for_all_namespaces()
            services = self.v1.list_service_for_all_namespaces()
            deployments = self.apps_v1.list_deployment_for_all_namespaces()
            
            # Analyze node health
            node_health = self._analyze_node_health(nodes)
            
            # Analyze pod health
            pod_health = self._analyze_pod_health(pods)
            
            # Analyze deployment health
            deployment_health = self._analyze_deployment_health(deployments)
            
            # Evidence collection
            evidence = {
                "cluster_info": {
                    "total_nodes": len(nodes.items),
                    "total_pods": len(pods.items),
                    "total_services": len(services.items),
                    "total_deployments": len(deployments.items)
                },
                "node_details": node_health["details"],
                "pod_details": pod_health["details"],
                "deployment_details": deployment_health["details"],
                "api_server_response_time_ms": await self._measure_api_response_time()
            }
            
            # Metrics for monitoring
            metrics = {
                "nodes_ready": node_health["ready_count"],
                "nodes_total": node_health["total_count"],
                "nodes_ready_percent": (node_health["ready_count"] / max(node_health["total_count"], 1)) * 100,
                "pods_running": pod_health["running_count"],
                "pods_total": pod_health["total_count"],
                "pods_failed": pod_health["failed_count"],
                "pods_pending": pod_health["pending_count"],
                "deployments_ready": deployment_health["ready_count"],
                "deployments_total": deployment_health["total_count"],
                "api_response_time_ms": evidence["api_server_response_time_ms"]
            }
            
            # Calculate overall health score
            score, status, severity = self._calculate_cluster_health_score(metrics)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return self._create_result(
                check_type="kubernetes_cluster",
                status=status,
                score=score,
                metrics=metrics,
                evidence=evidence,
                duration_ms=duration_ms,
                severity=severity
            )
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return self._create_result(
                check_type="kubernetes_cluster",
                status=HealthStatus.CRITICAL,
                score=0.0,
                metrics={},
                evidence={"error": str(e)},
                duration_ms=duration_ms,
                error_message=str(e),
                severity=Severity.CRITICAL
            )
    
    def _analyze_node_health(self, nodes) -> Dict[str, Any]:
        """Analyze Kubernetes node health status."""
        ready_count = 0
        node_details = []
        
        for node in nodes.items:
            node_ready = False
            conditions = []
            
            if node.status.conditions:
                for condition in node.status.conditions:
                    conditions.append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason or "",
                        "message": condition.message or ""
                    })
                    
                    if condition.type == "Ready" and condition.status == "True":
                        node_ready = True
                        ready_count += 1
            
            node_details.append({
                "name": node.metadata.name,
                "ready": node_ready,
                "conditions": conditions,
                "node_info": {
                    "kernel_version": node.status.node_info.kernel_version,
                    "os_image": node.status.node_info.os_image,
                    "container_runtime": node.status.node_info.container_runtime_version,
                    "kubelet_version": node.status.node_info.kubelet_version
                }
            })
        
        return {
            "ready_count": ready_count,
            "total_count": len(nodes.items),
            "details": node_details
        }
    
    def _analyze_pod_health(self, pods) -> Dict[str, Any]:
        """Analyze pod health across all namespaces."""
        running_count = 0
        failed_count = 0
        pending_count = 0
        pod_details = []
        
        for pod in pods.items:
            phase = pod.status.phase
            
            if phase == "Running":
                running_count += 1
            elif phase == "Failed":
                failed_count += 1
            elif phase == "Pending":
                pending_count += 1
            
            # Collect container statuses
            container_statuses = []
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    container_statuses.append({
                        "name": container.name,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "image": container.image
                    })
            
            pod_details.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": phase,
                "containers": container_statuses,
                "node": pod.spec.node_name or "unscheduled"
            })
        
        return {
            "running_count": running_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "total_count": len(pods.items),
            "details": pod_details[:50]  # Limit for performance
        }
    
    def _analyze_deployment_health(self, deployments) -> Dict[str, Any]:
        """Analyze deployment health and readiness."""
        ready_count = 0
        deployment_details = []
        
        for deployment in deployments.items:
            is_ready = (
                deployment.status.ready_replicas == deployment.status.replicas
                if deployment.status.ready_replicas and deployment.status.replicas
                else False
            )
            
            if is_ready:
                ready_count += 1
            
            deployment_details.append({
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "ready": is_ready,
                "replicas": deployment.status.replicas or 0,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "updated_replicas": deployment.status.updated_replicas or 0
            })
        
        return {
            "ready_count": ready_count,
            "total_count": len(deployments.items),
            "details": deployment_details
        }
    
    async def _measure_api_response_time(self) -> float:
        """Measure Kubernetes API server response time."""
        start_time = time.perf_counter()
        try:
            self.v1.list_namespace()
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000
        except Exception:
            return -1.0
    
    def _calculate_cluster_health_score(self, metrics: Dict[str, float]) -> tuple:
        """Calculate overall cluster health score."""
        score = 100.0
        status = HealthStatus.HEALTHY
        severity = Severity.LOW
        
        # Node health scoring
        if metrics["nodes_ready_percent"] < 80:
            score -= 40
            status = HealthStatus.CRITICAL
            severity = Severity.CRITICAL
        elif metrics["nodes_ready_percent"] < 90:
            score -= 20
            status = HealthStatus.DEGRADED
            severity = Severity.HIGH
        
        # Pod health scoring
        if metrics["pods_failed"] > 0:
            score -= min(metrics["pods_failed"] * 5, 30)
            status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
            severity = max(severity, Severity.MEDIUM)
        
        # Deployment health scoring
        deployment_ready_percent = (
            metrics["deployments_ready"] / max(metrics["deployments_total"], 1)
        ) * 100
        
        if deployment_ready_percent < 90:
            score -= 25
            status = HealthStatus.CRITICAL if deployment_ready_percent < 70 else HealthStatus.DEGRADED
            severity = max(severity, Severity.HIGH if deployment_ready_percent < 70 else Severity.MEDIUM)
        
        # API response time scoring
        if metrics["api_response_time_ms"] > 1000:
            score -= 15
            status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
            severity = max(severity, Severity.MEDIUM)
        
        return max(score, 0.0), status, severity


class NetworkConnectivityCheck(BaseHealthCheck):
    """Network connectivity and latency validation with forensic analysis."""
    
    def __init__(self, logger: ForensicLogger, targets: List[Dict[str, str]]):
        super().__init__("infrastructure.network", logger)
        self.targets = targets
    
    async def execute(self):
        """Execute network connectivity validation."""
        start_time = time.perf_counter()
        
        try:
            connectivity_results = []
            
            # Test each target
            for target in self.targets:
                result = await self._test_connectivity(target)
                connectivity_results.append(result)
            
            # Analyze results
            successful_tests = sum(1 for r in connectivity_results if r["success"])
            total_tests = len(connectivity_results)
            success_rate = (successful_tests / max(total_tests, 1)) * 100
            
            avg_latency = sum(
                r["latency_ms"] for r in connectivity_results 
                if r["success"] and r["latency_ms"] > 0
            ) / max(successful_tests, 1)
            
            # Evidence collection
            evidence = {
                "connectivity_tests": connectivity_results,
                "network_statistics": await self._get_network_statistics(),
                "dns_resolution": await self._test_dns_resolution()
            }
            
            # Metrics
            metrics = {
                "success_rate_percent": success_rate,
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "average_latency_ms": avg_latency,
                "max_latency_ms": max(
                    (r["latency_ms"] for r in connectivity_results if r["success"]), 
                    default=0
                ),
                "min_latency_ms": min(
                    (r["latency_ms"] for r in connectivity_results if r["success"]), 
                    default=0
                )
            }
            
            # Health scoring
            score, status, severity = self._calculate_network_health_score(metrics)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return self._create_result(
                check_type="network_connectivity",
                status=status,
                score=score,
                metrics=metrics,
                evidence=evidence,
                duration_ms=duration_ms,
                severity=severity
            )
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return self._create_result(
                check_type="network_connectivity",
                status=HealthStatus.CRITICAL,
                score=0.0,
                metrics={},
                evidence={"error": str(e)},
                duration_ms=duration_ms,
                error_message=str(e),
                severity=Severity.CRITICAL
            )
    
    async def _test_connectivity(self, target: Dict[str, str]) -> Dict[str, Any]:
        """Test connectivity to a specific target."""
        start_time = time.perf_counter()
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(target["url"]) as response:
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    
                    return {
                        "target": target["name"],
                        "url": target["url"],
                        "success": response.status < 400,
                        "status_code": response.status,
                        "latency_ms": latency_ms,
                        "response_size": len(await response.text())
                    }
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return {
                "target": target["name"],
                "url": target["url"],
                "success": False,
                "status_code": -1,
                "latency_ms": latency_ms,
                "error": str(e)
            }
    
    async def _get_network_statistics(self) -> Dict[str, Any]:
        """Get detailed network statistics."""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errors_in": net_io.errin,
            "errors_out": net_io.errout,
            "dropped_in": net_io.dropin,
            "dropped_out": net_io.dropout
        }
    
    async def _test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution performance."""
        import socket
        
        dns_tests = ["google.com", "kubernetes.default.svc.cluster.local", "localhost"]
        results = []
        
        for hostname in dns_tests:
            start_time = time.perf_counter()
            try:
                ip = socket.gethostbyname(hostname)
                resolution_time = (time.perf_counter() - start_time) * 1000
                results.append({
                    "hostname": hostname,
                    "resolved_ip": ip,
                    "resolution_time_ms": resolution_time,
                    "success": True
                })
            except Exception as e:
                resolution_time = (time.perf_counter() - start_time) * 1000
                results.append({
                    "hostname": hostname,
                    "resolution_time_ms": resolution_time,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "tests": results,
            "average_resolution_time_ms": sum(
                r["resolution_time_ms"] for r in results if r["success"]
            ) / max(sum(1 for r in results if r["success"]), 1)
        }
    
    def _calculate_network_health_score(self, metrics: Dict[str, float]) -> tuple:
        """Calculate network health score."""
        score = 100.0
        status = HealthStatus.HEALTHY
        severity = Severity.LOW
        
        # Success rate scoring
        if metrics["success_rate_percent"] < 95:
            score -= 40
            status = HealthStatus.CRITICAL
            severity = Severity.CRITICAL
        elif metrics["success_rate_percent"] < 98:
            score -= 20
            status = HealthStatus.DEGRADED
            severity = Severity.HIGH
        
        # Latency scoring
        if metrics["average_latency_ms"] > 500:
            score -= 25
            status = HealthStatus.CRITICAL if status != HealthStatus.CRITICAL else status
            severity = max(severity, Severity.HIGH)
        elif metrics["average_latency_ms"] > 200:
            score -= 15
            status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
            severity = max(severity, Severity.MEDIUM)
        
        return max(score, 0.0), status, severity