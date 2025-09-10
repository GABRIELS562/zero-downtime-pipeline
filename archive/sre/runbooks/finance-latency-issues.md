# 🚨 Finance Trading System: High Latency Issues

## 📊 SRE Runbook: Trading Latency >50ms

**Service**: Finance Trading System  
**SLO**: 95% of requests <50ms P95 latency  
**Severity**: High (impacts trading performance and revenue)

---

## 🚦 Immediate Response (0-5 minutes)

### 1. Verify the Alert
```bash
# Check current P95 latency from health endpoint
curl http://finance-trading-service/health/sre

# Verify in Grafana dashboard
# Navigate to: Finance Trading - Latency Dashboard
```

### 2. Assess Business Impact
- **Market Hours (9:30 AM - 4:00 PM EST)**: 🔴 **CRITICAL** - Immediate action required
- **After Hours**: 🟡 **HIGH** - Address within 15 minutes
- **Weekends**: 🟢 **MEDIUM** - Address within 1 hour

### 3. Quick Checks
```bash
# Check system resources
kubectl top pods -n finance-trading

# Check error budget status
python /path/to/sre/error-budgets/budget-calculator.py
```

---

## 🔍 Diagnosis (5-15 minutes)

### Step 1: Database Performance
```bash
# Check database latency
kubectl exec -it postgres-pod -- psql -c "
  SELECT query, mean_time, calls 
  FROM pg_stat_statements 
  ORDER BY mean_time DESC 
  LIMIT 10;"

# Look for:
# - Slow queries (>10ms)
# - High call frequency
# - Missing indexes
```

### Step 2: Application Performance
```bash
# Check application logs for slow operations
kubectl logs -n finance-trading deployment/trading-app | grep "SLOW\|>50ms"

# Check for:
# - Database connection pool exhaustion
# - External API timeouts (Alpha Vantage)
# - Memory/CPU spikes
```

### Step 3: Infrastructure Issues
```bash
# Check pod resource usage
kubectl describe pod -n finance-trading | grep -A 10 "Resource Requests\|Limits"

# Check node performance
kubectl top nodes

# Network latency check
ping postgres-service.finance-trading.svc.cluster.local
```

---

## 🛠 Mitigation Steps

### Option 1: Quick Wins (2-5 minutes)
```bash
# Restart pods to clear memory issues
kubectl rollout restart deployment/trading-app -n finance-trading

# Scale up if CPU/memory constrained
kubectl scale deployment trading-app --replicas=5 -n finance-trading

# Clear Redis cache if stale
kubectl exec redis-pod -- redis-cli FLUSHDB
```

### Option 2: Database Optimization (5-10 minutes)
```sql
-- Kill long-running queries
SELECT pg_cancel_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' AND query_start < NOW() - INTERVAL '30 seconds';

-- Check for blocking locks
SELECT * FROM pg_locks WHERE NOT granted;
```

### Option 3: Circuit Breaker (Emergency)
```bash
# If Alpha Vantage API is slow, force simulation mode
kubectl set env deployment/trading-app MARKET_DATA_PROVIDER=simulation -n finance-trading
```

---

## 📢 Communication

### Internal Notifications
- **Engineering Team**: Slack #trading-alerts
- **Business Team**: Only if >10 minutes during market hours
- **Management**: Only if >30 minutes or revenue impact >$50K

### External Notifications
- **Regulatory**: Not required for latency issues
- **Clients**: If trading orders affected >15 minutes

---

## 📈 Monitoring & Validation

### Verify Resolution
```bash
# Check latency returns to <50ms
curl http://finance-trading-service/health/sre | jq '.latency_p95_ms'

# Monitor error budget consumption
# Should stop increasing once latency is resolved

# Check SLO compliance dashboard
# Navigate to: SRE Error Budget Dashboard
```

### Success Criteria
- ✅ P95 latency <50ms sustained for 5 minutes
- ✅ Error budget burn rate returns to normal
- ✅ No new latency alerts for 15 minutes

---

## 🔄 Follow-up Actions

### Immediate (within 1 hour)
- [ ] Document root cause in incident ticket
- [ ] Update monitoring if gaps identified
- [ ] Review error budget impact

### Short-term (within 1 week)
- [ ] Conduct blameless post-mortem if incident >30 minutes
- [ ] Implement additional monitoring/alerting if needed
- [ ] Review and update this runbook with lessons learned

### Long-term (within 1 month)
- [ ] Consider architectural improvements if recurring
- [ ] Update capacity planning based on patterns
- [ ] Evaluate SLO targets if consistently difficult to meet

---

## 🎯 SRE Learning Notes

**Error Budget Impact**: High latency issues consume error budget quickly during market hours. If budget exhausted, consider deployment freeze until resolution.

**Business Context**: Every millisecond matters in high-frequency trading. 50ms+ latency can result in missed trading opportunities worth thousands of dollars per second.

**Escalation Criteria**: 
- Immediate: >100ms P95 latency during market hours
- 15 minutes: Any latency issue not resolved in timeframe
- 30 minutes: Automatically escalate to on-call manager

---

**Runbook Version**: 1.0  
**Last Updated**: Entry-level SRE implementation  
**Next Review**: After first incident usage