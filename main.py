from typing import List

from user_spider import UserSpider
from video_spider import VideoSpider
from rank_spider import RankSpider
from video_following_spider import VideoFollowingSpider

if __name__ == '__main__':
    rankSpider = RankSpider()
    videoFollowingSpider = VideoFollowingSpider()

    rankSpider.start()
    videoFollowingSpider.start()

    # 可以多线程加速
    userSpiders: List = [UserSpider()] * 1
    videoSpiders: List = [VideoSpider()] * 1

    for userSpider in userSpiders:
        userSpider.start()
    for videoSpider in videoSpiders:
        videoSpider.start()


