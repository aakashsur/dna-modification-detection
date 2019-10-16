# Ivan Montero

# ========== Imports ==========

# Boilerplate
import pandas as pd
from multiprocessing import Pool, Lock
import numpy as np 
import os
import math

# SciKit Learn
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
from scipy import interp
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import scale
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()

# Keras
from keras.models import Sequential
from keras.layers import Dense, Dropout

# XGBoost
import xgboost as xgb

# Commandline arguments.
from argparse import ArgumentParser

# ========== Command Arguments ==========

parser = ArgumentParser()

# Classfication related -- Required
parser.add_argument("method",
                    help=("The method of classification. "
                          "Must be one of the following: "
                          "knn, log_reg, svc, mlpc"))
parser.add_argument("-r", "--radius", required=True,
                    help="Radius to run classfier on.")
parser.add_argument("-p", "--param", nargs="*", action='append',
                    help="Parameters to the classfier.")

# Data related -- Required
parser.add_argument("-c", "--centers", required=True,
                    help="The file containing center IPD info.")
parser.add_argument("-s", "--sequences", required=True,
                    help="The file containing sequences.")
parser.add_argument("-o", "--outdir", required=True,
                    help="The directory to output.")

# Data related -- Optional
parser.add_argument("--parallel", action="store_true",
                    help="Run on a multithreaded environment.")
parser.add_argument("--interactive", action="store_true",
                    help="Makes plots show to the user.")
parser.add_argument("-top", "--top", action="store_true",
                    help="Analyze only top")
parser.add_argument("-bottom", "--bottom", action="store_true",
                    help="Analyze only bottom")
parser.add_argument("-e", "--even", action="store_true",
                    help="Use a 50-50 distribution of true and false examples.")
parser.add_argument("-folds", "--folds", default=5, type=int,
                    help="Number of folds to use for cross validation.")
parser.add_argument("-n", "--note", default="",
                    help="Post-fix to file name.")
args = parser.parse_args()

# ========== Classification Methods ==========
def knn(X_train, y_train, params):
    return KNeighborsClassifier(int(params[0])).fit(X_train, y_train) 

def log_reg(X_train, y_train, params):
    return LogisticRegression(max_iter=int(params[0])).fit(X_train, y_train) 

def ridge(X_train, y_train, params):
    return RidgeClassifier(alpha=float(params[0])).fit(X_train, y_train) 

def svc(X_train, y_train, params):
    return SVC(kernel=params[0], probability=True).fit(X_train, y_train) 

# Input relative
def mlpc(X_train, y_train, params):
    return MLPClassifier(tuple([int(float(i)*len(X_train[0])) for i in params[0].split(",")]), max_iter=int(params[1])).fit(X_train, y_train) 

def rfc(X_train, y_train, params):
    return RandomForestClassifier(n_estimators=int(params[0]), n_jobs=-1).fit(X_train, y_train) 

def keras_model(X_train, y_train, params):
    # layer sizes
    sizes = [int(float(i)*len(X_train[0])) for i in params[0].split(",")]
    model = Sequential()
    model.add(Dense(sizes[0], activation="relu", input_shape=(len(X_train[0]),)))
    model.add(Dropout(float(params[1])))
    for i in range(1, len(sizes)):
        model.add(Dense(sizes[i], activation="relu"))
        model.add(Dropout(float(params[1])))
    model.add(Dense(1, activation="sigmoid"))
    model.compile(optimizer="adam", loss="binary_crossentropy")
    model.fit(X_train, y_train, epochs=int(params[2]))
    return model

def boosting(X_train, y_train, params):
    # dtrain = xgb.DMatrix(np.array(X_train), label=np.array(y_train))
    # bparams = {
    #     "verbosity": 2,
    #     # "num_parallel_tree": 2
    #     "max_depth": int(params[1])
    # }
    # bst = xgb.train(bparams, dtrain, int(params[0]))
    # dtest = xgb.DMatrix(np.array(X_test))
    # return np.squeeze(bst.predict(dtest, ntree_limit=bst.best_ntree_limit))
    return xgb.XGBClassifier(max_depth=10, n_estimators=int(params[0]), n_jobs=-1,).fit(X_train, y_train) 

def get_classfication_name(method):
    if method == "knn":
        return "K-Nearest Neighbors"
    elif method == "log_reg":
        return "Logistic Regression"
    elif method == "svc":
        return "Support Vector"
    elif method == "mlpc":
        return "Multi-Layer Perception"
    elif method == "rfc":
        return "Random Forest"
    elif method == "keras_model":
        return "Keras Model"
    elif method == "boosting":
        return "XGBoost Random Forest"
    elif method == "ridge":
        return "Ridge Classifier"
    else:
        return "Unknown"

def prepare_input(sequences):
    ss = []
    # for s in sequences:
    #     if s in FEATURES:
    ss.append(scale(sequences["Top IPD Ratio"]))
    d = pd.get_dummies(pd.DataFrame(sequences["Base"]))
    cols = d.columns
    for col in cols:
        if "N" in col:
            d.drop(columns=[col], inplace=True)
            
    ss.append(d.values)
    print(d)
    data = np.concatenate(ss, axis=1)
    return data

def create_sequence(bases, index):
    # print(scale(sequences["Top IPD Ratio"][index]))
    # print(pd.get_dummies(pd.DataFrame(bases)).values.flatten())
    return np.concatenate([scale(sequences["Top IPD Ratio"][index]),
        pd.get_dummies(pd.DataFrame(bases)).values.flatten()])

# We want to see which T, when removed, drops the prediction value considerably
def determine_t(sequences, index, model):
    # Returns the offset of the T in the sequence.

    # List of T positions and their values.
    t_pos = []
    c_val = []
    sequence = sequences["Base"][index]
    # print(sequence)
    for i, c in enumerate(sequence):
        if c == "T":
            t_pos.append(i - len(sequence) // 2)
            te = []
            for n in ["A", "C", "G"]:
                # print(sequence)
                # print(create_sequence(np.concatenate([sequence[:i], [n], sequence[i+1:]]), index))
                te.append(create_sequence(np.concatenate([sequence[:i], [n], sequence[i+1:]]), index))
                if te[-1].shape[0] != 255:
                    del te[-1]
                    continue
                # print(te[-1].shape)
            # print(np.array(te))
            if len(te) != 3:
                continue
            try:
                vals = model.predict(np.array(te))
            except:
                print("ERROR")
                print(te)
                print(te[0].shape)
                print(te[1].shape)
                print(te[2].shape)
                continue
            # print(vals)
            c_val.append(min(vals))
    if len(c_val) == 0:
        return math.inf, math.inf
    m = np.argmin(c_val)
    return t_pos[m], c_val[m]


# ========== Main Setup ==========

def init(l, c, s, p, o):
    global lock, centers, sequences, params, outdir
    lock = l
    centers = c
    sequences = s
    params = p
    outdir = o
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

def get_resources():
    # Load in tables
    c = pd.read_csv(args.centers)
    s = np.load(args.sequences)[()]
    return c, s

# ========== Run Routine ==========
THRESHOLD = .5

def run(index):
    # print(f"[START] {params[index]}")

    radius = args.radius
    # c, f = resize_and_verify(centers, topsequences, bottomsequences, bases, radius)     
    s = prepare_input(sequences)
    y = c["Fold Change"].map(lambda x: 1 if x > 10 else 0).values
    print(s.shape)


    model = globals()[args.method](s, y, params[index])
    print(sequences.keys())
    js = pd.DataFrame()
    for index, (x, y) in enumerate(zip(s, y)):
        v = np.squeeze(np.squeeze(model.predict(x[np.newaxis,:])))
        if v > THRESHOLD and "T" in sequences["Base"][index]:
            offset, min_t = determine_t(sequences, index, model)
            if offset == math.inf or min_t == math.inf:
                continue
            js = js.append(pd.DataFrame({
                "Chromosome" : c["Chromosome"].iloc[index],
                "Position" : c["Position"].iloc[index] + offset,
                "Delta" : min_t - v
            }), ignore_index=True)
            # print(js)
        if index % (s.shape[0] // 1000) == 0:
            print(index / s.shape[0])
    js.sort_values(by=["Chromosome", "Position"]).to_csv("j_positions.tsv", sep="\t", index=False)



                        
                        



    # fprs = []
    # tprs = []
    # aucs = []
    # labels = []

    # cv = StratifiedKFold(n_splits=args.folds, random_state=0)

    # i = 0
    # mean_fpr = np.linspace(0, 1, 100)
    # for train, test in cv.split(s, y):
    #     y_scores = globals()[args.method](s[train], y[train], params[index])
    #     fpr, tpr, thresholds = roc_curve(y[test], y_scores)
    #     tprs.append(interp(mean_fpr, fpr, tpr))
    #     tprs[-1][0] = 0.0
    #     roc_auc = auc(fpr, tpr)
    #     aucs.append(roc_auc)
    #     plt.plot(fpr, tpr, lw=1, alpha=0.3, label=f"ROC fold {i} (AUC={roc_auc:.2f})")
    #     i += 1
    # plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r', alpha=.8)

    # mean_tpr = np.mean(tprs, axis=0)
    # mean_tpr[-1] = 1.0
    # mean_auc = auc(mean_fpr, mean_tpr)
    # std_auc = np.std(aucs)
    # plt.plot(mean_fpr, mean_tpr, color='b',
    #         label='Mean ROC (AUC = %0.2f $\pm$ %0.2f)' % (mean_auc, std_auc),
    #         lw=2, alpha=.8)

    # std_tpr = np.std(tprs, axis=0)
    # tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    # tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    # plt.fill_between(mean_fpr, tprs_lower, tprs_upper, color='grey', alpha=.2,
    #                 label='$\pm$ 1 std. dev.')

    # plt.xlim([0, 1])
    # plt.ylim([0, 1])
    # plt.xlabel('False Positive Rate')
    # plt.ylabel('True Positive Rate')
    # # plt.title("Classification ROC Plot: 50% Dropout, 25 Epochs")
    # plt.title(f"{get_classfication_name(args.method)} ROC Plot. Radius={radius}, Params: {' '.join(params[index])}")
    # plt.legend(loc="lower right")

    # if args.interactive:
    #     plt.show()
    # else:
    #     plt.savefig(outdir + f"{args.method}_kfolds_r_{radius}_p_{'_'.join(params[index]).replace(',','-').replace('.','-')}{args.note}", dpi=600)
    # plt.close("all")
    # plt.cla()

    # print(f"[FINISH] {params[index]}")

# ========== Main ==========

if __name__ == "__main__":
    l = Lock()
    c, s = get_resources()

    if args.parallel:
        pool = Pool(os.cpu_count(),
                    initializer=init,
                    initargs=(l, c, s, args.param, arg.outdir))
        pool.map(run, params)
        pool.close()
        pool.join()
    else:   
        init(l, c, s, args.param, args.outdir)
        for i in range(len(args.param)):
            run(i)