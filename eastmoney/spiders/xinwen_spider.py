# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider
from scrapy.selector import HtmlXPathSelector
from scrapy.selector import Selector
from eastmoney.items import EastmoneyItem
from scrapy.http import Request
from scrapy.spiders import BaseSpider
import json

class XinwenSpider(Spider):
    name = "xinwen"
    allowed_domains = ["eastmoney.com"]
    start_urls = [
        "http://datainterface3.eastmoney.com/EM_DataCenter_V3/api/LHBXQSUM/GetLHBXQSUM?tkn=eastmoney&mkt=0&dateNum=&startDateTime=2016-01-15&endDateTime=2016-04-15&sortRule=1&sortColumn=&pageNum=1&pageSize=50&cfg=lhbxqsum"
    ]    
    def parse(self, response):
        r = json.loads(Selector(response).xpath('//p/text()').extract()[0])
        p = 0
        while p < 3:
            url = "http://quote.eastmoney.com/"+r['Data'][0]['Data'][p].split('|')[0]+".html"
            item = EastmoneyItem()
            item['_id'] = r['Data'][0]['Data'][p].split('|')[0]
            item['name'] = r['Data'][0]['Data'][p].split('|')[1]    
            yield Request(url, meta={'item':item}, callback=self.parse_stock)
            p = p + 1
    def parse_stock(self,response):
        item = response.meta['item']
        url = 'http://guba.eastmoney.com/list,' + item['_id'] + ',1,f_1.html'
        item['number'] = {}
        return Request(url, meta={'item':item}, callback=self.parse_xinwen)
    def parse_xinwen(self,response):
        item = response.meta['item']
        i = 2
        while Selector(response).xpath('//div[@id="articlelistnew"]/div['+str(i)+']/span[5]').extract():
            url = 'http://guba.eastmoney.com' + Selector(response).xpath('//div[@id="articlelistnew"]/div['+str(i)+']/span[3]/a/@href').extract()[0]
            a = len(Selector(response).xpath('//div[@id="articlelistnew"]/div/span[5]').extract())
            item['number'] = [int(Selector(response).xpath(u'//div[@class="pager"]/text()').extract()[0][28:-3]),(int(response.url[42:-5])-1)*80+a-1,int(response.url[42:-5])]
            yield Request(url, meta={'item':item}, callback=self.parse_getxinwen)
            i = i + 1
    def parse_getxinwen(self,response):
        item = response.meta['item']
        dates = {}
        day = []
        time0 = Selector(response).xpath('//*[@id="zwconttb"]/div[2]/text()').extract()[0][4:14]
        k = 0
        for key in item:
            if key == 'xinwen':
                break
            else:
                k = k + 1
        if k == len(item.keys()):
            item['xinwen'] = {}
        k = 0
        for key in item['xinwen']:
            if key == time0:
                content = ''
                i = 0
                while i < len(Selector(response).xpath('//p/text()').extract()) - 3:
                    data = Selector(response).xpath('//p/text()').extract()[i]
                    content = content + data.encode("GBK",'ignore').encode("UTF-8",'ignore')
                    i = i + 1
                item['xinwen'][time0].append({
                    'title':Selector(response).xpath('//*[@id="zwconttbt"]/text()').extract()[0],
                    'author':Selector(response).xpath('//*[@id="zwconttbn"]/strong/a/text()').extract()[0],
                    'content':content,
                    'comments':{}
                })
            else:
                k = k + 1
        if k == len(item['xinwen'].keys()):
            if k == 30:
                return item
            content = ''
            i = 0
            while i < len(Selector(response).xpath('//p/text()').extract()) - 3:
                data = Selector(response).xpath('//p/text()').extract()[i]
                content = content + data.encode("GBK",'ignore').encode("UTF-8",'ignore')
                i = i + 1
            item['xinwen'][time0] = [{
                    'title':Selector(response).xpath('//*[@id="zwconttbt"]/text()').extract()[0],
                    'author':Selector(response).xpath('//*[@id="zwconttbn"]/strong/a/text()').extract()[0],
                    'content':content,
                    'comments':{}
                }]
        day = item['xinwen'][time0]
        for i in range(0, len(day)):
            if day[i]['title'] == Selector(response).xpath('//*[@id="zwconttbt"]/text()').extract()[0]:
                j = 1
                while Selector(response).xpath('//*[@id="zwlist"]/div['+str(j)+']').extract():
                    time1 = Selector(response).xpath('//*[@id="zwlist"]/div['+str(j)+']/div[3]/div/div[2]/text()').extract()[0][4:23]
                    if Selector(response).xpath('//*[@id="zwlist"]/div['+str(j)+']/div[3]/div/div/span/a/text()').extract():
                        name = Selector(response).xpath('//*[@id="zwlist"]/div['+str(j)+']/div[3]/div/div/span/a/text()').extract()[0]
                    else:
                        name = Selector(response).xpath('//*[@id="zwlist"]/div['+str(j)+']/div[3]/div/div/span/span/text()').extract()[0]
                    comment = ''
                    for data in Selector(response).xpath('//*[@id="zwlist"]/div['+str(j)+']/div[3]/div/div[3]/child::text()').extract():
                        comment = comment + data
                    day[i]['comments'][time1] = {
                        'name':name,
                        'comment':comment
                    }
                    j = j + 1
                break
        item['xinwen'][time0] = day
        num = 0
        for key in item['xinwen']:
            num = num + len(item['xinwen'][key])
        if item['number'][1] < item['number'][0] and num == item['number'][1]:
            url = "http://guba.eastmoney.com/list,"+item['_id']+",1,f_"+str(item['number'][2]+1)+".html"
            return Request(url, meta={'item':item}, callback=self.parse_xinwen)
        else:
            return item