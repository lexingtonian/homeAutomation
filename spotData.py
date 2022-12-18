import requests
import json
from dateTimeConversions import MyDateTime
SPOTDATAURL = "https://api.spot-hinta.fi/Today"

#https://api.spot-hinta.fi/Today (tämän päivän hinnat, mitä pienempi "Rank" lukema, sitä halvempi tunti)
#https://api.spot-hinta.fi/JustNow (tämän hetken hinta ja sen "Rank" päivän sisäisesti)
#https://api.spot-hinta.fi/JustNowRank (palauttaa ainoastaan "Rank" tämän hetken tunnille, ei mitään muuta)
#https://api.spot-hinta.fi/JustNowRank/{rank} (palauttaa "bad request", jos tämän hetkinen "Rank" on yli parametrina annetun arvon. Toimii myös "HEAD" requestilla jolloin rajapinta ei palauta muuta kuin otsikkotiedot).
#https://api.spot-hinta.fi/DayForward (huomisen hinnat, kun ne ilmestyy)
#https://api.spot-hinta.fi/TodayAndDayForward (yhdellä haulla tämän päivän hinnat ja huomiset jos ne on olemassa)


#one hour of electical info
class SpotItem:
    rank = -1  #cheapest == 0; most expensive == 24
    price = -1
    hour = -1


class SpotData:
    status = False
    data = 0
    spotItemArray = []
    taxDay = 0.0
    taxNight = 0.0

    #day tax, night tax
    def __init__(self,d,n):
        self.taxDay=d
        self.taxNight=n


    def spotDataOK(self):
        return self.status


    # Open Spot Data url
    # if opening OK, self.status == True
    # populate data structures
    def populateSpotData(self):
        #delete spot array firts so you can re-populate it every dat
        del self.spotItemArray[:]

        #api_response = requests.get('https://api.spot-hinta.fi/TodayAndDayForward')
        try:
            api_response = requests.get(SPOTDATAURL)
        except:
            print("ERROR: Cannot open ", SPOTDATAURL)
            return

        if (api_response.status_code == 200):
            self.status = True
        else:
            print("ERROR; api_response:", api_response, ".")
            return

        self.data = api_response.text

        parse_json = json.loads(self.data)
        tempDateTime = MyDateTime()
        for x in parse_json:
            #next build a teporary spot item
            tmpSpotItem = SpotItem()
            for key, value in x.items():
                if key == 'PriceWithTax':
                    tmpSpotItem.price=float(value)
                if key == 'DateTime':
                    tempDateTime.setHour(value)
                    tmpSpotItem.hour = int(tempDateTime.hour)
                if key == 'Rank':
                    tmpSpotItem.rank = int(value)
            #add new spot item to the spot item array
            self.spotItemArray.append(tmpSpotItem)

    def addTax(self):
        #add day and night tax
        if self.status == False:
            return
        for x in range(24):
            if x>7 and x<21:
                self.spotItemArray[x].price=self.spotItemArray[x].price+self.taxDay
            else:
                self.spotItemArray[x].price = self.spotItemArray[x].price + self.taxNight
        #re-organize rank
        setAlready = []
        here=-1
        rank = 1
        for x in range(24):
            setAlready.append(False)
        for x in range(24):
            price = 999.9 
            #find lowest price
            for y in range(24):
                #print("price. ", price, " self.spotItemArray[y].price: ", self.spotItemArray[y].price, "  setAlready[y]:",setAlready[y])
                if self.spotItemArray[y].price <= price and setAlready[y]==False:
                    price = self.spotItemArray[y].price
                    here=y
                    #print("Here in", here)
            self.spotItemArray[here].rank=rank
            setAlready[here]=True
            #print("Here out", here)
            rank=rank+1

    #for debugging
    def printSpotDataArray(self):

        print("SpotData: ")
        if self.status == False:
            return
        for x in range(24):
            print("Rank: ", self.spotItemArray[x].rank, " Hour: ", self.spotItemArray[x].hour, " Price: ", self.spotItemArray[x].price)

    def createSpotDataReport(self):
        report = "Spot Data: \n"
        if self.status == False:
            report = report + "Cannot generate report as Spot Data not available"
            return report
        for x in range(24):
            report = report + "Rank: " + str(self.spotItemArray[x].rank) + " Hour: " +  str(self.spotItemArray[x].hour) + " Price: " + str(self.spotItemArray[x].price) + "\n"
            #print("Rank: ", self.spotItemArray[x].rank, " Hour: ", self.spotItemArray[x].hour, " Price: ", self.spotItemArray[x].price)
        return report


    def testRunSavings(self, yearlyConsumption):
        #calculate average price of the day and multiply by 3
        #add three cheapest hours of a day
        #add hours 2,3,4
        #calculate price
        average = 0
        cheapest = 0
        night = 0
        hourlyConsumption = (yearlyConsumption / 24) / 365
        for x in range(24):
            average = average + self.spotItemArray[x].price
            if self.spotItemArray[x].rank < 4:
                cheapest = cheapest + self.spotItemArray[x].price
            if self.spotItemArray[x].hour < 5  and self.spotItemArray[x].hour > 1:
                night = night + self.spotItemArray[x].price

        average = (average / 24)
        cheapest = (cheapest / 3)
        night = (night / 3)

        average3 = average*3
        cheapest3 = cheapest * 3
        night3 = night *3

        #print results
        print("Yearly adjustable consumption is ", yearlyConsumption, " kWh")
        print("and the average yearly cost for 3 hours a day hours would be " , average * 24* 365 *hourlyConsumption, " in a year with an average hour prices of ", average, "€")
        print("Average three hours/day in a year:    ", average3 * 365 * hourlyConsumption, "€ where an average spot price is ", average , "€" )
        print("Cheapest three hours/day in a year:   ", cheapest3 * 365 *hourlyConsumption, "€ where the cheapest spot price is ", cheapest , "€")
        print("Night only three hours/day in a year: ", night3 * 365 * hourlyConsumption, "€ where the night spot price is ", night , "€" )
        print("==> thus, saving in a year using home automation is max ", (night3 * 365 * hourlyConsumption)-(cheapest3 * 365 *hourlyConsumption), "€. i.e. ", int(100-((cheapest3 * 365 *hourlyConsumption)/(night3 * 365 * hourlyConsumption))*100), "%")







