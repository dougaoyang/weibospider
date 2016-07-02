import time, sys, logging, gl, requests
from gl import time_out, login_name
from do_dataprocess.basic import is_403


def get_page(session, url, headers, user_verify=True):
    try:
        page = session.get(url, headers=headers, timeout=time_out, verify=False, stream=False).text
        if user_verify:
            if is_403(page):
                logging.info('账号{username}已经被冻结'.format(username=login_name))
                logging.info('本次抓取结束，时间是:{curtime}，一共抓取了{count}个页面'.format(curtime=time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime()), count=gl.count))
                sys.exit(-1)
    except TimeoutError:
        print('抓取{url}超时'.format(url=url))
        return ''
    except requests.exceptions.ConnectionError:
        logging.info('设置stream=False无效')
        logging.info('新浪服务器拒绝连接')
        time.sleep(60*10) # 休眠10分钟
    else:
        gl.count += 1
        time.sleep(60)
        return page