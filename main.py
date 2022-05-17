from tiling_prediction import TilingPredictor
from auxiliary_functions import get_abs_path


def main():
    file_to_optimize = 'programs_to_predict/mm_parsing.c'

    power_of_two_heuristic = True

    predictor = TilingPredictor(get_abs_path(file_to_optimize), power_of_two_heuristic)
    features = predictor.parse_input()
    predictor.predict(features)


if __name__ == '__main__':
    main()
