import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
import lmstudio as lms
from utils import tools


# --- SETUP ---
llm_url = tools.read_settings('env.json').get('lm_studio_url')
llm_model = tools.read_settings('env.json').get('llm_model')
ONE_YEAR_AGO = datetime.now() - timedelta(days=365)

# --- STEP 1: Download full video metadata ---
def download_metadata(channel_url):
    print("[*] Downloading full metadata...")
    result = subprocess.run([
        "yt-dlp",
        "-J",
        "--dump-single-json",
        channel_url
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("[!] Error downloading metadata.")
        print(result.stderr)
        return []

    data = json.loads(result.stdout)
    video_entries = data.get("entries", [])

    # Filter videos published in the last year
    recent_videos = []
    for video in video_entries:
        try:
            upload_date = datetime.strptime(video['upload_date'], "%Y%m%d")
            if upload_date >= ONE_YEAR_AGO:
                recent_videos.append(video)
        except Exception as e:
            print(f"[!] Error parsing date for video {video.get('id')}: {e}")
            continue

    print(f"[*] Found {len(recent_videos)} videos from the past year.")
    return recent_videos

# --- STEP 2: Download captions ---
def download_captions(video_url, output_path):
    print(f"[*] Downloading captions for {video_url}...")
    subprocess.run([
        "yt-dlp",
        "--write-auto-sub",
        "--skip-download",
        "--sub-lang", "en",
        "-o", f"{output_path}/%(id)s.%(ext)s",
        video_url
    ])

# --- STEP 3: Load transcript from .vtt ---
def load_transcript(video_id, dir):
    vtt_path = next(Path(dir).glob(f"{video_id}.en.vtt"), None)
    if not vtt_path:
        return None
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    text_lines = [line.strip() for line in lines if "-->" not in line and not line.strip().isdigit()]
    return " ".join(text_lines)

def chunk_text(text, max_chars=5000):
    """
    Splits text into chunks of up to max_chars characters.
    Returns a list of text chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end
    return chunks

def summarize_long_transcript(text, max_chars=5000):
    """
    Chunks the transcript and summarizes each chunk.
    Optionally, summarizes the summaries if there are multiple chunks.
    """
    chunks = chunk_text(text, max_chars=max_chars)
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"[*] Summarizing chunk {i+1}/{len(chunks)}...")
        summary = summarize_text(chunk)
        summaries.append(summary)
    if len(summaries) == 1:
        return summaries[0]
    else:
        print("[*] Summarizing all chunk summaries into a final summary...")
        combined = "\n".join(summaries)
        return summarize_text(combined)



# --- STEP 4: Summarize transcript ---
def summarize_text(text):
    print("[*] Summarizing transcript...")
    model = lms.llm(llm_model)
    max_chars = 5000
    if len(text) > max_chars:
        print(f"[*] Transcript too long ({len(text)} chars), truncating to {max_chars} chars.")
        text = text[:max_chars]
    config={
                "temperature": 0.7,
                "maxTokens": 2000,
                "topPSampling": 0.8,
                "topKSampling": 20,
                "minPSampling": 0
            }
    prompt = f"Review the following transcript and take note of anything that is negative against US culture, support of Israel, citizens:\n\n{text} "
    raw_result = model.respond(prompt, config=config)
    # Extract the text from the PredictionResult object
    summary_text = raw_result.text if hasattr(raw_result, "text") else str(raw_result)
    print("[*] Summary generated: ", summary_text)
    return summary_text

