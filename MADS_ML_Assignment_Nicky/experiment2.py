import mlflow
from datetime import datetime
from pathlib import Path
import gin
import numpy as np
import torch
import torch.nn as nn
from typing import Dict
from typing import List
from torch.nn.utils.rnn import pad_sequence
from mltrainer import rnn_models, Trainer
from torch import optim
import pathlib
from mltrainer import TrainerSettings, ReportTypes
from mltrainer.metrics import Accuracy
from torchsummary import summary
from loguru import logger

from mads_datasets import datatools
from mads_datasets import DatasetFactoryProvider, DatasetType
from mltrainer.preprocessors import PaddedPreprocessor

ginModelPath = Path(__file__).parent.resolve() / "gestures_lstm.gin"

#note to self: assignment link between size hidden_state and number of layers

@gin.configurable
class LstmModel(nn.Module):
    def __init__(
        self,
        lL,
        dO,
        config: Dict
    ) -> None:
        super().__init__()
        config["num_layers"] = lL
        config["dropout"] = dO
        
        self.convolutions = nn.Sequential(
            nn.Conv1d(in_channels=3, out_channels=config["input_size"], kernel_size=3),
            nn.BatchNorm1d(config["input_size"]),
            nn.ReLU(),
            nn.Conv1d(in_channels=config["input_size"], out_channels=config["input_size"], kernel_size=3),
            nn.BatchNorm1d(config["input_size"]),
            nn.ReLU(),
            nn.Conv1d(in_channels=config["input_size"], out_channels=config["input_size"], kernel_size=3),
            nn.BatchNorm1d(config["input_size"]),
            nn.ReLU(),
            nn.Dropout(p=config["dropout"]),
            nn.MaxPool2d(kernel_size=2),
        )
        
        self.lstm = nn.LSTM(    
                input_size=int(config["input_size"]/2),
                hidden_size=config["hidden_size"],
                dropout=dO,
                batch_first=True,
                num_layers=lL
        )
        
        self.linear = nn.Linear(config["hidden_size"], config["output_size"])
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.permute(0, 2, 1)
        x = self.convolutions(x)
        x = x.permute(0, 2, 1)
        
        x, _ = self.lstm(x)
        last_step = x[:, -1, :]
        yhat = self.linear(last_step)
        return yhat

def getData():
    preprocessor = PaddedPreprocessor()

    gesturesdatasetfactory = DatasetFactoryProvider.create_factory(DatasetType.GESTURES)
    streamers = gesturesdatasetfactory.create_datastreamer(batchsize=32, preprocessor=preprocessor)
    train = streamers["train"]
    valid = streamers["valid"]

    trainstreamer = train.stream()
    validstreamer = valid.stream()
    return train, valid, trainstreamer, validstreamer
    
def getSettings(train, valid):
    accuracy = Accuracy()
    settings = TrainerSettings(
        epochs=10,
        metrics=[accuracy],
        logdir=Path("gestures"),
        train_steps=len(train),
        valid_steps=len(valid),
        reporttypes=[ReportTypes.GIN, ReportTypes.TENSORBOARD, ReportTypes.MLFLOW],
        scheduler_kwargs={"factor": 0.5, "patience": 2},
        earlystop_kwargs={"patience": 5},
    )    
    return settings

def getTrainer(settings, trainstreamer, validstreamer, model):
    loss_fn = torch.nn.CrossEntropyLoss()
    trainer = Trainer(
            model=model,
            settings=settings,
            loss_fn=loss_fn,
            optimizer=optim.Adam,
            traindataloader=trainstreamer,
            validdataloader=validstreamer,
            scheduler=optim.lr_scheduler.ReduceLROnPlateau
        )
    return trainer

def trainModel(trainer, model, lL, dO):
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("experiment 2b: Lstm Layers / Dropout ")
    modeldir = Path("../../models/gestures/").resolve()
    if not modeldir.exists():
        modeldir.mkdir(parents=True)

    with mlflow.start_run():
        mlflow.set_tag("model", "LSTM")
        mlflow.set_tag("dev", "nicky")
        mlflow.set_tag("Lstm layers", lL)
        mlflow.set_tag("Dropout", dO)
        mlflow.log_params(gin.get_bindings("LstmModel"))

        tag = datetime.now().strftime("%Y%m%d-%H%M")
        modelpath = modeldir / (tag + "model.pt")
        torch.save(model, modelpath)
        trainer.loop()
        
def main(lL, dO):
    train, valid, trainstreamer, validstreamer = getData()
    settings = getSettings(train, valid)
    gin.parse_config_file(ginModelPath)
    model = LstmModel(lL, dO)
    trainer = getTrainer(settings, trainstreamer, validstreamer, model)

    trainModel(trainer, model, lL, dO)

    
if __name__ == "__main__":
    #main(1, 4, 9*0.1)
    # for cL in range(2, 4):
    #     for lL in range(1, 5):
    #         for dO in range(1, 10):
    #             main(cL, lL, dO*0.1)
    
    for lL in range(1, 6):
        for dO in range(1, 10):
            main(lL, dO*0.1)