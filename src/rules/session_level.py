import re

def de_name(session, name_set):
    n = 1
    name_dict = {}
    dialog = []
    for i, utter in enumerate(session):
        seq = []
        for j, word in enumerate(utter.split()):
            if word in name_set:
                if word not in name_dict:
                    name_dict[word] = "<NAME{}>".format(n)
                    n += 1
                seq.append(name_dict[word])
            else:
                seq.append(word)
        dialog.append(" ".join(seq))
    return dialog


def no_short_response(session, min_len=2):
    while session and len(session[-1].replace(" ", "")) < min_len:
        session = session[:-1]
    return session


# author: songyi
# date: 10-6
def isAd(dialog):
    '''判断当前dialog是否为广告，通过判断dialog的第一句话即context来决定（后续可进行更改）'''
    context = dialog[0]
    
    ad_list = ['出租','转卖','成新','代购','出售','转让','合租','直租','整租','开团','便宜卖']

    for ad_word in ad_list:
        if ad_word in context:
            return True
    return False

context_filter_pattern = re.compile('[0-9]{3,}$')
def pass_context_filter(dialog):
    text = dialog[0]
    if text.endswith('vo:') or context_filter_pattern.search(text):
        return False
    return True