import os
import pickle

from eduka_projects.bootstrap import Bootstrap

bts = Bootstrap()


def serialize(fname, data) -> bool:
    """
    Serialize data for later usage
    :param fname: (str) name of the file to be created for in which the bytes will be stored
    :param data: (any) the object to store. It can be of any datatype
    :return: (bool) function does True if successfully completed or False if an error occured
    """

    result = False
    try:
        with open(fname, "wb") as d:
            d.write(pickle.dumps(data))
        result = True
    except Exception as e:
        print(str(e))
    finally:
        return result


def deserialize(service_running, category):
    """
    Deserialize a store object
    :param service_running: (str) the name of the service running
    :param category: (str) the type of contained in data. It can be mail, memoize, etc.
    :return: (list) function return a list of python object
    """
    data = []
    fname = category + service_running
    for f in os.listdir(bts.autobackup_memoize):
        if f.find(fname) != -1:
            with open(bts.autobackup_memoize + os.sep + f, "rb") as d:
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
