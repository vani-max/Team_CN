# Private Network Service Platform

A local private network service platform demonstrating **LAN connectivity, private DNS, HTTP/REST backends, reverse proxying, round-robin load balancing, HTTPS/TLS termination, HTTP caching, protocol analysis, and resilient Phase 2 hardening (DNS failover, TTL cutover, service isolation firewall, and HA backend failover)**.

> **Core Principle:** *The application stays simple; the network is the project.*

---

## 1. Project Overview & Request Flow

The platform implements an end-to-end request journey across multiple physical macOS machines on a local area network without any cloud hosting or pre-configured services:

```text
Client (Mac 1 / Mac 3)
   │
   │  1. DNS Query (app.team1.test / api.team1.test)
   ▼
Primary DNS Server (Mac 1 :53)  ──[Failover]──►  Backup DNS Server (Mac 2 :53)
   │
   │  Resolves to Mac 2 IP (10.7.28.46)
   ▼
Nginx Edge Reverse Proxy (Mac 2 :8443)
   │
   │  2. HTTPS / TLS Termination & HTTP Caching Check
   │  3. Round-Robin Load Balancing
   ▼
Upstream Backend Cluster (Mac 3)
   ├──► Backend A (Port 3001)
   └──► Backend B (Port 3002)
   │
   ▼  [Service Isolation: Firewall / pf blocks direct client access; only Mac 2 allowed]
Response returned to Client with X-Backend, ETag, and Cache-Control headers
```

---

## 2. Team Architecture & Machine Roles

All machines are connected to the same private LAN (`10.7.0.0/19`, netmask `255.255.224.0`).

| Machine | Member | IP Address | Primary Roles | Key Services & Tools |
| :--- | :--- | :--- | :--- | :--- |
| **Mac 1** | **Vani** | `10.7.2.89` | Primary DNS Server + Test Client | `dnsmasq` (Port 53), `dig`, `curl`, Wireshark |
| **Mac 2** | **Bhoomi** | `10.7.28.46` | Edge Proxy, Load Balancer, TLS, Backup DNS | `nginx` (Port 8443 / 8080), OpenSSL, Backup `dnsmasq` |
| **Mac 3** | **Pranavi** | `10.7.25.37` | Backend Application Server + Test Client | `server.py` (Ports 3001 & 3002), `pf` Firewall |

---

## 3. Network Ports & Services

| Service | Host | Protocol | Port | Description |
| :--- | :--- | :--- | :---: | :--- |
| **Primary DNS** | Mac 1 (`10.7.2.89`) | UDP / TCP | `53` | Local DNS resolver (`dnsmasq`) |
| **Backup DNS** | Mac 2 (`10.7.28.46`) | UDP / TCP | `53` | Phase 2 secondary DNS resolver |
| **Edge HTTPS** | Mac 2 (`10.7.28.46`) | HTTPS / TCP | `8443` | TLS termination & Reverse Proxy (`nginx`) |
| **Edge HTTP** | Mac 2 (`10.7.28.46`) | HTTP / TCP | `8080` | Alternate unencrypted HTTP proxy |
| **Backend A** | Mac 3 (`10.7.25.37`) | HTTP / TCP | `3001` | Unified Python HTTP backend instance A |
| **Backend B** | Mac 3 (`10.7.25.37`) | HTTP / TCP | `3002` | Unified Python HTTP backend instance B |

---

## 4. Phase 1: Core Network Build & Observation

### 4.1 Private LAN Connectivity
- Machines verify direct layer 3 reachability using `ping` across all pairs with 0% packet loss.
- Subnet mask `255.255.224.0` (`/19`) provides a unified broadcast domain across `10.7.0.0` to `10.7.31.255`.

### 4.2 Private DNS Configuration
Mac 1 runs `dnsmasq` configured with:
```text
address=/app.team1.test/10.7.28.46
address=/api.team1.test/10.7.28.46
```
Client machines set their primary DNS resolver to `10.7.2.89` and verify resolution:
```bash
dig app.team1.test
nslookup api.team1.test
```

### 4.3 Unified Backend Service (`backend/server.py`)
A single, modular HTTP service handles both Backend A and Backend B based on command-line arguments:
```bash
# Backend A (Port 3001)
python3 backend/server.py A 3001

# Backend B (Port 3002)
python3 backend/server.py B 3002
```
Or using the provided helper scripts:
```bash
./scripts/start_backend_a.sh
./scripts/start_backend_b.sh
```

**Endpoints:**
- `GET /`: Returns running status message.
- `GET /api/status`: Returns JSON object `{"backend": "A"|"B", "status": "ok", "message": "Hello from Backend ..."}` with headers:
  - `X-Backend: A` or `X-Backend: B`
  - `Cache-Control: max-age=60`
  - `ETag: "<md5-hash>"`

### 4.4 Nginx Reverse Proxy & Load Balancing
Mac 2 runs `nginx` as the sole public gateway. Clients never connect directly to Mac 3.
```nginx
upstream backend_servers {
    server 10.7.25.37:3001;
    server 10.7.25.37:3002;
}

server {
    listen 8443 ssl;
    server_name app.team1.test api.team1.test;

    ssl_certificate /path/to/server.crt;
    ssl_certificate_key /path/to/server.key;

    location / {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
**Verification:**
```bash
for i in {1..10}; do
    curl -s -D - https://app.team1.test:8443/api/status -o /dev/null | grep X-Backend
done
```
Responses alternate cleanly between `X-Backend: A` and `X-Backend: B`.

### 4.5 HTTPS / TLS Termination
- Self-signed TLS certificate generated with `CN = app.team1.test` and Subject Alternative Names (`app.team1.test`, `api.team1.test`).
- TLS terminates on Mac 2 at port 8443; traffic between Mac 2 and Mac 3 travels over the secure private LAN.
- Verification command without bypassing certificate validation:
```bash
openssl s_client -connect app.team1.test:8443 -servername app.team1.test
```

### 4.6 HTTP Caching & Conditional Requests
- The backend serves `Cache-Control: max-age=60` and MD5-based `ETag`.
- Subsequent client requests passing `If-None-Match: <etag>` receive an immediate `HTTP/1.0 304 Not Modified`, preventing redundant payload re-transmission:
```bash
curl -i -H 'If-None-Match: "909c27cbe41158a3769253e22fb3581b"' http://10.7.25.37:3002/api/status
```

### 4.7 Protocol Packet Flow (Wireshark)
Packet evidence collected for:
1. **DNS:** UDP port 53 query and `A` record response.
2. **TCP:** Three-way handshake (`SYN` → `SYN-ACK` → `ACK`) on port 8443.
3. **TLS:** `ClientHello` → `ServerHello` → `Certificate` → `Key Exchange` → `Application Data` (encrypted payload).

---

## 5. Phase 2: Resilience, Hardening & Recovery

### Extension A: Backup DNS Resolver & Failover
- **Setup:** A second DNS resolver is configured on Mac 2 (`10.7.28.46`) with the identical zone records for `team1.test`.
- **Client Configuration:** Clients list Mac 1 (`10.7.2.89`) as primary DNS and Mac 2 (`10.7.28.46`) as secondary DNS.
- **Failover Test:** Stop primary DNS on Mac 1 (`brew services stop dnsmasq`). Clients seamlessly continue resolving `app.team1.test` through Mac 2 without interruption.

### Extension B: DNS TTL & Controlled Record Change
- **Setup:** Short TTL of `30` seconds configured in `dnsmasq.conf`:
  ```text
  address=/app.team1.test/10.7.25.37
  ```
- **Test:** Client resolves domain and observes `TTL: 30`. Record is updated to `10.7.28.46`. Client re-queries and demonstrates that cached entry expires after 30s before cutover to the new IP occurs.

### Extension C: Service Isolation (Backend Firewall Rules)
- **Objective:** Prevent clients on the LAN from bypassing the edge proxy and accessing backend ports directly.
- **Implementation:** Packet filter (`pf`) on Mac 3 (`/etc/pf.conf`) configured to allow incoming connections on ports 3001/3002 *only* from Mac 2 (`10.7.28.46`), blocking all other client IPs.
- **Verification:**
  ```bash
  # From Client (Mac 1) - Direct access is blocked:
  curl --connect-timeout 3 http://10.7.25.37:3001/api/status   # Result: Connection timed out
  curl --connect-timeout 3 http://10.7.25.37:3002/api/status   # Result: Connection timed out

  # From Client (Mac 1) - Access via Edge Proxy succeeds:
  curl https://app.team1.test:8443/api/status                  # Result: 200 OK via Mac 2
  ```

### Extension D: High-Availability Failover Behavior
- **Setup:** Nginx upstream passively monitors backend health.
- **Failure Injection:** Backend A is stopped on Mac 3 (`kill <pid>`).
- **Observation:** Nginx automatically detects Backend A is unavailable and routes 100% of incoming requests to Backend B without returning 502 errors to clients.
- **Recovery:** Backend A is restarted; round-robin balancing automatically resumes alternating between `A` and `B`.

### Extension E: Controlled Edge Migration (DNS Cutover)
- A standby edge configuration is staged.
- The DNS record for `app.team1.test` is dynamically switched from the primary edge to the standby edge IP.
- Demonstrates zero-downtime traffic cutover adhering to DNS TTL caching behavior.

---

## 6. Failure Demonstration & Diagnostic Layer Isolation

| Failure Scenario | How to Inject | Expected Observation | Protocol Layer Isolated |
| :--- | :--- | :--- | :--- |
| **Wrong DNS server configured** | Set client DNS to `8.8.8.8` or invalid IP | Name lookup fails (`NXDOMAIN` or timeout); `ping` by IP still succeeds | **Application / DNS Layer** (proves DNS is independent of IP connectivity) |
| **DNS points to wrong IP** | Set DNS record to non-existent IP | Name resolves, but TCP connection fails / times out | **DNS vs Transport Layer** (proves DNS is only a directory, not a connection) |
| **One backend stopped** | Terminate Backend A process on Mac 3 | Requests continue seamlessly via Backend B (`X-Backend: B`) | **Application Upstream Layer** (proves HA load balancer failover) |
| **Both backends stopped** | Terminate both Backend A & B | DNS and TLS handshake succeed, but Nginx returns `502 Bad Gateway` | **Transport/TLS vs Application Layer** (isolates edge termination from upstream origin) |
| **Wrong destination port** | Connect client to `https://app.team1.test:9999` | Host IP reachable via ping, but TCP connection refused | **Transport Layer / Port Identification** (proves socket pairs require matching ports) |

---

## 7. Final Demonstration Sequence (11 Evaluation Steps)

| # | Demonstration Step | Evaluator Check & Action | Verification Command / Target |
| :-: | :--- | :--- | :--- |
| **1** | **Show topology & IP inventory** | Present architecture diagram & IP allocation table | Section 2 table; Mac 1, 2, 3 roles |
| **2** | **Confirm LAN reachability** | Ping all machines from one another (0% packet loss) | `ping -c 3 10.7.28.46`, `ping -c 3 10.7.25.37` |
| **3** | **Resolve private domain** | Query `app.team1.test` using private DNS | `dig app.team1.test` (resolves to `10.7.28.46`) |
| **4** | **Open service over HTTPS** | Connect via domain name over HTTPS | `curl https://app.team1.test:8443/api/status` |
| **5** | **Show load balancing** | Repeated requests showing alternating backends | Loop checking `X-Backend: A` and `X-Backend: B` |
| **6** | **Wireshark evidence** | Inspect DNS, TCP 3-way handshake, and TLS packets | Open Wireshark packet captures in `evidence/wireshark/` |
| **7** | **HTTP headers & caching** | Demonstrate `Cache-Control`, `ETag`, and `304 Not Modified` | `curl -i -H "If-None-Match: ..." <url>` |
| **8** | **Fail one backend** | Stop Backend A; verify service continues via Backend B | `curl` shows `X-Backend: B` exclusively |
| **9** | **Phase 2 resilience demo** | Show backup DNS failover, TTL, or firewall isolation | Evidence in `evidence/resilience/` |
| **10** | **Diagnose faculty fault** | Faculty injects fault; team diagnoses layer by layer | DNS check → TCP ping/port check → TLS check → App logs |
| **11** | **Individual viva** | Answer protocol-level viva questions independently | End-to-end architecture & theoretical knowledge |

---

## 8. Project Evidence Catalog

All verification screenshots are cataloged in [evidence/README.md](evidence/README.md):

```text
evidence/
├── network/
│   └── 01_lan_ping_test.png                  # Multi-machine LAN ping test (0% loss)
├── dns/
│   └── 01_dns_resolution.png                 # dig queries for app.team1.test & api.team1.test
├── backend/
│   ├── 01_backend_direct_test.png            # Direct local verification of ports 3001 & 3002
│   └── 02_load_balancing_http.jpg            # Round-robin alternating responses (ports 8080)
├── nginx/
│   ├── 01_nginx_syntax_and_start.jpg         # nginx -t syntax validation and service start
│   └── 02_nginx_http_proxy_check.jpg         # Nginx edge reverse proxy verification
├── caching/
│   └── 01_http_caching_etag_304.png          # Conditional request returning 304 Not Modified
├── tls/
│   ├── 01_https_tls_verification.png         # HTTPS query to port 8443
│   ├── 02_https_load_balancing_recovered.jpg # HTTPS load balancing after recovery
│   └── 03_openssl_tls_cert_verify.png        # OpenSSL s_client TLS handshake & CN validation
├── resilience/
│   ├── 01_backup_dns_resolver_query.png      # Extension A: Direct query to backup DNS
│   ├── 02_dual_dns_resolvers_verified.jpg    # Extension A: Verification across both resolvers
│   ├── 03_dns_ttl_record_change.jpg          # Extension B: TTL (30s) observation & record change
│   ├── 04_firewall_rules_backup.jpg          # Extension C: pf.conf backup & pfctl inspection
│   ├── 05_service_isolation_enforced.png     # Extension C: Firewall blocks direct access; proxy works
│   ├── 06_ha_failover_single_backend.jpg     # Extension D: Failover to Backend B when A is stopped
│   ├── 07_controlled_edge_cutover.jpg        # Extension E: Dynamic edge IP migration
│   ├── 08_primary_dns_stopped.png            # Extension A: Stopping primary DNS on Mac 1
│   └── 09_dns_failover_query.png             # Extension A: Resolver failover resolution
├── wireshark/
│   ├── dns_capture.jpeg                      # Packet capture: DNS query & answer
│   ├── TCP_Handshake.jpeg                    # Packet capture: SYN, SYN-ACK, ACK sequence
│   └── TLS_handshake.jpeg                    # Packet capture: ClientHello, Certificate, TLS record
└── failures/
    ├── BackendA_Failure.png                  # Controlled failure test: Backend down
    ├── DNS_Failure.png                       # Controlled failure test: NXDOMAIN / Timeout
    ├── Failure_2.png                         # Controlled failure test: Port refusal
    ├── failure_4.jpeg                        # Controlled failure test: Network interface down
    └── Failure_5.png                         # Controlled failure test: 502 Bad Gateway
```

---

## 9. Repository Structure

```text
.
├── README.md                          # Complete project documentation (Phase 1 & 2)
│
├── architecture/
│   ├── architecture.md                # Network topology, IP tables, and service flow
│   └── topology_D.png                 # Network architecture topology diagram
│
├── backend/
│   ├── server.py                      # Unified HTTP backend application (A & B)
│   └── requirements.txt               # Dependencies (uses Python standard library)
│
├── config/
│   ├── dnsmasq.conf.example           # Example DNS zone configuration for team1.test
│   ├── nginx.conf.example             # Example Nginx reverse proxy, TLS & load balancing config
│   └── TLS_SETUP.md                   # Instructions for certificate generation and CA trust
│
├── scripts/
│   ├── start_backend_a.sh             # Launches Backend A on port 3001
│   ├── start_backend_b.sh             # Launches Backend B on port 3002
│   └── test_backends.sh               # Local test suite for backend endpoints
│
└── evidence/
    ├── README.md                      # Index of all verification screenshots and captions
    ├── network/                       # LAN ping tests
    ├── dns/                           # Private DNS resolution
    ├── backend/                       # Backend endpoints & local tests
    ├── nginx/                         # Reverse proxy configuration
    ├── caching/                       # HTTP 304 and cache-control headers
    ├── tls/                           # TLS handshake & HTTPS verification
    ├── resilience/                    # Phase 2 hardening (Extensions A, B, C, D, E)
    ├── wireshark/                     # Protocol flow packet captures
    └── failures/                      # Layer failure demonstration screenshots
```

---

## 10. Quick Start & Execution Guide

### Step 1: Start Backends (Mac 3 - `10.7.25.37`)
```bash
# Terminal 1 - Backend A
./scripts/start_backend_a.sh

# Terminal 2 - Backend B
./scripts/start_backend_b.sh

# Verify locally
./scripts/test_backends.sh
```

### Step 2: Configure & Start DNS (Mac 1 - `10.7.2.89`)
```bash
# Copy configuration and start dnsmasq
sudo cp config/dnsmasq.conf.example $(brew --prefix)/etc/dnsmasq.conf
sudo brew services start dnsmasq
```

### Step 3: Configure & Start Nginx Edge (Mac 2 - `10.7.28.46`)
```bash
# Verify configuration syntax and start Nginx
nginx -t
sudo brew services start nginx
```

### Step 4: Verify Full Flow from Client (Mac 1 or Mac 3)
```bash
# 1. Resolve domain
dig app.team1.test

# 2. Access service over HTTPS
curl -i https://app.team1.test:8443/api/status

# 3. Verify load balancing across backends
for i in {1..6}; do
    curl -s -D - https://app.team1.test:8443/api/status -o /dev/null | grep X-Backend
done
```
