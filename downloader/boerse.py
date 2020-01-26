#!/usr/bin/env python3
#
# Copyright (c) 2018-19 m-ll. All Rights Reserved.
#
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.
#
# 2b13c8312f53d4b9202b6c8c0f0e790d10044f9a00d8bab3edf3cd287457c979
# 29c355784a3921aa290371da87bce9c1617b8584ca6ac6fb17fb37ba4a07d191
#

import requests
import time

from colorama import init, Fore, Back, Style

class cBoerse:
	def __init__( self ):
		pass
	
	def Download( self, iBrowser, iCompany ):
		print( '	Boerse ... ' + Style.DIM + '[' + iCompany.mBoerse.Url() + ']' )

		if not iCompany.mBoerse.Name():
			print( Fore.CYAN + '	skipping ... (no id)' )
			return
		
		output = iCompany.DataPathFile( iCompany.mBoerse.FileName() )
			
		if not iBrowser.Options().ForceDownload() and output.exists():
			print( Fore.CYAN + '	skipping ... (existing file)' )
			return

		r = requests.get( iCompany.mBoerse.Url(), headers={ 'User-Agent' : iBrowser.Options().UserAgent() } )
		with output.open( 'w' ) as o:
			o.write( r.text )
			
		time.sleep( 1 )
	