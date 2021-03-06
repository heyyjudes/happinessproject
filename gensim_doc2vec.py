# gensim modules
import os
import feat
import svm
import logreg
import NNet
import numpy as np
from random import shuffle
from gensim import utils
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec
from sklearn.model_selection import ShuffleSplit

class D2V(feat.Feature):
    def __init__(self, name, dim):
        self.dim = dim
        feat.Feature.__init__(self, name)
        return

    def build_d2v_vecs(self, x_train, x_test, y_train, y_test):
        with open('data/anx_test_set.txt', 'w') as anx:
            with open('data/all_test_set.txt', 'w') as all:
                for i in range(0, len(x_test)):
                    if y_test[i] == 0:
                        anx.write(x_test[i])
                    else:
                        all.write(x_test[i])
        with open('data/anx_train_set.txt', 'w') as anx:
            with open('data/all_train_set.txt', 'w') as all:
                for i in range(0, len(x_train)):
                    if y_train[i] == 0:
                        anx.write(x_train[i])
                    else:
                        all.write(x_train[i])

        sources_train = {
            'data/anx_train_set.txt': 'TRAIN_NEG',
                   'data/all_train_set.txt': 'TRAIN_POS'}

        sources_test = {'data/anx_test_set.txt': 'TEST_NEG', 'data/all_test_set.txt': 'TEST_POS'}

        print('1. labeling')
        sentences = LabeledLineSentence(sources_train)

        model = Doc2Vec(min_count=1, window=10, size=self.dim, sample=1e-4, negative=5, workers=8)

        output_sen, train_neg_size, train_pos_size, test_neg_size, test_pos_size = sentences.to_array()
        model.build_vocab(output_sen)

        model_str = 'models/' + self.name + '_model.d2v'
        if os.path.isfile(model_str):
            print('2+3. loading existing doc2vec')
            model = Doc2Vec.load(model_str)
        else:
            print('2. training doc2vec')
            for epoch in range(10):
                model.train(sentences.sentences_perm())
                print epoch

            print('3. saving model')
            model.save(model_str)

        train_arrays = []
        for sent in x_train:
            train_arrays.append(model.infer_vector(sent.split(" ")))
        train_arrays = np.asarray(train_arrays)
        train_labels = y_train

        test_arrays = []
        for sent in x_test:
            test_arrays.append(model.infer_vector(sent.split(" ")))
        test_arrays = np.asarray(test_arrays)
        test_labels = y_test

        return train_arrays, test_arrays, train_labels, test_labels

class LabeledLineSentence(object):
    '''
    Sentence object from gensim.TaggedDocument type
    '''
    def __init__(self, sources):
        self.sources = sources
        self.train_neg_size = 0
        self.train_pos_size = 0
        self.test_pos_size = 0
        self.test_neg_size = 0
        flipped = {}

        for key, value in sources.items():
            if value not in flipped:
                flipped[value] = [key]

    def __iter__(self):
        for source, prefix in self.sources.items():
            with utils.smart_open(source) as fin:
                for item_no, line in enumerate(fin):
                    yield TaggedDocument(utils.to_unicode(line).split(), [prefix + '_%s' % item_no])

    def to_array(self):
        self.sentences = []
        for source, prefix in self.sources.items():
            with utils.smart_open(source) as fin:
                for item_no, line in enumerate(fin):
                    self.sentences.append(TaggedDocument(utils.to_unicode(line).split(), [prefix + '_%s' % item_no]))
                    if prefix =='TRAIN_NEG':
                        self.train_neg_size += 1
                    if prefix == 'TRAIN_POS':
                        self.train_pos_size += 1
                    if prefix == 'TEST_NEG':
                        self.test_neg_size += 1
                    if prefix == 'TEST_POS':
                        self.test_pos_size += 1
        return self.sentences, self.train_neg_size, self.train_pos_size, self.test_neg_size, self.test_pos_size

    def sentences_perm(self):
        shuffle(self.sentences)
        return self.sentences

    def find_words(self, tag):
        for sent in self.sentences:
            if tag in sent.tags:
                return sent.words


if __name__ == "__main__":
    print('a. fetching data')
    with open('data/anxiety_content.txt', 'r') as infile:
        dep_posts = infile.readlines()

    with open('data/control_content.txt', 'r') as infile:
        reg_posts = infile.readlines()

    with open('data/unlabeled_tweet.txt', 'r') as infile:
        unlabeled_posts = infile.readlines()

    new_arr = []
    for post in reg_posts:
        if len(post) > 5:
            new_arr.append(post)
    reg_posts = new_arr

    new_arr = []
    for post in dep_posts:
        if len(post) > 5:
            new_arr.append(post)
    dep_posts = new_arr

    y = np.concatenate((np.ones(len(reg_posts)), np.zeros(len(dep_posts))))
    x = np.concatenate((reg_posts, dep_posts))

    print('b. initializing')
    rs = ShuffleSplit(n_splits=10, test_size=.10, random_state=0)
    rs.get_n_splits(x)
    split = 0
    for train_index, test_index in rs.split(x):
        print "split", split

        x_train, x_test = x[train_index], x[test_index]
        y_train, y_test = y[train_index], y[test_index]

        new_doc = D2V('w2v_' + str(split), 300)
        train_arrays, test_arrays, train_labels, test_labels = new_doc.build_d2v_vecs(x_train, x_test, y_train, y_test)

        print('Logreg')
        logreg.run_logreg(train_arrays, test_arrays, train_labels, test_labels)

        print('SVM')
        svm.train_svm(train_arrays, test_arrays, train_labels, test_labels)

        print('Simple neural network')
        NNet.simpleNN(train_arrays, test_arrays, train_labels, test_labels, 0.01, 100, 100)

        split +=1


