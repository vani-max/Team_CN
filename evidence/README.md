# Project Evidence Directory

This directory contains experimental and verification evidence across Phase 1 and Phase 2 of the Private Network Service Platform project.

---

## 1. Network Connectivity (`network/`)
- **`01_lan_ping_test.png`**: LAN reachability test from Mac 1 (`10.7.2.89`) pinging Mac 2 (`10.7.28.46`) and Mac 3 (`10.7.25.37`) with 0.0% packet loss.

---

## 2. Private DNS Resolution (`dns/`)
- **`01_dns_resolution.png`**: Client DNS queries for `app.team1.test` and `api.team1.test` resolving to Mac 2 (`10.7.28.46`) via primary DNS server (`10.7.2.89`).

---

## 3. Backend Services (`backend/`)
- **`01_backend_direct_test.png`**: Direct local testing of Backend A (port 3001) and Backend B (port 3002) verifying individual service JSON responses.
- **`02_load_balancing_http.jpg`**: Round-robin HTTP load balancing alternating responses between Backend A and Backend B via Nginx proxy.

---

## 4. Nginx Edge Reverse Proxy (`nginx/`)
- **`01_nginx_syntax_and_start.jpg`**: Validating Nginx configuration syntax (`nginx -t`) and starting Nginx service on Mac 2.
- **`02_nginx_http_proxy_check.jpg`**: Testing Nginx edge reverse proxy on port 8080 forwarding client requests to backend services.

---

## 5. HTTP Caching (`caching/`)
- **`01_http_caching_etag_304.png`**: HTTP caching demonstration showing initial `200 OK` with `Cache-Control`/`ETag` and subsequent conditional `304 Not Modified` response.

---

## 6. HTTPS / TLS Termination (`tls/`)
- **`01_https_tls_verification.png`**: Verifying secure HTTPS communication and TLS termination on port 8443 (`https://app.team1.test:8443/api/status`).
- **`02_https_load_balancing_recovered.jpg`**: End-to-end HTTPS load balancing alternating across both Backend A and Backend B after restoring service.
- **`03_openssl_tls_cert_verify.png`**: OpenSSL `s_client` TLS handshake and certificate examination showing `CN = app.team1.test` and self-signed certificate identification (code 18).

---

## 7. Phase 2 Resilience & Hardening (`resilience/`)
- **`01_backup_dns_resolver_query.png`**: *Extension A* — Direct client DNS resolution of `app.team1.test` using backup DNS resolver on Mac 2 (`10.7.28.46`).
- **`02_dual_dns_resolvers_verified.jpg`**: *Extension A* — Dual DNS verification confirming consistent resolution from both backup DNS (`10.7.28.46`) and primary DNS (`10.7.2.89`).
- **`03_dns_ttl_record_change.jpg`**: *Extension B* — Demonstrating DNS TTL (30s) observation and controlled record change from client.
- **`04_firewall_rules_backup.jpg`**: *Extension C* — Backing up macOS packet filter rules (`/etc/pf.conf`) and checking firewall status.
- **`05_service_isolation_enforced.png`**: *Extension C* — Demonstrating backend port isolation: direct client access to ports 3001/3002 times out while HTTPS edge proxy access succeeds.
- **`06_ha_failover_single_backend.jpg`**: *Extension D* — High-availability failover: Backend A is down and Nginx seamlessly serves all traffic via healthy Backend B.
- **`07_controlled_edge_cutover.jpg`**: *Extension E* — Controlled edge migration: Updating DNS record in dnsmasq and restarting service to cut over traffic to new edge IP.
- **`08_primary_dns_stopped.png`**: *Extension A* — Stopping primary DNS service (`brew services stop dnsmasq` on Mac 1) to test resolver failover.
- **`09_dns_failover_query.png`**: *Extension A* — Client query for `app.team1.test` during failover scenario.

---

## 8. Packet Analysis (`wireshark/`)
*(Preserved existing captures)*
- **`dns_capture.jpeg`**: DNS query and response packets.
- **`TCP_Handshake.jpeg`**: TCP SYN, SYN-ACK, ACK 3-way handshake.
- **`TLS_handshake.jpeg`**: TLS handshake and encrypted application data.

---

## 9. Failure Demonstrations (`failures/`)
*(Preserved existing failure scenarios)*
- Controlled failure scenarios across DNS, service ports, and backend availability.
