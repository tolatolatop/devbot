#!/usr/bin/env python

"""Tests for `devbot` package."""

import pytest


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
