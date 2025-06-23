from flask import Flask, request, jsonify, send_file, redirect, url_for
from deep_translator import GoogleTranslator
from user_agents import parse
import requests
import random
import logging
import os

# Tắt các log không cần thiết
logging.getLogger('werkzeug').setLevel(logging.ERROR)


app = Flask(__name__)

# Tắt debug logging
app.logger.setLevel(logging.ERROR)

def get_device_info():
    """Phân tích user agent để xác định thiết bị"""
    user_agent_string = request.headers.get('User-Agent', '')
    user_agent = parse(user_agent_string)
    
    return {
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'is_bot': user_agent.is_bot,
        'browser': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string,
        'os': user_agent.os.family,
        'os_version': user_agent.os.version_string,
        'device': user_agent.device.family,
        'user_agent_string': user_agent_string
    }

def should_use_mobile():
    """Xác định có nên sử dụng mobile version không"""
    device_info = get_device_info()
    
    # Ưu tiên mobile cho mobile devices và tablets nhỏ
    if device_info['is_mobile']:
        return True
    
    # Tablet có thể dùng desktop hoặc mobile tùy kích thước
    # Nhưng mặc định sẽ dùng mobile cho tablet
    if device_info['is_tablet']:
        return True
    
    # Bot và PC dùng desktop
    return False

def translate_text(text):
    try:
        translator = GoogleTranslator(source='en', target='vi')
        return translator.translate(text)
    except:
        return "Không thể dịch lúc này"

@app.route('/')
def index():
    """Main route với automatic device detection"""
    if should_use_mobile():
        return send_file('mobile.html')
    else:
        return send_file('index.html')

@app.route('/desktop')
def desktop():
    """Force desktop version"""
    return send_file('index.html')

@app.route('/mobile')
def mobile():
    """Force mobile version"""
    return send_file('mobile.html')

@app.route('/device-info')
def device_info():
    """Debug endpoint để xem thông tin thiết bị"""
    device_info = get_device_info()
    recommended_version = 'mobile' if should_use_mobile() else 'desktop'
    
    return jsonify({
        **device_info,
        'recommended_version': recommended_version,
        'current_route': request.endpoint
    })

@app.route('/switch-version')
def switch_version():
    """Endpoint để chuyển đổi version"""
    current_version = request.args.get('from', 'auto')
    
    if current_version == 'mobile':
        return redirect(url_for('desktop'))
    elif current_version == 'desktop':
        return redirect(url_for('mobile'))
    else:
        # Auto detect
        return redirect(url_for('index'))

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    translation = translate_text(text)
    return jsonify({'translation': translation})

@app.route('/useless-fact')
def useless_fact():
    try:
        response = requests.get('https://uselessfacts.jsph.pl/random.json?language=en', timeout=5)
        data = response.json()
        return jsonify({'fact': data['text']})
    except:
        return jsonify({'fact': 'The average person walks past 36 murderers in their lifetime.'})

@app.route('/number-fact')
def number_fact():
    number = request.args.get('number', 'random')
    
    # Nếu là random, tạo số ngẫu nhiên
    if number == 'random':
        number = random.randint(1, 1000)
    
    try:
        response = requests.get(f'http://numbersapi.com/{number}', timeout=5)
        return jsonify({'fact': response.text, 'number': number})
    except:
        return jsonify({'fact': f'The number {number} is interesting in its own way.', 'number': number})

@app.route('/cat-fact')
def cat_fact():
    try:
        # Thử lấy nhiều cat facts
        count = random.randint(3, 5)
        response = requests.get(f'https://meowfacts.herokuapp.com/?count={count}', timeout=5)
        data = response.json()
        
        if data.get('data'):
            facts_data = data['data']
            
            # Xử lý cả trường hợp data là list hoặc object
            if isinstance(facts_data, list):
                # Nếu là list, lấy ngẫu nhiên
                selected_fact = random.choice(facts_data)
            elif isinstance(facts_data, dict):
                # Nếu là object với keys, chuyển thành list
                facts_list = [facts_data[key] for key in facts_data.keys()]
                selected_fact = random.choice(facts_list)
            else:
                raise Exception("Unexpected data format")
                
            return jsonify({'fact': selected_fact})
        else:
            raise Exception("No data received")
            
    except Exception as e:
        print(f"Error fetching cat fact: {e}")
        # Fallback với một fact cụ thể bằng ID
        try:
            fallback_id = random.randint(1, 100)
            response = requests.get(f'https://meowfacts.herokuapp.com/?id={fallback_id}', timeout=5)
            data = response.json()
            if data.get('data'):
                facts_data = data['data']
                if isinstance(facts_data, list) and len(facts_data) > 0:
                    return jsonify({'fact': facts_data[0]})
                elif isinstance(facts_data, dict) and '0' in facts_data:
                    return jsonify({'fact': facts_data['0']})
        except:
            pass
        
        # Fallback cuối cùng với facts tĩnh
        fallback_facts = [
            "Cats have been domesticated for over 4,000 years.",
            "A group of cats is called a clowder.",
            "Cats can rotate their ears 180 degrees.",
            "A cat's purr vibrates at a frequency that promotes bone healing.",
            "Cats have a third eyelid called a nictitating membrane.",
            "Cats spend 70% of their lives sleeping.",
            "A cat's brain is biologically more similar to a human brain than it is to a dog's.",
            "Cats make about 100 different sounds while dogs make only about 10."
        ]
        return jsonify({'fact': random.choice(fallback_facts)})

@app.route('/joke')
def joke():
    try:
        response = requests.get('https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit', timeout=5)
        data = response.json()
        if data['type'] == 'single':
            joke = data['joke']
        else:
            joke = f"{data['setup']} {data['delivery']}"
        return jsonify({'joke': joke})
    except:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why don't eggs tell jokes? They'd crack each other up!"
        ]
        return jsonify({'joke': random.choice(jokes)})

@app.route('/dog-image')
def dog_image():
    try:
        response = requests.get('https://dog.ceo/api/breeds/image/random', timeout=5)
        data = response.json()
        return jsonify({'image_url': data['message']})
    except:
        return jsonify({'image_url': 'https://images.unsplash.com/photo-1552053831-71594a27632d?w=800&h=600&fit=crop'})

@app.route('/github-trending')
def github_trending():
    try:
        response = requests.get('https://api.github.com/search/repositories?q=created:>2023-01-01&sort=stars&order=desc', timeout=5)
        data = response.json()
        if data.get('items') and len(data['items']) > 0:
            repo = data['items'][0]
            return jsonify({
                'name': repo['name'],
                'description': repo['description'],
                'url': repo['html_url'],
                'stars': repo['stargazers_count'],
                'language': repo['language']
            })
        else:
            raise Exception("No trending repositories found")
    except:
        return jsonify({
            'name': "Sample Repository",
            'description': "Unable to load trending repository at the moment.",
            'url': "#",
            'stars': "N/A",
            'language': "N/A"
        })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors với device detection"""
    if should_use_mobile():
        return send_file('mobile.html'), 200
    else:
        return send_file('index.html'), 200

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    device_info = get_device_info()
    return jsonify({
        'status': 'healthy',
        'version': 'mobile' if should_use_mobile() else 'desktop',
        'device_type': 'mobile' if device_info['is_mobile'] else 'tablet' if device_info['is_tablet'] else 'desktop',
        'browser': f"{device_info['browser']} {device_info['browser_version']}",
        'os': f"{device_info['os']} {device_info['os_version']}"
    })

if __name__ == '__main__':
    print("🚀 Starting FunFacts Hub with intelligent device detection...")
    print("📱 Mobile/Tablet devices → mobile.html")
    print("💻 Desktop/PC devices → index.html")
    print("🔍 Debug endpoints:")
    print("   - /device-info : Xem thông tin thiết bị")
    print("   - /health : Health check")
    print("   - /desktop : Force desktop version")
    print("   - /mobile : Force mobile version")
    print("   - /switch-version : Chuyển đổi version")
    app.run(debug=False, port=5000, use_reloader=False)
