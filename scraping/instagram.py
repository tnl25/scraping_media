# instagram.py
import datetime
import json
import random
from typing import Union, Literal
import uuid
from unicodedata import normalize

from logs import setup_logger
from utils import tools
from .base import BaseScrape

from playwright.sync_api import sync_playwright, Playwright

logger = setup_logger(__name__)
SETTINGS = tools.read_settings()

class Instagram(BaseScrape):
    
    def __init__(self):
        super().__init__()
    
    def struct_post(self, post):
        post = post.get('node', {})
        return {
            'id': post.get('id'),
            'user': post.get('owner', {}).get('username'),
            'img': post.get('thumbnail_src'),
            'desc': next(iter(post.get('edge_media_to_caption', {}).get("edges", [])),{}).get('node', {}).get('text'),
            'date': post.get('taken_at_timestamp'),
            'stats': {
                'views': post.get('video_view_count'),
                'comments': post.get('edge_media_to_comment', {}).get('count'),
                'likes': post.get('edge_liked_by', {}).get('count'),
            }
        }
    
    def struct_profile(self, profile):
        return {
            'id': profile.get('id'),
            'username': profile.get('username'),
            'name': profile.get('full_name'),
            'category': profile.get('category_name'),
            'desc': profile.get('biography'),
            'img': profile.get('profile_pic_url'),
            'stats': {
                'followers': profile.get('edge_followed_by', {}).get('count'),
                'follow': profile.get('edge_follow', {}).get('count'),
            } 
        }
    
    def get(self, username: str, type: Literal['raw', 'clean', 'bs64'] = 'raw'):
        if not username.startswith('@') or " " in username:
            logger.error(f'Instagram - Username "{username}" must start with @ and have not spaces (see the url and add @)')
            return None
        
        username = username[1:]
        
        logger.info(f'Instagram - Making Scrape for "{username}"')
        with sync_playwright() as playwright:
            self.__run(playwright, username)
        if not self.raw_data:
            logger.info(f'Instagram - No data found "{username}"')
            return None
        
        return self._type(type)
    
    def __run(self, playwright: Playwright, username: str) -> None:
        headless = SETTINGS.get('gral', {}).get('headless', True)        
        wait_time = SETTINGS.get('instagram', {}).get('time_ms', 6000)

        iphone_13 = playwright.devices['iPhone 13']
        browser = playwright.webkit.launch(headless=headless)
        iphone_13.pop('viewport', None)

        context = browser.new_context(
            **iphone_13,
        )

        page = context.new_page()
        
        page.on('response', self.__handle_response)
        page.goto(f'https://www.instagram.com/{username}/?hl=en')
        
        page.wait_for_timeout(wait_time)
        
        browser.close()
    
    def __handle_response(self, response):
        try:
            response_body = response.body().decode('utf-8')
            data = json.loads(response_body)
            if data.get('data', {}).get('user').get('edge_owner_to_timeline_media'):
                self.raw_data = data
        except json.JSONDecodeError as e:
            pass
        except Exception as e:
            pass
    
    def _clean(self, raw_data: dict):
        if not raw_data:
            return None
        
        max_posts = SETTINGS.get('instagram', {}).get('max_posts', 0) 
        
        profile = self.struct_profile(
            raw_data.get('data', {}).get('user', {})
        )
        
        posts_raw = raw_data.get('data', {}).get('user', {}).get('edge_owner_to_timeline_media', {}).get('edges', [])
        if not posts_raw:
            logger.error(f'Instagram - Error getting posts')
            return None
        
        if max_posts > 0:
            posts_raw = posts_raw[:max_posts]
        
        posts = []
        for post in posts_raw:
            d = self.struct_post(post)
            if d['date']:
                d['date'] = datetime.datetime.fromtimestamp(d.get('date')).isoformat()
            posts.append(d)
        
        return {
            'profile': profile,
            'posts': posts
        }

    def save(self):
        self._save('dist/instagram')
