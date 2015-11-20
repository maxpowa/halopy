# coding=utf-8
"""

HaloPy tests

"""
from __future__ import unicode_literals

import os
import pytest
from halopy import HaloPy

@pytest.fixture
def api():
    api_key = os.getenv('HALOPY_API_KEY', False)
    if api_key:
        return HaloPy(api_key)
    raise ValueError('No API key defined')


def test_emblem(api):
    api.get_player_emblem('themaxpowa')
