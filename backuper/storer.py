
import easywebdav
import ntpath

import datetime

import logging

class BackupStorer(object) :
    settings = {}
    path = '/'

    def __init__(self):
        return

    def store(self, fname, date=None, time=None, folder=None) :
        raise NotImplementedError("Call an abstract method")

    def manageStorage(self) :
        raise NotImplementedError("Call an abstract method")


class BackupStorerYandexDisk(BackupStorer) :
    webdav = None

    def setDomain(self, domain) :
        self.settings['domain'] = domain

    def setUsername(self, username) :
        self.settings['username'] = username

    def setPassword(self, password) :
        self.settings['password'] = password

    def setProtocol(self, protocol) :
        self.settings['protocol'] = protocol

    def setCertificate(self, cert) :
        self.settings['cert'] = cert

    def setDaysLeft(self, left_days) :
        self.settings['left_days'] = left_days

    def setManageEnabled(self, enabled) :
        self.settings['manage_enabled'] = enabled

    def setPath(self, path) :
        self.path = path
        if (self.path[-1] != '/') :
            self.path = "%s/" % (self.path,)

    def init(self) :
        if ('cert' in self.settings.keys()) :
            self.webdav = easywebdav.connect(self.settings['domain'], 
                                        username=self.settings['username'], 
                                        password=self.settings['password'], 
                                        protocol=self.settings['protocol'],
                                        cert=self.settings['cert']
                                        )
        else :
            self.webdav = easywebdav.connect(self.settings['domain'], 
                                        username=self.settings['username'], 
                                        password=self.settings['password'], 
                                        protocol=self.settings['protocol']
                                        )
        

    def store(self, fname, nowDate, nowTime, folder=None) :
        if not self.webdav :
            self.init()

        folderDate = "%s%s" % (self.path, nowDate)
        if folder :
            subfolder = "%s%s/%s" % (self.path, nowDate, folder)
            folderTime = "%s%s/%s/%s" % (self.path, nowDate, folder, nowTime)
        else :
            subfolder = "%s%s/%s" % (self.path, nowDate, nowTime)
            folderTime = "%s%s/%s" % (self.path, nowDate, nowTime)

        # folder like Date
        if not self.webdav.exists(folderDate) :
            self.webdav.mkdir(folderDate)
            logging.info("WEBDAV: dir %s created" % (folderDate,))

        #subfolder if specified
        if folder and not self.webdav.exists(subfolder) :
            self.webdav.mkdir(subfolder)
            logging.info("WEBDAV: dir %s created" % (subfolder,))
        
        #folder like Time
        if not self.webdav.exists(folderTime) :
            self.webdav.mkdir(folderTime)
            logging.info("WEBDAV: dir %s created" % (folderTime,))

        localFname = ntpath.basename(fname)
        remoteFname = "%s/%s" % (folderTime, localFname)
        logging.info("uploading file: %s -> %s" % (fname, remoteFname))
        self.webdav.upload(fname, remoteFname)
        logging.info("upload completed: %s -> %s" % (fname, remoteFname))

        return remoteFname

    def manageStorage(self) :
        if (not self.settings['manage_enabled']) :
            return
        if not self.webdav :
            self.init()
        logging.info("LEFT SPACE MANAGEMENT")
        logging.info("planned to left %s days" % (self.settings['left_days'],))
        now = datetime.datetime.now()
        logging.info("now: %s" % (now,))
        nowDate = now.strftime("%Y%m%d")
        logging.info("nowDate: %s" % (nowDate,))
        logging.info("path: %s, webdav: %s" % (self.path, self.webdav))
        days = self.webdav.ls('/')
        logging.info("ls done")
        #logging.info("days dirs: %s" % (days,))
        #currDay = int(nowDate)
        currDay = datetime.date(int(nowDate[0:4]), int(nowDate[4:6]), int(nowDate[6:8]))
        logging.info("currDay: %s" % (currDay,))
        
        for file in days :
            if (file.name != '/') :
                day = file.name.replace('/', '')
                #logging.info("testing folder by date: %s" % (day,))
                dayBup = None
                try :
                    dayBup = datetime.date(int(day[0:4]), int(day[4:6]), int(day[6:8]))
                    #logging.info("dayBup: %s" % (dayBup,))
                except ValueError :
                    #logging.info("unexpected day, skipped: %s, %s" % (file.name, day))
                    continue
                dd = str(currDay - dayBup)
                #logging.info("%s" % (dd,))
                try: 
                    period = int(dd.split()[0])
                    if (period > int(self.settings['left_days'])) :
                        logging.info("deleting remote folder: %s" % (file.name,))
                        self.webdav.rmdir(file.name)
                    else :
                        logging.info("skipping remote folder: %s" % (file.name,))
                        #continue
                except :
                    pass

        logging.info("store management done")