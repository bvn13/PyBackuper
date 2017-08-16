# PyBackuper

```
> python backuper.py
WRONG MODE: choose watcher/worker
```

WATCHER mode:
```
> python backuper.py watcher
usage: backuper watcher [-h] -s
backuper watcher: error: the following arguments are required: -s/--start
```

WORKER mode
```
> python backuper.py worker
usage: backuper worker [-h] -t type [-db database] [-c]
backuper worker: error: the following arguments are required: -t/--type
```