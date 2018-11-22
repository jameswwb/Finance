# -*- coding: utf-8 -*-

import numpy
import pandas
import matplotlib
import mpl_finance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import Formatter
#import datetime

from Logger import Log
#from DataBase import MongoDB
from DataBase import TdxData

class Trend(object):
    
    def __init__(self):
        self.writeLog = Log.Logger('TrendAnalyzer.txt')
    
    # the data format is DataFrame
    def Candlestick_MergeData(self, kData, Index, Count):

        # 设定方向，向上 or 向下
        Direction = 'no'
        #kData[(Index-1):Index].high[-1]
        #kData[Index:(Index+1)].high[-1]
        if Index > 0:   # 此组包含数据前有其他数据，并与本组包含数据不存在包含关系。
            if kData[Index:(Index+1)].high[-1] > kData[(Index-1):Index].high[-1]:
                Direction = 'up'
            elif kData[Index:(Index+1)].low[-1] < kData[(Index-1):Index].low[-1]:
                Direction = 'down'
        elif Index == 0: # 此组包含数据前无其他数据，判断方向 使用本组的前两条数据
            if kData[(Index+1):(Index+2)].high[-1] > kData[Index:(Index+1)].high[-1]:
                Direction = 'up'
            elif kData[(Index+1):(Index+2)].low[-1] < kData[Index:(Index+1)].low[-1]:
                Direction = 'down'
            elif kData[(Index+1):(Index+2)].high[-1] < kData[Index:(Index+1)].high[-1]:
                Direction = 'down'
            elif kData[(Index+1):(Index+2)].low[-1] > kData[Index:(Index+1)].low[-1]:
                Direction = 'up'
            else:
                Direction = 'up'    # it's for the same's case.
        
        tData = kData[Index:(Index+1)]
        open = tData.open[-1]
        close = tData.close[-1]
        high = tData.high[-1]
        low = tData.low[-1]
        
        if Direction == 'up':
            for i in range(Index + 1,(Index+Count)):
                open = open if open > kData[i:(i+1)].open[-1] else kData[i:(i+1)].open[-1]
                close = close if close > kData[i:(i+1)].close[-1] else kData[i:(i+1)].close[-1]
                high = high if high > kData[i:(i+1)].high[-1] else kData[i:(i+1)].high[-1]
                low = low if low > kData[i:(i+1)].low[-1] else kData[i:(i+1)].low[-1]
        elif Direction == 'down':
            for i in range(Index + 1,(Index+Count)):
                open = open if open < kData[i:(i+1)].open[-1] else kData[i:(i+1)].open[-1]
                close = close if close < kData[i:(i+1)].close[-1] else kData[i:(i+1)].close[-1]
                high = high if high < kData[i:(i+1)].high[-1] else kData[i:(i+1)].high[-1]
                low = low if low < kData[i:(i+1)].low[-1] else kData[i:(i+1)].low[-1]
        elif Direction == 'no':
            print ("ERROR : Direction is no, in Candlestick_MergeData")

        tData.open[-1] = open
        tData.close[-1] = close
        tData.high[-1] = high
        tData.low[-1] = low

        return tData

    # kData store K data, format is DataFrame
    # rkData store the result after the RemoveEmbody
    def Candlestick_RemoveEmbody(self, kData):
        rkData = pandas.DataFrame()

        CurData = kData[:1]
        print(CurData) #asd
        CurCount = 1
        for i in range(len(kData)):
            if i != (len(kData) - 1):
                NextData = kData[(i+1):(i+2)]
                print(NextData) #asd
            else:
                #最后一条数据的next data设定为无效值，不存在包含关系。
                #当最后一条数据与之前数据不存在包含关系时，进行最后一条数据的存储
                #当最后一条数据与之前数据存在包含关系时，进行数据的合并并存储
                NextData = pandas.DataFrame([[]])

            #whether there is a containment relationship.
            # 前2组if语句，记录包含关系的个数
            print(CurData.high[-1]) #asd
            if CurData.high[-1] >= NextData.high[-1] and CurData.low[-1] <= NextData.low[-1]:
                CurCount = CurCount + 1

            elif CurData.high[-1] <= NextData.high[-1] and CurData.low[-1] >= NextData.low[-1]:
                CurData = NextData
                CurCount = CurCount + 1
            else:
                # 当组数据存在包含关系时，CurCount > 1， 合并数据 并存储。
                if CurCount > 1:
                    tData = self.Candlestick_MergeData(kData, (i + 1 - CurCount), CurCount)
                    CurCount = 1
                # 在当前数据不存在包含关系时，CurCount = 1，直接存储    
                else:    
                    tData = CurData    
                CurData = NextData
                rkData = pandas.concat([rkData,tData],axis = 0)
        
        return rkData
    
    # 在去掉包含关系后，进行分型处理：顶分型或底分型
    # 在去掉包含关系后，k线转向必有一个顶分型和一个底分型
    def Candlestick_TypeAnalysis(self):
        pass 
    
    #将x轴的浮点数格式化成日期小时分钟
    #默认的x轴格式化是日期被dates.date2num之后的浮点数，因为在上面乘以了1440，所以默认是错误的
    #只能自己将浮点数格式化为日期时间分钟
    #参考https://matplotlib.org/examples/pylab_examples/date_index_formatter.html
    class MyFormatter(Formatter):
        def __init__(self, dates, fmt = '%Y%m%d %H:%M'):
            self.dates = dates
            self.fmt = fmt

        def __call__(self, x, pos = 0):
            'Return the label for time x at position pos'
            ind = int(numpy.round(x))
            #ind就是x轴的刻度数值，不是日期的下标
            return dates.num2date(ind/1440).strftime(self.fmt)

    # 绘制K线
    def Candlestick_Drawing(self, kData):

        # kData need to convert time to Pandas' format.
        tData = kData
        # convert data to pandas format, ignore it, for the continuesly K-line
        #tData['date'] = pandas.to_datetime(tData['date'],format = "%Y/%m/%d-%H:%M")
        #tData['date'] = tData['date'].apply(lambda x:dates.date2num(x)*1440)
        
        #convert to matrix
        tData_mat = tData.values

        asd = range(len(mat_wdyx[:,0]))
        print(asd)

        # 创建一个子图 
        fig,ax = plt.subplots(figsize = (20, 10))
 
        fig.subplots_adjust(bottom = 0.2)
        #开盘,最高,最低,收盘
        mpf.candlestick_ohlc(ax,tData_mat,width=1.2,colorup='r',colordown='green')
        #开盘,收盘,最高,最低
        #mpf.candlestick_ochl(ax,tData_mattData_mat,width=1.2,colorup='r',colordown='green')
        #mpf.candlestick_ohlc(ax, tData_mat, colordown = 'green', colorup = 'red', width = 0.2, alpha = 1)
        
        formatter = self.MyFormatter(tData_mat[:,0])
        ax.xaxis.set_major_formatter(formatter)

        for label in ax.get_xticklabels():
            label.set_rotation(90)
            label.set_horizontalalignment('right')
            
        plt.show()
        #plt.grid(True)

        # 创建一个子图 
        fig, ax = plt.subplots(facecolor=(0.5, 0.5, 0.5))
        fig.subplots_adjust(bottom=0.2)
        # 设置X轴刻度为日期时间
        ax.xaxis_date()
        # X轴刻度文字倾斜45度
        plt.xticks(rotation=45)
        plt.title("股票代码：601558两年K线图")
        plt.xlabel("时间")
        plt.ylabel("股价（元）")
        #开盘,最高,最低,收盘
        #mpf.candlestick_ohlc(ax,kData,width=1.2,colorup='r',colordown='green')
        #开盘,收盘,最高,最低
        #mpf.candlestick_ochl(ax,kData,width=1.2,colorup='r',colordown='green')
        
        plt.grid(True)

if __name__ == '__main__':

    tData = pandas.DataFrame([
        [9.33,   9.37,  9.37, 9.32],
        [9.37,   9.36,  9.37, 9.33],
        [9.34,   9.36,  9.37, 9.34],
        [9.35,   9.36,  9.36, 9.33],
        [9.34,   9.37,  9.37, 9.33],
        [9.37,   9.37,  9.38, 9.36],
        [9.37,   9.41,  9.44, 9.37],
        [9.41,   9.45,  9.46, 9.41],
        [9.45,   9.50,  9.53, 9.44],
        [9.51,   9.59,  9.60, 9.49],
        [9.60,   9.66,  9.69, 9.60],
        [9.67,   9.63,  9.71, 9.63],
        [9.63,   9.85,  9.85, 9.62],
        [9.82,   9.77,  9.83, 9.75],
        [9.76,   9.69,  9.77, 9.65],
        [9.69,   9.63,  9.71, 9.59],
        [9.63,   9.63,  9.63, 9.51],
        [9.62,   9.55,  9.63, 9.55],
        [9.56,   9.63,  9.64, 9.55],
        [9.63,   9.62,  9.63, 9.57],
        [9.62,   9.54,  9.62, 9.54],
        [9.54,   9.57,  9.57, 9.53],
        [9.56,   9.58,  9.58, 9.55],
        [9.58,   9.61,  9.62, 9.57],
        [9.63,   9.62,  9.63, 9.57],
        [9.61,   9.63,  9.64, 9.61],
        [9.62,   9.62,  9.63, 9.61],
        [9.61,   9.64,  9.64, 9.61],
        [9.64,9.61,9.65,9.61],
        [9.60,9.65,9.65,9.60]
        ], 
        columns=['open','close','high','low'], 
        index=[
        '2015-12-02 09:36:00',
        '2015-12-02 09:41:00',
        '2015-12-02 09:46:00',
        '2015-12-02 09:51:00',
        '2015-12-02 09:56:00',
        '2015-12-02 10:01:00',
        '2015-12-02 10:06:00',
        '2015-12-02 10:11:00',
        '2015-12-02 10:16:00',
        '2015-12-02 10:21:00',
        '2015-12-02 10:26:00',
        '2015-12-02 10:31:00',
        '2015-12-02 10:36:00',
        '2015-12-02 10:41:00',
        '2015-12-02 10:46:00',
        '2015-12-02 10:51:00',
        '2015-12-02 10:56:00',
        '2015-12-02 11:01:00',
        '2015-12-02 11:06:00',
        '2015-12-02 11:11:00',
        '2015-12-02 11:16:00',
        '2015-12-02 11:21:00',
        '2015-12-02 11:26:00',
        '2015-12-02 13:02:00',
        '2015-12-02 13:07:00',
        '2015-12-02 13:12:00',
        '2015-12-02 13:17:00',
        '2015-12-02 13:22:00',
        '2015-12-02 13:27:00',
        '2015-12-02 13:32:00'
        ])

    
    Tdx = TdxData.TdxDataEngine(r'C:\Users\wenbwang\Desktop\StockData\New folder')
    filePath = Tdx.GetTdxFileList()
    filePath = Tdx.SearchInFileList("SH", "600000", filePath)
    tData = Tdx.HandlerTdxDataToDataFrame(filePath)

    #print(tData)

    #asd = pandas.DataFrame([["2018/08/27-09:35",10.33 , 10.35 , 10.27 , 10.31 , 2151100.0  ,22191502.0]])
    #asd.columns =  ['date','open','high','low','close','volume','Turnover']

    '''
    #asd1 = asd[:1]
    asd1 = asd.iloc[:1]
    print(asd1)
    print(asd1.open)
    print(asd1.open[0])

    tData1 = tData[:1]
    print(tData1)
    print(tData1.open)
    print(tData1.open[0])
    '''

    T = Trend()
    #result = T.Candlestick_RemoveEmbody(tData)
    #print (result)
    T.Candlestick_Drawing(tData)

    #time = datetime.datetime.strptime('2018/11/08-09:51','%Y/%m/%d-%H:%M')
    time = pandas.to_datetime('2018/11/08-09:51',format="%Y/%m/%d-%H:%M")
    num = dates.date2num(time)
    print(time)
    print(num)
    print("Done")