
import glob
import easywebdav
import datetime
import ntpath
from zipfile import ZipFile as ZipFile
from pymssql import _mssql
import os

import pprint

from settings import settings


now = datetime.datetime.now()
nowDate = now.strftime("%Y%m%d")
nowTime = now.strftime("%H%M%S")
print("now: %s %s" % (nowDate, nowTime))


def getLocalFiles(dbname="") :
    return (glob.glob("%s%s%s" % (settings['path']['local'], dbname, settings['path']['fmask'])))

def zipFiles(files) :
    newFiles = []
    for fname in files :
        zipFname = "%s.zip" % (fname,)
        print("creating zip: %s" % (zipFname,))
        with ZipFile(zipFname, mode="w") as fzip :
            print(" - adding file: %s" % (fname,))
            fzip.write(fname)
            fzip.close()
            newFiles.append(zipFname)
        print("deleting source file: %s" % (fname,))
        os.remove(fname)
    return newFiles

def uploadFiles(webdav, locFiles) :
    global now, nowDate, nowTime

    print("UPLOADING FILES")
    #pprint.pprint(webdav.ls('/'))

    folderDate = "%s%s" % (settings['path']['remote'], nowDate)
    folderTime = "%s%s/%s" % (settings['path']['remote'], nowDate, nowTime)

    # folder like Date
    if not webdav.exists(folderDate) :
        webdav.mkdir(folderDate)
        print("WEBDAV: dir %s created" % (folderDate,))

    #folder like Time
    if not webdav.exists(folderTime) :
        webdav.mkdir(folderTime)
        print("WEBDAV: dir %s created" % (folderTime,))
    
    for file in locFiles :
        fname = ntpath.basename(file)
        remoteFname = "%s/%s" % (folderTime, fname)
        print("uploading file: %s -> %s" % (fname, remoteFname))
        webdav.upload(file, remoteFname)

def leftRemoteSpaceManagement(webdav) :
    global now, nowDate, nowTime

    print("LEFT SPACE MANAGEMENT")
    print("planned to left %s days" % (settings['space']['left_days'],))

    days = webdav.ls(settings['path']['remote'])
    currDay = int(nowDate)

    for file in days :
        if (file.name != '/') :
            day = file.name.replace('/', '')
            iDay = 0
            try :
                iDay = int(day)
            except ValueError :
                print("unexpected day, skipped: %s, %s" % (file.name, day))
                continue
            if (currDay - iDay > int(settings['space']['left_days'])) :
                print("deleting remote folder: %s" % (file.name,))
                webdav.rmdir(file.name)
            else :
                print("skipping remote folder: %s" % (file.name,))
    return

def backupDatabase(dbname) :
    print("making backup: %s" % (dbname,))
    command = settings['sql']['command_full']['query'].replace("%dbname%", dbname).replace("%path%", settings['path']['local'])
    with _mssql.connect(server="localhost", user=settings['sql']['username'], password=settings['sql']['password'], database=dbname) as db :
        db.execute_non_query(command)
    return

def deleteOldLocalBackups() :
    print("deleting old backups")
    for fname in glob.glob("%s%s" % (settings['path']['local'], settings['path']['allmask'])) :
        name = fname
        if (settings['zip']['make'] == 'yes') :
            name = "%s.zip" % (name,)
        os.remove(name)
        print(" - deleted: %s" % (name,))
    return

def do() :

    deleteOldLocalBackups()

    webdav = easywebdav.connect(settings['account']['domain'], username=settings['account']['login'], password=settings['account']['pass'], protocol=settings['account']['protocol'])
    
    for dbname in settings['sql']['databases'] :
        backupDatabase(dbname)
        locFiles = getLocalFiles(dbname)
        if len(locFiles) == 0 :
            print("ERROR: cound not find expected backup of database: %s" % (dbname,))
            continue
        if (settings['zip']['make'] == 'yes') :
            locFiles = zipFiles(locFiles)
        uploadFiles(webdav, locFiles)

    #at last
    leftRemoteSpaceManagement(webdav)

    return

if __name__ == '__main__':
    print("starting backup")
    do()
    print("ended")