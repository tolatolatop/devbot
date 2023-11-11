#!/usr/bin/env python

"""Tests for `devbot` package."""

import pytest
from .data.repo import webhook_test_data


@pytest.fixture
def client():
    from devbot import devbot
    from fastapi.testclient import TestClient

    return TestClient(devbot.app)


def test_root(client):
    """Sample pytest test function with the pytest fixture as an argument."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_healthz(client):
    """Sample pytest test function with the pytest fixture as an argument."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"message": "OK"}


@pytest.mark.parametrize("data", webhook_test_data)
def test_webhook_github(client, data):
    response = client.post("/webhook/github", json=data)
    assert response.status_code == 200


def test_all_endpoints_have_tests():
    from devbot import devbot

    # 检查所有的测试方法是否以“test_”开头
    test_methods = [
        f"/{item.__name__}"
        for item in globals().values()
        if callable(item) and item.__name__.startswith("test_")
    ]

    endpoints = [
        method.replace("test_", "").replace("_", "/")
        for method in test_methods
        if method != "test_all_endpoints_have_tests"
    ]

    endpoints.append("/") if "/root" in endpoints else None
    endpoints.append("/openapi.json")
    endpoints.append("/docs")
    endpoints.append("/docs/oauth2-redirect")
    endpoints.append("/redoc")

    # 获取所有的接口路径和方法
    routes = [
        route.path for route in devbot.app.routes if hasattr(route, "methods")
    ]

    # 断言每个接口路径是否出现在测试方法中
    for route in routes:
        assert route in endpoints
