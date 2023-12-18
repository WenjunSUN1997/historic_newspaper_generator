import random
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
import numpy as np

def create_sep(start, end, num, threshold):
    while True:
        if num == 0:
            return []

        random_numbers = sorted([random.randint(start, end) for _ in range(num)])
        if num > 1:
            if min([random_numbers[x+1]-random_numbers[x] for x in range(len(random_numbers)-1)]) > threshold:
                break

        else:
            if min([abs(start-random_numbers[0]), abs(end-random_numbers[0])]) > threshold:
                break

    return random_numbers

def split_col(col):
    col_bbox = col['bbox']
    col_index = col['index']
    col_heigth = col_bbox[3] - col_bbox[1]
    paragraph_list = []
    if col_heigth <= 500:
        col_sep = []
    else:
        col_sep = create_sep(col_bbox[1], col_bbox[3],
                             random.randint(0, 5), threshold=80)

    if len(col_sep) == 0:
        paragraph_list.append({'bbox': col_bbox,
                               'index': col_index + '_' + '0'})
    else:
        for index, value in enumerate(col_sep):
            if index == 0:
                paragraph_list.append({'bbox': [col_bbox[0], col_bbox[1], col_bbox[2], value],
                                       'index': col_index + '_' + str(index)})
            else:
                paragraph_list.append({'bbox': [col_bbox[0], col_sep[index-1], col_bbox[2], value],
                                       'index': col_index + '_' + str(index)})

        paragraph_list.append({'bbox': [col_bbox[0], col_sep[-1], col_bbox[2], col_bbox[3]],
                               'index': col_index + '_' + str(len(col_sep))})

    return paragraph_list

# def judge_overlap(bbox_0, bbox_1):
#     x1_min, y1_min, x1_max, y1_max = bbox_0
#     x2_min, y2_min, x2_max, y2_max = bbox_1
#     # 判断是否有重叠
#     if (x1_min < x2_max and x1_max > x2_min and
#             y1_min < y2_max and y1_max > y2_min):
#         return True
#     else:
#         return False

def judge_overlap(bbox_0, bbox_1):
    rect1 = np.array(bbox_0)
    rect2 = np.array(bbox_1)
    p1 = Polygon([(rect1[0], rect1[1]), (rect1[2], rect1[1]),(rect1[2],rect1[3]),(rect1[0],rect1[3])])
    p2 = Polygon([(rect2[0], rect2[1]), (rect2[2], rect2[1]), (rect2[2], rect2[3]), (rect2[0], rect2[3])])
    return (p1.intersects(p2))

def generate_independent_region(sub_page, col_list):
    num_col = len(col_list)
    independent_region_list = []
    sub_page_index = sub_page['index']
    independent_region_num = random.randint(0, 6)
    for independent_region_index in range(independent_region_num):
        store_flag = True
        start_col = random.randint(0, num_col-2)
        start_x = col_list[start_col]['bbox'][0]+1
        end_col = random.randint(start_col+1, num_col-1)
        end_x = col_list[end_col]['bbox'][2]-1
        start_y = random.randint(col_list[0]['bbox'][1], col_list[0]['bbox'][3])+1
        end_y = random.randint(start_y, col_list[0]['bbox'][3])-1
        for region_unit in independent_region_list:
            if judge_overlap(region_unit['bbox'], [start_x, start_y, end_x, end_y]):
                store_flag = False
                break

        if store_flag:
            independent_region_list.append({'bbox': [start_x, start_y, end_x, end_y],
                                            'index': sub_page_index + '_' + 'independ_'
                                                     + str(independent_region_index),
                                            'start_col': start_col,
                                            'end_col': end_col})

    return independent_region_list

def split_subpage(sub_page):
    sub_page_bbox = sub_page['bbox']
    sub_page_index = sub_page['index']
    col_list = []
    col_list_to_split = []
    paragraph_list = []
    col_num = random.randint(2, 6)
    col_width = int((sub_page_bbox[2] - sub_page_bbox[0]) / col_num)
    for index in range(col_num):
        col_list.append({'bbox': [sub_page_bbox[0] + index*col_width, sub_page_bbox[1],
                                  sub_page_bbox[0] + (index+1)*col_width, sub_page_bbox[3]],
                         'index': sub_page_index + '_' + str(index)})

    print('generate independt region')
    independent_region_list = generate_independent_region(sub_page, col_list)
    for col_index, col in enumerate(col_list):
        cx_0, cy_0, cx_1, cy_1 = col['bbox']
        store_flag = True
        independent_region_overlap = []
        for independent_region in independent_region_list:
            if judge_overlap(col['bbox'], independent_region['bbox']):
                ix_0, iy_0, ix_1, iy_1 = independent_region['bbox']
                if cy_0 >= iy_0 and cy_1 <= iy_1:
                    store_flag = False
                    break

                independent_region_overlap.append(independent_region)

        if len(independent_region_overlap) == 0:
            if store_flag:
             col_list_to_split.append(col)

        else:
            independent_region_overlap = sorted(independent_region_overlap, key=lambda x: x['bbox'][1])
            for ir_index, ir in enumerate(independent_region_overlap):
                irx_0, iry_0, irx_1, iry_1 = ir['bbox']
                if ir_index == 0:
                    col_list_to_split.append({'bbox': [cx_0, cy_0, cx_1, iry_0],
                                              'index': col['index'] + '_break_' + str(ir_index)})
                else:
                    col_list_to_split.append({'bbox': [cx_0, independent_region_overlap[ir_index-1]['bbox'][3],
                                                       cx_1, iry_0],
                                              'index': col['index'] + '_break_' + str(ir_index)})

            col_list_to_split.append({'bbox': [cx_0, independent_region_overlap[-1]['bbox'][3],
                                               cx_1, cy_1],
                                      'index': col['index'] + '_break_' + str(len(independent_region_overlap))})

    print('split col')
    for col in col_list_to_split:
        paragraph_list += split_col(col)

    return {'paragraph': paragraph_list,
            'independent_region': independent_region_list}

def layout_design(size=[2480, 3508]):
    image_to_draw = Image.new('RGB', (size[0], size[1]), (255, 255, 255))
    drawer = ImageDraw.Draw(image_to_draw, 'RGB')
    paragraph = []
    independent_region = []
    whole_page_size = size
    whole_page_bbox = [0, 0, size[0], size[1]]
    whole_page_sep_hori = create_sep(0, size[1], random.randint(0, 4), threshold=300)
    sub_page_of_whole = []
    # 开始全局水平切分
    print('split wohle page')
    if len(whole_page_sep_hori) == 0:
        sub_page_of_whole.append({'bbox': [0, 0, size[0], size[1]],
                                  'index': '0'})
    else:
        for index, location_hori in enumerate(whole_page_sep_hori):
            if index == 0:
                sub_page_of_whole.append({'bbox': [0, 0, size[0], location_hori],
                                          'index': str(index)})
            else:
                sub_page_of_whole.append({'bbox': [0, whole_page_sep_hori[index-1],
                                                   size[0], location_hori],
                                          'index': str(index)})

        sub_page_of_whole.append({'bbox': [0, whole_page_sep_hori[-1], size[0], size[1]],
                                  'index': str(len(whole_page_sep_hori))})


    # 开始垂直切分
    print('split sub page')
    for sub_page in sub_page_of_whole:
        result = split_subpage(sub_page)
        paragraph += result['paragraph']
        independent_region += result['independent_region']

    area = 0
    for x in paragraph:
        area += (x['bbox'][2]-x['bbox'][0]) *(x['bbox'][3]-x['bbox'][1])
        drawer.rectangle(x['bbox'], outline='white', width=10, fill='red')

    for x in independent_region:
        area += (x['bbox'][2] - x['bbox'][0]) * (x['bbox'][3] - x['bbox'][1])
        drawer.rectangle(x['bbox'], outline='white', width=10, fill='green')

    for x in sub_page_of_whole:
        drawer.rectangle(x['bbox'], outline='blue', width=30)

    image_to_draw.save('example.png')
    print(area)
    print(size[0]*size[1])
    # all_area = paragraph + independent_region
    # for index in range(len(all_area)-1):
    #     for index_1 in range(index+1, len(all_area)):
    #         if judge_overlap(all_area[index_1]['bbox'], all_area[index]['bbox']):
    #             print(all_area[index_1]['bbox'])
    #             print(all_area[index]['bbox'])
    #             print('---------------------------')
    return

if __name__ == "__main__":
    layout_design()


 # for paragraph in paragraph_list:
 #        store_flag = True
 #        px_0, py_0, px_1, py_1 = paragraph['bbox']
 #        for independent_region in independent_region_list:
 #            if judge_overlap(paragraph['bbox'], independent_region['bbox']):
 #                ix_0, iy_0, ix_1, iy_1 = independent_region['bbox']
 #                if py_0>=iy_0 and py_1<=iy_1:
 #                    store_flag = False
 #
 #                if py_0<iy_0 and py_1>iy_0 and py_1<iy_1:
 #                    final_paragraph_list.append({'bbox': [px_0, py_0, px_1, iy_0],
 #                                                 'index': paragraph['index'] + '_0'})
 #                    store_flag = False
 #
 #                if py_0>iy_0 and py_0<iy_1 and py_1>iy_1:
 #                    final_paragraph_list.append({'bbox': [px_0, iy_1, px_1, py_1],
 #                                                 'index': paragraph['index'] + '_0'})
 #                    store_flag = False
 #
 #                if py_0<iy_0 and py_1>iy_1:
 #                    final_paragraph_list.append({'bbox': [px_0, py_0, px_1, iy_0],
 #                                                 'index': paragraph['index'] + '_0'})
 #                    final_paragraph_list.append({'bbox': [px_0, iy_1, px_1, py_1],
 #                                                 'index': paragraph['index'] + '_1'})
 #                    store_flag = False
 #
 #        if store_flag:
 #            final_paragraph_list.append(paragraph)

