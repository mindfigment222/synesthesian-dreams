import tensorflow as tf
import time
import os
from tqdm import tqdm
import numpy as np

from discriminator import make_discriminator_model
from generator import make_generator_model
from losses import generator_loss, discriminator_loss
from utils import generate_and_save_images

# Training loop
EPOCHS = 50
noise_dim = 100
num_examples_to_generate = 16

# We will reuse this seed overtime (so it's easier)
# to visualize progress in the animated GIF
seed = tf.random.normal([num_examples_to_generate, noise_dim])

generator = make_generator_model()
discriminator = make_discriminator_model()

generator_optimizer = tf.keras.optimizers.Adam(1e-4)
discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)

checkpoint_dir = './training_checkpoints'
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
checkpoint = tf.train.Checkpoint(generator_optimizer=generator_optimizer,
                                 discriminator_optimizer=discriminator_optimizer,
                                 generator=generator,
                                 discriminator=discriminator)


# Notice the use of `tf function`
# This annotation causes the function to be "compiled"
@tf.function
def train_step(images):
    batch_size = images.shape[0]
    noise = tf.random.normal([batch_size, noise_dim])

    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        generated_images = generator(noise, training=True)

        real_output = discriminator(images, training=True)
        fake_output = discriminator(generated_images, training=True)

        gen_loss = generator_loss(fake_output)
        disc_loss = discriminator_loss(real_output, fake_output)

    gradients_of_generator = gen_tape.gradient(gen_loss, generator.trainable_variables)
    gradients_of_discriminator = disc_tape.gradient(disc_loss, discriminator.trainable_variables)

    generator_optimizer.apply_gradients(zip(gradients_of_generator, generator.trainable_variables))
    discriminator_optimizer.apply_gradients(zip(gradients_of_discriminator, discriminator.trainable_variables))

    return gen_loss, disc_loss


def train(dataset, epochs, dataset_size, batch_size):
    for epoch in range(epochs):
        start = time.time()

        gen_loss_sum = 0.0
        disc_loss_sum = 0.0
        batch_num = int(np.ceil(dataset_size / batch_size))

        with tqdm(total=batch_num, desc="Epoch {}: ".format(epoch + 1)) as pbar:

            for image_batch in dataset:
                # print('IMAGE BATCH SHAPE {}'.format(image_batch.shape))
                gen_loss, disc_loss = train_step(image_batch)
                gen_loss_sum += gen_loss
                disc_loss_sum += disc_loss

                pbar.update(1)

            # Produce images for the GIF as we go
            generate_and_save_images(generator, epoch + 1, seed)

            # Save the model every 15 epochs
            if (epoch + 1) % 1 == 0:
                checkpoint.save(file_prefix = checkpoint_prefix)
                print("Saving model...")
                # ************************************* #
                tf.saved_model.save(generator, "./models/1/")

            print("Time for epoch {} is {} sec".format(epoch + 1, time.time() - start))
            print("Generator loss is {:4f}".format(gen_loss_sum / batch_num))
            print("Discriminator loss is {:4f}".format(disc_loss / batch_num))

    # Generate after the final epoch
    generate_and_save_images(generator, epochs, seed)