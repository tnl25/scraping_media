# Scraping Media Tool
This is a short and simple repo for scraping social media.
- Support media are tiktok, instagram, x and youtube.
- For youtube get an api key of the *https://www.googleapis.com/youtube/v3*
- It's made with playwright because it's easy, maybe for in the future I will use `selenium-driverless`
- **If you have a suggestion let me now I would love to read it**

There are three types of content
- **The raw:** It's the intercepted request
- **The clean:** It's the cleaned raw
- **The bs64:** It's the cleaned raw but for the images scraped and converted to base64
  - *because the url of images have time limit or can't be use on a `html img`*
## Instalation

```cmd
git clone https://github.com/luciomorocarnero/scraping_media.git
python -m venv venv
.\venv\Scripts\activate # for windows
pip install -r requirements.txt
playwright install
```

## Settings
For the settings edit the settings.json
```json
{
    "gral":{
        "log_level": "ERROR",
        "headless": true,
        "dist_clear": false ,
        "img_scrape_sleep_s": 1
    },
    "youtube": {
        "max_posts": 10
    },
    "x": {
        "time_ms": 6000,
        "max_posts": 10

    },
    "tiktok": {
        "time_ms": 2000,
        "max_posts": 5
    },
    "instagram": {
        "time_ms": 6000,
        "max_posts": 20
    }
}
```
For the youtube key make an env.json like
```json
{
    "apikey": "your_youtube_apikey"
}
```
or make a real .env and config the main file

## Usage
- All usernames must be the ones in the url and must start with '@'
- The files saves in a dist folder
- `--save_img` is for saving the images in dist/app folders
- `--clear` for clear dist folder
- `see -h for help`

Example:
```cmd
python .\main.py -y "@joerogan" -x "@joerogan" -i "@joerogan" -t "@joe.rogan.clips33" --save_img
```

## Code
For code this is an example:
```python
from scraping import *

instagram = Instagram()
data_cleaned = instagram.get('@username', type='clean')
# type='raw' for only de requests
# type='clean' for clean and format the 'raw'
# type='bs64' for scrape the images of post and profile and converting to bs64
print(data_cleaned)

# if you want to save to the dist folder, it must exist first
instagram.save()
```
