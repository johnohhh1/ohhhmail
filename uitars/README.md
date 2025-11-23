# UI-TARS

**U**niversal **I**ntelligent **T**elemetry and **A**gent **R**eporting **S**ystem

Real-time monitoring dashboard for AI agent execution workflows. Built with React and TypeScript, UI-TARS provides deep visibility into agent decision-making, execution flow, and system performance.

## Features

- **Real-time WebSocket Updates**: Live connection to Dolphin orchestration service
- **Execution Timeline**: Step-by-step visualization of workflow progress
- **Agent Decision Tracking**: View reasoning, confidence scores, and tool usage
- **Screenshot Capture**: Visual artifacts from each execution step
- **DAG Visualization**: Interactive workflow graph with ReactFlow
- **Structured Logging**: Filterable, searchable execution logs
- **Statistics Dashboard**: Success rates, active executions, performance metrics

## Architecture

```
UI-TARS (React)
    ↓ WebSocket
Dolphin Service (Go)
    ↓ Events
Agent Workflows (n8n/custom)
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Running Dolphin service instance

### Installation

```bash
# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Configure Dolphin connection in .env
# REACT_APP_WS_URL=ws://your-dolphin-service:8080/ws
```

### Development

```bash
# Start development server
npm start

# Open http://localhost:3000
```

The app will automatically connect to the Dolphin WebSocket endpoint and start displaying execution data.

### Production Build

```bash
# Build optimized production bundle
npm run build

# Build Docker image
docker build -t uitars:latest .

# Run container
docker run -p 80:80 \
  -e REACT_APP_WS_URL=ws://dolphin-service:8080/ws \
  uitars:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_WS_URL` | `ws://localhost:8080/ws` | Dolphin WebSocket endpoint |
| `REACT_APP_API_URL` | `http://localhost:8080/api` | Dolphin REST API endpoint |
| `REACT_APP_WS_RECONNECT_INTERVAL` | `3000` | Reconnection delay (ms) |
| `REACT_APP_WS_MAX_RECONNECT` | `10` | Max reconnection attempts |
| `REACT_APP_MAX_EXECUTIONS` | `100` | Max executions to display |
| `REACT_APP_DEBUG` | `false` | Enable debug logging |

### WebSocket Protocol

UI-TARS expects Dolphin to send JSON messages in this format:

```typescript
{
  "type": "execution_started" | "step_completed" | "decision_made" | ...,
  "timestamp": "2025-01-15T10:30:00Z",
  "execution_id": "exec_abc123",
  "data": { ... }
}
```

See `src/types.ts` for complete protocol definitions.

## Project Structure

```
uitars/
├── public/
│   ├── index.html          # HTML template
│   └── manifest.json       # PWA manifest
├── src/
│   ├── App.tsx            # Main app with WebSocket logic
│   ├── UITARSPanel.tsx    # Dashboard layout and controls
│   ├── ExecutionDetail.tsx # Timeline and detail view
│   ├── WorkflowGraph.tsx  # DAG visualization
│   ├── types.ts           # TypeScript definitions
│   ├── config.ts          # Configuration management
│   └── *.css             # Component styles
├── Dockerfile             # Production container
├── nginx.conf            # Nginx configuration
└── package.json          # Dependencies
```

## Features in Detail

### Timeline View

- Chronological display of execution steps
- Visual indicators for status (running, completed, failed)
- Agent decision cards with confidence scores
- Screenshot gallery with lightbox modal
- Structured log viewer

### Graph View

- Interactive DAG visualization using ReactFlow
- Real-time status updates on nodes
- Zoom, pan, minimap controls
- Color-coded execution flow

### Logs View

- Aggregated logs from all steps
- Filterable by level (error, warning, info, debug)
- Timestamped entries with context
- Search functionality

### Connection Monitoring

- Live connection status indicator
- Automatic reconnection with exponential backoff
- Manual reconnect option
- Error state handling

## Development

### Tech Stack

- **React 18**: Component framework
- **TypeScript**: Type safety
- **ReactFlow**: Graph visualization
- **Recharts**: Statistics charts
- **date-fns**: Date formatting

### Code Style

```bash
# Lint code
npm run lint

# Format code
npm run format
```

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  uitars:
    image: uitars:latest
    ports:
      - "80:80"
    environment:
      - REACT_APP_WS_URL=ws://dolphin:8080/ws
    depends_on:
      - dolphin

  dolphin:
    image: dolphin:latest
    ports:
      - "8080:8080"
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uitars
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: uitars
        image: uitars:latest
        env:
        - name: REACT_APP_WS_URL
          value: "ws://dolphin-service:8080/ws"
        ports:
        - containerPort: 80
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 14+

## Performance

- Bundle size: ~500KB gzipped
- Initial load: <2s on fast 3G
- Real-time updates: <100ms latency
- Supports 1000+ executions with virtual scrolling

## Troubleshooting

### WebSocket Connection Issues

1. Check Dolphin service is running and accessible
2. Verify `REACT_APP_WS_URL` in `.env`
3. Check browser console for connection errors
4. Ensure no CORS/proxy issues

### Missing Data

1. Verify Dolphin is sending correct message format
2. Check browser console for parsing errors
3. Enable `REACT_APP_DEBUG=true` for verbose logging

## License

MIT

## Contributing

Pull requests welcome! Please ensure:
- TypeScript compilation passes
- ESLint shows no errors
- All tests pass
- Code is formatted with Prettier

## Roadmap

- [ ] Real-time metrics dashboard
- [ ] Export execution data (JSON, CSV)
- [ ] Agent performance analytics
- [ ] Custom workflow templates
- [ ] Mobile-responsive design
- [ ] Dark/light theme toggle
- [ ] Execution playback mode
