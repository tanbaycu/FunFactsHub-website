from flask import Flask, request, jsonify, send_file
from deep_translator import GoogleTranslator
import requests

app = Flask(__name__)

def translate_text(text):
    translator = GoogleTranslator(source='en', target='vi')
    return translator.translate(text)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    translation = translate_text(text)
    return jsonify({'translation': translation})

@app.route('/useless-fact')
def useless_fact():
    response = requests.get('https://uselessfacts.jsph.pl/random.json?language=en')
    data = response.json()
    return jsonify({'fact': data['text']})

@app.route('/number-fact')
def number_fact():
    number = request.args.get('number', 'random')
    response = requests.get(f'http://numbersapi.com/{number}')
    return jsonify({'fact': response.text})

@app.route('/cat-fact')
def cat_fact():
    response = requests.get('https://catfact.ninja/fact')
    data = response.json()
    return jsonify({'fact': data['fact']})

@app.route('/joke')
def joke():
    response = requests.get('https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit')
    data = response.json()
    if data['type'] == 'single':
        joke = data['joke']
    else:
        joke = f"{data['setup']} {data['delivery']}"
    return jsonify({'joke': joke})

@app.route('/dog-image')
def dog_image():
    response = requests.get('https://dog.ceo/api/breeds/image/random')
    data = response.json()
    return jsonify({'image_url': data['message']})

if __name__ == '__main__':
    app.run(debug=True)


app = app.wsgi_app