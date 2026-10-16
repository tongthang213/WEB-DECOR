import sys
import json
import os
import shutil
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt

DATA_FILE = "data.json"
IMAGES_DIR = "images"


class ProductManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Đã đổi tên Ứng dụng cho Tiệm Decor
        self.setWindowTitle("🪴 Quản Lý Web - Tiệm Decor 3D")
        self.resize(1000, 750)
        self.editing_product_id = None
        self.scanned_images = []

        self.init_ui()
        self.load_data_to_table()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- CỘT TRÁI: FORM NHẬP / SỬA LIỆU ---
        form_layout = QVBoxLayout()

        self.form_title = QLabel("<b>Thêm Sản Phẩm Mới</b>")
        self.form_title.setStyleSheet("font-size: 16px; color: #D4B895;")  # Màu Be Gỗ
        form_layout.addWidget(self.form_title)

        form_layout.addWidget(QLabel("Tên sản phẩm:"))
        self.name_input = QLineEdit()
        form_layout.addWidget(self.name_input)

        form_layout.addWidget(QLabel("Giá sản phẩm (VD: 150.000 đ):"))
        self.price_input = QLineEdit()
        form_layout.addWidget(self.price_input)

        form_layout.addWidget(QLabel("Thư mục ảnh (chọn folder chứa ảnh decor):"))
        folder_layout = QHBoxLayout()
        self.folder_path_input = QLineEdit()
        self.folder_path_input.setReadOnly(True)
        folder_layout.addWidget(self.folder_path_input)
        btn_browse = QPushButton("Chọn thư mục...")
        btn_browse.clicked.connect(self.browse_folder)
        folder_layout.addWidget(btn_browse)
        form_layout.addLayout(folder_layout)

        self.img_preview_label = QLabel("Chưa chọn ảnh nào")
        self.img_preview_label.setStyleSheet("color: #888; font-style: italic;")
        form_layout.addWidget(self.img_preview_label)

        form_layout.addWidget(QLabel("Link Video YouTube (Tùy chọn):"))
        self.video_input = QLineEdit()
        form_layout.addWidget(self.video_input)

        form_layout.addWidget(QLabel("Thông tin chi tiết (Đã set mẫu cho đồ Decor):"))
        self.desc_input = QTextEdit()

        # HTML MẶC ĐỊNH DÀNH RIÊNG CHO ĐỒ DECOR / CHẬU CÂY
        default_desc = """<ul>
  <li>🪴 <b>Chất liệu:</b> Nhựa sinh học PLA/PETG cao cấp, an toàn và thân thiện môi trường.</li>
  <li>📐 <b>Không gian:</b> Kích thước hoàn hảo để trang trí bàn làm việc, kệ sách, phòng khách...</li>
  <li>✨ <b>Đặc điểm:</b> Thiết kế 3D độc bản, hoàn thiện bề mặt tỉ mỉ, mang lại điểm nhấn nghệ thuật.</li>
  <li>🛡️ <b>Bảo hành:</b> Đóng gói hộp cát-tông chống sốc an toàn, hỗ trợ đổi trả nếu lỗi do vận chuyển.</li>
</ul>"""
        self.desc_input.setPlainText(default_desc)
        form_layout.addWidget(self.desc_input)

        self.btn_save = QPushButton("Thêm Sản Phẩm")
        # Nút bấm chính màu Be Gỗ sang trọng
        self.btn_save.setStyleSheet(
            "background-color: #D4B895; color: #0F0F0F; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_save.clicked.connect(self.save_product)
        form_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Hủy / Làm mới form")
        self.btn_clear.clicked.connect(self.clear_form)
        form_layout.addWidget(self.btn_clear)

        # --- NÚT ĐẨY CODE LÊN GITHUB CẬP NHẬT TRẠNG THÁI MỚI ---
        self.btn_push = QPushButton("🚀 CẬP NHẬT LÊN WEB DECOR")
        self.btn_push.setStyleSheet(
            "background-color: #0068FF; color: white; font-weight: bold; padding: 12px; margin-top: 15px; border-radius: 5px;")
        self.btn_push.clicked.connect(self.push_to_github)
        form_layout.addWidget(self.btn_push)

        self.btn_pull = QPushButton("⬇️ Lấy Data WEB")
        self.btn_pull.setStyleSheet(
            "background-color: #171717; color: #D4B895; border: 1px solid #D4B895; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.btn_pull.clicked.connect(self.pull_from_github)
        form_layout.addWidget(self.btn_pull)

        main_layout.addLayout(form_layout, 4)

        # --- CỘT PHẢI: BẢNG DANH SÁCH ---
        table_layout = QVBoxLayout()
        table_layout.addWidget(QLabel("<b>Danh Sách Sản Phẩm (Tiệm Decor)</b>"))

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Tên sản phẩm", "Giá"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.edit_product)
        table_layout.addWidget(self.table)

        self.btn_delete = QPushButton("Xóa Mẫu Đã Chọn")
        self.btn_delete.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 8px;")
        self.btn_delete.clicked.connect(self.delete_product)
        table_layout.addWidget(self.btn_delete)

        main_layout.addLayout(table_layout, 6)

    def load_data_to_table(self):
        self.table.setRowCount(0)
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for row_idx, item in enumerate(data):
                    self.table.insertRow(row_idx)
                    self.table.setItem(row_idx, 0, QTableWidgetItem(str(item.get("id", ""))))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(item.get("name", "")))
                    self.table.setItem(row_idx, 2, QTableWidgetItem(item.get("price", "")))
        except Exception as e:
            print("Lỗi load data:", e)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh")
        if folder:
            self.folder_path_input.setText(folder)
            valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
            images = [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
            images.sort()
            self.scanned_images = [os.path.join(folder, f) for f in images]
            self.img_preview_label.setText(f"Đã tìm thấy {len(self.scanned_images)} ảnh.")

    def save_product(self):
        name = self.name_input.text().strip()
        price = self.price_input.text().strip()
        video = self.video_input.text().strip()
        desc = self.desc_input.toPlainText().strip()

        if not name or not price:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Giá sản phẩm!")
            return

        if not os.path.exists(DATA_FILE):
            data = []
        else:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

        if self.editing_product_id is None:
            new_id = 1 if not data else max(item["id"] for item in data) + 1
        else:
            new_id = self.editing_product_id

        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR)

        image_paths = []
        if self.scanned_images:
            product_img_dir = os.path.join(IMAGES_DIR, f"sp_{new_id}")
            if not os.path.exists(product_img_dir):
                os.makedirs(product_img_dir)

            for idx, img_path in enumerate(self.scanned_images):
                ext = os.path.splitext(img_path)[1]
                new_filename = f"img_{idx + 1}{ext}"
                dest_path = os.path.join(product_img_dir, new_filename)
                shutil.copy2(img_path, dest_path)
                image_paths.append(f"{IMAGES_DIR}/sp_{new_id}/{new_filename}")

        product_dict = {
            "id": new_id,
            "name": name,
            "price": price,
            "desc": desc,
            "video_url": video
        }

        if self.editing_product_id is not None:
            # Find and update
            for i, item in enumerate(data):
                if item["id"] == self.editing_product_id:
                    if not image_paths and "images" in item:
                        product_dict["images"] = item["images"]
                        product_dict["img"] = item.get("img", "")
                    else:
                        product_dict["images"] = image_paths
                        product_dict["img"] = image_paths[0] if image_paths else ""
                    data[i] = product_dict
                    break
            QMessageBox.information(self, "Thành công", "Đã cập nhật sản phẩm!")
        else:
            product_dict["images"] = image_paths
            product_dict["img"] = image_paths[0] if image_paths else ""
            data.append(product_dict)
            QMessageBox.information(self, "Thành công", "Đã thêm sản phẩm mới!")

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.clear_form()
        self.load_data_to_table()

    def edit_product(self, item):
        row = item.row()
        prod_id = int(self.table.item(row, 0).text())

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for prod in data:
            if prod["id"] == prod_id:
                self.editing_product_id = prod_id
                self.form_title.setText(f"<b>Đang Sửa Sản Phẩm ID: {prod_id}</b>")
                self.name_input.setText(prod["name"])
                self.price_input.setText(prod["price"])
                self.video_input.setText(prod.get("video_url", ""))
                self.desc_input.setPlainText(prod.get("desc", ""))
                self.btn_save.setText("Lưu Cập Nhật")
                self.folder_path_input.setText("")
                self.scanned_images = []

                img_count = len(prod.get("images", []))
                self.img_preview_label.setText(f"Sản phẩm đang có {img_count} ảnh. (Chọn thư mục mới để ghi đè)")
                break

    def clear_form(self):
        self.editing_product_id = None
        self.form_title.setText("<b>Thêm Sản Phẩm Mới</b>")
        self.name_input.clear()
        self.price_input.clear()
        self.video_input.clear()
        self.folder_path_input.clear()
        self.scanned_images = []
        self.img_preview_label.setText("Chưa chọn ảnh nào")
        self.btn_save.setText("Thêm Sản Phẩm")

        default_desc = """<ul>
  <li>🪴 <b>Chất liệu:</b> Nhựa sinh học PLA/PETG cao cấp, an toàn và thân thiện môi trường.</li>
  <li>📐 <b>Không gian:</b> Kích thước hoàn hảo để trang trí bàn làm việc, kệ sách, phòng khách...</li>
  <li>✨ <b>Đặc điểm:</b> Thiết kế 3D độc bản, hoàn thiện bề mặt tỉ mỉ, mang lại điểm nhấn nghệ thuật.</li>
  <li>🛡️ <b>Bảo hành:</b> Đóng gói hộp cát-tông chống sốc an toàn, hỗ trợ đổi trả nếu lỗi do vận chuyển.</li>
</ul>"""
        self.desc_input.setPlainText(default_desc)

    def delete_product(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        prod_id = int(self.table.item(row, 0).text())

        reply = QMessageBox.question(self, 'Xác nhận', f'Xóa sản phẩm ID {prod_id}?', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = [p for p in data if p["id"] != prod_id]
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # Delete images folder if exists
            img_dir = os.path.join(IMAGES_DIR, f"sp_{prod_id}")
            if os.path.exists(img_dir):
                shutil.rmtree(img_dir)

            self.load_data_to_table()
            self.clear_form()

    def push_to_github(self):
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update Tiem Decor 3D via PyQt Manager"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main", "-f"], check=True)
            QMessageBox.information(self, "Thành công", "Đã đẩy dữ liệu lên web thành công!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def pull_from_github(self):
        try:
            subprocess.run(["git", "pull", "origin", "main"], check=True)
            self.load_data_to_table()
            QMessageBox.information(self, "Thành công", "Đã lấy dữ liệu mới nhất từ web về máy!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ProductManagerApp()
    window.show()
    sys.exit(app.exec_())