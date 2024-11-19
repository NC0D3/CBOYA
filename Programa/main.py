import os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
import time
from skimage import morphology
from libcamera import controls
import sys
from PyQt5.QtCore import Qt,QTimer,QSize
from PyQt5.QtGui import QPixmap, QColor, QFontDatabase, QFont, QIcon, QImage, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsDropShadowEffect, QSizePolicy, QFrame, QStackedWidget
#variables
main_color="#005281"
dark_color="#113042"
light_color="#E1DEE3"
 
 
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.picam=None        
        # Configuración de la ventana principal
        self.setWindowTitle("CBOYA")
        self.setGeometry(0, 0, 1024, 600)
        self.showFullScreen()
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
        DiagnosticoBTN=QPushButton("        Modo\n  Diagnostico", self)
        DiagnosticoBTN.setIcon(self.create_colored_icon("media/DiagnosticoLOGO.png",QColor(light_color)))
        DiagnosticoBTN.setIconSize(QSize(87,87))
        DiagnosticoBTN.setStyleSheet(f"color: {light_color};background-color:{main_color}; border-top-right-radius: 40px;border-top-left-radius: 40px;")
        DiagnosticoBTN.setFont(QFont(font_family,18))
        DiagnosticoBTN.setFixedHeight(120)
        DiagnosticoBTN.setFixedWidth(256)
        MenuLYT.addWidget(DiagnosticoBTN)
        self.MenuBTNS.append(DiagnosticoBTN)
 
        MedicionBTN=QPushButton("        Modo\n     Medición", self)
        MedicionBTN.setIcon(self.create_colored_icon("media/MedicionLOGO.png",QColor(main_color)))
        MedicionBTN.setIconSize(QSize(87,87))
        MedicionBTN.setStyleSheet(f"color:{main_color};background-color:{light_color}; border-top-right-radius: 40px;border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
        MedicionBTN.setFont(QFont(font_family,18))
        MedicionBTN.setFixedHeight(120)
        MedicionBTN.setFixedWidth(256)
        MenuLYT.addWidget(MedicionBTN)
        self.MenuBTNS.append(MedicionBTN)
 
        CalibracionBTN=QPushButton("        Modo\n  Calibración", self)
        CalibracionBTN.setIcon(self.create_colored_icon("media/CalibracionLOGO.png",QColor(main_color)))
        CalibracionBTN.setIconSize(QSize(87,87))
        CalibracionBTN.setStyleSheet(f"color:{main_color};background-color:{light_color}; border-top-right-radius: 40px;border-top-left-radius: 40px; border: 3px solid {main_color};")
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
        self.DiagnosticoLBL=QLabel("diagnostico:\n",Diagnostico)
        self.DiagnosticoLBL.setAlignment(Qt.AlignCenter)
        DiagnosticoInicioBTN=QPushButton("iniciar", self)
        DiagnosticoLYT.addWidget(self.DiagnosticoLBL)
        DiagnosticoLYT.addWidget(DiagnosticoInicioBTN)
        DiagnosticoInicioBTN.clicked.connect(lambda _,b=DiagnosticoInicioBTN: self.diagnosticar())
        self.Cuerpo.addWidget(Diagnostico)
     
        #Cuerpo Medicion
        Medicion=QWidget(self)
        MedicionLYT=QHBoxLayout(Medicion)
        self.CameraMedLBL=QLabel(Medicion)
        self.CameraMedLBL.setStyleSheet("border-radius:20px;")
        self.CameraMedLBL.setAlignment(Qt.AlignCenter)
        tetsto=QLabel("Medicion",self)
        MedicionLYT.addWidget(tetsto)
        MedicionLYT.addWidget(self.CameraMedLBL)
        self.Cuerpo.addWidget(Medicion)
        #Cuerpo Calibracion
        Calibracion=QWidget(self)
        CalibracionLYT=QVBoxLayout(Calibracion)
        self.CameraCaliLBL=QLabel(Calibracion)
        self.CameraCaliLBL.setAlignment(Qt.AlignCenter)
        CalibracionLYT.addWidget(self.CameraCaliLBL)
        self.Cuerpo.addWidget(Calibracion)
        PrincipalLYT.addWidget(self.Cuerpo)
        # Asignar el layout principal
        self.setLayout(PrincipalLYT)
        #temporizador
        self.timer=QTimer()
        self.timer.timeout.connect(self.LiveView)
        self.timer.stop()
 
        QTimer.singleShot(200,self.diagnosticar)
 
    def diagnosticar(self):
        print("entre al diagnostico")
        try:
            if self.picam is None:
                self.picam=Picamera2()
                print(self.picam)
                self.picam.configure(self.picam.create_preview_configuration(main={"format":"RGB888"}))
                self.picam.start()
                self.picam.set_controls({"AfMode":controls.AfModeEnum.Continuous})
            else:
                self.picam.stop()
                self.picam.start()
                self.picam.set_controls({"AfMode":controls.AfModeEnum.Continuous})
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"camara conectada\n")
        except:
            self.picam=None
            self.DiagnosticoLBL.setText(self.DiagnosticoLBL.text()+"camara desconectada\n")
            self.MenuBTNS[2].setDisabled(True)
            self.MenuBTNS[3].setDisabled(True)
 
 
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()  # Salir del modo pantalla completa
            event.accept()
 
    def LiveView(self):
        frame=self.picam.capture_array()
        if frame is not None and frame.ndim==3:
            frame=frame[..., ::-1]
            h,w,ch=frame.shape
            bytes_per_line=ch*w
            qt_image=QImage(frame.tobytes(),w,h,bytes_per_line,QImage.Format_RGB888)
            pixmap=QPixmap.fromImage(qt_image)
            self.CameraMedLBL.setPixmap(pixmap)
            self.CameraMedLBL.setScaledContents(True)
            self.CameraMedLBL.setFixedHeight(48*5)
            self.CameraMedLBL.setFixedWidth(60*5)
            self.CameraCaliLBL.setPixmap(pixmap)
            self.CameraCaliLBL.setScaledContents(False)
 
    def modo_diagnostico(self,button):
        self.MenuBTNS[0].setStyleSheet(f"background-color:{light_color}; border-bottom-right-radius: 40px;")
        self.MenuBTNS[1].setStyleSheet(f"color:{light_color};background-color:{main_color};border-top-right-radius: 40px; border-top-left-radius: 40px;")
        self.MenuBTNS[1].setIcon(self.create_colored_icon("media/DiagnosticoLOGO.png",QColor(light_color)))
        self.MenuBTNS[2].setStyleSheet(f"color:{main_color};background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border-bottom-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[2].setIcon(self.create_colored_icon("media/MedicionLOGO.png",QColor(main_color)))
        self.MenuBTNS[3].setStyleSheet(f"color:{main_color};background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[3].setIcon(self.create_colored_icon("media/CalibracionLOGO.png",QColor(main_color)))
        self.Cuerpo.setCurrentIndex(0)
        self.timer.stop()
        if 'self.picam' in globals():
            self.picam.stop()
 
 
    def modo_medicion(self,button):
        self.MenuBTNS[0].setStyleSheet(f"background-color:{light_color};")
        self.MenuBTNS[1].setStyleSheet(f"color:{main_color};background-color:{light_color}; border-bottom-right-radius: 40px;border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[1].setIcon(self.create_colored_icon("media/DiagnosticoLOGO.png",QColor(main_color)))
        self.MenuBTNS[2].setStyleSheet(f"color:{light_color};background-color:{main_color};border-top-right-radius: 40px;border-top-left-radius: 40px;")
        self.MenuBTNS[2].setIcon(self.create_colored_icon("media/MedicionLOGO.png",QColor(light_color)))
        self.MenuBTNS[3].setStyleSheet(f"color:{main_color};background-color:{light_color}; border-bottom-left-radius: 40px;border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[3].setIcon(self.create_colored_icon("media/CalibracionLOGO.png",QColor(main_color)))
        self.Cuerpo.setCurrentIndex(1)
        self.picam.start()
        self.timer.start(30)
 
    def modo_calibracion(self,button):
        self.MenuBTNS[0].setStyleSheet(f"background-color:{light_color};")
        self.MenuBTNS[1].setStyleSheet(f"color:{main_color};background-color:{light_color};border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[1].setIcon(self.create_colored_icon("media/DiagnosticoLOGO.png",QColor(main_color)))
        self.MenuBTNS[2].setStyleSheet(f"color:{main_color};background-color:{light_color}; border-bottom-right-radius: 40px;border-top-right-radius: 40px; border-top-left-radius: 40px; border: 3px solid {main_color};")
        self.MenuBTNS[2].setIcon(self.create_colored_icon("media/MedicionLOGO.png",QColor(main_color)))
        self.MenuBTNS[3].setStyleSheet(f"color:{light_color};background-color:{main_color};border-top-right-radius: 40px;border-top-left-radius: 40px;")
        self.MenuBTNS[3].setIcon(self.create_colored_icon("media/CalibracionLOGO.png",QColor(light_color)))
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
