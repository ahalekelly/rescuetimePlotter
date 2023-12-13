import requests
from pprint import pprint
import datetime
from contextlib import closing
import codecs
import csv
import pickle
from PIL import Image, ImageDraw, ImageFont
import os

KEY = 'API_KEY'
earliestDate = '2019-02-19'
daysAtATime = 15

def getData(beginDate, endDate, key):
    print("getting "+beginDate.strftime('%Y-%m-%d')+" to "+endDate.strftime('%Y-%m-%d'))
    days = {}
    url = 'https://www.rescuetime.com/anapi/data?format=csv&perspective=interval&resolution_time=minute&restrict_begin='+beginDate.strftime('%Y-%m-%d')+'&restrict_end='+endDate.strftime('%Y-%m-%d')+'&key='+KEY
    print(url)
    with closing(requests.get(url, stream=True)) as r:
        print("data received", len(r.content))
        reader = csv.DictReader(codecs.iterdecode(r.iter_lines(), 'utf-8'), delimiter=',', quotechar='"')
        for row in reader:
            date = row['Date'][:10]
            time = int((int(row['Date'][11:13])*60+int(row['Date'][14:16]))/5)
    #        print(row['Date'],date,time)
            if date not in days:
                days[date] = [[0]*5 for i in range(288)]
            timeSpent = int(row['Time Spent (seconds)'])
    #        print(timeSpent)
            days[date][time][int(row['Productivity'])] += timeSpent
    #            print(days[date][time])
    return days

try:
    file = open('rescuetime.pickle','rb')
    days = pickle.load(file)
    file.close()
except FileNotFoundError:
    print('no pickle found')
    days = {}

dates = sorted(days.keys())

earliestDateObj = datetime.datetime.strptime(earliestDate, '%Y-%m-%d')
print("earliestDate", earliestDateObj)
todayObj = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

while True:
    if len(dates) > 0:
        firstDate = max(dates[0], earliestDate)
        lastDate = dates[-1]
        print("have "+firstDate+" to "+lastDate)
        firstDateObj = datetime.datetime.strptime(firstDate, '%Y-%m-%d')
        lastDateObj = datetime.datetime.strptime(lastDate, '%Y-%m-%d')
        earliestDateObj = datetime.datetime.strptime(earliestDate, '%Y-%m-%d')
        if firstDateObj > earliestDateObj: # go backwards from firstDate to earliestDate
            beginDate = max(firstDateObj-datetime.timedelta(days=daysAtATime), earliestDateObj)
            endDate = firstDateObj
        else: # go forwards from lastDate to today
            beginDate = lastDateObj
            endDate = min(lastDateObj+datetime.timedelta(days=daysAtATime), todayObj)
            print("moving forwards", beginDate, "to", endDate)
    else:
        print("starting from scratch")
        endDate = todayObj
        beginDate = todayObj-datetime.timedelta(days=daysAtATime)
        firstDateObj = beginDate

    days.update(getData(beginDate,endDate,KEY))
    days = {k:v for k,v in days.items() if k >=earliestDate}
    days = dict(sorted(days.items()))
    dates = sorted(days.keys())

    print(len(days), "days, starting on", sorted(days.keys())[0])

    file = open('rescuetime.pickle','wb')
    pickle.dump(days,file)
    file.close()
    print("firstDateObj", firstDateObj)
    print("earliestDateObj", earliestDateObj)
    if firstDateObj <= earliestDateObj and endDate >= todayObj:
        break

boxHeight = 2
boxWidth = 20

#colorWeights = ((255,0,0),(200,0,0),(200,200,200),(0,0,200),(0,0,255))
colorWeights = ((200,200,200),(0,0,150),(0,0,255),(255,0,0),(150,0,0))
#colorWeights = ((200,200,200),(0,0,150),(0,0,255),(200,0,0),(100,0,0))
#colorWeights = ((0,0,150),(0,0,150),(0,0,150),(0,0,150),(0,0,150))
boxSpacing = 0
textBoxHeight = 100

x = 0
y = 0

dateExtents = sorted(days.keys())[::len(days)-1]
numYearBreaks = int(dateExtents[1][0:4])-int(dateExtents[0][0:4])
print("numYearBreaks", numYearBreaks)
imageWidth = (boxWidth+boxSpacing)*(len(days)+numYearBreaks)
imageHeight = boxHeight*288 + textBoxHeight

img = Image.new('RGB',(imageWidth, imageHeight),"white")
draw = ImageDraw.Draw(img)
fnt = ImageFont.truetype("FreeMono.ttf", 100)

draw.rectangle([0, boxHeight*288, imageWidth, imageHeight], fill="black")

events = { # ex: '2019-04-08': 'China'
}

for eventDate in events.keys():
    if eventDate not in days.keys():
        print(eventDate)
        raise ValueError

for dayString, day in days.items():
    for time, interval in enumerate(day):
        color = [int(sum(x)) for x in zip(*[[weightElement*timeSpent/300 for weightElement in weight] for weight,timeSpent in zip(colorWeights,interval)])]
        if color == [0,0,0] and time%24==0:
            if time == 144:
                color = [0,255,0]
            else:
                color = [0,150,0]
        draw.rectangle([x, y, x+boxWidth, y+boxHeight], fill=tuple(color))
        y += boxHeight
    if dayString in events:
        draw.text((x,y),events[dayString],fill='white',font=fnt)

    y = 0
    x += boxWidth + boxSpacing
    if "-12-31" in dayString:
        x += boxWidth + boxSpacing

img.show()
img.save('rescuetime.png')