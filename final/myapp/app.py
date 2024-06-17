from flask import Flask, request, jsonify, render_template
import speech_recognition as sr
from googletrans import Translator
from io import BytesIO

app = Flask(__name__)
translator = Translator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/luyin')
def luyin_page():
    return render_template('luyin.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files and 'audio' not in request.form:
        return jsonify({"error": "No audio file provided"}), 400

    if 'audio' in request.files:
        # Handle file upload
        audio_file = request.files['audio']
        source_language = request.form['source_language']

        recognizer = sr.Recognizer()
        audio_data = None

        try:
            with sr.AudioFile(BytesIO(audio_file.read())) as source:
                audio_data = recognizer.record(source)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif 'audio' in request.form:
        # Handle real-time recording
        audio_data = request.files['audio'].read()
        source_language = request.form['source_language']

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio_data)

    else:
        return jsonify({"error": "No audio file provided"}), 400

    try:
        transcription = recognizer.recognize_google(audio_data, language=source_language)
        
        # Determine target language based on source language
        if source_language == 'zh-CN':
            target_language = 'en'
        elif source_language == 'en':
            target_language = 'zh-CN'
        elif source_language == 'fr':
            target_language = 'zh-CN' 
        elif source_language == 'zh-CN-fr':
            target_language = 'fr'  
        elif source_language == 'fr-en':
            target_language = 'en'  
        elif source_language == 'en-fr':
            target_language = 'fr'  
        else:
            return jsonify({"error": "Unsupported source language"}), 400
        
        translated = translator.translate(transcription, dest=target_language)
        return jsonify({"transcription": transcription, "translation": translated.text})
    
    except sr.UnknownValueError:
        return jsonify({"error": "Speech Recognition could not understand audio"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Could not request results from Speech Recognition service; {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
