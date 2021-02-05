from cobra.mit.session import LoginSession
from cobra.mit.access import MoDirectory
from cobra.mit.request import ClassQuery
from cobra.mit.naming import Dn
import re
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


#######################################################################################################################
# This script takes leaf ID and the port number as input, supported input format for the port id is eth1/x
# please note that multi line cards leaves are not supported so far
# example : leaf id = 120 port id = eth1/1
# based on the provided input the script will tell you whether the port is configured under an interface profile
# if so, you will get the interface profile name, port block name and the associated policy group.
# You will also be informed on whether the port belong to a PC/VPC. Last but not least the script will give you vlan
#  encap's configured on that port (in case you are in Network Centric mode, encap vlan is probably 1:1 mapping to EPG)
#
# Features that will be added in next version :
#       - display name(s) of the EPG for the static path
#       - display objects friendly names instead of DN's
#       - add support for command line args
#######################################################################################################################


def apic_logon(url, username, password):
    my_session = LoginSession(url, username, password)
    modir_local = MoDirectory(my_session)
    modir_local.login()
    return modir_local


def apic_logoff():
    moDir.logout()


def class_query_by_dn(dn):
    print("Appel method Class_Query_by_DN")
    result = moDir.query(ClassQuery(dn))
    return result
    # this returns a list of objects matching the requested class


def get_leaf_prof_dn_by_nodeid(leaf_id):
    cq = ClassQuery('infraNodeBlk')
    result = moDir.query(cq)
    my_results = []

    for key in result:
        if int(key.from_) <= int(leaf_id) <= int(key.to_):
            child = Dn.fromString(format(key.dn))
            my_results.append(format(child.getAncestor(2)))
    return my_results
    # this returns a list of DN as string


def get_int_prof_by_leaf_prof(parm):
    cq = ClassQuery('infraRsAccPortP')
    my_result = []
    result = moDir.query(cq)
    for key in result:
        # temp = format(key.dn)  # this is a string
        child = Dn.fromString(format(key.dn))
        parent = format(child.getAncestor(1))
        if parent == parm:
            my_result.append(key.tDn)
    return my_result
    # this returns a list of interface profiles based attached to a particular switch profile


def get_pg_and_portblock_by_int_prof_from_port_id(parm1, parm2):
    temp = parm2.split("/")
    port = temp[1]
    req = moDir.lookupByClass("infraPortBlk", parentDn=parm1)
    my_result = []
    for key in req:
        if int(key.fromPort) <= int(port) <= int(key.toPort):
            # temp = format(key.dn)
            my_result.append(format(key.dn))
            child = Dn.fromString(format(key.dn))
            parent = format(child.getAncestor(1))  # here I got the port selector DN as a string
            # print self.parent
            req2 = moDir.lookupByClass("infraRsAccBaseGrp", parentDn=parent)  # here I get the Policy group DN
            for pg in req2:
                my_result.append(format(pg.tDn))
                return my_result


def get_epg_staticpaths_from_int_mo(int_mo):
    cq = ClassQuery('fvRsPathAtt')
    cq.propFilter = 'eq(fvRsPathAtt.tDn, "{0}")'.format(int_mo)
    my_result = moDir.query(cq)
    return my_result
    # return list of objects


def get_epg_staticpaths_from_pg_name(pg_name):
    cq = ClassQuery('fvRsPathAtt')
    cq.propFilter = 'wcard(fvRsPathAtt.tDn, "{0}")'.format(pg_name)
    my_result = moDir.query(cq)
    return my_result  # return list of objects


def get_policygroup_type(parm):
    pg_class = Dn.fromString(parm)

    if format(pg_class.moClass) == "<class 'cobra.modelimpl.infra.accbndlgrp.AccBndlGrp'>":
        is_bundle = True
        return is_bundle
    elif format(pg_class.moClass) == "<class 'cobra.modelimpl.infra.accportgrp.AccPortGrp'>":
        is_bundle = False
        return is_bundle


# format port id = eth1/1
def get_mo_for_interface(nodeid, portid):
    cq = ClassQuery('fabricPathEpCont')
    cq.propFilter = 'eq(fabricPathEpCont.nodeId, "{0}")'.format(nodeid)
    cq.subtree = 'children'
    cq.subtreeClassFilter = 'fabricPathEp'
    req = moDir.query(cq)
    for key in req[0].children:
        # children method applied to the query result will return a list of child objects
        # req[0] is fabricPathEpCont (leaf), children are fabricPathEp (ports)
        if key.name == portid:
            return format(key.dn)
            # return a string containing the MO for the requested interface


def get_port_config(leaf_id, port_name):
    found = False
    print ("\n""Querying port {0} on leaf {1} ...".format(leaf_id, port_name))
    step1 = get_leaf_prof_dn_by_nodeid(leaf_id)
    for i in step1:
        step2 = get_int_prof_by_leaf_prof(i)
        for j in step2:
            step3 = get_pg_and_portblock_by_int_prof_from_port_id(j, port_name)
            if step3:
                print ("")
                print ("LEAF PROFILE: ""\t\t""{0}".format(i))
                print ("INTERFACE PROFILE: ""\t""{0}".format(j))
                print ("PORT BLOCK: ""\t\t""{0}".format(step3[0]))
                print ("POLICY GROUP: ""\t\t" "{0}".format(step3[1]))

                if get_policygroup_type(format(step3[1])) is True:
                    print ("This port belongs to a PC/VPC")
                    m = re.search('^uni/infra/funcprof/accbundle-(.*)', format(step3[1]))
                    pg_name = m.group(1)
                    port_paths = get_epg_staticpaths_from_pg_name(pg_name)
                    for h in port_paths:
                        print ("\t\t\t\t\tEncap: {0}, Mode: {1}".format(h.encap, h.mode))

                else:
                    print ("This port DOES NOT belong to any PC/VPC")
                    port_mo = get_mo_for_interface(leaf_id, port_name)
                    port_paths = get_epg_staticpaths_from_int_mo(port_mo)
                    print ("VLAN(s):")
                    for h in port_paths:
                        print ("\t\t\t\t\tEncap: {0}, Mode: {1}".format(h.encap, h.mode))

                found = True

    if found is False:
        print ("--> Port not configured")


moDir = apic_logon('https://sandboxapicdc.cisco.com', 'admin', 'password')

get_port_config(102, "eth1/15")

# my_request = class_query_by_dn(moDir, 'fvRsPathAtt')
# my_request = get_leaf_prof_dn_by_nodeid(101)
# my_request = get_int_prof_by_leaf_prof('uni/infra/nprof-leaf_1')
# my_request = get_pg_and_portblock_by_int_prof_from_port_id('uni/infra/accportprof-Heroes_server1', 21)
# my_request = get_epg_staticpaths_from_int_mo(' topology/pod-1/paths-101/pathep-[eth1/40]')
# my_request = get_mo_for_interface(101, 'eth1/1')

apic_logoff()
