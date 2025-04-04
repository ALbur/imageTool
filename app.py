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

# 获取速率限制参数，默认为每分钟5次请求
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
    model = data.get('model', 'grok-2-image-latest')
    base_url = data.get('baseURL', API_BASE_URL)
    return_format = data.get('returnFormat', 'url')

    if not api_key or not prompt:
        logging.error("Missing apiKey or prompt in the request")
        return jsonify({"error": "Missing apiKey or prompt"}), 400

    logging.info("使用提示词: %s", prompt)

    request_data = {
        "model": model,
        "prompt": prompt
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
            for image_data in result["data"]:
                if "url" in image_data:
                    url = image_data["url"]
                    if return_format == "url":
                        images.append(url)
                    elif return_format == "base64":
                        try:
                            img_response = requests.get(url)
                            img_response.raise_for_status()
                            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                            images.append(image_base64)
                        except requests.exceptions.RequestException as e:
                            logging.error("下载图片时出错: %s", e)
                            return jsonify({"error": "Error downloading image"}), 500

            return jsonify({"images": images})

        else:
            logging.error("响应中未找到图片数据")
            return jsonify({"error": "响应中未找到图片数据"}), 500

    except Exception as e:
        logging.exception("发生错误: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)