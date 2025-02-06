import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import requests
from datetime import datetime

class TranslateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FOSSCOPE 翻译工具")
        self.geometry("1000x800")

        # 初始化配置
        self.settings = {
            "api_key": "",
            "model": "deepseek-reasoner",
            "prompt": """你是一个中英文翻译专家，将用户输入的英文科技新闻资讯或者英文技术文章翻译成中文，保持专业术语准确，不要翻译文件中的标记元素，保留原始文章中的Markdown标记格式，但需要将文件元信息中的所有{{translator}}替换为excniesnied，并将元信息中的applied字段和translated字段都修改为true（如果有的话），除此之外不要翻译元信息。并确保符合中文语言习惯，你可以调整语气和风格，并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。注意链接之间增加空格、中英文之间需要增加空格、中文与数字之间需要增加空格、数字与单位之间需要增加空格、全角标点与其他字符之间不加空格、，将中文引号“”转换为「」。
            """
        }

        self.project_path = tk.StringVar()
        self.selected_category = tk.StringVar()

        self.create_widgets()
        self.log("应用程序初始化完成")

    def create_widgets(self):
        # 项目路径部分
        path_frame = ttk.Frame(self)
        path_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Label(path_frame, text="项目路径：").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.project_path, width=60)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(path_frame, text="浏览", command=self.browse_project_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="加载", command=self.verify_project_structure).pack(side=tk.LEFT)

        # 分类选择
        category_frame = ttk.Frame(self)
        category_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Label(category_frame, text="分类：").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.selected_category,
                                           values=['news', 'talk', 'tech'], state="readonly", width=15)
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.load_file_list)

        # 文件列表
        list_frame = ttk.Frame(self)
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=10)

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 操作按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Button(button_frame, text="开始翻译", command=self.start_translation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.delete_selected_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="系统设置", command=self.open_settings_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_file_list).pack(side=tk.RIGHT, padx=5)

        # 日志区域
        log_frame = ttk.Frame(self)
        log_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=10)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def browse_project_path(self):
        path = filedialog.askdirectory()
        if path:
            self.project_path.set(path)
            self.log(f"已选择项目路径: {path}")

    def verify_project_structure(self):
        path = self.project_path.get()
        if not path:
            self.show_error("请先选择项目路径")
            return

        required_dirs = ['.github', 'License', 'published', 'sources', 'translated']
        missing = [d for d in required_dirs if not os.path.exists(os.path.join(path, d))]

        if missing:
            self.show_error(f"项目结构不完整，缺失目录: {', '.join(missing)}")
        else:
            self.log("项目结构验证通过")
            self.refresh_file_list()

    def load_file_list(self, event=None):
        category = self.selected_category.get()
        if not category:
            return

        source_dir = os.path.join(self.project_path.get(), 'sources', category)
        if not os.path.exists(source_dir):
            self.show_error(f"目录不存在: {source_dir}")
            return

        try:
            files = [f for f in os.listdir(source_dir)
                     if os.path.isfile(os.path.join(source_dir, f)) and f != 'README.md']

            self.file_listbox.delete(0, tk.END)
            for f in sorted(files):
                self.file_listbox.insert(tk.END, f)

            self.log(f"已加载 {len(files)} 个文件到 {category} 分类")
        except Exception as e:
            self.show_error(f"读取文件列表失败: {str(e)}")

    def start_translation(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            self.show_warning("请先选择要翻译的文件")
            return

        if not self.settings['api_key']:
            self.show_error("请先配置API密钥")
            return

        category = self.selected_category.get()
        source_dir = os.path.join(self.project_path.get(), 'sources', category)
        target_dir = os.path.join(self.project_path.get(), 'translated', category)

        os.makedirs(target_dir, exist_ok=True)

        for filename in selected_files:
            try:
                with open(os.path.join(source_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()

                translated = self.translate_content(content)

                with open(os.path.join(target_dir, filename), 'w', encoding='utf-8') as f:
                    f.write(translated)

                self.log(f"成功翻译并保存: {filename}")
            except Exception as e:
                self.show_error(f"翻译失败 ({filename}): {str(e)}")

    def translate_content(self, content):
        headers = {
            "Authorization": f"Bearer {self.settings['api_key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.settings['model'],
            "messages": [
                {"role": "system", "content": self.settings['prompt']},
                {"role": "user", "content": content}
            ]
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    def delete_selected_files(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            self.show_warning("请先选择要删除的文件")
            return

        if messagebox.askyesno("确认删除", f"确定要删除 {len(selected_files)} 个文件吗？"):
            category = self.selected_category.get()
            source_dir = os.path.join(self.project_path.get(), 'sources', category)

            for filename in selected_files:
                try:
                    os.remove(os.path.join(source_dir, filename))
                    self.log(f"已删除文件: {filename}")
                except Exception as e:
                    self.show_error(f"删除失败 ({filename}): {str(e)}")

            self.refresh_file_list()

    def open_settings_dialog(self):
        settings_win = tk.Toplevel(self)
        settings_win.title("系统设置")
        settings_win.geometry("600x400")

        ttk.Label(settings_win, text="API配置").pack(pady=10)

        # API密钥
        ttk.Label(settings_win, text="API密钥:").place(x=20, y=50)
        api_entry = ttk.Entry(settings_win, width=50)
        api_entry.place(x=120, y=50)
        api_entry.insert(0, self.settings['api_key'])

        # 模型选择
        ttk.Label(settings_win, text="模型名称:").place(x=20, y=90)
        model_entry = ttk.Entry(settings_win, width=50)
        model_entry.place(x=120, y=90)
        model_entry.insert(0, self.settings['model'])

        # 提示词
        ttk.Label(settings_win, text="提示词:").place(x=20, y=130)
        prompt_text = tk.Text(settings_win, width=65, height=10)
        prompt_text.place(x=20, y=160)
        prompt_text.insert(tk.END, self.settings['prompt'])

        def save_settings():
            self.settings['api_key'] = api_entry.get()
            self.settings['model'] = model_entry.get()
            self.settings['prompt'] = prompt_text.get("1.0", tk.END).strip()
            settings_win.destroy()
            self.log("系统设置已更新")

        ttk.Button(settings_win, text="保存配置", command=save_settings).pack(side=tk.BOTTOM, pady=10)

    def refresh_file_list(self):
        self.load_file_list()
        self.log("文件列表已刷新")

    def get_selected_files(self):
        return [self.file_listbox.get(i) for i in self.file_listbox.curselection()]

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, log_message)
        self.log_area.configure(state=tk.DISABLED)
        self.log_area.see(tk.END)
        print(log_message.strip())

    def show_error(self, message):
        messagebox.showerror("错误", message)
        self.log(f"[错误] {message}")

    def show_warning(self, message):
        messagebox.showwarning("警告", message)
        self.log(f"[警告] {message}")

if __name__ == "__main__":
    app = TranslateApp()
    app.mainloop()