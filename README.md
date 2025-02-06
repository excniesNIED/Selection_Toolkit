# 开源观察选题工具箱（自用）

## Convert

这是一个用于将 ITS FOSS 网站上的文章转换为 Markdown 格式的 Python 脚本。该脚本可以读取包含多个 URL 的 `urls.txt` 文件，并根据指定的规则将文章内容转换为 Markdown 文件。

### 功能

- **自动生成 Markdown 文件**：根据文章的标题和发布日期生成文件名。
- **提取元数据**：包括标题、发布日期、作者、分类等信息。
- **内容转换**：将 HTML 内容转换为 Markdown 格式，支持图片、按钮、备注块、代码块、视频等元素的转换。
- **自定义模板**：使用 `template.md` 作为 Markdown 文件的模板，支持动态替换变量。

### 使用方法

1. **安装依赖**：
   确保已安装 Python 3.x，并安装所需的依赖库：
   ```bash
   pip install requests beautifulsoup4 html2text slugify
   ```

2. **准备 URL 文件**：
   在项目根目录下创建一个名为 `urls.txt` 的文件，每行包含一个 ITS FOSS 文章的 URL。例如：
   ```
   https://itsfoss.com/hyprland-0.47.0-releases-with-hdr-support-and-squircles/
   https://news.itsfoss.com/linux-boot-time/
   ```

3. **运行脚本**：
   运行 `convert1.7.py` 脚本，并输入你的 GitHub ID：
   ```bash
   python convert1.7.py
   ```

4. **生成 Markdown 文件**：
   脚本将根据 `urls.txt` 中的 URL 生成对应的 Markdown 文件，并保存在当前目录下。

### 文件结构

- `convert1.7.py`：主脚本文件，负责处理 URL 并生成 Markdown 文件。
- `urls.txt`：包含要处理的 ITS FOSS 文章 URL。
- `template.md`：Markdown 文件的模板，包含动态替换的变量。
- `README.md`：项目说明文件。

### 转换规则

1. **文件名**：根据文章的标题和发布日期生成文件名，例如 `20250128-hyprland-0.47.0-releases-with-hdr-support-and-squircles.md`。
2. **标题**：提取 `<h1 class="post-hero__title">` 中的内容作为 `{{title}}`。
3. **分类**：根据 URL 判断文章分类，`https://news.itsfoss.com/*` 为 `新闻`，`https://itsfoss.com/*` 为 `技术`。
4. **作者信息**：提取作者名称和链接，并根据 URL 判断链接前缀。
5. **摘要**：提取 `<meta property="og:description">` 中的内容作为文章摘要。
6. **正文转换**：
   - 移除第一个 `<a>` 标签（广告）。
   - 转换图片为 `{% image [src] [description] %}` 格式。
   - 转换按钮为 `{% button [text] [url] %}` 格式。
   - 转换备注块为 `{% note [title] [content] color:[color] %}` 格式。
   - 转换代码块为 Markdown 的 ``` 代码块。
   - 转换 YouTube 视频为 `{% video youtube:[video_id] %}` 格式。
   - 转换普通视频为 `{% video [video_url] %}` 格式。

## Translate

### 简介

FOSSCOPE 翻译工具是一个基于 Python 和 Tkinter 的桌面应用程序，旨在帮助用户管理和翻译 FOSSCOPE Translate Project 中的文章。该工具提供了文件加载、翻译、删除和设置等功能，支持调用大模型 API 进行自动化翻译。

### 功能

- **项目路径设置**：用户可以设置 FOSSCOPE Translate Project 的路径，并加载项目。
- **分类选择**：支持选择 `news`、`talk` 和 `tech` 分类。
- **文件加载**：加载所选分类下的 Markdown 文件。
- **多选翻译**：用户可以选择多个文件进行翻译，翻译后的文件将保存在 `translated` 目录下。
- **文件删除**：支持删除选中的源文件。
- **API 设置**：用户可以设置 API 基础地址、API 密钥、模型名称和提示词。
- **日志记录**：工具会记录所有操作和错误信息，并在界面上显示。

### 安装

1. 确保已安装 Python 3.x。
2. 克隆本仓库或下载源代码。
3. 安装所需的依赖项：

   ```bash
   pip install requests
   ```

### 使用

1. 运行 `translate.py` 启动应用程序。
2. 在界面中设置 FOSSCOPE Translate Project 的路径并加载项目。
3. 选择分类并加载文件。
4. 选择要翻译的文件，点击“翻译选中”按钮开始翻译。
5. 翻译完成后，翻译后的文件将保存在 `translated` 目录下。
6. 如需删除文件，选择文件后点击“删除选中”按钮。
7. 点击“设置”按钮可以配置 API 相关设置。

### API 设置

在设置窗口中，用户可以配置以下参数：

- **API 基础地址**：API 的基础 URL。
- **API 密钥**：用于认证的 API 密钥。
- **模型名称**：使用的模型名称。
- **提示词**：翻译时使用的提示词。

### 提示词示例

```plaintext
你是一个中英文翻译专家，将用户输入的英文科技新闻资讯或者英文技术文章翻译成中文，保持专业术语准确，不要翻译文件中的标记元素，保留原始文章中的Markdown标记格式，但需要将文件元信息中的所有{{translator}}替换为excniesnied，并将元信息中的applied字段和translated字段都修改为true（如果有的话），除此之外不要翻译元信息。并确保符合中文语言习惯，你可以调整语气和风格，并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。注意链接之间增加空格、中英文之间需要增加空格、中文与数字之间需要增加空格、数字与单位之间需要增加空格、全角标点与其他字符之间不加空格、，将中文引号“”转换为「」。
```

### 错误处理

- 如果翻译过程中出现错误，工具会记录错误信息并在界面上显示。
- 如果 API 请求失败或响应格式无效，工具会记录详细的错误信息。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进此项目。

## 许可证

本项目暂时没有许可证。