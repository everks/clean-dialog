from hanziconv import HanziConv
import re
import string
import string
from zhon import hanzi

def toSimplified(text):
    return HanziConv.toSimplified(text)

def puncRegularized(text):
    '''如果有多个标点符号连在一起，调整为最后一个出现的符号'''
    punctuation = string.punctuation + hanzi.punctuation
    return re.sub("([%s]+)([%s])" %(punctuation, punctuation), "\\2", text)

def isAd(dialog):
    '''判断当前dialog是否为广告，通过判断dialog的第一句话即context来决定（后续可进行更改）'''
    context = dialog[0]
    
    ad_list = ['出租','转卖','成新','代购','出售','转让','合租','直租','整租','开团','便宜卖']

    for ad_word in context:
        if ad_word in context:
            return True
    return False


pattern = re.compile('[^\u4e00-\u9fa5_a-zA-Z0-9%s%s]+' % (string.punctuation, hanzi.punctuation))
def removeAll(text):
    '''删除所有非中文和英文的字符'''
    text = "'我是[🍐]@/.(⊙o⊙)…फक यूadkg/,\]\=-'./.,';.'"
    print(pattern.sub('', text))

if __name__ == '__main__':

    ret = puncRegularized('衣服】11元!zara工字背心!要干净的纯棉的!不要螺纹的不要竖纹的!!!手机党马克')
    print(ret)
    


