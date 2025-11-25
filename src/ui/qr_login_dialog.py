"""二维码登录对话框"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPixmap, QImage
from pathlib import Path
import io
from PIL import Image
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class QRLoginWorker(QThread):
    """二维码登录工作线程"""
    
    # 信号定义
    qr_ready = Signal(object)  # 二维码图像
    login_success = Signal(dict)  # 登录成功，返回auth_data
    login_failed = Signal(str)  # 登录失败，返回错误信息
    
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        
    def run(self):
        """执行登录流程"""
        try:
            import sys
            from pathlib import Path
            
            # 确保mijiaAPI可导入
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "mijia-api"))
            from mijiaAPI import mijiaLogin
            from mijiaAPI.consts import qrURL
            
            login = mijiaLogin()
            
            # 获取二维码登录URL
            data = login._get_index()
            from urllib import parse
            import time
            
            location = data['location']
            location_parsed = parse.parse_qs(parse.urlparse(location).query)
            params = {
                '_qrsize': 240,
                'qs': data['qs'],
                'bizDeviceType': '',
                'callback': data['callback'],
                '_json': 'true',
                'theme': '',
                'sid': 'xiaomiio',
                'needTheme': 'false',
                'showActiveX': 'false',
                'serviceParam': location_parsed['serviceParam'][0],
                '_local': 'zh_CN',
                '_sign': data['_sign'],
                '_dc': str(int(time.time() * 1000)),
            }
            url = qrURL + '?' + parse.urlencode(params)
            ret = login.session.get(url)
            
            if ret.status_code != 200:
                self.login_failed.emit(f'获取二维码URL失败: {ret.text}')
                return
            
            import json
            ret_data = json.loads(ret.text[11:])
            
            if ret_data['code'] != 0:
                self.login_failed.emit(ret_data['desc'])
                return
            
            loginurl = ret_data['loginUrl']
            
            # 生成二维码图像
            from qrcode import QRCode
            qr = QRCode(border=2, box_size=10)
            qr.add_data(loginurl)
            qr.make(fit=True)
            
            # 转换为PIL Image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 发送二维码图像
            self.qr_ready.emit(img)
            
            # 等待扫码登录
            try:
                import requests
                ret = login.session.get(ret_data['lp'], timeout=60, headers={'Connection': 'keep-alive'})
            except requests.exceptions.Timeout:
                self.login_failed.emit('超时，请重试')
                return
            
            if ret.status_code != 200:
                self.login_failed.emit(f'等待登录失败: {ret.text}')
                return
            
            ret_data = json.loads(ret.text[11:])
            
            if ret_data['code'] != 0:
                self.login_failed.emit(ret_data['desc'])
                return
            
            ret = login.session.get(ret_data['location'])
            if ret.status_code != 200:
                self.login_failed.emit(f'获取跳转位置失败: {ret.text}')
                return
            
            cookies = login.session.cookies.get_dict()
            
            auth_data = {
                'userId': ret_data['userId'],
                'ssecurity': ret_data['ssecurity'],
                'deviceId': data['deviceId'],
                'serviceToken': cookies['serviceToken'],
                'cUserId': cookies['cUserId'],
                'expireTime': login._extract_latest_gmt_datetime(cookies).strftime('%Y-%m-%d %H:%M:%S'),
                'account_info': login._get_account_info(ret_data['userId'])
            }
            
            # 保存认证信息
            import json
            from pathlib import Path
            auth_file = self.monitor.config.get('mijia.auth_file', 'config/mijia_auth.json')
            auth_path = Path(auth_file)
            auth_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(auth_path, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, indent=2)
            
            self.login_success.emit(auth_data)
            
        except Exception as e:
            logger.error(f"二维码登录过程出错: {e}")
            self.login_failed.emit(str(e))


class QRLoginDialog(QDialog):
    """二维码登录对话框"""
    
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.auth_data = None
        self.worker = None
        
        self.setWindowTitle("米家账号登录")
        self.setModal(True)
        self.resize(400, 500)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 提示标签
        self.tip_label = QLabel("正在生成二维码...")
        self.tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tip_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self.tip_label)
        
        # 二维码显示标签
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumSize(300, 300)
        self.qr_label.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        layout.addWidget(self.qr_label)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
    def start_login(self):
        """开始登录流程"""
        self.tip_label.setText("请使用米家APP扫描二维码")
        self.status_label.setText("二维码有效期60秒")
        
        # 创建工作线程
        self.worker = QRLoginWorker(self.monitor)
        self.worker.qr_ready.connect(self.on_qr_ready)
        self.worker.login_success.connect(self.on_login_success)
        self.worker.login_failed.connect(self.on_login_failed)
        self.worker.start()
        
    def on_qr_ready(self, qr_img):
        """二维码生成完成"""
        try:
            # 将PIL Image转换为QPixmap
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qimage = QImage()
            qimage.loadFromData(buffer.read())
            
            pixmap = QPixmap.fromImage(qimage)
            scaled_pixmap = pixmap.scaled(
                300, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.qr_label.setPixmap(scaled_pixmap)
            self.status_label.setText("请使用米家APP扫描二维码登录")
            
        except Exception as e:
            logger.error(f"显示二维码失败: {e}")
            self.status_label.setText(f"显示二维码失败: {e}")
            
    def on_login_success(self, auth_data):
        """登录成功"""
        self.auth_data = auth_data
        self.status_label.setText("登录成功！")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
        # 延迟关闭对话框
        QTimer.singleShot(1000, self.accept)
        
    def on_login_failed(self, error_msg):
        """登录失败"""
        self.status_label.setText(f"登录失败: {error_msg}")
        self.status_label.setStyleSheet("color: red;")
        
        QMessageBox.warning(self, "登录失败", error_msg)
        
    def showEvent(self, event):
        """对话框显示事件"""
        super().showEvent(event)
        # 对话框显示后开始登录流程
        QTimer.singleShot(100, self.start_login)
        
    def get_auth_data(self) -> Optional[dict]:
        """获取认证数据"""
        return self.auth_data
