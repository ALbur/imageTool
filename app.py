from flask import Flask, request, jsonify
import os
import logging
import requests
import base64
import sys
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 设置日志配ç½®
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

# 检查SECRET是否已设ç½®
if not SECRET:
    logging.error("环境变量SECRET未设置。请通过-e参数指定SECRET。")
    sys.exit(1)

def process_image_generation(api_key, request_data, is_openai_compatible=False):
    """处理图像生成请求的通用函数"""
    # 提取和标准化参数
    prompt = request_data.get('prompt', '')
    model = request_data.get('model', 'grok-2-image')# 默认模型
    base_url = request_data.get('baseURL', API_BASE_URL)
    response_format = request_data.get('response_format', 'url')
    n = request_data.get('n', 1)
    # 检查必要参数
    if not api_key or not prompt:
        logging.error("Missing apiKey or prompt in the request")
        return jsonify({"error": "Missing apiKey or prompt"}), 400
    
    # 限制n的范围为1-10
    if n < 1 or n > 10:
        logging.error("n must be between 1 and 10")
        return jsonify({"error": "n must be between 1 and 10"}), 400

    # 如果模型名称以dall-e 开头,替换为 grok-2-image-latest
    if isinstance(model, str) and model.startswith('dall-e'):
        logging.info(f"替换模型 {model} 为 grok-2-image-latest")
        model = 'grok-2-image-latest'

    logging.info("使用提示词: %s", prompt)
    logging.info(f"使用模型: {model}")

    # 构建API请求数据,只保留X.AI API支持的参数
    api_request_data = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "response_format": response_format
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
            json=api_request_data
        )

        if response.status_code != 200:
            logging.error("API error: %s", response.text)
            return jsonify({"error": response.text}), response.status_code

        result = response.json()

        if "data" in result and len(result["data"]) > 0:
            # 如果是OpenAI兼容模式,则保持OpenAI格式的响应
            if is_openai_compatible:
                # 创建OpenAIæ ¼式的响应
                openai_response = {
                    "created": int(time.time()),
                    "data": []
                }
                
                for image_data in result["data"]:
                    item = {}
                    if response_format == "url" and "url" in image_data:
                        item["url"] = image_data["url"]
                    elif response_format == "b64_json" and "b64_json" in image_data:
                        item["b64_json"] = image_data["b64_json"]
                    
                    if "revised_prompt" in image_data:
                        item["revised_prompt"] = image_data["revised_prompt"]
                    openai_response["data"].append(item)
                
                return jsonify(openai_response)
            else:
                # 原始的响应格式
                images = []
                revised_prompts = []
                
                for image_data in result["data"]:
                    if response_format == "url" and "url" in image_data:
                        images.append(image_data["url"])
                    elif response_format == "b64_json" and "b64_json" in image_data:
                        images.append(image_data["b64_json"])
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

@app.route('/<secret>/generate_image', methods=['POST'])
@limiter.limit(f"{RATE_LIMIT} per minute")
def generate_image(secret):
    """原始的图像生成端点"""
    if secret != SECRET:
        logging.warning("Unauthorized request with secret: %s", secret)
        return jsonify({"error": "Unauthorized request"}), 401

    data = request.json
    api_key = data.get('apiKey', '')
    return process_image_generation(api_key, data, is_openai_compatible=False)

@app.route('/<secret>/v1/images/generations', methods=['POST'])
@limiter.limit(f"{RATE_LIMIT} per minute")
def openai_compatible_generate(secret):
    """OpenAI兼容的图像生成端点"""
    if secret != SECRET:
        logging.warning("Unauthorized request with secret: %s", secret)
        return jsonify({"error": "Unauthorized request"}), 401

    # 从请求头获取API密钥
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        api_key = auth_header.split(' ')[1]
    else:
        api_key = ''# 获取请求数据,忽略不支持的参数
    data = request.json
    logging.info(f"收到请求参数: {data}")
    
    # 如果请求中存在不支持的参数,记录日志但不返回错误
    unsupported_params = ['size', 'quality', 'style']
    for param in unsupported_params:
        if param in data:
            logging.info(f"忽略不支持的参数: {param}={data[param]}")
    
    return process_image_generation(api_key, data, is_openai_compatible=True)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'type': 'ping'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
