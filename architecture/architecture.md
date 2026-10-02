# Network Architecture

## Physical Machines

| Machine | Role | IP Address | Services |
|---|---|---|---|
| Mac 1 | DNS + Client | 10.7.3.71 | dnsmasq, dig, curl |
| Mac 2 | Edge / Reverse Proxy | 10.7.5.11 | nginx, HTTPS/TLS |
| Mac 3 | Backend Server | 10.7.20.49 | Backend A :3001, Backend B :3002 |

## Request Flow

Client
  ↓
DNS Query
  ↓
Mac 1 - dnsmasq
  ↓
app.teamX.test → Mac 2 IP
  ↓
Mac 2 - nginx
  ↓
Load Balancing
  ↓
Mac 3 - Backend A :3001
       OR
Mac 3 - Backend B :3002
  ↓
Response
