import io
import json
import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, redirect, url_for
from playhouse.shortcuts import model_to_dict

from models import create_tables, Chat, Message
from utils import llm_chat

app = Flask(__name__, static_folder='static')

# Load environment variables
load_dotenv()


@app.route('/', methods=['GET'])
def index_page():
    # GET request: display the form with default values
    return render_template('setup.html')



@app.route('/chat/<chat_id>', methods=['GET', 'POST'])
def view_chat(chat_id):
    if request.method == 'POST':
        chat = Chat.get_by_id_str(chat_id)
        return jsonify({
            'success': True,
            'data': model_to_dict(chat),
        })
    else:
        return render_template('chat.html', chat_id=chat_id)


@app.route('/create', methods=['POST'])
def create_chat():
    request_json = request.get_json()
    my_name = request_json['my_name']
    my_avatar = request_json.get('my_avatar')
    my_personality = request_json['my_personality']
    other_name = request_json['other_name']
    other_avatar = request_json.get('other_avatar')
    other_personality = request_json['other_personality']
    relationship = request_json['relationship']
    communication_history = request_json['communication_history']
    objective = request_json['objective']

    chat = Chat.create_chat({
        'my_name': my_name,
        'my_avatar': my_avatar,
        'my_personality': my_personality,
        'other_name': other_name,
        'other_avatar': other_avatar,
        'other_personality': other_personality,
        'relationship': relationship,
        'communication_history': communication_history,
        'objective': objective
    })

    return jsonify({
        'success': True,
        'redirect': url_for('view_chat', chat_id=chat.id)
    })

@app.route('/error')
def error_page():
    error_message = request.args.get('message')
    """错误页面"""
    return render_template('error.html', error_message=error_message)



@app.route('/static/fonts/<filename>')
def serve_font(filename):
    """提供字体文件服务"""
    from flask import send_from_directory
    return send_from_directory('static/fonts', filename)

@app.route('/send', methods=['POST'])
def send_message():
    """处理发送消息的请求"""
    request_json = request.get_json()
    chat_id = request_json.get('chat_id')
    sender = request_json.get('sender')
    message = request_json.get('message')

    if not chat_id or not message or not sender:
        return jsonify({'success': False, 'error': 'Missing chat_id or message'}), 400

    chat = Chat.get_by_id_str(chat_id)
    if not chat:
        return jsonify({'success': False, 'error': 'Chat not found'}), 404

    m = Message.create_message(chat_id, sender, message)


    return jsonify({'success': True, 'message': model_to_dict(m)})


@app.route('/generate_reply', methods=['POST'])
def generate_reply():
    chat_id = request.json.get('chat_id')
    chat = Chat.get_by_id_str(chat_id)
    if not chat:
        return jsonify({'success': False, 'error': 'Chat not found'}), 404
    messages = Message.select().where(Message.chat_id == chat_id).order_by(Message.created_at.asc())

    messages_text = '\n'.join([f"{msg.created_at} [{msg.sender}]: {msg.content}" for msg in messages])

    prompt = f"""你是一位经验丰富、洞察深刻的情感大师。你擅长深度解读对话的弦外之音，精准把握双方的情绪和意图，并能基于此给出最能促进积极沟通、体现高情商的最佳回复建议。你的语气应该冷静、客观，同时富有同理心和建设性。

你的核心任务： 根据我提供的聊天记录，分析当前的对话状态、双方的情绪与需求，并给出接下来最合适的、具有高情商的回复建议。

## 背景信息
### 聊天双方信息
[{chat.my_name}] 是我， 我的个性特点是：[{chat.my_personality}]。 
[{chat.other_name}] 是对方，对方的个性特点是：[{chat.other_personality}]。

### 双方的关系及交往记录
我们之间的关系是 [{chat.relationship}]。曾经的交往记录包括：[{chat.communication_history}]。

### 当前对话目标
我希望通过这次对话达到的目标是：[{chat.objective}]。

### 聊天记录
{messages_text}

## 分析建议时重点关注
### 上下文理解与情绪洞察：
    - 仔细分析聊天记录中的每一句话，理解其字面意思和潜在含义。
    - 判断对话双方（尤其是我方和对方）当前的情绪状态（例如：开心、焦虑、失望、愤怒、困惑等）。
    - 识别对方语言背后可能未明说的需求、期望或担忧。
    - 指出对话中可能存在的误解或沟通障碍。
    
### 沟通目标导向：
    - 帮助我明确在当前对话情境下，我希望通过回复达到什么沟通目标（例如：缓和气氛、解决问题、表达关心、澄清误会、拒绝请求等）。
    - 你建议的回复应服务于这个沟通目标。
    
### 高情商回复构建：
    - 共情与认同： 指导我如何通过回复来表达对对方情绪的理解和认同（如果合适）。例如：“我能感觉到你现在有些着急/失落…”
    - 清晰与真诚： 确保回复既清晰表达我的观点/感受/需求，又显得真诚不敷衍。
    - 积极与建设性： 避免使用指责、抱怨、消极或模糊不清的语言。引导对话向积极和建设性的方向发展。
    - 尊重与边界： 即使在困难的对话中，也要保持对对方的尊重，同时注意维护自己的合理边界。
    - 提问技巧： 在需要时，建议使用开放式、探索性的问题来鼓励对方进一步表达，或澄清疑虑。
    - “黄金回应”与“避坑指南”： 针对具体情境，直接给出建议的回复句式，并说明为什么这样回复是最佳的。同时，指出哪些类型的回复应该避免以及为什么。

### 其他注意事项
    - 回复要简短，尽量20个字内，适合即时聊天工具的交流风格。
    - 避免使用专业术语或复杂的表达方式，确保回复通俗易懂。
    - 只需要生成 [{chat.my_name}] 的回复内容，不需要生成对方视角的回复。




## 响应要求
- 直接给出回复内容文本，前后不需要解释或分析，不需要说明理由。
- 如果无法回答，直接返回“无法生成回复”。


现在请根据以上信息，给出  [{chat.my_name}]  最合适的回复建议。请确保回复内容具有高情商，能够促进积极沟通，并体现出对双方情绪和需求的深刻理解。
    """

    reply = llm_chat(prompt)

    return jsonify({'success': True, 'data': reply})



if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5020)
