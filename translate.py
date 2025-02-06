import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import configparser
import threading
import queue
import requests

class TranslateApp:
    def __init__(self, master):
        self.master = master
        master.title("FOSSCOPE 翻译工具")
        master.geometry("800x600")

        # 初始化配置
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        if not self.config.has_section('deepseek'):
            self.config.add_section('deepseek')

        # 初始化队列用于线程通信
        self.queue = queue.Queue()

        # 创建界面组件
        self.create_widgets()

        # 定期检查队列
        self.master.after(100, self.process_queue)

    def create_widgets(self):
        # 路径选择部分
        path_frame = ttk.Frame(self.master)
        path_frame.pack(pady=10, fill=tk.X)

        ttk.Label(path_frame, text="项目路径:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="加载", command=self.load_project).pack(side=tk.LEFT, padx=5)

        # 分类选择
        self.category_var = tk.StringVar()
        category_frame = ttk.Frame(self.master)
        category_frame.pack(pady=5)

        ttk.Label(category_frame, text="选择分类:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var,
                                           values=['news', 'talk', 'tech'], state='disabled')
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', self.load_files)

        # 文件列表
        list_frame = ttk.Frame(self.master)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 操作按钮
        button_frame = ttk.Frame(self.master)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="翻译", command=self.start_translation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="设置", command=self.open_settings).pack(side=tk.LEFT, padx=5)

    def browse_path(self):
        path = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)

    def load_project(self):
        self.project_path = self.path_entry.get()
        if not self.validate_project_structure():
            messagebox.showerror("错误", "项目目录结构不正确")
            return

        self.category_combo.config(state='readonly')
        self.load_files()

    def validate_project_structure(self):
        required = [
            'sources',
            'translated',
            'sources/news',
            'sources/talk',
            'sources/tech',
            'translated/news',
            'translated/talk',
            'translated/tech'
        ]
        return all(os.path.exists(os.path.join(self.project_path, p)) for p in required)

    def load_files(self, event=None):
        category = self.category_var.get()
        if not category:
            return

        source_dir = os.path.join(self.project_path, 'sources', category)
        files = [f for f in os.listdir(source_dir)
                 if os.path.isfile(os.path.join(source_dir, f)) and f != 'README.md']

        self.file_listbox.delete(0, tk.END)
        for f in files:
            self.file_listbox.insert(tk.END, f)

    def start_translation(self):
        selected = self.file_listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要翻译的文件")
            return

        files = [self.file_listbox.get(i) for i in selected]
        category = self.category_var.get()

        # 在独立线程中运行翻译
        threading.Thread(target=self.translate_files,
                         args=(files, category), daemon=True).start()

    def translate_files(self, files, category):
        try:
            api_key = self.config.get('deepseek', 'api_key')
            endpoint = self.config.get('deepseek', 'api_endpoint')
            prompt = self.config.get('deepseek', 'prompt', fallback=self.get_default_prompt())

            source_dir = os.path.join(self.project_path, 'sources', category)
            target_dir = os.path.join(self.project_path, 'translated', category)

            for filename in files:
                source_path = os.path.join(source_dir, filename)
                target_path = os.path.join(target_dir, filename)

                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                translated = self.translate_content(content, prompt, api_key, endpoint)

                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(translated)

                self.queue.put(('success', f"{filename} 翻译完成"))

        except Exception as e:
            self.queue.put(('error', f"翻译失败: {str(e)}"))

    def translate_content(self, content, prompt, api_key, endpoint):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content}
            ],
            "model": "deepseek-chat",
            "temperature": 0.3
        }

        response = requests.post(endpoint, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    def delete_files(self):
        selected = self.file_listbox.curselection()
        if not selected:
            return

        if not messagebox.askyesno("确认", "确定要删除选中的文件吗？"):
            return

        category = self.category_var.get()
        source_dir = os.path.join(self.project_path, 'sources', category)

        for i in selected:
            filename = self.file_listbox.get(i)
            os.remove(os.path.join(source_dir, filename))

        self.load_files()

    def open_settings(self):
        settings = tk.Toplevel(self.master)
        settings.title("API 设置")

        ttk.Label(settings, text="API Key:").grid(row=0, column=0, padx=5, pady=5)
        api_key_entry = ttk.Entry(settings, width=50)
        api_key_entry.insert(0, self.config.get('deepseek', 'api_key', fallback=''))
        api_key_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings, text="API Endpoint:").grid(row=1, column=0, padx=5, pady=5)
        endpoint_entry = ttk.Entry(settings, width=50)
        endpoint_entry.insert(0, self.config.get('deepseek', 'api_endpoint',
                                                 fallback='https://api.deepseek.com/v1/chat/completions'))
        endpoint_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(settings, text="提示词:").grid(row=2, column=0, padx=5, pady=5)
        prompt_text = tk.Text(settings, width=60, height=15)
        prompt_text.insert('1.0', self.config.get('deepseek', 'prompt', fallback=self.get_default_prompt()))
        prompt_text.grid(row=2, column=1, padx=5, pady=5)

        def save_settings():
            self.config.set('deepseek', 'api_key', api_key_entry.get())
            self.config.set('deepseek', 'api_endpoint', endpoint_entry.get())
            self.config.set('deepseek', 'prompt', prompt_text.get('1.0', tk.END).strip())

            with open('config.ini', 'w') as f:
                self.config.write(f)

            settings.destroy()

        ttk.Button(settings, text="保存", command=save_settings).grid(row=3, column=1, pady=10)

    def get_default_prompt(self):
        return """你是一个中英文翻译专家，将用户输入的英文科技新闻资讯或者英文技术文章翻译成中文，保持专业术语准确，不要翻译文件中的标记元素，输出时完整输出文件中的所有元素。并确保符合中文语言习惯，你可以调整语气和风格，并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文注意链接之间增加空格、中英文之间需要增加空格、中文与数字之间需要增加空格、数字与单位之间需要增加空格、全角标点与其他字符之间不加空格、，将中文引号“”转换为「」。"""

    def process_queue(self):
        while not self.queue.empty():
            msg_type, msg = self.queue.get()
            if msg_type == 'success':
                messagebox.showinfo("成功", msg)
            elif msg_type == 'error':
                messagebox.showerror("错误", msg)
        self.master.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslateApp(root)
    root.mainloop()
