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

from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style

class cReuters:
	def __init__( self ):
		pass
	
	def Parse( self, iCompany ):
		print( '	Reuters ...' )

		if not iCompany.mReuters.Symbol():
			print( Fore.CYAN + '	skipping ... (no id)' )
			return
			
		#---

		input = iCompany.DataPathFile( iCompany.mReuters.FileName() )
		
		html_content = ''
		with input.open( 'r', encoding='utf-8' ) as fd:
			html_content = fd.read()
			
		soup = BeautifulSoup( html_content, 'html5lib' )
		
		#---
		
		# iCompany.mReuters.mBNAGrowthType = ''
		
		td = soup.find( string='EPS (TTM) %' ).parent.find_next_sibling()
		td_value = td.string
		iCompany.mReuters.mBNAGrowth['-1'] = td_value
		
		td = td.find_next_sibling()
		td_value = td.string
		iCompany.mReuters.mBNAGrowth['-3'] = td_value
	
		td = td.find_next_sibling()
		td_value = td.string
		iCompany.mReuters.mBNAGrowth['-5'] = td_value
		