import os

text = ' 一起来吗？@Cindy //@Bob: 算我一个//@Amy: 今晚开派对吗？'

def split_multi_repost(utter):
    # 一起来吗？@Cindy //@Bob: 算我一个//@Amy: 今晚开派对吗？
    if utter.find("//@") > -1:
        utters = [x.strip() for x in utter.split("//@")]
        for i in range(1, len(utters)):
            if utters[i]:
                utters[i] = "@" + utters[i]
        return utters
    return [utter]

print(split_multi_repost(text))