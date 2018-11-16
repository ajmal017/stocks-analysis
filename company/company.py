#!/usr/bin/python3

import os
import shutil
import requests
from enum import Enum, auto

from bs4 import BeautifulSoup

class cDataMorningstar:
	def __init__( self, iRow=None, iParent=None, iComputeGrowthAverage=False ):
		self.mData = []
		
		self.mTTM = ''
		self.mLatestQuarter = ''
		
		self.mCurrent = ''
		self.m5Years = ''
		self.mIndex = ''
		
		self.mComputeGrowthAverage=iComputeGrowthAverage
		self.mGrowthAverage = ''
		
		self.mParent = iParent
		
		if iRow is not None:
			self.SetRow( iRow )
	
	def __repr__(self):
		return 'cDataMorningstar( [{}], "{}", "{}" )'.format( ', '.join( map( str, self.mData ) ), self.mTTM, self.mLatestQuarter )
	
	def ComputeAverage( self, iData, iYears=8 ):
		if not iData:
			return
		
		data = []
		for value in iData:
			if not value:
				continue
			data.append( float( value ) )
			
		data = sorted( data[-1*iYears:] )
		if len( data ) >= 5:
			del( data[0] )
			del( data[-1] )
		
		return sum( data ) / float( len( data ) )
	
	def Update( self ):
		if self.mComputeGrowthAverage:
			self.mGrowthAverage = '{:.02f}'.format( self.ComputeAverage( self.mData ) )
	
	def SetRow( self, iRow ):
		if self.mParent is None:
			if iRow[-1] == 'TTM':
				self.mData = iRow[1:-1]
				self.mTTM = iRow[-1]
			elif iRow[-1].startswith( 'Latest' ):
				self.mData = iRow[1:-1]
				self.mLatestQuarter = iRow[-1]
			else:
				self.mData = iRow[1:]
		else:
			if self.mParent.mTTM:
				self.mData = iRow[1:-1]
				self.mTTM = iRow[-1]
			elif self.mParent.mLatestQuarter:
				self.mData = iRow[1:-1]
				self.mLatestQuarter = iRow[-1]
			else:
				self.mData = iRow[1:]
		
		self.mData = list( map( self._FixLocale, self.mData ) );
		self.mTTM = self._FixLocale( self.mTTM )
		self.mLatestQuarter = self._FixLocale( self.mLatestQuarter )
		
		self.Update()
			
	def _FixLocale( self, iString ):
		return iString.replace( ',', '.' ).replace( '(', '-' ).replace( ')', '' )
			
	def SetTR( self, iSSection, iTag, iText ):
		td = iSSection.find( iTag, string=iText )
		if not td and self.mParent:		# value doesn't exist, like EBITDA for CNP
			self.mData = [''] * len( self.mParent.mData )
			return
			
		if td.name == 'td':		# for years row
			td = td.find_next_sibling( 'td' )
			while td and 'Current' not in td.string:
				v = td.string
				self.mData.append( v )
				
				td = td.find_next_sibling( 'td' )
				
			self.mCurrent = td.string
			td = td.find_next_sibling( 'td' )
			self.m5Years = td.string
			td = td.find_next_sibling( 'td' )
			self.mIndex = td.string
			
		else:
			td = td.find_parent( 'td' )
			td = td.find_next_sibling( 'td' )
			while len( self.mData ) != len( self.mParent.mData ):
				v = td.find( 'span' ).string
				self.mData.append( v )
				
				td = td.find_next_sibling( 'td' )
			
			self.mCurrent = td.find( 'span' ).string
			td = td.find_next_sibling( 'td' )
			self.m5Years = td.find( 'span' ).string
			td = td.find_next_sibling( 'td' )
			self.mIndex = td.find( 'span' ).string
			
		self.mData = list( map( self._FixLocale2, self.mData ) );
		self.mCurrent = self._FixLocale2( self.mCurrent )
		self.m5Years = self._FixLocale2( self.m5Years )
		self.mIndex = self._FixLocale2( self.mIndex )
		
		self.Update()
			
	def _FixLocale2( self, iString ):
		return iString.replace( ',', '' ).replace( '—', '' )
		
#---

class cZoneBourse:
	class eAppletMode( Enum ):
		kStatic = auto()
		kDynamic = auto()
	
	def __init__( self, iCompany, iName, iCode, iSymbol ):
		self.mCompany = iCompany
		self.mName = iName
		self.mCode = iCode
		self.mSymbol = iSymbol
		
		self.mSoupSociety = None
		
		self.mSoupPER = None
		self.mSoupBNA = None
		self.mPrice = ''
		self.mCurrency = ''
		
		self.mSoupData = None	#TODO: TMP: must have 1 variable per line like morningstar !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		self.mBNAGrowth = []
		self.mBNAGrowthAverage = 0
		self.mDividendsGrowth = []
		self.mDividendsGrowthAverage = 0	# 0.0 < ... < 1.0
		self.mYieldCurrent = 0				# 0.0 < ... < 100.0
		
	def Name( self ):
		return self.mName
	def Code( self ):
		return self.mCode
	def Symbol( self ):
		return self.mSymbol
		
	def UrlData( self ):
		return 'https://www.zonebourse.com/{}-{}/{}/'.format( self.mName, self.mCode, 'fondamentaux' )
	def FileNameData( self ):
		return '{}.{}.zonebourse-data.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
		
	def UrlSociety( self ):
		return 'https://www.zonebourse.com/{}-{}/{}/'.format( self.mName, self.mCode, 'societe' )
	def FileNameSociety( self ):
		return '{}.{}.zonebourse-society.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
		
	def UrlGraphic( self, iAppletMode ):
		applet_mode = 'statique'
		if iAppletMode is self.eAppletMode.kDynamic:
			applet_mode = 'dynamic2'
		return 'https://www.zonebourse.com/{}-{}/{}/&applet_mode={}'.format( self.mName, self.mCode, 'graphiques', applet_mode )
		
	def UrlPricesSimple( self, iDuration, iWidth, iHeight ):
		return 'https://www.zonebourse.com/zbcache/charts/ObjectChart.aspx?Name={0}&Type=Custom&Intraday=1&Width={2}&Height={3}&Cycle=NONE&Duration={1}&TopMargin=10&Render=Candle&ShowName=0'.format( self.mCode, iDuration, iWidth, iHeight )
	def FileNamePricesSimple( self, iYears ):
		return '{}.{}.{}.{}.gif'.format( self.mCompany.Name(), self.mCompany.ISIN(), self.mCode, iYears )
	
	def UrlPricesIchimoku( self ):
		return self.UrlGraphic( self.eAppletMode.kDynamic )
	def FileNamesPricesIchimoku( self ):
		return ( '{}.{}.{}.{}-{}.png'.format( self.mCompany.Name(), self.mCompany.ISIN(), self.mCode, 'content', 'ichimoku' ),
				'{}.{}.{}.{}-{}.png'.format( self.mCompany.Name(), self.mCompany.ISIN(), self.mCode, 'prices', 'ichimoku' ),
				'{}.{}.{}.{}-{}.png'.format( self.mCompany.Name(), self.mCompany.ISIN(), self.mCode, 'times', 'ichimoku' ) )
	
class cFinviz:
	def __init__( self, iCompany, iSymbol ):
		self.mCompany = iCompany
		self.mSymbol = iSymbol
		
		# string 'xx%'
		self.mBNAGrowth = { '-5': '', '0': '', '+1': '', '+5':'' }
		
	def Symbol( self ):
		return self.mSymbol
		
	def Url( self ):
		return 'https://finviz.com/quote.ashx?t={}'.format( self.mSymbol )
	def FileName( self ):
		return '{}.{}.finviz.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
	
class cYahooFinance:
	def __init__( self, iCompany, iSymbol ):
		self.mCompany = iCompany
		self.mSymbol = iSymbol
		
		# string 'xx%'
		self.mGrowth = { '-5': '', '0': '', '+1': '', '+5':'' }
		
	def Symbol( self ):
		return self.mSymbol
		
	def Url( self ):
		if self.mCompany.ISIN() == 'GB0008847096':
			return 'https://uk.finance.yahoo.com/quote/{}/analysis?p={}'.format( self.mSymbol, self.mSymbol )
		else:
			return 'https://finance.yahoo.com/quote/{}/analysis?p={}'.format( self.mSymbol, self.mSymbol )
	def FileName( self ):
		return '{}.{}.yahoofinance.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
	
class cReuters:
	def __init__( self, iCompany, iSymbol ):
		self.mCompany = iCompany
		self.mSymbol = iSymbol
		
		# string 'xx'
		self.mBNAGrowth = { '-5': '', '-3': '', '-1': '' }
		
	def Symbol( self ):
		return self.mSymbol
		
	def Url( self ):
		return 'https://www.reuters.com/finance/stocks/financial-highlights/{}'.format( self.mSymbol )
	def FileName( self ):
		return '{}.{}.reuters.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
	
class cBoerse:
	def __init__( self, iCompany, iName ):
		self.mCompany = iCompany
		self.mName = iName
		
		self.mYears = []
		self.mPER = []
		self.mBNA = []
		self.mBNAGrowth = []
		self.mBNAGrowthAverage = 0
		self.mBNAGrowthAverageLast5Y = 0
		self.mDividend = []
		self.mDividendGrowth = []
		self.mDividendGrowthAverage = 0
		self.mDividendGrowthAverageLast5Y = 0
		self.mDividendYield = []
		
	def Name( self ):
		return self.mName
		
	def Url( self ):
		return 'https://www.boerse.de/fundamental-analyse/{}-Aktie/{}'.format( self.mName, self.mCompany.ISIN() )
	def FileName( self ):
		return '{}.{}.boerse.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
	
class cTradingSat:
	class cDividend:
		class eType( Enum ):
			kNone = 0
			kDividend = 1
			kSplit = 2
			kActionOnly = 3		# add Exceptionel (BIC) ?
			
		def __init__( self ):
			self.mType = self.eType.kNone
			self.mYear = 0
			self.mPrice = 0

	def __init__( self, iCompany, iName ):
		self.mCompany = iCompany
		self.mName = iName
		
		self.mDividends = []
		
	def Name( self ):
		return self.mName
		
	def Url( self ):
		return 'https://www.tradingsat.com/{}-{}/dividende.html'.format( self.mName, self.mCompany.ISIN() )
	def FileName( self ):
		return '{}.{}.tradingsat.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
	
class cFinances:
	class cDividend:
		class eType( Enum ):
			kNone = 0
			kDividend = 1
			kSplit = 2
			kActionOnly = 3		# add Exceptionel (BIC) ?
			
		def __init__( self ):
			self.mType = self.eType.kNone
			self.mYear = 0
			self.mPrice = 0

	def __init__( self, iCompany, iName ):
		self.mCompany = iCompany
		self.mName = iName
		
		self.mDividends = []
		
	def Name( self ):
		return self.mName
		
	def Url( self ):
		return 'http://www.finances.net/dividendes/{}'.format( self.mName )
	def FileName( self ):
		return '{}.{}.finances.html'.format( self.mCompany.Name(), self.mCompany.ISIN() )
	
class cMorningstar:
	def __init__( self, iCompany, iSymbol, iRegion, iCity ):
		self.mCompany = iCompany
		self.mSymbol = iSymbol
		self.mRegion = iRegion
		self.mCity = iCity
		
		self.mISYears = None
		self.mEBITDA = None
		
		self.mBSYears = None
		self.mLongTermDebt = None
		self.mLTDOnEBITDA = cDataMorningstar()
		
		self.mFinancialsYears = None
		self.mFinancialsRevenue = None
		self.mFinancialsNetIncome = None
		self.mFinancialsDividends = None
		self.mFinancialsGrowthDividends = cDataMorningstar( iComputeGrowthAverage=True )
		self.mFinancialsPayoutRatio = None
		self.mFinancialsEarnings = None
		self.mFinancialsBook = None
		self.mFinancialsGrowthBook = cDataMorningstar()
		self.mProfitabilityYears = None
		self.mProfitabilityROE = None
		self.mProfitabilityROI = None
		self.mProfitabilityIC = None
		self.mGrowthYears = None
		self.mGrowthRevenue = None
		self.mGrowthNetIncome = None
		self.mGrowthEarnings = None
		self.mCashFlowFCFOnSales = None
		self.mHealthYears = None
		self.mHealthCurrentRatio = None
		self.mHealthDebtOnEquity = None
		
		self.mValuationYears = cDataMorningstar()
		self.mValuationP2S = cDataMorningstar( iParent=self.mValuationYears )
		self.mValuationPER = cDataMorningstar( iParent=self.mValuationYears )
		self.mValuationP2CF = cDataMorningstar( iParent=self.mValuationYears )
		self.mValuationP2B = cDataMorningstar( iParent=self.mValuationYears )
		self.mValuationEVOnEBITDA = cDataMorningstar( iParent=self.mValuationYears )
		
		self.mFinancialsDividendsYield = cDataMorningstar( iParent=self.mValuationYears )
		self.mFinancialsDividendsYield10Years = cDataMorningstar( iParent=self.mValuationYears )
		self.mFinancialsDividendsYield20Years = cDataMorningstar( iParent=self.mValuationYears )
		self.mUrlDividendCalculator10Years = ''
		self.mUrlDividendCalculator20Years = ''
		
		self.mDividendNextDates = []
		
	def Symbol( self ):
		return self.mSymbol
	def Region( self ):
		return self.mRegion
	def City( self ):
		return self.mCity
		
	def UrlIncomeStatement( self ):
		if self.mCity == 'xetr':
			return 'http://financials.morningstar.com/income-statement/is.html?t={}:{}&region={}&culture=en-US'.format( self.mCity, self.mSymbol, self.mRegion )
		return 'http://financials.morningstar.com/income-statement/is.html?t={}&region={}&culture=en-US'.format( self.mSymbol, self.mRegion )
	def FileNameIncomeStatement( self ):
		return '{}.{}.{}.csv'.format( self.mCompany.Name(), self.mCompany.ISIN(), 'morningstar-income-statement' )
		
	def UrlBalanceSheet( self ):
		if self.mCity == 'xetr':
			return 'http://financials.morningstar.com/balance-sheet/bs.html?t={}:{}&region={}&culture=en-US'.format( self.mCity, self.mSymbol, self.mRegion )
		return 'http://financials.morningstar.com/balance-sheet/bs.html?t={}&region={}&culture=en-US'.format( self.mSymbol, self.mRegion )
	def FileNameBalanceSheet( self ):
		return '{}.{}.{}.csv'.format( self.mCompany.Name(), self.mCompany.ISIN(), 'morningstar-balance-sheet' )
		
	def UrlRatios( self ):
		if self.mCity == 'xetr':
			return 'http://financials.morningstar.com/ratios/r.html?t={}:{}&region={}&culture=en-US'.format( self.mCity, self.mSymbol, self.mRegion )
		return 'http://financials.morningstar.com/ratios/r.html?t={}&region={}&culture=en-US'.format( self.mSymbol, self.mRegion )
	def FileNameRatios( self ):
		return '{}.{}.{}.csv'.format( self.mCompany.Name(), self.mCompany.ISIN(), 'morningstar-ratios' )
		
	def UrlValuation( self ):
		return 'https://www.morningstar.com/stocks/{}/{}/quote.html'.format( self.mCity, self.mSymbol.lower() )
	def FileNameValuation( self ):
		return '{}.{}.{}.html'.format( self.mCompany.Name(), self.mCompany.ISIN(), 'morningstar-valuation' )
		
	def UrlDividends( self ):
		return 'https://www.morningstar.com/stocks/{}/{}/quote.html'.format( self.mCity, self.mSymbol.lower() )
	def FileNameDividends( self ):
		return '{}.{}.{}.html'.format( self.mCompany.Name(), self.mCompany.ISIN(), 'morningstar-dividends' )

class cCompany:
	def __init__( self, iISIN, iZBName, iZBCode, iZBSymbol, iMorningstarRegion, iMorningstarX, iTradingViewSymbol, iYFSymbol, iRSymbol, iFVSymbol, iTSName, iFCName ):
		self.mISIN = iISIN
		self.mName = iZBName
		
		self.mZoneBourse = cZoneBourse( self, iZBName, iZBCode, iZBSymbol )
		self.mFinviz = cFinviz( self, iFVSymbol )
		self.mMorningstar = cMorningstar( self, iZBSymbol, iMorningstarRegion, iMorningstarX )	# ( ..., fra/gbr/usa/..., xpar/xlon/... )
		self.mYahooFinance = cYahooFinance( self, iYFSymbol )
		self.mReuters = cReuters( self, iRSymbol )
		self.mBoerse = cBoerse( self, iZBName )	# use the same name as ZoneBourse, may use anything in fact
		self.mTradingSat = cTradingSat( self, iTSName )
		self.mFinances = cFinances( self, iFCName )
		
		#---
		
		self.mTradingViewSymbol = iTradingViewSymbol	# NYSE:MMM		# Not use yet
		
		self.mDataPath = ''
		self.mImgDirRelativeToHTML = ''
		self.mGroup = ''
		
	#---
	
	def Group( self, iGroup ):
		self.mGroup = iGroup
		
	def ISIN( self ):
		return self.mISIN
	def Name( self ):
		return self.mName
	
	#---
	
	def DataPath( self, iPath=None ):
		if iPath is None:
			return self.mDataPath
		
		previous_value = self.mDataPath
		self.mDataPath = iPath
		return previous_value
	
	def OutputImgPathRelativeToHTMLFile( self, iPath=None ):
		if iPath is None:
			return self.mImgDirRelativeToHTML
		
		previous_value = self.mImgDirRelativeToHTML
		self.mImgDirRelativeToHTML = iPath
		return previous_value
	
	#---
	
	def DataPathFile( self, iFileName ):
		return os.path.join( self.mDataPath, iFileName )
	
	def OutputImgPathFileRelativeToHTMLFile( self, iFileName ):
		return '{}/{}'.format( self.mImgDirRelativeToHTML, iFileName )	# Always '/' as it's for html
	
	#---
	
	def SourceUrlDividendCalculator( self, iYield, iGrowth, iYears ):
		url = 'http://www.dividend-calculator.com/annually.php?yield={:.2f}&yieldgrowth={:.2f}&shares=100&price=100&years={}&do=Calculate'
		return url.format( iYield, iGrowth, iYears )
	
	def AskDividendCalculatorProjection( self, iUrl ):
		req = requests.get( iUrl, headers={ 'User-Agent' : 'Mozilla/5.0' } )
		
		soup = BeautifulSoup( req.text, 'html5lib' )
		results = soup.find( string='With Reinvestment' ).find_parent().find_next_sibling( 'p' ).find_all( 'b' )
		cost_start = results[0].string
		cost_stop = results[1].string
		annual_average = results[4].string.replace( '%', '' )
		
		return annual_average
	
	#---
	
	def WriteImages( self, iOutputPath ):
		# print( 'WriteImages: {}'.format( self.mName ) )
		
		#TOIMPROVE: with tuple/dict/... like ichimoku (?)
		filename = self.mZoneBourse.FileNamePricesSimple( 9999 )
		shutil.copy( self.DataPathFile( filename ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filename ) ) )
		filename = self.mZoneBourse.FileNamePricesSimple( 10 )
		shutil.copy( self.DataPathFile( filename ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filename ) ) )
		filename = self.mZoneBourse.FileNamePricesSimple( 5 )
		shutil.copy( self.DataPathFile( filename ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filename ) ) )
		filename = self.mZoneBourse.FileNamePricesSimple( 2 )
		shutil.copy( self.DataPathFile( filename ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filename ) ) )
		
		filenames = self.mZoneBourse.FileNamesPricesIchimoku()
		shutil.copy( self.DataPathFile( filenames[0] ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filenames[0] ) ) )
		shutil.copy( self.DataPathFile( filenames[1] ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filenames[1] ) ) )
		shutil.copy( self.DataPathFile( filenames[2] ), os.path.join( iOutputPath, self.OutputImgPathFileRelativeToHTMLFile( filenames[2] ) ) )
	