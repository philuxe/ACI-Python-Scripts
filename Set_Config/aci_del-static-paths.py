from cobra.mit.access import MoDirectory, ClassQuery
from cobra.mit.session import LoginSession
from cobra.mit.request import ConfigRequest

import requests.packages.urllib3

# Features :
# Deleting static paths for regular ports, port-channel and virtual port-channel

requests.packages.urllib3.disable_warnings()

session = LoginSession('https://sandboxapicdc.cisco.com', 'admin', 'password')
moDir = MoDirectory(session)
moDir.login()


def delete_mo(mo_object):
    if mo_object is not None:
        mo_object.delete()
        config_req = ConfigRequest()
        config_req.addMo(mo_object)
        moDir.commit(config_req)


# format port id = eth1/1
def get_mo_for_interface(nodeid, portid):
    cq = ClassQuery('fabricPathEpCont')
    cq.propFilter = 'eq(fabricPathEpCont.nodeId, "{0}")'.format(nodeid)
    cq.subtree = 'children'
    cq.subtreeClassFilter = 'fabricPathEp'
    req = moDir.query(cq)
    for key in req[0].children:
        if key.name == portid:
            return format(key.dn)  # return a string containing the MO for the requested interface


def get_epg_staticpaths_from_int_mo(parm1):
    cq = ClassQuery('fvRsPathAtt')
    cq.propFilter = 'eq(fvRsPathAtt.tDn, "{0}")'.format(parm1)
    my_result = moDir.query(cq)
    return my_result  # return list of objects


def get_epg_staticpaths_from_pg_name(parm1):
    cq = ClassQuery('fvRsPathAtt')
    regex = "\[" + parm1 + "\]"
    cq.propFilter = 'wcard(fvRsPathAtt.tDn, "{0}")'.format(regex)
    my_result = moDir.query(cq)
    return my_result  # return list of objects


vpc_choice = ('vpc',)
int_po_choice = ('reg', 'po')

path_type = raw_input("Enter the port type: "
                      "'reg' for a standalone port, "
                      "'po' for a port-channel or 'vpc' for a VPC [reg/po/vpc]:  ")

if path_type in int_po_choice:
    node_id = raw_input("Enter Leaf ID:  ")
    port_id = raw_input("Enter Port ID (ethx/y):  ")
    int_mo = get_mo_for_interface(node_id, port_id)
    if int_mo:
        path_list = get_epg_staticpaths_from_int_mo(int_mo)
        print ("Found {0} path(s)".format(len(path_list)))
        if path_list:
            for mo in path_list:
                print mo.dn
            confirm = raw_input("Delete Paths ? (Y/N):  ")
            if confirm == "Y":
                for mo in path_list:
                    print ("deleting path : {0}".format(mo.dn))
                    delete_mo(mo)
            else:
                moDir.logout()
                exit("Aborted")
        else:
            print ("Exiting ...")
    else:
        print ("Port {0} on Leaf {1} does not exist !!!".format(port_id, node_id))

elif path_type in vpc_choice:
    pg_name = raw_input("Enter Policy Group Name:  ")
    path_list = get_epg_staticpaths_from_pg_name(pg_name)
    print ("Found {0} path(s)".format(len(path_list)))
    if path_list:
        for mo in path_list:
            print mo.dn
        confirm = raw_input("Continue and Delete them ? (Y/N):  ")

        if confirm == "Y":
            for mo in path_list:
                print ("deleting path(s) : {0}".format(mo.dn))
                delete_mo(mo)
        else:
            moDir.logout()
            exit("Aborted")
    else:
        print ("Exiting ...")

else:
    moDir.logout()
    exit("wrong value")

moDir.logout()
