# Network Architecture

## Physical Machines

| Machine | Role | IP Address | Services |
|---|---|---|---|
| Mac 1 (Vani) | DNS + Client | 10.7.2.89 | dnsmasq, dig, curl |
| Mac 2 (Bhoomi) | Edge / Reverse Proxy | 10.7.28.46 | nginx, HTTPS/TLS |
| Mac 3 (Pranavi) | Backend Server | 10.7.25.37 | Backend A :3001, Backend B :3002 |

## Request Flow

Client
  ↓
DNS Query
  ↓
Mac 1 - dnsmasq
  ↓
app.team1.test → Mac 2 IP
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
