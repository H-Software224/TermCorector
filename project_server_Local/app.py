from flask import Flask, render_template, request, redirect, url_for
import os
from markupsafe import Markup
import re

import subprocess
from threading import Thread
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/' # 업로드 폴더 설정

# uploads 폴더가 없으면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 출력 전 txt 파일 전처리
def process_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    pattern = r'\[(.*?)\->(.*?)\]'

    def replacement(match):
        incorrect_word = match.group(1)
        correct_words = match.group(2).split(', ')
        if len(correct_words) > 1:
            # Multiple correct words: apply red highlight and allow selection
            options = ', '.join(correct_words)
            return f'<span class="highlighted red-highlight" data-options="{options}">{incorrect_word}</span>'
        else:
            # Single correct word: apply yellow highlight
            return f'<span class="highlighted yellow-highlight" data-wrong="{incorrect_word}">{correct_words[0]}</span>'

    processed_text = re.sub(pattern, replacement, content)
    
    paragraphs = processed_text.split('\n\n')
    processed_text = ''.join(f'<div class="paragraph">{p.replace("\n", "<br>")}</div><br>' for p in paragraphs)

    return Markup(processed_text)

# 메인 페이지
@app.route('/', methods=['GET', 'POST'])
def Index():
    return render_template('design.html')

# 파일 업로드 처리
@app.route('/upload', methods=['GET','POST'])
def upload_file():
    if 'audio_file' not in request.files or 'pdf_file' not in request.files:
        return "No file part in the request", 400
    
    audio_file = request.files['audio_file']
    pdf_files = request.files.getlist('pdf_file')
    
     # 확장자 검사 (오디오 파일)
    if not audio_file.filename.endswith('.m4a'):
        return "Unsupported file extension for audio file", 400

    # 확장자 검사 및 파일 저장 (PDF 파일들)
    saved_pdf_paths = []
    for pdf in pdf_files:
        if not pdf.filename.endswith('.pdf'):
            return "Unsupported file extension in one of the PDF files", 400
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf.filename)
        pdf.save(pdf_path)
        saved_pdf_paths.append(pdf_path)

    # 오디오 파일 저장
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
    audio_file.save(audio_path)

    # 업로드 완료 후 대기화면 진입
    render_template('wait.html')
    return redirect(url_for('wait'))

# 대기화면, 결과 텍스트 감지되면 결과 화면으로 진입
result_file_path = 'results/result_text.txt'

def run_script():
    # 파일 없는 경우
    if not os.path.exists(result_file_path):
        subprocess.run(["python", "main.py"], shell=True)

@app.route('/wait', methods=['GET', 'POST'])
def wait():
    if not os.path.exists(result_file_path):
        thread = Thread(target=run_script)
        thread.start()
    return render_template('wait.html')

@app.route('/check_status')
def check_status():
    if os.path.exists(result_file_path):
        return redirect(url_for('index'))
    return "", 204  # 204 No Content

@app.route('/index')
def index():
    upload_folder = 'uploads'
    file_name = None

    for file in os.listdir(upload_folder):
        if file.endswith('.m4a'):
            file_name = file
            break

    if os.path.exists(result_file_path):
        processed_text = process_text_file(result_file_path)
        return render_template('index.html', processed_text=processed_text, file_name=file_name)
    else:
        return redirect(url_for('wait'))

@app.route('/menu')
def menu():
    upload_folder = 'uploads'
    file_name = None

    for file in os.listdir(upload_folder):
        if file.endswith('.m4a'):
            file_name = file
            break

    return render_template('menu.html', file_name=file_name)

if __name__ == "__main__":
    app.run(debug=True)