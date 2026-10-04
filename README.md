# Private Network Service Platform

A local private network service platform demonstrating **LAN connectivity, private DNS, HTTP/REST backends, reverse proxying, load balancing, HTTPS/TLS, HTTP caching, and packet-level protocol analysis**.

The entire system runs locally on the team's private LAN. No cloud hosting is required.

---

## 1. Project Overview

The project implements the following request flow:

```text
Client
   |
   | DNS Query
   v
Private DNS Server
   |
   | Resolves app.teamX.test
   v
Nginx Edge / Reverse Proxy
   |
   | HTTPS / TLS
   v
Load Balancer
   |
   +-------------------+
   |                   |
   v                   v
Backend A           Backend B
Port 3001           Port 3002
```

The client accesses the service using the private domain name rather than directly using a backend IP address.

---

## 2. Network Architecture

All machines are connected to the same private LAN.

### Machine Roles

| Machine | Role                 | IP Address  | Services                         |
| ------- | -------------------- | ----------- | -------------------------------- |
| Mac 1   | DNS + Test Client    | `10.7.3.71` | dnsmasq, dig, curl               |
| Mac 2   | Edge / Reverse Proxy | `10.7.5.11` | nginx, HTTPS/TLS                 |
| Mac 3   | Backend Server       | `10.7.20.49` | Backend A :3001, Backend B :3002 |

Note : When we reconned the network due to some error, our IPs changed and thus failure test 2, 3 and 5 are done on the new IPs.

### Network

```text
Private LAN: 10.7.3.0/24

Mac 1
DNS + Client
       |
       |
Mac 2
Nginx + HTTPS
       |
       |
Mac 3
Backend A :3001
Backend B :3002
```

---

## 3. Services and Ports

| Service     | Protocol  |        Port |
| ----------- | --------- | ----------: |
| DNS         | UDP       |          53 |
| Backend A   | HTTP/TCP  |        3001 |
| Backend B   | HTTP/TCP  |        3002 |
| Nginx HTTPS | HTTPS/TCP | 443 or 8443 |

If ports 80/443 cannot be used because of local system restrictions, ports 8080/8443 can be used.

---

## 4. Private DNS

The private DNS server runs on Mac 1 using `dnsmasq`.

Required DNS records:

```text
app.team3.test -> 10.7.5.11
api.team3.test -> 10.7.5.11
```

### Verify DNS

```bash
dig app.team3.test
```

or:

```bash
nslookup app.team3.test
```

The returned address should be the private IP address of Mac 2.

---

## 5. Backend Services

Two simple HTTP/REST backend services are provided.

### Backend A

Port:

```text
3001
```

Run:

```bash
./scripts/start_backend_a.sh
```

### Backend B

Port:

```text
3002
```

Run:

```bash
./scripts/start_backend_b.sh
```

Both services listen on:

```text
0.0.0.0
```

so that they can be reached from other machines on the LAN.

---

## 6. Backend Endpoints

### GET /

```bash
curl http://BACKEND_IP:3001/
```

Example response:

```json
{
  "service": "Private Network Service Platform",
  "backend": "A",
  "status": "running"
}
```

### GET /api/status

```bash
curl http://BACKEND_IP:3001/api/status
```

Example:

```json
{
  "backend": "A",
  "status": "ok"
}
```

Backend B provides the same endpoints with:

```json
{
  "backend": "B",
  "status": "ok"
}
```

Each response also contains an `X-Backend` response header.

Example:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

This allows load balancing to be demonstrated clearly.

---

## 7. Nginx Reverse Proxy and Load Balancing

Nginx runs on Mac 2 and acts as the single public entry point.

The client does not directly access the backend servers.

Example upstream configuration:

```nginx
upstream backend_servers {
    server 10.7.20.49:3001;
    server 10.7.20.49:3002;
}
```

Nginx uses round-robin load balancing by default.

The request flow is:

```text
Client
  |
  | HTTPS
  v
app.team3.test
  |
  v
Nginx
  |
  +------> Backend A :3001
  |
  +------> Backend B :3002
```

---

## 8. HTTPS / TLS

TLS terminates at the nginx edge server.

The certificate must cover:

```text
app.team3.test
api.team3.test
```

The client machines should trust the local CA/certificate.

The final demonstration should access the service without bypassing certificate verification.

Do not use:

```bash
curl -k
```

---

## 9. HTTP Caching

The backend returns a cache-control header.

Example:

```text
Cache-Control: max-age=60
```

Check the headers using:

```bash
curl -I https://app.team3.test
```

The response should contain the cache-control header.

The caching demonstration should show either:

* a cache hit, or
* a conditional request returning `304 Not Modified`.

---

## 10. Testing

### Test Backend A

```bash
curl -i http://10.7.20.49:3001/
```

### Test Backend B

```bash
curl -i http://10.7.20.49:3002/
```

### Test DNS

```bash
dig app.team3.test
```

### Test HTTPS

```bash
curl -i https://app.team3.test/
```

### Test status endpoint

```bash
curl -i https://app.team3.test/api/status
```

### Test load balancing

Run multiple requests:

```bash
for i in {1..10}; do
    curl -s -D - https://app.team3.test/api/status -o /dev/null | grep X-Backend
done
```

Expected output should show responses from both:

```text
X-Backend: A
X-Backend: B
X-Backend: A
X-Backend: B
...
```

---

## 11. Packet Capture / Wireshark

Wireshark is used to demonstrate the complete protocol flow.

Important evidence:

### DNS

Filter:

```text
dns
```

Show:

```text
Client -> DNS Server
DNS Query
DNS Response
```

### TCP

Filter:

```text
tcp.port == 443
```

or, if using port 8443:

```text
tcp.port == 8443
```

Show:

```text
SYN
SYN-ACK
ACK
```

### TLS

Filter:

```text
tls
```

Show the TLS handshake, including:

```text
ClientHello
ServerHello
Certificate
Key Exchange
Finished
```

### HTTP

Show HTTP headers and the encrypted application traffic carried over TLS.

---

## 12. Evidence

The `evidence/` directory contains all the screenshots or exported captures for:

```text
evidence/
├── 01_topology.png
├── 02_ip_configuration.png
├── 03_ping_test.png
├── 04_dns_resolution.png
├── 05_backend_a.png
├── 06_backend_b.png
├── 07_nginx_load_balancing.png
├── 08_https_tls.png
├── 09_http_headers_cache.png
├── 10_wireshark_dns.png
├── 11_wireshark_tcp.png
├── 12_wireshark_tls.png
└── 13_load_balancing_results.png
```

Packet captures can also be stored here if required:

```text
*.pcap
*.pcapng
```

---

## 13. Repository Structure

```text
.
├── README.md
│
├── backend/
│   ├── backend_a.py
│   ├── backend_b.py
│   └── requirements.txt
│
├── scripts/
│   ├── start_backend_a.sh
│   ├── start_backend_b.sh
│   └── test_backends.sh
│
├── config/
│   ├── dnsmasq.conf.example
│   ├── nginx.conf.example
│   └── TLS_SETUP.md
│
├── architecture/
│   └── architecture.md
│
└── evidence/
    └── ...
```

---

## 14. Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/vani-max/Team_CN.git
cd Team_CN
```

### 2. Start Backend A

```bash
./scripts/start_backend_a.sh
```

### 3. Start Backend B

Open another terminal:

```bash
./scripts/start_backend_b.sh
```

### 4. Test both backends

```bash
./scripts/test_backends.sh
```

### 5. Configure private DNS

Configure dnsmasq using:

```text
config/dnsmasq.conf.example
```


### 6. Configure nginx

Use:

```text
config/nginx.conf.example
```

### 7. Configure TLS

Follow:

```text
config/TLS_SETUP.md
```

### 8. Test the complete flow

```bash
dig app.team3.test
```

then:

```bash
curl -i https://app.team3.test/api/status
```

---

## 15. Troubleshooting

### DNS does not resolve

Check:

```bash
dig app.team3.test
```

Then verify that:

* dnsmasq is running
* the client is using the correct DNS server
* the DNS record points to the nginx/edge IP
* all machines are on the same LAN

### Backend cannot be reached

Check:

```bash
curl http://10.7.20.49:3001/
curl http://10.7.20.49:3002/
```

Check that the backend is listening:

```bash
lsof -i :3001
lsof -i :3002
```

### Nginx cannot reach backend

Check direct connectivity from Mac 2:

```bash
curl http://10.7.20.49:3001/
curl http://10.7.20.49:3002/
```

Then inspect the nginx configuration and logs.

### HTTPS certificate warning

Verify that:

* the certificate contains the correct domain name
* the certificate/CA is trusted by the client
* nginx is using the correct certificate and private key
* the client is accessing the domain name rather than the IP address

### Load balancing only shows one backend

Check the nginx upstream:

```nginx
upstream backend_servers {
    server 10.7.20.49:3001;
    server 10.7.20.49:3002;
}
```

Then send multiple requests and inspect:

```text
X-Backend
```
---

## 17. Team Members

| Name     | Role / Contribution |
| -------- | ------------------- |
| Pranavi | DNS / Network       |
| Bhoomi | Nginx / TLS         |
| Vani | Backend / Testing   |

---
