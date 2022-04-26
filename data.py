import os
import random
from copy import deepcopy
from functools import wraps

import numpy as np
import pandas as pd
import torch
from scipy.sparse.construct import rand
from sklearn.metrics.pairwise import cosine_similarity
from torch.utils.data import Dataset
from tqdm import tqdm

from const import *
from utils.decorator import cache4method
from utils.preprocess import l2_norm, min_max_scaler, z_score


class ToTorchDataset(Dataset):
    """将一个三元组转成Torch Dataset的形式
    """

    def __init__(self, triad) -> None:
        super().__init__()
        self.triad = triad
        self.user_tensor = torch.LongTensor([i[0] for i in triad])
        self.service_tensor = torch.LongTensor([i[1] for i in triad])
        self.target_tensor = torch.FloatTensor([i[2] for i in triad])

    def __len__(self):
        return len(self.triad)

    def __getitem__(self, index):
        return self.user_tensor[index], self.service_tensor[
            index], self.target_tensor[index]


class DatasetBase(object):
    """
    指定要使用的数据集
    rt: rtMatrix
    tp: tpMatrix
    user: userlist
    service: wslist
    """

    def __init__(self, type_) -> None:
        super().__init__()

        self.type = type_
        assert self.type in ["rt", "tp", "user", "service"], f"类型不符，请在{['rt', 'tp', 'user', 'service']}中选择"

    def get_row_data(self):
        if self.type == "rt":
            data = np.loadtxt(RT_MATRIX_DIR)
        elif self.type == "tp":
            data = np.loadtxt(TP_MATRIX_DIR)
        elif self.type == "user":
            data = pd.read_csv(USER_DIR, sep="\t")
        elif self.type == "service":
            data = pd.read_csv(WS_DIR, sep="\t")
        return data


class InfoDataset(DatasetBase):
    """用户和服务的详细描述数据
    """

    def __init__(self, type_, enabled_columns: list) -> None:
        self.type = type_
        super().__init__(type_)
        assert self.type in ["user",
                             "service"], f"类型不符，请在{['user', 'service']}中选择"
        self.enabled_columns = enabled_columns
        self.info_data = self.get_row_data()
        self._fit()

    @property
    def _is_available_columns(self):
        return set(self.enabled_columns).issubset(
            set(self.info_data.columns.tolist()))

    def _fit(self):
        assert self._is_available_columns == True, f"{self.enabled_columns} is not a subset of {self.info_data.columns().tolist()}"
        self.feature2idx = {}  # 为某一个特征所有可能的值编号
        self.feature2num = {}  #
        for column in tqdm(self.enabled_columns, desc="Preparing..."):
            vc = self.info_data[column].value_counts(dropna=False)
            self.feature2idx[column] = {
                k: idx
                for idx, (k, v) in enumerate(vc.to_dict().items())
            }
            self.feature2num[column] = len(vc)

    @property
    def embedding_nums(self):
        return [v for k, v in self.feature2num.items()]

    @cache4method
    def query(self, id_):
        """根据uid或者iid，获得columns的index
        """
        row = self.info_data.iloc[id_, :]
        r = []
        for column in self.enabled_columns:
            idx = self.feature2idx[column][row[column]]
            r.append(idx)
        return r


class MatrixDataset():
    def __init__(self) -> None:
        super().__init__()
        self.rtMatrix = np.loadtxt(RT_MATRIX_DIR)
        self.tpMatrix = np.loadtxt(TP_MATRIX_DIR)
        self.row_num, self.col_num = self.rtMatrix.shape

    # def _get_row_data(self):
    #     data = super().get_row_data()
    #     if isinstance(data, pd.DataFrame):
    #         data = data.to_numpy()
    #     self.row_n, self.col_n = data.shape
    #     return data

    def get_triad(self, nan_symbol=-1):
        """生成四元组(uid,iid,rt,tp)

        Args:
            nan_symbol (int, optional): 数据集中用于表示数据缺失的值. Defaults to -1.

        Returns:
            list[list]: (uid,iid,rate)
        """
        triad_data = []
        row_data_rt = deepcopy(self.rtMatrix)
        row_data_tp = deepcopy(self.tpMatrix)

        row_data_rt[row_data_rt == nan_symbol] = 0
        row_data_tp[row_data_tp == nan_symbol] = 0
        non_zero_index_tuple = np.nonzero(row_data_rt)

        for uid, iid in zip(non_zero_index_tuple[0], non_zero_index_tuple[1]):
            if row_data_tp[uid, iid] != 0:
                triad_data.append([uid, iid, row_data_rt[uid, iid], row_data_tp[uid, iid]])
        triad_data = np.array(triad_data)
        print("triad_data size:", triad_data.shape)
        return triad_data

    def split_train_test(self,
                         density,
                         nan_symbol=-1,
                         shuffle=True,
                         normalize_type=None):
        triad_data = self.get_triad(nan_symbol)

        if shuffle:
            np.random.shuffle(triad_data)

        train_n = int(self.row_num * self.col_num * density)  # 训练集数量
        train_data, test_data = triad_data[:train_n], triad_data[train_n:]

        return train_data, test_data


def normalization(data):
    min_ = np.min(data)
    max_ = np.max(data)
    range_ = max_ - min_
    return (data - min_) / range_


if __name__ == "__main__":
    # md = MatrixDataset("rt")
    # data = md.get_triad()
    # print("random shuffle之前")
    # print(data[:5])
    # print("random shuffle之后")
    # np.random.shuffle(data)
    # print(data[:5])
    ifd = InfoDataset("user", ["[User ID]"])
    print(ifd.feature2idx)
