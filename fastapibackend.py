from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import librosa
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer, pipeline
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize models
tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("main.html", {"request": None})

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    if not file.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .mp4 files are supported.")

    try:
        video_path = f"./{file.filename}"
        with open(video_path, "wb") as buffer:
            buffer.write(await file.read())

        audio_path = video_path.replace(".mp4", ".wav")
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path], 
            capture_output=True, check=True
        )

        speech, rate = librosa.load(audio_path, sr=16000)
        input_values = tokenizer(speech, return_tensors="pt").input_values
        logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]

        summary = summarizer(transcription, max_length=130, min_length=30, do_sample=False)

        return JSONResponse({"transcription": transcription, "summary": summary[0]['summary_text']})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
