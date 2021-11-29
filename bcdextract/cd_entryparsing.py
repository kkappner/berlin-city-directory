# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 13:43:33 2021

Adapted version of the city-directory-entry-parser by Bert Spaan and Stephen Balogh
https://github.com/nypl-spacetime/city-directory-entry-parser

"""

import csv
import fileinput
import json
import sys
import sklearn_crfsuite
from sklearn_crfsuite import metrics
from functools import partial

class Classifier:
    def __init__ (self, training_data=None):
        self.training_set_labeled = []
        self.training_set_features = []
        self.training_set_labels = []
        self.validation_set_labeled = []
        self.validation_set_features = []
        self.validation_set_labels = []
        self.crf = None

    def load_labeled_data(self, path_to_csv, rows_to_ignore=0):
        rows = []
        labeled_data = []
        with open(path_to_csv, 'r') as csvfile:
            rdr = csv.reader(csvfile)
            index = -1
            for row in rdr:
                index += 1
                if index >= rows_to_ignore:
                    rows.append(row)
        example_number = -1
        example = None
        for row in rows:
            sentence_number = int(row[0])
            if sentence_number > example_number:
                example_number = sentence_number
                if example == None:
                    example = []
                else:
                    labeled_data.append(example)
                    example = []
            example.append((row[1], row[2]))
        labeled_data.append(example)
        return labeled_data

    def listen(self):
        for line in fileinput.input(sys.argv[3:]):
            entry = LabeledEntry(line.rstrip())
            print(json.dumps(self.label(entry).categories))

    def load_training(self, path_to_csv, rows_to_ignore=0):
        self.training_set_labeled = self.load_labeled_data(path_to_csv, rows_to_ignore)
        self.__process_training_data()

    def load_validation(self, path_to_csv, rows_to_ignore=0):
        self.validation_set_labeled = self.load_labeled_data(path_to_csv, rows_to_ignore)
        self.__process_validation_data()

    def __process_training_data(self):
        self.training_set_features = [Features.get_sentence_features(s) for s in self.training_set_labeled]
        self.training_set_labels = [Features.get_sentence_labels(s) for s in self.training_set_labeled]

    def __process_validation_data(self):
        self.validation_set_features = [Features.get_sentence_features(s) for s in self.validation_set_labeled]
        self.validation_set_labels = [Features.get_sentence_labels(s) for s in self.validation_set_labeled]

    def train(self):
        self.crf = sklearn_crfsuite.CRF(
            algorithm='lbfgs',
            c1=0.1,
            c2=0.1,
            max_iterations=1000,
            all_possible_transitions=False,
            verbose=False
            )
        self.crf.fit(self.training_set_features, self.training_set_labels)

    def validation_metrics(self):
        labels = list(self.crf.classes_)
        validation_predictions = self.crf.predict(self.validation_set_features)
        return metrics.flat_f1_score(self.validation_set_labels, validation_predictions, average='weighted', labels=labels)

    def print_validation_metrics_per_class(self):
        validation_predictions = self.crf.predict(self.validation_set_features)
        sorted_labels = sorted(
            list(self.crf.classes_),
            key=lambda name: (name[1:], name[0])
        )
        print(metrics.flat_classification_report(
            self.validation_set_labels, validation_predictions, labels=sorted_labels, digits=5
        ))

    def predict_labeled_tokens(self, labeled_tokens):
        features_set = [Features.get_sentence_features(labeled_tokens)]
        return self.crf.predict(features_set)[0]

    def label(self, labeled_entry):
        if isinstance(labeled_entry, list):
            return list(self.label(x) for x in labeled_entry)
        else:
            labeled_entry.token_labels = self.predict_labeled_tokens(labeled_entry.tokens)
            labeled_entry.is_parsed = True
            labeled_entry.reduce_labels()
            return labeled_entry

class LabeledEntry:
    def __init__(self, input_string='', input_tokens=None):
        self.original_string = input_string
        self.tokens = input_tokens or Utils.label_tokenize(input_string)
        self.token_labels = []
        self.is_parsed = False
        self.categories = None

    # reduce_labels() creates a best-guess record from a sequence of predicted labels
    def reduce_labels(self):
        if self.categories == None:
            categories = {
                'subjects': [],
                'occupations': [],
                'other': [],
                'proprietor': [],
                'absentee': []
            }
            # We use the three vars below to construct record inputs as we iterate
            # through the sequence of labels
            constructing_label = None
            constructing_entity = ""
            constructing_predicate = ""
            for label, token_tuple in zip(self.token_labels, self.tokens):
                token = token_tuple[0] # 'token' gets the actual text of the token
                if constructing_label == label:
                    # If the previously seen label is the same as the current, we simply append
                    if constructing_label == "PA":
                        constructing_predicate += " " + token
                    else:
                        constructing_entity += " " + token
                else:
                    # Otherwise, we have a new label, and have to clean up when is currently
                    # stored in the 'constructing_' vars...
                    if constructing_label == 'N':
                        categories['subjects'].append(constructing_entity)
                    elif constructing_label == 'O':
                        categories['occupations'].append(constructing_entity)
                    elif constructing_label == 'A':
                        location = {'value': constructing_entity}
                        if len(constructing_predicate) != 0:
                            location['labels'] = list(filter(None, constructing_predicate.split(" .")))
                            constructing_predicate = ""
                        categories['absentee'].append(location)
                    elif constructing_label == 'P':
                        categories['proprietor'].append(constructing_entity)
                    elif constructing_label == 'S':
                        categories['other'].append(constructing_entity)
                    constructing_entity = ""
                    constructing_label = label
                    if constructing_label == "PA":
                        constructing_predicate += token
                    else:
                        constructing_entity += token
            self.categories = categories
            return self
                
    def __str__(self):
        if self.is_parsed:
            return Utils.to_pretty_string(self.tokens, self.token_labels)
        else:
            return self.original_string

class Features:

    @staticmethod
    def __emit_word_features(rel_pos, word):
        features = {}
        for f in Features.__word_feature_functions().items():
            features.update({str(rel_pos) + ":" + f[0]: f[1](word)})
        return features

    @staticmethod
    def get_word_features(sentence,i):
        features = {}
        for x in range(i - 2, i + 3):
            if 0 <= x < len(sentence):
                features.update(Features.__emit_word_features(-(i - x), sentence[x][0]))
        if i == 0:
            features.update({'BOS' : True})
        if i == len(sentence) - 1:
            features.update({'EOS': True})
        if len(sentence) == 4:
            if i == 1: features.update({'word.1stoftwo': True})
            if i == 2: features.update({'word.2ndoftwo': True})
        return features

    @staticmethod
    def __word_feature_functions():
        return {
            "word.repeated_name": Features.__starts_with_longdash,
            "word.pens": Features.__is_pens_token,
            "word.geh.token": Features.__is_geh_token,
            "word.widow.token": Features.__is_widow_token,
            "word.contains.digit": Features.__contains_digit,
            "word.is.delimiter": Features.__is_delimiter,
            "word.is.start.token": Features.__is_start,
            "word.is.end.token": Features.__is_end,
            "word.is.lower": str.islower,
            "word.is.title": str.istitle,
            "word.is.upper": str.isupper,
            "word.substr[-2:]" : partial(Features.__substr, 2),
            "word.substr[-1:]": partial(Features.__substr, 1),
            "word.parenS": Features.__starts_with_paranth,
            "word.parenE": Features.__ends_with_paranth,
            "word.endswithStr": Features.__ends_with_str,
            "word.isconstructionsite": Features.__is_construction_site,
            "word.1stoftwo": Features.set_false,
            "word.2ndoftwo": Features.set_false
        }

    @staticmethod
    def get_sentence_features(sentence):
        return [Features.get_word_features(sentence, i) for i in range(len(sentence))]

    @staticmethod
    def get_sentence_labels(sentence):
        return [label for token, label in sentence]

    @staticmethod
    def get_sentence_tokens(sentence):
        return [token for token, label in sentence]

    @staticmethod
    def set_false(input):
        return False 

    @staticmethod
    def __contains_digit(input):
        for c in input:
            if c.isdigit():
                return True
        return False

    @staticmethod
    def __substr(amount, word):
        return word[amount:]

    @staticmethod
    def __is_start(input):
        if input == "START":
            return True
        return False

    @staticmethod
    def __is_end(input):
        if input == "END":
            return True
        return False

    @staticmethod
    def __starts_with_longdash(input):
        if input.startswith('—') or input.startswith('-'):
            return True
        return False    
    
    @staticmethod
    def __starts_with_paranth(input):
        if input.startswith('('):
            return True
        return False

    @staticmethod
    def __ends_with_paranth(input):
        if input.endswith(')'):
            return True
        return False

    @staticmethod
    def __ends_with_str(input):
        if input.endswith('str') or input.endswith('ſtr'):
            return True
        return False

    @staticmethod
    def __is_construction_site(input):
        if input in ('Baustelle', 'Baustellen', 'Bauſtelle', 'Bauſtellen', 'Neubau', 'Umbau', 'Rohbau', 'Rohbauten'):
            return True
        return False

    @staticmethod
    def __is_delimiter(input):
        for c in input:
            if c == '.' or c == ',':
                return True
        return False

    @staticmethod
    def __is_pens_token(input):
        dc = input.lower()
        if dc == "pens" or dc == "penſ":
            return True
        return False

    @staticmethod
    def __is_geh_token(input):
        dc = input.lower()
        if dc == "geh" or dc == "wirkl":
            return True
        return False
    
    @staticmethod
    def __segment_of_sentence(sent, i, div):
        sent_length = len(sent)
        pos = i + 1
        for j in range(1,div + 1):
            if pos <= j*(sent_length / float(div)):
                return j

    @staticmethod
    def __is_widow_token(input):
        dc = input.lower()
        if dc == "ww" or dc == "wwe" or dc == "vw" or dc == "verw":
            return True
        return False
    
class Utils:
    @staticmethod
    def label_tokenize(input):
        return list(map(lambda x: (x, None), Utils.tokenize(input, True)))

    @staticmethod
    def tokenize(input, append_start_end=False):
        tokens = ['START'] if append_start_end else []
        buffer = ''
        for elem in input:
            if elem == '.' or elem == ',' or elem == '&':
                if len(buffer) > 0:
                    tokens.append(buffer)
                    buffer = ''
                tokens.append(elem)
            elif elem == ' ':
                if len(buffer) > 0:
                    tokens.append(buffer)
                    buffer = ''
                #tokens.append(',')
            else:
                buffer += elem
        if len(buffer) > 0:
            tokens.append(buffer)
        if append_start_end:
            tokens.append('END')
        return tokens

    @staticmethod
    def to_pretty_string(original_tokens, token_labels):
        text = ""
        if len(original_tokens) == len(token_labels):
            for i in range(0, len(original_tokens)):
                tag = token_labels[i]
                color = Utils.TAG_MAP[tag]
                text += Utils.COLORS[color].format(original_tokens[i][0]) + " "
        return text

    COLORS = {
        'white': "\033[0;37m{}\033[0m",
        'yellow': "\033[0;33m{}\033[0m",
        'green': "\033[0;32m{}\033[0m",
        'blue': "\033[0;34m{}\033[0m",
        'cyan': "\033[0;36m{}\033[0m",
        'red': "\033[0;31m{}\033[0m",
        'magenta': "\033[0;35m{}\033[0m",
        'black': "\033[0;30m{}\033[0m",
        'darkwhite': "\033[1;37m{}\033[0m",
        'darkyellow': "\033[1;33m{}\033[0m",
        'darkgreen': "\033[1;32m{}\033[0m",
        'darkblue': "\033[1;34m{}\033[0m",
        'darkcyan': "\033[1;36m{}\033[0m",
        'darkred': "\033[1;31m{}\033[0m",
        'darkmagenta': "\033[1;35m{}\033[0m",
        'hilite': "\x1b[93;41m{}\033[0m",
        'darkblack': "\033[1;30m{}\033[0m",
        'off': "\033[0;0m{}\033[0m"
    }

    TAG_MAP = {
        'N': 'red',
        'O': 'darkyellow',
        'A': 'green',
        'P': 'darkcyan',
        'START': 'blue',
        'D': 'darkmagenta',
        'X': 'black',
        'S': 'white',
        'END': 'blue',
    }
