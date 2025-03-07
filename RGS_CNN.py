import numpy as np
import os
import tensorflow as tf
from tensorflow.keras import mixed_precision

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
os.environ['CUDA_VISIBLE_DEVICES']="0" 

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
  try:
    # Currently, memory growth needs to be the same across GPUs
    for gpu in gpus:
      tf.config.experimental.set_memory_growth(gpu, True)
    logical_gpus = tf.config.experimental.list_logical_devices('GPU')
    print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
  except RuntimeError as e:
    # Memory growth must be set before GPUs have been initialized
    print(e)


base_dir = '/media/tord/T7/Thesis_ssd/MasterThesis3'
os.chdir(base_dir)
from Classes.DataProcessing.LoadData import LoadData
from Classes.DataProcessing.HelperFunctions import HelperFunctions
from Classes.DataProcessing.DataHandler import DataHandler
from Classes.Modeling.RGS import RGS
helper = HelperFunctions()
mixed_precision.set_global_policy('mixed_float16')


load_args = {
    'earth_explo_only' : False,
    'noise_earth_only' : False,
    'noise_not_noise' : True,
    'downsample' : True,
    'upsample' : True,
    'frac_diff' : 1,
    'seed' : 1,
    'subsample_size' : 0.05,
    'balance_non_train_set' : False,
    'use_true_test_set' : False,
    'even_balance' : True
}
loadData = LoadData(**load_args)
train_ds, val_ds, test_ds = loadData.get_datasets()
noise_ds = loadData.noise_ds
handler = DataHandler(loadData)

#- Consider editing the decay_sequences.

"""
hyper_grid = {
    "num_layers" : [1, 2, 3],
    "batch_size" : [64, 128, 256],
    "epochs" : [50, 50, 50, 50, 50, 50, 50, 50, 50],
    "learning_rate" : [0.1, 0.01, 0.01, 0.001, 0.001, 0.0001, 0.0001],
    "optimizer" : ["sgd", "sgd", "sgd", "sgd", "rmsprop", "adam", "rmsprop", "sgd"],
    "num_filters" : np.arange(50, 100, 2),
    "filter_size" : np.arange(50, 130, 3),
    "cnn_activation" : ["tanh", "relu"],
    "dense_activation" : ["relu", "tanh"],
    "padding" : ["same"],
    "use_layerwise_dropout_batchnorm" : [False, True],
    "decay_sequence" : [[1,2,4,4,2,1], [1,4,8,8,4,1], [1,1,1,1,1,1], [1, 2, 4, 6, 8, 10]],
    "dropout_rate" : [0.3, 0.2, 0.1, 0.01, 0.001, 0],
    "l2_r" : [0.01, 0.001, 0.0001],
    "l1_r" : [0.1, 0.01, 0.001, 0.0001],
    "first_dense_units" : np.arange(150,300),
    "second_dense_units" : np.arange(75,300),
    "output_layer_activation" : ["sigmoid"]
}
"""
# Near the parameters of the old best performer
hyper_grid = {
    "num_layers" : [1, 2, 3],
    "batch_size" : [48, 64, 128, 256],
    "epochs" : [50],
    "learning_rate" : [0.01, 0.005, 0.0025, 0.0001],
    "optimizer" : ["sgd", "sgd", "adam"],
    "num_filters" : np.arange(60, 80, 2),
    "filter_size" : np.arange(40, 80, 2),
    "cnn_activation" : ["tanh", "relu"],
    "dense_activation" : ["relu", "tanh"],
    "padding" : ["same"],
    "use_layerwise_dropout_batchnorm" : [True, False],
    "dropout_T_bn_F" : [True, False],
    "growth_sequence" : [[1,2,4,4,2,1], [1,4,8,8,4,1], [1,1,1,1,1,1], [1, 2, 4, 6, 8, 10], [1,8,16,32,64,128], [1,4,8], [1,4,4], [1,8,8], [1,2,2]],
    "dropout_rate" : [0.2, 0.1, 0.01, 0.001, 0],
    "l2_r" : [0.1, 0.01, 0.001, 0.0001, 0],
    "l1_r" : [0.1, 0.01, 0.001, 0.0001, 0],
    "first_dense_units" : np.arange(250,300, 2),
    "second_dense_units" : np.arange(150, 300, 2),
    "output_layer_activation" : ["sigmoid"]
}
"""
hyper_grid = {
    "num_layers" : [1, 2],
    "batch_size" : [64],
    "epochs" : [75],
    "learning_rate" : [0.025],
    "optimizer" : ["sgd"],
    "num_filters" : [68],
    "filter_size" : [42],
    "cnn_activation" : ["relu"],
    "dense_activation" : ["relu"],
    "padding" : ["same"],
    "use_layerwise_dropout_batchnorm" : [True],
    "growth_sequence" : [[1,2,4,4,2,1], [1,4,8,8,4,1], [1,1,1,1,1,1], [1, 2, 4, 6, 8, 10], [1,0.75, 0.50, 0.5, 0.75, 1]],
    "dropout_rate" : [0.001],
    "l2_r" : [0.01],
    "l1_r" : [0.001],
    "first_dense_units" : [286],
    "output_layer_activation" : ["sigmoid"]
}
"""


model_type = "CNN_grow_double"
is_lstm = True
num_channels = 3

use_time_augmentor = True
scaler_name = "normalize"
use_noise_augmentor = True
filter_name = None
band_min = 2.0
band_max = 4.0
highpass_freq = 15

n_picks = 300

use_tensorboard = True
use_liveplots = False
use_custom_callback = True
use_early_stopping = True
start_from_scratch = False
use_reduced_lr = True
log_data = True

shutdown = False

def clear_tensorboard_dir():
        import os
        import shutil
        path = f"{base_dir}/Tensorboard_dir/fit"
        files = os.listdir(path)
        print(files)
        for f in files:
            shutil.rmtree(os.path.join(path,f))
if use_tensorboard:
    clear_tensorboard_dir()

      
randomGridSearch = RGS(loadData, train_ds, val_ds, test_ds, model_type, scaler_name, use_time_augmentor, use_noise_augmentor,
                        filter_name, n_picks, hyper_grid=hyper_grid, use_tensorboard = use_tensorboard, 
                        use_liveplots = use_liveplots, use_custom_callback = use_custom_callback, use_early_stopping = use_early_stopping, 
                        use_reduced_lr = use_reduced_lr, band_min = band_min, band_max = band_max, highpass_freq = highpass_freq, 
                        start_from_scratch = start_from_scratch, is_lstm = is_lstm, log_data = log_data, num_channels = num_channels)
randomGridSearch.fit()

