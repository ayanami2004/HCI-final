from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import speech_recognition as sr
from googletrans import Translator
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'  # SQLite database, filename uploads.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)  # SQLAlchemy instance in application context
translator = Translator()

# Database model definition
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255))
    transcription = db.Column(db.Text)
    translation = db.Column(db.Text)
    source_language = db.Column(db.String(10))

    def __repr__(self):
        return f'<Upload {self.id}>'

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

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
        
        # Determine target language for translation
        if source_language == 'zh-CN':
            target_language = 'en'
        elif source_language == 'en':
            target_language = 'zh-CN'
        elif source_language == 'fr':
            target_language = 'zh-CN'  # French to Chinese translation
        elif source_language == 'zh-CN-fr':
            target_language = 'fr'  # Chinese to French translation
        elif source_language == 'fr-en':
            target_language = 'en'  # French to English translation
        elif source_language == 'en-fr':
            target_language = 'fr'  # English to French translation
        else:
            return jsonify({"error": "Unsupported source language"}), 400
        
        translated = translator.translate(transcription, dest=target_language)

        # Save upload record to database
        new_upload = Upload(original_filename=audio_file.filename,
                            transcription=transcription,
                            translation=translated.text,
                            source_language=source_language)
        db.session.add(new_upload)
        db.session.commit()

        return jsonify({"transcription": transcription, "translation": translated.text})
    
    except sr.UnknownValueError:
        return jsonify({"error": "Speech Recognition could not understand audio"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Could not request results from Speech Recognition service; {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_uploads')
def get_uploads():
    # Get all upload records
    uploads = Upload.query.all()
    upload_data = []
    for upload in uploads:
        upload_data.append({
            'id': upload.id,
            'original_filename': upload.original_filename,
            'transcription': upload.transcription,
            'translation': upload.translation,
            'source_language': upload.source_language
        })
    return jsonify(upload_data)

@app.route('/clear_uploads', methods=['POST'])
def clear_uploads():
    try:
        # Delete all records from the Upload table
        db.session.query(Upload).delete()
        db.session.commit()
        return jsonify({"message": "Upload history cleared successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
