from dotenv import load_dotenv
import os
import requests
import time
from flask import Flask, render_template, redirect, request
import google.generativeai as genai
import base64
import wolframalpha
load_dotenv()

GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro-exp-0801")
text_model = genai.GenerativeModel(model_name="gemini-pro")
grabbber = os.environ.get("app_id")
client = wolframalpha.Client(grabbber)



app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/result")
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
    
    Based on this information, recommend 10 suitable activities, programs, or opportunities that align with their profile. 
    The recommendations should be realistic and tailored to their academic and personal background, taking into account their interests, academic performance, and location.
     Add links as well as adding info about it.
    
    """

    response = text_model.generate_content([
        {
            "role": 'user',
            "parts": [
              {"text": prompt}
            ]
        }
    ], stream=False)
    xer = response.text
    pr= f"""take this recomendations { xer } and split it apart via adding exlaimation marks before a new number starts, remove all commas"""

    xresponse = text_model.generate_content([
        {
            "role": 'user',
            "parts": [
              {"text":   pr }     ]
        }
    ], stream=False)
    print (response.text)
    recommendations = xresponse.text.split("!")
    return render_template("result.html", recommendations=recommendations)



@app.post("/college")
def college():
    resume = request.files['resume']
    resume_string = base64.b64encode(resume.read())
    resumeBase64 = resume_string.decode('utf-8')

    transcript = request.files['transcript']
    transcript_string = base64.b64encode(transcript.read())
    transcriptBase64 = transcript_string.decode('utf-8')

    Rresponse = model.generate_content([
        {
            "role": 'user',
            "parts": [
                {"inline_data": {"mime_type": 'application/pdf', "data": resumeBase64}},
                {"text": "Analyze the uploaded resume and provide a summary."}
            ]
        }
    ], stream=False)

    rsum = Rresponse.text
    tresponse = model.generate_content([
        {
            "role": 'user',
            "parts": [
                {"inline_data": {"mime_type": 'application/pdf', "data": transcriptBase64}},
                {"text": "Analyze the uploaded transcript and provide a summary. Take out all listed grades and write them along with their credit worth. Also, grab the GPA unweighted and weighted."}
            ]
        }
    ], stream=False)

    tsum = tresponse.text

    prompt = f"""
    A student needs college recommendations based on their profile. They are most likely low income, so recommend options specifically meant for low-income students. Here are their details: \n
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
    
    These are their transcript grades: {tsum}
    and this is their summarized resume: {rsum}
    
    Based on this information, recommend 11 colleges that align with their profile. The recommendations should be realistic and tailored to their academic and personal background, taking into account their interests, academic performance, and location. Keep in mind that these are low-income students, so make sure to add colleges that support low-income families. Separate your recommendations with only the college name and then a comma.
    """

    zresponse = text_model.generate_content([
        {
            "role": 'user',
            "parts": [
                {"text": prompt}
            ]
        }
    ], stream=False)

    zrecommendations_list = zresponse.text.split(",")


    college_info = []


    college_info = []
    for college_name in zrecommendations_list:
        res = client.query(f"Tell me about {college_name} and their low-income student help")
        answer = next(res.results).text
        college_info.append({
            "college_name": college_name.strip(),
            "info": answer
        })

    return render_template("college_info.html", info=college_info)

    
    for college_name in zrecommendations_list:
      zxresponse = text_model.generate_content([
          {
            "role": 'user',
              "parts": [
                  {"text":f"Tell me about {college_name} and summarize into 2 sentences with no commas. Start off by listing the college name then  the summary" }
              ]
          }
      ], stream=False)
      
      college_info.append( zxresponse.text)
    return render_template("college.html", info=college_info)





@app.post("/identify")
def identify():
    resume = request.files['resume']
    ext = resume.filename.split(".")[-1]
    resume_string = base64.b64encode(resume.read())
    resumeBase64 = resume_string.decode('utf-8')

    response = model.generate_content([
      {
        "role": 'user',
        "parts": [
          {"inline_data": {"mime_type": 'application/pdf', "data": resumeBase64}},
          {"text": "Analyze the uploaded resume and provide a summary. Tell them places where they can imporve and what is good already. Also tell them what places in their resume is bad and they should remove. Do not use astreiks do signify bolding just keep it all text and puncttuation "}
        ]
      }
    ], stream=False)

    summary = response.text

    return render_template("identify.html", summary=summary, transcript=resumeBase64, ext=ext)

if __name__ == '__main__':
    app.run(debug=True)
