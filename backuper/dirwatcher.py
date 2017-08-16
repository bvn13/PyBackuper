import os
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import threading

import logging

_MAX_CHECKS_BY_TIMER = 5


class FileSystemEventHandler(PatternMatchingEventHandler) :
    checkAvailability = True
    onCreated = None
    onModified = None
    
    def isFileAvailable(self, filename) :
        logging.info("CHECK: %s" % (filename,))
        if os.path.exists(filename) :
            try :
                os.rename(filename, filename)
                return True
            except OSError :
                return False
        return False


    def process(self, event, isThread=False) :
        global _MAX_CHECKS_BY_TIMER

        logging.info("PROCESS: %r" % (isThread,))
        doProcess = True

        if self.checkAvailability :
            logging.info("check for file availability: %s" % (event.src_path,))
            if not self.isFileAvailable(event.src_path) :
                logging.info("file is not available: %s" % (event.src_path,))
                if (isThread) :
                    return None

                t = threading.Timer(5, self.process, [event, True])
                t.start()
                doProcess = False

        if doProcess :
            logging.info("file is available: %s" % (event.src_path,))
            logging.info("event_type: %s, onCreated: %s, onModified: %s" % (event.event_type, self.onCreated, self.onModified))
            if event.event_type == 'created' and self.onCreated :
                logging.info("call onCreated")
                return self.onCreated(event.src_path)
            if event.event_type == 'modified' and self.onModified :
                logging.info("call onModified")
                return self.onModified(event.src_path)

    def on_any_event(self, event) :
        logging.info("Any event, type: %s, source: %s, is dir: %r" % (event.event_type, event.src_path, event.is_directory))

        if event.is_directory :
            return None

        return self.process(event)


class DirWatcher(object) :

    onFileCreated = None
    onFileModified = None

    observer = None
    eventHandler = None

    def __init__(self, onFileCreatedHandler=None, onFileModifiedHandler=None) :
        self.onFileCreated = onFileCreatedHandler
        self.onFileModified = onFileModifiedHandler

    def watch(self, path, mask) :
        self.observer = Observer()
        self.eventHandler = FileSystemEventHandler(patterns=[mask], ignore_patterns=[], ignore_directories=True, case_sensitive=True)
        self.eventHandler.onCreated = self.onFileCreated
        self.eventHandler.onModified = self.onFileModified
        self.observer.schedule(self.eventHandler, path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    


#def onFileCreatedHandler(event) :
#    logging.info("Created: %s" % (event.src_path,))


#def onFileModifiedHandler(event) :
#    logging.info("Modified: %s" % (event.src_path,))


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    

    watcher = DirWatcher(onFileCreatedHandler, onFileModifiedHandler)
    watcher.watch(path, "*.bak")

