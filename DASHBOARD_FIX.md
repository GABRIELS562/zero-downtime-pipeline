# Dashboard Connection Fix

## Problem
The dashboard was not showing Pharma and Trading app data because:
1. Wrong API endpoints in `dashboard.js` (was using port 8080 instead of 30002/30003)
2. Services status not updating dynamically
3. No proper error handling for offline services

## Solution

### Files Fixed/Created:

1. **`frontend/dashboard-fixed.js`** - New JavaScript file with correct endpoints:
   - Pharma API: `http://localhost:30002`
   - Trading API: `http://localhost:30003`
   - Proper health checks and error handling
   - Dynamic status updates

2. **`frontend/index.html`** - Updated to:
   - Use `dashboard-fixed.js` instead of `dashboard.js`
   - Add dynamic status indicators for both services
   - Show port numbers in the UI
   - Add pharma metrics section

3. **Test & Deployment Scripts**:
   - `test-dashboard-connection.sh` - Test backend connectivity
   - `serve-dashboard.sh` - Serve dashboard on port 30004

## How to Run

### 1. Start Backend Services

```bash
# Build and push images
./build-and-deploy-services.sh

# Or run locally with Docker
docker run -d -p 30002:8000 localhost:5000/pharma-app:production
docker run -d -p 30003:8000 localhost:5000/finance-app:production
```

### 2. Test Connectivity

```bash
./test-dashboard-connection.sh
```

### 3. Serve Dashboard

```bash
./serve-dashboard.sh
# Dashboard will be available at http://localhost:30004
```

## Architecture

```
┌─────────────────────────────────────────┐
│      Dashboard (Port 30004)             │
│         frontend/index.html             │
│      frontend/dashboard-fixed.js        │
└──────────┬──────────────┬───────────────┘
           │              │
     AJAX Calls      AJAX Calls
           │              │
    ┌──────▼──────┐ ┌────▼──────┐
    │ Pharma API  │ │Trading API│
    │ Port 30002  │ │Port 30003 │
    └─────────────┘ └───────────┘
```

## Features

### Dashboard Now Shows:

1. **Real-time Service Status**
   - Green check when services are operational
   - Red X when services are offline
   - Yellow spinner while checking

2. **Pharma Data (Port 30002)**
   - Batch tracking information
   - Equipment status
   - FDA compliance metrics
   - Quality control data

3. **Trading Data (Port 30003)**
   - Live market prices
   - Trading latency metrics
   - Order throughput
   - Portfolio value chart

4. **Automatic Fallback**
   - Uses demo data when services are offline
   - Shows notifications for connection status
   - Continues to retry connections

## API Endpoints Used

### Pharma Service (30002)
- `/` - Service info
- `/health/live` - Health check
- `/api/v1/batches` - Batch data
- `/api/v1/equipment` - Equipment status
- `/api/v1/quality` - Quality metrics

### Trading Service (30003)
- `/` - Service info
- `/health/live` - Health check
- `/api/v1/market` - Market data
- `/api/v1/orders` - Order management
- `/api/v1/portfolio` - Portfolio data

## Troubleshooting

### Dashboard shows "OFFLINE" for services

1. Check services are running:
```bash
curl http://localhost:30002/health/live
curl http://localhost:30003/health/live
```

2. Check Docker containers:
```bash
docker ps | grep -E "pharma|finance"
```

3. Restart services:
```bash
docker restart pharma-test trading-test
```

### CORS Errors

The Flask apps already have CORS enabled via `flask-cors`. If you still see CORS errors:
1. Clear browser cache
2. Use incognito/private browsing
3. Check browser console for specific error

### Tailwind CSS Warning

The warning about Tailwind CDN is informational only and doesn't affect functionality. For production, you should:
1. Install Tailwind via npm
2. Build CSS with PostCSS
3. Or use Tailwind CLI

## Testing

Open browser console and run:
```javascript
// Test connections
testConnections()

// Check service status
console.log('Pharma:', pharmaStatus)
console.log('Trading:', tradingStatus)
```

## Notes

- Services must be running on correct ports (30002, 30003)
- Dashboard automatically polls services every 10 seconds
- Market data updates every 5 seconds
- Metrics update every second
- Both services have CORS enabled for cross-origin requests