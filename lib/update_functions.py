import os
import glob
import urllib2
import tarfile
import json
from lib.environment import env_mode, env_server, env_inst
import lib.tactic_classes as tc


def get_version(major=0, minor=0, build=0, revision=0, string=False):
    version_dict = {
        'major': major,
        'minor': minor,
        'build': build,
        'revision': revision,
    }
    if string:
        return '{major}_{minor}_{build}_{revision}'.format(**version_dict)
    else:
        return version_dict


def read_json_from_path(file_path):
    if os.path.exists(file_path):
        json_file = file(file_path)
        return json.load(json_file)
    else:
        return get_version()


def save_json_to_path(file_path, data):
    updates_dir = '{0}/updates'.format(env_mode.get_current_path())
    if not os.path.exists(updates_dir):
        os.makedirs(updates_dir)
    json_file = file(file_path, mode='w+')
    json.dump(data, json_file)


def get_current_version():
    file_path = '{0}/lib/version.json'.format(env_mode.get_current_path())
    return read_json_from_path(file_path)


def check_need_update():
    server_ver = check_for_last_version()
    if not server_ver:
        return False
    current_ver = get_current_version()

    if get_version(**server_ver) != get_version(**current_ver):
        return True


def save_current_version(data):
    file_path = '{0}/lib/version.json'.format(env_mode.get_current_path())
    save_json_to_path(file_path, data)


def get_info_from_updates_folder(files_list=False):
    updates_dir = '{0}/updates'.format(env_mode.get_current_path())
    json_files = glob.glob1(updates_dir, '*.json')
    if files_list:
        return json_files
    updates_list = []
    for jf in json_files:
        if jf != 'versions.json':
            updates_list.append(read_json_from_path('{0}/{1}'.format(updates_dir, jf)))

    return updates_list


def create_updates_list():
    file_path = '{0}/updates/versions.json'.format(env_mode.get_current_path())
    save_json_to_path(file_path, get_info_from_updates_folder(files_list=True))


def download_from_url(url):
    proxy = env_server.get_proxy()
    if proxy['enabled']:
        server = proxy['server'].replace('http://', '')
        proxy_dict = {
            'http': 'http://{login}:{pass}@{0}'.format(server, **proxy)
        }
        proxy_handler = urllib2.ProxyHandler(proxy_dict)
        auth = urllib2.HTTPBasicAuthHandler()
        opener = urllib2.build_opener(proxy_handler, auth, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

    run_thread = tc.ServerThread(env_inst.ui_main)
    run_thread.kwargs = dict(url=url)
    run_thread.routine = urllib2.urlopen
    run_thread.run()
    result_thread = tc.treat_result(run_thread)
    if result_thread.isFailed():
        return False
    else:
        return result_thread.result


def check_for_last_version():
    last_ver = download_from_url('http://tactichandler.tk/th/version.json')
    if last_ver:
        update_str = json.loads(last_ver.read())
        return update_str


def get_updates_from_server():

    updates_list = download_from_url('http://tactichandler.tk/th/versions.json')
    if updates_list:
        versions_list = json.loads(updates_list.read())
        path_to_save = '{0}/updates'.format(env_mode.get_current_path())

        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)

        for vl in versions_list:
            update_file = download_from_url('http://tactichandler.tk/th/{0}'.format(vl))
            with open('{0}/{1}'.format(path_to_save, vl), 'wb') as output:
                output.write(update_file.read())


def get_update_archive_from_server(archive_name):

    archive_path = '{0}/updates/{1}'.format(env_mode.get_current_path(), archive_name)

    update_archive_file = download_from_url('http://tactichandler.tk/th/{0}'.format(archive_name))
    if update_archive_file:
        with open(archive_path, 'wb') as output:
            output.write(update_archive_file.read())

        return archive_path


def delete_files_from_list(files_list):
    print files_list


def update_from_archive(archive_path):
    tar = tarfile.open(archive_path, "r:gz")
    tar.extractall(env_mode.get_current_path())
    tar.close()
