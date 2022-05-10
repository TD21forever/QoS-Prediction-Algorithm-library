import os

from scdmlab.config import BASE_PATH

# 获取项目根路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIRNAME = "data"  # 数据集放在根目录的data文件夹下

# 确定文件名正确
RT_MATRIX_NAME = "WSDream_1.rtMatrix"
TP_MATRIX_NAME = "WSDream_1.tpMatrix"
USERS_NAME = "WSDream_1.user"
WSLIST_NAME = "WSDream_1.service"

DATASET_DIR = os.path.join(BASE_PATH, 'data', 'dataset')

RT_MATRIX_DIR = os.path.join(DATASET_DIR, RT_MATRIX_NAME)
TP_MATRIX_DIR = os.path.join(DATASET_DIR, TP_MATRIX_NAME)
USER_DIR = os.path.join(DATASET_DIR, USERS_NAME)
WS_DIR = os.path.join(DATASET_DIR, WSLIST_NAME)

__all__ = ["RT_MATRIX_DIR", "TP_MATRIX_DIR", "USER_DIR", "WS_DIR"]