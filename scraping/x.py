# x.py
import datetime
import json
from typing import Literal

from logs import setup_logger
from utils import tools
from .base import BaseScrape

from playwright.sync_api import sync_playwright, Playwright

logger = setup_logger(__name__)
SETTINGS = tools.read_settings()


class X(BaseScrape):
    
    def __init__(self):
        super().__init__()
        self.profile_img = None
    
    
    def struct_profile(self, profile):
        return {
            'username': profile.get('screen_name'),
            'uniqueid': profile.get(''),
            'img': self.profile_img,
            'stats': {
                'followers': profile.get('followers_count'),
                'media': profile.get('media_count'),
                'friends': profile.get('friends_count'),
                'status': profile.get('statuses_count')
            }
        }
    
    def struct_post(self, post):
        content = post.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
        legacy = content.get('legacy', {})
        return {
            'id': legacy.get('id_str'),
            'typename': content.get('__typename'),
            'date': legacy.get('created_at'),
            'retweeted': legacy.get('retweeted'),
            'user': content.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {}).get('screen_name'),
            'url':f"https://x.com/anyuser/status/{legacy.get('id_str')}",
            'desc': legacy.get('full_text'),
            'img': legacy.get('entities', {}).get('media', [{},{}])[0].get('media_url_https'),
            'stats': {
                'likes': legacy.get('favorite_count'),
                'retweets': legacy.get('retweet_count'),
                'quotes': legacy.get('quote_count'),
                'replies': legacy.get('reply_count'),
                'bookmarks': legacy.get('bookmark_count')
            }
        }
    
    def get(self, username: str, type: Literal['raw', 'clean', 'bs64'] = 'raw'):
        if " " in username or not username.startswith('@'):
            logger.error(f'X - Username "{username}" must not have spaces and starts with @. See "username" in the profile url: https://x.com/username')
            return None
        
        username = username[1:]
        logger.info(f'X - Making Scrape for "{username}"')
        with sync_playwright() as playwright:
            self.__run(playwright, username)
        
        if not self.raw_data:
            logger.info(f'X - No data found "{username}"')
            return None

        return self._type(type)
        

    def __handle_response(self, response):
        
        if 'UserTweets?variables' in response.url:
            try:
                try:
                    response_body = response.body().decode('utf-8')
                    self.raw_data = json.loads(response_body)
                except Exception as e:
                    logger.error(f'X - decoding response fail for: {response.url} - {e}')
            except Exception as e:
                logger.error(f'X - response handle fail: {response.url} - {e}')
        
        
    def __run(self, playwright: Playwright, username: str) -> None:
        wait_time = SETTINGS.get('x', {}).get('time_ms', 6000)
        headless = SETTINGS.get('gral', {}).get('headless', True)
        
        user_agent = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
        cookies = [
            {
                'name': 'hlsPlayback',
                'value': 'on',
                'domain': 'x.com',
                'path': '/',
                'httpOnly': False,
                'secure': False
            }
        ]
        browser = playwright.firefox.launch(headless=headless)
        context = browser.new_context(
            user_agent=user_agent,
        )
        context.add_cookies(cookies)
        page = context.new_page()

        page.on('response', self.__handle_response)
        page.goto(f'https://x.com/{username}/')
        page.wait_for_timeout(wait_time)
        
        page.goto(f'https://x.com/{username}/photo')
        page.wait_for_timeout(wait_time)
        img = page.locator('img')
        self.profile_img = img.get_attribute('src')
        
        browser.close()

    def _clean(self, raw_data):
        if not raw_data:
            return None
        
        max_posts = SETTINGS.get('x', {}).get('max_posts', 0) 
        
        profile = {}
        posts = []
        profiles = []
        instructions = raw_data.get('data', {}).get('user', {}).get('result', {}).get('timeline_v2', {}).get('timeline', {}).get('instructions', [])
        for inst in instructions:
            for entrie in inst.get('entries', []):
                content = entrie.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                legacy = content.get('legacy', {})
                if not content or not legacy:
                    continue
                
                d = self.struct_post(entrie)
                
                try:
                    d['date'] = datetime.datetime.strptime(d['date'], r"%a %b %d %H:%M:%S %z %Y").isoformat()
                except Exception as e:
                    logger.error(f'X - No Critical - Date cant be parsed: {e}')
                    pass
                
                posts.append(d)
                profiles.append(content.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {}))
                
        # Debug: print profiles before using mostcommon_Bykey
        print("DEBUG: profiles =", profiles)
        try:
            profile = tools.mostcommon_Bykey(profiles, key='screen_name')
        except ValueError as e:
            print("ERROR:", e)
            profile = None  # or handle as needed
        
        profile = self.struct_profile(profile)
        
        if max_posts > 0:
            posts = posts[:max_posts]
        
        return {
            'profile': profile,
            'posts': posts
        }

    def save(self):
        self._save('dist/x')
