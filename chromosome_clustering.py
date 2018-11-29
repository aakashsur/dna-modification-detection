import pandas as pd
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import numpy as np 
import os
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()


# The chromosome file to parse
FILE = "l_tarentolae.tsv"

# The directory to store plots
PLOT_DIR = "plots/"
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# Create the pandas file
TABLE = pd.read_table(FILE)



def create_sequences(table, sequence_length, stride, peak_threshold):
    """
    Creates sequences through a sliding window method.

    Args:
        table: The chromosome table whose IPD ratios to create sequences from.
        sequence_length: the length of the sequences to create.
        stride: how much to jump between sequences.
        peak_threshold: The threshold that must be hit for a fold change value
            to be considered a "peak"
    
    Returns:
        sequences: The sequences created from the IPD ratios.
        labels: The labels for each sequence, where 1 is a peak, and 0 o.w.
    """

    # The sequences to visualize
    sequences = []
    # For each sequence, 1 if peak, 0 o.w.
    labels = []
    
    # curr keeps track of current sequence.
    curr = []
    curr_peaks = []
    for index, row in table.iterrows(): 

        # Add to the sequence.
        curr.append(row["IPD Top Ratio"])
        curr_peaks.append(1 if row["Fold Change"] > peak_threshold else 0)
    
        # Make sure we have a sequence of appropriate length
        if len(curr) == sequence_length:
            # Add to our sequences if the stride is followed.
            if index % stride == 0:
                sequences.append(curr.copy())
                labels.append(sum(curr_peaks) == sequence_length)
            # Remove front of sequence
            curr.pop(0)
            curr_peaks.pop(0)

    return sequences, labels

def reduce_dimensions(sequences, red_type):
    """
    Runs dimensionality reduction on the following array of sequences.
    
    Args:
        sequences: The sequences which to run dimensionality reduction on.
        red_type: The name of the type of dimensionality reduction. Must be
            either "pca" or "tsne"

    Returns:
        reduced: The reduced form of the sequences.
    """
    
    reduced = []

    if red_type == "pca":
        pca = PCA()
        reduced = pca.fit_transform(sequences)
    
    if red_type == "tsne":
        tsne = TSNE()
        reduced = tsne.fit_transform(sequences)
    
    return reduced

from threading import Lock
PLOT_LOCK = Lock()
def plot_and_save(dim_red, labels, name):
    """
    Plots and saves the sequences with reduced dimensions.

    Args:
        dim_red: The sequences, after dimensionality reduction.
        labels: For each sequence, specifies if it is a peak
        name: The name of the graph
    """

    # Plot lock, if we are plotting in a parallel manner.
    PLOT_LOCK.acquire()
    # Find max values to normalize:
    # np_2d = np.asarray(dim_red)
    # m_0 = max(abs(np.min(np_2d, axis=0)[0]), np.max(np_2d, axis=0)[0])
    # m_1 = max(abs(np.min(np_2d, axis=0)[1]), np.max(np_2d, axis=0)[1])
        
    # Plot all the normalized values
    for i in range(len(dim_red)):
        peak = labels[i] == 1
        c = 'r' if peak else 'b'
        plt.scatter(dim_red[i, 0], dim_red[i, 1], c=c, s=1)
        
    # Save the plot
    plt.savefig(PLOT_DIR + name + ".png")
    PLOT_LOCK.release()

# For each chromosome, run this:
# for chromosome in table["Chromosome"].unique():
def plot_chromosome(chromosome, sequence_length=10):
    global TABLE
    # Filter out the single LtaP_01 chromosome file
    c = TABLE[TABLE["Chromosome"] == chromosome].dropna()
    
    # ===== Create Sequences ===== 
    sequences, labels = create_sequences(c, sequence_length, 10, 10)
    # ===== Dimensionality Reduction =====
    reduced = reduce_dimensions(sequences, "pca")

    plot_and_save(reduced, labels, chromosome)
    


# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("-c","--chromosome")
# parser.add_argument("-f","--file")
# args = parser.parse_args()

from multiprocessing import Pool
if __name__ == "__main__":
    # pool = Pool(os.cpu_count())
    # pool.map(plot_chromosome, TABLE["Chromosome"].unique())
    plot_chromosome("LtaP_03")
