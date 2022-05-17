from ast_parsing import AST_parsing
from auxiliary_functions import save_to_cvs


def reconstruct_arrays(list_of_iterators):
    arrays_for_read = []
    arrays_for_write = []
    current_pattern = ''
    current_index = list_of_iterators[0][1]
    for idx, iterator in enumerate(list_of_iterators):
        array_name, dimensionality, side, it = iterator
        if current_index == 0:
            current_index += dimensionality
            if list_of_iterators[idx - 1][2] == 'l':
                arrays_for_write.append(current_pattern)
            else:
                arrays_for_read.append(current_pattern)
            current_pattern = it
            current_index -= 1
        else:
            current_pattern += it
            current_index -= 1
    if list_of_iterators[-1][2] == 'l':
        arrays_for_write.append(current_pattern)
    else:
        arrays_for_read.append(current_pattern)
    return arrays_for_read, arrays_for_write


def yuki_approach_ijk_loop(arrays_for_read, arrays_for_writes):
    features = [0] * 6
    locality = ['i', 'j', 'k', 'ij', 'ik', 'jk', 'ijk']
    for array in arrays_for_read:
        if 'k' not in array:
            features[0] += 1
        else:
            if array in locality:
                features[1] += 1
            else:
                features[2] += 1

    for array in arrays_for_writes:
        if 'k' not in array:
            features[3] += 1
        else:
            if array in locality:
                features[4] += 1
            else:
                features[5] += 1

    return features


def bruteforce_approach_ijk_loop(arrays_for_read, arrays_for_writes):
    combinations_read = {'ij': 0, 'ik': 0, 'ji': 0, 'jk': 0, 'ki': 0, 'kj': 0, 'kk': 0, 'ii': 0, 'jj': 0}
    combinations_write = {'ij': 0, 'ik': 0, 'ji': 0, 'jk': 0, 'ki': 0, 'kj': 0, 'kk': 0, 'ii': 0, 'jj': 0}

    for array in arrays_for_read:
        combinations_read[array] += 1
    for array in arrays_for_writes:
        combinations_write[array] += 1

    combined_array = list(combinations_read.values()) + list(combinations_write.values())
    return combined_array


def liu_approach_ijk_loop(arrays_for_read, arrays_for_writes, number_of_statements=1):
    number_of_statements = len(arrays_for_writes)
    combined_array = arrays_for_read + arrays_for_writes
    features = [0] * 4
    iterators = ['k', 'j', 'i']
    locality = ['i', 'j', 'k', 'ij', 'ik', 'jk', 'ijk']
    inner_most_iterator = 'k'
    for array in combined_array:
        if array[-1] == inner_most_iterator and array in locality:
            features[0] += 1
    for idx, iterator in enumerate(iterators):
        for array in combined_array:
            if (iterator not in array) or (array[-1] == iterator and array in locality):
                features[1 + idx] += 1
    features = [x / number_of_statements for x in features]

    return features


def extract_features_generated_code(path):
    ast_parsing = AST_parsing()
    ast_features = ast_parsing.get_features(path)
    extract_features_based_on_reconstructed_arrays(ast_features)
    return list(ast_features.values())


def extract_features_based_on_reconstructed_arrays(features):
    for k, v in features.items():
        arrays = v['iterators']
        reconstructed_arrays = reconstruct_arrays(arrays)
        liu_features = liu_approach_ijk_loop(*reconstructed_arrays)
        bruteforce_features = bruteforce_approach_ijk_loop(*reconstructed_arrays)
        yuki_features = yuki_approach_ijk_loop(*reconstructed_arrays)
        features[k] = {'label': features[k]['label']}

        add_features(features[k], liu_features, 'liu')

        add_features(features[k], yuki_features, 'yuki')
        add_features(features[k], bruteforce_features, 'brute')


def add_features(features, encoding, name):
    feature_names = {'liu': ['vectorization_feature', 'k-loop_feature', 'j-loop_feature', 'i-loop_feature'],
                     'yuki': ['loop_invariant_read', 'spatial_locality_read', 'no_locality_read',
                              'loop_invariant_write', 'spatial_locality_write', 'no_locality_write'],
                     'brute': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',
                               '17', '18']

                     }

    for idx, value in enumerate(encoding):
        features[feature_names[name][idx]] = value