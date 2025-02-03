import re
import os
import requests
import traceback
from bs4 import BeautifulSoup
import html2text
from datetime import datetime
from urllib.parse import urlparse
from slugify import slugify

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def sanitize_filename(title):
    return slugify(title, lowercase=True, max_length=80, word_boundary=True)

def process_image(figure):
    imgs = figure.find_all('img')
    if not imgs:
        return ""

    figcaption = figure.find('figcaption')
    description = figcaption.get_text(strip=True) if figcaption else ''

    image_tags = []
    for idx, img in enumerate(imgs):
        src = img.get('src', '')
        img_description = description if idx == len(imgs)-1 else ''
        image_tags.append(f"{{% image {src} '{img_description}' %}}")

    return '\n'.join(image_tags)

def process_button(div):
    a_tag = div.find('a')
    if not a_tag:
        return ""

    text = a_tag.get_text(strip=True)
    url = a_tag['href'].split('?')[0]
    return f"{{% button '{text}' '{url}' %}}"

def process_callout(div):
    color_class = [c for c in div['class'] if c.startswith('kg-callout-card-')]
    color = color_class[0].split('-')[-1] if color_class else ''
    emoji_div = div.find(class_='kg-callout-emoji')
    emoji = emoji_div.get_text(strip=True) if emoji_div else ''
    text_div = div.find(class_='kg-callout-text')
    text = html2text.html2text(str(text_div)).strip() if text_div else ''
    return f"{{% note {emoji} '{text}' color:{color} %}}"

def process_article(article):
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = True
    h.ul_item_mark = '*'
    h.emphasis_mark = '_'

    output = []
    first_a = True

    for element in article.children:
        if element.name == 'a' and first_a:
            first_a = False
            continue

        element_str = str(element)
        soup = BeautifulSoup(element_str, 'html.parser')

        # 处理图片
        for figure in soup.find_all('figure'):
            img_md = process_image(figure)
            figure.replace_with(img_md)

        # 处理代码块
        for code_tag in soup.find_all('code'):
            code_content = code_tag.get_text(strip=False).strip()
            code_tag.replace_with(f'```\n{code_content}\n```')

        # 处理按钮
        for div in soup.find_all('div', class_='kg-button-card'):
            button_md = process_button(div)
            div.replace_with(button_md)

        # 处理备注块
        for div in soup.find_all('div', class_='kg-callout-card'):
            callout_md = process_callout(div)
            div.replace_with(callout_md)

        modified_html = str(soup)
        modified_html = re.sub(r'\?ref=(itsfoss\.com|news\.itsfoss\.com)', '', modified_html)

        # 处理剩余内容
        md_content = h.handle(modified_html).strip()
        if md_content:
            output.append(md_content)

    return '\n\n'.join(output)

def main():
    github_id = input("请输入GitHub ID: ")

    with open('urls.txt') as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        try:
            print(f"处理 {url}")
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 元数据提取
            og_title = soup.find('meta', property='og:title')['content']
            publish_time = soup.find('meta', property='article:modified_time')['content']
            date_str = datetime.fromisoformat(publish_time[:-1]).strftime('%Y%m%d')
            og_description = soup.find('meta', property='og:description')
            summary = og_description['content'].strip() if og_description else ''

            # 生成文件名
            safe_title = sanitize_filename(og_title)
            filename = f"{date_str}-{safe_title}.md"

            # 标题提取
            title = soup.find('h1', class_='post-hero__title').get_text(strip=True)

            # 作者信息
            author_span = soup.find('span', class_=lambda c: c and c.startswith('post-info__author'))
            author_link_tag = author_span.find('a') if author_span else None
            author = "Unknown"
            author_link = "#"

            if author_span and author_link_tag:
                href = author_link_tag.get('href', '')
                if 'post-info__author' in author_span['class']:
                    base_url = 'https://itsfoss.com'
                else:
                    base_url = 'https://news.itsfoss.com'
                author_link = f"{base_url}{href}"
                author = author_link_tag.get_text(strip=True)

            # 分类判断
            domain = urlparse(url).netloc
            category = '新闻' if 'news.' in domain else '技术'

            # 正文处理
            article = soup.find('article', class_='post')
            content = process_article(article)

            # 写入文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('---\n')
                f.write(f'title: {title}\n')
                f.write('date: {{release_date}}\n')
                f.write('abbrlink: \n')
                f.write('author:\n')
                f.write('  - fosscope-translation-team\n')
                f.write('  - {{translator}}\n')
                f.write('  - {{proofreader}}\n')
                f.write('banner: {{cover_image}}\n')
                f.write('cover: {{cover_image}}\n')
                f.write('categories:\n')
                f.write('  - 翻译\n')
                f.write(f'  - {category}\n')
                f.write('tags: \n')
                f.write('  - {{tags}}\n')
                f.write('authorInfo: |\n')
                f.write(f'  via: {url}\n\n')
                f.write(f'  作者：[{author}]({author_link})\n')
                f.write(f'  选题：[{github_id}](https://github.com/{github_id})\n')
                f.write('  译者：[{{translator}}](https://github.com/{{translator}})\n')
                f.write('  校对：[{{proofreader}}](https://github.com/{{proofreader}})\n\n')
                f.write('  本文由 [FOSScope翻译组](https://github.com/FOSScope/TranslateProject) 原创编译，[开源观察](https://fosscope.com/) 荣誉推出\n')
                f.write('applied: false # 是否已被申领翻译\n')
                f.write('translated: false # 是否已翻译完成\n')
                f.write('proofread: false # 是否已校对完成\n')
                f.write('published: false # 是否已发布\n')
                f.write('---\n\n')
                f.write(f'{summary}\n\n')
                f.write('<!-- more -->\n\n')
                f.write(f'{content}\n')

            print(f"已生成文件：{filename}")

        except Exception as e:
            print(f"处理 {url} 出错: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    main()