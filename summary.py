import os
import inquirer
import yaml
from inquirer import prompt, List
import requests
from dotenv import load_dotenv
import json

# 用于存储满足条件的文件信息
todo_files = []

# 遍历目录和子目录下的所有.md文件
def traverse_directory(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                process_md_file(filepath)

# 处理单个.md文件
def process_md_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分离yaml front matter和markdown内容
    front_matter, markdown_content = separate_front_matter(content)
    
    if front_matter and 'summary' in front_matter and front_matter['summary'] == 'todo':
        todo_files.append({
            'file_path': filepath,
            'title': front_matter.get('title', 'No Title'),
            'content': markdown_content
        })

# 分离yaml front matter和markdown内容
def separate_front_matter(content):
    front_matter = {}
    markdown_content = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front_matter = yaml.safe_load(parts[1])
            markdown_content = parts[2:]

    return front_matter, markdown_content

# 交互式选择文件
def select_file():
    choices = [{'title': f"{file['title']}", 'path': file['file_path']} for file in todo_files]
    questions = [inquirer.Checkbox('selected_file', message='选择一个文件来修改summary字段:', choices=choices)]
    selected_file = prompt(questions)['selected_file']
    return selected_file

def update_summary(path:str,instr:str):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        new_content = text.replace('summary: "todo"','summary: "%s"' % instr)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        print('%s 已更新summary字段。' % path)


def ai_summary(text: str):
    load_dotenv()
    # Get environment variables
    token = os.getenv("bd_qianfan_token")
    headers = {
        "Content-Type": "application/json;"
    }
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + token
    response = requests.post(url, headers=headers, data=json.dumps({"messages": [{"role": "user", "content":"总结概述下面文章为一行内 100 汉字以内的一到三句话: " +  text}]}))
    obj = response.json()
    result = obj['result']
    usage_total_tokens = obj['usage']['total_tokens']
    print("Use {} tokens.".format(usage_total_tokens))
    return result


# 主程序
if __name__ == '__main__':
    target_directory = 'content/posts'  # 修改为实际的目录路径
    traverse_directory(target_directory)

    if todo_files:
        selected_files = select_file()
        print(selected_files)
        choices = ["确定","取消"]
        check = [List('AI Summary', message='确认：:', choices=choices)]
        new_summary = prompt(check)
        print(new_summary['AI Summary'])
        if new_summary['AI Summary'] == '确定':
            for it in selected_files:
                print(it['title'],it['path'])
                with open(it['path'], 'r', encoding='utf-8') as f:
                    text = f.read()
                    front_matter, markdown_content = separate_front_matter(text)
                    new_ai_summary = ai_summary("---".join(markdown_content))
                    print(new_ai_summary)
                    update_summary(it['path'],new_ai_summary)

        # 替换选中文件的summary字段并保存

    else:
        print('没有符合条件的文件。')
