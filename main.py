import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from db.database import init_database
from db.seed_data import seed_test_data

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    init_database()
    seed_test_data()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
