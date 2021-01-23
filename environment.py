import pymongo

production = False

bilibili_accounts = [
    {
        "username": "wdan15854011021@163.com",
        "password": "214899"
    },
    {
        "username": "yvec2708459",
        "password": "ss1122"
    },
    {
        "username": "wfu9930",
        "password": "491145"
    },
    {
        "username": "jhe2109",
        "password": "821246"
    },
    {
        "username": "qe565386",
        "password": "zzxx1122"
    },
]

client = pymongo.MongoClient(
    "mongodb://crepusculum.xyz:27017/",
    username="bilibili",
    password="123"
)
DB = client["bilibili"]

USER_SPIDER_PERIOD = 2  # 访问速度2s
VIDEO_SPIDER_PERIOD = 2  # 访问速度2s

RANK_PERIOD: int = 60 * 60 * 24  # 排行榜数据1天更新一次
TRACKED_USER_PERIOD: int = 60 * 60 * 12  # 追踪用户每12小时获取数据
TRACKED_VIDEO_PERIOD: int = 60 * 30  # 追踪视频每0.5小时更新一次

MAX_UID = 700000000  # 随机用的最大uid
MAX_AID = 250000000  # 随机用的最大aid
