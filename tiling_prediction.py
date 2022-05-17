import _pickle as cPickle
import numpy as np
import sklearn
from feature_spaces_tiling import extract_features_generated_code
import warnings
import math

warnings.filterwarnings("ignore")


class TilingPredictor:

    def __init__(self, filename, heuristic):
        self.bruteforce_model = None
        self.yuki_model = None
        self.liu_model = None
        self.init_models()
        self.divisor_heuristic = heuristic
        self.filename = filename

    def init_models(self):
        with open('models/brute.csv', 'rb') as f:
            self.bruteforce_model = cPickle.load(f)

        with open('models/yuki_model.csv', 'rb') as f:
            self.yuki_model = cPickle.load(f)

        with open('models/liu_model.csv', 'rb') as f:
            self.liu_model = cPickle.load(f)

    def parse_input(self):
        feature_names = ['vectorization_feature', 'k-loop_feature', 'j-loop_feature', 'i-loop_feature',
                         'loop_invariant_read', 'spatial_locality_read', 'no_locality_read', 'loop_invariant_write',
                         'spatial_locality_write', 'no_locality_write', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                         '10',
                         '11', '12', '13', '14', '15', '16', '17', '18']

        extracted_features = extract_features_generated_code(self.filename)

        liu_features = list(extracted_features[0].values())[1:5]
        yuki_features = list(extracted_features[0].values())[5:11]
        brute_features = list(extracted_features[0].values())[11:]

        return yuki_features, liu_features, brute_features

    def predict(self, features):
        yuki_features, liu_features, brute_features = features

        yuki_prediction = self.yuki_model.predict(np.array(yuki_features).reshape(1, -1))
        yuki_prediction = round(yuki_prediction[0])

        liu_prediction = self.liu_model.predict(np.array(liu_features).reshape(1, -1))
        liu_prediction = round(liu_prediction[0])

        brute_prediction = self.bruteforce_model.predict(np.array(brute_features).reshape(1, -1))
        brute_prediction = round(brute_prediction[0])

        if self.divisor_heuristic:
            yuki_prediction = 2 ** round(math.log2(yuki_prediction))
            liu_prediction = 2 ** round(math.log2(liu_prediction))
            brute_prediction = 2 ** round(math.log2(brute_prediction))

        print('Yuki features prediction is {}\n'.format(yuki_prediction))
        print('Liu features prediction is {}\n'.format(liu_prediction))
        print('Bruteforce features prediction is {}\n'.format(brute_prediction))
