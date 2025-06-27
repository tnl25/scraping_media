from typing import Literal

from logs import setup_logger
from utils import tools
from .base import BaseScrape, RequestsHandler

logger = setup_logger(__name__)
SETTINGS = tools.read_settings()



class Youtube(BaseScrape):
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.request_handler = RequestsHandler("https://www.googleapis.com/youtube/v3")
    
    def struct_profile(self, profile):
        snippet = profile.get('snippet', {}) 
        stats = profile.get('statistics', {})
        return {
            'id': profile.get('id'),
            'username': snippet.get('customUrl'),
            'name': snippet.get('title'),
            'desc': snippet.get('description'),
            'joined': snippet.get('publishedAt'),
            'img': snippet.get('thumbnails', {}).get('high', {}).get('url'),
            'country': snippet.get('country'),
            'stats': {
                'views': int(stats.get('viewCount')) if stats.get('viewCount').isnumeric() else None,
                'followers': int(stats.get('subscriberCount')) if stats.get('subscriberCount').isnumeric() else None,
                'posts': int(stats.get('videoCount')) if stats.get('videoCount').isnumeric() else None
            }
        }
    
    def struct_post(self, post):
        snippet = post.get('snippet', {})
        stats = post.get('statistics', {})
        return {
            'id': post.get('id'),
            'user': snippet.get('channelId'),
            'title': snippet.get('title'),
            'date': snippet.get('publishedAt'),
            'img': snippet.get('thumbnails', {}).get('maxres', {}).get('url'),
            'stats': {
                'views': int(stats.get('viewCount')) if stats.get('viewCount').isnumeric() else None,
                'likes': int(stats.get('likeCount')) if stats.get('likeCount').isnumeric() else None,
                'favorites': int(stats.get('favoriteCount')) if stats.get('favoriteCount').isnumeric() else None,
                'comments': int(stats.get('commentCount')) if stats.get('commentCount').isnumeric() else None,
            }
        }
    
    def get(self, username: str, type: Literal['raw', 'clean', 'bs64'] = 'raw'):
        """
        For username do "@username" and for id do it without the @
        if username is provided and not id, It will do and additional api request
        """
        
        if ' ' in username:
            logger.error(f'Youtube - "{username}" - The username must not have spaces')
            
        if username.startswith('@'):
            id = self._obtain_id(username)
        else:
            id = username

        profile = self._get_profile(id)
        posts = self._get_posts(id)
        if not profile or not posts:
            return None
        
        self.raw_data = {
            'profile_req': profile,
            'posts_req': posts
        }
        
        return self._type(type)
        
                
    def _obtain_id(self, username: str) -> str:
        params = {
            'forHandle': username,
            'part': 'id',
            'key': self.api_key
        }
        
        response = self.request_handler.make_request('/channels', params=params)
        
        if not response:
            return None
        
        if not response.get('pageInfo', {}).get('totalResults', 0) == 1:
            logger.error(f'Youtube - More than one profile finded for "{username}"')
            return None
        
        youtube_id = next(iter(response.get('items', [])), {}).get('id')
        
        if not youtube_id:
            logger.error(f'Youtube - Error finding youtube id in response for {username}')
            return None
        
        return youtube_id
    
    def _get_profile(self, id):
        params = {
            'part': 'statistics,status,snippet',
            'id': id,
            'key': self.api_key
        }
        response = self.request_handler.make_request('/channels',params=params)
        if not response:
            logger.error(f'Youtube - error fetching __get_profile for id: "{id}"')
            return None
        if not response.get('pageInfo', {}).get('totalResults', 0) == 1:
            logger.critical(f'Youtube - No channel found for id: "{id}"')
            return None
        return response
    
    def _get_posts(self, id):
        max_posts = SETTINGS.get('youtube', {}).get('max_posts', 30)
        params = {
            'channelId': id,
            'maxResults': max_posts,
            'order': 'date',
            'type': 'video',
            'key': self.api_key
        }
        response = self.request_handler.make_request('/search', params=params)
        if not response:
            logger.error(f'Youtube - error fetching "__get_posts /search" for id "{id}"')
            return None
        
        if response.get('error'):
            logger.error(f'Youtube - api error "__get_posts /search" for id "{id}"')
            return None
        
        videos_items = response.get('items', [])
        if not videos_items:
            logger.error(f'Youtube - error no items in "__get_posts /search" response for id "{id}"')
            return None
        
        videos =  ",".join([video['id']['videoId'] for video in videos_items])
        params = {
            'part': 'id,snippet,statistics',
            'id': videos,
            'key': self.api_key
        }
        response = self.request_handler.make_request('/videos', params)
        if not response:
            logger.error(f'Youtube - error no items in "__get_posts /videos" response for id "{id}" videos_str: "videos"')
            return None
        return response
    
    def _clean(self, raw_data: dict):
        if not raw_data:
            return None
        
        profile = self.struct_profile(raw_data.get('profile_req', {}).get('items')[0])
        posts = [self.struct_post(post) for post in raw_data.get('posts_req',{}).get('items')]

        return {
            'profile': profile,
            'posts': posts
        }
    
    def save(self):
        self._save('./dist/youtube')
