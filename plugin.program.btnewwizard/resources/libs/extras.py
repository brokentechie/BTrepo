#
#      Copyright (C) 2015 Andy Robbins (Brokentechie)
#
#  Credit to Lee Randall (Whufclee) and Guruwan (Kodimaster) for original code
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import urllib, urllib2, re, xbmcplugin, xbmcgui, xbmc, xbmcaddon, os, sys, time, xbmcvfs
import glob
import shutil
import subprocess
import datetime
import uservar
import communitybuilds
import zipfile
import ntpath
from addon.common.addon import Addon
from addon.common.net import Net

AddonID    = uservar.ADDON_ID
BASEURL    = 'http://brokentechie.ddns.net'
ADDON      =  xbmcaddon.Addon(id=AddonID)
HOME       =  xbmc.translatePath('special://home/')
ARTPATH    =  'http://brokentechie.ddns.net/wizard/art/' + os.sep
zip        =  ADDON.getSetting('zip')
dialog     =  xbmcgui.Dialog()
dp         =  xbmcgui.DialogProgress()
USERDATA   =  xbmc.translatePath(os.path.join('special://home/userdata',''))
ADDON_DATA =  xbmc.translatePath(os.path.join(USERDATA,'addon_data'))
ADDONS     =  xbmc.translatePath(os.path.join('special://home','addons'))
USB        =  xbmc.translatePath(os.path.join(zip))
log_path   =  xbmc.translatePath('special://logpath/')
skin       =  xbmc.getSkinDir()
net        =  Net()
notifyart  =  xbmc.translatePath(os.path.join(ADDONS,AddonID,'resources/'))
EXCLUDES     =  ['plugin.program.btnewwizard','script.module.addon.common','addon.common.addon']
FANART       =  xbmc.translatePath(os.path.join(ADDONS,AddonID,'fanart.jpg'))

#-----------------------------------------------------------------------------------------------------------------    
#Popup class - thanks to whoever codes the help popup in TVAddons Maintenance for this section. Unfortunately there doesn't appear to be any author details in that code so unable to credit by name.
class SPLASH(xbmcgui.WindowXMLDialog):
    def __init__(self,*args,**kwargs): self.shut=kwargs['close_time']; xbmc.executebuiltin("Skin.Reset(AnimeWindowXMLDialogClose)"); xbmc.executebuiltin("Skin.SetBool(AnimeWindowXMLDialogClose)")
    def onFocus(self,controlID): pass
    def onClick(self,controlID): 
        if controlID==12: xbmc.Player().stop(); self._close_dialog()
    def onAction(self,action):
        if action in [5,6,7,9,10,92,117] or action.getButtonCode() in [275,257,261]: xbmc.Player().stop(); self._close_dialog()
    def _close_dialog(self):
        xbmc.executebuiltin("Skin.Reset(AnimeWindowXMLDialogClose)"); time.sleep( .4 ); self.close()
#-----------------------------------------------------------------------------------------------------------------    
#Add a standard directory and grab fanart and iconimage from artpath defined in global variables
def addDir(type,name,url,mode,iconimage = '',fanart = '',video = '',description = ''):
    if type != 'folder2' and type != 'addon':
        if len(iconimage) > 0:
            iconimage = ARTPATH + iconimage
        else:
            iconimage = 'DefaultFolder.png'
    if type == 'addon':
        if len(iconimage) > 0:
            iconimage = iconimage
        else:
            iconimage = 'http://brokentechie.ddns.net/wizard/Maintenance.png'
    if fanart == '':
        fanart = FANART
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)+"&video="+urllib.quote_plus(video)+"&description="+urllib.quote_plus(description)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
    liz.setProperty( "Fanart_Image", fanart )
    liz.setProperty( "Build.Video", video )
    if (type=='folder') or (type=='folder2') or (type=='tutorial_folder') or (type=='news_folder'):
        ok=Add_Directory_Item(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    else:
        ok=Add_Directory_Item(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok
#---------------------------------------------------------------------------------------------------
def Add_Directory_Item(handle, url, listitem, isFolder):
    xbmcplugin.addDirectoryItem(handle, url, listitem, isFolder) 
#----------------------------------------------------------------------------------------------------------------- 
def Add_Install_Dir(title,name,url,mode,iconimage = '',fanart = '',video = '',description = '',zip_link = '',repo_link = '',repo_id = '',addon_id = '',provider_name = '',forum = '',data_path = ''):
    if len(iconimage) > 0:
        iconimage = ARTPATH + iconimage
    else:
        iconimage = 'DefaultFolder.png'
    if fanart == '':
        fanart = FANART
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&zip_link="+urllib.quote_plus(zip_link)+"&repo_link="+urllib.quote_plus(repo_link)+"&data_path="+urllib.quote_plus(data_path)+"&provider_name="+str(provider_name)+"&forum="+str(forum)+"&repo_id="+str(repo_id)+"&addon_id="+str(addon_id)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)+"&video="+urllib.quote_plus(video)+"&description="+urllib.quote_plus(description)
    ok=True
    liz=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
    liz.setProperty( "Fanart_Image", fanart )
    liz.setProperty( "Build.Video", video )
    Add_Directory_Item(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
#-----------------------------------------------------------------------------------------------------------------  
#Function to delete crash logs
def Delete_Logs():  
    for infile in glob.glob(os.path.join(log_path, 'xbmc_crashlog*.*')):
         File=infile
         print infile
         os.remove(infile)
         dialog = xbmcgui.Dialog()
         dialog.ok("Crash Logs Deleted", "Your old crash logs have now been deleted.")
#-----------------------------------------------------------------------------------------------------------------    
#Function to delete the packages folder
def Delete_Packages():
    purgePath = xbmc.translatePath('special://home/addons/packages')
    dialog = xbmcgui.Dialog()
    for root, dirs, files in os.walk(purgePath):
            file_count = 0
            file_count += len(files)
    if dialog.yesno("Delete Package Cache Files", "%d packages found."%file_count, "Delete Them?"):  
        for root, dirs, files in os.walk(purgePath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:            
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
                dialog = xbmcgui.Dialog()
                dialog.ok("Brokentechie Maintenance", "Purge Packages - Completed")
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok("Brokentechie Maintenance", "No Packages to Purge")
#---------------------------------------------------------------------------------------------------
#Function to delete the userdata/addon_data folder
def Delete_Userdata():
    print '############################################################       DELETING USERDATA             ###############################################################'
    addon_data_path = xbmc.translatePath(os.path.join('special://home/userdata/addon_data', ''))
    for root, dirs, files in os.walk(addon_data_path):
        file_count = 0
        file_count += len(files)
    # Count files and give option to delete
        if file_count >= 0:
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))        
#-----------------------------------------------------------------------------------------------------------------  
#Function to do a full wipe.
def Destroy_Path(path):
    dp.create("[COLOR=white]Brokentechie Wizard[/COLOR]","Wiping...",'', 'Please Wait')
    shutil.rmtree(path, ignore_errors=True)
#---------------------------------------------------------------------------------------------------
def Get_Keyboard( default="", heading="", hidden=False ):
    """ shows a keyboard and returns a value """
    keyboard = xbmc.Keyboard( default, heading, hidden )
    keyboard.doModal()
    if ( keyboard.isConfirmed() ):
        return unicode( keyboard.getText(), "utf-8" )
    return default
#-----------------------------------------------------------------------------------------------------------------  
def Get_Params():    
    if len(sys.argv[2]) < 2:
        return []

    param = []

    params        = sys.argv[2]
    cleanedparams = params.replace('?','')

    if (params[len(params)-1] == '/'):
        params = params[0:len(params)-2]

    pairsofparams = cleanedparams.split('&')
    param         = {}

    for i in range(len(pairsofparams)):
        splitparams = {}
        splitparams = pairsofparams[i].split('=')

        if (len(splitparams)) == 2:
            param[splitparams[0]] = splitparams[1]

    return param


#---------------------------------------------------------------------------------------------------
#Thanks to metalkettle for his work on the original IP checker addon        
def IP_Check(url='http://www.iplocation.net/',inc=1):
    match=re.compile("<td width='80'>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td>.+?</td><td>(.+?)</td>").findall(net.http_GET(url).content)
    for ip, region, country, isp in match:
        if inc <2: dialog=xbmcgui.Dialog(); dialog.ok('Check My IP',"[B][COLOR gold]Your IP Address is: [/COLOR][/B] %s" % ip, '[B][COLOR gold]Your IP is based in: [/COLOR][/B] %s' % country, '[B][COLOR gold]Your Service Provider is:[/COLOR][/B] %s' % isp)
        inc=inc+1
#-----------------------------------------------------------------------------------------------------------------
def killxbmc():
    choice = xbmcgui.Dialog().yesno('Force Close Kodi', 'You are about to close Kodi', 'Would you like to continue?', nolabel='No, Cancel',yeslabel='Yes, Close')
    if choice == 0:
        return
    elif choice == 1:
        pass
    myplatform = platform()
    print "Platform: " + str(myplatform)
    if myplatform == 'osx': # OSX
        print "############   try osx force close  #################"
        try: os.system('killall -9 XBMC')
        except: pass
        try: os.system('killall -9 Kodi')
        except: pass
        dialog.ok("[COLOR=red][B]WARNING  !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.",'')
    elif myplatform == 'linux': #Linux
        print "############   try linux force close  #################"
        try: os.system('killall XBMC')
        except: pass
        try: os.system('killall Kodi')
        except: pass
        try: os.system('killall -9 xbmc.bin')
        except: pass
        try: os.system('killall -9 kodi.bin')
        except: pass
        dialog.ok("[COLOR=red][B]WARNING  !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.",'')
    elif myplatform == 'android': # Android  
        print "############   try android force close  #################"
        try: os.system('adb shell am force-stop org.xbmc.kodi')
        except: pass
        try: os.system('adb shell am force-stop org.kodi')
        except: pass
        try: os.system('adb shell am force-stop org.xbmc.xbmc')
        except: pass
        try: os.system('adb shell am force-stop org.xbmc')
        except: pass        
        dialog.ok("[COLOR=red][B]WARNING  !!![/COLOR][/B]", "Your system has been detected as Android, you ", "[COLOR=yellow][B]MUST[/COLOR][/B] force close XBMC/Kodi. [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.","Pulling the power cable is the simplest method to force close.")
    elif myplatform == 'windows': # Windows
        print "############   try windows force close  #################"
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
        dialog.ok("[COLOR=red][B]WARNING  !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit cleanly via the menu.","Use task manager and NOT ALT F4")
    else: #ATV
        print "############   try atv force close  #################"
        try: os.system('killall AppleTV')
        except: pass
        print "############   try raspbmc force close  #################" #OSMC / Raspbmc
        try: os.system('sudo initctl stop kodi')
        except: pass
        try: os.system('sudo initctl stop xbmc')
        except: pass
        dialog.ok("[COLOR=red][B]WARNING  !!![/COLOR][/B]", "If you\'re seeing this message it means the force close", "was unsuccessful. Please force close XBMC/Kodi [COLOR=lime]DO NOT[/COLOR] exit via the menu.","Your platform could not be detected so just pull the power cable.")    

def platform():
    if xbmc.getCondVisibility('system.platform.android'):
        return 'android'
    elif xbmc.getCondVisibility('system.platform.linux'):
        return 'linux'
    elif xbmc.getCondVisibility('system.platform.windows'):
        return 'windows'
    elif xbmc.getCondVisibility('system.platform.osx'):
        return 'osx'
    elif xbmc.getCondVisibility('system.platform.atv2'):
        return 'atv2'
    elif xbmc.getCondVisibility('system.platform.ios'):
        return 'ios'
#---------------------------------------------------------------------------------------------------
def Log_Viewer():
    log_path = xbmc.translatePath('special://logpath')
    xbmc_version=xbmc.getInfoLabel("System.BuildVersion")
    version=float(xbmc_version[:4])
    if version < 14:
        log = os.path.join(log_path, 'xbmc.log')
        Text_Boxes('XBMC Log', log)
    else:
        log = os.path.join(log_path, 'kodi.log')
        Text_Boxes('Kodi Log', log)
#---------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------
#Simple shortcut to create a notification
def Notify(title,message,times,icon):
    icon = notifyart+icon
    xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+icon+")")
#---------------------------------------------------------------------------------------------------
#Function to create a text box
def Open_URL(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link     = response.read()
    response.close()
    return link.replace('\r','').replace('\n','').replace('\t','')
#---------------------------------------------------------------------------------------------------
def Remove_Addons(url):
    data_path = str(url).replace(ADDONS,ADDON_DATA)
    if dialog.yesno("Remove", '', "Do you want to Remove"):
        for root, dirs, files in os.walk(url):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        os.rmdir(url)
        try:
            for root, dirs, files in os.walk(data_path):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
            os.rmdir(data_path)
        except: pass
        xbmc.executebuiltin('Container.Refresh')         
#---------------------------------------------------------------------------------------------------
#Function to restore a zip file 
def Remove_Build():
    communitybuilds.Check_Download_Path()
    filename = xbmcgui.Dialog().browse(1, 'Select the backup file you want to DELETE', 'files', '.zip', False, False, USB)
    if filename != USB:
        clean_title = ntpath.basename(filename)
        choice = xbmcgui.Dialog().yesno('Delete Backup File', 'This will completely remove '+clean_title, 'Are you sure you want to delete?', '', nolabel='No, Cancel',yeslabel='Yes, Delete')
        if choice == 1:
            os.remove(filename)
#---------------------------------------------------------------------------------------------------

def Text_Boxes(heading,anounce):
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
      try: f=open(anounce); text=f.read()
      except: text=anounce
      self.win.getControl(self.CONTROL_TEXTBOX).setText(str(text))
      return
  TextBox()  
#-----------------------------------------------------------------------------------------------------------------
#Report back with the version of Kodi installed
def XBMC_Version(url):
    xbmc_version=xbmc.getInfoLabel("System.BuildVersion")
    version=float(xbmc_version[:4])
    if version < 14:
        kodiorxbmc = 'You are running XBMC'
    else:
        kodiorxbmc = 'You are running Kodi'
    dialog=xbmcgui.Dialog()
    dialog.ok(kodiorxbmc, "Your version is: %s" % version)
#---------------------------------------------------------------------------------------------------

params=Get_Params()
url=None
name=None
mode=None
iconimage=None
description=None
author=None
fanart=None
zip_link=None
repo_id=None
repo_link=None

try:    mode = urllib.unquote_plus(params['mode'])
except: mode = None

try:    url = urllib.unquote_plus(params['url'])
except: url = ''

try:    name = urllib.unquote_plus(params['name'])
except: name = ''

try:    type = urllib.unquote_plus(params['filetype'])
except: type = ''

try:    repo = urllib.unquote_plus(params['repourl'])
except: repo = ''

try:    author = urllib.unquote_plus(params['author'])
except: author = 'anonymous'

try:    iconimage=urllib.unquote_plus(params["iconimage"])
except: pass

try:    description=urllib.unquote_plus(params["description"])
except: pass

try:    fanart=urllib.unquote_plus(params["fanart"])
except: pass

try:    special=urllib.unquote_plus(params["special"])
except: pass

try:    repo_link=urllib.unquote_plus(params["repo_link"])
except: repo_link=''

try:    repo_id=urllib.unquote_plus(params["repo_id"])
except: repo_id=''

try:    zip_link=urllib.unquote_plus(params["zip_link"])
except: zip_link=''

if mode=='kill_xbmc' : killxbmc()
