from __future__ import absolute_import
import bisect
import warnings

import torch
from torch import randperm
from torch._utils import _accumulate
from torch.utils.data import Dataset


class ConcatDataset(Dataset):
    """
    Dataset to concatenate multiple datasets.
    Purpose: useful to assemble different existing datasets, possibly
    large-scale datasets as the concatenation operation is done in an
    on-the-fly manner.

    Arguments:
        datasets (sequence): List of datasets to be concatenated
    """

    @staticmethod
    def cumsum(sequence, real_multiplier):
        r, s = [], 0
        for e in sequence:
            l = len(e)
            if e.real_world:
                l *= real_multiplier
            s += l  # cummulative
            r.append(s)
        return r

    def __init__(self, datasets, real_multiplier=500):
        super(ConcatDataset, self).__init__()
        assert len(datasets) > 0, 'datasets should not be an empty iterable'
        self.datasets = list(datasets)
        self.real_multiplier = real_multiplier
        self.cumulative_sizes = self.cumsum(self.datasets, self.real_multiplier)
        self.max_len = max([_dataset.max_len for _dataset in self.datasets]) # size of vocabulary
        for _dataset in self.datasets:
            _dataset.max_len = self.max_len

    def __len__(self):
        return self.cumulative_sizes[-1]

    def __getitem__(self, idx):
        dataset_idx = bisect.bisect_right(self.cumulative_sizes, idx)
        if dataset_idx == 0:
            sample_idx = idx
        else:
            sample_idx = idx - self.cumulative_sizes[dataset_idx - 1]
        if self.datasets[dataset_idx].real_world:
            return self.datasets[dataset_idx][sample_idx % len(self.datasets[dataset_idx])]
        return self.datasets[dataset_idx][sample_idx]

    @property
    def cummulative_sizes(self):
        warnings.warn("cummulative_sizes attribute is renamed to "
                      "cumulative_sizes", DeprecationWarning, stacklevel=2)
        return self.cumulative_sizes
