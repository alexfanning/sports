# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


pip install lxml
import requests
import pandas as pd

url = 'https://www.teamrankings.com/nfl/ranking/predictive-by-other/'
html = requests.get(url).content
trData = pd.read_html(html)
