# -*- coding: UTF-8 -*-
import os
import re
import sys
import time
import json
import getopt
import shutil

__author__ = 'Bingo'


def usage():
    eg = """\t\tFile Transaction Tool Man Info.\t\t
NAME
    file_transaction - a configration files transaction commit tool.
DESCRIPTION
    This tool is used to set the content of the file and modify the batch configuration file.
    The modification actions are atomic, successful or failed together;
    The tool relies on a JSON configuration file,
    which specifies the operation steps and parameters of specific files.

    You can specify a transaction name when BeginTrans/Commit/RollBack transactions,
    In this way, the current transaction will not be affected by other transaction processes.
    If the transaction name is not specified, it is considered as a global transaction,
    and multiple processes may affect each other when global transactions occur at the same time.

USAGE
    python3 file_transaction.py -c BeginTrans [trans_name]
    python3 file_transaction.py -f example.json -t ACTION1 [-p param1|param2] [trans_name]
    python3 file_transaction.py -f example.json -t ACTION2 [-p param1|param2] [trans_name]
    python3 file_transaction.py -c Commit [trans_name]
    python3 file_transaction.py -c RollBack [trans_name] \n"""
    sys.stderr.write(eg)


class Util:

    @classmethod
    def is_sublist(cls, a, b):
        return set(a).issubset(set(b))

    @classmethod
    def chown(cls, path):
        shutil.chown(path, user='ubp', group='ubpsysm')
        os.chmod(path, 0o750)

    @classmethod
    def mkdir(cls, path):
        os.mkdir(path)
        cls.chown(path)

    @classmethod
    def rmdir(cls, path):
        shutil.rmtree(path)

    @classmethod
    def write_to_file(cls, filename, info):
        with open(filename, 'w') as f:
            f.write(info)
        cls.chown(filename)

    @classmethod
    def write_append_file(cls, filename, infos):
        with open(filename, 'a+') as f:
            f.write(infos + '\n')
        cls.chown(filename)

    @classmethod
    def copy_to(cls, srcfile, dst):
        # if not os.path.isfile(srcfile):
        #    return False
        if not os.path.isdir(dst):
            os.makedirs(dst)
        dstfile = os.path.join(dst, os.path.basename(srcfile))
        shutil.copy2(srcfile, dstfile)
        Util.chown(dstfile)

    @classmethod
    def copy_file(cls, srcfile, dstfile):
        dst_dir = os.path.dirname(dstfile)
        if not os.path.isdir(dst_dir):
            cls.mkdir(dst_dir)
        shutil.copyfile(srcfile, dstfile)

    @classmethod
    def file_uniq(cls, filepath):
        uniq_lines = set()
        with open(filepath, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line not in uniq_lines:
                uniq_lines.add(line)
        new_lines = '\n'.join(list(uniq_lines))
        cls.write_to_file(filepath, new_lines+'\n')


class Logger:

    @classmethod
    def _get_time(cls):
        ct = time.time()
        msec = (ct - int(ct)) * 1000
        return '%s.%03d' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), msec)

    @classmethod
    def info(cls, info):
        print('[INFO ] %s: %s' % (cls._get_time(), info))

    @classmethod
    def warn(cls, info):
        print('[WARN ] %s: %s' % (cls._get_time(), info))

    @classmethod
    def error(cls, info):
        print('[ERROR] %s: %s' % (cls._get_time(), info))


class Env:
    _base = '/home/ubp/.file_transaction'
    _default_trans = 'GLOBAL_TRANS'
    _trans_name = ''
    _base_trans = ''
    _base_bak = ''
    _trans_dir = ''
    _bak_dir = ''
    _bak_info = ''
    _commit_info = ''
    _commit_list = ''
    _bak_list = ''

    @classmethod
    def translate(cls, trans_name):
        return trans_name if trans_name else cls._default_trans

    @classmethod
    def init_path(cls, trans_name):
        cls._trans_name = trans_name
        cls._base_trans = os.path.join(cls._base, 'trans')
        cls._base_bak = os.path.join(cls._base, 'backup')
        cls._trans_dir = os.path.join(cls._base_trans, trans_name)
        cls._bak_dir = os.path.join(cls._base_bak, trans_name)
        cls._commit_list = os.path.join(cls._base_trans, 'commit_list.ini')
        cls._bak_list = os.path.join(cls._base_bak, 'backup_list.ini')

    @classmethod
    def init_trans(cls):
        for path in [cls._base, cls._base_trans, cls._base_bak]:
            if not os.path.exists(path):
                Util.mkdir(path)

    @classmethod
    def init_action(cls, tag_name, conf_path):
        cls._commit_info = " ".join([cls._trans_name, tag_name, conf_path])

    @classmethod
    def init_commit(cls):
        if not os.path.isdir(cls._bak_dir):
            Util.mkdir(cls._bak_dir)

    @classmethod
    def record_in_trans(cls):
        Util.mkdir(cls._trans_dir)
        try:
            Util.mkdir(cls._bak_dir)
        except:
            pass

    @classmethod
    def record_in_action(cls):
        # Record a list of commits required
        Util.write_append_file(cls._commit_list, cls._commit_info)

    @classmethod
    def record_in_commit(cls):
        Util.write_to_file(cls._commit_list, '')
        Util.write_append_file(cls._bak_list, cls._bak_info.strip())
        Util.file_uniq(cls._bak_list)
        Util.rmdir(cls._trans_dir)

    @classmethod
    def is_in_trans(cls):
        return os.path.exists(cls._trans_dir)

    @classmethod
    def is_in_action(cls):
        if not cls.is_in_trans():
            return False
        if not os.path.isfile(cls._commit_list):
            return False
        with open(cls._commit_list, 'r') as f:
            commit_lines = f.readlines()
        ret = False
        try:
            for line in commit_lines:
                if cls._trans_name == line.split()[0]:
                    ret = True
                    break
        except:
            ret = False
        return ret

    @classmethod
    def is_in_commit(cls):
        if not os.path.isfile(cls._bak_list):
            return False
        with open(cls._bak_list, 'r') as f:
            backup_lines = f.readlines()
        ret = False
        try:
            for line in backup_lines:
                if cls._trans_name == line.split()[0]:
                    ret = True
                    break
        except:
            ret = False
        return ret

    @classmethod
    def rollback(cls):
        with open(cls._bak_list, 'r') as f:
            backup_lines = f.readlines()
        left_lines = []
        for line in backup_lines:
            line = line.strip()
            try:
                trans, conf = line.split()
                if cls._trans_name != trans:
                    left_lines.append(line)
                    continue
                Logger.info("rollback: %s" % conf)
                name = os.path.basename(conf)
                Util.copy_file(os.path.join(cls._bak_dir, name), conf)
            except Exception as e:
                Logger.error("RollBackError: %s" % e)
                continue
        new_lines = '\n'.join(left_lines)+'\n' if left_lines else ''
        Util.write_to_file(cls._bak_list, new_lines)
        Util.rmdir(cls._bak_dir)

    @classmethod
    def get_commit_list(cls):
        out_list = []
        with open(cls._commit_list, 'r') as f:
            commit_lines = f.readlines()
        try:
            for line in commit_lines:
                trans, tag, conf = line.split()
                if trans == cls._trans_name:
                    out_list.append((tag, conf))
        except:
            Logger.error("format of %s is invalid" % cls._commit_list)
            out_list = []
        return out_list

    @classmethod
    def get_script_path(cls, tag_name):
        return "%s/%s.sh" % (cls._trans_dir, tag_name)

    @classmethod
    def backup_conf(cls, conf_path):
        Util.copy_to(conf_path, cls._bak_dir)
        cls._bak_info += "%s %s\n" % (cls._trans_name, conf_path)


class Actor:
    _param_list = []
    _bash_lines = ''

    @classmethod
    def do_action(cls, tag_name, config_path, action_list, param_str):
        head = """#!/bin/bash\nconf_path=%s""" % config_path
        cls.append_lines(head)
        try:
            cls._param_list = param_str.split('|')
            for action in action_list:
                cls.combine_shell(action)
        except Exception as e:
            Logger.error("DoActionError: %s" % e)
            return False
        # build script
        # Logger.info("cat shell:\n%s" % cls._bash_lines)
        script_path = Env.get_script_path(tag_name)
        Util.write_to_file(script_path, cls._bash_lines)
        return True

    @classmethod
    def do_commit(cls, trans_name):
        commit_list = Env.get_commit_list()
        conf_list, script_list = [], []
        try:
            for info_tuple in commit_list:
                tag_name, conf_path = info_tuple
                script_path = Env.get_script_path(tag_name)
                if not os.access(conf_path, os.R_OK | os.W_OK):
                    raise Exception("%s is can't access" % conf_path)
                if not os.access(script_path, os.X_OK):
                    raise Exception("%s is can't executable" % script_path)
                conf_list.append(conf_path)
                script_list.append(script_path)
        except Exception as e:
            Logger.error("DoCommitError: %s" % e)
            return False
        # Logger.info("Execute %s" % script_list)
        [Env.backup_conf(conf) for conf in conf_list]
        [os.system("sh %s" % script) for script in script_list]
        return True

    @classmethod
    def combine_shell(cls, action):
        operate, match_want = action
        if not isinstance(match_want, list):
            raise Exception("%s match_want is not list" % operate)
        # Logger.info("op: %s, match_want: %s" % (operate, match_want))
        line = ""
        if operate == 'cover_write':
            want = cls.param_convert(match_want[0])
            line = "echo '%s' >${conf_path}" % want
        elif operate == 'append_line':
            want = cls.param_convert(match_want[0])
            line = "echo '%s' >>${conf_path}" % want
        elif operate == 'delete_line':
            want = cls.param_convert(match_want[0])
            line = "sed -i '/%s/d' ${conf_path}" % want
        elif operate == 'update_line':
            match = cls.param_convert(match_want[0])
            want = cls.param_convert(match_want[1])
            line = "sed -i 's/%s/%s/g' ${conf_path}" % (match, want)
        elif operate == 'insert_after':
            match = cls.param_convert(match_want[0])
            want = cls.param_convert(match_want[1])
            line = "sed -i '/%s/a\%s' ${conf_path}" % (match, want)
        elif operate == 'insert_before':
            match = cls.param_convert(match_want[0])
            want = cls.param_convert(match_want[1])
            line = "sed -i '/%s/i\%s' ${conf_path}" % (match, want)
        elif operate == 'delete_after':
            want = cls.param_convert(match_want[0])
            line = "sed -i '/%s/{n;d}' ${conf_path}" % want
        elif operate == 'delete_before':
            want = cls.param_convert(match_want[0])
            line = "sed -i '$!N;/\\n.*%s/!P;D' ${conf_path}" % want
        elif operate == 'rewrite_after':
            match = cls.param_convert(match_want[0])
            want = cls.param_convert(match_want[1])
            line = "sed -i -e '/%s/{n;d}' -e '/%s/a\%s' ${conf_path}" % (match, match, want)
        elif operate == 'rewrite_before':
            match = cls.param_convert(match_want[0])
            want = cls.param_convert(match_want[1])
            line = "sed -i -e '$!N;/\\n.*%s/!P;D' -e '/%s/i\%s' ${conf_path}" % (match, match, want)
        else:
            Logger.warn("Not support operate: %s, ignore..." % operate)
        if line:
            cls.append_lines(line)

    @classmethod
    def param_convert(cls, in_str):
        """
        Parameter conversion, if the actual number of incoming
        parameters is less than the required number,
        fill in the empty
        """
        out_str = ''
        split_list = re.split('{P\d}', in_str)
        if len(split_list) == 1:
            return in_str
        param_count, split_len = len(cls._param_list), len(split_list)
        for index in range(split_len):
            # The actual parameter value is appended when the
            # number of arguments is greater than the index
            # and not the last element of split_list
            if index < param_count and index != (split_len - 1):
                param = cls._param_list[index]
            else:
                param = ''
            out_str = out_str + split_list[index] + param
        return out_str

    @classmethod
    def append_lines(cls, line):
        _line = line + '\n'
        cls._bash_lines += _line


class JsonManager:
    _action_list = []
    _conf_path = ''
    _params_str = ''
    _tag_name = ''

    @classmethod
    def parser(cls, param_tuple):
        try:
            json_path, tag, cls._params_str = param_tuple
            with open(json_path, 'r', encoding='UTF-8') as f:
                data_dict = json.load(f)[tag]
                cls._conf_path = data_dict["Path"]
                cls._tag_name = tag
                # No need to verify if the file exists
                for each in data_dict["Action"]:
                    (action, value_list), = each.items()
                    cls._action_list.append((action, value_list))
        except Exception as e:
            Logger.error("JsonParserError: %s" % e)
            return False
        return True

    @classmethod
    def tag_infos(cls):
        out = (cls._tag_name,
               cls._conf_path,
               cls._action_list,
               cls._params_str
               )
        return out


class OptManager:
    _opts_dict = {}
    _is_begintrans = False
    _is_action = False
    _is_commit = False
    _is_rollback = False
    _trans_name = ''

    @classmethod
    def parser(cls):
        try:
            opts_list, args_list = getopt.getopt(sys.argv[1:], "c:f:t:p:")
            cls._opts_dict = {tup[0]: tup[1] for tup in opts_list}
            cls.check_valid(args_list)
        except Exception as e:
            Logger.error("OptManagerError: %s" % e)
            usage()
            return False
        return True

    @classmethod
    def check_valid(cls, args_list):
        if not cls._opts_dict:
            raise Exception("miss necessary params")
        if args_list:
            cls._trans_name = args_list[0].strip()
        if "-c" in cls._opts_dict:
            if len(cls._opts_dict) > 1:
                raise Exception("-c option can't be with another option")
            cmd_val = cls._opts_dict['-c']
            if cmd_val == "BeginTrans":
                cls._is_begintrans = True
            elif cmd_val == "Commit":
                cls._is_commit = True
            elif cmd_val == "RollBack":
                cls._is_rollback = True
            else:
                raise Exception("not support -c %s" % cmd_val)
        elif Util.is_sublist(["-f", "-t"], list(cls._opts_dict.keys())):
            cls._is_action = True
            if '-p' not in cls._opts_dict:
                cls._opts_dict['-p'] = ""
        else:
            raise Exception("Action must contain '-f' and '-t' options")

    @classmethod
    def is_begintrans(cls):
        return cls._is_begintrans

    @classmethod
    def is_action(cls):
        return cls._is_action

    @classmethod
    def is_commit(cls):
        return cls._is_commit

    @classmethod
    def is_rollback(cls):
        return cls._is_rollback

    @classmethod
    def get_trans_name(cls):
        return cls._trans_name

    @classmethod
    def get_action_opts(cls):
        opts = cls._opts_dict
        out = (opts['-f'], opts['-t'], opts['-p'])
        return out


class Entry(object):
    _finish_success = 0
    _opts_fail_errno = 1
    _in_trans_errno = 2
    _not_trans_errno = 3
    _json_fail_errno = 4
    _action_fail_errno = 5
    _not_action_errno = 6
    _commit_fail_errno = 7
    _not_commit_errno = 8
    _exception_errno = 9

    def beginTrans(self, trans_name):
        Env.init_trans()
        if Env.is_in_trans():
            Logger.error("%s is already in transaction" % trans_name)
            return self._in_trans_errno
        Logger.info("begin transaction for %s" % trans_name)
        Env.record_in_trans()
        return self._finish_success

    def action(self, trans_name, cmd_tuple):
        if not Env.is_in_trans():
            Logger.error("%s isn't begin transaction yet" % trans_name)
            return self._not_trans_errno
        if not JsonManager.parser(cmd_tuple):
            return self._json_fail_errno
        tag_name, conf_path, actions, param = JsonManager.tag_infos()
        Logger.info("start %s actions for %s" % (tag_name, trans_name))
        Env.init_action(tag_name, conf_path)
        if not Actor.do_action(tag_name, conf_path, actions, param):
            return self._action_fail_errno
        Env.record_in_action()
        return self._finish_success

    def commit(self, trans_name):
        if not Env.is_in_action():
            Logger.error("%s isn't start actions yet" % trans_name)
            return self._not_action_errno
        Logger.info("start commit for %s" % trans_name)
        Env.init_commit()
        if not Actor.do_commit(trans_name):
            return self._commit_fail_errno
        Env.record_in_commit()
        return self._finish_success

    def rollback(self, trans_name):
        if not Env.is_in_commit():
            Logger.error("%s isn't commit yet" % trans_name)
            return self._not_commit_errno
        Logger.info("start rollback for %s" % trans_name)
        Env.rollback()

    def enter_gate(self):
        if not OptManager.parser():
            return self._opts_fail_errno
        trans_name = Env.translate(OptManager.get_trans_name())
        Env.init_path(trans_name)
        try:
            if OptManager.is_begintrans():
                return self.beginTrans(trans_name)
            elif OptManager.is_action():
                return self.action(trans_name, OptManager.get_action_opts())
            elif OptManager.is_commit():
                return self.commit(trans_name)
            elif OptManager.is_rollback():
                return self.rollback(trans_name)
        except Exception as e:
            Logger.error("Exception: %s" % e)
            return self._exception_errno
        return self._finish_success

    def for_import(self):
        pass


if __name__ == "__main__":
    sys.exit(Entry().enter_gate())

