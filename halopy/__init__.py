# coding=utf-8
"""
__init__.py - HaloPy
Copyright 2015, Max Gurela

Licensed under the Eiffel Forum License 2
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import requests
import requests_cache
import time


__version__ = '0.1'


class HaloPyError(Exception):
    pass


class HaloPy(object):
    """HaloPy is an abstraction layer for the Halo 5 REST API.

    Requires an API key from https://developer.haloapi.com/

    Args:
        api_key (str): Halo API key. 
        title   (str): Title string, presumably for forward compat. default=h5
        cache   (int): Seconds to cache API results, None=no cache. default=300
        cacheFile(str): Filename to cache in, defaults to halopy.cache
        rate  (tuple): Maximum rate limit in form (req, sec), default=(10,10)
    """
    def now(self):
        return round(time.time())

    def __init__(self, api_key, title='h5', cache=300, rate=(10,10)):
        self._api_key = api_key
        self.title = title
        self._cache = cache
        self._rate = rate
        requests_cache.install_cache(backend='memory', expire_after=self.cache)

        self._allowance = rate[0]
        self._last_check = self.now()

    @property
    def api_key(self):
        """str: current API key"""
        return self._api_key

    @property
    def cache(self):
        """int: seconds to cache API results"""
        return self._cache

    @cache.setter
    def cache(self, value):
        """int: seconds to cache API results"""
        self._cache = value
        requests_cache.install_cache(backend='memory', expire_after=self.cache)

    @property
    def rate(self):
        """tuple: maximum rate limit in form (req, sec)"""
        return self._rate

    _err_400 = 'Bad request'
    _err_401 = 'Unauthorized'
    _err_404 = 'Endpoint not found'
    _err_429 = 'Rate limit exceeded'
    _err_500 = 'Internal server error'

    def _post_request(self):
        current = self.now()
        time_passed = current - self._last_check
        self._last_check = current
        self._allowance += time_passed * (self.rate[0] / self.rate[1])
        if self._allowance > self.rate[0]:
            self._allowance = self.rate[0]

    def can_request(self):
        if self._allowance >= 1.0:
            return True
        return False

    def request(self, endpoint, params={}, headers={}):
        if not self.can_request():
            raise HaloPyError(self._err_429)
        self._allowance -= 1.0

        p = {}
        for k,v in params.items():
            if k not in p and v:
                p[k] = v

        if 'Ocp-Apim-Subscription-Key' not in headers:
            headers['Ocp-Apim-Subscription-Key'] = self.api_key

        response = requests.get(
            'https://www.haloapi.com/{e}'.format(e = endpoint),
            params = p,
            headers = headers
        )
        if not getattr(response, 'from_cache', False):
            # IF the request was not cached, ensure that we are rate limiting
            self._post_request()

        if response.status_code == 400:
            raise HaloPyError(self._err_400)
        elif response.status_code == 401:
            raise HaloPyError(self._err_401)
        elif response.status_code == 404:
            raise HaloPyError(self._err_404)
        elif response.status_code == 429:
            raise HaloPyError(self._err_429)
        elif response.status_code == 500:
            raise HaloPyError(self._err_500)
        else:
            response.raise_for_status()
        return response.json()

    def meta_request(self, endpoint, params={}, headers={}):
        self.request(
            'metadata/{t}/metadata/{e}'.format(t=self.title, e=endpoint),
            params,
            headers
        )

    def profile_request(self, endpoint, params={}, headers={}):
        self.request(
            'profile/{t}/profiles/{e}'.format(t=self.title, e=endpoint),
            params,
            headers
        )

    def stats_request(self, endpoint, params={}, headers={}):
        self.request(
            'stats/{t}/{e}'.format(t=self.title, e=endpoint),
            params,
            headers
        )

    def  get_campaign_missions(self):
        url = 'campaign-missions'
        return self.meta_request(url)
    
    def  get_commendations(self):
        url = 'commendations'
        return self.meta_request(url)
        
    def get_csr_designations(self):
        url = 'csr-designations'
        return self.meta_request(url)
    
    def get_enemies(self):
        url = 'enemies'
        return self.meta_request(url)
        
    def get_flexible_stats(self):
        url = 'flexible-stats'
        return self.meta_request(url)
    
    def get_game_base_variants(self):
        url = 'game-base-variants'
        return self.meta_request(url)
        
    def get_game_variants_by_id(self,  varID):
        url = 'game-variants/{id1}'.format(
            id1 = varID)
        return self.meta_request(url)    
    
    def get_impulses(self):
        url = 'impulses'
        return self.meta_request(url)
    
    def get_maps_variants_by_id(self,  mapID):
        url = 'map-variants/{id1}'.format(
            id1 = mapID)
        return self.meta_request(url)       
    
    def get_maps(self):
        url = 'maps'
        return self.meta_request(url)    
    
    def get_medals(self):
        url = 'medals'
        return self.meta_request(url)        

    def get_playlists(self):
        url = 'playlists'
        return self.meta_request(url)    

    def get_requisition_packs_by_id(self, reqpackID):
        url = 'requisition-packs/{id1}'.format(id1 = reqpackID)
        return self.meta_request(url)      
    
    def get_requisition_by_id(self, reqID):
            url = 'requisitions/{id1}'.format(id1 = reqID)
            return self.meta_request(url)          
        
    def get_skulls(self):
        url = 'skulls'
        return self.meta_request(url)        
    
    def get_spartan_ranks(self):
        url = 'spartan-ranks'
        return self.meta_request(url)            

    def get_team_colors(self):
        url = 'team-colors'
        return self.meta_request(url)            

    def get_vehicles(self):
        url = 'vehicles'
        return self.meta_request(url)            

    def get_weapons(self):
        url = 'weapons'
        return self.meta_request(url)

    '''
    Profile functions
    '''

    def get_emblem_by_id(self, playerID, size=None):
        url = '{player}/emblem'.format(player = playerID)
        return self.profile_request(url, {'size':size})
    
    def get_profile_by_id(self, playerID, size=None, crop=None):
        url = '{player}/spartan'.format(player = playerID)
        return self.profile_request(url, {'size':size, 'crop':crop})

    '''
    Statistics functions
    '''

    def get_matches_for_player(self, playerID, modes=None, start=None, count=None):
        url = 'players/{player}/matches'.format(player = playerID)
        return self.stats_request(url, {'modes':modes, 
                                        'start':start, 
                                        'count':count})
    
    def get_match_by_id(self, matchId, gametype):
        url = '{t}/matches/{m}'.format(t = gametype, m = matchId)
        return self.stats_request(url)

    def get_arena_match_by_id(self, matchId):
        url = 'arena/matches/{matchId}'.format(matchId = matchId)
        return self.stats_request(url)              
        
    def get_campaign_match_by_id(self, matchId):
        url = 'campaign/matches/{matchId}'.format(matchId = matchId)
        return self.stats_request(url)
    
    def get_custom_match_by_id(self, matchId):
        url = 'custom/matches/{matchId}'.format(matchId = matchId)
        return self.stats_request(url)    
        
    def get_warzone_match_by_id(self, matchId):
        url = 'warzone/matches/{matchId}'.format(matchId = matchId)
        return self.stats_request(url)       
    
    def get_servicerecord_for_players(self, playerIds, servicerecord):
        url = 'servicerecords/{s}'.format(s = servicerecord)
        return self.stats_request(url, {'players': playerIds})

    def get_arena_servicerecord_for_players(self, playerIds):
        url = 'servicerecords/arena'
        return self.stats_request(url, {'players':playerIds})
    
    def get_campaign_servicerecord_for_players(self, playerIds):
        url = 'servicerecords/campaign'
        return self.stats_request(url, {'players':playerIds})    
        
    def get_custom_servicerecord_for_players(self, playerIds):
        url = 'servicerecords/custom'
        return self.stats_request(url, {'players':playerIds})    

    def get_warzone_servicerecord_for_players(self, playerIds):
        url = 'servicerecords/warzone'
        return self.stats_request(url, {'players':playerIds})   
