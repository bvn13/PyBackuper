
settings = {
    'path' : {
        #'local' : 'E:\\backup_1C\\sql\\', #ends with slash
        'local' : 'E:\\ftp\\bvn13\\1\\',
        'remote' : '/', #ends with slash
        'fmask' : '*.bak',
        'allmask' : '*.bak',
    },
    'account' : {
        'domain' : 'webdav.yandex.ru',
        'protocol' : 'https',
        'login' : 'user@yandex.ru',
        'pass' : 'pass_for_webdav',
    },
    'space' : {
        'left_days' : '5',
    },
    'zip' : {
        'make' : 'no',
    },
    'sql' : {
        'username' : 'sa',
        'password' : 'pass_for_sa',
        'command_full' : {
            'query' : "EXEC dbo.sp_BackupDatabases @databaseName='%dbname%',@backupLocation='%path%', @backupType='F'",
            'procedure' : "dbo.sp_BackupDatabases",
            #'backupLocation' : 'E:\\backup_1C\\sql\\', #@databaseName='%dbname%',@backupLocation='E:\\backup_1C\\sql\\', @backupType='F'", #two params included!
            'backupType' : 'F',
        },
        'databases' : ['ou', 'hrm', 'buh', 'buh_fo'],
    }
}