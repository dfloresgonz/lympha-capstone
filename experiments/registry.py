from models.micn.micn_trainer import train_and_eval_model as train_micn
# from experiments.models.lstm_trainer import build_lstm
# from experiments.models.informer_trainer import build_informer

MODEL_REGISTRY = {
    "MICN": {"train_fn": train_micn},
    # "LSTM": build_lstm,
    # "Informer": build_informer,
}
