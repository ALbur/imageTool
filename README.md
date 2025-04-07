# imageTool

这是一个使用Flask构建的简单图像生成服务器应用程序，包含速率限制功能。应用程序可以通过Docker容器运行，并允许用户通过环境变量配置一些参数。

## 先决条件

- Docker
- Python 3.9 或更高版本（用于本地开发）

## 快速开始

### 克隆项目

首先，克隆这个Git仓库到你的本地机器上：

```bash
git clone https://github.com/ALbur/imageTool.git
cd imageTool
```

### 构建Docker镜像

在项目目录下，使用以下命令构建Docker镜像：

```bash
docker build -t image-generation-server .
```

### 运行Docker容器

使用以下命令运行Docker容器：

```bash
docker run -p 3000:3000 -e SECRET=your_secret_key_here -e RATE_LIMIT=10 image-generation-server
```

- `SECRET` 是必需的环境变量，用于验证请求。
- `RATE_LIMIT` 是可选的环境变量，默认值是每分钟5次请求。可以通过这个变量来设置不同的速率限制。

### 访问应用

应用将在`http://localhost:3000`上运行。你可以通过发送HTTP请求来与API交互。

## API 端点

### POST `/your_secret_key_here/generate_image`

- **请求体**：
  - `apiKey`: API密钥。
  - `prompt`: 图像生成提示词。
  - `model`: 使用的模型（默认是`grok-2-image-latest`）。
  - `baseURL`: API的基础URL（默认是`https://api.x.ai`）。
  - `returnFormat`: 返回格式，`url`或`base64`。

- **响应**：
  - 成功时返回生成的图像URL或base64编码的图像。

## Python 请求示例

```python
import requests
import base64
from io import BytesIO
from PIL import Image

def fetch_and_display_image(api_key, prompt, model="grok-2-image-latest", base_url="https://api.x.ai", response_format="b64_json", url="", n=1):
    """
    根据指定参数获取图像并显示。
    
    参数:
        api_key (str): API 密钥
        prompt (str): 提示信息
        model (str, 可选): 使用的模型名称,默认为"grok-2-image"
        base_url (str, 可选): API基础URL,默认为"https://api.x.ai"
        response_format (str, 可选): 返回格式,可以是"url"或"b64_json",默认为"b64_json"
        url (str,必填): 服务器URL,包含secret和路径
        n (int, 可选): 生成图片的数量,范围1-10,默认为1
        
        
    返回:
        如果成功返回图像数组,否则返回None。对于response_format="url"返回图片URL列表,对于"b64_json"返回Base64编码字符串列表。
    """
    
    headers = {"Content-Type": "application/json"}
    data = {
        "apiKey": api_key,
        "prompt": prompt,
        "model": model,
        "baseURL": base_url,
        "response_format": response_format,  # ä¿®正参数名称
        "n": n  # 添加n参数
    }

    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        
        # 检查请求是否成功
        if response.status_code == 200:
            # 解析返回的JSON数据
            response_data = response.json()
            
            # 提取图像数据
            images = response_data.get('images', [])
            
            # 如果返回的是URL
            if response_format == "url":
                # 对于URL格式,可以打印或返回URL
                for i, image_url in enumerate(images):
                    print(f"图片 {i+1} URL: {image_url}")
                
                return images
            
            # 如果返回的是Base64编码的图像数据
            elif response_format == "b64_json":
                displayed_images = []
                for i, base64_image in enumerate(images):
                    try:
                        # 将base64编码图像转换为PIL图像并显示
                        image_data = base64.b64decode(base64_image)
                        image = Image.open(BytesIO(image_data))
                        image.show()
                        print(f"已显示图片 {i+1}")
                        displayed_images.append(image)
                    except Exception as e:
                        print(f"显示图片 {i+1} 时出错: {e}")
                
                # 如果response_data中包含修订后的提示词,打印它们
                if 'revised_prompts' in response_data:
                    for i, revised_prompt in enumerate(response_data['revised_prompts']):
                        print(f"修订后的提示词 {i+1}: {revised_prompt}")
                
                return images
            
            else:
                print(f"不支持的响应格式: {response_format}")
                return None
                
        else:
            print(f"请求失败,状态码:{response.status_code}")
            if response.text:
                print(f"错误信息:{response.text}")
            return None
            
    except Exception as e:
        print(f"请求过程中发生错误:{e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 这些参数需要根据实际{'type': 'ping'}情况填写
    api_key = "your_api_key"
    prompt = "一只可爱的小猫在阳光下玩耍"
    url = "http://localhost:3000/<secret>/generate_image"  # 服务器URL,包含secret和路径
    
    # 调用函数
    images = fetch_and_display_image(
        api_key=api_key,
        prompt=prompt,
        model="grok-2-image",
        base_url="https://api.x.ai",
        response_format="b64_json",
        url=url,
        n=1
    )

```

### 说明

1. **请求库**：使用 `requests` 库来发送 HTTP POST 请求。
2. **数据格式**：请求体使用 JSON 格式，通过 `json` 参数传递。
3. **处理响应**：如果请求成功（状态码为200），则解析返回的 JSON 数据并提取图像的 base64 编码。
4. **显示图像**：使用 `PIL` 库（也称为 `Pillow`）来解码 base64 数据并显示图像。

确保你安装了 `requests` 和 `Pillow` 库，可以通过以下命令安装：

```shell
pip install requests pillow
```

## 许可证

此项目采用MIT许可证。
