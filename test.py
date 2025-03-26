import os
import requests
import re
import json
from moviepy import *

# API Key and Paths
PEXELS_API_KEY = "cI1tOfJAeKGGWC5ZaTzaHou9XOwkO36k3vtC1fzkkDnpJInH9m6VOs0j"
VIDEO_DOWNLOAD_PATH = "selected_video.mp4"
OUTPUT_VIDEO_PATH = "output.mp4"
CACHE_FILE = "cached_videos.json"

# Predefined themes
THEMES = {
    "1": "nature",
    "2": "travel",
    "3": "music",
    "4": "sports",
    "5": "technology",
    "6": "art",
    "7": "history"
}

def extract_keywords_from_filename(filename):
    """Extract meaningful keywords from the audio filename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    keywords = re.findall(r'\b\w+\b', name)  
    return " ".join(keywords)  

def load_cached_results():
    """Load cached API results from a JSON file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    return {}

def save_cached_results(cache):
    """Save the updated cache back to the file."""
    with open(CACHE_FILE, "w") as file:
        json.dump(cache, file, indent=4)

def fetch_video_options(search_query, use_cache_only=False):
    """Fetch related video options from Pexels, optionally using only cached results."""
    cache = load_cached_results()
    
    if search_query in cache:
        print(f"Using cached results for '{search_query}'")
        return cache[search_query]

    if use_cache_only:
        print(f"No cached results found for '{search_query}'. Skipping API call.")
        return []

    print(f"Fetching new videos for '{search_query}' from Pexels API...")
    url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        videos = data.get("videos", [])
        
        cache[search_query] = videos
        save_cached_results(cache)
        return videos
    else:
        print("Failed to fetch videos from API.")
        return []

def download_video(video_url):
    """Download the selected video from Pexels."""
    response = requests.get(video_url)
    with open(VIDEO_DOWNLOAD_PATH, "wb") as f:
        f.write(response.content)
    print(f"Video downloaded and saved as {VIDEO_DOWNLOAD_PATH}")

def resized_to_reel_format(video):
    """Resize video to 1080x1920 (Instagram Reel format) while maintaining aspect ratio."""
    target_width, target_height = 1080, 1920
    video = video.resized(height=target_height) if video.h < video.w else video.resized(width=target_width)

    bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=video.duration)
    final_video = CompositeVideoClip([bg.with_duration(video.duration), video.with_position("center")])
    
    return final_video

def ensure_video_length(video, target_duration):
    """Ensure the video matches the desired duration by trimming or looping."""
    if video.duration > target_duration:
        print(f"Trimming video from {video.duration:.2f} sec to {target_duration:.2f} sec")
        return video.subclipped(0, target_duration)
    
    elif video.duration < target_duration:
        print(f"Looping video to fill {target_duration:.2f} sec (original {video.duration:.2f} sec)")
        clips = []
        remaining_duration = target_duration

        while remaining_duration > 0:
            clip = video.subclipped(0, min(video.duration, remaining_duration))
            clips.append(clip)
            remaining_duration -= clip.duration

        return concatenate_videoclips(clips, method="compose")
    
    return video

def merge_video_audio(video_path, audio_path, output_path, target_duration):
    """Ensure video and audio match user-selected duration, always in Reel format."""
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)

    # Trim both to the selected duration
    video = ensure_video_length(video, target_duration)
    audio = audio.subclipped(0, target_duration)

    # Apply Instagram Reel format by default
    video = resized_to_reel_format(video)

    final_video = video.with_audio(audio)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    print(f"Final video saved as {output_path}")

if __name__ == "__main__":
    # Step 1: Get the audio file from the user
    audio_path = input("Enter the local path of the audio file: ")

    if not os.path.exists(audio_path):
        print("Error: Audio file not found.")
        exit()

    # Step 2: User chooses a theme or defaults to filename-based search
    print("\nSelect a theme for your video:")
    for key, value in THEMES.items():
        print(f"{key}. {value.capitalize()}")

    theme_choice = input("\nEnter the number of your chosen theme (or press Enter to use audio filename): ")
    
    if theme_choice in THEMES:
        search_query = THEMES[theme_choice]
    else:
        search_query = extract_keywords_from_filename(audio_path)
    
    print(f"\nSearching for videos related to: {search_query}")

    # Step 3: Ask user whether to use cached data only
    cache_only_choice = input("Do you want to use only cached results? (yes/no): ").strip().lower()
    use_cache_only = cache_only_choice == "yes"

    # Fetch video options
    videos = fetch_video_options(search_query, use_cache_only)

    if not videos:
        print("No relevant videos found.")
        exit()

    # Step 4: Show video options to the user
    print("\nSelect a video from the options below:")
    for i, video in enumerate(videos, 1):
        print(f"{i}. {video['url']} (Duration: {video['duration']} sec)")

    choice = int(input("\nEnter the number of the video you want to select: "))
    
    if choice < 1 or choice > len(videos):
        print("Invalid choice. Exiting.")
        exit()

    # Step 5: Download the selected video
    selected_video_url = videos[choice - 1]["video_files"][0]["link"]
    download_video(selected_video_url)

    # Step 6: Ask user for the final duration
    target_duration = float(input("\nEnter the desired duration (in seconds) for the output video: "))

    # Step 7: Merge and adjust video/audio (ALWAYS in Reel format)
    merge_video_audio(VIDEO_DOWNLOAD_PATH, audio_path, OUTPUT_VIDEO_PATH, target_duration)
