import easywebdav
import ntpath

import datetime


if __name__ == '__main__' :
	print("START TEST")

	left_days = 150

	webdav = easywebdav.connect('webdav.yandex.ru', 
                                username='user@yandex.ru', 
                                password='passworx', 
                                protocol='https'
                                )

	now = datetime.datetime.now()
	nowDate = now.strftime("%Y%m%d")
	#webdav.cd('/')
	days = webdav.ls('/')
	print("days dirs: %s" % (days,))