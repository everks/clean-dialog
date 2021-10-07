import os
import gc
import jieba
import tqdm
import collections
import logging

from cleantext import clean

from src.inputters.data_utils import *
from src.rules import session_level, data_level, str_level

logger = logging.getLogger(__file__)

MAX_LEN_STR_BLACKWORD = 120
SHOWALL = ["zhihu"]
BRACKET = ["weibo_tang"]
SPECIAL_LISTS = ["<EMAIL>", "<PHONE>"]


def main_filter(opt, file_id, data, blacklist, out_path, dirty_dir, cut=True):
    '''
    Args:
        opt: 命令行参数args
        file_id: 清洗后的数据应该存放的文件名（不包含后缀）
        data: (path, start, end) 分别为需要清洗的数据文件存放路径，文件中开始行数（包含）和结束行数（不包含）
        blacklist: 字典类型，存放各种辅助数据，TODO: 待补充
        out_path: 清洗后的数据应该存放的文件路径
        dirty_dir: 清洗后的脏数据应该存放的文件路径
        cut: 
    Returns:

    '''
    try:
        logger.info("The saved path of data is {}".format(out_path))

        if not os.path.exists(os.path.dirname(out_path)):
            logger.error("{} dost not exist!!!!!!".format(os.path.dirname(out_path)))
            return

        logger.info("Start : {}".format(file_id))
        # data = loader(path)

        dirty_data = {k: collections.defaultdict(set) for k in
                      ["other", "name", "str_blacklist", "word_blacklist", "not_en", "confused", "generic", "emoji",
                       "duplicated", "confuse"]} if dirty_dir else None

        time_dict = collections.defaultdict(float)

        global MAX_LEN_STR_BLACKWORD
        MAX_LEN_STR_BLACKWORD = max(len(x) for x in blacklist["str_blacklist"]) + 2

        res = []
        if isinstance(data, tuple):
            data = load_lines(data[0], data[1], data[2])
        logger.info("Size of this batch : {}, log in {}".format(len(data), file_id))
        logger.info("Batch sample: {}, log in {}".format(data[0][0], file_id))
        while len(data):
            dialog = data.pop(0)
            # session level
            # dialog = session_check(opt, dialog)

            if opt.no_utter_dup:
                # 排除所有去重后不构成对话的数据
                if len(set(dialog)) < 2:
                    if dirty_data and len(set(dialog)) > 0:
                        dirty_data["other"]["less_pair"].add(dialog[0])
                    continue

            # songyi 10-6
            if opt.no_session_ad and session_level.isAd(dialog):
                dirty_data['other']['session_ad'].add(dialog[0])

            new_dialog = []
            # 对dialog中的每一个uttr进行清洗，将清洗后的数据放入new_dialog
            for i in range(len(dialog)):
                # 根据微博转发规则将对话拆开, utters 是对话的数组，即数组的数组。
                # TODO: 问答是不是倒了？
                if opt.split_multi_repost:
                    utters = str_level.split_multi_repost(dialog[i])
                else:
                    utters = [dialog[i]]

                skip_utter = False
                # 对于拆分出来的utters
                for j, utter in enumerate(utters):
                    if skip_utter:
                        skip_utter = False
                        continue

                    # 判断如果数据是微博投票，将数据过滤掉
                    # 如果下一句是投票的话，则跳过这句和下一句
                    if opt.no_toupiao and (j + 1) < len(utters):
                        toupiao = str_level.no_toupiao(utters[j + 1])
                        if toupiao:
                            skip_utter = True
                            if dirty_data:
                                dirty_data["other"]["toupiao"].add(utters[j] + "\t\t" + utters[j + 1])
                            continue

                    
                    # 删除空格
                    tight_utter = utter.replace(" ", "")
                    # 进行正则表达式，关键词匹配，将clean后的utter保存到new_dialog
                    utter = utterance_clean(opt, file_id, utter, tight_utter, blacklist, dirty_data, time_dict, cut)
                    # utter为分词后的字符串，词与词之间用空格隔开
                    new_dialog.append(utter)

            # 同一替换对话中所有的人名
            if opt.re_name:
                new_dialog = session_level.de_name(new_dialog, blacklist["name"])


            # TODO: 暂时没看懂
            start_idx = 0 if new_dialog[0] else 1
            for i in range(1, len(new_dialog) + 1):
                if i == len(new_dialog) or not new_dialog[i]:
                    if opt.no_short_response:
                        part_dialog = new_dialog[start_idx: i][:]
                        part_dialog = session_level.no_short_response(part_dialog)
                        if len(part_dialog) > 1:
                            res.append(part_dialog)
                    else:
                        if len(new_dialog[start_idx: i]) > 1:
                            res.append(new_dialog[start_idx: i])
                    start_idx = i + 1
            # for i in range(1, len(new_dialog)):
            #     if not new_dialog[i]:
            #         if len(new_dialog[start_idx: i]) > 1:
            #             res.append(new_dialog[start_idx: i])
            #         start_idx = i + 1
            #     elif i == len(new_dialog) - 1:
            #         if len(new_dialog[start_idx:]) > 1:
            #             res.append(new_dialog[start_idx:])

        # data level
        if opt.no_ad:
            res = data_level.no_ad(res, dirty_data)

        if opt.de_generic_dialog:
            res = data_level.de_generic(res, dirty_data, out_path.replace(".jsonl", "_trigram.jsonl"), 1000)

        if len(res) > 0:
            # save_jsonl(res, out_path)
            save_txt("\n".join(["\t\t".join(x) for x in res]), out_path)
            logger.info("Resulting {} dialogs".format(len(res)))
            del res, data
            gc.collect()

        # save dirty data
        if dirty_dir:
            save_dirty(dirty_dir, dirty_data, file_id)
        logger.info("{}  over".format(file_id))
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        logger.error("Error !!!! : {}, log in {}".format(e, out_path))
    return file_id


def save_dirty(dirty_dir, dirty_data, file_id):
    dirty_dir = os.path.join(dirty_dir, "dirty_data")
    if not os.path.isdir(dirty_dir):
        os.makedirs(dirty_dir)
    for k, v in dirty_data.items():
        k_path = os.path.join(dirty_dir, k)
        if sum(len(subv) for subv in v.values()):
            if not os.path.isdir(k_path):
                os.mkdir(k_path)
            if "blacklist" in k and len(v) > 0:
                temp_bl = {bk: len(bv) for bk, bv in v.items()}
                temp_bl = sorted(temp_bl.items(), key=lambda x: x[1], reverse=True)
                save_json(temp_bl, os.path.join(k_path, "sta_{}.json".format(file_id)))
                save_json({bk: list(bv) for bk, bv in v.items()}, os.path.join(k_path, "{}.json".format(file_id)))
            else:
                for sub_k, sub_v in v.items():
                    if len(sub_v) > 0:
                        save_jsonl(sub_v, os.path.join(k_path, "{}_{}.jsonl".format(sub_k, file_id)))
    del dirty_data
    gc.collect()
    return


def add_filter_args(argparser):
    opt = argparser.add_argument_group('Filter Arguments')

    opt.add_argument('--no_utter_dup', action="store_true")
    opt.add_argument('--re_name', action="store_true")
    opt.add_argument('--split_multi_repost', action="store_true")
    opt.add_argument('--no_ad', action="store_true")
    opt.add_argument('--de_generic_dialog', action="store_true")
    opt.add_argument('--de_reply_tag', action="store_true")
    opt.add_argument('--de_hashtag', action="store_true")
    opt.add_argument('--de_emotion', action="store_true")
    opt.add_argument('--de_mention', action="store_true")
    opt.add_argument('--de_repost', action="store_true")
    opt.add_argument('--de_duplicated', action="store_true")
    opt.add_argument('--de_emoji', action="store_true")
    opt.add_argument('--no_short', action="store_true")
    opt.add_argument('--no_long', action="store_true")
    opt.add_argument('--no_special_topic', action="store_true")
    opt.add_argument('--bert_clean', action="store_true")
    opt.add_argument('--cleantext_clean', action="store_true")
    opt.add_argument('--no_str_blacklist', action="store_true")
    opt.add_argument('--no_toupiao', action="store_true")
    opt.add_argument('--no_short_response', action="store_true")
    opt.add_argument('--no_specific_utter', action="store_true")
    opt.add_argument('--contain_zh', action="store_true")
    opt.add_argument('--de_single_repost_mention', action="store_true")
    opt.add_argument('--de_weibo_url', action="store_true")
    opt.add_argument('--de_url', action="store_true")
    opt.add_argument('--no_mention', action="store_true")
    opt.add_argument('--de_angle', action="store_true")
    opt.add_argument('--de_alpha_num', action="store_true")
    opt.add_argument('--de_phone', action="store_true")
    opt.add_argument('--de_qq', action="store_true")
    opt.add_argument('--de_specific', action="store_true")

    # special files
    opt.add_argument('--de_showall', action="store_true")
    opt.add_argument('--de_brackets', action="store_true")

    # words list level
    opt.add_argument('--no_word_blacklist', action="store_true")
    opt.add_argument('--no_alpha_noise', action="store_true")
    opt.add_argument('--check_confuse_word', action="store_true")
    opt.add_argument('--yda_dedupl', action="store_true")
    # todo remedy http

    # songyi 10-6
    opt.add_argument('--simplified', action='store_true')
    opt.add_argument('--punc_regularized', action='store_true')
    opt.add_argument('--no_session_ad', action='store_true')
    opt.add_argument('--remove_all', action='store_true')


def utterance_clean(opt, file_id, utterance, tight_utter, blacklist, dirty_data, time_dict, cut,
                    return_segmented=True) -> str:
    """
    Args:
        opt: 
        file_id: 
        utterance: 拆分过后的句子
        tight_utter: 拆分过后并祛除了空格的句子
        blacklist: 
        dirty_data:
        time_dict:
        cut:
        return_segmented:
    """
    orig_utter = utterance[:]
    utterance = utterance.strip()

    # TODO: 不知道是什么作用
    utterance = utterance.replace("alink", "")

    # songyi 10-6
    if opt.remove_all:
        utterance = str_level.removeAll(utterance)

    # TODO check
    if "¡ 评论" in utterance:
        utterance = utterance[:utterance.index("¡ 评论")]
        if dirty_data:
            dirty_data["other"]["¡ 评论"].add(orig_utter)

    # 去除一些特定的句子，如 "转发" 
    if utterance and opt.no_specific_utter:
        specific_utter = str_level.no_specific_utter(tight_utter)
        if specific_utter:
            if dirty_data:
                dirty_data["other"]["specific_utter"].add(orig_utter)
            utterance = ""

    # 去除微博中 "回复 @XXX:"
    if utterance and opt.de_reply_tag:
        len_before = len(utterance)
        utterance = str_level.REPLY_MENTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_reply_tag"].add(orig_utter)

    # regex
    # 去除 <XXX> 其中XXX为非中文
    if utterance and opt.de_angle:
        len_before = len(utterance)
        utterance = str_level.ANGLE_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["angle"].add(orig_utter)

    if utterance and opt.de_url:
        len_before = len(utterance)
        utterance = str_level.URL_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["url"].add(orig_utter)

    if utterance and opt.de_weibo_url:
        len_before = len(utterance)
        utterance = str_level.WEIBO_URL_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["weibo_url"].add(orig_utter)

    if utterance and opt.de_brackets:
        len_before = len(utterance)
        utterance = str_level.BRACKETS_REGEX2.sub("", utterance).strip()
        # utterance = str_level.BRACKETS_REGEX3.sub("", utterance).strip()
        if any([x for x in BRACKET if x in file_id]):
            utterance = str_level.BRACKETS_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["weibo_emoji"].add(orig_utter)

    if utterance and opt.de_hashtag:
        len_before = len(utterance)
        utterance = str_level.HASHTAG_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["hashtag"].add(orig_utter)

    if utterance and opt.de_emotion:
        len_before = len(utterance)
        utterance = str_level.EMOTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["emotion"].add(orig_utter)

    if utterance and opt.no_mention:
        if str_level.contain_at(utterance):
            if dirty_data:
                dirty_data["other"]["mention"].add(orig_utter)
            utterance = ""

    if utterance and opt.de_mention:
        len_before = len(utterance)
        # utterance = str_level.COMMON_MENTION_REGEX.sub("", utterance).strip()
        utterance = str_level.no_at(utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["no_at"].add(orig_utter)

    if utterance and opt.de_single_repost_mention:
        len_before = len(utterance)
        utterance = str_level.SINGLE_REPPOST_MENTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["single_repost"].add(orig_utter)

    if utterance and opt.de_repost:
        len_before = len(utterance)
        utterance = str_level.REPPOST_MENTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["repost_mention"].add(orig_utter)

    if utterance and opt.de_showall and any([x for x in SHOWALL if x in file_id]):
        len_before = len(utterance)
        utterance = str_level.ZHIHU_SHOW_ALL_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["showall"].add(orig_utter)

    if utterance and opt.de_emoji:
        len_before = len(utterance)
        utterance = str_level.remove_emoji3(utterance)
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["emoji"].add(orig_utter)

    if utterance and opt.de_alpha_num:
        len_before = len(utterance)
        utterance = str_level.ALPHA_NUM_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_alpha_num"].add(orig_utter)

    if utterance and opt.de_specific:
        len_before = len(utterance)
        utterance = str_level.de_specific(utterance)
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_specific"].add(orig_utter)

    if utterance and opt.de_phone:
        len_before = len(utterance)
        utterance = str_level.PHONE_REGEX.sub("</PHONE>", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_phone"].add(orig_utter)

    if utterance and opt.de_qq:
        len_before = len(utterance)
        utterance = str_level.QQ_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_qq"].add(orig_utter)

    # clean-text lib
    if utterance and opt.cleantext_clean:
        len_before = len(utterance)
        utterance = clean(
            utterance,
            fix_unicode=True,
            to_ascii=False,
            normalize_whitespace=True,
            no_line_breaks=True,
            no_urls=False,
            no_emails=True,
            no_phone_numbers=True,
            replace_with_url=" ",
            replace_with_email="</EMAIL>",
            replace_with_phone_number="</PHONE>")
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["cleantext"].add(orig_utter)

    # TODO: 没细看
    if utterance and opt.bert_clean:
        utterance = str_level.bert_clean(utterance)

    if utterance and opt.de_emoji:
        utterance = str_level.COLON_REGEX.sub("", utterance).strip()

    if utterance and opt.contain_zh:
        if not str_level.contains_Chinese(utterance):
            if dirty_data:
                dirty_data["other"]["contain_zh"].add(orig_utter)
            utterance = ""

    if utterance and opt.no_special_topic:
        special_topic_word = str_level.de_str_blacklist(tight_utter, blacklist["special_topic"])
        if special_topic_word:
            if dirty_data:
                dirty_data["special_topic"][special_topic_word].add(orig_utter)
            utterance = ""

    if utterance and opt.no_str_blacklist:
        utterance = str_level.TM_REGEX.sub(lambda m: m.group(1) + m.group(3), utterance)
        global MAX_LEN_STR_BLACKWORD
        black_word = str_level.de_str_blacklist2(tight_utter, blacklist["str_blacklist"], MAX_LEN_STR_BLACKWORD)
        if black_word:
            if dirty_data:
                dirty_data["str_blacklist"][black_word].add(orig_utter)
            utterance = ""

    # TODO: 没细看
    if utterance and opt.de_duplicated:
        len_before = len(utterance)
        utterance = str_level.reduce_duplicated_phrase(utterance)
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_duplicated"].add(orig_utter)

    if utterance and opt.no_short:
        len_flag = str_level.too_short(utterance)
        if len_flag:
            if dirty_data:
                dirty_data["other"]["short"].add(orig_utter)
            utterance = ""

    if utterance and opt.no_long:
        len_flag = str_level.too_long(utterance)
        if len_flag:
            if dirty_data:
                dirty_data["other"]["long"].add(orig_utter)
            utterance = ""

    # songyi 10-6 
    if utterance and opt.simplified:
        utterance = str_level.toSimplified(utterance)
    
    if utterance and opt.punc_regularized:
        utterance = str_level.puncRegularized(utterance)



    if not any([opt.no_alpha_noise, opt.check_confuse_word, opt.no_word_blacklist, opt.yda_dedupl]):
        return utterance.strip()

    

    ### word level
    if cut:
        word_list = list(jieba.cut(utterance))
    else:
        word_list = utterance.strip().split()

    if word_list and opt.no_alpha_noise:
        alpha_word = str_level.not_en(word_list, blacklist["english"])
        if alpha_word:
            if dirty_data:
                dirty_data["not_en"][alpha_word].add(orig_utter)
            word_list = []
            utterance = ""

    if word_list and opt.check_confuse_word:
        confuse_word = str_level.check_confuse(word_list, blacklist["confuse"])
        if confuse_word:
            if dirty_data:
                dirty_data["confuse"][confuse_word].add(orig_utter)

    if word_list and opt.no_word_blacklist:
        dirty_word = str_level.de_word_blacklist(word_list, blacklist["word_blacklist"])
        if dirty_word:
            if dirty_data:
                dirty_data["word_blacklist"][dirty_word].add(orig_utter)
            word_list = []
            utterance = ""

    if word_list and opt.yda_dedupl:
        yda_dupl_flag = str_level.judge_yda_dupl(word_list)
        if yda_dupl_flag:
            if dirty_data:
                dirty_data["duplicated"]["yda"].add(orig_utter)
            word_list = []
            utterance = ""

    return " ".join(word_list).strip() if return_segmented else utterance.strip()
