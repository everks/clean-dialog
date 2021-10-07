import re
import string
from zhon import hanzi
print(string.punctuation)

punctuation = string.punctuation + hanzi.punctuation
print(re.sub("([%s]+)([%s])" %(punctuation, punctuation), "\\2", "h哈。。。？？？！！！你好"))