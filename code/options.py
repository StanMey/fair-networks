import sys
from bank_marketing_dataset import BankMarketingDataset
from adult_dataset import AdultDataset
from synth_dataset import SynthDataset
import tensorflow as tf
import argparse
import textwrap

class Options:
    def __init__(self):
        # self.num_features = 108   # Adult
        # self.num_features = 51     # Bank

        self.epoch_start = 0
        self.epoch_end = 10000
        self.epochs = range(self.epoch_start, self.epoch_end)
        self.resume_learning = False

        self.epochs_per_save = 1000

        self.parse(sys.argv)

        self.exp_name = "%s_h%s_s%s_y%s" % (self.dataset_name, self.hidden_layers_specs, self.sensible_layers_specs, self.class_layers_specs)



    def parse_epochs(self, epochs_str):
        epochs_spec = epochs_str.split(':')
        if len(epochs_spec) == 1:
            self.epoch_end = int(epochs_spec[0])
            self.epochs = range(self.epoch_start, self.epoch_end)

            return

        start,end = epochs_spec

        if start != '':
            self.epoch_start = int(start)
            self.resume_learning = True

        if end != '':
            self.epoch_end = int(end)

        self.epochs = range(self.epoch_start, self.epoch_end)

    def parse_layers(self, str):
        layers_specs = str.split(':')
        return [(int(hidden_units), tf.nn.sigmoid, tf.truncated_normal_initializer)
               for hidden_units in layers_specs ]

    def parse(self, argv):
        description = """\
        epoch_specs specifies the range of epochs to work with;
        syntax is:  <start>:<end>

        with <start> defaulting to 0 and <end> defaulting to 10000
        giving a single number and omitting the colon will be
        interpreted as :<end>

        examples:
            100:5000  -- epochs from 100 to 5000
            :5000     -- epochs from 0 to 5000
            5000      -- epochs from 0 to 5000
            100:      -- epochs from 100 to 10000
        NOTE: at test time <end> need to be set to the epoch of the
            model to be retrieved.

        *_layers specify the composition of sub networks;
        syntax is: h_1:h_2:...:h_K

        where h_i being the number of hidden units in the i-th layer.

        examples:
             10       -- a single hidden layer with 10 neurons
             10:5:2   -- three hidden layers with 10, 5, and 2 neuron respectively
                            """
        datasets = { 'adult': AdultDataset, 'bank': BankMarketingDataset, 'synth': SynthDataset }
        parser = argparse.ArgumentParser(description=description,formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('dataset', choices=['adult', 'bank', 'synth'], help="dataset to be loaded")
        parser.add_argument('-H', '--hidden-layers', type=str, help='hidden layers specs', required=True)
        parser.add_argument('-S', '--sensible-layers', type=str, help='sensible network specs', required=True)
        parser.add_argument('-Y', '--class-layers', type=str, help='output network specs', required=True)
        parser.add_argument('-y', '--train-y', default=False, action='store_const', const=True, help='optimize the network to predict y variables')
        parser.add_argument('-s', '--train-s', default=False, action='store_const', const=True, help='optimize the network to predict s variables')
        parser.add_argument('-x', '--train-not-s', default=False, action='store_const', const=True, help='optimize the network to "not" predict s variables')
        parser.add_argument('-e', '--eval-stats', default=False, action='store_const', const=True, help='Evaluate all stats and print the result on the console (if set training options will be ignored)')

        parser.add_argument('epoch_specs', help = 'which epochs to be run')
        result = parser.parse_args()

        self.dataset_name = result.dataset
        self.dataset = datasets[self.dataset_name]()
        self.num_features = self.dataset.num_features()

        self.hidden_layers_specs = result.hidden_layers
        self.hidden_layers = self.parse_layers(result.hidden_layers)

        self.sensible_layers_specs = result.sensible_layers
        self.sensible_layers = self.parse_layers(result.sensible_layers)

        self.class_layers_specs = result.class_layers
        self.class_layers = self.parse_layers(result.class_layers)

        print(self.hidden_layers)
        print(self.sensible_layers)
        print(self.class_layers)

        self.parse_epochs(result.epoch_specs)
        self.train_y = result.train_y
        self.train_s = result.train_s
        self.train_not_s = result.train_not_s
        self.eval_stats = result.eval_stats


        return self

    def model_fname(self, epoch):
        return "models/%s-epoch-%d.ckpt" % (self.exp_name, epoch)

    def log_fname(self):
        return 'logdir/log_%s' % self.exp_name

    def save_at_epoch(self, epoch):
        early_saves = epoch < 100000 and epoch % 100 == 0
        normal_saves = epoch % self.epochs_per_save == 0

        return early_saves or normal_saves
