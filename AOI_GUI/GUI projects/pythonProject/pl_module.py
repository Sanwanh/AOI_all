import pytorch_lightning as pl
from model import WaferModel
from torch import optim, nn


class PLWaferModule(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = WaferModel()
        self.loss = nn.CrossEntropyLoss()

    def configure_optimizers(self):
        return optim.Adam(self.parameters())

    def forward(self, x):
        return self.model(x)

    def __step(self, batch):
        x, y = batch
        y_hat = self(x)
        loss = self.loss(y_hat, y)
        acc = (y_hat.argmax(1) == y.argmax(1)).float().mean()

        return loss, acc

    def training_step(self, batch, batch_idx):
        loss, acc = self.__step(batch)
        self.log('train_loss', loss, prog_bar=True)
        self.log('train_acc', acc, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        loss, acc = self.__step(batch)
        self.log('val_loss', loss, prog_bar=True)
        self.log('val_acc', acc, prog_bar=True)
