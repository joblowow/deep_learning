import numpy as np
import time

import PIL.Image as Image
import matplotlib.pylab as plt

import tensorflow as tf
import tensorflow_hub as hub

IMAGE_SHAPE = (224, 224)

def main():
    batch_size = 32  # the number of training examples utilized in one iteration
    img_height = 224
    img_width = 224
    num_epoch = 100

    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        str('deep_learning/Data'),
        validation_split=0.2,  # Fraction of the training data to be used as validation data.
        subset="training",
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size)

    class_names = np.array(train_ds.class_names)
    print(class_names)
    print(train_ds)

    normalization_layer = tf.keras.layers.experimental.preprocessing.Rescaling(1. / 255)
    train_ds = train_ds.map(lambda x, y: (normalization_layer(x), y))

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)

    for image_batch, labels_batch in train_ds:
        print(image_batch.shape)
        print(labels_batch.shape)
        break

    # Resnet 50
    feature_extractor_model = "https://tfhub.dev/tensorflow/resnet_50/feature_vector/1"  # @param {type:"string"}
    feature_extractor_layer = hub.KerasLayer(
        # trainable = False freezes the variables in feature extractor layer,
        # so that the training only modifies the new classifier layer.
        feature_extractor_model, input_shape=(224, 224, 3), trainable=False)

    # It returns a 1280-length vector for each image:
    feature_batch = feature_extractor_layer(image_batch)
    print(feature_batch.shape)

    # Attach a classification head
    num_classes = len(class_names)

    # Now wrap the hub layer in a tf.keras.Sequential model
    model = tf.keras.Sequential([
        feature_extractor_layer,
        tf.keras.layers.Dense(num_classes)  # add a new classification layer.
    ])

    model.summary()

    predictions = model(image_batch)
    predictions.shape

    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['acc'])

    class CollectBatchStats(tf.keras.callbacks.Callback):
        def __init__(self):
            self.batch_losses = []
            self.batch_acc = []

        def on_train_batch_end(self, batch, logs=None):
            self.batch_losses.append(logs['loss'])
            self.batch_acc.append(logs['acc'])
            self.model.reset_metrics()

    batch_stats_callback = CollectBatchStats()

    history = model.fit(train_ds, epochs=num_epoch,
                        callbacks=[batch_stats_callback])

    plt.figure()
    plt.ylabel("Loss")
    plt.xlabel("Training Steps")
    plt.ylim([0, 2])
    plt.plot(batch_stats_callback.batch_losses)
    plt.savefig('Loss_headless.png')

    plt.figure()
    plt.ylabel("Accuracy")
    plt.xlabel("Training Steps")
    plt.ylim([0, 1])
    plt.plot(batch_stats_callback.batch_acc)
    plt.savefig('Accuracy_headless.png')

    predicted_batch = model.predict(image_batch)
    predicted_id = np.argmax(predicted_batch, axis=-1)
    predicted_label_batch = class_names[predicted_id]

    plt.figure(figsize=(10, 9))
    plt.subplots_adjust(hspace=0.5)
    for n in range(30):
        plt.subplot(6, 5, n + 1)
        plt.imshow(image_batch[n])
        plt.title(predicted_label_batch[n].title())
        plt.axis('off')
    _ = plt.suptitle("Model predictions")
    plt.savefig('predicted_images_headless.png')


if __name__ == "__main__":
    main()
