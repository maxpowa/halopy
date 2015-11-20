# coding=utf-8
"""
.. moduleauthor:: Max Gurela <maxpowa@outlook.com>

Licensed under the Eiffel Forum License 2
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import requests
import requests_cache
import time


__version__ = '0.3'


class HaloPyError(Exception):
    """Standard HaloPy exception class"""
    pass


class HaloPy(object):
    """Primary abstraction class for HaloPy

    Args:
        api_key          (str): Halo API key.
        title (Optional[str])): Game title, presumably for forward 
            compatibility.
        cache  (Optional[int]): Seconds to cache API results, 0 indicates no 
            cache.
        rate (Optional[tuple]): Maximum rate limit in form ``(req, sec)``
    """

    def _now(self):
        return round(time.time())

    def __init__(self, api_key, title='h5', cache=300, rate=(10,10)):
        self._api_key = api_key
        self.title = title
        self._cache = cache
        self._rate = rate
        requests_cache.install_cache(backend='memory', expire_after=self.cache)

        self._allowance = rate[0]
        self._last_check = self._now()

    @property
    def api_key(self):
        """str: Halo API key."""
        return self._api_key

    @property
    def cache(self):
        """int: Seconds to cache API results, 0 indicates no cache."""
        return self._cache

    @cache.setter
    def cache(self, value):
        self._cache = value
        requests_cache.install_cache(backend='memory', expire_after=self.cache)

    @property
    def rate(self):
        """tuple: Maximum rate limit in form ``(req, sec)``"""
        return self._rate

    _err_400 = 'Bad request'
    _err_401 = 'Unauthorized'
    _err_404 = 'Endpoint not found'
    _err_429 = 'Rate limit exceeded'
    _err_500 = 'Internal server error'

    def _post_request(self):
        current = self._now()
        time_passed = current - self._last_check
        self._last_check = current
        self._allowance += time_passed * (self.rate[0] / self.rate[1])
        if self._allowance > self.rate[0]:
            self._allowance = self.rate[0]

    def can_request(self):
        """Check if we should be within our rate limits.

        This is called before actually executing any request internally, so
        you aren't required to check this yourself.

        Returns:
            bool: True if we are within the limit, False otherwise.
        """
        if self._allowance >= 1.0:
            return True
        return False

    def request(self, endpoint, params={}, headers={}):
        """Sends request to the Halo API servers.

        API key header will automatically be attached if it't not already
        specified. Endpoint will be prefixed with ``https://www.haloapi.com/``
        before the request is executed. 

        Retrieved values will be cached via cache method specified when 
        initializing HaloPy. If the value is from the cache, we the request
        will not count towards our rate limit bucket.

        Args:
            endpoint           (str): The endpoint to send the request to
            params  (Optional[dict]): Dictionary of key, value URL params
            headers (Optional[dict]): Dictionary of key, value request headers

        Returns:
            Response: :class:requests.Response object.

        Raises:
            HaloPyError: If we are over our rate limit, or if an
                HTTP error occurs.
        """
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
        return response

    def meta_request(self, endpoint, params={}, headers={}):
        """Helper method for metadata requests

        Prepends the endpoint with ``metadata/{title}/metadata/`` where 
        ``{title}`` is the game title.

        Args:
            endpoint           (str): The endpoint to send the request to
            params  (Optional[dict]): Dictionary of key, value URL params
            headers (Optional[dict]): Dictionary of key, value request headers

        Returns:
            json-encoded content of a response, if any
        """
        return self.request(
            'metadata/{t}/metadata/{e}'.format(t=self.title, e=endpoint),
            params,
            headers
        ).json()

    def profile_request(self, endpoint, params={}, headers={}):
        """Helper method for profile requests

        Prepends the endpoint with ``profile/{title}/profiles/`` where
        ``{title}`` is the game title.

        Args:
            endpoint           (str): The endpoint to send the request to
            params  (Optional[dict]): Dictionary of key, value URL params
            headers (Optional[dict]): Dictionary of key, value request headers

        Returns:
            Response: :class:requests.Response object.    
        """
        return self.request(
            'profile/{t}/profiles/{e}'.format(t=self.title, e=endpoint),
            params,
            headers
        )

    def stats_request(self, endpoint, params={}, headers={}):
        """Helper method for metadata requests

        Prepends the endpoint with ``stats/{title}/`` where
        ``{title}`` is the game title.

        Args:
            endpoint           (str): The endpoint to send the request to
            params  (Optional[dict]): Dictionary of key, value URL params
            headers (Optional[dict]): Dictionary of key, value request headers

        Returns:
            json-encoded content of a response, if any
        """
        return self.request(
            'stats/{t}/{e}'.format(t=self.title, e=endpoint),
            params,
            headers
        ).json()

    def  get_campaign_missions(self):
        """Get a listing of campaign missions supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f53
        for more information on this endpoint.

        Returns:
            List[object]: List of campaign mission details
        """
        url = 'campaign-missions'
        return self.meta_request(url)
    
    def  get_commendations(self):
        """Get a listing of commendations supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f4e
        for more information on this endpoint.

        Returns:
            List[object]: List of commendation details
        """
        url = 'commendations'
        return self.meta_request(url)
        
    def get_csr_designations(self):
        """Get a listing of CSR designations supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f50
        for more information on this endpoint.

        Returns:
            List[object]: List of CSR designation details
        """
        url = 'csr-designations'
        return self.meta_request(url)
    
    def get_enemies(self):
        """Get a listing of enemies supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f49
        for more information on this endpoint.

        Returns:
            List[object]: List of enemy details
        """
        url = 'enemies'
        return self.meta_request(url)
        
    def get_flexible_stats(self):
        """Get a listing of flexible statistics supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f43
        for more information on this endpoint.

        Returns:
            List[object]: List of flexible statistic details
        """
        url = 'flexible-stats'
        return self.meta_request(url)
    
    def get_game_base_variants(self):
        """Get a listing of all game base variants supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f45
        for more information on this endpoint.

        Returns:
            List[object]: List of game base variant details
        """
        url = 'game-base-variants'
        return self.meta_request(url)
        
    def get_game_variant_by_id(self, var_id):
        """Get details for specified game variant id.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f46
        for more information on this endpoint.

        Args:
            var_id (uid): Game variant unique identifier

        Returns:
            object: Game variant details
        """
        url = 'game-variants/{var_id}'.format(var_id = var_id)
        return self.meta_request(url)    
    
    def get_impulses(self):
        """Get list of supported impulses for the title. Impulses are 
        essentially invisible medals, players receive them for performing 
        virtually any action in the game.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f4f
        for more information on this endpoint.

        Returns:
            List[object]: List of impulse details
        """
        url = 'impulses'
        return self.meta_request(url)
    
    def get_maps_variant_by_id(self,  map_id):
        """Get details for specified map variant id

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f4c
        for more information on this endpoint.

        Args:
            map_id (uid): Unique identifier for the map

        Returns:
            object: Map variant details
        """
        url = 'map-variants/{map_id}'.format(map_id = map_id)
        return self.meta_request(url)       
    
    def get_maps(self):
        """Get list of supported maps in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f44
        for more information on this endpoint.

        Returns:
            List[object]: List of map details
        """
        url = 'maps'
        return self.meta_request(url)    
    
    def get_medals(self):
        """Get list of supported medals in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f47
        for more information on this endpoint.

        Returns:
            List[object]: List of medal details
        """
        url = 'medals'
        return self.meta_request(url)        

    def get_playlists(self):
        """Get list of playlists available in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f4b
        for more information on this endpoint.

        Returns:
            List[object]: List of playlist details
        """
        url = 'playlists'
        return self.meta_request(url)    

    def get_requisition_pack_by_id(self, req_pack_id):
        """Get details for a specific "REQ" pack

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f52
        for more information on this endpoint.

        Args:
            req_pack_id (uid): Unique identifier string

        Returns:
            object: "REQ" pack details
        """
        url = 'requisition-packs/{req}'.format(req=req_pack_id)
        return self.meta_request(url)      
    
    def get_requisition_by_id(self, req_id):
        """Get details for a specific "REQ"

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f51
        for more information on this endpoint.

        Args:
            req_id (uid): Unique identifier string

        Returns:
            object: "REQ" details
        """
        url = 'requisitions/{req_id}'.format(req_id = req_id)
        return self.meta_request(url)          
        
    def get_skulls(self):
        """Get list of skulls supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f54
        for more information on this endpoint.

        Returns:
            List[object]: List of skull details
        """
        url = 'skulls'
        return self.meta_request(url)        
    
    def get_spartan_ranks(self):
        """Get list of spartan ranks supported in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f4d
        for more information on this endpoint.

        Returns:
            List[object]: List of spartan rank details
        """
        url = 'spartan-ranks'
        return self.meta_request(url)            

    def get_team_colors(self):
        """Get list of supported team colors in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f55
        for more information on this endpoint.

        Returns:
            List[object]: List of team color details
        """
        url = 'team-colors'
        return self.meta_request(url)            

    def get_vehicles(self):
        """Get list of supported vehicles in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f4a
        for more information on this endpoint.

        Returns:
            List[object]: List of vehicle details
        """
        url = 'vehicles'
        return self.meta_request(url)            

    def get_weapons(self):
        """Get list of supported weapons in the title.

        See https://developer.haloapi.com/docs/services/560af0dae2f7f710cc79e516/operations/562d68f1e2f7f72764ff1f48
        for more information on this endpoint.

        Returns:
            List[object]: List of weapon details
        """
        url = 'weapons'
        return self.meta_request(url)

    '''
    Profile functions
    '''

    def get_player_emblem(self, player_gt, size=None):
        """Get the emblem image for the given player gamertag.

        See https://developer.haloapi.com/docs/services/56393773e2f7f718548921d7/operations/56393774e2f7f70ad8d46e9c
        for more information on this endpoint.

        Args:
            player_gt      (str): Player gamertag
            size (Optional[int]): Size of emblem image, must be one of the 
                following values: 95, 128, 190, 256, 512. Default is 256.

        Returns:
            Response: Response object containing the player's emblem
        """
        url = '{player}/emblem'.format(player = player_gt)
        return self.profile_request(url, {'size':size})
        
    
    def get_player_spartan_image(self, player_gt, size=None, crop=None):
        """Get the given player's spartan image.

        See https://developer.haloapi.com/docs/services/56393773e2f7f718548921d7/operations/56393774e2f7f70ad8d46e9b
        for more information on this endpoint.

        Args:
            player_gt      (str): Player gamertag
            size (Optional[int]): Size of spartan image, must be one of the
                following values: 95, 128, 190, 256, 512. Default is 256.
            crop (Optional[str]): Either ``full`` or ``portrait``. If not
                specified, ``full`` is used.

        Returns:
            Response: Response object containing the player's spartan image
        """
        url = '{player}/spartan'.format(player = player_gt)
        return self.profile_request(url, {'size':size, 'crop':crop})

    '''
    Statistics functions
    '''

    def get_player_matches(self, player_gt, modes=None, start=None, count=None):
        """Get matches played by the given player

        See https://developer.haloapi.com/docs/services/560af163e2f7f710cc79e517/operations/560af163e2f7f703f8349976
        for more information on this endpoint.

        Args:
            player_gt       (str): Player gamertag
            modes (Optional[str]): Game mode(s) to show, if unspecified, all
                game modes will be included in the result set. You may specify
                multiple game modes by comma-delimiting the values.
            start (Optional[int]): Start index for batched results
            count (Optional[int]): Count of results to return. Minimum value is
                1, maximum is 25. 25 is assumed if unspecified.

        Returns:
            object: A batched results object::
                {
                    "Start": int,
                    "Count": int,
                    "ResultCount": int,
                    "Results" list
                }
        """
        url = 'players/{player}/matches'.format(player = player_gt)
        return self.stats_request(url, {'modes':modes, 
                                        'start':start, 
                                        'count':count})
    
    def get_arena_match_by_id(self, match_id):
        """Get arena match details by match id.

        See https://developer.haloapi.com/docs/services/560af163e2f7f710cc79e517/operations/5612e539e2f7f7334c177fb3
        for more information on this endpoint.

        Args:
            match_id (uid): Match unique identifier

        Returns:
            object: An object representing an arena match's details
        """
        url = 'arena/matches/{match_id}'.format(match_id = match_id)
        return self.stats_request(url)
        
    def get_campaign_match_by_id(self, match_id):
        """Get campaign match details by match id.

        See https://developer.haloapi.com/docs/services/560af163e2f7f710cc79e517/operations/5612e539e2f7f7334c177fb4
        for more information on this endpoint.

        Args:
            match_id (uid): Match unique identifier

        Returns:
            object: An object representing a campaign match details
        """
        url = 'campaign/matches/{match_id}'.format(match_id = match_id)
        return self.stats_request(url)
    
    def get_custom_match_by_id(self, match_id):
        """Get custom match details by match id.

        See https://developer.haloapi.com/docs/services/560af163e2f7f710cc79e517/operations/5612e539e2f7f7334c177fb5
        for more information on this endpoint.

        Args:
            match_id (uid): Match unique identifier

        Returns:
            object: An object representing a custom match details
        """
        url = 'custom/matches/{match_id}'.format(match_id = match_id)
        return self.stats_request(url)    
        
    def get_warzone_match_by_id(self, match_id):
        """Get warzone match details by match id.

        See https://developer.haloapi.com/docs/services/560af163e2f7f710cc79e517/operations/5612e539e2f7f7334c177fb6
        for more information on this endpoint.

        Args:
            match_id (uid): Match unique identifier

        Returns:
            object: An object representing a warzone match details
        """
        url = 'warzone/matches/{match_id}'.format(match_id = match_id)
        return self.stats_request(url)       
    
    def get_players_service_record(self, player_gts, game_mode='campaign'):
        """Get service records for the given list of player gamertags and the 
        given mode

        Args:
            player_gts(List[str]): List of player gamertags
            game_mode       (str): Must be ``arena``, ``warzone``, ``custom``,
                or ``campaign``. Defaults to ``campaign``.

        Returns:
            List[object]: List of player service record objects
        """
        url = 'servicerecords/{game_mode}'.format(game_mode = game_mode)
        res_json = self.stats_request(url, {'players':player_ids})
        return res_json.get('Results', [])
