import sys
import numpy as np
import tensorflow as tf
import time
import pandas
import sklearn.svm as svm
from termcolor import colored

sys.path.append('code')

from model import Model
from options import Options
from fair_networks_training import FairNetworksTraining



def print_stats(session, model, dataset):
    print("Learning rate:")
    print(session.run(model.optimizer._learning_rate_tensor))

    train_xs, train_ys, train_s = dataset.train_all_data()
    test_xs, test_ys, test_s = dataset.test_all_data()

    train_feed = {model.x: train_xs, model.y: train_ys, model.s: train_s}
    test_feed = {model.x: test_xs, model.y: test_ys, model.s: test_s}


    print("loss and accuracy:")
    model.print_loss_and_accuracy(session, train_feed_dict = train_feed, test_feed_dict = test_feed)

    print(colored("\nConfusion matrix -- Train:", attrs=['bold']))
    model.print_confusion_matrix(session, feed_dict = train_feed)

    print(colored("\nConfusion matrix -- Test:", attrs=['bold']))
    model.print_confusion_matrix(session, feed_dict = test_feed)

def print_processed_data(session, model, dataset):
    train_xs, train_ys, train_s = dataset.train_all_data()
    test_xs, test_ys, test_s = dataset.test_all_data()

    model_data_representation = session.run(model.model_last_hidden_layer, feed_dict={model.x:train_xs, model.y:train_ys, model.s:train_s})

    result = np.hstack((model_data_representation, train_s, train_ys))
    h_header = ["h_"+str(index) for index in range(len(model_data_representation[0]))]
    s_header = ["s_"+str(index) for index in range(len(train_s[0]))]
    y_header = ["y_"+str(index) for index in range(len(train_ys[0]))]

    print(colored("Saving data representations onto %s" % opts.eval_data_path, "green"))
    pandas.DataFrame(result, columns=h_header + s_header + y_header).to_csv(opts.eval_data_path, index=False)



# --------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------

opts = Options(sys.argv)
tf.set_random_seed(opts.random_seed)

print(colored("Initialized system based on config:", "green"))
opts.print_config()

print(colored("Loaded dataset %s" % opts.dataset.name(), "green"))
opts.dataset.print_stats()

optimizer = tf.train.AdagradOptimizer(1.0)
model = Model(opts, optimizer)

session = tf.Session()
saver = tf.train.Saver()
writer = tf.summary.FileWriter(logdir=opts.log_fname())

if tf.train.checkpoint_exists(opts.input_fname()):
    model_to_resume = opts.input_fname()

    print(colored("Restoring model: %s" % (model_to_resume), 'yellow'))
    saver.restore(session, model_to_resume)

    graph_fairness_importance = session.run(tf.get_default_graph().get_tensor_by_name("fairness_importance:0"))

    if graph_fairness_importance != opts.fairness_importance:
        print(colored("Warning:", "yellow") +
                "Fairness importance changed by the options, but it is part of the model.")
        exit(1)
else:
    print(colored("Initializing a new model", 'yellow'))
    init = tf.global_variables_initializer()
    session.run(init)
    writer.add_graph(session.graph)


if opts.eval_stats:
    print_stats(session, model, opts.dataset)
elif opts.eval_data_path != None:
    print_processed_data(session, model, opts.dataset)
else:
    fnt = FairNetworksTraining(opts, session, model, saver, writer)
    fnt.training_loop()



