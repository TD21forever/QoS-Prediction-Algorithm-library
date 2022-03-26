from collections import namedtuple
from functools import partial

import numpy as np
import torch
from data import InfoDataset, MatrixDataset, ToTorchDataset
from models.XXXPlus.model import XXXPlus
from models.XXXPlus.resnet_utils import ResNetBasicBlock
from torch import nn, optim
from torch.nn.modules import loss
from torch.optim import Adam, optimizer
from torch.utils.data import DataLoader
from tqdm import tqdm
from utils.decorator import timeit
from utils.evaluation import mae, mse, rmse
from utils.model_util import count_parameters, freeze_random

from .model import XXXPlusModel

epochs = 3000
desnity = 0.05
type_ = "rt"


def data_preprocess(triad,
                    u_info_obj: InfoDataset,
                    i_info_obj: InfoDataset,
                    is_dtriad=False):
    """生成d_triad [[triad],[p_triad]]
    """
    r = []
    for row in tqdm(triad, desc="Gen d_triad"):
        uid, iid, rate = int(row[0]), int(row[1]), float(row[2])
        u = u_info_obj.query(uid)
        i = i_info_obj.query(iid)
        r.append([[uid, iid, rate], [u, i, rate]]) if is_dtriad else r.append(
            [u, i, rate])
    return r


u_enable_columns = ["[User ID]", "[Country]", "[AS]"]
i_enable_columns = ["[Service ID]", "[Country]", "[AS]"]

fed_data_preprocess = partial(data_preprocess, is_dtriad=True)

md = MatrixDataset(type_)
u_info = InfoDataset("user", u_enable_columns)
i_info = InfoDataset("service", i_enable_columns)
train, test = md.split_train_test(desnity)

# loss_fn = nn.SmoothL1Loss()
loss_fn = nn.L1Loss()

user_params = {
    "type_": "cat",  # embedding层整合方式 stack or cat
    "embedding_nums": u_info.embedding_nums,  # 每个要embedding的特征的总个数
    "embedding_dims": [8, 8, 8],
}

item_params = {
    "type_": "cat",  # embedding层整合方式 stack or cat
    "embedding_nums": i_info.embedding_nums,  # 每个要embedding的特征的总个数
    "embedding_dims": [8, 8, 8],
}

train_data = data_preprocess(train, u_info, i_info)
test_data = data_preprocess(test, u_info, i_info)
train_dataset = ToTorchDataset(train_data)
test_dataset = ToTorchDataset(test_data)
train_dataloader = DataLoader(train_dataset, batch_size=128)
test_dataloader = DataLoader(test_dataset, batch_size=2048)

model = XXXPlusModel(user_params, item_params, 48, 128, [128, 64, 32],
                     [2, 2, 2], loss_fn)
opt = Adam(model.parameters(), lr=0.0005)
print(f"模型参数:", count_parameters(model))
model.fit(train_dataloader,
          epochs,
          opt,
          eval_loader=test_dataloader,
          save_filename=f"{desnity}_{type_}")
