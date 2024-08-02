from dotenv import load_dotenv
import os
import requests
import time
from flask import Flask, render_template, redirect, request
import google.generativeai as genai
import base64

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-pro-vision")
text_model = genai.GenerativeModel(model_name="gemini-pro")

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/")
def get_data():
    prompt = f"""
    A student needs activity recommendations based on their profile.They are most likly low income so recommend them options which is specifically meant for income  Here are their details: \n
    - Age: {request.form['age']}
    - Grade level: {request.form['grade']}
    - GPA (Weighted): {request.form['weighted_gpa']}
    - GPA (Unweighted): {request.form['unweighted_gpa']}
    - Race: {request.form['race']}
    - Total Family Income: {request.form['income']}
    - SAT Score: {request.form['sat']}
    - ACT Score: {request.form['act']}
    - Financial Aid Received: {request.form['aid']}
    - Interests: {request.form['interest']}
    - Hard Classes Taken: {request.form['courses']}
    - Location: {request.form['location']}
    
    Based on this information, recommend 10 suitable activities, programs, or opportunities that align with their profile. The recommendations should be realistic and tailored to their academic and personal background, taking into account their interests, academic performance, and location. Add links as well. Separate your recommendations with a exclmation mark.
    """

    response = text_model.generate_content([
        {
            "role": 'user',
            "parts": [
              {"text": prompt}
            ]
        }
    ], stream=False)

    recommendations = response.text.split("! ")
    return render_template("result.html", recommendations=recommendations)


@app.post("/identify")
def identify():
    transcript = request.files['resume']
    ext = transcript.filename.split(".")[-1]
    transcript_string = base64.b64encode(transcript.read())
    transcriptBase64 = transcript_string.decode('utf-8')

    response = model.generate_content([
      {
        "role": 'user',
        "parts": [
          {"inline_data": {"mime_type": 'application/pdf', "data": transcriptBase64}},
          {"text": "Analyze the uploaded resume and provide a summary tell them places where they can imporve and what is already."}
        ]
      }
    ], stream=False)

    summary = response.text

    return render_template("identify.html", summary=summary, transcript=transcriptBase64, ext=ext)

if __name__ == '__main__':
    app.run(debug=True)
