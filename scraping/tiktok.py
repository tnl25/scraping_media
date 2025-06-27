# tiktok.py
import datetime
import json
from typing import Union, Literal

from logs import setup_logger
from utils import tools
from .base import BaseScrape

from playwright.sync_api import sync_playwright, Playwright

logger = setup_logger(__name__)
SETTINGS = tools.read_settings()


class Tiktok(BaseScrape):
    
    def __init__(self):
        super().__init__()
    
    def struct_profile(self, profile):
        return {
            'id': profile.get('id'),
            'uniqueid': profile.get('uniqueId'),
            'img': profile.get('avatarLarger'),
            'username': profile.get('uniqueId'),
            'name': profile.get('nickname'),
        }
    
    def struct_post(self, post):
        stats = post.get('stats', {})
        return {
            'id': post.get('id'),
            'img': post.get('video', {}).get('cover'),
            'desc': post.get('desc'),
            'date': post.get('createTime'),
            'stats': {
                'views': stats.get('playCount'),
                'likes': stats.get('diggCount'),
                'shares': stats.get('shareCount'),
                'saves': stats.get('collectCount'),
                'comments': stats.get('commentCount')
            },
        }
    
    def get(self, username: str, type: Literal['raw', 'clean', 'bs64'] = 'raw'):
        if not username.startswith('@') or " " in username:
            logger.error(f'Tiktok - Username "{username}" must start with @ and have not spaces')
            return None
        
        logger.info(f'Tiktok - Making Scrape for "{username}"')
        with sync_playwright() as playwright:
            self.__run(playwright, username)
        if not self.raw_data:
            logger.info(f'Tiktok - No data found "{username}"')
            return None
        
        return self._type(type)
        

    def __handle_response(self, response):
        
        if '/api/post' in response.url:
            try:
                response_body = response.body().decode('utf-8')
                self.raw_data = json.loads(response_body)
            except json.JSONDecodeError as e:
                logger.error(f'Tiktok - JSON decoding error: {e}')
            except Exception as e:
                logger.error(f'Tiktok - Error scraping: {e}')
        
    def __run(self, playwright: Playwright, username: str) -> None:
        headless = SETTINGS.get('gral', {}).get('headless', True)
        wait_time = SETTINGS.get('tiktok', {}).get('time_ms', 2000)
        
        iphone_13 = playwright.devices['iPhone 13']
        browser = playwright.webkit.launch(headless=headless)
        iphone_13.pop('viewport', None)

        context = browser.new_context(
            **iphone_13,
        )

        page = context.new_page()
        
        page.on('response', self.__handle_response)
        page.goto(f'https://www.tiktok.com/{username}/', wait_until='load')
        
        page.wait_for_timeout(wait_time)
        
        browser.close()

    def _clean(self, raw_data) -> dict:
        if not raw_data:
            return None
        
        max_posts = SETTINGS.get('tiktok', {}).get('max_posts', 0) 
        
        cleaned = {
            'profile': {},
            'posts': []
        }
        
        posts = raw_data.get('itemList', [])
        if not posts:
            logger.error(f'Tiktok - Error geting posts')
            return None
        
        profile = tools.mostcommon([i.get('author') for i in posts if i.get('author')])
        profile = self.struct_profile(profile)
        cleaned['profile'] = profile
        
        if max_posts > 0:
            posts = posts[:max_posts]
        
        for post in posts:
            d = self.struct_post(post)      
            d['tags'] = tools.find_tags(d.get('desc'))
            d['date'] = datetime.datetime.fromtimestamp(d.get('date')).isoformat() if d.get('date') else None                
            cleaned['posts'].append(d)

        return cleaned
            
    def save(self):
        self._save('dist/tiktok')
