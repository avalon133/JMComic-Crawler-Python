from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
48691
60863
68459
84137
514371
587952
607341
579071
601284
596428
572167
535646
591506
615085
616118
641824
516851
517500
525223
509017
507113
501643
495488
481163
483827
484397
485015
480297
451610
448042
427369
409571
389479
326315
217709
91628
102769
121940
138988
87746
596428
458445
235769
309325
428338
509224
579071
217709
572167
448042
484397
524327
404482
250599
213645
102488
561626
228621
258589
455914
216113
645301
544851
496414
421058
372787
372619
271268
262054
247933
138334
136541
104906
135781
95472
625283
616067
1026854
527339
475378
413360
302792
363849
288261
181721
123901
17284
1070326
1068578
1033504
592437
608121
522397
519847
365563
592688
478541
520940
434252
439126
428980
380317
350772
356005
358988
344980
344524
341501
260994
259154
292444
292374
289442
273370
275130
275497
260290
295006
298257
304756
306827
336504
292761
259515
258086
250595
256489
229961
224711
239498
225191
222992
222461
145318
142180
97539
72926
65566
59778
37813
13793
6003
12895
444971
427741
414831
404137
181745
181862
181743
181742
148549
181740
136542
57406
35228
285830
332609
333042
632635
627809
347790
338732
309338
288661
288332
245223
245222
258589
254807
228621
216113
211776
148058
114380
31687
6873
10538
91628
102769
121940
138988
87746
596428
458445
235769
309325
428338
509224
579071
217709
572167
448042
484397
524327
404482
250599
213645
102488
561626
228621
258589
455914
216113














'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
