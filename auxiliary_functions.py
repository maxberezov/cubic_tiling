import csv
import os
import pathlib


def get_content(path):
    with open(path) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    return content


def rewrite(path, file):
    with open(path, 'w+') as f:
        for item in file:
            f.write("%s\n" % item)


def do_for_all_files_in_directory(path, extension, f, *args):
    os.chdir(path)
    files = os.listdir(path)
    for item in files:
        if item.endswith(extension):
            target_path = os.path.join(path, item)
            f(target_path, *args)


def delete(path):
    os.remove(path)


def get_abs_path(filename):
    return os.path.join(pathlib.Path().resolve(), filename)


def deletion(path, extension):
    do_for_all_files_in_directory(path, extension, delete)


def save_to_cvs(dictionary, target_dir):
    toCSV = dictionary
    keys = toCSV[0].keys()
    with open(target_dir, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)
