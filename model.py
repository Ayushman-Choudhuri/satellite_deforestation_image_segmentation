import tensorflow as tf

from tensorflow.keras.layers import Conv2D, BatchNormalization, Activation,\
                                    MaxPool2D, UpSampling2D, concatenate,\
                                    Input, Conv2DTranspose, MaxPooling2D,\
                                    Dropout, BatchNormalization
from tensorflow.keras.models import Model

import matplotlib.pyplot as plt
import numpy as np
from numba import cuda
from PIL import Image

config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.compat.v1.Session(config=config)

from utils import center_crop
import yaml
config = yaml.safe_load(open("config.yaml"))
pretrained_model_path = config['pretrained_model']
image = config['image']
def conv2d_block(input_tensor, n_filters, kernel_size=3, batchnorm=True, sublayers=2):
    '''In case batchnorm=False "if" statement will be skipped and in amount of "sublayers" convolutional layers will be created.'''
    for idx in range(sublayers):
        conv = Conv2D(filters=n_filters, kernel_size=(kernel_size, kernel_size),
                   kernel_initializer="he_normal", padding="same")(input_tensor if idx==0 else conv)
        if batchnorm:
            normalized = BatchNormalization()(conv)
        conv = Activation("relu")(conv) # normalized to conv
    return conv

def conv2d_transpose_block(input_tensor, concatenate_tensor, n_filters, kernel_size=3, strides=2, transpose=False):
    if transpose:
        conv = Conv2DTranspose(n_filters, (kernel_size, kernel_size),
                               strides=(strides, strides), padding='same')(input_tensor)
    else:
        conv = Conv2D(n_filters, (kernel_size, kernel_size), activation = 'relu', padding = 'same',
                      kernel_initializer = 'he_normal')(UpSampling2D(size=(kernel_size, kernel_size))(input_tensor))
    conv = Activation("relu")(conv)
    concatenation = concatenate([conv, concatenate_tensor])
    return concatenation

def build_unet(input_shape=(512, 512, 3), filters=[16, 32, 64, 128, 256], batchnorm=True, transpose=False, dropout_flag=False):  # dropout_rate=0.2

    conv_dict = dict()
    inputs = Input(input_shape)
    dropout_rate = 0.5

    for idx, n_filters in enumerate(filters[:-1]):
        conv = conv2d_block(inputs if n_filters==filters[0] else max_pool, # Change max_pool to dropout
                            n_filters=n_filters, kernel_size=3,
                            batchnorm=batchnorm)
        max_pool = MaxPooling2D((2, 2))(conv)
        # # Commented dropout
        # if idx > 1 and dropout_flag:
        #     print('[INFO] Dropout down')
        #     dropout = Dropout(dropout_rate)(max_pool)
        # else:
        #     print('[INFO] Dropout down skip')
        #     dropout = max_pool
        # print(f'[INFO] Conv block {idx} created.')
        # # Save layer
        conv_dict[f"conv2d_{idx+1}"] = conv

    # Change max_pool to dropout
    conv_middle = conv2d_block(max_pool, n_filters=filters[-1], kernel_size=3, batchnorm=batchnorm)

    for idx, n_filters in enumerate(reversed(filters[:-1])):
        concatenation = conv2d_transpose_block(conv_middle if idx==0 else conv,
                                               conv_dict[f"conv2d_{len(conv_dict) - idx}"],
                                               n_filters, kernel_size=2, strides=2, transpose=transpose) # kernel_size=2, like in previous
        # Commented Dropout
#         if idx < len(filters) - 3 and dropout_flag:
#             print('[INFO] Dropout up')
#             dropout = Dropout(dropout_rate)(concatenation)
#         else:
#             print('[INFO] Dropout up skip')
#             dropout = concatenation
        conv = conv2d_block(concatenation, n_filters=n_filters, kernel_size=3, # Change concatenation to Dropout
#                             batchnorm = batchnorm if idx not in [len(conv_dict), len(conv_dict) - 1] else False)
                              batchnorm = batchnorm)
        print(f'[INFO] UpConv block {idx} created.')
    outputs = Conv2D(3, (1, 1), activation='softmax')(conv)
    model = Model(inputs=inputs, outputs=outputs)
    return model

def get_prediction(image):

    final_filters = 2048
    model10 = build_unet(input_shape=(1024, 1024, 3),
                         filters=[2 ** i for i in range(5, int(np.log2(final_filters) + 1))], # Amount of filters in U-Net arch.
                         batchnorm=False, transpose=False, dropout_flag=False)

    model10.load_weights(pretrained_model_path)

    image = Image.open(image)

    image = np.asarray(image)
    image = center_crop(image, (1024, 1024))
    image = image[:,:,:3]
    image = image[np.newaxis, ...]
    # plt.imshow(image[0])
    # plt.show()

    prediction = model10.predict(image)

    prediction_class1 = np.copy(prediction[..., 0]) # Forest
    prediction_class2 = np.copy(prediction[..., 1]) # Deforest
    prediction[..., 0] = prediction_class2 # RED - Deforest
    prediction[..., 1] = prediction_class1 # GREEN - Forest
    # plt.imshow(prediction[0])
    # plt.show()

    return prediction[0]

output = get_prediction(image)
plt.imshow(output)
plt.show()

