#!/usr/bin/env python
# encoding: utf-8
"""
这个文件中记录了所有的全局静态配置变量。现在只有named.conf所属路径和nameddb目录存储路径。
"""

# 安装路径，是否能传进来？暂时写成根据相对路径
import os
import platform
import pwd
import sys

system, _, release, version, machine, processor = platform.uname()
system, release, version = platform.system_alias(system, release,version)

installdir = os.path.dirname(os.path.realpath(__file__)) + "/.."
# 这里记录了bind启动的chroot根目录
chroot_path = "/var/named"
# 这里记录了named.conf所存储的路径
namedconf = "/etc/namedb"

if (system == 'Darwin'):
    #操作系统为Mac OSX
    chroot_path = "/"
    namedconf = "/etc"
    named_user = "root"
    if (release == '9.1.0'):
        pass
elif (system == "FreeBSD"):
    #操作系统为FreeBSD
    chroot_path = "/var/named"
    namedconf = "/etc/namedb"
    named_user = "bind"
    if (release[:3] == "6.2"):
        pass
    elif (release[:3] == "7.0"):
        pass
elif (system == "OpenBSD"):
    # 操作系统为OpenBSD
    named_user = "named"
    chroot_path = "/var/named"
    namedconf = "/etc"
    if (release[:3] ==  "4.2"):
        pass
elif (system == "Linux"):
    # 操作系统为Linux
    named_user = "bind"
    chroot_path = "/"
    namedconf = "/etc/bind"
try:
    named_uid = pwd.getpwnam(named_user)[2]
except KeyError:
    print "No such a user %s. I'll exit."%named_user
    sys.exit(errno.EINVAL)
        
default_acl = dict(internal=('127.0.0.1', '10.217.24.0/24'))
filename_map = dict(acl='acl/acldef.conf', defzone='defaultzone.conf')

