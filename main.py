import requests
import os
import subprocess

# Function to download file from URL
def download_file(url, output_path):
    response = requests.get(url, stream=True)
    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

# Get user input for MP3 file
audio_path = input("Enter the path of the MP3 audio file: ").strip()
if not os.path.exists(audio_path):
    print(" Error: Audio file not found.")
    exit()

# Get duration input
duration = int(input("Enter the reel duration (5-60 seconds): "))
if duration < 5 or duration > 60:
    print(" Invalid duration. Please enter a value between 5 and 60.")
    exit()

# Choose media type (video or image)
content_type = input("Do you want a 'video' or 'image' theme? (video/image): ").strip().lower()
if content_type not in ["video", "image"]:
    print(" Invalid option. Choose 'video' or 'image'.")
    exit()

# Choose theme
themes = ["Nature", "City", "Food", "Travel", "Animals"]
print("Available themes:", ", ".join(themes))
theme = input("Enter a theme from the above list: ").strip()
if theme not in themes:
    print(" Invalid theme selection.")
    exit()

# Pexels API key (replace with your actual key)
pexels_api_key = "cI1tOfJAeKGGWC5ZaTzaHou9XOwkO36k3vtC1fzkkDnpJInH9m6VOs0j"  # Replace with your actual API key
headers = {"Authorization": pexels_api_key}

# Fetch media from Pexels
if content_type == "video":
    url = f"https://api.pexels.com/videos/search?query={theme}&per_page=4"
else:
    url = f"https://api.pexels.com/v1/search?query={theme}&per_page=4"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    media_options = []

    if content_type == "video":
        media_options = [video["video_files"][0]["link"] for video in data.get("videos", [])]
    else:
        media_options = [photo["src"]["original"] for photo in data.get("photos", [])]

    if not media_options:
        print(" No media found for the selected theme.")
        exit()

    # Display options
    print("\nAvailable Options:")
    for index, link in enumerate(media_options, 1):
        print(f"{index}. {link}")

    # Let user select a media file
    choice = int(input("Enter the number of the media you want to use: "))
    if choice < 1 or choice > len(media_options):
        print(" Invalid selection.")
        exit()

    selected_media_url = media_options[choice - 1]
else:
    print(" Failed to fetch media. Check your Pexels API key.")
    exit()

# Download the selected media
temp_media_path = "temp_media.mp4" if content_type == "video" else "temp_image.jpg"
download_file(selected_media_url, temp_media_path)

# Process media and merge with audio using FFmpeg
output_path = "final_reel.mp4"

try:
    if content_type == "video":
        # Trim video and merge with audio properly
        command = [
            "ffmpeg",
            "-i", temp_media_path,  # Input video
            "-i", audio_path,  # Input audio
            "-t", str(duration),  # Trim duration
            "-c:v", "libx264",  # Video codec
            "-c:a", "aac",  # Audio codec
            "-map", "0:v:0",  # Use video from first input
            "-map", "1:a:0",  # Use audio from second input
            "-shortest",  # Match shortest duration
            output_path
        ]
    else:
        # Convert image to a video and merge with audio
        command = [
            "ffmpeg",
            "-loop", "1",  # Loop image
            "-i", temp_media_path,  # Input image
            "-i", audio_path,  # Input audio
            "-t", str(duration),  # Set duration
            "-vf", "scale=1280:720,format=yuv420p",  # Scale image to 720p
            "-c:v", "libx264",  # Video codec
            "-c:a", "aac",  # Audio codec
            "-map", "0:v:0",  # Use video from first input
            "-map", "1:a:0",  # Use audio from second input
            "-shortest",  # Match shortest duration
            output_path
        ]

    subprocess.run(command, check=True)
    print(f"\n Reel generated successfully! Saved as {output_path}")

except subprocess.CalledProcessError as e:
    print(f" Error occurred: {e}")

finally:
    # Clean up temporary files
    if os.path.exists(temp_media_path):
        os.remove(temp_media_path)
