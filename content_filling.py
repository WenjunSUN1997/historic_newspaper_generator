import random
import os
from create_layout import layout_design
import textwrap
from PIL import ImageDraw, Image, ImageFont

def add_text_in_paragraph(x_0, y_0, width, height, font_name, font_size, text, drawer):
    font = ImageFont.load_default()
    # font = ImageFont.truetype(font_name, font_size)
    _, _, letter_width, letter_height = font.getbbox('a')
    line_list = []
    while letter_height * (len(line_list)+1) <= height:
        line_text = ''
        width_this_line = 0
        for letter_index, letter in enumerate(text):
            width_this_line += letter_width
            if width_this_line < width:
                line_text += letter
            else:
                line_text = line_text[:-1] + '-'
                line_list.append(line_text)
                text = text[letter_index: ]
                break

    for line_index, line_text in enumerate(line_list):
        drawer.text((x_0, y_0+line_index*letter_height),
                    line_text,
                    (255, 0, 0),
                    font=font)
    return text

def split_list(input_list):
    # 生成1到4之间的随机数，确定分割成几份
    num_partitions = random.randint(1, min([4, len(input_list)]))

    # 确定每份的大小
    list_length = len(input_list)
    partition_sizes = []
    remaining_length = list_length
    for i in range(num_partitions - 1):
        partition = random.randint(1, remaining_length - (num_partitions - i - 1))
        partition_sizes.append(partition)
        remaining_length -= partition
    partition_sizes.append(remaining_length)

    # 使用切片操作分割列表
    result = []
    start = 0
    for size in partition_sizes:
        end = start + size
        result.append(input_list[start:end])
        start = end

    return result

def draw_multiple_line_text(image, text, font, text_color, text_start_height):
    '''
    From unutbu on [python PIL draw multiline text on image](https://stackoverflow.com/a/7698300/395857)
    '''
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=40)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text),
                  line, font=font, fill=text_color)
        y_text += line_height

def gengerate_textual_content(text_path):
    book_list = os.listdir(text_path)
    result = ''
    text_list = []
    for book in book_list:
        with open(text_path+book, 'r', encoding='utf-8') as file:
            book_content = file.readlines()
            for line in book_content:
                line = line.replace('\n', '')
                if len(line) > 0:
                    text_list.append(line)

        text_list.append(book_content)

    start = random.randint(0, len(text_list)-5000)
    selected_text = text_list[start: start+5000]
    for text in selected_text:
        if isinstance(text, list):
            continue

        result += text + ' '

    return result

def fill_textual_content(text_path = r'data/french/', output_layout=None):
    image_to_draw = Image.new('RGB',
                              (output_layout['image'].width, output_layout['image'].height),
                              (255, 255, 255))
    drawer = ImageDraw.Draw(image_to_draw, 'RGB')
    for x in output_layout['paragraph']:
        drawer.rectangle(x['bbox'], outline='black', width=5)

    for x in output_layout['independent_region']:
        drawer.rectangle(x['bbox'], outline='black', width=5)

    image_to_draw.save('temp.png')
    article_region_list = []
    for paragraph_group in output_layout['paragraph_grouped']:
        output_split = split_list(paragraph_group)
        for output in output_split:
            article_region_list.append(output)

    for inedex, article_region in enumerate(article_region_list):
        # print(inedex)
        text = gengerate_textual_content(text_path)
        for paragrapg_region in article_region:
            x_0, y_0, x_1, y_1 = paragrapg_region['bbox']
            height = y_1 - y_0
            width = x_1 - x_0
            if height <= 10:
                continue
            text = add_text_in_paragraph(x_0+10, y_0+10, width-20, height-20, "DejaVuSerif.ttf", 7, text, drawer)

    image_to_draw.save('paragraph.png')


if __name__ == "__main__":
    text_path = r'data/french/'
    output_layout = layout_design()
    fill_textual_content(text_path=r'data/french/', output_layout=output_layout)
