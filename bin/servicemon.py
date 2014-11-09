#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# Copyright 2002-2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#
"""
This program controls the service monitoring in NAV.
"""
import os
import sys
import types
import time
import getopt
import random
import gc
import threading
import signal

import nav.daemon
from nav.daemon import safesleep as sleep
from nav.statemon import RunQueue
from nav.statemon import abstractChecker
from nav.statemon import config
from nav.statemon import db
from nav.statemon import debug

class controller:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self.conf=config.serviceconf()
        debug.setDebugLevel(int(self.conf.get('debuglevel', 4)))
        self._deamon=kwargs.get("fork", 1)
        self._isrunning=1
        self._checkers=[]
        self._looptime=int(self.conf.get("checkinterval",60))
        debug.debug("Setting checkinterval=%i"% self._looptime)
        self.db=db.db()
        debug.debug("Reading database config")
        debug.debug("Setting up runqueue")
        self._runqueue=RunQueue.RunQueue(controller=self)
        self.dirty = 1


    def getCheckers(self):
        """
        Fetches new checkers from the NAV database and appends them to
        the runqueue.
        """
        newcheckers = self.db.getCheckers(self.dirty)
        self.dirty=0
        # make sure we don't delete all checkers if we get an empty
        # list from the database (maybe we have lost connection to
        # the db)
        if newcheckers:
            s=[]    
            for i in newcheckers:
                if i in self._checkers:
                    oldchecker = self._checkers[self._checkers.index(i)]
                    s.append(oldchecker)
                else:
                    s.append(i)

            self._checkers=s
        elif self.db.status and self._checkers:
            debug.debug("No checkers left in database, flushing list.")
            self._checkers=[]

        #randomiserer rekkef�lgen p� checkerbene
        for i in self._checkers:
            self._checkers.append(self._checkers.pop(int(len(self._checkers)*random.random())))
                    
    def main(self):
        """
        Loops until SIGTERM is caught. The looptime is defined
        by self._looptime
        """
        self.db.start()
        while self._isrunning:
            start=time.time()
            self.getCheckers()

            wait=self._looptime - (time.time() - start)
            if wait <= 0:
                debug.debug("System clock has drifted backwards, resetting loop delay", 2)
                wait = self._looptime
            if self._checkers:
                pause=wait/(len(self._checkers)*2)
            else:
                pause=0
            for checker in self._checkers:
                self._runqueue.enq(checker)
                sleep(pause)

            # extensive debugging
            dbgthreads=[]
            for i in gc.get_objects():
                if isinstance(i, threading.Thread):
                    dbgthreads.append(i)
            debug.debug("Garbage: %s Objects: %i Threads: %i" % (gc.garbage, len(gc.get_objects()), len(dbgthreads)))

            wait=(self._looptime - (time.time() - start))
            debug.debug("Waiting %i seconds." % wait)
            if wait <= 0:
                debug.debug("Only superman can do this. Humans cannot wait for %i seconds." % wait,2)
                wait %= self._looptime
                sleep(wait)
            else:
                sleep(wait)


    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            debug.debug( "Caught SIGTERM. Exiting.")
            self._runqueue.terminate()
            sys.exit(0)
        elif signum == signal.SIGHUP:
            # reopen the logfile
            logfile_path = self.conf.get("logfile", "servicemon.log")
            debug.debug("Caught SIGHUP. Reopening logfile...")
            logfile = file(logfile_path, 'a')
            nav.daemon.redirect_std_fds(stdout=logfile, stderr=logfile)

            debug.debug("Reopened logfile: %s" % logfile_path)
        else:
            debug.debug( "Caught %s. Resuming operation." % (signum))


def start(fork):
    """
    Forks a new prosess, letting the service run as
    a daemon.
    """
    conf = config.serviceconf()
    pidfilename = conf.get("pidfile","servicemon.pid")

    # Already running?
    try:
        nav.daemon.justme(pidfilename)
    except nav.daemon.AlreadyRunningError, e:
        otherpid = file(pidfilename, "r").read().strip()
        sys.stderr.write("servicemon is already running (pid: %s)\n" % otherpid)
        sys.exit(1)
    except nav.daemon.DaemonError, e:
        sys.stderr.write("%s\n" % e)
        sys.exit(1)

    if fork:
        logfile_path = conf.get('logfile','servicemon.log')
        logfile = file(logfile_path, 'a')
        nav.daemon.daemonize(pidfilename, stdout=logfile, stderr=logfile)

    myController=controller(fork=fork)
    myController.main()


def help():
    print """Service monitor for NAV (Network Administration Visualized).

    Usage: %s [OPTIONS]
    -h  --help      Displays this message
    -n  --nofork    Run in foreground
    -v  --version   Display version and exit


Written by Erik Gorset and Magnus Nordseth, 2002

    """  % os.path.basename(sys.argv[0])


if __name__=='__main__':
    # chdir into own dir
    #mydir, myname = os.path.split(sys.argv[0])
    #os.chdir(mydir)
    # Make sure our files are readable for all 
    os.umask(0002)
                                  
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hnv', ['help','nofork', 'version'])
        fork=1

        for opt, val in opts:
            if opt in ('-h','--help'):
                help()
                sys.exit(0)
            elif opt in ('-n','--nofork'):
                fork=0
            elif opt in ('-v','--version'):
                print __version__
                sys.exit(0)
                

    except (getopt.error):
        help()
        sys.exit(2)
                               
    start(fork)
