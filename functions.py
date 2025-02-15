import openai
from openai import OpenAI
#import gtts
import moviepy.editor as mpy
#import cv2
import matplotlib.pyplot as plt
import os
from gtts import gTTS
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, \
ImageClip, ColorClip, AudioFileClip, vfx
import numpy as np
import shutil
import pandas as pd
import subprocess
import sys
from config import Config

openai.api_key = Config.API_KEY
API_key = Config.API_KEY

def update_libraries(requirements_path='requirements.txt'):
    try:
        with open(requirements_path, 'r') as file:
            libraries = file.readlines()
            libraries = [lib.strip() for lib in libraries]  # Remove any whitespace or newline characters

        for lib in libraries:
            if lib:  # Check if the line is not empty
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", lib])
    except FileNotFoundError:
        print(f"The file {requirements_path} was not found.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while installing the libraries: {e}")

def clear_folder(folder_path):
    
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"The folder {folder_path} does not exist.")

def get_user_input():
    prompt = "Please enter your question or topic related to economics: "
    user_input = input(prompt)
    return user_input

def query_genapi(user_input, API_key = API_key):
    try:

        openai.api_key = API_key
        client = OpenAI(api_key=API_key)

        response = client.chat.completions.create(
            model="gpt-4-1106-preview",  # GPT-4 Turbo 1106 model
            messages=[
            {
                "role": "system",
                "content": (
                    "You are an economic tutor. Let’s think step-by-step."
                    "Firstly, check if there are any economic concepts and questions within the prompt."
                    "If there are no economic concepts or questions, respond with 'This is not Economic related.Ask me anything about Economics instead!'."
                    "If an economic concept or question is mentioned, explain the concept using figures and explanations for each part of the concept."
                    "The figures should be labeled [Figure - concept name] and the explanations should be labeled [Explanation - concept name]"
                    "All figures in the response should be displayed as either Python code for figures (graphs/tables/matrix/equations/more)."
                    "Each explanation should refer to each and all of the figures and real-life scenarios."
                    "You can have multiple [Figure] and [Explanation]. Have the response displayed in the order of [figure - a], [explanation - a], [figure - b], [explanation - b], etc"
                )
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
            temperature=1,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        assistant_message = response.choices[0].message.content

        return assistant_message
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

def segment_response(response):
    def extract_figure_code(text):
        if "```python" in text:
            code = text.split("```python")[1].split("```")[0].strip()
            return code
        return ""

    figure_codes = []
    explanations = []

    segments = response.split('[Figure - ')
    for segment in segments[1:]:
        if '[Explanation - ' in segment:
            figure_part, explanation_part = segment.split('[Explanation - ', 1)
            figure_code = extract_figure_code(figure_part)
            explanation = explanation_part.split(']\n', 1)[1].strip() if ']\n' in explanation_part else explanation_part.strip()

            figure_codes.append(figure_code)
            explanations.append(explanation)

    return figure_codes, explanations

def generate_audio_explanations(explanations, folder_path='./audios'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    audio_paths = []
    for i, explanation in enumerate(explanations):
        audio_path = os.path.join(folder_path, f"Explanation{i+1}.mp3")
        tts = gTTS(text=explanation, lang='en')
        tts.save(audio_path)
        audio_paths.append(audio_path)

    return audio_paths

def process_figures(figure_codes, folder_path='./figures'):
    def save_plot(figure_code, figure_path, namespace):
        """ Executes Python code for plotting and saves the plot. """
        try:
            exec(figure_code, globals(), namespace)
            plt.savefig(figure_path)
            plt.close()
        except Exception as e:
            raise ValueError(f"Error generating plot: {e}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    figure_paths = []
    namespace = {}
    for i, figure_code in enumerate(figure_codes):
        modified_figure_code = figure_code.replace('plt.show()', '')
        figure_path = os.path.join(folder_path, f"Figure{i+1}.png")
        save_plot(modified_figure_code, figure_path, namespace)
        figure_paths.append(figure_path)
#     if figure_paths == []:
#         raise ValueError(f"Error generating plot: no plot generated")
    return figure_paths


def create_video_clips(figure_paths, audio_paths, folder_path='./clips'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    video_clip_paths = []
    for i, (figure_path, audio_path) in enumerate(zip(figure_paths, audio_paths)):
        image_clip = ImageClip(figure_path)
        audio_clip = AudioFileClip(audio_path)
        video_clip = image_clip.set_audio(audio_clip).set_duration(audio_clip.duration)
        video_clip_path = os.path.join(folder_path, f"Clip{i+1}.mp4")
        video_clip.write_videofile(video_clip_path, codec="libx264", fps=24)
        video_clip_paths.append(video_clip_path)

    return video_clip_paths

def combine_and_save_video(clip_paths, final_video_path, background_path=None, bg_color='black', bg_size=(1280, 720), clip_size=(960, 540)):

    def load_and_resize_clip(path):
        return VideoFileClip(path).resize(newsize=clip_size)

    def create_background_clip(duration):
        if background_path and os.path.exists(background_path):
            return ImageClip(background_path, duration=duration).resize(newsize=bg_size)
        else:
            return ColorClip(size=bg_size, color=bg_color, duration=duration)

    result_folder = os.path.dirname(final_video_path)
    os.makedirs(result_folder, exist_ok=True)

    longest_duration = max(VideoFileClip(path).duration for path in clip_paths)
    background_clip = create_background_clip(longest_duration)

    composited_clips = []
    for path in clip_paths:
        clip = load_and_resize_clip(path)
        composited_clip = CompositeVideoClip([background_clip, clip.set_position("center")], size=bg_size).set_duration(clip.duration)
        composited_clips.append(composited_clip)

    final_clip = concatenate_videoclips(composited_clips, method='compose')
    final_clip.write_videofile(final_video_path, codec='libx264', fps=24)

def clear_all_folders(figures_path ='./figures',clips_path = './clips',audio_path = './audios',final_video_path = './results'):
    clear_folder(final_video_path)
    clear_folder(audio_path)
    clear_folder(figures_path)
    clear_folder(clips_path)

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File deleted successfully.")
    else:
        print("The file does not exist.")


def excuteAPI(input, figures_path ='./figures',clips_path = './clips',audio_path = './audios',final_video_path = './results/final_video.mp4', backgound = './background1.jpg'):
    remove_file(final_video_path)
    userinput = input +". Make sure are figures are generated correctly and number of figures match the number of explanations."
    clear_folder(audio_path)
    clear_folder(figures_path)
    clear_folder(clips_path)
    exc = True
    prompt = userinput
    response = ""
    while exc:
        response = query_genapi(prompt)
        code, explaination = segment_response(response)
        exc = False
        try:
            if code == []:
                raise ValueError("Regenerate response for the question, Make sure are figures are generated correctly and number of figures match the number of explainations.")
            print(len(code))
            figure_paths = process_figures(code)
        except Exception as e:
            exc = True
            clear_folder(figures_path)
            print(f"\nThere was an error in the response: \n{e}\n Regenerating...\n\n")
            print(response)
            prompt = f"In your previous response:{response} for question{userinput}, the code part raised an error f{e}. Regenarate response to fix it."
    audio_paths = generate_audio_explanations(explaination)
    clip_paths = create_video_clips(figure_paths, audio_paths)
    background_path = backgound
    combine_and_save_video(clip_paths, final_video_path, background_path)
    clear_folder(audio_path)
    clear_folder(figures_path)
    clear_folder(clips_path)

