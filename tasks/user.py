# coding:utf-8
from tasks.workers import app
from page_parse.user import public
from page_get.basic import get_page
from page_parse.basic import is_404
from page_get import user as user_get
from db.seed_ids import (
                         get_seed_ids,
                         get_seed_by_id,
                         insert_seeds,
                         set_seed_other_crawled
                        )


home_url = 'https://weibo.com/u/{}/home?topnav=1&wvr=6'


@app.task(ignore_result=True)
def crawl_follower_fans(uid, domain):
    seed = get_seed_by_id(uid)
    if seed.other_crawled == 0:
        rs = user_get.get_fans_or_followers_ids(uid, domain, 1)
        rs.extend(user_get.get_fans_or_followers_ids(uid, domain, 2))
        datas = set(rs)
        # If data already exits, just skip it
        if datas:
            insert_seeds(datas)
        set_seed_other_crawled(uid)


@app.task(ignore_result=True)
def crawl_person_infos(uid):
    """
    Crawl user info and their fans and followers
    For the limit of weibo's backend, we can only crawl 5 pages of the fans and followers.
    We also have no permissions to view enterprise's followers and fans info
    :param uid: current user id
    :return: None
    """
    if not uid:
        return

    url = home_url.format(uid)
    html = get_page(url)
    if is_404(html):
        return None

    domain = public.get_userdomain(html)

    user, is_crawled = user_get.get_profile(uid, domain)
    # If it's enterprise user, just skip it
    if user and user.verify_type == 2:
        set_seed_other_crawled(uid)
        return

    # Crawl fans and followers
    if not is_crawled:
        app.send_task('tasks.user.crawl_follower_fans', args=(uid, domain), queue='fans_followers',
                      routing_key='for_fans_followers')


@app.task(ignore_result=True)
def excute_user_task():
    seeds = get_seed_ids()
    if seeds:
        for seed in seeds:
            app.send_task('tasks.user.crawl_person_infos', args=(seed.uid,), queue='user_crawler',
                          routing_key='for_user_info')

