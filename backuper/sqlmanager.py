
from pymssql import _mssql


class SQLManager(object) :

    commandTemplate = "EXEC dbo.sp_BackupDatabases @databaseName='%dbname%',@backupLocation='%path%', @backupType='%type%'"
    server = 'localhost'
    username = ''
    password = ''

    def setServer(self, server) :
        self.server = server

    def setUsername(self, username) :
        self.username = username

    def setPassword(self, password) :
        self.password = password


    def makeBackup(self, database, type, path) :
        print("making backup: %s" % (database,))
        command = self.commandTemplate \
                        .replace("%dbname%", database) \
                        .replace("%type%", type) \
                        .replace("%path%", path)
        with _mssql.connect(server=self.server, user=self.username, password=self.password, database=database) as db :
            db.execute_non_query(command)