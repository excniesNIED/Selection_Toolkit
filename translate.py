import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import threading
import logging
from datetime import datetime

class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FOSSCOPE 翻译工具")
        self.setup_ui()
        self.setup_logging()
        self.config = {
            'api_base': "https://api.deepseek.com/v1",
            'api_key': "",
            'model': "deepseek-reasoner",
            'prompt': ""
        }

    def setup_logging(self):
        self.logger = logging.getLogger('TranslationTool')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def setup_ui(self):
        # 路径设置
        path_frame = ttk.Frame(self.root)
        path_frame.pack(pady=5, fill=tk.X)

        ttk.Label(path_frame, text="项目路径:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="加载", command=self.load_project).pack(side=tk.LEFT, padx=5)

        # 分类选择
        self.category_var = tk.StringVar()
        category_frame = ttk.Frame(self.root)
        category_frame.pack(pady=5, fill=tk.X)
        ttk.Label(category_frame, text="分类:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var,
                                           values=["news", "talk", "tech"], state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.load_files)

        # 文件列表
        self.file_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=60, height=15)
        self.file_listbox.pack(pady=5, fill=tk.BOTH, expand=True)

        # 操作按钮
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5, fill=tk.X)
        ttk.Button(button_frame, text="翻译选中", command=self.start_translation).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="删除选中", command=self.delete_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="设置", command=self.show_settings).pack(side=tk.RIGHT)

        # 日志显示
        self.log_text = scrolledtext.ScrolledText(self.root, height=10)
        self.log_text.pack(pady=5, fill=tk.BOTH, expand=True)

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def load_project(self):
        self.project_path = self.path_entry.get()
        if not os.path.exists(os.path.join(self.project_path, "sources")):
            messagebox.showerror("错误", "无效的项目路径")
            return
        self.log("项目加载成功")

    def load_files(self, event=None):
        category = self.category_var.get()
        if not category:
            return
        source_dir = os.path.join(self.project_path, "sources", category)
        try:
            files = [f for f in os.listdir(source_dir) if f.endswith('.md')]
            self.file_listbox.delete(0, tk.END)
            for f in files:
                self.file_listbox.insert(tk.END, f)
        except Exception as e:
            self.log_error(f"加载文件失败: {str(e)}")

    def start_translation(self):
        selected = self.file_listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要翻译的文件")
            return
        files = [self.file_listbox.get(i) for i in selected]
        threading.Thread(target=self.translate_files, args=(files,), daemon=True).start()

    def translate_files(self, files):
        category = self.category_var.get()
        source_dir = os.path.join(self.project_path, "sources", category)
        target_dir = os.path.join(self.project_path, "translated", category)
        os.makedirs(target_dir, exist_ok=True)

        for file in files:
            try:
                self.log(f"开始翻译: {file}")
                with open(os.path.join(source_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()

                translated = self.call_translation_api(content)
                if translated:
                    translated = self.process_translation(translated)
                    target_path = os.path.join(target_dir, file)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(translated)
                    self.log(f"翻译完成: {file}")
            except Exception as e:
                self.log_error(f"翻译失败 ({file}): {str(e)}")
                messagebox.showerror("错误", f"翻译失败: {file}\n错误信息: {str(e)}")

    def call_translation_api(self, content):
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.config['model'],
            "messages": [
                {"role": "system", "content": self.config['prompt']},
                {"role": "user", "content": content}
            ]
        }
        try:
            response = requests.post(
                f"{self.config['api_base']}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            try:
                result = response.json()
                self.log(f"模型响应: {json.dumps(result, ensure_ascii=False)}")
                return result['choices'][0]['message']['content']
            except json.JSONDecodeError as e:
                self.log_error(f"JSON解析失败，响应内容: {response.text}")
                raise ValueError("无效的API响应格式")

        except requests.exceptions.RequestException as e:
            self.log_error(f"API请求失败: {str(e)}")
            raise

    def process_translation(self, text):
        # 处理元信息替换
        text = text.replace("{{translator}}", "excniesnied")
        text = text.replace("applied: false", "applied: true")
        text = text.replace("translated: false", "translated: true")
        return text

    def delete_files(self):
        selected = self.file_listbox.curselection()
        if not selected:
            return
        if not messagebox.askyesno("确认", "确定要删除选中的源文件吗？"):
            return
        category = self.category_var.get()
        source_dir = os.path.join(self.project_path, "sources", category)
        for i in reversed(selected):
            file = self.file_listbox.get(i)
            try:
                os.remove(os.path.join(source_dir, file))
                self.file_listbox.delete(i)
                self.log(f"已删除文件: {file}")
            except Exception as e:
                self.log_error(f"删除失败 ({file}): {str(e)}")

    def show_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("API设置")

        ttk.Label(settings_win, text="API基础地址:").grid(row=0, column=0, padx=5, pady=2)
        api_base_entry = ttk.Entry(settings_win, width=40)
        api_base_entry.insert(0, self.config['api_base'])
        api_base_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(settings_win, text="API密钥:").grid(row=1, column=0)
        api_key_entry = ttk.Entry(settings_win, width=40)
        api_key_entry.insert(0, self.config['api_key'])
        api_key_entry.grid(row=1, column=1)

        ttk.Label(settings_win, text="模型名称:").grid(row=2, column=0)
        model_entry = ttk.Entry(settings_win, width=40)
        model_entry.insert(0, self.config['model'])
        model_entry.grid(row=2, column=1)

        ttk.Label(settings_win, text="提示词:").grid(row=3, column=0)
        prompt_entry = tk.Text(settings_win, width=40, height=10)
        prompt_entry.insert(tk.END, self.config['prompt'])
        prompt_entry.grid(row=3, column=1)

        def save_settings():
            self.config.update({
                'api_base': api_base_entry.get(),
                'api_key': api_key_entry.get(),
                'model': model_entry.get(),
                'prompt': prompt_entry.get("1.0", tk.END).strip()
            })
            settings_win.destroy()
            self.log("设置已保存")

        ttk.Button(settings_win, text="保存", command=save_settings).grid(row=4, column=1, pady=5)

    def log(self, message):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.log_text.insert(tk.END, f"{timestamp} {message}\n")
        self.log_text.see(tk.END)
        self.logger.info(message)

    def log_error(self, message):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.log_text.insert(tk.END, f"{timestamp} [错误] {message}\n", 'error')
        self.log_text.see(tk.END)
        self.logger.error(message)

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslationApp(root)
    root.geometry("800x600")
    root.mainloop()