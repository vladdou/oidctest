import json
import logging
import os
import tarfile
from urllib import quote_plus

from aatest.check import END_TAG, STATUSCODE
from oic.utils.time_util import in_a_while

__author__ = 'roland'


def setup_logging(logfile, log):
    hdlr = logging.FileHandler(logfile)
    base_formatter = logging.Formatter(
        "%(asctime)s %(name)s:%(levelname)s %(message)s")

    hdlr.setFormatter(base_formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)


def mk_tardir(issuer, test_profile):
    wd = os.getcwd()

    tardirname = wd
    for part in ["tar", issuer, test_profile]:
        tardirname = os.path.join(tardirname, part)
        if not os.path.isdir(tardirname):
            os.mkdir(tardirname)

    logdirname = os.path.join(wd, "log", issuer, test_profile)
    for item in os.listdir(logdirname):
        if item.startswith("."):
            continue

        ln = os.path.join(logdirname, item)
        tn = os.path.join(tardirname, "{}.txt".format(item))
        if not os.path.isfile(tn):
            os.symlink(ln, tn)


def create_tar_archive(issuer, test_profile):
    mk_tardir(issuer, test_profile)

    wd = os.getcwd()
    _dir = os.path.join(wd, "tar", issuer)
    os.chdir(_dir)

    tar = tarfile.open("{}.tar".format(test_profile), "w")

    for item in os.listdir(test_profile):
        if item.startswith("."):
            continue

        fn = os.path.join(test_profile, item)

        if os.path.isfile(fn):
            tar.add(fn)
    tar.close()
    os.chdir(wd)


def not_logging(logfile, logger):
    hdlr = logging.FileHandler(logfile)
    base_formatter = logging.Formatter(
        "%(asctime)s %(name)s:%(levelname)s %(message)s")

    hdlr.setFormatter(base_formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)


def get_test_info(session, test_id):
    return session["test_info"][test_id]


def with_or_without_slash(path):
    if os.path.isdir(path):
        return path

    if path.endswith("%2F"):
        path = path[:-3]
        if os.path.isdir(path):
            return path
    else:
        path += "%2F"
        if os.path.isdir(path):
            return path

    return None


def log_path(session, test_id=None):
    _conv = session["conv"]

    try:
        iss = _conv.client.provider_info["issuer"]
    except TypeError:
        return ""
    else:
        qiss = quote_plus(iss)

    path = with_or_without_slash(os.path.join("log", qiss))
    if path is None:
        path = os.path.join("log", qiss)

    prof = ".".join(to_profile(session))

    if not os.path.isdir("%s/%s" % (path, prof)):
        os.makedirs("%s/%s" % (path, prof))

    if test_id is None:
        test_id = session["testid"]

    return "%s/%s/%s" % (path, prof, test_id)


RT = {"C": "code", "I": "id_token", "T": "token"}
OC = {"T": "config", "F": "no-config"}
REG = {"T": "dynamic", "F": "static"}
CR = {"n": "none", "s": "sign", "e": "encrypt"}
EX = {"+": "extras"}
ATTR = ["response_type", "openid-configuration", "registration", "crypto",
        "extras"]


def to_profile(session, representation="list"):
    p = session["profile"].split(".")
    prof = [
        "+".join([RT[x] for x in p[0]]),
        "%s" % OC[p[1]],
        "%s" % REG[p[2]]]

    try:
        prof.append("%s" % "+".join([CR[x] for x in p[3]]))
    except KeyError:
        pass
    else:
        try:
            prof.append("%s" % EX[p[4]])
        except (KeyError, IndexError):
            pass

    if representation == "list":
        return prof
    elif representation == "dict":
        ret = {}
        for r in range(0, len(prof)):
            ret[ATTR[r]] = prof[r]

        if "extras" in ret:
            ret["extras"] = True
        return ret


def get_profile_info(session, test_id=None):
    try:
        _conv = session["conv"]
    except KeyError:
        pass
    else:
        try:
            iss = _conv.client.provider_info["issuer"]
        except TypeError:
            iss = ""

        profile = to_profile(session, "dict")

        if test_id is None:
            try:
                test_id = session["testid"]
            except KeyError:
                return {}

        return {"Issuer": iss, "Profile": profile,
                "Test ID": test_id,
                "Test description": session["node"].desc,
                "Timestamp": in_a_while()}

    return {}
