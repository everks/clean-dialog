python3 run_dist.py --raw_dir ./toy_data/raw/ --out_dir ./toy_data/output/ \
--dirty_dir ./toy_data/output/ --no_utter_dup --split_multi_repost --de_reply_tag \
--de_hashtag --de_single_repost_mention --de_duplicated --de_emoji --no_long \
--bert_clean --no_str_blacklist --cleantext_clean --no_specific_utter --no_toupiao \
--de_url --de_weibo_url --contain_zh --no_mention --de_showall --de_brackets \
--de_angle --de_specific --de_phone --de_qq --de_alpha_num  --n_p 16 \
--remove_all --simplified --punc_regularized --no_session_ad --context_filter