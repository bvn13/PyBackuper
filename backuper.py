import os
import sys
import argparse
import glob
import ntpath
import traceback
from zipfile import ZipFile as ZipFile

import datetime

from pprint import pprint

from backuper.storer import BackupStorerYandexDisk
from backuper.sqlmanager import SQLManager
from backuper.dirwatcher import DirWatcher
from backuper.reporter import Reporter

from sets import settings

import threading

import logging


logging.basicConfig(level = logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=settings['log'])

def exception_hook(exc_type, exc_value, exc_traceback):
    logging.error(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

sys.excepthook = exception_hook

#raise Exception('Boom')

version = '0.3.0'


class Backuper(object) :

    storer = None
    sqlManager = None

    localPath = ''
    fileMask = '*'
    makeZip = 'no'

    databases = []

    def init(self, settings) :

        self.fileMask = settings['file_mask']
        self.localPath = settings['local_path']
        self.makeZip = settings['zip']['make']

        storerType = settings['storer']
        storerSettings = settings['storers'][storerType]
    
        if (storerType == 'ya_disk') :
            self.storer = BackupStorerYandexDisk()
            self.storer.setPath(storerSettings['path'])
            self.storer.setDomain(storerSettings['account']['domain'])
            self.storer.setUsername(storerSettings['account']['username'])
            self.storer.setPassword(storerSettings['account']['password'])
            self.storer.setProtocol(storerSettings['account']['protocol'])
        else : 
            raise NotImplementedError("%s storer is not implemented yet" % (storerType,))
        
        sqlSettings = settings['sql']

        self.sqlManager = SQLManager()
        self.sqlManager.setServer(sqlSettings['server'])
        self.sqlManager.setUsername(sqlSettings['username'])
        self.sqlManager.setPassword(sqlSettings['password'])

        self.databases = sqlSettings['databases']
        return


    def getLocalFiles(self, dirname, dbname="") :
        print("file search mask: %s%s/%s/%s" % (self.localPath, dirname, dbname, self.fileMask))
        return (glob.glob("%s%s/%s/%s" % (self.localPath, dirname, dbname, self.fileMask)))


    def deleteOldLocalBackups(self) :
        logging.info("deleting old backups")
        for fname in self.getLocalFiles() : #glob.glob("%s%s" % (self.localPath, self.fileMask)) :
            name = fname
            if (self.makeZip == 'yes') :
                name = "%s.zip" % (name,)
            os.remove(name)
            logging.info(" - deleted: %s" % (name,))

    def zipFiles(files) :
        newFiles = []
        for fname in files :
            zipFname = "%s.zip" % (fname,)
            logging.info("creating zip: %s" % (zipFname,))
            with ZipFile(zipFname, mode="w") as fzip :
                logging.info(" - adding file: %s" % (fname,))
                fzip.write(fname)
                fzip.close()
                newFiles.append(zipFname)
            logging.info("deleting source file: %s" % (fname,))
            os.remove(fname)
        return newFiles


    def backup(self, type='F', database=None, copyOnly=False) :

        dirName = ''
        if (type.upper() == 'F') :
            dirName = 'full'
        elif (type.upper() == 'D') :
            dirName = 'diff'
        elif (type.upper() == 'L') :
            dirName = 'logs'
        else :
            raise NotImplementedError("Unknown type of database backups has been specified")

        #self.deleteOldLocalBackups()

        now = datetime.datetime.now()
        nowDate = now.strftime("%Y%m%d")
        nowTime = now.strftime("%H%M%S")
        logging.info("now: %s %s" % (nowDate, nowTime))

        databases = []

        if not database :
            databases = self.databases
        else :
            databases.append(database)

        for dbname in databases :
            if (not copyOnly) :
                self.sqlManager.makeBackup(dbname, type, self.localPath)

            locFiles = self.getLocalFiles(dirName, dbname)
            if len(locFiles) == 0 :
                logging.info("ERROR: could not find expected backup of database: %s" % (dbname,))
                continue
            if (self.makeZip == 'yes') :
                locFiles = zipFiles(locFiles)

            for file in locFiles :
                self.storer.store(file, nowDate, nowTime, dirName)

        #self.storer.manageStorage(setStorerSettings['left_days'])
        


class Watcher(object) :

    storer = None
    watcher = None
    reporter = None

    watchPath = ''
    dirFullBackup = ''
    dirDiffBackup = ''
    fileMask = '*'
    makeZip = 'no'

    databases = []
    files = set()

    def init(self, settings) :

        #self.fileMask = settings['file_mask']

        self.watchPath = settings['watcher']['path']
        self.dirFullBackup = settings['watcher']['dir_full']
        self.dirDiffBackup = settings['watcher']['dir_diff'] if 'dir_diff' in settings['watcher'] else ''
        self.dirLogsBackup = settings['watcher']['dir_logs'] if 'dir_logs' in settings['watcher'] else ''

        self.makeZip = settings['zip']['make']

        storerType = settings['storer']
        storerSettings = settings['storers'][storerType]
    
        self.reporter = Reporter()
        self.reporter.init(settings)

        if (storerType == 'ya_disk') :
            self.storer = BackupStorerYandexDisk()
            self.storer.setPath(storerSettings['path'])
            self.storer.setDomain(storerSettings['account']['domain'])
            self.storer.setUsername(storerSettings['account']['username'])
            self.storer.setPassword(storerSettings['account']['password'])
            self.storer.setProtocol(storerSettings['account']['protocol'])
            self.storer.setDaysLeft(storerSettings['left_days'])
            self.storer.setManageEnabled(storerSettings['manage_enabled'] == 'true')
        else : 
            raise NotImplementedError("%s storer is not implemented yet" % (storerType,))
        
        return

    def _getCurrentTime(self) :
        now = datetime.datetime.now()
        nowDate = now.strftime("%Y%m%d")
        nowTime = now.strftime("%H")
        minutes = int(now.strftime("%M"))
        if (minutes <= 15) :
            nowTime += "00"
        elif (minutes <= 30) :
            nowTime += "15"
        elif (minutes <= 45) :
            nowTime += "30"
        else :
            nowTime += "45"

        logging.info("now: %s %s" % (nowDate, nowTime))
        return (nowDate, nowTime)

    def onBackupCreated(self, filename) :

        self.storer.manageStorage()

        if not filename in self.files :
            self.files.add(filename)
            logging.info("BACKUP: %s" % (filename,))
            full_path = "%s%s" % (self.watchPath, self.dirFullBackup)
            logging.info("FULL PATH: %s" % (full_path,))
            diff_path = "%s%s" % (self.watchPath, self.dirDiffBackup)
            logging.info("DIFF PATH: %s" % (diff_path,))
            logs_path = "%s%s" % (self.watchPath, self.dirLogsBackup)
            logging.info("LOGS PATH: %s" % (logs_path,))

            if (filename.find(full_path) >= 0) :
                logging.info("FULL BACKUP")

                t1 = threading.Timer(0, self._makeBackup, [filename, "FULL"])
                t1.start()

            elif (self.dirDiffBackup and filename.find(diff_path) >= 0) :
                logging.info("DIFF BACKUP")
                
                t2 = threading.Timer(0, self._makeBackup, [filename, "DIFF"])
                t2.start()

            elif (self.dirLogsBackup and filename.find(logs_path) >= 0) :
                logging.info("LOGS BACKUP")
                
                t2 = threading.Timer(0, self._makeBackup, [filename, "LOGS"])
                t2.start()

            else :
                logging.warning("IGNORING: %s" % (filename,))
        else :
            logging.warning("SKIP DOUBLE TRIGGER FOR: %s" % (filename,))

        return

    def _makeBackup(self, filename, subfolder) :
        (nowDate, nowTime) = self._getCurrentTime()
        #fname = ntpath.basename(filename)
        errortext = ""
        remoteFname = ""
        try :
            remoteFname = self.storer.store(filename, nowDate, nowTime, subfolder)
            self.reporter.report("%s BACKUP SUCCESSFULL" % (subfolder,), "%s BACKUP UPLOADED: %s -> %s" % (subfolder, filename, remoteFname))
            logging.info("%s BACKUP UPLOADED: %s -> %s" % (subfolder, filename, remoteFname))
        except :
            trace = traceback.format_exc()
            self.reporter.report("%s BACKUP ERROR" % (subfolder,), "%s BACKUP UPLOAD ERROR: %s - %s" % (subfolder, filename, trace))
            logging.error("%s BACKUP UPLOAD ERROR: %s -> %s - %s" % (subfolder, filename, remoteFname, trace))

        self.files.remove(filename)
        return

    def start(self) :
        self.watcher = DirWatcher(onFileCreatedHandler=self.onBackupCreated, onFileModifiedHandler=self.onBackupCreated)
        logging.info("Start watching files: %s%s" % (self.watchPath, self.fileMask))
        self.watcher.watch(self.watchPath, self.fileMask)


if __name__ == '__main__':

    verstr = '%%(prog) %s' % (version,)
    description = 'Backup maker. %s' % (verstr,)

    parser = argparse.ArgumentParser(add_help=True, description='Backup Maker', prog='backuper')
    parser.add_argument('-v', '--ver', '--version', action='version', version=version)
    subparsers = parser.add_subparsers()

    parser_watcher = subparsers.add_parser('watcher')
    parser_watcher.add_argument('-s', '--start', required=True, dest='watcher', action='store_true')

    parser_work = subparsers.add_parser('worker')
    parser_work.add_argument('-t', '--type', metavar='type', required=True, type=str, choices=['F', 'D', 'L'], default='F', help='type of database backup to make this time: F - full, D - diff, L - logs')
    parser_work.add_argument('-db', '--database', metavar='database', type=str, help='database name to backup. Will make backups for all databases (from settings) if not specified.')
    parser_work.add_argument('-c', '--copy-only', action='store_true', dest='copy', help='Only copy files to storage')

    args = parser.parse_args()

    #pprint(args)

    if not 'watcher' in args and not 'type' in args :
        print("WRONG MODE: choose watcher/worker")
    else :
        if 'watcher' in args and args.watcher :
            print("WATCH MODE")
            watcher = Watcher()
            watcher.init(settings)
            watcher.start()

        else :
            backuper = Backuper()
            backuper.init(settings)
            if 'database' in args :
                backuper.backup(type=args.type, database=args.database, copyOnly='copy' in args)
            else :
                backuper.backup(type=args.type, copyOnly='copy' in args)
