# main.py
from utils import tools
from scraping import *
import argparse
from scraping.yt_summary import download_metadata, download_captions, load_transcript, summarize_text, summarize_long_transcript
import time



def main():
    
    parser = argparse.ArgumentParser(
                        prog='Scraping Media Tool',
                        description='Scrape info from social media',
                        epilog='See readme file or the files because they are very simple to read, settings must be in a settings.json file'
                        )

    parser.add_argument('--youtube', '-y', type=str, help='Youtube id or username with "@"')
    parser.add_argument('--x', '-x', type=str, help='X username in the url')
    parser.add_argument('--instagram', '-i', type=str, help='Instagram username with "@" in the url')
    parser.add_argument('--tiktok', '-t', type=str, help='Tiktok username with "@"')
    parser.add_argument('--clear', action='store_true', help='clear dist dict')
    
    parser.add_argument('--save_imgs', action='store_true', help='Save the imgs and make bs64 file')

    args = parser.parse_args()

    print("DEBUG: args =", args)
    print("DEBUG: args.youtube =", args.youtube)
    channel_url = None
    if args.youtube:
        yt_input = args.youtube.strip()
        if yt_input.startswith('@'):
            channel_url = f"https://www.youtube.com/{yt_input}"
        elif yt_input.startswith("UC"):  # likely a channel ID
            channel_url = f"https://www.youtube.com/channel/{yt_input}"
        else:  # fallback, treat as username
            channel_url = f"https://www.youtube.com/c/{yt_input}"
        print("DEBUG: channel_url =", channel_url)

    
    if args.clear:
        tools.rm_dir('dist/')
    
    tools.make_dir('dist')
    
    if args.youtube:
        print("DEBUG: args.youtube =", args.youtube)
        key = tools.read_settings('env.json').get('apikey')
        youtube = Youtube(key)
        # if args.save_imgs:
        #     youtube.get(args.youtube, type='bs64')
        # else:
        #     youtube.get(args.youtube, type='clean')
        # youtube.save()
        videos = download_metadata(channel_url)
        OUTPUT_DIR = 'dist'
        for video in videos[:5]:  # Limit to 5 videos for testing
            video_id = video['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            download_captions(video_url, OUTPUT_DIR)
            time.sleep(2)  # Avoid hitting rate limits

            transcript = load_transcript(video_id, OUTPUT_DIR)
            if transcript:
                summary = summarize_long_transcript(transcript)
                output = summarize_text(summary)
                with open(f"{OUTPUT_DIR}/{video_id}_summary.txt", "w", encoding="utf-8") as f:
                    f.write(f"Title: {video.get('title')}\n")
                    f.write(f"URL: {video_url}\n\n")
                    f.write(output)
            else:
                print(f"[!] No transcript found for {video_id}")
    if args.instagram:
        instagram = Instagram()
        if args.save_imgs:
            instagram.get(args.instagram, type='bs64')
        else:
            instagram.get(args.instagram, type='clean')
        instagram.save()
    if args.tiktok:
        tiktok = Tiktok()
        if args.save_imgs:
            tiktok.get(args.tiktok, type='bs64')
        else:
            tiktok.get(args.tiktok, type='clean')
        tiktok.save()
    if args.x:
        x = X()
        if args.save_imgs:
            x.get(args.x, type='bs64')
        else:
            x.get(args.x, type='clean')
        x.save()        

    
    

if __name__ == "__main__":
    main()
