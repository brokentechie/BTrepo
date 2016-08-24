import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
import time
try:    from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
from datetime import date, datetime, timedelta
from resources.libs import wizard as wiz

ADDON_ID       = uservar.ADDON_ID
ADDONTITLE     = uservar.ADDONTITLE
ADDON          = wiz.addonId(ADDON_ID)
DIALOG         = xbmcgui.Dialog()
HOME           = xbmc.translatePath('special://home/')
ADDONS         = os.path.join(HOME,      'addons')
USERDATA       = os.path.join(HOME,      'userdata')
PLUGIN         = os.path.join(ADDONS,    ADDON_ID)
PACKAGES       = os.path.join(ADDONS,    'packages')
ADDONDATA      = os.path.join(USERDATA,  'addon_data', ADDON_ID)
REALFOLD       = os.path.join(ADDONDATA, 'debrid')
ICON           = os.path.join(PLUGIN,    'icon.png')
TODAY          = date.today()
TOMORROW       = TODAY + timedelta(days=1)
THREEDAYS      = TODAY + timedelta(days=3)
REAL_EXODUS    = wiz.getS('realexodus')
REAL_SPECTO    = wiz.getS('realspecto')
REAL_URL       = wiz.getS('urlresolver')
KEEPTRAKT      = wiz.getS('keepdebrid')
REALSAVE       = wiz.getS('debridlastsave')
EXODUS         = 'plugin.video.exodus'
SPECTO         = 'plugin.video.specto'
URLRESOLVER    = 'script.module.urlresolver'
PATHEXODUS     = os.path.join(ADDONS, EXODUS)
PATHSPECTO     = os.path.join(ADDONS, SPECTO)
PATHURL        = os.path.join(ADDONS, URLRESOLVER)

def debridUser(who):
	user=None
	if who == 'exodus'       and os.path.exists(PATHEXODUS):     ADD_EXODUS       = wiz.addonId(EXODUS);       user = ADD_EXODUS.getSetting('realdebrid.id')
	if who == 'specto'       and os.path.exists(PATHSPECTO):     ADD_SPECTO       = wiz.addonId(SPECTO);       user = ADD_SPECTO.getSetting('realdebrid_client_id')
	if who == 'url'          and os.path.exists(PATHURL):        ADD_URL          = wiz.addonId(URLRESOLVER);  user = ADD_URL.getSetting('RealDebridResolver_client_id')
	return user
		
def debridIt(do, who):
	if not os.path.exists(ADDONDATA): os.makedirs(ADDONDATA)
	if not os.path.exists(REALFOLD):  os.makedirs(REALFOLD)
	if who == "all":
		if os.path.exists(PATHEXODUS):      debrid_Exodus(do)
		if os.path.exists(PATHSPECTO):      debrid_Specto(do)
		if os.path.exists(PATHURL):         debrid_Url(do)
		wiz.setS('debridlastsave', str(THREEDAYS))
	else:
		if who == "exodus"       and os.path.exists(PATHEXODUS):      debrid_Exodus(do)
		if who == "specto"       and os.path.exists(PATHSPECTO):      debrid_Specto(do)
		if who == "url"          and os.path.exists(PATHURL):         debrid_Url(do)

def clearSaved(who):
	addonlist = {'exodus':'exodus_debrid', 'specto':'specto_debrid', 'url':'url_debrid'}
	if who == 'all':
		for debrid in addonlist:
			file = os.path.join(REALFOLD, addonlist[debrid])
			if os.path.exists(file): os.remove(file)
			wiz.setS('urlresolver' if debrid == 'url' else str('real'+debrid), '')
			wiz.LogNotify(debrid.upper(),'Real Debrid Data: [COLOR green]Removed![/COLOR]', 2000, os.path.join(eval('PATH'+debrid.replace('real', '').upper()),'icon.png'))
	else:
		file = os.path.join(REALFOLD, addonlist[who])
		if os.path.exists(file): os.remove(file)
		wiz.setS('urlresolver' if who == 'url' else str('real'+who), '')
		wiz.LogNotify(who.upper().replace('real', ''),'Real Debrid Data: [COLOR green]Removed![/COLOR]', 2000, os.path.join(eval('PATH'+who.replace('real', '').upper()),'icon.png'))
	xbmc.executebuiltin('Container.Refresh')	
		
def debrid_Exodus(do):
	EXODUSFILE      = os.path.join(REALFOLD, 'exodus_debrid')
	EXODUSSETTINGS  = os.path.join(USERDATA, 'addon_data', EXODUS,'settings.xml')
	EXODUS_DEBRID   = ['realdebrid.auth', 'realdebrid.id', 'realdebrid.secret', 'realdebrid.token', 'realdebrid.refresh']
	ADD_EXODUS      = wiz.addonId(EXODUS)
	TRAKTEXODUS     = ADD_EXODUS.getSetting('realdebrid.id')
	if do == 'update':
		if not TRAKTEXODUS == '':
			with open(EXODUSFILE, 'w') as f:
				for debrid in EXODUS_DEBRID: f.write('<debrid>\n\t<id>%s</id>\n\t<value>%s</value>\n</debrid>\n' % (debrid, ADD_EXODUS.getSetting(debrid)))
			f.closed
			wiz.setS('realexodus', ADD_EXODUS.getSetting('realdebrid.id'))
			wiz.LogNotify('Exodus','Real Debrid Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
		else: wiz.LogNotify('Exodus','Real Debrid Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
	elif do == 'restore':
		if os.path.exists(EXODUSFILE):
			f = open(EXODUSFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<debrid><id>(.+?)</id><value>(.+?)</value></debrid>').findall(g)
			if len(match) > 0:
				for debrid, value in match:
					ADD_EXODUS.setSetting(debrid, value)
			wiz.setS('realexodus', ADD_EXODUS.getSetting('realdebrid.id'))
			wiz.LogNotify('Exodus','Real Debrid: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
		else: wiz.LogNotify('Exodus','Real Debrid Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('Exodus SETTINGS: %s' % EXODUSSETTINGS)
		if os.path.exists(EXODUSSETTINGS):
			f = open(EXODUSSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(EXODUSSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in EXODUS_DEBRID: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('Exodus','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
		else: wiz.LogNotify('Exodus','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')

def debrid_Specto(do):
	SPECTOFILE      = os.path.join(REALFOLD, 'specto_debrid')
	SPECTOSETTINGS  = os.path.join(USERDATA, 'addon_data', SPECTO,'settings.xml')
	SPECTO_DEBRID   = ['realdebrid_auth', 'realdebrid_token', 'realdebrid_refresh', 'realdebrid_client_id', 'realdebrid_client_secret']
	ADD_SPECTO      = wiz.addonId(SPECTO)
	DEBRIDSPECTO    = ADD_SPECTO.getSetting('realdebrid_client_id')
	if do == 'update':
		if not ADD_SPECTO.getSetting('realdebrid_client_id') == '':
			with open(SPECTOFILE, 'w') as f:
				for debrid in SPECTO_DEBRID: f.write('<debrid>\n\t<id>%s</id>\n\t<value>%s</value>\n</debrid>\n' % (debrid, ADD_SPECTO.getSetting(debrid)))
			f.closed
			wiz.setS('realspecto', ADD_SPECTO.getSetting('realdebrid_client_id'))
			wiz.LogNotify('Specto','Real Debrid Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHSPECTO,'icon.png'))
		else: wiz.LogNotify('Specto','Real Debrid Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHSPECTO,'icon.png'))
	elif do == 'restore':
		if os.path.exists(SPECTOFILE):
			f = open(SPECTOFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<debrid><id>(.+?)</id><value>(.+?)</value></debrid>').findall(g)
			if len(match) > 0:
				for debrid, value in match:
					ADD_SPECTO.setSetting(debrid, value)
				wiz.setS('realspecto', ADD_SPECTO.getSetting('realdebrid_client_id'))
			wiz.LogNotify('Specto','Real Debrid Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHSPECTO,'icon.png'))
		else: wiz.LogNotify('Specto','Real Debrid Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHSPECTO,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('Specto SETTINGS: %s' % SPECTOSETTINGS)
		if os.path.exists(SPECTOSETTINGS):
			f = open(SPECTOSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(SPECTOSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in SPECTO_DEBRID: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('Specto','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHSPECTO,'icon.png'))
		else: wiz.LogNotify('Specto','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHSPECTO,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')

def debrid_Url(do):
	URLFILE         = os.path.join(REALFOLD, 'url_debrid')
	URLSETTINGS     = os.path.join(USERDATA, 'addon_data', URLRESOLVER,'settings.xml')
	URL_DEBRID      = ['RealDebridResolver_enabled', 'RealDebridResolver_autopick', 'RealDebridResolver_token', 'RealDebridResolver_refresh', 'RealDebridResolver_client_id', 'RealDebridResolver_client_secret']
	ADD_URL         = wiz.addonId(URLRESOLVER)
	DEBRIDURL       = ADD_URL.getSetting('RealDebridResolver_client_id')
	if do == 'update':
		if not ADD_URL.getSetting('RealDebridResolver_client_id') == '':
			with open(URLFILE, 'w') as f:
				for debrid in URL_DEBRID: f.write('<debrid>\n\t<id>%s</id>\n\t<value>%s</value>\n</debrid>\n' % (debrid, ADD_URL.getSetting(debrid)))
			f.closed
			wiz.setS('urlresolver', ADD_URL.getSetting('RealDebridResolver_client_id'))
			wiz.LogNotify('Url Resolver','Real Debrid Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHURL,'icon.png'))
		else: wiz.LogNotify('Url Resolver','Real Debrid Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHURL,'icon.png'))
	elif do == 'restore':
		if os.path.exists(URLFILE):
			f = open(URLFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<debrid><id>(.+?)</id><value>(.+?)</value></debrid>').findall(g)
			if len(match) > 0:
				for debrid, value in match:
					ADD_URL.setSetting(debrid, value)
				wiz.setS('urlresolver', ADD_URL.getSetting('RealDebridResolver_client_id'))
			wiz.LogNotify('Url Resolver','Real Debrid Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHURL,'icon.png'))
		else: wiz.LogNotify('Url Resolver','Real Debrid Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHURL,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('Url Resolver SETTINGS: %s' % URLSETTINGS)
		if os.path.exists(URLSETTINGS):
			f = open(URLSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(URLSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in URL_DEBRID: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('Url Resolver','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHURL,'icon.png'))
		else: wiz.LogNotify('Url Resolver','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHURL,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')
	
def autoUpdate(who):
	if who == 'all':
		autoUpdate('exodus')
		autoUpdate('specto')
		autoUpdate('url')
	else:
		if who == 'exodus'   and os.path.exists(PATHEXODUS):
			if not debridUser('exodus') == REAL_EXODUS and not debridUser('exodus') == '': 
				if DIALOG.yesno(ADDONTITLE, "Would you like to save the Real Debrid data for Exodus?", "Addon: [COLOR green][B]%s[/B][/COLOR]" % debridUser('exodus'), "Saved: [COLOR red][B]%s[/B][/COLOR]" % REAL_EXODUS if not REAL_EXODUS == '' else 'Saved: [COLOR red][B]None[/B][/COLOR]', yeslabel="Yes Save", nolabel="No Cancel"):
					debridIt('update', 'exodus')
		
		elif who == 'specto' and os.path.exists(PATHSPECTO): 
			if not debridUser('specto') == REAL_SPECTO and not debridUser('specto') == '': 
				if DIALOG.yesno(ADDONTITLE, "Would you like to save the Real Debrid data for Specto?", "Addon: [COLOR green][B]%s[/B][/COLOR]" % debridUser('specto'), "Saved: [COLOR red][B]%s[/B][/COLOR]" % REAL_SPECTO if not REAL_SPECTO == '' else 'Saved: [COLOR red][B]None[/B][/COLOR]', yeslabel="Yes Save", nolabel="No Cancel"):
					debridIt('update', 'specto')
		
		elif who == 'url' and os.path.exists(PATHURL):
			if not debridUser('url') == REAL_URL and not debridUser('url') == '':
				if DIALOG.yesno(ADDONTITLE, "Would you like to save the Real Debrid data for URL Resolver?", "Addon: [COLOR green][B]%s[/B][/COLOR]" % debridUser('url'), "Saved: [COLOR red][B]%s[/B][/COLOR]" % REAL_URL if not REAL_URL == '' else 'Saved: [COLOR red][B]None[/B][/COLOR]', yeslabel="Yes Save", nolabel="No Cancel"):
					debridIt('update', 'url')		
	
	
def activateDebrid(name):
	url = None
	if name == 'exodus':
		if os.path.exists(PATHEXODUS): url = 'RunPlugin(plugin://plugin.video.exodus/?action=rdAuthorize)'
		else: DIALOG.ok(ADDONTITLE, 'Exodus is not currently installed.')
	elif name == 'specto': 
		if os.path.exists(PATHSPECTO): url = 'RunPlugin(plugin://plugin.video.specto/?action=realdebridauth)'
		else: DIALOG.ok(ADDONTITLE, 'Specto is not currently installed.')
	elif name == 'url': 
		if os.path.exists(PATHURL):    url = 'RunPlugin(plugin://script.module.urlresolver/?mode=auth_rd)'
		else: DIALOG.ok(ADDONTITLE, 'Url Resolver is not currently installed.')
	if not url == None: 
		xbmc.executebuiltin(url)
		check = 0
		while debridUser(name) == None:
			if check == 30: break
			check += 1
			time.sleep(10)
	xbmc.executebuiltin('Container.Refresh')