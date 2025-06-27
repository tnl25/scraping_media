# scraping / __init__.py
from .tiktok import Tiktok
from .x import X
from .instagram import Instagram
from .youtube import Youtube

__all__ = [
    'Tiktok',
    'X',
    'Instagram',
    "Youtube"
]
