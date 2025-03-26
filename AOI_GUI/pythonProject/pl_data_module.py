import pytorch_lightning as pl
from dataset import WaferDataset
from torch.utils.data import DataLoader, random_split


class PLWaferDataModule(pl.LightningDataModule):
    def __init__(self, batch_size=16):
        super().__init__()
        self.batch_size = batch_size
        self.wafer_train, self.wafer_val, self.wafer_test = None, None, None

    def setup(self, stage=None):
        if stage == "fit" or stage is None:
            wafer_full = WaferDataset(data_path="data")
            self.wafer_train, self.wafer_val = random_split(wafer_full, [1800, 200])

        if stage == "test" or stage is None:
            self.wafer_test = WaferDataset(data_path="data")

    def train_dataloader(self):
        return DataLoader(self.wafer_train, batch_size=self.batch_size, shuffle=True, num_workers=8, persistent_workers=True)

    def val_dataloader(self):
        return DataLoader(self.wafer_val, batch_size=self.batch_size, num_workers=8, persistent_workers=True)
