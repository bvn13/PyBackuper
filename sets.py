
settings = {

    'email' : {
        'LOGIN' : "user@yandex.ru",
        'EMAIL' : "user@yandex.ru",
        'SMTP' : "smtp.yandex.ru",
        'PORT' : 465,
        'PASS' : "password",
    },

    'log' : 'backuper.log',

    'admins' : [
        'report@gmail.com',
    ],

    'storers' : {
        'ya_disk' : {
            'left_days' : '5',
            'path' : '/',
            'account' : {
                'domain' : 'webdav.yandex.ru',
                'protocol' : 'https',
                'username' : 'user@yandex.ru',
                'password' : 'password',
            },
        },
    },

    'storer' : 'ya_disk',

    'sql' : {
        'server' : 'localhost',
        'username' : 'sa',
        'password' : 'pass_for_sa',
        'databases' : ['ou', 'hrm', 'buh', 'buh_fo'],
    },

    #'local_path' : 'E:\\ftp\\bvn13\\1\\',
    'local_path' : 'D:\\dev\\bup2yadisk\\',

    'watcher' : {
        'path' : 'D:\\dev\\bup2yadisk\\',
        'dir_full' : 'full',
        'dir_diff' : 'diff',
    },

    'file_mask' : '*.bak',

    'zip' : {
        'make' : 'no',
    },

    'path' : {
        #'local' : 'E:\\backup_1C\\sql\\', #ends with slash
        'local' : 'E:\\ftp\\bvn13\\1\\',
        'remote' : '/', #ends with slash
        'fmask' : '*.bak',
        'allmask' : '*.bak',
    },


    
    
}