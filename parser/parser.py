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

from .zonebourse import cZoneBourse
from .finviz import cFinviz
from .morningstar import cMorningstar
from .yahoofinance import cYahooFinance
from .reuters import cReuters
from .boerse import cBoerse
from .tradingsat import cTradingSat
from .finances import cFinances

class cParser:
	def __init__( self ):
		pass
	
	def Parse( self, iCompanies ):
		for i, company in enumerate( iCompanies, start=1 ):
			print( 'Parse ({}/{}): {} ...'.format( i, len( iCompanies ), company.Name() ) )
			
			parser = cZoneBourse()
			parser.Parse( company )
			parser = cFinviz()
			parser.Parse( company )
			parser = cMorningstar()
			parser.Parse( company )
			# parser = cReuters()
			# parser.Parse( company )
			parser = cYahooFinance()
			parser.Parse( company )
			parser = cBoerse()
			parser.Parse( company )
			parser = cFinances()
			parser.Parse( company )
			parser = cTradingSat()
			parser.Parse( company )
			
			print( '' )
	