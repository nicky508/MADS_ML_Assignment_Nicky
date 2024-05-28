from pathlib import Path
from typing import Dict

import plotly.express as px

import ray
import torch
from filelock import FileLock
from loguru import logger
from mltrainer import ReportTypes, Trainer, TrainerSettings, metrics, rnn_models
from mltrainer.preprocessors import PaddedPreprocessor
from ray import tune
from ray.tune import CLIReporter
from ray.tune.schedulers.hb_bohb import HyperBandForBOHB
from ray.tune.search.bohb import TuneBOHB

from ray.tune import ExperimentAnalysis
import ray
ray.init(ignore_reinit_error=True)

tune_dir = Path("MADS_ML_Assignment_Nicky/models/ray").resolve()
# print(tune_dir.exists())

tunelogs = [d for d in tune_dir.iterdir()]
tunelogs.sort()
latest = tunelogs[-1]

analysis = ExperimentAnalysis(latest)

# analysis.results_df.columns


plot = analysis.results_df
select = ["Accuracy", "config/hidden_size", "config/dropout", "config/num_layers"]
p = plot[select].reset_index().dropna()

p.sort_values("Accuracy", inplace=True)

fig = px.parallel_coordinates(p, color="Accuracy")
fig.write_html('test.html')