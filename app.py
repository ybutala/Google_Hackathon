from flask import Flask, render_template, request, jsonify, redirect, url_for
from functions import *
import requests

app = Flask(__name__)

@app.route('/')
def index():

    return render_template('chat_page.html')

@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data['question']

    excuteAPI(question,
            #   backgound = '/home/ubuntu/EconimateR/background1.jpg',
            #   figures_path ='/home/ubuntu/EconimateR/figures',
            #   clips_path = '/home/ubuntu/EconimateR/clips',
            #   audio_path = '/home/ubuntu/EconimateR/audios',
            #   final_video_path='/home/ubuntu/EconimateR/static/results/final_video.mp4',
            final_video_path= './static/results/final_video.mp4',
            backgound= "./ai_final.png"
            )
              
    # video_id = '_TsyUrSkRqU'

    # if video_id:
        # YouTube video embedding
    #     embed_code = f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
    # else:
    #     answer = f"Question: {question} No Video Generated. Let me try again"
    video_path = 'static/results/final_video.mp4'
    answer = f"Video: {video_path}"

    return jsonify({'answer': answer, 'video_path': video_path})

if __name__ == '__main__':
    app.run(debug=True)