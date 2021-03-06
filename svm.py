from sklearn import svm
from sklearn.model_selection import ShuffleSplit
from sklearn.metrics import precision_score, recall_score


def train_svm(x_train, x_test, y_train, y_test):
    '''
    run SVM from sklearn and print output
    :param train_vecs: feature vectors training set
    :param test_vecs: feature vectors test set
    :param y_train: labels training set
    :param y_test: labels test set
    :return: accuracy, percision and recall
    '''
    clf = svm.LinearSVC()
    clf.fit(x_train, y_train)
    y_test_pred = clf.predict(x_test)

    print 'Train Accuracy: %.3f' % clf.score(x_train, y_train)

    acc = clf.score(x_test, y_test)
    per = precision_score(y_test, y_test_pred)
    recall = recall_score(y_test, y_test_pred)
    print 'Test Accuracy: %.3f'% acc
    print 'Test Percision %.3f' % per
    print 'Test Recall %.3f' % recall
    return acc, per, recall


def run_SVM(x, y):
    '''
    run cross validated SVM regression
    :param x: feature vectors
    :param y: labels
    :return: None
    '''
    print 'SVM: '
    rs = ShuffleSplit(n_splits=5, test_size=.20)
    rs.get_n_splits(x)
    split = 0
    for train_index, test_index in rs.split(x):
        print "split", split
        x_train, x_test = x[train_index], x[test_index]
        y_train, y_test = y[train_index], y[test_index]
        train_svm(x_train, x_test, y_train, y_test)
        split += 1