import pandas as pd
# from sklearn.cluster import KMeans
# from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
from sklearn.preprocessing import scale
from sklearn.linear_model import LogisticRegression
from multiprocessing import Pool, Lock
import numpy as np 
import os
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-c", "--centers", help="The file containing center files.")
parser.add_argument("-s", "--sequences", help="The file containing sequences")
parser.add_argument("-o", "--outdir", help="The directory to hold output.")
parser.add_argument("-top", "--top", help="Analyze only top", action="store_true")
parser.add_argument("-bottom", "--bottom", help="Analyze only bottom", action="store_true")
parser.add_argument("-a", "--all", help="Don't use a 50-50 distribution of true and false examples.", action="store_true")
args = parser.parse_args()
# finish

def run(radius=100):
    print("run  " + str(radius))

    # Max radius in the dataset
    mr = len(sequences.iloc[0]) // 2

    # Sequences to work with Xz
    X = sequences.iloc[:,mr-radius:mr+radius+1]
    X = scale(X)

    y = centers["Fold Change"].map(lambda x: 1 if x > 10 else 0).values
    # classifications = knn(r_seq, is_peak, k)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    lg = LogisticRegression(max_iter=1000)
    lg.fit(X_train, y_train)

    y_scores = lg.predict_proba(X_test)
    fpr, tpr, threshold = roc_curve(y_test, y_scores[:,1])
    roc_auc = auc(fpr, tpr)

    # lock.acquire()
    plt.plot(fpr, tpr, label="r=%d (AUC=%0.2f)" % (radius, roc_auc))

    # plt.cla()
    # plt.close("all")
    # lock.release()

def wrapper(args):
    run(*args)

def init(l, s, c):
    global lock, sequences, centers
    lock = l
    sequences = s
    centers = c

# ========== Main ==========
if __name__ == "__main__":
    # Prepare necessary resources.
    s = pd.read_csv(args.sequences)
    c = pd.read_csv(args.centers)
    l = Lock()

    if args.top:
        strand = c["IPD Top Ratio"] > c["IPD Bottom Ratio"]
    elif args.bottom:
        strand = c["IPD Top Ratio"] < c["IPD Bottom Ratio"]
    else:
        strand = c["IPD Top Ratio"] == c["IPD Top Ratio"] #always true

    if not args.all:
        # Create 50-50 distribution of fp and tp
        n_pos = c[(c["Fold Change"] > 10) & strand].shape[0]
        neg = c[(c["Fold Change"] <= 10) & strand].sample(n=n_pos, random_state=0)
        to_drop = c.isin(pd.concat([neg, c[(c["Fold Change"] > 10) & strand]])).iloc[:,0]
        c = c[to_drop]
        s = s[to_drop]
        # print(n_pos)
    print(len(c))

    # Prepare job parameters.
    params = []
    
    # for r in [5]:
    for r in [100, 50, 25, 20, 15, 10, 5]:
        # Different radii
        params.append((r,))

    # Create pool
    # # pool = Pool(os.cpu_count(), initializer=init, initargs=(l, s, c))
    # pool = Pool(1, initializer=init, initargs=(l, s, c))

    # # Run
    # pool.map(wrapper, params)
    # pool.close()
    # pool.join()

    init(l, s, c)
    for param in params:
        wrapper(param)
    
    plt.legend(loc='lower right')
    plt.plot([0, 1], [0, 1], 'r--')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel("True Positive Rate")
    plt.xlabel("False Positive Rate")
    strand = ", Top Strand" if args.top else (", Bottom Strand" if args.bottom else "")
    plt.title("Logistic Regression ROC Curve%s" % (strand))

    o = args.outdir
    o += "lg_roc"
    if args.top:
        o += "_top"
    elif args.bottom:
        o += "_bottom"
    if args.all:
        o += "_all"
    # o +="_lbfgs"
    o += ".png"

    plt.savefig(o , dpi=600)