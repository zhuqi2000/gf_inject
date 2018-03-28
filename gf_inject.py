#!/bin/python
"""
GF-5卫星姿轨控分系统注数生成工具V1.00

编写人：朱琦
"""

import wx
import os
import math
import sys
import datetime

wildcard = u"文本文件(*.txt)|*.txt|"   \
           u"All Files(*.*)|*.*"

strInfo = u"GF-5卫星姿轨控分系统注数生成工具V1.00\n"  \
                      "软件需求：蔡陈生\n" \
                      "编程实现：朱琦"

class MyInjectFrame(wx.Frame):
    """
    A Frame
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(MyInjectFrame, self).__init__(*args, **kw)

        # create a panel in the frame
        pnl = wx.Panel(self)

        font = wx.Font(12,wx.MODERN,wx.NORMAL,wx.BOLD)
        
        # 主界面设计
        self.st1 = wx.StaticText(pnl, label = "输入遥控地址",pos=(25,25))
        self.textAddr = wx.TextCtrl(pnl,pos=(125,25),value="0002")
        typeList = ['单精度浮点数','双精度浮点数','16位整数','32位整数','J2000毫秒计数']
        self.st2 = wx.StaticText(pnl, label="选择数据类型",pos=(25,75))
        self.comboType =wx.ComboBox(pnl,-1,value = "单精度浮点数",choices = typeList,style = wx.CB_READONLY,pos=(125,75))
        self.comboType.SetSelection(0)
        
        self.stRatio = wx.StaticText(pnl, label = "系数",pos=(250,75))
        self.stRatio.Hide()
        self.textRatio = wx.TextCtrl(pnl,pos=(325,75),value="1.0")
        self.textRatio.Hide()
        self.st3 = wx.StaticText(pnl, label = "输入数值",pos=(25,125))
        self.textValue = wx.TextCtrl(pnl,pos=(125,125),size = (175,25),value="0.0")
        
        self.buttonAdd = wx.Button(pnl,label ="加入列表",pos=(325,125))
        self.listInject =wx.ListBox(pnl,-1,style = wx.LB_SINGLE,size=(280,200),pos=(25,175))
        self.listInject.SetFont(font)
        self.listInject.SetForegroundColour(wx.BLUE)
        
        abList = ['A、B机均接受注数','仅A机均接受注数','仅B机均接受注数']
        self.comboAB =wx.ComboBox(pnl,-1,value = "A、B机均接受注数",choices = abList,style = wx.CB_READONLY,pos=(325,180))
        self.comboAB.SetSelection(0)

        self.buttonClear = wx.Button(pnl,label ="清除列表",pos=(325,230))
        self.buttonDel = wx.Button(pnl,label ="删除选中条目",pos=(325,285))        
        self.buttonSave = wx.Button(pnl,label ="存入文件",pos=(325,340))
        
        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("欢迎使用注数生成工具")
        
        #事件绑定
        self.Bind(wx.EVT_COMBOBOX, self.OnSelType, self.comboType)
        self.Bind(wx.EVT_BUTTON, self.OnClickSave, self.buttonSave)
        self.Bind(wx.EVT_BUTTON, self.OnClickAdd, self.buttonAdd)
        self.Bind(wx.EVT_BUTTON, self.OnClickClear, self.buttonClear)
        self.Bind(wx.EVT_BUTTON, self.OnClickDel, self.buttonDel)
		
    def OnSelType(self, event):
        """select in comboType"""
        currentIndex = event.GetSelection()
        if currentIndex == 2 or currentIndex == 3 : 
           self.stRatio.Show()
           self.textRatio.Show()
        else :
           self.stRatio.Hide()
           self.textRatio.Hide()
           
        if currentIndex == 4:
            currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.textValue.SetValue(currentTime)
        else:
            self.textValue.SetValue(str("0.0"))
            
    def OnClickSave(self, event):
        """click buttonSave"""
        dlg = wx.FileDialog(self,message = u"保存文件",
                                defaultDir = os.getcwd(),
                                defaultFile = "",
                                wildcard = wildcard,
                                style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            #校验和初值0
            xorsum = 0
            nCount = self.listInject.GetCount()
            if nCount > 0:
                #设置遥控包头字符串
                strLine = "1E0FC000"
                xorsum = xorsum ^ 0x1e0f
                xorsum = xorsum ^ 0xc000
                
                #包长域=列表（地址、数据）中所有字节长度加方式字2字节减1
                pkg_len = nCount * 4 + 2 - 1
                #包长度限定最大256字节，而包长域是实际包长扣掉包头、长度，再减1，最大为249
                if pkg_len > 249:
                   wx.MessageBox("注数包长度超限，建议分包")
                   pkg_len = 249
                   
                str_len = '%04X' % pkg_len
                strLine = strLine + str_len
                xorsum = xorsum ^ pkg_len

                #方式字：F222\A222\B222
                imodeSel = self.comboAB.GetSelection()
                if imodeSel == 0:
                    strmode = 'F222'
                    wmode=0xf222
                elif imodeSel == 1:
                    strmode = 'A222'
                    wmode=0xa222                    
                elif imodeSel == 2:
                    strmode = 'B222'
                    wmode=0xb222                    
                else:
                    strmode = 'F222'
                    wmode=0xf222
                    wx.MessageBox("方式字没有该选项")
                    
                xorsum = xorsum ^ wmode
                
                #将方式字加入
                strLine = strLine + strmode
                
                #将列表中地址、数据加入
                for i in range(nCount):
                    strhex = self.listInject.GetString(i)
                    strLine = strLine + strhex
                    straddr = strhex[0:4]
                    strdata = strhex[4:8]
                    waddr = int(straddr,16)
                    wdata = int(strdata,16)
                    xorsum = xorsum ^ waddr
                    xorsum = xorsum ^ wdata

               #将校验和加入串     
                strsum = '%04X' % xorsum
                strLine = strLine + strsum
                
                with open(filename,'w') as fw:
                    fw.write(strLine)
               
        #将列表中数据加上帧头存入指定文件
        dlg.Destroy()
            
    def OnClickAdd(self, event):
        """click buttonAdd"""
        """ 判断地址输入是否合法16进制数,2字节数据"""
        strStartAddress = self.textAddr.GetValue()
        try:
            wStartAddr = int(strStartAddress,16)
            if wStartAddr > 4095 :
                 wx.MessageBox("输入地址超过规定范围，限定为0-FFF")
                 self.textAddr.SetValue("2")
                 wStartAddr = 2
        except ValueError:
            wx.MessageBox("输入必须是16进制数")
            self.textAddr.SetValue("2")
            wStartAddr = 2
            
        strDigit = self.textValue.GetValue()
        selIndex = self.comboType.GetSelection()
        
        if self.comboType.GetSelection() != 4:
            #将字符串转为数值
            try:
               digitnum = float(strDigit)
            except ValueError:
               wx.MessageBox("输入必须是数字（整数或浮点数）")
               self.textValue.SetValue("0")
               digitnum = 0.0
        else:
            try:
               t1 = datetime.datetime.strptime(strDigit, "%Y-%m-%d %H:%M:%S")
            except ValueError:
               wx.MessageBox("输入格式为YYYY-MM-DD H:M:S")
               t1 = datetime.datetime.now()
               self.textValue.SetValue(t1.strftime("%Y-%m-%d %H:%M:%S"))
            t0 = datetime.datetime(2000,1,1,12,0,0)
            digitnum = (t1 - t0).total_seconds() * 1000
            
        #系数判断
        strRadio = self.textRatio.GetValue()
        try:
            radio = float(strRadio)
        except ValueError:
            wx.MessageBox("系数输入必须是数字（整数或浮点数）")
            self.textValue.SetValue("1.0")
            radio = 1.0

        #无穷小判断
        zeroFlag = 0
        if abs(digitnum) < sys.float_info.epsilon:
            zeroFlag = 1            
            
        #计算符号位
        if digitnum < 0:
           flt_S = 1
        else:
           flt_S = 0
           
        str_s = str(flt_S)

        #拆分整数、小数部分，modf返回元组(小数,整数)
        flt_pre = math.modf(abs(digitnum))
        flt_a  = flt_pre[1]
        flt_b  = flt_pre[0]
        serial_a = []
        serial_b = []

        #整数部分逐级模2量化，直至除到0
        serial_a.append(int(flt_a) % 2)
        flt_a = int(flt_a / 2)
        while flt_a > 0:
             serial_a.append(int(flt_a) % 2)
             flt_a = int(flt_a / 2)

        #整数部分顺序要倒过来
        serial_a.reverse()
        #小数部分乘2，取整量化
        for i in range(128):
             flt_c = math.modf(flt_b * 2)
             serial_b.append(int(flt_c[1]))
             flt_b =flt_c[0]

        if len(serial_a) > 1:
           #阶码等于整数部分小数点向左移到1-2位之间的移位次数
           flt_e = len(serial_a) - 1
           #尾数等于移位后小数点后面的部分
           flt_m = serial_a[1:] + serial_b[:] 
        else:
            if (serial_a[0] == 0) and (zeroFlag == 0):
                i=0
                flt_e=0
                while serial_b[i] == 0:
                    i=i+1
                    flt_e = flt_e - 1
                flt_m = serial_b[i+1:]
                flt_e = flt_e - 1
            else:
                flt_m = serial_b[:]
                flt_e=0

        if selIndex == 0 : 
            #单精度浮点数处理
            #阶码加127
            if zeroFlag == 0:
               flt_e = flt_e + 127
            else:
               flt_e = 0
                
            #阶码转2进制，占8位
            str_e = str(bin(flt_e))
            str_e = str_e[2:]
            if len(str_e) > 8:
                wx.MessageBox("超出单精度浮点数范围")
                str_e = str_e[len(str_e)-8:]
            # 阶码如果少于8位应补足    
            while len(str_e) < 8 :
                str_e= "0" + str_e

            #尾数取23位，将列表转为字符串
            str_m=""
            for i in range(23):
                 str_m = str_m + str(flt_m[i])
            #把符号位、阶码、尾数连接起来
            str_binary =str_s + str_e + str_m
            
            #二进制字符串转整数
            dw_binary = int(str_binary,2)

            #尾数转换少1问题的0舍1入补足，如果第23位尾数为1，则需要加1
            if flt_m[23] == 1:
                dw_binary = dw_binary + 1

            #将整数转16进制字符串
            strHex = '%08X' % dw_binary

            #地址处理
            wAdd = wStartAddr
            #加入地址1、数据1
            strAdd = '%04X' % wAdd
            
            strAdd = strAdd + strHex[0:4]
            #加入列表
            self.listInject.Append(strAdd)

            #加入地址2、数据2
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strHex[4:8]
            #加入列表
            self.listInject.Append(strAdd)
            
        elif selIndex == 1 :
            #双精度浮点数处理
            #阶码加1023
            if zeroFlag == 0:
               flt_e = flt_e + 1023
            else:
               flt_e = 0

            #阶码转2进制，占11位
            str_e = str(bin(flt_e))
            str_e = str_e[2:]
            if len(str_e) > 11:
                wx.MessageBox("超出双精度浮点数范围")
                str_e = str_e[len(str_e)-8:]
            # 阶码如果少于11位应补足    
            while len(str_e) < 11 :
                str_e= "0" + str_e

            #尾数取52位，将列表转为字符串
            str_m=""
            for i in range(52):
                 str_m = str_m + str(flt_m[i])
            
            #把符号位、阶码、尾数连接起来
            str_binary =str_s + str_e + str_m
            
            #二进制字符串转整数
            dw_binary = int(str_binary,2)

            #将整数转16进制字符串
            strHex = '%016X' % dw_binary

            #地址处理
            wAdd = wStartAddr
            #加入地址1、数据1
            strAdd = '%04X' % wAdd
            
            strAdd = strAdd + strHex[0:4]
            #加入列表
            self.listInject.Append(strAdd)

            #加入地址2、数据2
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strHex[4:8]
            #加入列表
            self.listInject.Append(strAdd)

            #加入地址3、数据3
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strHex[8:12]
            #加入列表
            self.listInject.Append(strAdd)

            #加入地址4、数据4
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strHex[12:]
            #加入列表
            self.listInject.Append(strAdd)
            
        elif selIndex == 2 :
            #16位整数处理
            wData16 = int(digitnum / radio) % 65536            
            strData = '%04X' % wData16
            wAdd = wStartAddr
            #加入地址、数据
            strAdd = '%04X' % wAdd           
            strAdd = strAdd + strData
            #加入列表
            self.listInject.Append(strAdd)

        elif selIndex == 3 :
            #32位整数处理
            wData32 = int(digitnum / radio) % 0x100000000            
            strData = '%08X' % wData32
            wAdd = wStartAddr
            #加入地址1、数据1
            strAdd = '%04X' % wAdd
            strAdd = strAdd + strData[0:4]
            #加入列表
            self.listInject.Append(strAdd)
            
            #加入地址2、数据2
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strData[4:8]
            #加入列表
            self.listInject.Append(strAdd)
            
        elif selIndex == 4 :
            #J2000毫秒计数处理
            #wx.MessageBox(str(digitnum))
            strData = '%016X' % int(digitnum)
            wAdd = wStartAddr
            #加入地址1、数据1
            strAdd = '%04X' % wAdd
            strAdd = strAdd + strData[4:8]
            #加入列表
            self.listInject.Append(strAdd)
            
            #加入地址2、数据2
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strData[8:12]
            #加入列表
            self.listInject.Append(strAdd)
            
            #加入地址3、数据3
            wAdd = wAdd + 2
            strAdd = '%04X' % wAdd
           
            strAdd = strAdd + strData[12:]
            #加入列表
            self.listInject.Append(strAdd)

        else :
             wx.MessageBox("没有该选项")

    def OnClickClear(self, event):
        """click buttonClear"""
        self.listInject.Clear()

    def OnClickDel(self, event):
        """click buttonDel"""
        self.listInject.Delete(self.listInject.GetSelection())
        
    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox(strInfo,
                      "About GF-5 Inject Data Gen Tool",
                      wx.OK|wx.ICON_INFORMATION)


					  
if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = MyInjectFrame(None, title='GF-5卫星姿轨控分系统注数生成工具',size=(600,500))
    frm.Show()
    app.MainLoop()
