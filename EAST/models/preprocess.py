import numpy as np
from PIL import Image, ImageDraw
import os
import random
from tqdm import tqdm

import cfg
from label import shrink
import pandas as pd


def batch_reorder_vertexes(xy_list_array):
    reorder_xy_list_array = np.zeros_like(xy_list_array)
    for xy_list, i in zip(xy_list_array, range(len(xy_list_array))):
        reorder_xy_list_array[i] = reorder_vertexes(xy_list)
    return reorder_xy_list_array


def reorder_vertexes(xy_list):
    reorder_xy_list = np.zeros_like(xy_list)
    # determine the first point with the smallest x,
    # if two has same x, choose that with smallest y,
    ordered = np.argsort(xy_list, axis=0)
    xmin1_index = ordered[0, 0]
    xmin2_index = ordered[1, 0]
    if xy_list[xmin1_index, 0] == xy_list[xmin2_index, 0]:
        if xy_list[xmin1_index, 1] <= xy_list[xmin2_index, 1]:
            reorder_xy_list[0] = xy_list[xmin1_index]
            first_v = xmin1_index
        else:
            reorder_xy_list[0] = xy_list[xmin2_index]
            first_v = xmin2_index
    else:
        reorder_xy_list[0] = xy_list[xmin1_index]
        first_v = xmin1_index
    # connect the first point to others, the third point on the other side of
    # the line with the middle slope
    others = list(range(4))
    others.remove(first_v)
    k = np.zeros((len(others),))
    for index, i in zip(others, range(len(others))):
        k[i] = (xy_list[index, 1] - xy_list[first_v, 1]) \
                    / (xy_list[index, 0] - xy_list[first_v, 0] + cfg.epsilon)
    k_mid = np.argsort(k)[1]
    third_v = others[k_mid]
    reorder_xy_list[2] = xy_list[third_v]
    # determine the second point which on the bigger side of the middle line
    others.remove(third_v)
    b_mid = xy_list[first_v, 1] - k[k_mid] * xy_list[first_v, 0]
    second_v, fourth_v = 0, 0
    for index, i in zip(others, range(len(others))):
        # delta = y - (k * x + b)
        delta_y = xy_list[index, 1] - (k[k_mid] * xy_list[index, 0] + b_mid)
        if delta_y > 0:
            second_v = index
        else:
            fourth_v = index
    reorder_xy_list[1] = xy_list[second_v]
    reorder_xy_list[3] = xy_list[fourth_v]
    # compare slope of 13 and 24, determine the final order
    k13 = k[k_mid]
    k24 = (xy_list[second_v, 1] - xy_list[fourth_v, 1]) / (
                xy_list[second_v, 0] - xy_list[fourth_v, 0] + cfg.epsilon)
    if k13 < k24:
        tmp_x, tmp_y = reorder_xy_list[3, 0], reorder_xy_list[3, 1]
        for i in range(2, -1, -1):
            reorder_xy_list[i + 1] = reorder_xy_list[i]
        reorder_xy_list[0, 0], reorder_xy_list[0, 1] = tmp_x, tmp_y
    return reorder_xy_list


def resize_image(im, max_img_size=cfg.max_train_img_size):
    im_width = np.minimum(im.width, max_img_size)
    if im_width == max_img_size < im.width:
        im_height = int((im_width / im.width) * im.height)
    else:
        im_height = im.height
    o_height = np.minimum(im_height, max_img_size)
    if o_height == max_img_size < im_height:
        o_width = int((o_height / im_height) * im_width)
    else:
        o_width = im_width
    d_wight = o_width - (o_width % 32)
    d_height = o_height - (o_height % 32)
    return d_wight, d_height


def preprocess():
    print(cfg.train_task_id)
    data_dir = cfg.data_dir
    #
    origin_image_dir = os.path.join(data_dir, cfg.origin_image_dir_name)
    origin_txt_dir = os.path.join(data_dir, cfg.origin_txt_dir_name)

    origin_val_image_dir = os.path.join(data_dir, cfg.origin_val_image_dir_name)
    origin_val_txt_dir = os.path.join(data_dir, cfg.origin_val_txt_dir_name)

    origin_test_image_dir = os.path.join(data_dir, cfg.origin_test_image_dir_name)
    origin_test_txt_dir=os.path.join(data_dir, cfg.origin_test_txt_dir_name)
    #
    train_image_dir = os.path.join(data_dir, cfg.train_image_dir_name)
    train_label_dir = os.path.join(data_dir, cfg.train_label_dir_name)

    val_image_dir = os.path.join(data_dir, cfg.val_image_dir_name)
    val_label_dir = os.path.join(data_dir, cfg.val_label_dir_name)

    test_image_dir = os.path.join(data_dir, cfg.test_image_dir_name)
    # test_label_dir = os.path.join(data_dir, cfg.test_label_dir_name)


    if not os.path.exists(train_image_dir):
        os.mkdir(train_image_dir)
    if not os.path.exists(train_label_dir):
        os.mkdir(train_label_dir)
    if not os.path.exists(val_image_dir):
        os.mkdir(val_image_dir)
    if not os.path.exists(val_label_dir):
        os.mkdir(val_label_dir)
    if not os.path.exists(test_image_dir):
        os.mkdir(test_image_dir)
    draw_gt_quad = cfg.draw_gt_quad

    if draw_gt_quad:
        show_gt_image_dir = os.path.join(data_dir, cfg.show_gt_image_dir_name)
        if not os.path.exists(show_gt_image_dir):
            os.mkdir(show_gt_image_dir)
        show_act_image_dir = os.path.join(cfg.data_dir, cfg.show_act_image_dir_name)
        if not os.path.exists(show_act_image_dir):
            os.mkdir(show_act_image_dir)
    else:
        show_gt_image_dir=''
        show_act_image_dir=''
    f(origin_image_dir, origin_txt_dir,
          cfg.gen_origin_img, train_image_dir, train_label_dir,
          draw_gt_quad, show_gt_image_dir
          , cfg.train_fname)
    f(origin_val_image_dir,origin_val_txt_dir,
        cfg.gen_origin_img, val_image_dir, val_label_dir,
        draw_gt_quad, show_act_image_dir
        , cfg.val_fname)
    #==================================Train===============================================#
    #
    # label = pd.read_csv(origin_txt_dir)
    #
    # o_img_list = os.listdir(origin_image_dir)
    # print('found %d origin images.' % len(o_img_list))
    # train_val_set = []
    # for o_img_fname in tqdm(o_img_list):
    #     with Image.open(os.path.join(origin_image_dir, o_img_fname)) as im:
    #         # d_wight, d_height = resize_image(im)
    #         d_wight, d_height = cfg.max_train_img_size, cfg.max_train_img_size
    #         scale_ratio_w = d_wight / im.width
    #         scale_ratio_h = d_height / im.height
    #         im = im.resize((d_wight, d_height), Image.NEAREST).convert('RGB')
    #         show_gt_im = im.copy()
    #         # draw on the img
    #         draw = ImageDraw.Draw(show_gt_im)
    #         # with open(os.path.join(origin_txt_dir,'gt_'+o_img_fname[:-4] + '.txt'), 'r',encoding='utf-8-sig') as f:
    #         #     anno_list = f.readlines()
    #
    #         txt = label[label['FileName'] == o_img_fname]
    #
    #         anno_list = txt.get_values()
    #         xy_list_array = np.zeros((len(anno_list), 4, 2))
    #         for anno, i in zip(anno_list, range(len(anno_list))):
    #             anno_colums = anno[1:9]
    #             anno_array = np.array(anno_colums)
    #             xy_list = np.reshape(anno_array[:8].astype(float), (4, 2))
    #             xy_list[:, 0] = xy_list[:, 0] * scale_ratio_w
    #             xy_list[:, 1] = xy_list[:, 1] * scale_ratio_h
    #             xy_list = reorder_vertexes(xy_list)
    #             xy_list_array[i] = xy_list
    #             _, shrink_xy_list, _ = shrink(xy_list, cfg.shrink_ratio)
    #             shrink_1, _, long_edge = shrink(xy_list, cfg.shrink_side_ratio)
    #             if draw_gt_quad:
    #                 draw.line([tuple(xy_list[0]), tuple(xy_list[1]),
    #                            tuple(xy_list[2]), tuple(xy_list[3]),
    #                            tuple(xy_list[0])
    #                            ],
    #                           width=2, fill='green')
    #                 draw.line([tuple(shrink_xy_list[0]),
    #                            tuple(shrink_xy_list[1]),
    #                            tuple(shrink_xy_list[2]),
    #                            tuple(shrink_xy_list[3]),
    #                            tuple(shrink_xy_list[0])
    #                            ],
    #                           width=2, fill='blue')
    #                 vs = [[[0, 0, 3, 3, 0], [1, 1, 2, 2, 1]],
    #                       [[0, 0, 1, 1, 0], [2, 2, 3, 3, 2]]]
    #                 for q_th in range(2):
    #                     draw.line([tuple(xy_list[vs[long_edge][q_th][0]]),
    #                                tuple(shrink_1[vs[long_edge][q_th][1]]),
    #                                tuple(shrink_1[vs[long_edge][q_th][2]]),
    #                                tuple(xy_list[vs[long_edge][q_th][3]]),
    #                                tuple(xy_list[vs[long_edge][q_th][4]])],
    #                               width=3, fill='yellow')
    #         if cfg.gen_origin_img:
    #             im.save(os.path.join(train_image_dir, 'train_' + o_img_fname))
    #         np.save(os.path.join(
    #             train_label_dir,
    #             'train_' + o_img_fname[:-4] + '.npy'),
    #             xy_list_array)
    #         if draw_gt_quad:
    #             show_gt_im.save(os.path.join(show_gt_image_dir, o_img_fname))
    #         train_val_set.append('{},{},{}\n'.format('train_'+o_img_fname,
    #                                                  d_wight,
    #                                                  d_height))
    #

    # #==================================Val================================================#
    #
    # label = pd.read_csv(origin_val_txt_dir)
    #
    # o_img_list = os.listdir(origin_val_image_dir)
    # print('found %d origin images.' % len(o_img_list))
    # for o_img_fname in tqdm(o_img_list):
    #     with Image.open(os.path.join(origin_val_image_dir, o_img_fname)) as im:
    #         # d_wight, d_height = resize_image(im)
    #         d_wight, d_height = cfg.max_train_img_size, cfg.max_train_img_size
    #         scale_ratio_w = d_wight / im.width
    #         scale_ratio_h = d_height / im.height
    #         im = im.resize((d_wight, d_height), Image.NEAREST).convert('RGB')
    #         show_gt_im = im.copy()
    #         # draw on the img
    #         draw = ImageDraw.Draw(show_gt_im)
    #         # with open(os.path.join(origin_txt_dir,'gt_'+o_img_fname[:-4] + '.txt'), 'r',encoding='utf-8-sig') as f:
    #         #     anno_list = f.readlines()
    #
    #         txt = label[label['FileName'] == o_img_fname]
    #
    #         anno_list = txt.get_values()
    #         xy_list_array = np.zeros((len(anno_list), 4, 2))
    #         for anno, i in zip(anno_list, range(len(anno_list))):
    #             anno_colums = anno[1:9]
    #             anno_array = np.array(anno_colums)
    #             xy_list = np.reshape(anno_array[:8].astype(float), (4, 2))
    #             xy_list[:, 0] = xy_list[:, 0] * scale_ratio_w
    #             xy_list[:, 1] = xy_list[:, 1] * scale_ratio_h
    #             xy_list = reorder_vertexes(xy_list)
    #             xy_list_array[i] = xy_list
    #             _, shrink_xy_list, _ = shrink(xy_list, cfg.shrink_ratio)
    #             shrink_1, _, long_edge = shrink(xy_list, cfg.shrink_side_ratio)
    #             if draw_gt_quad:
    #                 draw.line([tuple(xy_list[0]), tuple(xy_list[1]),
    #                            tuple(xy_list[2]), tuple(xy_list[3]),
    #                            tuple(xy_list[0])
    #                            ],
    #                           width=2, fill='green')
    #                 draw.line([tuple(shrink_xy_list[0]),
    #                            tuple(shrink_xy_list[1]),
    #                            tuple(shrink_xy_list[2]),
    #                            tuple(shrink_xy_list[3]),
    #                            tuple(shrink_xy_list[0])
    #                            ],
    #                           width=2, fill='blue')
    #                 vs = [[[0, 0, 3, 3, 0], [1, 1, 2, 2, 1]],
    #                       [[0, 0, 1, 1, 0], [2, 2, 3, 3, 2]]]
    #                 for q_th in range(2):
    #                     draw.line([tuple(xy_list[vs[long_edge][q_th][0]]),
    #                                tuple(shrink_1[vs[long_edge][q_th][1]]),
    #                                tuple(shrink_1[vs[long_edge][q_th][2]]),
    #                                tuple(xy_list[vs[long_edge][q_th][3]]),
    #                                tuple(xy_list[vs[long_edge][q_th][4]])],
    #                               width=3, fill='yellow')
    #         if cfg.gen_origin_img:
    #             im.save(os.path.join(val_image_dir, 'val_' + o_img_fname))
    #         np.save(os.path.join(
    #             val_label_dir,
    #             'val_' + o_img_fname[:-4] + '.npy'),
    #             xy_list_array)
    #         if draw_gt_quad:
    #             show_gt_im.save(os.path.join(show_gt_image_dir, o_img_fname))
    #         train_val_set.append('{},{},{}\n'.format('val_'+o_img_fname,
    #                                                  d_wight,
    #                                                  d_height))
    #

    #================================Test===================================================#
    o_test_img_list = os.listdir(origin_test_image_dir)
    print('found %d origin images.' % len(o_test_img_list))
    test_set = []
    for o_img_fname in tqdm(o_test_img_list):
        with Image.open(os.path.join(origin_test_image_dir, o_img_fname)) as im:
            d_wight, d_height = cfg.max_train_img_size, cfg.max_train_img_size
            im = im.resize((d_wight, d_height), Image.NEAREST).convert('RGB')
            if cfg.gen_origin_img:
                im.save(os.path.join(test_image_dir, 'test_'+o_img_fname))
            test_set.append('{},{},{}\n'.format('test_'+o_img_fname,
                                                     d_wight,
                                                     d_height))
    with open(os.path.join(data_dir, cfg.test_fname), 'w') as f_val:
        f_val.writelines(test_set)
    #

def f(origin_image_dir,origin_txt_dir,
    gen_origin_img,train_image_dir,train_label_dir,
    draw_gt_quad,show_gt_image_dir
    ,train_fname):
#origin_image_dir 存放训练集图像的文件夹
#origin_txt_dir 训练集的标签文件
#gen_origin_img 是否生成预处理后的图像
#train_image_dir 预处理后的图像所在文件夹
#train_label_dir 预处理后的标签所在文件夹
#draw_gt_quad 是否生成带bounding——box的图像
#show_gt_image_dir 预处理后的带bounding-box图像所在文件夹
#train_fname 提取出训练集图像高度和宽度后生成此txt文件, 文件内容及格式： 文件名 高度 宽度
    label = pd.read_csv(origin_txt_dir)

    o_img_list = os.listdir(origin_image_dir)
    print('found %d origin images.' % len(o_img_list))
    train_val_set = []
    for o_img_fname in tqdm(o_img_list):
        with Image.open(os.path.join(origin_image_dir, o_img_fname)) as im:
            # d_wight, d_height = resize_image(im)
            d_wight, d_height = cfg.max_train_img_size, cfg.max_train_img_size
            scale_ratio_w = d_wight / im.width
            scale_ratio_h = d_height / im.height
            im = im.resize((d_wight, d_height), Image.NEAREST).convert('RGB')
            show_gt_im = im.copy()
            # draw on the img
            draw = ImageDraw.Draw(show_gt_im)
            # with open(os.path.join(origin_txt_dir,'gt_'+o_img_fname[:-4] + '.txt'), 'r',encoding='utf-8-sig') as f:
            #     anno_list = f.readlines()

            txt = label[label['FileName'] == o_img_fname]

            anno_list = txt.get_values()
            xy_list_array = np.zeros((len(anno_list), 4, 2))
            for anno, i in zip(anno_list, range(len(anno_list))):
                anno_colums = anno[1:9]
                anno_array = np.array(anno_colums)
                xy_list = np.reshape(anno_array[:8].astype(float), (4, 2))
                xy_list[:, 0] = xy_list[:, 0] * scale_ratio_w
                xy_list[:, 1] = xy_list[:, 1] * scale_ratio_h
                xy_list = reorder_vertexes(xy_list)
                xy_list_array[i] = xy_list
                _, shrink_xy_list, _ = shrink(xy_list, cfg.shrink_ratio)
                shrink_1, _, long_edge = shrink(xy_list, cfg.shrink_side_ratio)
                if draw_gt_quad:
                    draw.line([tuple(xy_list[0]), tuple(xy_list[1]),
                               tuple(xy_list[2]), tuple(xy_list[3]),
                               tuple(xy_list[0])
                               ],
                              width=2, fill='green')
                    draw.line([tuple(shrink_xy_list[0]),
                               tuple(shrink_xy_list[1]),
                               tuple(shrink_xy_list[2]),
                               tuple(shrink_xy_list[3]),
                               tuple(shrink_xy_list[0])
                               ],
                              width=2, fill='blue')
                    vs = [[[0, 0, 3, 3, 0], [1, 1, 2, 2, 1]],
                          [[0, 0, 1, 1, 0], [2, 2, 3, 3, 2]]]
                    for q_th in range(2):
                        draw.line([tuple(xy_list[vs[long_edge][q_th][0]]),
                                   tuple(shrink_1[vs[long_edge][q_th][1]]),
                                   tuple(shrink_1[vs[long_edge][q_th][2]]),
                                   tuple(xy_list[vs[long_edge][q_th][3]]),
                                   tuple(xy_list[vs[long_edge][q_th][4]])],
                                  width=3, fill='yellow')
            if gen_origin_img:
                im.save(os.path.join(train_image_dir, 'train_' + o_img_fname))
            np.save(os.path.join(
                train_label_dir,
                'train_' + o_img_fname[:-4] + '.npy'),
                xy_list_array)
            if draw_gt_quad:
                show_gt_im.save(os.path.join(show_gt_image_dir, o_img_fname))
            train_val_set.append('{},{},{}\n'.format('train_'+o_img_fname,
                                                     d_wight,
                                                     d_height))
    with open(os.path.join(cfg.data_dir, train_fname), 'w') as f_train:
        f_train.writelines(train_val_set)
    train_img_list = os.listdir(train_image_dir)
    print('found %d train images.' % len(train_img_list))
    train_label_list = os.listdir(train_label_dir)
    print('found %d train labels.' % len(train_label_list))


if __name__ == '__main__':
    preprocess()
