# backend/utils/qr_generator.py
import qrcode
from io import BytesIO
import base64

def generate_qr_base64(data: str) -> str:
    # Компактный QR для требования &lt;500 мс генерации (MoSCoW)
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"