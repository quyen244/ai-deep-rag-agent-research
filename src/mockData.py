from typing import Literal

tickers = Literal[
    'AAPL' , 'TSLA' , 'BTC/USDT'
]


timeframes = Literal[
    '5m' , '15m' , '1H' , '4H' , '1D' , '1M' , '1Q' , '1Y'
]

analysis_types = [
    'Technical' , 'Fundamental' , 'Sentiment' 
]

focus_area = Literal[
    'profitability' , 'growth' 
]