# 🚨 Cross-System: Error Budget Exhaustion

## 💰 SRE Runbook: Error Budget Policy Enforcement

**Affected Services**: Finance Trading & Pharma Manufacturing  
**Trigger**: Error budget <10% remaining in measurement window  
**Severity**: High (affects deployment velocity and reliability)

---

## 🚦 Immediate Response (0-5 minutes)

### 1. Verify Error Budget Status
```bash
# Check current error budget for both services
python /path/to/sre/error-budgets/budget-calculator.py

# Review error budget dashboard
# Navigate to: SRE Error Budget Dashboard
```

### 2. Assess Impact
```bash
# Check which SLO is driving budget consumption
curl http://finance-trading-service/health/sre | jq '.error_budget_remaining'
curl http://pharma-manufacturing-service/health/sre | jq '.error_budget_remaining'
```

### 3. Immediate Policy Enforcement
```bash
# Freeze all non-emergency deployments
echo "DEPLOYMENT_FREEZE=true" >> /etc/sre/deployment-policy.conf

# Notify development teams
slack-notify "#dev-team" "🚨 Error budget exhausted. Deployment freeze in effect until SLO recovery."
```

---

## 🔍 Root Cause Analysis (5-15 minutes)

### Step 1: Identify Budget Consumption Source
```bash
# Check recent incidents and alerts
kubectl get events --sort-by='.lastTimestamp' -n finance-trading
kubectl get events --sort-by='.lastTimestamp' -n pharma-manufacturing

# Review error budget burn rate patterns
# Look for: Sudden spikes, gradual degradation, specific timeframes
```

### Step 2: Categorize Budget Consumption
```bash
# Check different SLI contributions to budget burn
# Finance Trading:
# - Availability issues (downtime)
# - Latency issues (>50ms responses)  
# - Error rate issues (failed requests)

# Pharma Manufacturing:
# - Data integrity failures
# - Batch production failures
# - Environmental compliance issues
```

### Step 3: Business Impact Assessment
- **Finance**: Calculate revenue impact from SLO violations
- **Pharma**: Assess regulatory compliance risk
- **Both**: Determine if budget consumption is acceptable vs business needs

---

## 🛠 Recovery Strategies

### Strategy 1: Quick SLO Recovery (Recommended)
```bash
# Focus on easiest SLO improvements
# - Scale up resources temporarily
# - Enable circuit breakers for external dependencies
# - Optimize most obvious performance bottlenecks

# Finance Trading quick wins:
kubectl scale deployment trading-app --replicas=10 -n finance-trading
kubectl set env deployment/trading-app MARKET_DATA_PROVIDER=simulation

# Pharma Manufacturing quick wins:
kubectl scale deployment manufacturing-app --replicas=5 -n pharma-manufacturing
python scripts/optimize-database-queries.py
```

### Strategy 2: SLO Adjustment (If justified)
```yaml
# Temporarily relax SLOs if business context supports it
# Example: During planned maintenance windows or known issues

# Finance Trading: Relax latency from 50ms to 75ms temporarily
# Pharma Manufacturing: Adjust batch success rate from 98% to 96%

# Note: Requires business stakeholder approval
```

### Strategy 3: Emergency Override (Last resort)
```bash
# Override error budget policy for critical business needs
# Requires VP+ approval and explicit risk acceptance

echo "EMERGENCY_OVERRIDE=true" >> /etc/sre/deployment-policy.conf
echo "OVERRIDE_REASON='Critical business deployment approved by [VP NAME]'" >> /etc/sre/deployment-policy.conf
echo "OVERRIDE_EXPIRY='$(date -d '+24 hours' -Iseconds)'" >> /etc/sre/deployment-policy.conf
```

---

## 📢 Communication & Escalation

### Development Team Notification
```bash
# Automated notification to all development teams
cat > /tmp/error-budget-notice.txt << EOF
🚨 ERROR BUDGET EXHAUSTION NOTICE

Service: [Finance Trading / Pharma Manufacturing]
Current Budget Remaining: [X%]
Deployment Status: FROZEN
Expected Recovery: [TimeFrame]

Immediate Actions Required:
1. No non-emergency deployments
2. Focus on SLO improvement
3. Monitor #sre-alerts for updates

SRE Contact: [On-call Engineer]
Business Context: [Revenue/Compliance Impact]
EOF

# Send to Slack, email, and incident management system
```

### Business Stakeholder Updates
- **Finance Trading**: Trading desk manager, revenue operations
- **Pharma Manufacturing**: Quality assurance, regulatory affairs
- **Executive**: If multiple consecutive budget exhaustions

### Regulatory Notifications (Pharma only)
- **Quality Manager**: If patient safety implications
- **Regulatory Affairs**: If FDA compliance risk

---

## 📊 Monitoring During Recovery

### Real-time Budget Tracking
```bash
# Monitor error budget recovery every 15 minutes
while true; do
    echo "$(date): Error Budget Status:"
    python /path/to/sre/error-budgets/budget-calculator.py | grep "Budget Remaining"
    sleep 900  # 15 minutes
done
```

### SLO Compliance Tracking
```bash
# Track individual SLI improvements
# Finance Trading:
watch -n 60 'curl -s http://finance-trading-service/health/sre | jq ".slo_compliance"'

# Pharma Manufacturing:
watch -n 60 'curl -s http://pharma-manufacturing-service/health/sre | jq ".slo_compliance"'
```

---

## 🔄 Recovery and Policy Reset

### Error Budget Recovery Criteria
- **Finance Trading**: >25% error budget remaining for 4 hours
- **Pharma Manufacturing**: >50% error budget remaining for 2 hours (conservative)
- **All SLOs**: Meeting targets consistently

### Deployment Freeze Lift
```bash
# Verify recovery criteria met
if [[ $(check_error_budget_health.sh) == "HEALTHY" ]]; then
    echo "DEPLOYMENT_FREEZE=false" >> /etc/sre/deployment-policy.conf
    echo "Error budget recovered. Deployment freeze lifted."
    slack-notify "#dev-team" "✅ Error budget recovered. Deployments resumed with normal approval process."
fi
```

### Post-Incident Review
```bash
# Generate error budget incident report
cat > /tmp/error-budget-incident-report.md << EOF
# Error Budget Exhaustion Incident Report

**Date**: $(date -Iseconds)
**Duration**: [X hours]
**Services Affected**: [List]
**Root Cause**: [Summary]

## Business Impact
- Revenue Impact: $[Amount]
- Compliance Risk: [High/Medium/Low]
- Deployment Delay: [X deployments delayed]

## Lessons Learned
1. [Key insight 1]
2. [Key insight 2]
3. [Key insight 3]

## Action Items
- [ ] Improve monitoring for [specific area]
- [ ] Update SLO targets based on [business context]
- [ ] Enhance error budget alerting
- [ ] Review deployment practices

**Next Review Date**: $(date -d '+1 week' +%Y-%m-%d)
EOF
```

---

## 🎯 SRE Learning Notes

**Error Budget Philosophy**: Error budgets balance reliability and velocity. Exhaustion indicates either:
1. System reliability issues (need engineering focus)
2. Unrealistic SLO targets (need business discussion)
3. Exceptional circumstances (acceptable budget burn)

**Business Alignment**: Error budget policies should align with business priorities:
- **Finance**: Market opportunities may justify budget consumption
- **Pharma**: Patient safety requires conservative budget management

**Deployment Velocity Impact**: Budget exhaustion freezes feature development, creating tension between reliability and business needs. SRE role is to facilitate data-driven discussions about this trade-off.

**Policy Enforcement**: Automated policy enforcement reduces human judgment errors but requires override mechanisms for genuine business emergencies.

---

**Runbook Version**: 1.0  
**Last Updated**: Entry-level SRE implementation  
**Next Review**: After each budget exhaustion incident