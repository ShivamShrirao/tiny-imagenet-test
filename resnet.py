import tensorflow as tf
import tensorflow.keras.layers as layers

from resblock import norm_act, conv_norm, BasicBlock, Bottleneck, AttnBottleneck

# https://github.com/tensorflow/tensorflow/blob/v2.4.1/tensorflow/python/keras/applications/resnet.py


class Resnet():
    def __init__(self, block, filters_per_stack=[64, 128, 256, 512], num_repeats=[3,4,6,3], strides=[2,2,2,1],
                 expansion=4, dp_rate=0, activation=tf.nn.relu, inputs=None, input_shape=(224, 224, 3),
                 num_classes=1000, groups=32, base_width=4, squeeze_reduce=0, self_attn=[False]*4, nheads=8,
                 pos_emb=True, frac_dk=0.5, frac_dv=0.25):
        self.block = block
        self.dp_rate = dp_rate
        self.activation = activation
        self.num_classes = num_classes
        self.expansion = expansion
        self.input_shape = input_shape
        if inputs is None:
            self.inputs = layers.Input(shape=input_shape)
        else:
            self.inputs = inputs

        assert len(filters_per_stack) == len(num_repeats) == len(strides)
        self.filters_per_stack = filters_per_stack
        self.num_repeats = num_repeats
        self.strides = strides
        self.groups = groups
        self.base_width = base_width
        self.squeeze_reduce = squeeze_reduce
        self.self_attn = self_attn
        self.attn_args = {
                            "nheads"      : nheads,
                            "pos_emb"     : pos_emb,
                            "frac_dk"     : frac_dk,
                            "frac_dv"     : frac_dv
                        }

    def get_model(self):
        o = self.build_model()
        self.model = tf.keras.Model(inputs=self.inputs, outputs=o)
        return self.model

    def build_model(self, include_top=True):
        x = self.inputs
        # stem
        x = conv_norm(x, 64, kernel_size=7, strides=2, activation=self.activation, do_norm_act=False)
        x = layers.ZeroPadding2D(padding=((1, 1), (1, 1)), data_format="channels_first")(x)
        x = layers.MaxPool2D(3, strides=2, data_format="channels_first")(x)

        # body
        for i in range(len(self.filters_per_stack)):
            x = self.stack(x, self.block, self.filters_per_stack[i], self.strides[i], repeat=self.num_repeats[i],
                      dp_rate=self.dp_rate, squeeze_reduce=self.squeeze_reduce, self_attn=self.self_attn[i], suffix=i)

        x = norm_act(x)
        if not include_top:
            return x
        else:
            x = layers.GlobalAveragePooling2D(data_format="channels_first")(x)
            x = layers.Dense(self.num_classes)(x)
            x = layers.Softmax(axis=-1)(x)
            return x

    def stack(self, x, block, filters, stride1=2, dp_rate=0, repeat=3, squeeze_reduce=False,
              self_attn=False, suffix=0):
        for i in range(repeat-1):
            x = block(x, filters, strides=1, activation=self.activation, groups=self.groups, base_width=self.base_width,
                      expansion=self.expansion, dp_rate=dp_rate, squeeze_reduce=squeeze_reduce,
                      suffix=f"{suffix}_block{i}", self_attn=self_attn, **self.attn_args)
        i+= 1
        x = block(x, filters, strides=stride1, activation=self.activation, groups=self.groups, base_width=self.base_width,
                  expansion=self.expansion, dp_rate=dp_rate, squeeze_reduce=squeeze_reduce,
                  suffix=f"{suffix}_block{i}", self_attn=self_attn, **self.attn_args)
        
        return x


def Resnet18(inputs=None,
             input_shape=(3,224,224),
             num_classes=1000,
             dp_rate=0,
             activation=tf.nn.relu,
             block=BasicBlock):

    return Resnet(block, num_repeats=[2,2,2,2], inputs=inputs, input_shape=input_shape, num_classes=num_classes,
                  dp_rate=dp_rate, activation=activation)

def Resnet34(inputs=None,
             input_shape=(3,224,224),
             num_classes=1000,
             dp_rate=0,
             activation=tf.nn.relu,
             block=BasicBlock,
             **kwargs):

    return Resnet(block, num_repeats=[3,4,6,3], inputs=inputs, input_shape=input_shape, num_classes=num_classes,
                  dp_rate=dp_rate, activation=activation, **kwargs)

def Resnet50(inputs=None,
             input_shape=(3,224,224),
             num_classes=1000,
             dp_rate=0,
             activation=tf.nn.relu,
             block=Bottleneck,
             **kwargs):

    return Resnet(block, num_repeats=[3,4,6,3], inputs=inputs, input_shape=input_shape, num_classes=num_classes,
                  dp_rate=dp_rate, activation=activation, **kwargs)

def Resnet101(inputs=None,
             input_shape=(3,224,224),
             num_classes=1000,
             dp_rate=0,
             activation=tf.nn.relu,
             block=Bottleneck,
             **kwargs):

    return Resnet(block, num_repeats=[3,4,23,3], inputs=inputs, input_shape=input_shape, num_classes=num_classes,
                  dp_rate=dp_rate, activation=activation, **kwargs)

def Resnext50_32x4d(inputs=None,
                    input_shape=(3,224,224),
                    num_classes=1000,
                    dp_rate=0,
                    activation=tf.nn.relu,
                    block=Bottleneck,
                    **kwargs):

    return Resnet(block, num_repeats=[3,4,6,3], inputs=inputs, input_shape=input_shape, num_classes=num_classes,
                  dp_rate=dp_rate, activation=activation, groups=32, base_width=4, **kwargs)