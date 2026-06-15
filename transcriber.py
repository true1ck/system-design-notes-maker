import os
import mlx_whisper

def transcribe_audio(audio_path: str, model_path: str = "mlx-community/whisper-large-v3-turbo") -> str:
    """
    Transcribes the given audio file using MLX Whisper.
    Uses the provided MLX model.
    """
    print(f"Transcribing {audio_path} using {model_path}...")
    try:
        # Check if local model exists in cache, mlx_whisper can use huggingface paths or local paths
        # We try to use the huggingface repo name, if the user has downloaded it, it'll use the cached version.
        # Alternatively, we could specify the exact path if needed.
        
        result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=model_path)
        text = result.get("text", "")
        print(f"Transcription completed for {audio_path}.")
        return text.strip()
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        return ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = transcribe_audio(sys.argv[1])
        print("--- Transcription ---")
        print(text)
    else:
        print("Usage: python transcriber.py <audio_file>")
