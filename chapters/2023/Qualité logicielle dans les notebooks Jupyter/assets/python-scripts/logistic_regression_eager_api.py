#!/usr/bin/env python
# coding: utf-8

# # Logistic Regression with Eager API
# 
# A logistic regression implemented using TensorFlow's Eager API.
# 
# - Author: Aymeric Damien
# - Project: https://github.com/aymericdamien/TensorFlow-Examples/

# ## MNIST Dataset Overview
# 
# This example is using MNIST handwritten digits. The dataset contains 60,000 examples for training and 10,000 examples for testing. The digits have been size-normalized and centered in a fixed-size image (28x28 pixels) with values from 0 to 1. For simplicity, each image has been flattened and converted to a 1-D numpy array of 784 features (28*28).
# 
# ![MNIST Dataset](http://neuralnetworksanddeeplearning.com/images/mnist_100_digits.png)
# 
# More info: http://yann.lecun.com/exdb/mnist/

# In[1]:


from __future__ import absolute_import, division, print_function

import tensorflow as tf

# In[2]:


# Set Eager API
tf.enable_eager_execution()
tfe = tf.contrib.eager

# In[3]:


# Import MNIST data
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets("/tmp/data/", one_hot=False)

# In[4]:


# Parameters
learning_rate = 0.1
batch_size = 128
num_steps = 1000
display_step = 100

# In[5]:


# Iterator for the dataset
dataset = tf.data.Dataset.from_tensor_slices(
    (mnist.train.images, mnist.train.labels))
dataset = dataset.repeat().batch(batch_size).prefetch(batch_size)
dataset_iter = tfe.Iterator(dataset)

# In[6]:


# Variables
W = tfe.Variable(tf.zeros([784, 10]), name='weights')
b = tfe.Variable(tf.zeros([10]), name='bias')

# Logistic regression (Wx + b)
def logistic_regression(inputs):
    return tf.matmul(inputs, W) + b

# Cross-Entropy loss function
def loss_fn(inference_fn, inputs, labels):
    # Using sparse_softmax cross entropy
    return tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
        logits=inference_fn(inputs), labels=labels))

# Calculate accuracy
def accuracy_fn(inference_fn, inputs, labels):
    prediction = tf.nn.softmax(inference_fn(inputs))
    correct_pred = tf.equal(tf.argmax(prediction, 1), labels)
    return tf.reduce_mean(tf.cast(correct_pred, tf.float32))

# In[7]:


# SGD Optimizer
optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)

# Compute gradients
grad = tfe.implicit_gradients(loss_fn)

# In[8]:


# Training
average_loss = 0.
average_acc = 0.
for step in range(num_steps):

    # Iterate through the dataset
    d = dataset_iter.next()

    # Images
    x_batch = d[0]
    # Labels
    y_batch = tf.cast(d[1], dtype=tf.int64)

    # Compute the batch loss
    batch_loss = loss_fn(logistic_regression, x_batch, y_batch)
    average_loss += batch_loss
    # Compute the batch accuracy
    batch_accuracy = accuracy_fn(logistic_regression, x_batch, y_batch)
    average_acc += batch_accuracy

    if step == 0:
        # Display the initial cost, before optimizing
        print("Initial loss= {:.9f}".format(average_loss))

    # Update the variables following gradients info
    optimizer.apply_gradients(grad(logistic_regression, x_batch, y_batch))

    # Display info
    if (step + 1) % display_step == 0 or step == 0:
        if step > 0:
            average_loss /= display_step
            average_acc /= display_step
        print("Step:", '%04d' % (step + 1), " loss=",
              "{:.9f}".format(average_loss), " accuracy=",
              "{:.4f}".format(average_acc))
        average_loss = 0.
        average_acc = 0.

# In[9]:


# Evaluate model on the test image set
testX = mnist.test.images
testY = mnist.test.labels

test_acc = accuracy_fn(logistic_regression, testX, testY)
print("Testset Accuracy: {:.4f}".format(test_acc))
