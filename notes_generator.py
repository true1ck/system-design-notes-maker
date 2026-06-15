import os
from openai import OpenAI

def generate_notes(transcription: str, model_name: str = "sarvam-local") -> str:
    """
    Generates structured system design notes from a transcription using a local LLM via Ollama.
    """
    print(f"Generating notes using Ollama model '{model_name}'...")
    
    # Initialize OpenAI client to point to local Ollama server
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"  # Ollama doesn't require an actual API key
    )
    
    prompt = f"""
You are an expert software engineer and technical writer. 
I am going to provide you with a transcription of a video about System Design.
Your task is to extract the key concepts, architectures, trade-offs, and important details, and structure them into clear, comprehensive Markdown notes.

Here is the transcription:
{transcription}

Please format the notes cleanly with appropriate headings, bullet points, and code blocks if applicable.
"""
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful expert system design assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        notes = response.choices[0].message.content
        print("Notes generation completed.")
        return notes
    except Exception as e:
        print(f"Error generating notes: {e}")
        return ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            transcription = f.read()
        notes = generate_notes(transcription)
        print("--- Generated Notes ---")
        print(notes)
    else:
        print("Usage: python notes_generator.py <transcription_txt_file>")
