# import re
# import string
# from zhon import hanzi
# print(string.punctuation)

# punctuation = string.punctuation + hanzi.punctuation
# print(re.sub("([%s]+)([%s])" %(punctuation, punctuation), "\\2", "h哈。。。？？？！！！你好"))


# suffix = "/home/zhengyinhe/DialogueFilter/data/ripe_20180813"

# filename = suffix + '/weibo_20000002_30000002.pkl'

# import pickle
# with open(filename, 'rb') as f:
#     res = pickle.load(f)

# 生成lccc测试文件，判断清洗框架留存率
import jsonlines
def convert_to_jsonl(file, write_suffix):
    if not os.path.exists(write_suffix):
        os.makedirs(write_suffix)

    write_path = os.path.join(write_suffix, file.rsplit('/', 1)[-1] + 'jsonl')


    with open(file, 'r', errors='ignore') as f:
        lines = f.read().strip('\n').split('\n') 

    with jsonlines.open(write_path, mode='w') as writer:
        for line in tqdm(lines):
            dialog = line.split('\t')
            writer.write(dialog) 

    
def to_jsonl(type='lccc', number=10):
    suffix = '/extension/songyi/' + type
    file_list = [os.path.join(suffix, file) for file in os.listdir(suffix) if file.startswith('dialog')]
    file_list = random.sample(file_list, number)
    for file in file_list:
        convert_to_jsonl(file, type)

import os
from tqdm import tqdm
def score(file_paths):

    session_count, sentence_count, token_count, \
        multi_session_count, multi_sentence_count, multi_token_count = 0, 0, 0, 0, 0, 0
    
    for file_path in file_paths:
        with open(file_path, 'r', errors='ignore') as f:
            lines = f.read().strip('\n').split('\n')
        for line in tqdm(lines):
            dialog = line.split('\t')
            session_count += 1
            sentence_count += len(dialog)
            if len(dialog) > 2:
                multi_session_count += 1
                multi_sentence_count += len(dialog)
            for sentence in dialog:
                token_count += len(sentence)
                if len(dialog) > 2:
                    multi_token_count += len(sentence)
    
    return session_count, sentence_count / session_count, token_count / sentence_count, \
        session_count - multi_session_count, multi_sentence_count / multi_session_count, \
            multi_token_count / multi_sentence_count
            
import re
import string
from zhon import hanzi
REMOVE_ALL_PATTERN = re.compile('[^\u4e00-\u9fa5_a-zA-Z0-9%s%s]+' % (string.punctuation, hanzi.punctuation))
def removeAll(text):
    '''删除所有非中文和英文的字符'''
    return REMOVE_ALL_PATTERN.sub('', text)

import os
import random
if __name__ == '__main__':
    # print(score())

    # to_jsonl('lccc')
    # to_jsonl('lccc-origin')

    print(removeAll('$*&(@$#)($&)2346'))

    # 评估lccc
    # suffix = '/extension/songyi/lccc-origin/'
    # file_paths = [os.path.join(suffix, file) for file in os.listdir(suffix) if file.startswith('dialog')]

    # 评估豆瓣

    ## 评估基本分数
    suffix = '/extension/songyi/douban_data'
    file_paths = [os.path.join(suffix, file) for file in os.listdir(suffix)]
    #print(score(file_paths))
    ## 评估留存率
    import random
    write_suffix = '/home/songyi/clean/9-30/clean_test/input/douban/test/'
    convert_to_jsonl(random.choice(file_paths), write_suffix)

    
    

