# Employee Portal — Corporate HR System

Demo target repository for ThreatGPT. This is a deliberately vulnerable FastAPI application
used to demonstrate SAST/DAST webhook integration and threat model generation.

## ⚠️ WARNING
This codebase contains intentional security vulnerabilities for demonstration purposes.
Do NOT deploy this to any real environment.

## Structure

```
employee-portal/
├── auth_service/         # JWT auth — CWE-798, CWE-522
├── employee_api/         # Employee endpoints — CWE-89
├── upload_service/       # File handling — CWE-434, CWE-639
├── admin_api/            # Admin operations — CWE-306
├── notification_service/ # RabbitMQ → SendGrid
└── infra/                # docker-compose, semgrep config
```

## Running Locally

```bash
docker-compose -f infra/docker-compose.yml up
```

Services start on:
- API Gateway (Kong): http://localhost:8000
- Auth Service: http://localhost:8001
- Employee API: http://localhost:8002
- File Upload Service: http://localhost:8003
- Admin API: http://localhost:8004
- Admin Dashboard: http://localhost:4000

## Running SAST and Sending to ThreatGPT Webhook

```bash
# Install semgrep
pip install semgrep

# Run scan and send to ThreatGPT
cd infra
chmod +x run_sast_webhook.sh
./run_sast_webhook.sh
```

Set your ThreatGPT webhook URL in infra/.env before running.

## Intentional Vulnerabilities

| CWE | Location | Description |
|-----|----------|-------------|
| CWE-89 | employee_api/views.py:142 | SQL injection on payroll endpoint |
| CWE-434 | upload_service/handlers.py:67 | Unrestricted file upload |
| CWE-639 | upload_service/handlers.py:89 | IDOR on file download |
| CWE-798 | auth_service/config.py:9 | Hardcoded JWT secret |
| CWE-522 | auth_service/token_store.py:41 | Unauthenticated Redis token storage |
| CWE-306 | admin_api/routes.py:203 | Missing role check on payroll approval |


test commits
yalla beena 
