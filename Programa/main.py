import glob
import serial
import os
import csv
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import time
from skimage import morphology
from libcamera import controls
import sys
from PyQt5.QtCore import Qt,QTimer,QSize
from PyQt5.QtGui import QPixmap, QColor, QFontDatabase, QFont, QIcon, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QGraphicsDropShadowEffect, QSizePolicy, QFrame, QStackedWidget, QScrollArea, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QSlider, QComboBox
from gpiozero import PWMLED
import rooter
from picamera2 import Picamera2
import numpy as np
#variables
main_color="#005281"
dark_color="#113042"
light_color="#E1DEE3"
asparagus_color="#679436"
 
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.brightness=50
        self.threshold=127
        self.picam=None
        self.ser=None
        # Configuración de la ventana principal
        self.setWindowTitle("CBOYA")
        self.setGeometry(0, 0, 1024, 600)
        self.showFullScreen()
        #carga del archivo setup
        if os.path.exists("setup.csv"):
            with open("setup.csv","r") as file:
                reader=csv.reader(file)
                data=list(reader)
                if len(data)>=2:
                    self.brightness=int(data[0][0]) if data[0] else 50
                    self.threshold=int(data[1][0]) if data[1] else 127
        else:
            print("no existe setup")
            with open("setup.csv","w",newline="") as file:
                writer=csv.writer(file)
                writer.writerow([50])
                writer.writerow([127])
            self.brightness=50
            self.threshold=127
        #configuracion pwm
        self.led=PWMLED(17)
        self.led.value=self.brightness/100.0
        #cargo la fuente
        font_db=QFontDatabase()
        font_id=font_db.addApplicationFont("media/Itim-Regular.ttf")
        font_family=font_db.applicationFontFamilies(font_id)[0]
        font=QFont(font_family)
        # Crear layout principal
        PrincipalLYT = QVBoxLayout()
        PrincipalLYT.setContentsMargins(0,0,0,0)
        PrincipalLYT.setSpacing(0)
        # Sección superior
        Menu= QWidget(self)
        Menu.setFixedHeight(120)
        Menu.setFixedWidth(1024)
        Menu.setStyleSheet(f"""
            background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 {light_color},stop:0.5 {light_color},stop:0.51 {main_color},stop:1 {main_color})""")
        MenuLYT = QHBoxLayout(Menu)
        MenuLYT.setSpacing(0)
        MenuLYT.setContentsMargins(0,0,0,0)
        # logo y etiqueta
        self.MenuBTNS=[]
        Nombre= QFrame(self)
        Nombre.setFixedHeight(120)
        Nombre.setFixedWidth(256)
        Nombre.setStyleSheet(f"background-color:{light_color}; border-bottom-right-radius: 40px;")
        NombreLYT=QHBoxLayout(Nombre)
        self.MenuBTNS.append(Nombre)
        # Logo
        LogoLBL = QLabel(self)
        pixmap = QPixmap("media/LOGO.png")
        LogoLBL.setPixmap(pixmap)
        LogoLBL.setScaledContents(True)
        LogoLBL.setFixedHeight(110)
        LogoLBL.setFixedWidth(79)
        # texto
        CboyaLBL=QLabel("C-BOYA",self)
        CboyaLBL.setFont(font)
        CboyaLBL.setStyleSheet(f"color:{main_color}; font-size: 42px;")
        #se agrega logo y texto a nombre
        NombreLYT.addWidget(LogoLBL)
        NombreLYT.addWidget(CboyaLBL)
        #se agrega el nombre al menu
        MenuLYT.addWidget(Nombre)
        # Botones
        DiagnosticoBTN=QPushButton("        Modo\n  Diagnóstico", self)
        DiagnosticoBTN.setIcon(self.create_colored_icon("media/DiagnosticoICON.png",QColor(light_color)))
        DiagnosticoBTN.setIconSize(QSize(87,87))
        DiagnosticoBTN.setStyleSheet(f"outline:none;color: {light_color};background-color:{main_color}; border-top-right-radius: 40px;border-top-left-radius: 40px;")
        DiagnosticoBTN.setFont(QFont(font_family,18))
        DiagnosticoBTN.setFixedHeight(120)
        DiagnosticoBTN.setFixedWidth(256)
        MenuLYT.addWidget(DiagnosticoBTN)
        self.MenuBTNS.append(DiagnosticoBTN)
 
        MedicionBTN=QPushButton("        Modo\n     Medición", self)
        MedicionBTN.setIcon(self.create_colored_icon("media/MedicionICON.png",QColor(main_color)))
        MedicionBTN.setIconSize(QSize(87,87))
        MedicionBTN.setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color}; border-top-right-radius: 40px;border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
        MedicionBTN.setFont(QFont(font_family,18))
        MedicionBTN.setFixedHeight(120)
        MedicionBTN.setFixedWidth(256)
        MenuLYT.addWidget(MedicionBTN)
        self.MenuBTNS.append(MedicionBTN)
 
        CalibracionBTN=QPushButton("        Modo\n  Calibración", self)
        CalibracionBTN.setIcon(self.create_colored_icon("media/CalibracionICON.png",QColor(main_color)))
        CalibracionBTN.setIconSize(QSize(87,87))
        CalibracionBTN.setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color}; border-top-right-radius: 40px;border-top-left-radius: 40px; border: 3px solid {main_color};")
        CalibracionBTN.setFont(QFont(font_family,18))
        CalibracionBTN.setFixedHeight(120)
        CalibracionBTN.setFixedWidth(256)
        MenuLYT.addWidget(CalibracionBTN)
        self.MenuBTNS.append(CalibracionBTN)
 
        DiagnosticoBTN.clicked.connect(lambda _,b=DiagnosticoBTN: self.modo_diagnostico(b))
        MedicionBTN.clicked.connect(lambda _,b=MedicionBTN: self.modo_medicion(b))
        CalibracionBTN.clicked.connect(lambda _,b=CalibracionBTN: self.modo_calibracion(b))
        PrincipalLYT.addWidget(Menu)
 
        # Sección inferior
        self.Cuerpo=QStackedWidget(self)
        self.Cuerpo.setStyleSheet(f"background-color:{main_color}")
 
        #Cuerpo Diagnostico
        Diagnostico=QWidget(self)
        DiagnosticoLYT=QHBoxLayout(Diagnostico)
        #texto de notificacion
        self.DiagnosticoLBL=QLabel("",Diagnostico)
        self.DiagnosticoLBL.setStyleSheet(f"color:{light_color};")
        self.DiagnosticoLBL.setAlignment(Qt.AlignTop)
        self.DiagnosticoLBL.setFont(QFont(font_family,15))
        self.DiagnosticoLBL.setWordWrap(True)
        scroll=QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea{{
                outline:none;
                border:none;
            }}
 
            QScrollBar:vertical{{
                outline:none;
                border:none;
                width:20px;
            }}
            QScrollBar::handle:vertical{{
                background:{dark_color};
                border-radius:10px;
                outline:none;
                border:none;
            }}
 
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{{
                height:0px;
            }}
 
        """)
        scroll.setWidget(self.DiagnosticoLBL)
        #boton de inicio
        DiagnosticoInicioBTN=QPushButton("    INICIAR", self)
        DiagnosticoInicioBTN.setIcon(self.create_colored_icon("media/PlayICON.png",QColor(light_color)))
        DiagnosticoInicioBTN.setIconSize(QSize(84,84))
        DiagnosticoInicioBTN.setStyleSheet(f"margin:10px;outline:none;color:{light_color};background-color:{asparagus_color};border-radius:40px;")
        DiagnosticoInicioBTN.setFont(QFont(font_family,33))
        DiagnosticoInicioBTN.setFixedHeight(200)
        DiagnosticoInicioBTN.setFixedWidth(400)
        #adicion al layout
        DiagnosticoLYT.addWidget(scroll)
        DiagnosticoLYT.addWidget(DiagnosticoInicioBTN)
        DiagnosticoInicioBTN.clicked.connect(lambda _,b=DiagnosticoInicioBTN: self.diagnosticar())
        self.Cuerpo.addWidget(Diagnostico)
 
        #######Cuerpo Medicion
        Medicion=QWidget(self)
        MedicionLYT=QHBoxLayout(Medicion)
        #lado izquierdo de medicion
        MedicionLeft=QWidget(self)
        MedicionLeftLYT=QVBoxLayout(MedicionLeft)
        #ingreso de datos
        MedicionIN=QWidget(self)
        MedicionINLYT=QHBoxLayout(MedicionIN)
        #lote
        label=QLabel("LOTE:",self)
        label.setStyleSheet(f"color:{light_color}")
        label.setFont(QFont(font_family,18))
        MedicionINLYT.addWidget(label)
        self.LoteIN=QPushButton("", self)
        self.LoteIN.setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color};border-radius:10px;")
        self.LoteIN.setFont(QFont(font_family,18))
        self.LoteIN.setFixedHeight(30)
        self.LoteIN.setFixedWidth(200)
        self.LoteIN.clicked.connect(lambda: self.Cuerpo.setCurrentIndex(3))
        MedicionINLYT.addWidget(self.LoteIN)
        #replicas
        label=QLabel("REP:",self)
        label.setStyleSheet(f"color:{light_color}")
        label.setFont(QFont(font_family,18))
        MedicionINLYT.addWidget(label)
        self.ReplicaIN=QPushButton("1", self)
        self.ReplicaIN.setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color};border-radius:10px;")
        self.ReplicaIN.setFont(QFont(font_family,18))
        self.ReplicaIN.setFixedHeight(30)
        self.ReplicaIN.setFixedWidth(80)
        self.ReplicaIN.clicked.connect(lambda: self.Cuerpo.setCurrentIndex(4))
        MedicionINLYT.addWidget(self.ReplicaIN)
        #fecha
        label=QLabel("FECHA:",self)
        label.setStyleSheet(f"color:{light_color}")
        label.setFont(QFont(font_family,18))
        MedicionINLYT.addWidget(label)
        self.FechaIN=QPushButton("", self)
        self.FechaIN.setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color};border-radius:10px;")
        self.FechaIN.setFont(QFont(font_family,18))
        self.FechaIN.setFixedHeight(30)
        self.FechaIN.setFixedWidth(150)
        self.FechaIN.clicked.connect(lambda: self.Cuerpo.setCurrentIndex(5))
        MedicionINLYT.addWidget(self.FechaIN)
        MedicionLeftLYT.addWidget(MedicionIN)
        #tabla de registro
        self.MedicionTBL=QTableWidget(self)
        self.MedicionTBL.setColumnCount(5)
        self.MedicionTBL.setHorizontalHeaderLabels(["LOTE","MIN.","PROM.","MAX.","FECHA"])
        self.MedicionTBL.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.MedicionTBL.setFont(QFont(font_family,13))
        self.MedicionTBL.horizontalHeader().setFont(QFont(font_family,13))
        self.MedicionTBL.horizontalHeader().setSectionResizeMode(0,self.MedicionTBL.horizontalHeader().Stretch)
        self.MedicionTBL.setColumnWidth(1,120)
        self.MedicionTBL.setColumnWidth(2,120)
        self.MedicionTBL.setColumnWidth(3,120)
        self.MedicionTBL.setColumnWidth(4,120)
        self.MedicionTBL.verticalHeader().setVisible(False)
        self.MedicionTBL.setEditTriggers(QTableWidget.NoEditTriggers)
        self.MedicionTBL.setStyleSheet(f"""
            QHeaderView::section{{
                outline:none;
                background-color:{dark_color};
                color:white;
                border: 2px solid {light_color};
            }}
 
            QHeaderView::section:first{{
                border-top-left-radius:15px;
                border-bottom-left-radius:15px;
            }}
 
            QHeaderView::section:last{{
                border-top-right-radius:15px;
                border-bottom-right-radius:15px;
            }}
 
            QTableWidget::item{{
                color:{light_color};
 
            }}
            QTableWidget{{
                outline:none;
                gridline-color:{light_color};
            }}
        """)
 
        TableScroll=QScrollArea(self)
        TableScroll.setWidgetResizable(True)
        TableScroll.setStyleSheet(f"""
            QScrollArea{{
                outline:none;
                border:none;
            }}
 
            QScrollBar:vertical{{
                outline:none;
                border:none;
                width:20px;
            }}
            QScrollBar::handle:vertical{{
                background:{dark_color};
                border-radius:10px;
                outline:none;
                border:none;
            }}
 
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{{
                height:0px;
            }}
 
        """)
        TableScroll.setWidget(self.MedicionTBL)
        MedicionLeftLYT.addWidget(TableScroll)
        ExportarBTN=QPushButton("Exportar",self)
        ExportarBTN.clicked.connect(self.modo_exportar)
        MedicionLeftLYT.addWidget(ExportarBTN)
 
        #lado derecho
        MedicionRight=QWidget(self)
        MedicionRightLYT=QVBoxLayout(MedicionRight)
        self.CameraMedLBL=QLabel(Medicion)
        self.CameraMedLBL.setAlignment(Qt.AlignCenter)
        MedicionInicioBTN=QPushButton("  INICIAR", self)
        MedicionInicioBTN.setIcon(self.create_colored_icon("media/PlayICON.png",QColor(light_color)))
        MedicionInicioBTN.setIconSize(QSize(84,84))
        MedicionInicioBTN.setStyleSheet(f"outline:none;color:{light_color};background-color:{asparagus_color};border-radius:40px;")
        MedicionInicioBTN.setFont(QFont(font_family,33))
        MedicionInicioBTN.setFixedHeight(170)
        MedicionInicioBTN.setFixedWidth(60*5)
        MedicionInicioBTN.clicked.connect(self.medir)
        MedicionRightLYT.addWidget(self.CameraMedLBL)
        MedicionRightLYT.addWidget(MedicionInicioBTN)
 
        MedicionLYT.addWidget(MedicionLeft)
        MedicionLYT.addWidget(MedicionRight)
        MedicionLYT.setStretch(0,1)
        MedicionLYT.setStretch(1,0)
 
 
        self.Cuerpo.addWidget(Medicion)
 
        #Cuerpo Calibracion
        Calibracion=QWidget(self)
        CalibracionLYT=QHBoxLayout(Calibracion)
        #cuerpo calibracion izquierdo
        CaliIzquierda=QWidget(self) 
        CaliIzquierdaLYT=QVBoxLayout(CaliIzquierda)
        self.CameraCaliLBL=QLabel(CaliIzquierda)
        self.CameraCaliLBL.setAlignment(Qt.AlignCenter)
        CaliIzquierdaLYT.addWidget(self.CameraCaliLBL)
 
        self.CameraCali2LBL=QLabel(CaliIzquierda)
        self.CameraCali2LBL.setAlignment(Qt.AlignCenter)
        CaliIzquierdaLYT.addWidget(self.CameraCali2LBL)
 
        CalibracionLYT.addWidget(CaliIzquierda)
        #cuerpo calibracion derecha
        CaliDerecha=QWidget(self) 
        CaliDerechaLYT=QVBoxLayout(CaliDerecha)
        label=QLabel("iluminacion",self)
        label.setFont(QFont(font_family,25))
        label.setFixedHeight(25)
        label.setStyleSheet(f"color:{light_color}")
        CaliDerechaLYT.addWidget(label)
        self.LuzSLDR=QSlider(Qt.Horizontal)
        self.LuzSLDR.setMinimum(1)
        self.LuzSLDR.setMaximum(50)
        self.LuzSLDR.setValue(self.brightness)
        self.LuzSLDR.setTickPosition(QSlider.TicksBelow)
        self.LuzSLDR.setTickInterval(5)
        self.LuzSLDR.setFixedHeight(50)
        self.LuzSLDR.setStyleSheet(f"""
            QSlider::groove:horizontal{{
                height: 10px;
                background:{light_color};
                border-radius: 5px;
            }}
            QSlider::handle:horizontal{{
                background:{dark_color};
                width:50px;
                height: 50px;
                border-radius:25px;
                margin: -20px 0;
            }}
            QSlider::sub-page:horizontal{{
                border-radius: 5px;
                background:{dark_color}
            }}
        """)
        self.LuzSLDR.valueChanged.connect(lambda value: setattr(self.led,'value',value/100.0))
        CaliDerechaLYT.addWidget(self.LuzSLDR)
        label=QLabel("umbral",self)
        label.setFont(QFont(font_family,25))
        label.setFixedHeight(25)
        label.setStyleSheet(f"color:{light_color}")
        CaliDerechaLYT.addWidget(label)
        self.UmbralSLDR=QSlider(Qt.Horizontal,self)
        self.UmbralSLDR.setRange(0,255)
        self.UmbralSLDR.setValue(self.threshold)
        self.UmbralSLDR.setFixedHeight(60)
        self.UmbralSLDR.setStyleSheet(f"""
            QSlider::groove:horizontal{{
                height: 10px;
                background:{light_color};
                border-radius: 5px;
            }}
            QSlider::handle:horizontal{{
                background:{dark_color};
                width:50px;
                height: 50px;
                border-radius:25px;
                margin: -20px 0;
            }}
            QSlider::sub-page:horizontal{{
                border-radius: 5px;
                background:{dark_color}
            }}
        """)
        self.UmbralSLDR.valueChanged.connect(lambda value: setattr(self, 'threshold', value))
        CaliDerechaLYT.addWidget(self.UmbralSLDR)
        CaliSaveBTN=QPushButton("GUARDAR", self)
        CaliSaveBTN.setStyleSheet(f"background:{light_color};color:{main_color};border-radius:30px")
        CaliSaveBTN.setFixedHeight(80)
        CaliSaveBTN.setFont(QFont(font_family,20))
        CaliSaveBTN.clicked.connect(self.save_config)
        CaliDerechaLYT.addWidget(CaliSaveBTN)
        CalibracionLYT.addWidget(CaliDerecha)
        self.Cuerpo.addWidget(Calibracion)
 
        #########teclado alfanumerico
        TecladoAlfa=QWidget(self)
        TecladoAlfaLYT=QGridLayout(TecladoAlfa)
        Keys=[
            ['Label','Cancelar','Aceptar'],
            ['1','2','3','4','5','6','7','8','9','0'],
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L','Ñ'],
            ['Z','X','C','V','B','N','M','Borrar']
        ]
 
        for row,key_row in enumerate(Keys):
            for col,key in enumerate(key_row):
                if key == "Label":
                    LabelTecladoAlfa = QLabel("",self)
                    LabelTecladoAlfa.setStyleSheet(f"outline:none;color:{light_color};")
                    LabelTecladoAlfa.setFont(QFont(font_family,33))
                    TecladoAlfaLYT.addWidget(LabelTecladoAlfa,row,col,1,6)
                elif key == "Cancelar":
                    Cancelar = QPushButton(key,self)
                    Cancelar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Cancelar.setFont(QFont(font_family,24))
                    Cancelar.setFixedHeight(Cancelar.height()*2)
                    TecladoAlfaLYT.addWidget(Cancelar,row,6,1,2)
                    Cancelar.clicked.connect(lambda:(self.Cuerpo.setCurrentIndex(1),LabelTecladoAlfa.setText("")))
                elif key == "Aceptar":
                    Aceptar = QPushButton(key,self)
                    Aceptar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Aceptar.setFont(QFont(font_family,24))
                    Aceptar.setFixedHeight(Aceptar.height()*2)
                    TecladoAlfaLYT.addWidget(Aceptar,row,8,1,2)
                    Aceptar.clicked.connect(lambda:(self.LoteIN.setText(LabelTecladoAlfa.text()),LabelTecladoAlfa.setText(""),self.Cuerpo.setCurrentIndex(1)))
                elif key == "Borrar":
                    Borrar = QPushButton(key,self)
                    Borrar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Borrar.setFont(QFont(font_family,24))
                    Borrar.setFixedHeight(Borrar.height()*2)
                    TecladoAlfaLYT.addWidget(Borrar,row,col,1,3)
                    Borrar.clicked.connect(lambda _,lbl=LabelTecladoAlfa:lbl.setText(lbl.text()[:-1]))
                else:
                    Tecla = QPushButton(key,self)
                    Tecla.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Tecla.setFont(QFont(font_family,24))
                    Tecla.setFixedHeight(Tecla.height()*2)
                    TecladoAlfaLYT.addWidget(Tecla,row,col,1,1)
                    Tecla.clicked.connect(lambda _,k=key,lbl=LabelTecladoAlfa:lbl.setText((lbl.text()+k)[:10]))
        self.Cuerpo.addWidget(TecladoAlfa)        
 
        #########teclado replicas
        TecladoNum1=QWidget(self)
        TecladoNum1LYT=QGridLayout(TecladoNum1)
        Keys=[
            ['Label','Cancelar','Aceptar'],
            ['1','2','3'],
            ['4','5','6'],
            ['Borrar']
        ]
 
        for row,key_row in enumerate(Keys):
            for col,key in enumerate(key_row):
                if key == "Label":
                    LabelTecladoNum1 = QLabel("",self)
                    LabelTecladoNum1.setStyleSheet(f"outline:none;color:{light_color};")
                    LabelTecladoNum1.setFont(QFont(font_family,33))
                    TecladoNum1LYT.addWidget(LabelTecladoNum1,row,col,1,1)
                elif key == "Cancelar":
                    Cancelar = QPushButton(key,self)
                    Cancelar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Cancelar.setFont(QFont(font_family,24))
                    Cancelar.setFixedHeight(Cancelar.height()*2)
                    TecladoNum1LYT.addWidget(Cancelar,row,col,1,1)
                    Cancelar.clicked.connect(lambda:(self.Cuerpo.setCurrentIndex(1),LabelTecladoNum1.setText("")))
                elif key == "Aceptar":
                    Aceptar = QPushButton(key,self)
                    Aceptar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Aceptar.setFont(QFont(font_family,24))
                    Aceptar.setFixedHeight(Aceptar.height()*2)
                    TecladoNum1LYT.addWidget(Aceptar,row,col,1,1)
                    Aceptar.clicked.connect(lambda:(self.ReplicaIN.setText(LabelTecladoNum1.text()),LabelTecladoNum1.setText(""),self.Cuerpo.setCurrentIndex(1)))
                elif key == "Borrar":
                    Borrar = QPushButton(key,self)
                    Borrar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Borrar.setFont(QFont(font_family,24))
                    Borrar.setFixedHeight(Borrar.height()*2)
                    TecladoNum1LYT.addWidget(Borrar,row,col,1,1)
                    Borrar.clicked.connect(lambda _,lbl=LabelTecladoNum1:lbl.setText(lbl.text()[:-1]))
                else:
                    Tecla = QPushButton(key,self)
                    Tecla.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Tecla.setFont(QFont(font_family,24))
                    Tecla.setFixedHeight(Tecla.height()*2)
                    TecladoNum1LYT.addWidget(Tecla,row,col,1,1)
                    Tecla.clicked.connect(lambda _,k=key,lbl=LabelTecladoNum1:lbl.setText((lbl.text()+k)[:1]))
        self.Cuerpo.addWidget(TecladoNum1)        
 
        #########teclado fecha
        TecladoDate=QWidget(self)
        TecladoDateLYT=QGridLayout(TecladoDate)
        Keys=[
            ['Label','Cancelar','Aceptar'],
            ['1','2','3'],
            ['4','5','6'],
            ['7','8','9'],
            ['/','0','Borrar']
        ]
 
        for row,key_row in enumerate(Keys):
            for col,key in enumerate(key_row):
                if key == "Label":
                    LabelTecladoDate = QLabel("",self)
                    LabelTecladoDate.setStyleSheet(f"outline:none;color:{light_color};")
                    LabelTecladoDate.setFont(QFont(font_family,33))
                    TecladoDateLYT.addWidget(LabelTecladoDate,row,col,1,1)
                elif key == "Cancelar":
                    Cancelar = QPushButton(key,self)
                    Cancelar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Cancelar.setFont(QFont(font_family,24))
                    Cancelar.setFixedHeight(Cancelar.height()*2)
                    TecladoDateLYT.addWidget(Cancelar,row,col,1,1)
                    Cancelar.clicked.connect(lambda:(self.Cuerpo.setCurrentIndex(1),LabelTecladoDate.setText("")))
                elif key == "Aceptar":
                    Aceptar = QPushButton(key,self)
                    Aceptar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Aceptar.setFont(QFont(font_family,24))
                    Aceptar.setFixedHeight(Aceptar.height()*2)
                    TecladoDateLYT.addWidget(Aceptar,row,col,1,1)
                    Aceptar.clicked.connect(lambda:(self.FechaIN.setText(LabelTecladoDate.text()),LabelTecladoDate.setText(""),self.Cuerpo.setCurrentIndex(1)))
                elif key == "Borrar":
                    Borrar = QPushButton(key,self)
                    Borrar.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Borrar.setFont(QFont(font_family,24))
                    Borrar.setFixedHeight(Borrar.height()*2)
                    TecladoDateLYT.addWidget(Borrar,row,col,1,1)
                    Borrar.clicked.connect(lambda _,lbl=LabelTecladoDate:lbl.setText(lbl.text()[:-1]))
                else:
                    Tecla = QPushButton(key,self)
                    Tecla.setStyleSheet(f"outline:none;background-color:{light_color};color:{main_color};border-radius:20px;")
                    Tecla.setFont(QFont(font_family,24))
                    Tecla.setFixedHeight(Tecla.height()*2)
                    TecladoDateLYT.addWidget(Tecla,row,col,1,1)
                    Tecla.clicked.connect(lambda _,k=key,lbl=LabelTecladoDate:lbl.setText((lbl.text()+k)[:10]))
        self.Cuerpo.addWidget(TecladoDate)        
 
        ########selector de usb
        self.USB=QWidget(self)
        self.USBLYT=QVBoxLayout(self.USB)
        self.Cuerpo.addWidget(self.USB)
 
 
        PrincipalLYT.addWidget(self.Cuerpo)
        # Asignar el layout principal
        self.setLayout(PrincipalLYT)
        #temporizador
        self.timer=QTimer()
        self.timer.timeout.connect(self.LiveView)
        self.timer.stop()
 
        QTimer.singleShot(1000,self.diagnosticar)
 
    def medir(self):
        self.timer.start(30)
        send="medicion\n"
        self.ser.write(send.encode())
        send=self.ReplicaIN.text()+"\n"
        self.ser.write(send.encode())
        respuesta=""
        while True:
            if self.ser.in_waiting>0:
                respuesta = self.ser.readline().decode().strip()
                break
        print(f"{respuesta}")
        if respuesta=="rM":
            for i in range(1,1+int(self.ReplicaIN.text())):
                send="sigM\n"
                self.ser.write(send.encode())
                respuesta=""
                while True:
                    if self.ser.in_waiting>0:
                        respuesta = self.ser.readline().decode().strip()
                        break
                print(f"{respuesta}")
                if respuesta=="rm":
                    for j in range(1,7):
                        print(f"foto {j} de muestra {i}")
                        respuesta=""
                        send="next\n"
                        self.ser.write(send.encode())
                        while True:
                            if self.ser.in_waiting>0:
                                respuesta = self.ser.readline().decode().strip()
                                break
                        print(f"{respuesta}")
                        if respuesta=="r":
                            try:
                                frame=self.picam.capture_array()
                                distancias=rooter.rooteador(frame,self.threshold)
                            except Exception as e:
                                QMessageBox.critical(self,"Error",f"Error en calculo\n{e}")
                            if distancias is not None:
                                print(f"Numero total de distancias calculadas: {len(distancias)}")
                                for k, distancia in enumerate(distancias):
                                    print(f"Distancia {k+1}: {distancia:.3f} mm")
                send="Ok\n"
                self.ser.write(send.encode())
                respuesta=""
                while True:
                    if self.ser.in_waiting>0:
                        respuesta = self.ser.readline().decode().strip()
                        break
                print(f"{respuesta}")
                if respuesta=="r":
                    print("muestra dejada")
                else:
                    print(f"error: {respuesta}")
                    break
            send="exitM\n"                    
            self.ser.write(send.encode())
        else:
            print(f"else: {respuesta}")
 
        for i in range(1,1+int(self.ReplicaIN.text())):
            self.MedicionTBL.insertRow(self.MedicionTBL.rowCount())
            Lote=QTableWidgetItem(self.LoteIN.text()+f".{i}")
            Lote.setTextAlignment(Qt.AlignCenter)
            self.MedicionTBL.setItem(self.MedicionTBL.rowCount()-1,0,Lote)
            Fecha=QTableWidgetItem(self.FechaIN.text())
            Fecha.setTextAlignment(Qt.AlignCenter)
            self.MedicionTBL.setItem(self.MedicionTBL.rowCount()-1,4,Fecha)
 
    def diagnosticar(self):
        self.DiagnosticoLBL.setText("")
        #diagnostico fisico STM
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"Diagnóstico STM:\n")
        try:
            devices=glob.glob('/dev/ttyACM*')
            self.ser=serial.Serial(devices[0],baudrate=2000000,timeout=1)
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSTM conectada fisicamente\n")
        except:
            self.ser=None
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSTM desconectada fisicamente\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            return None
        #diagnostico digital STM
        try:
            send="diagnostico\n"
            self.ser.write(send.encode())
            start=time.time()
            response=""
            while time.time() - start < 3:
                if self.ser.in_waiting > 0:
                    response=self.ser.readline().decode().strip()
                    break
                time.sleep(0.1)
            if response == "Pollo":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSTM bien configurada\n")
            else:
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSTM mal configurada\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
        except:
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSTM mal configurada\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            return None
        #diagnostico Limit Switches
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"Diagnóstico Switches:\n")
        try:
            send="LIM\n"
            self.ser.write(send.encode())
            response=""
            while True:
                if self.ser.in_waiting > 0:
                    response=self.ser.readline().decode().strip()
                    break
            if response == "r":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSwitches conectados\n")
            else:
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSwitches desconectados\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
        except:
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSwitches desconectados\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            return None
        #diagnostico Motores
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"Diagnóstico Motores:\n")
        try:
            send="MTR\n"
            self.ser.write(send.encode())
            start=time.time()
            response=""
            while time.time() - start < 3:
                if self.ser.in_waiting > 0:
                    response=self.ser.readline().decode().strip()
                    break
                time.sleep(0.1)
            if response == "r1":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor 1 funcionando\n")
            else:
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor 1 desconectado o descompuesto o encoder 1 desconectado o descompuesto\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
            response=self.ser.readline().decode().strip()
            if response == "r2":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor 2 funcionando\n")
            else:
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor 2 desconectado o descompuesto o encoder 2 desconectado o descompuesto\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
        except:
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor 2 desconectado o descompuesto o encoder 2 desconectado o descompuesto\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            return None
        #diagnostico HALL
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"Diagnóstico Sensor Hall:\n")
        try:
            send="HLL\n"
            self.ser.write(send.encode())
            response=""
            while True:
                if self.ser.in_waiting > 0:
                    response=self.ser.readline().decode().strip()
                    break
            if response == "r":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSensor Hall funcionando\n")
            else:
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSensor Hall desconectado o descompuesto\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
        except:
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSensor Hall desconectado o descompuesto\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            return None
        #diagnostico STPR y Presencia
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"Diagnóstico Sistema de carrusel:\n")
        try:
            send="STP\n"
            self.ser.write(send.encode())
            response=""
            while True:
                if self.ser.in_waiting > 0:
                    response=self.ser.readline().decode().strip()
                    break
            if response == "rSrP":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor del carrusel funcionando\n")
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSensor de presencia funcionando\n")   
            elif response == "rSeP":
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSensor de presencia desconectado o descompuesto\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
            else:
                self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tMotor del carrusel desconectado o iman perdido\n")
                self.MenuBTNS[1].setDisabled(True)
                self.MenuBTNS[2].setDisabled(True)
                self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
                self.MenuBTNS[3].setDisabled(True)
                self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
                return None
        except:
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tSensor Hall desconectado o descompuesto\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            return None
        #diagnostico camara
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"Diagnóstico Camara:\n")
        try:
            if self.picam is None:
                self.picam=Picamera2()
                print(self.picam)
                self.picam.configure(self.picam.create_preview_configuration(main={"format":"RGB888"}))
                self.picam.start()
                self.picam.set_controls({"AfMode":controls.AfModeEnum.Continuous})
                self.timer.start(30)
            else:
                self.picam.stop()
                self.picam.start()
                self.picam.set_controls({"AfMode":controls.AfModeEnum.Continuous})
                self.timer.start(30)
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tCámara conectada\n")
        except Exception as e:
            self.picam=None
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"\tCámara desconectada\n")
            self.MenuBTNS[1].setDisabled(True)
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[2].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
            self.MenuBTNS[3].setDisabled(True)
            self.MenuBTNS[3].setStyleSheet(f"outline:none;color:#777777;background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
            print(f"error:{e}")
        send="exit\n"
        self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"-------------------------------------------\n")
        self.ser.write(send.encode())
 
    def rooteador():
        return None
 
 
 
    def exportar(self,button):
        path=os.path.join("/media/TT/"+button.text(),"table.csv")
        try:
            with open(path,mode='w',newline='',encoding='utf-8') as file:
                writer=csv.writer(file)
                headers=[self.MedicionTBL.horizontalHeaderItem(i).text() if self.MedicionTBL.horizontalHeaderItem(i) else "" for i in range(self.MedicionTBL.columnCount())]
                print(headers)
                writer.writerow(headers)
                for row in range(self.MedicionTBL.rowCount()):
                    row_data=[]
                    for col in range(self.MedicionTBL.columnCount()):
                        item=self.MedicionTBL.item(row,col)
                        row_data.append(item.text() if item is not None else "")
                    print(row_data)
                    writer.writerow(row_data)
                    print("escrito")
            print("archivo cerrado")
            QMessageBox.information(self,"Exportacion finalizada",f"el archivo table.csv se guardo en {path}") and self.Cuerpo.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self,"Error",f"no se pudo exportar\n{e}")
 
 
    def save_config(self):
        self.brightness=self.LuzSLDR.value()
        self.threshold=self.UmbralSLDR.value()
        with open("setup.csv","w",newline="") as file:
                writer=csv.writer(file)
                writer.writerow([self.brightness])
                writer.writerow([self.threshold])
 
 
 
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()  # Salir del modo pantalla completa
            event.accept()
 
    def LiveView(self):
        frame=self.picam.capture_array()
        img = Image.fromarray(frame).convert('L')
        binarized = np.array(img.point(lambda p: 255 if p > self.threshold else 0, mode='1')).astype(np.uint8)
        if frame is not None and frame.ndim==3:
            frame=frame[..., ::-1]
            h,w,ch=frame.shape
            bytes_per_line=ch*w
            qt_image=QImage(frame.tobytes(),w,h,bytes_per_line,QImage.Format_RGB888)
            pixmap=QPixmap.fromImage(qt_image)
 
            rounded=QPixmap(pixmap.size())
            rounded.fill(Qt.transparent)
            painter=QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            path=QPainterPath()
            path.addRoundedRect(0,0,pixmap.width(),pixmap.height(),60,60)
            painter.setClipPath(path)
            painter.drawPixmap(0,0,pixmap)
            painter.end()
 
            self.CameraMedLBL.setPixmap(rounded)
            self.CameraMedLBL.setScaledContents(True)
            self.CameraMedLBL.setFixedHeight(48*5)
            self.CameraMedLBL.setFixedWidth(60*5)
 
            self.CameraCaliLBL.setPixmap(rounded)
            self.CameraCaliLBL.setScaledContents(True)
            self.CameraCaliLBL.setFixedHeight(48*4)
            self.CameraCaliLBL.setFixedWidth(60*4)
 
 
            h2,w2=binarized.shape
            binarized=(binarized*255).astype(np.uint8)
            qt_image2=QImage(binarized.tobytes(),w2,h2,w2,QImage.Format_Grayscale8)
            pixmap2=QPixmap.fromImage(qt_image2)
 
            rounded2=QPixmap(pixmap2.size())
            rounded2.fill(Qt.transparent)
            painter=QPainter(rounded2)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            path=QPainterPath()
            path.addRoundedRect(0,0,pixmap2.width(),pixmap2.height(),60,60)
            painter.setClipPath(path)
            painter.drawPixmap(0,0,pixmap2)
            painter.end()
 
            self.CameraCali2LBL.setPixmap(rounded2)
            self.CameraCali2LBL.setScaledContents(True)
            self.CameraCali2LBL.setFixedHeight(48*4)
            self.CameraCali2LBL.setFixedWidth(60*4)
 
 
    def modo_exportar(self):
        for i in reversed(range(self.USBLYT.count())):
            widget=self.USBLYT.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.Cuerpo.setCurrentIndex(6)
        Cancelar = QPushButton("Cancelar",self)
        Cancelar.setFixedHeight(Cancelar.height()*2)
        self.USBLYT.addWidget(Cancelar)
        Cancelar.clicked.connect(lambda:self.Cuerpo.setCurrentIndex(1))
        for device in os.listdir("/media/TT"):
            if device=="NOD_F446RE":
                print("node")
            else:
                deviceBTN=QPushButton(device,self)
                deviceBTN.clicked.connect(lambda _,BTN=deviceBTN:self.exportar(BTN))
                self.USBLYT.addWidget(deviceBTN)
 
    def modo_diagnostico(self,button):
        self.MenuBTNS[0].setStyleSheet(f"background-color:{light_color}; border-bottom-right-radius: 40px;")
        self.MenuBTNS[1].setStyleSheet(f"outline:none;color:{light_color};background-color:{main_color};border-top-right-radius: 40px; border-top-left-radius: 40px;")
        self.MenuBTNS[1].setIcon(self.create_colored_icon("media/DiagnosticoICON.png",QColor(light_color)))
        self.MenuBTNS[2].setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[2].setIcon(self.create_colored_icon("media/MedicionICON.png",QColor(main_color)))
        self.MenuBTNS[3].setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[3].setIcon(self.create_colored_icon("media/CalibracionICON.png",QColor(main_color)))
        self.Cuerpo.setCurrentIndex(0)
        self.timer.stop()
        if 'self.picam' in globals():
            self.picam.stop()
 
 
    def modo_medicion(self,button):
        self.MenuBTNS[0].setStyleSheet(f"background-color:{light_color};")
        self.MenuBTNS[1].setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color}; border-bottom-right-radius: 40px;border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[1].setIcon(self.create_colored_icon("media/DiagnosticoICON.png",QColor(main_color)))
        self.MenuBTNS[2].setStyleSheet(f"outline:none;color:{light_color};background-color:{main_color};border-top-right-radius: 40px;border-top-left-radius: 40px;")
        self.MenuBTNS[2].setIcon(self.create_colored_icon("media/MedicionICON.png",QColor(light_color)))
        self.MenuBTNS[3].setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color}; border-bottom-left-radius: 40px;border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[3].setIcon(self.create_colored_icon("media/CalibracionICON.png",QColor(main_color)))
        self.Cuerpo.setCurrentIndex(1)
        self.picam.start()
        self.timer.start(30)
 
    def modo_calibracion(self,button):
        self.MenuBTNS[0].setStyleSheet(f"background-color:{light_color};")
        self.MenuBTNS[1].setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[1].setIcon(self.create_colored_icon("media/DiagnosticoICON.png",QColor(main_color)))
        self.MenuBTNS[2].setStyleSheet(f"outline:none;color:{main_color};background-color:{light_color}; border-bottom-right-radius: 40px;border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[2].setIcon(self.create_colored_icon("media/MedicionICON.png",QColor(main_color)))
        self.MenuBTNS[3].setStyleSheet(f"outline:none;color:{light_color};background-color:{main_color};border-top-right-radius: 40px;border-top-left-radius: 40px;")
        self.MenuBTNS[3].setIcon(self.create_colored_icon("media/CalibracionICON.png",QColor(light_color)))
        self.Cuerpo.setCurrentIndex(2)
        self.picam.start()
        self.timer.start(30)
 
 
    def create_colored_icon(self, image_path, color):
        pixmap=QPixmap(image_path)
        colored_pixmap=QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.transparent)
        painter=QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawPixmap(0,0,pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(),color)
        painter.end()
        return QIcon(colored_pixmap)
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
