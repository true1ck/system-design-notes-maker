import os
import argparse
from downloader import download_audio
from transcriber import transcribe_audio
from notes_generator import generate_notes

def main():
    parser = argparse.ArgumentParser(description="Playlist to System Design Notes Pipeline")
    parser.add_argument("url", help="YouTube Playlist or Video URL")
    parser.add_argument("--downloads-dir", default="downloads", help="Directory to save audio files")
    parser.add_argument("--transcripts-dir", default="transcripts", help="Directory to save transcriptions")
    parser.add_argument("--notes-dir", default="notes", help="Directory to save final notes")
    parser.add_argument("--whisper-model", default="mlx-community/whisper-large-v3-turbo", help="Whisper model path or repo")
    parser.add_argument("--llm-model", default="sarvam-local", help="Ollama model to use for notes generation")
    
    args = parser.parse_args()
    
    # 1. Download
    print("\n=== Phase 1: Downloading Audio ===")
    download_audio(args.url, args.downloads_dir)
    
    # Get downloaded files
    if not os.path.exists(args.downloads_dir):
        print("Downloads directory not found. Exiting.")
        return
        
    audio_files = [f for f in os.listdir(args.downloads_dir) if f.endswith(".mp3")]
    if not audio_files:
        print("No audio files found. Exiting.")
        return
    
    # Create output directories
    os.makedirs(args.transcripts_dir, exist_ok=True)
    os.makedirs(args.notes_dir, exist_ok=True)
    
    for audio_file in audio_files:
        audio_path = os.path.join(args.downloads_dir, audio_file)
        base_name = os.path.splitext(audio_file)[0]
        
        transcript_path = os.path.join(args.transcripts_dir, f"{base_name}.txt")
        notes_path = os.path.join(args.notes_dir, f"{base_name}.md")
        
        print(f"\n=== Processing: {base_name} ===")
        
        # 2. Transcribe
        if os.path.exists(transcript_path):
            print(f"Transcript already exists at {transcript_path}, skipping transcription.")
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcription = f.read()
        else:
            print("--- Transcribing Audio ---")
            transcription = transcribe_audio(audio_path, args.whisper_model)
            if transcription:
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(transcription)
            else:
                print("Failed to transcribe audio. Skipping to next file.")
                continue
                
        # 3. Generate Notes
        if os.path.exists(notes_path):
            print(f"Notes already exist at {notes_path}, skipping notes generation.")
        else:
            print("--- Generating Notes ---")
            notes = generate_notes(transcription, args.llm_model)
            if notes:
                with open(notes_path, "w", encoding="utf-8") as f:
                    f.write(notes)
            else:
                print("Failed to generate notes.")
                
    print("\n=== Pipeline Finished ===")

if __name__ == "__main__":
    main()
