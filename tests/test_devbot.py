#!/usr/bin/env python

"""Tests for `devbot` package."""

import pytest


@pytest.fixture
def client():
    from devbot import devbot
    from fastapi.testclient import TestClient

    return TestClient(devbot.app)


@pytest.fixture
def response(client):
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return client.get("/")


def test_root(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
