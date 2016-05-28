###########################################################
#
# Copyright (c) 2008, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

'''ping.py: simpe function to ping the server.  This scripts illustrates the
most basic interaction with the server'''
import os
import sys

DATA_DIR = os.environ['TACTIC_DATA_DIR'] + '/TACTIC_handler'
INSTALL_DIR = os.environ['TACTIC_INSTALL_DIR'] + '/src/client'

sys.path.append(INSTALL_DIR)
sys.path.append(DATA_DIR)


# import the client api library
from lib.client.tactic_client_lib import TacticServerStub

def main():
    # get an instance of the stub
    server = TacticServerStub()

    # start the transaction
    server.start("Ping Test")
    try:
        # ping the server
        print server.fast_ping()
        snapshots = server.query_snapshots(filters=[('search_code', 'CHARS00001'), ('process', 'Blocking')], single=False, include_full_xml=False, include_paths_dict=True, include_parent=False, include_files=True)
        print(snapshots)
    except:
        # in the case of an exception, abort all of the interactions
        server.abort()
        raise
    else:
        # otherwise, finish the transaction
        server.finish()



if __name__ == '__main__':
    main()


