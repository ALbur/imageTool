from flask import Flask, request, jsonify
import os
import logging
import requests
import base64
import sys
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 设置日志配置
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# 获取速率限制参数,默认为每分钟5次请求
RATE_LIMIT = os.environ.get('RATE_LIMIT', '5')

# 设置速率限制器
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[f"{RATE_LIMIT} per minute"]
)

# 获取环境变量中的SECRET
SECRET = os.environ.get('SECRET')
API_BASE_URL = os.environ.get('API_BASE_URL', 'https://api.x.ai')

# 检查SECRET是否已设置
if not SECRET:
    logging.error("环境变量SECRET未设置。请通过-e参数指定SECRET。")
    sys.exit(1)

@app.route('/<secret>/generate_image', methods=['POST'])
@limiter.limit(f"{RATE_LIMIT} per minute")
def generate_image(secret):
    if secret != SECRET:
        logging.warning("Unauthorized request with secret: %s", secret)
        return jsonify({"error": "Unauthorized request"}), 401

    data = request.json
    api_key = data.get('apiKey', '')
    prompt = data.get('prompt', '')
    model = data.get('model', 'grok-2-image')  # 按照文档更新默认模型名称
    base_url = data.get('baseURL', API_BASE_URL)
    response_format = data.get('response_format', 'url')  # 使用文档中的参数名称
    n = data.get('n', 1)  # 添加生成图片数量参数,默认为1

    if not api_key or not prompt:
        logging.error("Missing apiKey or prompt in the request")
        return jsonify({"error": "Missing apiKey or prompt"}), 400
    
    # 限制n的范围为1-10
    if n < 1 or n > 10:
        logging.error("n must be between 1 and 10")
        return jsonify({"error": "n must be between 1 and 10"}), 400

    logging.info("使用提示词: %s", prompt)

    request_data = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "response_format": response_format  # 添加响应格式参数
    }

    try:
        api_url = f'{base_url}/v1/images/generations'

        logging.info("Sending request to API URL: %s", api_url)
        response = requests.post(
            api_url,
            headers={
                'accept': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=request_data
        )

        if response.status_code != 200:
            logging.error("API error: %s", response.text)
            return jsonify({"error": response.text}), response.status_code

        result = response.json()

        if "data" in result and len(result["data"]) > 0:
            images = []
            revised_prompts = []
            
            for image_data in result["data"]:
                # 根据response_format处理不同的返回格式
                if response_format == "url" and "url" in image_data:
                    images.append(image_data["url"])
                elif response_format == "b64_json" and "b64_json" in image_data:
                    images.append(image_data["b64_json"])
                
                # 添加修订后的提示词
                if "revised_prompt" in image_data:
                    revised_prompts.append(image_data["revised_prompt"])

            response_data = {"images": images}
            if revised_prompts:
                response_data["revised_prompts"] = revised_prompts
                
            return jsonify(response_data)
        else:
            logging.error("响应中未找到图片数据")
            return jsonify({"error": "响应中未找到图片数据"}), 500

    except Exception as e:
        logging.exception("发生错误: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'type': 'ping'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
