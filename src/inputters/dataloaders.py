import os
import random
import platform
from src.inputters.data_utils import *


def simple_dataloader(dir_path, out_dir, batch_size):
    """Load jsonl data, each line should be a list of dialog: ["你好", "你也好", "哈哈"]"""
    cleaned_dir = os.path.join(out_dir, "cleaned_data")
    if not os.path.exists(cleaned_dir):
        os.mkdir(cleaned_dir)

    subdirs = [(subdir, os.path.join(dir_path, subdir)) for subdir in os.listdir(dir_path)]
    jsonl_path_list = [(file, subdir, os.path.join(subdir_path, file))
                       for subdir, subdir_path in subdirs
                       for file in os.listdir(subdir_path) if file.endswith(".jsonl")]
    # random.shuffle(jsonl_path_list)
    for file, subdir_name, path in jsonl_path_list:
        dataset = load_jsonl(path)
        for i in range(0, len(dataset), batch_size):
            fid = subdir_name + "_" + file.replace(".jsonl", "") + "_trunc" + str(i)
            # out
            out_subdir = os.path.join(cleaned_dir, subdir_name)
            if not os.path.exists(out_subdir):
                os.mkdir(out_subdir)
            out_path = os.path.join(out_subdir, fid + ".jsonl")
            yield fid, dataset[i: i + batch_size], out_path


def paths_dataloader(dir_path, out_dir, batch_size):
    """Load jsonl data, each line should be a list of dialog: ["你好", "你也好", "哈哈"]
    清洗过后的文件保存在"out_dir/cleaned_data/"目录下
    输入目录应为单层目录

    return:
        fid: 清洗后的数据存放的文件名（不包含后缀）
        path: 输入文件的路径
        start: 对应batch需要处理的输入文件开始行
        end -- 对应batch需要处理的输入文件结束行（不包含）
        out_path -- 清洗后的数据存放的文件路径
    """

    cleaned_dir = os.path.join(out_dir, "cleaned_data")
    if not os.path.exists(cleaned_dir):
        os.makedirs(cleaned_dir)
    jsonl_path_list = [(file, os.path.join(dir_path, file)) for file in os.listdir(dir_path) if file.endswith('.jsonl')]
    for file, path in jsonl_path_list:
        if platform.system() == "Windows":
            file_len = buff_count(path)
        elif platform.system() == "Linux":
            file_len = wc_count(path)
        else:
            raise Exception
        print('path', file_len)
        for i in range(0, file_len, batch_size):
            fid = file.replace(".jsonl", "") + "_trunc" + str(i)
            # out
            out_subdir = cleaned_dir
            if not os.path.exists(out_subdir):
                os.mkdir(out_subdir)
            out_path = os.path.join(out_subdir, fid + ".txt")
            yield fid, path, i, i + batch_size, out_path




# def paths_dataloader(dir_path, out_dir, batch_size):
#     """Load jsonl data, each line should be a list of dialog: ["你好", "你也好", "哈哈"]
#     清洗过后的文件保存在"out_dir/cleaned_data/"目录下
#     TODO: 目前这个dataloader只处理jsonl文件，且输入目录应是两级目录而且以及目录下不能存在文件。
#     return:
#         fid: 清洗后的数据存放的文件名（不包含后缀）
#         path: 输入文件的路径
#         start: 对应batch需要处理的输入文件开始行
#         end -- 对应batch需要处理的输入文件结束行（不包含）
#         out_path -- 清洗后的数据存放的文件路径
#     """
#     cleaned_dir = os.path.join(out_dir, "cleaned_data")
#     if not os.path.exists(cleaned_dir):
#         os.makedirs(cleaned_dir)

#     subdirs = [(subdir, os.path.join(dir_path, subdir)) for subdir in os.listdir(dir_path)]
#     jsonl_path_list = [(file, subdir, os.path.join(subdir_path, file))
#                        for subdir, subdir_path in subdirs
#                        for file in os.listdir(subdir_path) if file.endswith(".jsonl")]
#     # random.shuffle(jsonl_path_list)
#     for file, subdir_name, path in jsonl_path_list:
#         #dataset = load_jsonl(path)
#         #print(len(dataset))
#         if platform.system() == "Windows":
#             file_len = buff_count(path)
#         elif platform.system() == "Linux":
#             file_len = wc_count(path)
#         else:
#             raise Exception
#         print('path', file_len)
#         for i in range(0, file_len, batch_size):
#             fid = subdir_name + "_" + file.replace(".jsonl", "") + "_trunc" + str(i)
#             # out
#             out_subdir = os.path.join(cleaned_dir, subdir_name)
#             if not os.path.exists(out_subdir):
#                 os.mkdir(out_subdir)
#             out_path = os.path.join(out_subdir, fid + ".txt")
#             yield fid, path, i, i + batch_size, out_path
