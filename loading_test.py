import time
import os
import threading
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import sys
from PyQt6.QtWidgets import QApplication, QPlainTextEdit, QMainWindow
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QEventLoop
from functools import partial

class LoaderSignals(QObject):
    chunk_loaded = pyqtSignal(str)
    loading_finished = pyqtSignal()

class LoadingTest(QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
        self.setup_ui()
        self.loader_signals = LoaderSignals()
        self.loader_signals.chunk_loaded.connect(self.append_text)
        self.loader_signals.loading_finished.connect(self.on_loading_finished)
        self.loading_start_time = 0
        print(f"Testing file: {file_path}")
        print(f"File size: {self.file_size:.2f} MB")

    def setup_ui(self):
        self.text_viewer = QPlainTextEdit(self)
        self.setCentralWidget(self.text_viewer)
        self.resize(800, 600)
        # 设置等宽字体
        font = self.text_viewer.font()
        font.setFamily("Courier New")
        font.setPointSize(12)
        self.text_viewer.setFont(font)

    def append_text(self, text):
        self.text_viewer.appendPlainText(text.rstrip('\n'))

    def on_loading_finished(self):
        end_time = time.time()
        total_time = end_time - self.loading_start_time
        print(f"Total time (including rendering): {total_time:.2f} seconds")
        print("Loading and rendering finished")

    def test_traditional_load(self):
        """测试传统的一次性加载方式"""
        self.text_viewer.clear()
        self.loading_start_time = time.time()

        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.text_viewer.setPlainText(content)
            # 强制处理所有待处理的事件，确保文本完全渲染
            QApplication.processEvents()

        end_time = time.time()
        total_time = end_time - self.loading_start_time
        print(f"Total time (including rendering): {total_time:.2f} seconds")
        return {
            'time': total_time,
            'content_size': len(content)
        }

    def test_chunk_load(self, chunk_size_mb=8):
        """测试单线程分块加载"""
        self.text_viewer.clear()
        chunk_size = chunk_size_mb * 1024 * 1024  # 转换为字节
        self.loading_start_time = time.time()

        content_size = 0
        with open(self.file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                content_size += len(chunk)
                self.loader_signals.chunk_loaded.emit(chunk)
                QApplication.processEvents()  # 让UI有机会更新

        end_time = time.time()
        total_time = end_time - self.loading_start_time
        print(f"Total time (including rendering): {total_time:.2f} seconds")
        self.loader_signals.loading_finished.emit()
        return {
            'time': total_time,
            'content_size': content_size
        }
        
    async def async_load_chunk(self, chunk_size_mb=8):
        """异步分块加载"""
        chunk_size = chunk_size_mb * 1024 * 1024
        content_size = 0
        
        async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                content_size += len(chunk)
                # 在主线程中更新UI
                self.loader_signals.chunk_loaded.emit(chunk)
                await asyncio.sleep(0)  # 让出控制权给事件循环
                
        return content_size
        
    def test_async_load(self, chunk_size_mb=8):
        """测试异步加载"""
        self.text_viewer.clear()
        self.loading_start_time = time.time()
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_async():
            try:
                content_size = await self.async_load_chunk(chunk_size_mb)
                return content_size
            except Exception as e:
                print(f"Error in async load: {e}")
                return 0
            
        # 运行异步任务
        content_size = loop.run_until_complete(run_async())
        loop.close()
        
        end_time = time.time()
        total_time = end_time - self.loading_start_time
        print(f"Total time (including rendering): {total_time:.2f} seconds")
        self.loader_signals.loading_finished.emit()
        return {
            'time': total_time,
            'content_size': content_size
        }

    def test_multi_thread_load(self, chunk_size_mb=1, num_threads=4):
        """测试多线程分块加载"""
        self.text_viewer.clear()
        chunk_size = chunk_size_mb * 1024 * 1024
        self.loading_start_time = time.time()

        def load_chunk(start_pos):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(start_pos)
                chunk = f.read(chunk_size)
                self.loader_signals.chunk_loaded.emit(chunk)
                return len(chunk)

        # 计算需要的块数
        file_size = os.path.getsize(self.file_path)
        num_chunks = (file_size + chunk_size - 1) // chunk_size
        content_size = 0

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_chunks):
                start_pos = i * chunk_size
                futures.append(executor.submit(load_chunk, start_pos))

            for future in futures:
                content_size += future.result()
                QApplication.processEvents()  # 让UI有机会更新

        end_time = time.time()
        total_time = end_time - self.loading_start_time
        print(f"Total time (including rendering): {total_time:.2f} seconds")
        self.loader_signals.loading_finished.emit()
        return {
            'time': total_time,
            'content_size': content_size
        }

def run_tests(file_path):
    """运行所有测试"""
    app = QApplication(sys.argv)
    test = LoadingTest(file_path)
    test.show()
    
    # 使用QTimer延迟开始测试，确保窗口已经显示
    def start_tests():
        # 测试传统加载
        print("\nTesting traditional loading...")
        traditional_result = test.test_traditional_load()
        content_mb = traditional_result['content_size'] / (1024*1024)
        speed = content_mb / traditional_result['time']
        print(f"Traditional loading:")
        print(f"  Time: {traditional_result['time']:.2f} seconds")
        print(f"  Content size: {content_mb:.2f} MB")
        print(f"  Speed: {speed:.2f} MB/s")

        # 等待一会儿再进行下一个测试
        QTimer.singleShot(1000, lambda: run_chunk_tests(test))

    def run_chunk_tests(test):
        # 测试不同块大小的分块加载
        print("\nTesting chunk loading with different chunk sizes...")
        chunk_sizes = [1, 4, 8, 16]  # MB
        def run_chunk_test(index):
            if index >= len(chunk_sizes):
                QTimer.singleShot(1000, lambda: run_async_tests(test))
                return
            chunk_size = chunk_sizes[index]
            chunk_result = test.test_chunk_load(chunk_size_mb=chunk_size)
            content_mb = chunk_result['content_size'] / (1024*1024)
            speed = content_mb / chunk_result['time']
            print(f"Chunk loading ({chunk_size}MB chunks):")
            print(f"  Time: {chunk_result['time']:.2f} seconds")
            print(f"  Content size: {content_mb:.2f} MB")
            print(f"  Speed: {speed:.2f} MB/s")
            QTimer.singleShot(1000, lambda: run_chunk_test(index + 1))
        run_chunk_test(0)

    def run_async_tests(test):
        # 测试不同块大小的异步加载
        print("\nTesting async loading with different chunk sizes...")
        chunk_sizes = [1, 4, 8, 16]  # MB
        def run_async_test(index):
            if index >= len(chunk_sizes):
                QTimer.singleShot(1000, lambda: run_mt_tests(test))
                return
            chunk_size = chunk_sizes[index]
            async_result = test.test_async_load(chunk_size_mb=chunk_size)
            content_mb = async_result['content_size'] / (1024*1024)
            speed = content_mb / async_result['time']
            print(f"Async loading ({chunk_size}MB chunks):")
            print(f"  Time: {async_result['time']:.2f} seconds")
            print(f"  Content size: {content_mb:.2f} MB")
            print(f"  Speed: {speed:.2f} MB/s")
            QTimer.singleShot(1000, lambda: run_async_test(index + 1))
        run_async_test(0)

    def run_mt_tests(test):
        # 测试多线程分块加载
        print("\nTesting multi-threaded loading...")
        thread_counts = [2, 4, 8]
        def run_mt_test(index):
            if index >= len(thread_counts):
                app.quit()
                return
            thread_count = thread_counts[index]
            mt_result = test.test_multi_thread_load(chunk_size_mb=8, num_threads=thread_count)
            content_mb = mt_result['content_size'] / (1024*1024)
            speed = content_mb / mt_result['time']
            print(f"Multi-threaded loading ({thread_count} threads, 8MB chunks):")
            print(f"  Time: {mt_result['time']:.2f} seconds")
            print(f"  Content size: {content_mb:.2f} MB")
            print(f"  Speed: {speed:.2f} MB/s")
            QTimer.singleShot(1000, lambda: run_mt_test(index + 1))
        run_mt_test(0)

    QTimer.singleShot(1000, start_tests)
    return app.exec()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a file path to test")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    sys.exit(run_tests(file_path))