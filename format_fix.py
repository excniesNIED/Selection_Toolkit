import os
import re

def process_markdown_file(filepath):
    """
    处理单个Markdown文件，删除指定区域的行首空格，并规范化空行。

    参数:
    filepath (str): Markdown文件的路径。

    返回:
    str: 处理后的Markdown文件内容。
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_metadata = False
    in_code_block = False # 新增：标记是否在代码块内
    metadata_end_line = -1
    processed_lines = []
    consecutive_blank_lines = 0

    # 步骤1：定位元数据区域和代码块区域，并处理非元数据区域的行首空格
    for i, line in enumerate(lines):

        stripped_line = line.lstrip() # 移除行首所有空格，用于判断类型 (提前到循环最前面)

        if stripped_line.startswith('---'):
            if not in_metadata:
                in_metadata = True
            else:
                in_metadata = False
                metadata_end_line = i # 记录元数据结束行
            processed_lines.append(stripped_line + '\n') # 元数据行, 使用stripped_line, 并添加换行符
            continue

        if in_metadata:
            processed_lines.append(line) # 元数据区域内容保持不变
            continue


        if stripped_line.startswith('```'): # 代码块开始/结束行 (`)
            if not in_code_block:
                in_code_block = True
            else:
                in_code_block = False
            processed_lines.append(stripped_line + '\n') # 代码块标识行, 使用stripped_line, 并添加换行符
            continue

        if in_code_block:
            processed_lines.append(stripped_line + '\n') # 代码块内的行，移除所有行首空格和制表符, 并添加换行符
            continue


        if re.match(r'^    ', line) or re.match(r'^\t', line): # 缩进代码块 (4个空格或制表符开头)，在代码块之外的缩进代码需要保留
            processed_lines.append(line) # 缩进代码行保留原始格式
        elif re.match(r'^[-*+] ', stripped_line): # 无序列表
            processed_lines.append(stripped_line + '\n') # 移除列表项前的空格, 并添加换行符
        elif re.match(r'^\d+\. ', stripped_line) or re.match(r'^\d+\) ', stripped_line): # 有序列表
            processed_lines.append(stripped_line + '\n') # 移除列表项前的空格, 并添加换行符
        elif stripped_line == '\n': # 空行 （只包含换行符，或者去除空格后是空行）
            processed_lines.append(stripped_line) # 空行保留，后续处理空行数量
        else:
            processed_lines.append(stripped_line + '\n') # 非特殊格式行，移除行首空格, 并添加换行符


    # 步骤2：清除大于两个的空行 (这部分代码保持不变)
    final_processed_lines = []
    consecutive_blank_lines = 0
    for line in processed_lines:
        if line.strip() == '': # 再次判断是否是空行 (处理步骤1后可能产生的空行)
            consecutive_blank_lines += 1
            if consecutive_blank_lines <= 2:
                final_processed_lines.append('\n') # 保留最多两个空行
        else:
            final_processed_lines.append(line)
            consecutive_blank_lines = 0 # 重置计数器

    return "".join(final_processed_lines)


def process_directory(directory_path):
    """
    处理指定目录下的所有Markdown文件。

    参数:
    directory_path (str): 目录路径。
    """
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.md', '.markdown')): # 检查文件是否是Markdown文件
            filepath = os.path.join(directory_path, filename)
            print(f"正在处理文件: {filepath}")
            processed_content = process_markdown_file(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            print(f"文件处理完成: {filepath}")


if __name__ == "__main__":
    path = input("请输入包含Markdown文件的目录路径: ")
    if os.path.isdir(path):
        process_directory(path)
        print("所有Markdown文件处理完成。")
    else:
        print("输入的路径不是一个有效的目录。")