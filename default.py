import urlparse
import xbmc
import os
import sys
import glob
import resources.lib.utils as utils
import platform
import subprocess

def main(argv):

	params = getParams(argv)

	defaultsettings = getDefaults()

	if "profile" in params:
		profilenum = params['profile']
	else:
		profilenum = ''

	profiledict = getProfile(defaultsettings, profilenum)

	verifyProfile(profiledict)

	# Let's see if we just want to show the commands in a Kodi notification. This is
	# useful if you want to verify settings or cron them up manually.
	if "getcommand" in params:
		if params['getcommand'] == "makemkvcon":
			utils.showOK(buildMakeMKVConCommand(profiledict))
			return 0
		elif params['getcommand'] == "handbrakecli":
			utils.showOK(buildHandBrakeCLICommand(profiledict, profiledict['tempfolder']))
			return 0

	command = buildMakeMKVConCommand(profiledict)

	# Beginning Rip. Command:
	utils.log("{beginning} {rip}. {commandstr}: {command}".format(beginning = utils.getString(30070),
		rip = utils.getString(30027), commandstr = utils.getString(30071),
		command = command))
	output = ""
	try:
		output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
	# For some reason, it seems that this always exits with a non-zero status, so
	# I'm just checking the output for success.
	except subprocess.CalledProcessError, e:
		if "Copy complete." not in e.output:
			utils.exitFailed("MakeMKV {failed}".format( failed = utils.getString(30059)),
				e.output)

	# Eject if we need to
	# 30027 == Rip
	if profiledict['ejectafter'] == utils.getStringLow(30027):
		xbmc.executebuiltin('EjectTray()')

	# Display notification/dialog if we need to. A notification is a toast that
	# auto-dismisses after a few seconds, whereas a dialog requires the user to
	# press ok.
	# 30065 == Notification
	if profiledict['notifyafterrip'] == utils.getStringLow(30065):
		utils.showNotification("{rip} {completedsuccessfully}".format(rip =
			utils.getString(30027), completedsuccessfully = utils.getString(30058)))
	# 30066 == Dialog
	elif profiledict['notifyafterrip'] == utils.getStringLow(30066):
		utils.showOK("{rip} {completedsuccessfully}".format(rip =
			utils.getString(30027), completedsuccessfully = utils.getString(30058)))

	# Some people may want to just rip movies, and not encode them. If that's the
	# case, we are done here.
	if profiledict['encodeafterrip'] == 'false':
		return 0

	filestoencode = glob.glob(os.path.join(profiledict['tempfolder'], '*.mkv'))
	for f in filestoencode:
		command = buildHandBrakeCLICommand(profiledict, f)
		utils.log("{beginning} {encode}. {commandstr}: {command}".format(beginning =
			utils.getString(30070), encode = utils.getString(30028),
			commandstr = utils.getString(30071),
			command = command))
		output = ""
		try:
			output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
		except subprocess.CalledProcessError, e:
			if "Encode done!" not in e.output:
				utils.exitFailed("HandBrake {failed}".format(failed =
					utils.getString(30059)), e.output)
		if profiledict['cleanuptempdir'] == 'true':
			os.remove(f)

	# 30028 == Encode
	if profiledict['ejectafter'] == utils.getStringLow(30028):
		xbmc.executebuiltin('EjectTray()')

	# 30065 == Notification
	if profiledict['notifyafterencode'] == utils.getStringLow(30065):
		utils.showNotification("{encode} {completedsuccessfully}".format(encode =
			utils.getString(30028), completedsuccessfully = utils.getString(30058)))
	elif profiledict['notifyafterencode'] == utils.getStringLow(30066):
		utils.showOK("{encode} {completedsuccessfully}".format(encode =
			utils.getString(30028), completedsuccessfully = utils.getString(30058)))

	return 0

def getDefaults():
	# Get all the profile's settings. I know there has to be a better way to do profiles,
	# but this should work.
	defaultsettings = {'defaultmakemkvpath': utils.getSetting('defaultmakemkvpath'),
		'defaulthandbrakeclipath': utils.getSetting('defaulthandbrakeclipath'),
		'defaulttempfolder': utils.getSetting('defaulttempfolder'),
		'defaultdestinationfolder': utils.getSetting('defaultdestinationfolder'),
		'defaultniceness': utils.getSettingLow('defaultniceness'),
		'defaultresolution': utils.getSetting('defaultresolution'),
		'defaultquality': utils.getSettingLow('defaultquality'),
		'defaultmintitlelength': utils.getSetting('defaultmintitlelength'),
		'defaultnativelanguage': utils.getSettingLow('defaultnativelanguage'),
		'defaultforeignaudio': utils.getSettingLow('defaultforeignaudio'),
		'defaultencodeafterrip': utils.getSettingLow('defaultencodeafterrip'),
		'defaultejectafter': utils.getSettingLow('defaultejectafter'),
		'defaultnotifyafterrip': utils.getSettingLow('defaultnotifyafterrip'),
		'defaultnotifyafterencode': utils.getSettingLow('defaultnotifyafterencode'),
		'defaultcleanuptempdir': utils.getSettingLow('defaultcleanuptempdir'),
		'defaultblackandwhite': utils.getSettingLow('defaultblackandwhite'),
		'defaultadditionalhandbrakeargs': utils.getSetting('defaultadditionalhandbrakeargs')}
	return defaultsettings

def getProfile(defaultsettings, profilenum):
	if profilenum == '':
		validprofiles = []
		for profile in ['profile1', 'profile2', 'profile3', 'profile4', 'profile5',
			'profile6', 'profile7', 'profile8', 'profile9', 'profile10']:
			if utils.getSetting(profile + 'enabled') == 'true':
				validprofiles.append(utils.getSetting(profile + 'prettyname'))
		profilenum = utils.showSelectDialog("{couchripper} - {profilestr}".format(
			couchripper = utils.getString(30010), profilestr =
			utils.getString(30051)), validprofiles)
		profilename = validprofiles[profilenum]
	else:
		profilename = utils.getSetting(profilenum + 'prettyname')
	profiledict = []
	for profile in ['profile1', 'profile2', 'profile3', 'profile4', 'profile5',
		'profile6', 'profile7', 'profile8', 'profile9', 'profile10']:
		if utils.getSetting(profile + 'prettyname') == profilename:
			profiledict = {'makemkvpath': utils.getSetting(profile + 'makemkvpath'),
			'handbrakeclipath': utils.getSetting(profile + 'handbrakeclipath'),
			'tempfolder': utils.getSetting(profile + 'tempfolder'),
			'destinationfolder': utils.getSetting(profile + 'destinationfolder'),
			'niceness': utils.getSettingLow(profile + 'niceness'),
			'resolution': utils.getSettingLow(profile + 'resolution'),
			'quality': utils.getSettingLow(profile + 'quality'),
			'mintitlelength': utils.getSettingLow(profile + 'mintitlelength'),
			'nativelanguage': utils.getSettingLow(profile + 'nativelanguage'),
			'foreignaudio': utils.getSettingLow(profile + 'foreignaudio'),
			'encodeafterrip': utils.getSettingLow(profile + 'encodeafterrip'),
			'ejectafter': utils.getSettingLow(profile + 'ejectafter'),
			'notifyafterrip': utils.getSettingLow(profile + 'notifyafterrip'),
			'notifyafterencode': utils.getSettingLow(profile + 'notifyafterencode'),
			'cleanuptempdir': utils.getSettingLow(profile + 'cleanuptempdir'),
			'blackandwhite': utils.getSettingLow(profile + 'blackandwhite'),
			'additionalhandbrakeargs': utils.getSetting(profile + 'additionalhandbrakeargs')}
			for key, value in profiledict.iteritems():
				if ( value == 'default' or value == ''):
					profiledict[key] = defaultsettings['default' + key]
	return profiledict

def verifyProfile(profiledict):
	# Let's verify all of our settings.
	errors = ""
	if not os.path.isfile(profiledict['makemkvpath']):
		errors = errors + utils.settingsError("{couldnotfind} makemkvcon. "
			.format(couldnotfind = utils.getString(30052)))
	if not os.path.isfile(profiledict['handbrakeclipath']):
		errors = errors + utils.settingsError("{couldnotfind} HandBrakeCLI. "
			.format(couldnotfind = utils.getString(30052)))
	if not os.path.isdir(profiledict['tempfolder']):
		errors = errors + utils.settingsError("{couldnotfind} {tempfolder}. "
			.format(couldnotfind = utils.getString(30052), tempfolder =
			profiledict[tempfolder]))
	if not os.path.isdir(profiledict['destinationfolder']):
		errors = errors + utils.settingsError("{couldnotfind} {destinationfolder}. "
		.format(couldnotfind = utils.getString(30052), destinationfolder =
		profiledict[destinationfolder]))
	# 30013 == High, 30015 == Low, 30019 == Normal
	if ( profiledict['niceness'] != utils.getStringLow(30013) and
		profiledict['niceness'] != utils.getStringLow(30015) and
		profiledict['niceness'] != utils.getStringLow(30019) ):
		errors = errors + utils.settingsError("{invalid} {niceness}. "
			.format(invalid = utils.getString(30056),
			niceness = utils.getString(30018)))
	# 30042 == 1080, 30043 == 720, 30044 == 480
	if ( profiledict['resolution'] != utils.getStringLow(30042) and
		profiledict['resolution'] != utils.getStringLow(30043) and
		profiledict['resolution'] != utils.getStringLow(30044) ):
		errors = errors + utils.settingsError("{invalid} {resolution}. "
			.format(invalid = utils.getString(30056),
			resolution = utils.getString(30011)))
	# 30013 == High, 30015 == Low, 30014 == Medium
	if ( profiledict['quality'] != utils.getStringLow(30013) and
		profiledict['quality'] != utils.getStringLow(30014) and
		profiledict['quality'] != utils.getStringLow(30015) ):
		errors = errors + utils.settingsError("{invalid} {quality}. "
			.format(invalid = utils.getString(30056),
			quality = utils.getString(30012)))
	if not profiledict['mintitlelength'].isdigit():
		errors = errors + utils.settingsError("{invalid} {mintitlelength}. "
			.format(invalid = utils.getString(30056),
			mintitlelength = utils.getString(30022)))

	# List of valid ISO-639.2 language names.
	# From http://www.loc.gov/standards/iso639-2/ISO-639-2_8859-1.txt This is the
	# format that HandBrake requires language arguments to be in.
	validlanguages = [ 'all', 'aar', 'abk', 'ace', 'ach', 'ada', 'ady', 'afa', 'afh',
		'afr', 'ain', 'aka', 'akk', 'alb', 'ale', 'alg', 'alt', 'amh', 'ang', 'anp',
		'apa', 'ara', 'arc', 'arg', 'arm', 'arn', 'arp', 'art', 'arw', 'asm', 'ast',
		'ath', 'aus', 'ava', 'ave', 'awa', 'aym', 'aze', 'bad', 'bai', 'bak', 'bal',
		'bam', 'ban', 'baq', 'bas', 'bat', 'bej', 'bel', 'bem', 'ben', 'ber', 'bho',
		'bih', 'bik', 'bin', 'bis', 'bla', 'bnt', 'bos', 'bra', 'bre', 'btk', 'bua',
		'bug', 'bul', 'bur', 'byn', 'cad', 'cai', 'car', 'cat', 'cau', 'ceb', 'cel',
		'cha', 'chb', 'che', 'chg', 'chi', 'chk', 'chm', 'chn', 'cho', 'chp', 'chr',
		'chu', 'chv', 'chy', 'cmc', 'cop', 'cor', 'cos', 'cpe', 'cpf', 'cpp', 'cre',
		'crh', 'crp', 'csb', 'cus', 'cze', 'dak', 'dan', 'dar', 'day', 'del', 'den',
		'dgr', 'din', 'div', 'doi', 'dra', 'dsb', 'dua', 'dum', 'dut', 'dyu', 'dzo',
		'efi', 'egy', 'eka', 'elx', 'eng', 'enm', 'epo', 'est', 'ewe', 'ewo', 'fan',
		'fao', 'fat', 'fij', 'fil', 'fin', 'fiu', 'fon', 'fre', 'frm', 'fro', 'frr',
		'frs', 'fry', 'ful', 'fur', 'gaa', 'gay', 'gba', 'gem', 'geo', 'ger', 'gez',
		'gil', 'gla', 'gle', 'glg', 'glv', 'gmh', 'goh', 'gon', 'gor', 'got', 'grb',
		'grc', 'gre', 'grn', 'gsw', 'guj', 'gwi', 'hai', 'hat', 'hau', 'haw', 'heb',
		'her', 'hil', 'him', 'hin', 'hit', 'hmn', 'hmo', 'hrv', 'hsb', 'hun', 'hup',
		'iba', 'ibo', 'ice', 'ido', 'iii', 'ijo', 'iku', 'ile', 'ilo', 'ina', 'inc',
		'ind', 'ine', 'inh', 'ipk', 'ira', 'iro', 'ita', 'jav', 'jbo', 'jpn', 'jpr',
		'jrb', 'kaa', 'kab', 'kac', 'kal', 'kam', 'kan', 'kar', 'kas', 'kau', 'kaw',
		'kaz', 'kbd', 'kha', 'khi', 'khm', 'kho', 'kik', 'kin', 'kir', 'kmb', 'kok',
		'kom', 'kon', 'kor', 'kos', 'kpe', 'krc', 'krl', 'kro', 'kru', 'kua', 'kum',
		'kur', 'kut', 'lad', 'lah', 'lam', 'lao', 'lat', 'lav', 'lez', 'lim', 'lin',
		'lit', 'lol', 'loz', 'ltz', 'lua', 'lub', 'lug', 'lui', 'lun', 'luo', 'lus',
		'mac', 'mad', 'mag', 'mah', 'mai', 'mak', 'mal', 'man', 'mao', 'map', 'mar',
		'mas', 'may', 'mdf', 'mdr', 'men', 'mga', 'mic', 'min', 'mis', 'mkh', 'mlg',
		'mlt', 'mnc', 'mni', 'mno', 'moh', 'mon', 'mos', 'mul', 'mun', 'mus', 'mwl',
		'mwr', 'myn', 'myv', 'nah', 'nai', 'nap', 'nau', 'nav', 'nbl', 'nde', 'ndo',
		'nds', 'nep', 'new', 'nia', 'nic', 'niu', 'nno', 'nob', 'nog', 'non', 'nor',
		'nqo', 'nso', 'nub', 'nwc', 'nya', 'nym', 'nyn', 'nyo', 'nzi', 'oci', 'oji',
		'ori', 'orm', 'osa', 'oss', 'ota', 'oto', 'paa', 'pag', 'pal', 'pam', 'pan',
		'pap', 'pau', 'peo', 'per', 'phi', 'phn', 'pli', 'pol', 'pon', 'por', 'pra',
		'pro', 'pus', 'qaa-qtz', 'que', 'raj', 'rap', 'rar', 'roa', 'roh', 'rom',
		'rum', 'run', 'rup', 'rus', 'sad', 'sag', 'sah', 'sai', 'sal', 'sam', 'san',
		'sas', 'sat', 'scn', 'sco', 'sel', 'sem', 'sga', 'sgn', 'shn', 'sid', 'sin',
		'sio', 'sit', 'sla', 'slo', 'slv', 'sma', 'sme', 'smi', 'smj', 'smn', 'smo',
		'sms', 'sna', 'snd', 'snk', 'sog', 'som', 'son', 'sot', 'spa', 'srd', 'srn',
		'srp', 'srr', 'ssa', 'ssw', 'suk', 'sun', 'sus', 'sux', 'swa', 'swe', 'syc',
		'syr', 'tah', 'tai', 'tam', 'tat', 'tel', 'tem', 'ter', 'tet', 'tgk', 'tgl',
		'tha', 'tib', 'tig', 'tir', 'tiv', 'tkl', 'tlh', 'tli', 'tmh', 'tog', 'ton',
		'tpi', 'tsi', 'tsn', 'tso', 'tuk', 'tum', 'tup', 'tur', 'tut', 'tvl', 'twi',
		'tyv', 'udm', 'uga', 'uig', 'ukr', 'umb', 'und', 'urd', 'uzb', 'vai', 'ven',
		'vie', 'vol', 'vot', 'wak', 'wal', 'war', 'was', 'wel', 'wen', 'wln', 'wol',
		'xal', 'xho', 'yao', 'yap', 'yid', 'yor', 'ypk', 'zap', 'zbl', 'zen', 'zgh',
		'zha', 'znd', 'zul', 'zun', 'zxx', 'zza' ]

	if profiledict['nativelanguage'] not in validlanguages:
		errors = errors + utils.settingsError("{invalid} {nativelanguage}. "
			.format(invalid = utils.getString(30056),
			nativelanguage = utils.getString(30023)))
	if ( profiledict['foreignaudio'] != 'true' and profiledict['foreignaudio'] != 'false' ):
		errors = errors + utils.settingsError("{invalid} {foreignaudio}. "
			.format(invalid = utils.getString(30056),
			foreignaudio = utils.getString(30024)))
	if ( profiledict['encodeafterrip'] != 'true' and profiledict['encodeafterrip'] != 'false' ):
		errors = errors + utils.settingsError("{invalid} {encodeafterrip}. "
			.format(invalid = utils.getString(30056),
			encodeafterrip = utils.getString(30025)))
	if ( profiledict['cleanuptempdir'] != 'true' and profiledict['cleanuptempdir'] != 'false' ):
		errors = errors + utils.settingsError("{invalid} {cleanuptempdir}. "
			.format(invalid = utils.getString(30056),
			cleanuptempdir = utils.getString(30030)))
	if ( profiledict['blackandwhite'] != 'true' and profiledict['blackandwhite'] != 'false' ):
		errors = errors + utils.settingsError("{invalid} {blackandwhite}. "
			.format(invalid = utils.getString(30056),
			blackandwhite = utils.getString(30060)))
	# 30027 == Rip, 30028 == Encode, 30029 == Never
	if ( profiledict['ejectafter'] != utils.getStringLow(30027) and
		profiledict['ejectafter'] != utils.getStringLow(30028) and
		profiledict['ejectafter'] != utils.getStringLow(30029)):
		errors = errors + utils.settingsError("{invalid} {ejectafter}. "
			.format(invalid = utils.getString(30056),
			ejectafter = utils.getString(30026)))
	# 30065 == Notification,
	if ( profiledict['notifyafterrip'] != utils.getStringLow(30065) and
		profiledict['notifyafterrip'] != utils.getStringLow(30066) and
		profiledict['notifyafterrip'] != utils.getStringLow(30067)):
		errors = errors + utils.settingsError("{invalid} {notifyafterrip}. "
			.format(invalid = utils.getString(30056),
			notifyafterrip = utils.getString(30049)))
	if ( profiledict['notifyafterencode'] != utils.getStringLow(30065) and
		profiledict['notifyafterencode'] != utils.getStringLow(30066) and
		profiledict['notifyafterencode'] != utils.getStringLow(30067)):
		errors = errors + utils.settingsError("{invalid} {notifyafterencode}. "
			.format(invalid = utils.getString(30056),
			notifyafterencode = utils.getString(30061)))

	if errors:
		utils.exitFailed(errors, errors)

def buildMakeMKVConCommand(profiledict):
	niceness = ""
	# 30013 == High, 30015 == Low
	if (profiledict['niceness'] == utils.getString(30013).lower()
		or profiledict['niceness'] == utils.getString(30015).lower()):
		if (platform.system() == 'Windows'):
			if (profiledict['niceness'] == utils.getStringLow(30013)):
				niceness = "start /wait /b /high "
			else:
				niceness = "start /wait /b /low "
		else:
			if (profiledict['niceness'] == utils.getStringLow(30013)):
				niceness = "nice -n -19 "
			else:
				niceness = "nice -n 19 "

	mintitlelength = str(int(profiledict['mintitlelength']) * 60)

	command = niceness + '"' + profiledict['makemkvpath'] + \
		'" mkv --decrypt disc:0 all --minlength=' + mintitlelength + ' "' + \
		profiledict['tempfolder'] + '"'
	return command

def buildHandBrakeCLICommand(profiledict, f):
	niceness = ""
	# 30013 == High, 30015 == Low, 30014 == Medium
	if (profiledict['niceness'] == utils.getString(30013).lower()
		or profiledict['niceness'] == utils.getString(30015).lower()):
		if (platform.system() == 'Windows'):
			if (profiledict['niceness'] == utils.getStringLow(30013)):
				niceness = "start /wait /b /high "
			else:
				niceness = "start /wait /b /low "
		else:
			if (profiledict['niceness'] == utils.getStringLow(30013)):
				niceness = "nice -n -19 "
			else:
				niceness = "nice -n 19 "

	if profiledict['resolution'] == '1080':
		maxwidth = ' --maxWidth 1920'
	elif profiledict['resolution'] == '720':
		maxwidth = ' --maxWidth 1280'
	elif profiledict['resolution'] == '480':
		maxwidth = ' --maxWidth 640'

	if profiledict['quality'] == utils.getStringLow(30013):
		quality = ""
	elif profiledict['quality'] == utils.getStringLow(30014):
		quality = " -q 25 "
	elif profiledict['quality'] == utils.getStringLow(30015):
		quality = " -q 26 "

	if profiledict['blackandwhite'] == 'true':
		blackandwhite = " --grayscale "
	else:
		blackandwhite = ""

	additionalhandbrakeargs = " " + profiledict['additionalhandbrakeargs']

	# To make things easier when we rip foreign films, we just grab all the audio
	# tracks. Otherwise it can be hard to grab just the native language of the
	# movie and the native language of the user. Since grabbing all audio tracks
	# doesn't appear to be an option with HandBrake, I just grab the first ten
	# tracks. When you list audio tracks here that don't exist, it doesn't seem
	# to error out or anything.
	if profiledict['foreignaudio'] == 'true':
		audiotracks = " -a 1,2,3,4,5,6,7,8,9,10 "
	else:
		audiotracks = ""

	command = '{niceness} "{handbrakeclipath}" -i "{filename}" -o "{destination}"'\
		' -f mkv -d slower -N {nativelanguage} --native-dub -m -Z "High Profile" -s'\
		' 1{audiotracks}{quality}{blackandwhite}{maxwidth}{additionalhandbrakeargs}'\
		.format(niceness = niceness, handbrakeclipath = profiledict['handbrakeclipath'],
		filename = f, destination = os.path.join(profiledict['destinationfolder'],
		os.path.basename(f).replace('_', ' ')), nativelanguage = profiledict['nativelanguage'],
		audiotracks = audiotracks, quality = quality, blackandwhite = blackandwhite,
		maxwidth = maxwidth, additionalhandbrakeargs = additionalhandbrakeargs)

	return command

def getParams(argv):
	param = {}
	if(len(argv) > 1):
		for i in argv:
			args = i
			if(args.startswith('?')):
				args = args[1:]
			param.update(dict(urlparse.parse_qsl(args)))

	return param

if __name__ == '__main__':
	sys.exit(main(sys.argv))
