
import click
import numpy as np
import pandas as pd
import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)

def next_batch(data, batch_size, i, NN):
    ''' Helper function to get a batch from the data
    '''
    indx = (batch_size * i) % NN
    if (batch_size + indx) > NN:
        indx = 1

    return data.iloc[indx:indx + batch_size]

## Model ##
@click.command()
@click.argument('input_file')
@click.option('--obs_col', default='obs')
@click.option('--var_col', default='variable')
@click.option('--val_col', default='value')
@click.option('--batch_size', default=25)
@click.option('--num_iter', default=2000)
@click.option('--learning_rate', default=0.01)
@click.option('--inner_iter', default=5)
@click.option('--report_every', default=100)
def main(input_file, obs_col, var_col, val_col, batch_size, num_iter,
         learning_rate, inner_iter, report_every):
    ## Load data ##
    data = pd.read_csv(input_file, index_col=0)

    G = data[var_col].unique().shape[0]
    S = data[obs_col].unique().shape[0]

    tf.logging.info('Shuffling...')
    data = data.sample(frac=1)
    NN = data.shape[0]

    N = 2  # Latent space dimensionality

    W = tf.Variable(np.random.randn(G, N), name='weights')
    x = tf.Variable(np.random.randn(N, S), name='PCs')

    sample_idx = tf.placeholder(tf.int32, shape=[None])
    variable_idx = tf.placeholder(tf.int32, shape=[None])
    y_ = tf.placeholder(tf.float64, shape=[None])

    W_ = tf.gather(W, variable_idx)
    x_ = tf.gather(tf.matrix_transpose(x), sample_idx)
    y_hat = tf.reduce_sum(W_ * x_, 1)

    cost = tf.nn.l2_loss(y_ - y_hat) / batch_size

    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)

    init = tf.global_variables_initializer()

    costs = np.zeros(num_iter)

    tf.logging.info('Training')
    with tf.Session() as sess:
        sess.run(init)

        for i in range(num_iter):
            batch = next_batch(data, batch_size, i, NN)
            feed_dict = {sample_idx: batch[obs_col],
                            variable_idx: batch[var_col],
                            y_: batch[val_col]}

            for j in range(inner_iter):
                sess.run(optimizer, feed_dict=feed_dict)

            c = sess.run(cost, feed_dict=feed_dict)
            costs[i] = c

            if not i % report_every:
                tf.logging.info('Iter: {}, Cost: {}'.format(i, c))
        
        X_result = sess.run(x)

    import matplotlib.pyplot as plt

    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.top'] = False

    plt.figure(figsize=(8, 4))
    plt.subplot(1, 2, 1)
    alpha = 1. if S < 1000 else 0.33
    plt.scatter(X_result[0], X_result[1], s=10, alpha=alpha, c='k')
    plt.xlabel('PC1')
    plt.ylabel('PC2')

    plt.subplot(1, 2, 2)

    plt.plot(costs, c='k')
    plt.xlabel('Iteration')
    plt.ylabel('Cost')

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
