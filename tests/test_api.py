# coding=utf-8
"""

HaloPy tests

"""
from __future__ import unicode_literals

import os
import time
import pytest
from halopy import HaloPy, HaloPyResult

@pytest.fixture
def api(request):
    def finalize():
        time.sleep(1)
    request.addfinalizer(finalize)

    api_key = os.getenv('HALOPY_API_KEY', False)
    if api_key:
        return HaloPy(api_key, cache_backend='memory')
    raise ValueError('No API key defined')

@pytest.fixture
def no_cache_api(request):
    api_key = os.getenv('HALOPY_API_KEY', False)
    if api_key:
        hpy = HaloPy(api_key, cache_backend='memory')
        hpy.cache = 0
        hpy.rate = (1,2)
        return hpy
    raise ValueError('No API key defined')

def test_emblem(api):
    response = api.get_player_emblem('themaxpowa')
    assert response.status_code == 200

def test_spartan_image(api):
    response = api.get_player_spartan_image('themaxpowa')
    assert response.status_code == 200

def test_service_record(api):
    response = api.get_player_service_record('themaxpowa')
    assert response.Id == 'themaxpowa'
    assert response.ResultCode == 0
    assert response.PlayerId['Gamertag'] == 'themaxpowa'
    assert response.CampaignStat != None

def test_multi_service_record(api):
    response = api.get_players_service_record(['themaxpowa', 'Major Nelson'])
    for hpyo in response:
        assert hpyo.ResultCode == 0
        assert hpyo.CampaignStat != None

def test_matches(api):
    response = api.get_player_matches('themaxpowa', count=1)
    assert response.Start == 0
    assert response.Count == 1
    assert response.ResultCount == 1
    assert response.Results != None 

def test_campaign_missions(api):
    response = api.get_campaign_missions()
    for mission in response:
        assert mission.missionNumber != None
        assert mission.name != None
        assert mission.imageUrl != None
        assert mission.type in ['BlueTeam', 'OsirisTeam']
        assert mission.id != None

def test_commendations(api):
    response = api.get_commendations()

def test_csr_designations(api):
    api.get_csr_designations()

def test_enemies(api):
    api.get_enemies()

def test_flexible_stats(api):
    api.get_flexible_stats()

def test_game_base_variants(api):
    api.get_game_base_variants()

def test_impulses(api):
    api.get_impulses()

def test_maps(api):
    api.get_maps()

def test_medals(api):
    api.get_medals()

def test_playlists(api):
    api.get_playlists()

def test_skulls(api):
    api.get_skulls()

def test_spartan_ranks(api):
    api.get_spartan_ranks()

def test_team_colors(api):
    api.get_team_colors()

def test_vehicles(api):
    api.get_vehicles()

def test_weapons(api):
    api.get_weapons()

def test_can_request(api):
    assert api.can_request() == True
    api._allowance = 0
    assert api.can_request() == False

def test_cache_result(api):
    r1 = api.get_player_emblem('themaxpowa')
    r2 = api.get_player_emblem('themaxpowa')
    assert r2.from_cache == True

def test_rate_limit(no_cache_api):
    with pytest.raises(Exception) as ex:
        no_cache_api.rate = '1,1'
    no_cache_api.get_campaign_missions()
    time.sleep(2)
    no_cache_api.get_campaign_missions()

def test_rate_limit2(no_cache_api):
    with pytest.raises(Exception) as ex:
        no_cache_api._allowance = 0
        no_cache_api.get_campaign_missions()
    with pytest.raises(Exception) as ex:
        for x in range(20):
            no_cache_api.get_campaign_missions()

def test_wrapped_result():
    hpyo = HaloPyResult({'foo': 'bar', 'Result': {'team': 'blue'}})
    with pytest.raises(Exception) as ex:
        print(hpyo.bar)
    assert hpyo.foo == 'bar'
    assert hpyo.team == 'blue'

def test_bad_request():
    hpy = HaloPy(None, cache=0, cache_backend='memory')
    with pytest.raises(Exception) as ex:
        for x in range(10):
            hpy.get_campaign_missions()
