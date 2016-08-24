import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
import time
from datetime import date, datetime, timedelta
try:    from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
from string import digits

ADDON_ID       = uservar.ADDON_ID
ADDONTITLE     = uservar.ADDONTITLE
ADDON          = xbmcaddon.Addon(ADDON_ID)
VERSION        = ADDON.getAddonInfo('version')
USER_AGENT     = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
DIALOG         = xbmcgui.Dialog()
DP             = xbmcgui.DialogProgress()
HOME           = xbmc.translatePath('special://home/')
LOG            = xbmc.translatePath('special://logpath/')
PROFILE        = xbmc.translatePath('special://profile/')
ADDONS         = os.path.join(HOME, 'addons')
USERDATA       = os.path.join(HOME, 'userdata')
PLUGIN         = os.path.join(ADDONS, ADDON_ID)
PACKAGES       = os.path.join(ADDONS, 'packages')
ADDONDATA      = os.path.join(USERDATA, 'addon_data', ADDON_ID)
ADVANCED       = os.path.join(USERDATA, 'advancedsettings.xml')
SOURCES        = os.path.join(USERDATA, 'sources.xml')
FAVOURITES     = os.path.join(USERDATA, 'favourites.xml')
PROFILES       = os.path.join(USERDATA, 'profiles.xml')
THUMBS         = os.path.join(USERDATA, 'Thumbnails')
DATABASE       = os.path.join(USERDATA, 'Database')
FANART         = os.path.join(PLUGIN, 'fanart.jpg')
ICON           = os.path.join(PLUGIN, 'icon.png')
ART            = os.path.join(PLUGIN, 'resources', 'art')
WIZLOG         = os.path.join(ADDONDATA, 'wizard.log')
SKIN           = xbmc.getSkinDir()
TODAY          = date.today()
TOMORROW       = TODAY + timedelta(days=1)
THREEDAYS      = TODAY + timedelta(days=3)
KODIV          = float(xbmc.getInfoLabel("System.BuildVersion")[:4])
EXODUS         = 'plugin.video.exodus'
VELOCITY       = 'plugin.video.velocity'
VELOCITYKIDS   = 'plugin.video.velocitykids'
SALTS          = 'plugin.video.salts'
SALTSHD        = 'plugin.video.saltshd.lite'
ROYALWE        = 'plugin.video.theroyalwe'
SPECTO         = 'plugin.video.specto'
URLRESOLVER    = 'script.module.urlresolver'
TRAKT          = 'script.trakt'
PATHSALTS      = os.path.join(ADDONS, SALTS)
PATHSALTSHD    = os.path.join(ADDONS, SALTSHD)
PATHEXODUS     = os.path.join(ADDONS, EXODUS)
PATHVELOCITY   = os.path.join(ADDONS, VELOCITY)
PATHVELOCITYKI = os.path.join(ADDONS, VELOCITYKIDS)
PATHROYALWE    = os.path.join(ADDONS, ROYALWE)
PATHSPECTO     = os.path.join(ADDONS, SPECTO)
PATHURLRESOLVE = os.path.join(ADDONS, URLRESOLVER)
PATHTRAKT      = os.path.join(ADDONS, TRAKT)
EXCLUDES       = uservar.EXCLUDES
BUILDFILE      = uservar.BUILDFILE
APKFILE        = uservar.APKFILE
NOTIFICATION   = uservar.NOTIFICATION
ENABLE         = uservar.ENABLE
AUTOUPDATE     = uservar.AUTOUPDATE
WIZARDFILE     = uservar.WIZARDFILE
AUTOINSTALL    = uservar.AUTOINSTALL
REPOADDONXML   = uservar.REPOADDONXML
REPOZIPURL     = uservar.REPOZIPURL
CONTACT        = uservar.CONTACT

###########################
###### Settings Items #####
###########################

def getS(name):
	try: return ADDON.getSetting(name)
	except: return False

def setS(name, value):
	try: ADDON.setSetting(name, value)
	except: return False

def openS():
	ADDON.openSettings();

def clearS(type):
	trakt   = {'exodus':'', 'salts':'', 'saltshd':'', 'royalwe':'', 'velocity':'', 'velocity':'', 'specto':'', 'trakt':'', 'keeptrakt':'false', 'traktlastsave':'2016-01-01'}
	debrid  = {'exodus':'', 'specto':'', 'urlresolver':'', 'keepdebrid':'false', 'debridlastsave':'2016-01-01'}
	build   = {'buildname':'', 'buildversion':'', 'buildtheme':'', 'latestversion':'', 'lastbuildcheck':'2016-01-01'}
	install = {'installed':'false', 'extract':'', 'errors':''}
	if type == 'trakt':
		for set in trakt:
			setS(set, trakt[set])
	if type == 'debrid':
		for set in debrid:
			setS(set, debrid[set])
	elif type == 'build':
		for set in build:
			setS(set, build[set])
		for set in install:
			setS(set, install[set])
	elif type == 'install':
		for set in install:
			setS(set, install[set])


###########################
###### Display Items ######
###########################

def TextBoxes(heading,announce):
	class TextBox():
		WINDOW=10147
		CONTROL_LABEL=1
		CONTROL_TEXTBOX=5
		def __init__(self,*args,**kwargs):
			xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW, )) # activate the text viewer window
			self.win=xbmcgui.Window(self.WINDOW) # get window
			xbmc.sleep(500) # give window time to initialize
			self.setControls()
		def setControls(self):
			self.win.getControl(self.CONTROL_LABEL).setLabel(heading) # set heading
			try: f=open(announce); text=f.read()
			except: text=announce
			self.win.getControl(self.CONTROL_TEXTBOX).setText(str(text))
			return
	TextBox()
	while xbmc.getCondVisibility('Window.IsVisible(10147)'):
		time.sleep(.5)

def LogNotify(title,message,times=2000,icon=ICON):
	xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (title , message , times, icon))


###########################
###### Build Info #########
###########################

def checkBuild(name, ret):
	if not workingURL(BUILDFILE) == True: return False
	link = openURL(BUILDFILE).replace('\n','').replace('\r','').replace('\t','')
	match = re.compile('name="%s".+?ersion="(.+?)".+?rl="(.+?)".+?ui="(.+?)".+?odi="(.+?)".+?heme="(.+?)".+?con="(.+?)".+?anart="(.+?)"' % name).findall(link)
	if len(match) > 0:
		for version, url, gui, kodi, theme, icon, fanart in match:
			if ret   == 'version': return version
			elif ret == 'url':     return url
			elif ret == 'gui':     return gui
			elif ret == 'kodi':    return kodi
			elif ret == 'theme':   return theme
			elif ret == 'icon':    return icon
			elif ret == 'fanart':  return fanart
	else: return False

def checkTheme(name, theme, ret):
	themeurl = checkBuild(name, 'theme')
	if not workingURL(themeurl) == True: return False
	link = openURL(themeurl).replace('\n','').replace('\r','').replace('\t','')
	match = re.compile('name="%s".+?rl="(.+?)".+?con="(.+?)".+?anart="(.+?)"' % theme).findall(link)
	if len(match) > 0:
		for url, icon, fanart in match:
			if ret   == 'url':    return url
			elif ret == 'icon':   return icon
			elif ret == 'fanart': return fanart
	else: return False

def checkApk(name, ret):
	if not workingURL(APKFILE) == True: return False
	link = openURL(APKFILE).replace('\n','').replace('\r','').replace('\t','')
	match = re.compile('name="%s".+?rl="(.+?)".+?con="(.+?)".+?anart="(.+?)"' % name).findall(link)
	if len(match) > 0:
		for url, icon, fanart in match:
			if   ret == 'url':     return url
			elif ret == 'icon':    return icon
			elif ret == 'fanart':  return fanart
	else: return False

def checkWizard(ret):
	if not workingURL(WIZARDFILE) == True: return False
	link = openURL(WIZARDFILE).replace('\n','').replace('\r','').replace('\t','')
	match = re.compile('id="%s".+?ersion="(.+?)".+?ip="(.+?)"' % ADDON_ID).findall(link)
	if len(match) > 0:
		for version, zip in match:
			if ret   == 'version': return version
			elif ret == 'zip':     return zip
	else: return False

def buildCount(ver=None):
	link = openURL(BUILDFILE).replace('\n','').replace('\r','').replace('\t','')
	match = re.compile('name="(.+?)".+?odi="(.+?)".+?').findall(link)
	count = 0
	if len(match) > 0:
		for name, kodi in match:
			kodi = int(float(kodi))
			if ver == None: count += 1
			elif int(ver) == 16 and kodi >= 16: count += 1
			elif int(ver) == 15 and kodi <= 15: count += 1
	return count

###########################
###### URL Checks #########
###########################
 
def workingURL(url):
	if url == 'http://': return False
	try: 
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		response.close()
	except Exception, e:
		return e
	return True
 
def openURL(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', USER_AGENT)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link

###########################
###### Misc Functions #####
###########################

def removeFolder(path):
	log("Deleting Folder: %s" % path)
	try: shutil.rmtree(path,ignore_errors=True, onerror=None)
	except: return False

def removeFile(path):
	log("Deleting File: %s" % path)
	try:    os.remove(path)
	except: return False

def cleanHouse(folder, ignore=False):
	total_files = 0; total_folds = 0
	for root, dirs, files in os.walk(folder):
		if ignore == False: dirs[:] = [d for d in dirs if d not in EXCLUDES]
		file_count = 0
		file_count += len(files)
		if file_count >= 0:
			for f in files:
				try: 
					os.unlink(os.path.join(root, f))
					total_files += 1
				except: 
					try:
						shutil.rmtree(os.path.join(root, f))
					except:
						log("Error Deleting %s" % f)
			for d in dirs:
				total_folds += 1
				try: 
					shutil.rmtree(os.path.join(root, d))
					total_folds += 1
				except: 
					log("Error Deleting %s" % d)
	return '%s/%s' % (total_files, total_folds)

def emptyfolder(folder):
	total = 0
	for root, dirs, files in os.walk(folder, topdown=True):
		dirs[:] = [d for d in dirs if d not in EXCLUDES]
		file_count = 0
		file_count += len(files) + len(dirs)
		if file_count == 0:
			shutil.rmtree(os.path.join(root))
			total += 1
			log("Empty Folder: %s" % root)
	return total

def log(log):
	xbmc.log("[%s]: %s" % (ADDONTITLE, log))
	if not os.path.exists(ADDONDATA): os.makedirs(ADDONDATA)
	if not os.path.exists(WIZLOG): f = open(WIZLOG, 'w'); f.close()
	with open(WIZLOG, 'r+') as f:
		line = "[%s %s] %s" % (datetime.now().date(), str(datetime.now().time())[:8], log)
		content = f.read()
		f.seek(0, 0)
		f.write(line.rstrip('\r\n') + '\n' + content)

def latestDB(DB):
	if DB in ['Addons', 'ADSP', 'Epg', 'MyMusic', 'MyVideos', 'Textures', 'TV', 'ViewModes']:
		match = glob.glob(os.path.join(DATABASE,'%s*.db' % DB))
		comp = '%s(.+?).db' % DB[1:]
		highest = 0
		for file in match :
			try: check = int(re.compile(comp).findall(file)[0])
			except: check = 0
			if highest < check :
				highest = check
		return '%s%s.db' % (DB, highest)
	else: return False

def addonId(add):
	return xbmcaddon.Addon(id=add)

def addonInfo(add, info):
	addon = addonId(add)
	return addon.getAddonInfo(info)

def forceUpdate():
	xbmc.executebuiltin('UpdateAddonRepos()')
	xbmc.executebuiltin('UpdateLocalAddons()')
	LogNotify(ADDONTITLE, 'Forcing Check Updates')
	if DIALOG.yesno(ADDONTITLE, "Would you like to go to the Avaliable Updates screen?", yeslabel="Go to Page", nolabel="No Thanks"):
		xbmc.executebuiltin('ActivateWindow(10040,"addons://outdated/",return)')

def convertSpecial(url):
	if DIALOG.yesno(ADDONTITLE, "Convert paths to special only works on the device the build was created on.", "Would you like to continue?"):
		DP.create(ADDONTITLE, "Changing Physical Paths To Special", "", "Please Wait")
		for root, dirs, files in os.walk(url):
			for file in files:
				if file.endswith(".xml") or file.endswith(".hash") or file.endswith("properies"):
					DP.update(0,"Fixing", "[COLOR yellow]%s[/COLOR]" % file, "Please Wait")
					a = open((os.path.join(root, file))).read()
					encodedpath  = HOME.replace(':','%3a').replace('\\','%5c')
					extraslashes = HOME.replace('\\','\\\\')
					b = a.replace(HOME, 'special://home/').replace(encodedpath, 'special://home/').replace(extraslashes, 'special://home/')
					f = open((os.path.join(root, file)), mode='w')
					f.write(str(b))
					f.close()
		DP.close()
		LogNotify("Convert Paths to Special", "[COLOR green]Complete![/COLOR]")
	else: log("Convert Paths to Special: Cancelled")

def latestApk(apk, ret=None):
	if apk == "kodi":
		kodi  = "https://kodi.tv/download/"
		link  = openURL(kodi).replace('\n','').replace('\r','').replace('\t','')
		match = re.compile("<h2>Current release:.+?odi v(.+?) &#8220;(.+?)&#8221;</h2>").findall(link)
		if len(match) == 1:
			ver    = match[0][0]
			title  = match[0][1]
			apkurl = "http://mirrors.kodi.tv/releases/android/arm/kodi-%s-%s-armeabi-v7a.apk" % (ver, title)
		if ret == 'version': return ver
		else:                return apkurl
	elif apk == "spmc":
		spmc  = 'https://github.com/koying/SPMC/releases/latest/'
		link  = openURL(spmc).replace('\n','').replace('\r','').replace('\t','')
		match = re.compile(".+?class=\"release-title\">(.+?)</h1>.+?").findall(link)
		ver   = re.sub('<[^<]+?>', '', match[0]).replace(' ', '')
		apkurl = 'https://github.com/koying/SPMC/releases/download/%s-spmc/SPMC-armeabi-v7a_%s.apk' % (ver, ver)
		if ret == 'version': return ver
		else:                return apkurl

##########################
###DETERMINE PLATFORM#####
##########################

def platform():
	if xbmc.getCondVisibility('system.platform.android'):   return 'android'
	elif xbmc.getCondVisibility('system.platform.linux'):   return 'linux'
	elif xbmc.getCondVisibility('system.platform.windows'): return 'windows'
	elif xbmc.getCondVisibility('system.platform.osx'):	    return 'osx'
	elif xbmc.getCondVisibility('system.platform.atv2'):    return 'atv2'
	elif xbmc.getCondVisibility('system.platform.ios'):	    return 'ios'

def log_check():
	ret = False
	if os.path.exists(os.path.join(LOG,'xbmc.log')):
		ret = os.path.join(LOG,'xbmc.log')
	elif os.path.exists(os.path.join(LOG,'kodi.log')):
		ret = os.path.join(LOG,'kodi.log')
	elif os.path.exists(os.path.join(LOG,'spmc.log')):
		ret = os.path.join(LOG,'spmc.log')
	elif os.path.exists(os.path.join(LOG,'tvmc.log')):
		ret = os.path.join(LOG,'tvmc.log')
	return ret

def clearPackages(over=None):
	if os.path.exists(PACKAGES):
		try:	
			for root, dirs, files in os.walk(PACKAGES):
				file_count = 0
				file_count += len(files)
				# Count files and give option to delete
				if file_count > 0:
					if over: yes=1
					else: yes=DIALOG.yesno("Delete Package Cache Files", str(file_count) + " files found", "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove')
					if yes:
						for f in files:	os.unlink(os.path.join(root, f))
						for d in dirs: shutil.rmtree(os.path.join(root, d))
						LogNotify(ADDONTITLE,'Clear Packages: [COLOR green]Success[/COLOR]!')
				else: LogNotify(ADDONTITLE,'Clear Packages: [COLOR red]None Found![/COLOR]')
		except: LogNotify(ADDONTITLE,'Clear Packages: [COLOR red]Error[/COLOR]!')
	else: LogNotify(ADDONTITLE,'Clear Packages: [COLOR red]None Found![/COLOR]')

def clearCache():
	PROFILEADDONDATA = os.path.join(PROFILE,'addon_data')
	cachelist = [
		(PROFILEADDONDATA),
		(ADDONDATA),
		(os.path.join(HOME,'cache')),
		(os.path.join(HOME,'temp')),
		(os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'Other')),
		(os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'LocalAndRental')),
		(os.path.join(ADDONDATA,'script.module.simple.downloader')),
		(os.path.join(ADDONDATA,'plugin.video.itv','Images')),
		(os.path.join(PROFILEADDONDATA,'script.module.simple.downloader')),
		(os.path.join(PROFILEADDONDATA,'plugin.video.itv','Images'))]
		
	delfiles = 0

	for item in cachelist:
		if os.path.exists(item) and not item in [ADDONDATA, PROFILEADDONDATA]:
			for root, dirs, files in os.walk(item):
				file_count = 0
				file_count += len(files)
				if file_count > 0:
					for f in files:
						if not f in ['kodi.log', 'tvmc.log', 'spmc.log', 'xbmc.log']:
							try:
								os.unlink(os.path.join(root, f))
							except:
								pass
						else: log('Ignore Log File: %s' % f)
					for d in dirs:
						try:
							shutil.rmtree(os.path.join(root, d))
							delfiles += 1
							log("[Success] cleared %s files from %s" % (str(file_count), os.path.join(item,d)))
						except:
							log("[Failed] to wipe cache in: %s" % os.path.join(item,d))
		else:
			for root, dirs, files in os.walk(item):
				for d in dirs:
					if 'cache' in d.lower():
						try:
							shutil.rmtree(os.path.join(root, d))
							delfiles += 1
							log("[Success] wiped %s " % os.path.join(item,d))
						except:
							log("[Failed] to wipe cache in: %s" % os.path.join(item,d))

	LogNotify(ADDONTITLE,'Clear Cache: Removed %s Files' % delfiles)

#############################
####KILL XBMC ###############
#####THANKS GUYS @ TI########

def killxbmc():
	choice = DIALOG.yesno('Force Close Kodi', 'You are about to close Kodi', 'Would you like to continue?', nolabel='No, Cancel',yeslabel='Yes, Close')
	if choice == 0: return
	elif choice == 1: pass
	myplatform = platform()
	log("Platform: " + str(myplatform))
	if myplatform == 'osx': # OSX
		log("############ try osx force close #################")
		try: os.system('killall -9 XBMC')
		except: pass
		try: os.system('killall -9 Kodi')
		except: pass
		DIALOG.ok("[COLOR=red][B]WARNING !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.",'')
	elif myplatform == 'linux': #Linux
		log("############ try linux force close #################")
		try: os.system('killall XBMC')
		except: pass
		try: os.system('killall Kodi')
		except: pass
		try: os.system('killall -9 xbmc.bin')
		except: pass
		try: os.system('killall -9 kodi.bin')
		except: pass
		DIALOG.ok("[COLOR=red][B]WARNING !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.",'')
	elif myplatform == 'android': # Android 
		log("############ try android force close #################")
		try: os.system('adb shell am force-stop org.xbmc.kodi')
		except: pass
		try: os.system('adb shell am force-stop org.kodi')
		except: pass
		try: os.system('adb shell am force-stop org.xbmc.xbmc')
		except: pass
		try: os.system('adb shell am force-stop org.xbmc')
		except: pass		
		try: os.system('adb shell kill org.xbmc.kodi')
		except: pass
		try: os.system('adb shell kill org.kodi')
		except: pass
		try: os.system('adb shell kill org.xbmc.xbmc')
		except: pass
		try: os.system('adb shell kill org.xbmc')
		except: pass
		try: os.system('Process.killProcess(android.os.Process.org.xbmc,kodi());')
		except: pass
		try: os.system('Process.killProcess(android.os.Process.org.kodi());')
		except: pass
		try: os.system('Process.killProcess(android.os.Process.org.xbmc.xbmc());')
		except: pass
		try: os.system('Process.killProcess(android.os.Process.org.xbmc());')
		except: pass
		DIALOG.ok(ADDONTITLE, "Press the HOME button on your remote and [COLOR=red][B]FORCE STOP[/COLOR][/B] KODI via the Manage Installed Applications menu in settings on your Amazon home page then re-launch KODI")
	elif myplatform == 'windows': # Windows
		log("############ try windows force close #################")
		try:
			os.system('@ECHO off')
			os.system('tskill XBMC.exe')
		except: pass
		try:
			os.system('@ECHO off')
			os.system('tskill Kodi.exe')
		except: pass
		try:
			os.system('@ECHO off')
			os.system('TASKKILL /im Kodi.exe /f')
		except: pass
		try:
			os.system('@ECHO off')
			os.system('TASKKILL /im XBMC.exe /f')
		except: pass
		DIALOG.ok("[COLOR=red][B]WARNING !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.","Use task manager and NOT ALT F4")
	else: #ATV
		log("############ try atv force close #################")
		try: os.system('killall AppleTV')
		except: pass
		log("############ try raspbmc force close #################") #OSMC / Raspbmc
		try: os.system('sudo initctl stop kodi')
		except: pass
		try: os.system('sudo initctl stop xbmc')
		except: pass
		DIALOG.ok("[COLOR=red][B]WARNING !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit via the menu.","iOS detected. Press and hold both the Sleep/Wake and Home button for at least 10 seconds, until you see the Apple logo.")

##########################
### PURGE DATABASE #######
##########################
def purgeDb(name):
	#dbfile = name.replace('.db','').translate(None, digits)
	#if dbfile not in ['Addons', 'ADSP', 'Epg', 'MyMusic', 'MyVideos', 'Textures', 'TV', 'ViewModes']: return False
	#textfile = os.path.join(DATABASE, name)
	log('Purging DB %s.' % name)
	if os.path.exists(name):
		try:
			textdb = database.connect(name)
			textexe = textdb.cursor()
		except Exception, e:
			log(str(e))
			return False
	else: log('%s not found.' % name); return False
	textexe.execute("""SELECT name FROM sqlite_master WHERE type = 'table';""")
	for table in textexe.fetchall():
		if table[0] == 'version': 
			log('Data from table `%s` skipped.' % table[0])
		else:
			try:
				textexe.execute("""DELETE FROM %s""" % table[0])
				textdb.commit()
				log('Data from table `%s` cleared.' % table[0])
			except e: log(str(e))
	log('%s DB Purging Complete.' % name)
	show = name.replace('\\', '/').split('/')
	LogNotify("Purge Database", "%s Complete" % show[len(show)-1])