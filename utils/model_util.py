import copy
import os
import random
import shutil

import numpy as np
import torch
from root import absolute
from torch import nn
"""
    Some handy functions for model training ...
"""


def save_checkpoint(state,
                    is_best,
                    save_dirname="output",
                    save_filename="best_model.ckpt"):
    """Save checkpoint if a new best is achieved"""
    if not os.path.isdir(absolute(save_dirname)):
        os.makedirs(absolute(save_dirname))
    file_path = absolute(f"{save_dirname}/{save_filename}")
    if is_best:
        print("=> Saving a new best")
        print(file_path)
        torch.save(state, file_path)  # save checkpoint
    else:
        print("=> Validation Accuracy did not improve")


def load_checkpoint(file_path: str, device=None):
    """Loads torch model from checkpoint file.
    Args:
        file_path (str): Path to checkpoint directory or filename
    """
    if not os.path.exists(file_path):
        raise Exception("ckpt file doesn't exist")
    ckpt = torch.load(file_path, map_location=device)
    print(' [*] Loading checkpoint from %s succeed!' % file_path)
    return ckpt


def use_cuda(enabled, device_id=0):
    if enabled:
        assert torch.cuda.is_available(), 'CUDA is not available'
        torch.cuda.set_device(device_id)


def freeze_random(seed=2021):
    torch.cuda.manual_seed(seed)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)


def triad_to_matrix(triad, nan_symbol=-1):
    """三元组转矩阵

    Args:
        triad : 三元组
        nan_symbol : 非零数据的表示方法. Defaults to -1.

    """
    # 注意下标应该为int
    if not isinstance(triad, np.ndarray):
        triad = np.array(triad)
    x_max = triad[:, 0].max().astype(int)  # 用户数量
    y_max = triad[:, 1].max().astype(int)  # 项目数量
    matrix = np.full((x_max + 1, y_max + 1), nan_symbol,
                     dtype=triad.dtype)  # 初始化QoS矩阵
    matrix[triad[:, 0].astype(int),
           triad[:, 1].astype(int)] = triad[:, 2]  # 将评分值放到QoS矩阵的对应位置中
    return matrix


def split_d_triad(d_triad):
    l = np.array(d_triad, dtype=np.object)
    return np.array(l[:, 0].tolist()), l[:, 1].tolist()


def nonzero_user_mean(matrix, nan_symbol):
    """快速计算一个矩阵的行均值
    """
    m = copy.deepcopy(matrix)
    m[matrix == nan_symbol] = 0
    t = (m != 0).sum(axis=-1)  # 每行非0元素的个数
    res = (m.sum(axis=-1) / t).squeeze()
    res[np.isnan(res)] = 0
    return res


def nonzero_item_mean(matrix, nan_symbol):
    """快速计算一个矩阵的列均值
    """
    return nonzero_user_mean(matrix.T, nan_symbol)


def use_optimizer(network, opt, lr):
    if opt == 'sgd':
        optimizer = torch.optim.SGD(network.parameters(), lr=lr, momentum=0.99)
    elif opt == 'adam':
        optimizer = torch.optim.Adam(network.parameters(),
                                     lr=lr,
                                     weight_decay=1e-8)
    return optimizer


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


#########################
# Weight initialization #
#########################
def init_weights(model, init_type, init_gain):
    """Function for initializing network weights.

    Args:
        model: A torch.nn instance to be initialized.
        init_type: Name of an initialization method (normal | xavier | kaiming | orthogonal).
        init_gain: Scaling factor for (normal | xavier | orthogonal).

    Reference:
        https://github.com/DS3Lab/forest-prediction/blob/master/pix2pix/models/networks.py
    """
    def init_func(m):
        classname = m.__class__.__name__
        if hasattr(m, 'weight') and (classname.find('Conv') != -1
                                     or classname.find('Linear') != -1):
            if init_type == 'normal':
                init.normal_(m.weight.data, 0.0, init_gain)
            elif init_type == 'xavier':
                init.xavier_normal_(m.weight.data, gain=init_gain)
            elif init_type == 'kaiming':
                init.kaiming_normal_(m.weight.data, a=0, mode='fan_in')
            else:
                raise NotImplementedError(
                    f'[ERROR] ...initialization method [{init_type}] is not implemented!'
                )
            if hasattr(m, 'bias') and m.bias is not None:
                init.constant_(m.bias.data, 0.0)

        elif classname.find('BatchNorm2d') != -1 or classname.find(
                'InstanceNorm2d') != -1:
            init.normal_(m.weight.data, 1.0, init_gain)
            init.constant_(m.bias.data, 0.0)

    model.apply(init_func)


def init_net(model, init_type, init_gain, gpu_ids):
    """Function for initializing network weights.

    Args:
        model: A torch.nn.Module to be initialized
        init_type: Name of an initialization method (normal | xavier | kaiming | orthogonal)l
        init_gain: Scaling factor for (normal | xavier | orthogonal).
        gpu_ids: List or int indicating which GPU(s) the network runs on. (e.g., [0, 1, 2], 0)

    Returns:
        An initialized torch.nn.Module instance.
    """
    if len(gpu_ids) > 0:
        assert (torch.cuda.is_available())
        model.to(gpu_ids[0])
        model = nn.DataParallel(model, gpu_ids)
    init_weights(model, init_type, init_gain)
    return model


if __name__ == "__main__":
    d_triad = [[[1, 2, 3.2], [[1, 1], [2, 2], 3.2]],
               [[1, 2, 3.2], [[1, 1], [2, 2], 3.2]],
               [[1, 2, 3.2], [[1, 1], [2, 2], 3.2]],
               [[1, 2, 3.2], [[1, 1], [2, 2], 3.2]]]
    a, b = split_d_triad(d_triad)
    t2m = triad_to_matrix(a)
    print(t2m)
    print(nonzero_user_mean(t2m, -1))
