import os
import subprocess

def download_audio(url: str, output_dir: str = "downloads"):
    """
    Downloads audio from a YouTube video or playlist.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", output_template,
        url
    ]
    
    print(f"Downloading audio from {url}...")
    try:
        subprocess.run(command, check=True)
        print("Download completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {url}: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        download_audio(sys.argv[1])
    else:
        print("Usage: python downloader.py <youtube_url>")
