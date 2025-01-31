from personalidades import personas, voces, memorias, ledColor
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import uuid
import time
import numpy as np
from pinecone import Pinecone, ServerlessSpec
import subprocess
import os
from collections import deque
import io
from pynput import keyboard
from keyboard import is_pressed

#LLaves ========================================================================================================================
client = OpenAI(api_key="Your DeepSeek key goes here", base_url="https://api.deepseek.com")
client2 = ElevenLabs(api_key="Your elevenlabs key goes here")
openai_client = OpenAI(api_key="Your openai key goes here")
pc = Pinecone(api_key="Your pinecone key goes here")


stop_loop = False
chat_log = []
n_remembered_post = 3 #Max number of posts to retrieve from pinecone
personality =next(personas)
voice = next(voces)
rgbLed = next(ledColor)
memory = next(memorias)

#Alwas initialize pinecone as normal chatbot
index_name = "botmemory"
spec = ServerlessSpec(cloud='aws', region='us-east-1')

# Ensure index is ready
while not pc.describe_index(index_name).status['ready']:
  time.sleep(1)
  
# Connect to index
index = pc.Index(index_name)

#Funciones ====================================================================================================================

def pineconeStartup(index_name):
    global index
    spec = ServerlessSpec(cloud='aws', region='us-east-1')
    # Ensure index is ready
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)
        print("Cargando...")
    # Connect to index
    index = pc.Index(index_name)
    print("Conexión a pinecone exitosa")
    
def on_press(key):
    global stop_loop
    try:
        if key.char == '0':  
            stop_loop = True
    except AttributeError:
        pass
listener = keyboard.Listener(on_press=on_press)
listener.start()

def chat(chat_log):
    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=chat_log,
    stream=False,
    max_tokens=200
)
    return response.choices[0].message.content.strip()

def genAudio(respuesta):
    audio = client2.text_to_speech.convert(
        text = respuesta,
        voice_id = voice,
        model_id = 'eleven_multilingual_v2',
        output_format="mp3_44100_128"
    )
    play(audio)
    
def embedding_vector(text):
  try:
    response = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"  # Update as necessary
    )
    return response.data[0].embedding
  except Exception as e:
    print(f"Error generating embeddings: {e}")
    return None

def similar_results(embedding_vector, similarity_threshold=0.6, namespace=None):
    # Query Pinecone index
    query_results = index.query(
        vector=embedding_vector,
        top_k=n_remembered_post,
        include_metadata=True,
        namespace=namespace
    )
    # Extract and filter matches by similarity threshold
    filtered_matches = [
        match.get('metadata', {}).get('text', '')
        for match in query_results.get('matches', [])
        if match['score'] >= similarity_threshold
    ]
    # Combine filtered matches into a single string
    combined_text = " ".join(filtered_matches)
    return combined_text 

def save_to_pinecone(text, embedding_vector):
  try:
    unique_id = str(uuid.uuid4())
    index.upsert(vectors=[(unique_id, embedding_vector, {"text": text})])
    return True
  except Exception as e:
    print(f"Error saving to Pinecone: {e}")
    return False

def transcribe_audio(audio_chunk):
    with io.BytesIO(audio_chunk) as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        return transcription["text"]
    
def push_to_talk():
    print("Press and hold SPACE to talk...")

    while True:
        if is_pressed("space"):  # Start recording when spacebar is pressed
            temp_audio_file = f"temp_audio_{uuid.uuid4()}.wav"
            
            if 'ffmpeg_process' in locals() and ffmpeg_process.poll() is None:
                ffmpeg_process.terminate()
                ffmpeg_process.wait()
            
            # Start recording using ffmpeg as a subprocess
            print("Recording...")
            ffmpeg_process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-y",  # Overwrite the file if it exists
                    "-f", "dshow",
                    "-i", "audio=Varios micrófonos (Intel® Smart Sound Technology for Digital Microphones)",  # Replace with your microphone's name
                    temp_audio_file,
                ],
                stdout=subprocess.PIPE,  # Suppress ffmpeg output
                stderr=subprocess.PIPE,
            )
            
            # Wait until the spacebar is released
            while is_pressed("space"):
                time.sleep(0.1)
            
            # Stop recording once the spacebar is released
            print("Recording stopped.")
            if ffmpeg_process.poll() is None:  # Ensure the process is terminated
                ffmpeg_process.terminate()
                ffmpeg_process.wait()
                
            if not os.path.exists(temp_audio_file):
                print(f"Recording failed: {temp_audio_file} was not created.")
                continue
            
            # Transcribe audio
            print("Transcribing audio...")
            try:
                with open(temp_audio_file, "rb") as audio_file:
                    transcription = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                    )
                    text = transcription.text
                    print("You:", text)

                    # Chatbot interaction
                    chat_log.append({'role': 'user', 'content': text})
                    if len(chat_log) > n_remembered_post:
                        del chat_log[:len(chat_log)-n_remembered_post]
                    #Conseguir la memoria del chatbot================================================================================================
                    try:
                        user_embedding = embedding_vector(text)
                        if user_embedding:
                            recuerdos = similar_results(user_embedding)
                            #print(recuerdos)
                            memory = {"role": "system", "content": f"These are the top memories relevant to your query if they are empty that means we haven't talked about it: {recuerdos}"}
                            chat_log.insert(1, memory)
                    except Exception as e:
                        print(f"Error retrieving memories: {e}")
                    
                    chat_log.insert(1, personality)
                    
                    try:
                        response = chat(chat_log)
                        print("Chatbot:", response)
                        chat_log.append({'role': "assistant", 'content': response})
                    except Exception as e:
                        print(f"Error generating response: {e}")
                        continue
                
                    # Convert response to audio
                    try:
                        genAudio(response)
                    except Exception as e:
                        print(f"Error generating audio: {e}")
                    
                    # Save interaction to Pinecone
                    try:
                        interaction_text = f"My input: {text}\nYour output: {response}"
                        interaction_embedding = embedding_vector(interaction_text)
                        if interaction_embedding:
                            save_to_pinecone(interaction_text, interaction_embedding)
                    except Exception as e:
                        print(f"Error saving interaction: {e}")

            except Exception as e:
                print(f"Error in transcription: {e}")
            
            # Clean up the temporary file
            if os.path.exists(temp_audio_file):
                os.remove(temp_audio_file)
        elif is_pressed("0"):
            break
        
        time.sleep(0.1)
        

if __name__ == "__main__":
    while True:
        push_to_talk()
        personality = next(personas)
        voice = next(voces)
        rgbLed = next(ledColor)
        pineconeStartup(next(memorias))