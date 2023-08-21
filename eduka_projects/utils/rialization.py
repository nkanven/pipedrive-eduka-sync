"""
The rialization contains all the methods needed to store python objets for memoization and further usage
"""

import datetime
import os
import pickle


def serialize(file_path, data) -> bool:
    """
    Serialize data for later usage
    :param file_path: (str) full path of the file to be created for in which the bytes will be stored
    :param data: (any) the object to store. It can be of any datatype
    :return: (bool) function does True if successfully completed or False if an error occured
    """

    result = False
    try:
        with open(file_path, "wb") as d:
            d.write(pickle.dumps(data))
        result = True
    except Exception as e:
        print("Error ", str(e))
    finally:
        return result


def deserialize(dir_name, fname) -> list:
    """
    Deserialize a store object
    :param dir_name: (str) the name of the directory in which file is stored
    :param fname: (str) name of the file to desirialize.
    :return: (list) function return a list of python object
    """
    data = []

    for f in os.listdir(dir_name):

        if f.find(fname) != -1:
            with open(dir_name + os.sep + f, "rb") as d:
                data.append(pickle.loads(d.read()))

    return data


def delete_serialized(folder_path, file_name):
    """
    Delete serialized files
    :param folder_path: (str) path of the folder in which files should be searched
    :param file_name: (str) partial or full name of the file to delete.
    """
    for stored_memo_file in os.listdir(folder_path):
        if stored_memo_file.find(file_name) != -1:
            os.remove(folder_path + os.sep + stored_memo_file)


def clean_memoize_folder(folder_path):
    """
    Delete old serialized file
    @param folder_path: self explaining
    @return: void
    """
    for _file in os.listdir(folder_path):
        c_time = os.path.getctime(folder_path)
        dt_c = datetime.datetime.fromtimestamp(c_time)
        dt_now = datetime.datetime.now()
        date_dtc = datetime.datetime.strptime(dt_c.strftime("%Y-%m-%d"), "%Y-%m-%d")
        date_dtn = datetime.datetime.strptime(dt_now.strftime("%Y-%m-%d"), "%Y-%m-%d")

        if date_dtn > date_dtc:
            os.remove(os.path.join(folder_path, _file))
