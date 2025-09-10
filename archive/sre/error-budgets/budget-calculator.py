#!/usr/bin/env python3
"""
🎯 SRE: Error Budget Calculator and Tracker
============================================
Simple error budget calculation and monitoring for both applications
Entry-level SRE implementation for DevOps portfolio
"""

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
import json

# 🏷️ SRE COMPONENT: Error Budget Management

@dataclass
class SLOTarget:
    """
    📊 SRE: Service Level Objective definition
    """
    name: str
    target_percentage: float  # e.g., 99.9 for 99.9%
    measurement_window_days: int = 30
    
    def error_budget_percentage(self) -> float:
        """Calculate error budget as percentage"""
        return 100.0 - self.target_percentage
    
    def error_budget_minutes_per_month(self) -> float:
        """Calculate monthly error budget in minutes"""
        minutes_per_month = 30 * 24 * 60  # 43,200 minutes
        return minutes_per_month * (self.error_budget_percentage() / 100)

@dataclass 
class ErrorBudgetStatus:
    """
    💰 SRE: Current error budget consumption status
    """
    slo_name: str
    budget_consumed_percentage: float
    budget_remaining_percentage: float
    time_to_exhaustion_days: Optional[float]
    burn_rate: float  # Current rate of budget consumption
    
    def is_healthy(self) -> bool:
        """Check if error budget consumption is healthy"""
        return self.budget_consumed_percentage < 75.0
    
    def needs_attention(self) -> bool:
        """Check if error budget needs attention"""
        return self.budget_consumed_percentage >= 75.0
    
    def is_critical(self) -> bool:
        """Check if error budget is critically low"""
        return self.budget_consumed_percentage >= 90.0

class ErrorBudgetCalculator:
    """
    🧮 SRE: Error Budget Calculator for Finance Trading and Pharma Manufacturing
    
    This class implements basic error budget tracking to demonstrate
    SRE knowledge for DevOps portfolio purposes.
    """
    
    def __init__(self):
        # 🏦 Finance Trading SLOs (Ultra-high reliability)
        self.finance_slos = {
            'availability': SLOTarget('Finance Availability', 99.9),
            'latency': SLOTarget('Finance Latency P95', 95.0),  # 95% under 50ms
            'error_rate': SLOTarget('Finance Error Rate', 99.9)  # <0.1% errors
        }
        
        # 🏥 Pharma Manufacturing SLOs (Patient safety focus)
        self.pharma_slos = {
            'availability': SLOTarget('Pharma Availability', 99.95),
            'latency': SLOTarget('Pharma Latency P95', 95.0),  # 95% under 100ms
            'data_integrity': SLOTarget('Pharma Data Integrity', 99.99),
            'batch_success': SLOTarget('Pharma Batch Success', 98.0)
        }
    
    def calculate_error_budget(self, 
                             total_requests: int, 
                             failed_requests: int,
                             slo_target: SLOTarget) -> ErrorBudgetStatus:
        """
        📊 SRE: Calculate current error budget status
        
        Args:
            total_requests: Total number of requests in measurement window
            failed_requests: Number of failed requests
            slo_target: SLO target definition
            
        Returns:
            ErrorBudgetStatus with current consumption details
        """
        if total_requests == 0:
            return ErrorBudgetStatus(
                slo_name=slo_target.name,
                budget_consumed_percentage=0.0,
                budget_remaining_percentage=100.0,
                time_to_exhaustion_days=None,
                burn_rate=0.0
            )
        
        # Calculate current success rate
        success_rate = ((total_requests - failed_requests) / total_requests) * 100
        
        # Calculate error budget consumption
        error_budget_total = slo_target.error_budget_percentage()
        current_error_rate = (failed_requests / total_requests) * 100
        
        if error_budget_total == 0:
            budget_consumed_percentage = 0.0
        else:
            budget_consumed_percentage = (current_error_rate / error_budget_total) * 100
        
        budget_remaining_percentage = max(0.0, 100.0 - budget_consumed_percentage)
        
        # Calculate burn rate (budget consumed per day)
        burn_rate = budget_consumed_percentage / slo_target.measurement_window_days
        
        # Estimate time to exhaustion
        if burn_rate > 0 and budget_remaining_percentage > 0:
            time_to_exhaustion_days = budget_remaining_percentage / burn_rate
        else:
            time_to_exhaustion_days = None
        
        return ErrorBudgetStatus(
            slo_name=slo_target.name,
            budget_consumed_percentage=min(100.0, budget_consumed_percentage),
            budget_remaining_percentage=budget_remaining_percentage,
            time_to_exhaustion_days=time_to_exhaustion_days,
            burn_rate=burn_rate
        )
    
    def get_finance_trading_budget_report(self, metrics: Dict) -> Dict[str, ErrorBudgetStatus]:
        """
        🏦 SRE: Generate error budget report for Finance Trading system
        
        Args:
            metrics: Dictionary containing request metrics
                    {
                        'total_requests': int,
                        'failed_requests': int,
                        'slow_requests': int  # requests over latency SLO
                    }
        """
        report = {}
        
        # Availability error budget
        if 'total_requests' in metrics and 'failed_requests' in metrics:
            report['availability'] = self.calculate_error_budget(
                metrics['total_requests'],
                metrics['failed_requests'], 
                self.finance_slos['availability']
            )
        
        # Latency error budget  
        if 'total_requests' in metrics and 'slow_requests' in metrics:
            report['latency'] = self.calculate_error_budget(
                metrics['total_requests'],
                metrics['slow_requests'],
                self.finance_slos['latency'] 
            )
        
        return report
    
    def get_pharma_manufacturing_budget_report(self, metrics: Dict) -> Dict[str, ErrorBudgetStatus]:
        """
        🏥 SRE: Generate error budget report for Pharma Manufacturing system
        
        Args:
            metrics: Dictionary containing manufacturing metrics
                    {
                        'total_requests': int,
                        'failed_requests': int,
                        'slow_requests': int,
                        'total_batches': int,
                        'failed_batches': int,
                        'total_data_validations': int,
                        'failed_data_validations': int
                    }
        """
        report = {}
        
        # Availability error budget
        if 'total_requests' in metrics and 'failed_requests' in metrics:
            report['availability'] = self.calculate_error_budget(
                metrics['total_requests'],
                metrics['failed_requests'],
                self.pharma_slos['availability']
            )
        
        # Batch success error budget
        if 'total_batches' in metrics and 'failed_batches' in metrics:
            report['batch_success'] = self.calculate_error_budget(
                metrics['total_batches'],
                metrics['failed_batches'],
                self.pharma_slos['batch_success']
            )
        
        # Data integrity error budget  
        if 'total_data_validations' in metrics and 'failed_data_validations' in metrics:
            report['data_integrity'] = self.calculate_error_budget(
                metrics['total_data_validations'],
                metrics['failed_data_validations'],
                self.pharma_slos['data_integrity']
            )
        
        return report
    
    def generate_budget_summary(self, service_name: str, budget_report: Dict[str, ErrorBudgetStatus]) -> str:
        """
        📝 SRE: Generate human-readable error budget summary
        """
        summary = [f"\n🎯 SRE Error Budget Report: {service_name}"]
        summary.append("=" * 50)
        summary.append(f"📅 Report Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("")
        
        for slo_name, budget_status in budget_report.items():
            status_emoji = "🟢" if budget_status.is_healthy() else "🟡" if budget_status.needs_attention() else "🔴"
            
            summary.append(f"{status_emoji} {budget_status.slo_name}")
            summary.append(f"   📊 Budget Consumed: {budget_status.budget_consumed_percentage:.1f}%")
            summary.append(f"   💰 Budget Remaining: {budget_status.budget_remaining_percentage:.1f}%")
            summary.append(f"   🔥 Burn Rate: {budget_status.burn_rate:.2f}%/day")
            
            if budget_status.time_to_exhaustion_days:
                summary.append(f"   ⏰ Time to Exhaustion: {budget_status.time_to_exhaustion_days:.1f} days")
            
            if budget_status.is_critical():
                summary.append("   🚨 CRITICAL: Error budget critically low!")
            elif budget_status.needs_attention():
                summary.append("   ⚠️  WARNING: Error budget needs attention")
            
            summary.append("")
        
        return "\n".join(summary)

def main():
    """
    🎯 SRE: Demo error budget calculations
    """
    calculator = ErrorBudgetCalculator()
    
    # 🏦 Example Finance Trading metrics
    finance_metrics = {
        'total_requests': 1000000,     # 1M requests this month
        'failed_requests': 500,        # 500 failed requests (0.05%)
        'slow_requests': 5000          # 5000 slow requests (0.5%)
    }
    
    # 🏥 Example Pharma Manufacturing metrics  
    pharma_metrics = {
        'total_requests': 500000,           # 500K requests this month
        'failed_requests': 100,             # 100 failed requests (0.02%)
        'slow_requests': 2500,              # 2500 slow requests (0.5%)
        'total_batches': 1000,              # 1000 manufacturing batches
        'failed_batches': 15,               # 15 failed batches (1.5%)
        'total_data_validations': 10000,    # 10K data validations
        'failed_data_validations': 1        # 1 failed validation (0.01%)
    }
    
    # Generate reports
    finance_report = calculator.get_finance_trading_budget_report(finance_metrics)
    pharma_report = calculator.get_pharma_manufacturing_budget_report(pharma_metrics)
    
    # Print summaries
    print(calculator.generate_budget_summary("Finance Trading", finance_report))
    print(calculator.generate_budget_summary("Pharma Manufacturing", pharma_report))
    
    # 💾 SRE: Save reports as JSON for monitoring systems
    report_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'finance_trading': {
            slo: {
                'budget_consumed_percentage': status.budget_consumed_percentage,
                'budget_remaining_percentage': status.budget_remaining_percentage,
                'burn_rate': status.burn_rate,
                'is_healthy': status.is_healthy()
            }
            for slo, status in finance_report.items()
        },
        'pharma_manufacturing': {
            slo: {
                'budget_consumed_percentage': status.budget_consumed_percentage,
                'budget_remaining_percentage': status.budget_remaining_percentage,
                'burn_rate': status.burn_rate,
                'is_healthy': status.is_healthy()
            }
            for slo, status in pharma_report.items()
        }
    }
    
    with open('/tmp/error-budget-report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print("📊 Error budget report saved to /tmp/error-budget-report.json")

if __name__ == "__main__":
    main()

# 📝 SRE Implementation Notes:
# ============================
# 1. This calculator demonstrates basic SRE error budget concepts
# 2. In production, metrics would come from Prometheus/monitoring system
# 3. Error budget policies would automate deployment decisions
# 4. Reports would be integrated into Grafana dashboards
# 5. Alerts would fire when budgets reach warning thresholds