"""
Phase 20 - Production Deployment Verification Test Suite
Validates health checks, readiness probes, metrics, security headers, CORS,
environment variable sanitization, and clean startup.
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError

from app.main import app
from app.core.config import settings

client = TestClient(app)


class TestDeploymentHealthAndReadiness:
    """Validates orchestrator probes (liveness, readiness, metrics)."""

    def test_liveness_probe_health(self):
        """GET /health must return HTTP 200 with valid service health metadata."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "foodloop-backend"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data
        assert "environment" in data

    def test_liveness_probe_health_v1_alias(self):
        """GET /api/v1/health must return HTTP 200 matching root liveness probe."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_probe_ready_success(self):
        """GET /ready must return HTTP 200 when database connectivity is verified."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "dialect" in data
        assert data["checks"]["database"] == "pass"

    def test_readiness_probe_ready_v1_alias(self):
        """GET /api/v1/ready must return HTTP 200 matching root readiness probe."""
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_readiness_probe_failure_returns_503(self):
        """GET /ready must return HTTP 503 SERVICE UNAVAILABLE when database is down."""
        mock_db = MagicMock()
        mock_db.execute.side_effect = OperationalError("connection refused", {}, None)

        from app.core.database import get_db
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["database"] == "disconnected"
            assert data["checks"]["database"] == "fail"
            assert "error" in data
        finally:
            app.dependency_overrides.clear()

    def test_metrics_endpoint_prometheus_format(self):
        """GET /metrics must return HTTP 200 with Prometheus gauge lines."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        text = response.text
        assert "foodloop_app_uptime_seconds" in text
        assert "foodloop_service_status" in text


class TestDeploymentSecurityAndHeaders:
    """Validates HTTP security headers, CORS policies, and HTTPS proxy handling."""

    def test_security_headers_present(self):
        """Responses must include modern security headers (HSTS, CSP, X-Frame, nosniff)."""
        response = client.get("/health")
        assert response.status_code == 200
        headers = response.headers
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("x-xss-protection") == "1; mode=block"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in headers.get("content-security-policy", "")
        assert "max-age=" in headers.get("strict-transport-security", "")

    def test_cors_preflight_allowed_origin(self):
        """Preflight OPTIONS request from configured origin must return 200 with CORS headers."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type"
        }
        response = client.options("/api/v1/health", headers=headers)
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_preflight_disallowed_origin(self):
        """Preflight OPTIONS request from unknown origin must not return allow-origin header."""
        headers = {
            "Origin": "https://malicious-attacker-website.com",
            "Access-Control-Request-Method": "GET"
        }
        response = client.options("/api/v1/health", headers=headers)
        assert response.headers.get("access-control-allow-origin") is None

    def test_https_redirection_under_production_proxy(self):
        """In production environment, requests with X-Forwarded-Proto: http must redirect to https."""
        with patch.object(settings, "ENVIRONMENT", "production"):
            prod_client = TestClient(app)
            response = prod_client.get(
                "/health",
                headers={"X-Forwarded-Proto": "http"},
                follow_redirects=False
            )
            assert response.status_code == 308
            assert response.headers.get("location", "").startswith("https://")


class TestSecretHygieneAndEnvironmentSanitization:
    """Ensures no real secrets, passwords, or production credentials are leaked in templates."""

    def test_env_example_has_no_real_passwords(self):
        """Verify root .env.example contains only sanitized placeholders."""
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        example_path = os.path.join(root_path, ".env.example")
        assert os.path.exists(example_path), ".env.example must exist at root"
        with open(example_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "your_strong_password" in content or "your-db-password" in content or "password" in content
        assert "Sih%4026234" not in content, "Real database password found in .env.example!"
        assert "sb_publishable_KOX8cTLR2U2fv4k3VsTxhA_EvH1QNcN" not in content

    def test_infrastructure_env_template_sanitized(self):
        """Verify infrastructure/.env.template is strictly sanitized."""
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(root_path, "infrastructure", ".env.template")
        assert os.path.exists(template_path), "infrastructure/.env.template must exist"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Sih%4026234" not in content, "Real database password found in infrastructure/.env.template!"
        assert "sb_publishable_KOX8cTLR2U2fv4k3VsTxhA_EvH1QNcN" not in content

    def test_docker_compose_files_exist_and_valid(self):
        """Verify root Dockerfile and docker-compose.yml exist and contain required services."""
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dockerfile = os.path.join(root_path, "Dockerfile")
        compose = os.path.join(root_path, "docker-compose.yml")

        assert os.path.exists(dockerfile), "Root Dockerfile must exist"
        assert os.path.exists(compose), "Root docker-compose.yml must exist"

        with open(compose, "r", encoding="utf-8") as f:
            compose_content = f.read()

        assert "postgis" in compose_content
        assert "backend" in compose_content
        assert "frontend" in compose_content
        assert "/health" in compose_content
