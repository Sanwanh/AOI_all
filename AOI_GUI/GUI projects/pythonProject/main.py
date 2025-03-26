import torch

from pl_data_module import PLWaferDataModule
from pl_module import PLWaferModule
import pytorch_lightning as pl

if __name__ == "__main__":
    torch.set_float32_matmul_precision("highest")
    data_module = PLWaferDataModule()
    model = PLWaferModule()

    logger = pl.loggers.TensorBoardLogger("tb_logs", name="wafer")
    best_model_callback = pl.callbacks.ModelCheckpoint(
        monitor="val_acc",  # 監測的指標
        mode="max",  # 監測指標的模式
        dirpath="saves",  # 儲存的路徑
        save_top_k=1,  # 儲存的數量
        filename="{epoch}-{val_acc:.6f}",  # 儲存的檔名
    )

    trainer = pl.Trainer(max_epochs=50, callbacks=[best_model_callback], logger=logger, log_every_n_steps=1)
    trainer.fit(model, data_module)
