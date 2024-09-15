"""
Tests for the datastore module
"""
import unittest
import pytest
from motu_osc_bridge.server import MotuOscBridge

class MotuOscBridgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.bridge = MotuOscBridge("test_service", "http://localhost:8888")

    @pytest.mark.asyncio
    async def test_increment(self):
        pass