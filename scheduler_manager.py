#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化调度系统 - 智能任务调度管理器
支持定时任务、健康监控、故障恢复、智能策略
"""

import schedule
import time
import threading
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import subprocess
import psutil
import sqlite3
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    """任务类型枚举"""
    DAILY_SCAN = "daily_scan"
    MARKET_ANALYSIS = "market_analysis"
    NOTIFICATION = "notification"
    DATA_BACKUP = "data_backup"
    SYSTEM_HEALTH = "system_health"
    CUSTOM = "custom"

@dataclass
class TaskConfig:
    """任务配置类"""
    id: str
    name: str
    task_type: TaskType
    command: str
    schedule_time: str
    enabled: bool = True
    retry_count: int = 3
    timeout: int = 300  # 5分钟超时
    notify_on_fail: bool = True
    notify_on_success: bool = False
    dependencies: List[str] = None
    max_runtime: int = 1800  # 30分钟最大运行时间
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    exit_code: Optional[int] = None
    output: str = ""
    error: str = ""
    retry_count: int = 0
    duration: float = 0.0

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "scheduler.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建任务执行历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL,
                exit_code INTEGER,
                output TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                duration REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建系统监控表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                network_sent INTEGER,
                network_recv INTEGER,
                active_tasks INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_task_result(self, result: TaskResult):
        """保存任务执行结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO task_history (
                    task_id, start_time, end_time, status, exit_code, 
                    output, error, retry_count, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.task_id,
                result.start_time.isoformat(),
                result.end_time.isoformat() if result.end_time else None,
                result.status.value,
                result.exit_code,
                result.output,
                result.error,
                result.retry_count,
                result.duration
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存任务结果失败: {e}")
    
    def save_system_metrics(self, metrics: Dict[str, Any]):
        """保存系统监控指标"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics (
                    timestamp, cpu_percent, memory_percent, disk_percent,
                    network_sent, network_recv, active_tasks
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                metrics.get('cpu_percent', 0),
                metrics.get('memory_percent', 0),
                metrics.get('disk_percent', 0),
                metrics.get('network_sent', 0),
                metrics.get('network_recv', 0),
                metrics.get('active_tasks', 0)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存系统指标失败: {e}")
    
    def get_task_history(self, task_id: str = None, limit: int = 100) -> List[Dict]:
        """获取任务执行历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if task_id:
                cursor.execute('''
                    SELECT * FROM task_history 
                    WHERE task_id = ?
                    ORDER BY start_time DESC 
                    LIMIT ?
                ''', (task_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM task_history 
                    ORDER BY start_time DESC 
                    LIMIT ?
                ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"获取任务历史失败: {e}")
            return []

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 60):
        """启动系统监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止系统监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("系统监控已停止")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self.collect_metrics()
                self.db_manager.save_system_metrics(metrics)
                
                # 检查系统健康状态
                self.check_system_health(metrics)
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"系统监控错误: {e}")
                time.sleep(interval)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 网络IO
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent
            network_recv = network.bytes_recv
            
            # 活跃进程数
            active_tasks = len([p for p in psutil.process_iter() if p.is_running()])
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'network_sent': network_sent,
                'network_recv': network_recv,
                'active_tasks': active_tasks
            }
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return {}
    
    def check_system_health(self, metrics: Dict[str, Any]):
        """检查系统健康状态"""
        warnings = []
        
        # CPU检查
        if metrics.get('cpu_percent', 0) > 80:
            warnings.append(f"CPU使用率过高: {metrics['cpu_percent']:.1f}%")
        
        # 内存检查
        if metrics.get('memory_percent', 0) > 85:
            warnings.append(f"内存使用率过高: {metrics['memory_percent']:.1f}%")
        
        # 磁盘检查
        if metrics.get('disk_percent', 0) > 90:
            warnings.append(f"磁盘使用率过高: {metrics['disk_percent']:.1f}%")
        
        if warnings:
            logger.warning("系统健康警告: " + "; ".join(warnings))

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.running_tasks = {}
        self.task_locks = {}
    
    def execute_task(self, task_config: TaskConfig) -> TaskResult:
        """执行单个任务"""
        result = TaskResult(
            task_id=task_config.id,
            start_time=datetime.now(),
            status=TaskStatus.RUNNING
        )
        
        # 检查任务是否已在运行
        if task_config.id in self.running_tasks:
            logger.warning(f"任务 {task_config.id} 已在运行中，跳过")
            result.status = TaskStatus.CANCELLED
            result.error = "任务已在运行中"
            result.end_time = datetime.now()
            return result
        
        self.running_tasks[task_config.id] = result
        
        try:
            logger.info(f"开始执行任务: {task_config.name}")
            
            # 检查依赖任务
            if not self._check_dependencies(task_config.dependencies):
                raise Exception("依赖任务未完成")
            
            # 执行命令
            process = subprocess.Popen(
                task_config.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            # 等待完成或超时
            try:
                stdout, stderr = process.communicate(timeout=task_config.timeout)
                exit_code = process.returncode
                
                result.output = stdout
                result.error = stderr
                result.exit_code = exit_code
                result.status = TaskStatus.SUCCESS if exit_code == 0 else TaskStatus.FAILED
                
            except subprocess.TimeoutExpired:
                process.kill()
                result.error = f"任务超时 ({task_config.timeout}秒)"
                result.status = TaskStatus.FAILED
                result.exit_code = -1
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            result.error = str(e)
            result.status = TaskStatus.FAILED
            result.exit_code = -1
        
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            # 移除运行标记
            if task_config.id in self.running_tasks:
                del self.running_tasks[task_config.id]
            
            # 保存结果
            self.db_manager.save_task_result(result)
            
            logger.info(f"任务完成: {task_config.name} - {result.status.value}")
        
        return result
    
    def execute_with_retry(self, task_config: TaskConfig) -> TaskResult:
        """带重试的任务执行"""
        last_result = None
        
        for attempt in range(task_config.retry_count + 1):
            result = self.execute_task(task_config)
            result.retry_count = attempt
            
            if result.status == TaskStatus.SUCCESS:
                return result
            
            last_result = result
            
            if attempt < task_config.retry_count:
                wait_time = 2 ** attempt  # 指数退避
                logger.info(f"任务失败，{wait_time}秒后重试 (第{attempt + 1}次)")
                time.sleep(wait_time)
        
        return last_result
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖任务是否完成"""
        if not dependencies:
            return True
        
        for dep_task_id in dependencies:
            # 检查最近的执行记录
            history = self.db_manager.get_task_history(dep_task_id, 1)
            if not history or history[0]['status'] != TaskStatus.SUCCESS.value:
                logger.warning(f"依赖任务 {dep_task_id} 未成功完成")
                return False
        
        return True

class SchedulerManager:
    """调度管理器主类"""
    
    def __init__(self, config_file: str = "scheduler_config.json"):
        self.config_file = config_file
        self.db_manager = DatabaseManager()
        self.system_monitor = SystemMonitor(self.db_manager)
        self.task_executor = TaskExecutor(self.db_manager)
        self.tasks = {}
        self.running = False
        self.scheduler_thread = None
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        self.load_config()
    
    def load_config(self):
        """加载调度配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.tasks = {}
                for task_data in data.get('tasks', []):
                    task = TaskConfig(**task_data)
                    self.tasks[task.id] = task
                
                logger.info(f"加载了 {len(self.tasks)} 个任务配置")
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def save_config(self):
        """保存调度配置"""
        try:
            data = {
                'tasks': [asdict(task) for task in self.tasks.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def _create_default_config(self):
        """创建默认配置"""
        default_tasks = [
            TaskConfig(
                id="morning_scan",
                name="早盘选股扫描",
                task_type=TaskType.DAILY_SCAN,
                command="python full_market_scanner.py",
                schedule_time="09:15",
                retry_count=2,
                notify_on_success=True
            ),
            TaskConfig(
                id="afternoon_analysis",
                name="午后市场分析",
                task_type=TaskType.MARKET_ANALYSIS,
                command="python market_analyzer.py",
                schedule_time="13:30",
                retry_count=1
            ),
            TaskConfig(
                id="evening_report",
                name="收盘选股报告",
                task_type=TaskType.NOTIFICATION,
                command="python -c \"from notification_manager import NotificationManager; nm = NotificationManager(); nm.send_daily_report([])\"",
                schedule_time="15:30",
                dependencies=["morning_scan", "afternoon_analysis"],
                notify_on_success=True
            ),
            TaskConfig(
                id="daily_backup",
                name="每日数据备份",
                task_type=TaskType.DATA_BACKUP,
                command="python -c \"import shutil; import datetime; shutil.make_archive(f'backup_{datetime.date.today()}', 'zip', 'results')\"",
                schedule_time="20:00",
                retry_count=3
            ),
            TaskConfig(
                id="system_health_check",
                name="系统健康检查",
                task_type=TaskType.SYSTEM_HEALTH,
                command="python -c \"print('系统健康检查完成')\"",
                schedule_time="every_hour",
                timeout=60
            )
        ]
        
        for task in default_tasks:
            self.tasks[task.id] = task
        
        self.save_config()
        logger.info("创建了默认任务配置")
    
    def add_task(self, task_config: TaskConfig):
        """添加任务"""
        self.tasks[task_config.id] = task_config
        self.save_config()
        
        # 如果调度器正在运行，重新注册任务
        if self.running:
            self._register_task(task_config)
        
        logger.info(f"添加任务: {task_config.name}")
    
    def remove_task(self, task_id: str):
        """删除任务"""
        if task_id in self.tasks:
            task_name = self.tasks[task_id].name
            del self.tasks[task_id]
            self.save_config()
            
            # 从调度器中移除
            schedule.clear(task_id)
            
            logger.info(f"删除任务: {task_name}")
        else:
            logger.warning(f"任务不存在: {task_id}")
    
    def enable_task(self, task_id: str, enabled: bool = True):
        """启用/禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = enabled
            self.save_config()
            
            if self.running:
                if enabled:
                    self._register_task(self.tasks[task_id])
                else:
                    schedule.clear(task_id)
            
            status = "启用" if enabled else "禁用"
            logger.info(f"{status}任务: {self.tasks[task_id].name}")
    
    def _register_task(self, task_config: TaskConfig):
        """注册单个任务到调度器"""
        if not task_config.enabled:
            return
        
        def job_wrapper():
            try:
                result = self.task_executor.execute_with_retry(task_config)
                
                # 发送通知
                if ((result.status == TaskStatus.SUCCESS and task_config.notify_on_success) or
                    (result.status == TaskStatus.FAILED and task_config.notify_on_fail)):
                    self._send_task_notification(task_config, result)
                
            except Exception as e:
                logger.error(f"任务包装器错误: {e}")
        
        # 根据时间类型注册任务
        time_str = task_config.schedule_time.lower()
        
        if time_str == "every_hour":
            schedule.every().hour.do(job_wrapper).tag(task_config.id)
        elif time_str == "every_30min":
            schedule.every(30).minutes.do(job_wrapper).tag(task_config.id)
        elif time_str.startswith("every_"):
            # 解析every_X_minutes格式
            parts = time_str.split('_')
            if len(parts) >= 3 and parts[2] in ['minutes', 'min']:
                interval = int(parts[1])
                schedule.every(interval).minutes.do(job_wrapper).tag(task_config.id)
        else:
            # 按时间点执行
            try:
                schedule.every().day.at(time_str).do(job_wrapper).tag(task_config.id)
            except Exception as e:
                logger.error(f"无效的时间格式 {time_str}: {e}")
    
    def _send_task_notification(self, task_config: TaskConfig, result: TaskResult):
        """发送任务通知"""
        try:
            from notification_manager import NotificationManager
            
            nm = NotificationManager()
            
            if result.status == TaskStatus.SUCCESS:
                title = f"✅ 任务成功: {task_config.name}"
                content = f"任务执行成功\n耗时: {result.duration:.1f}秒\n输出: {result.output[:200]}"
            else:
                title = f"❌ 任务失败: {task_config.name}"
                content = f"任务执行失败\n错误: {result.error[:200]}\n重试次数: {result.retry_count}"
            
            nm.send_all(title, content)
            
        except Exception as e:
            logger.error(f"发送任务通知失败: {e}")
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行中")
            return
        
        # 注册所有任务
        for task in self.tasks.values():
            self._register_task(task)
        
        # 启动系统监控
        self.system_monitor.start_monitoring()
        
        # 启动调度循环
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"调度器已启动，管理 {len(self.tasks)} 个任务")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        self.system_monitor.stop_monitoring()
        
        if self.scheduler_thread:
            self.scheduler_thread.join()
        
        schedule.clear()
        logger.info("调度器已停止")
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"调度循环错误: {e}")
                time.sleep(5)
    
    def run_task_now(self, task_id: str) -> TaskResult:
        """立即执行指定任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task_config = self.tasks[task_id]
        return self.task_executor.execute_with_retry(task_config)
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态概览"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for task in self.tasks.values() if task.enabled)
        running_tasks = len(self.task_executor.running_tasks)
        
        # 获取最近24小时的执行统计
        recent_history = self.db_manager.get_task_history(limit=1000)
        recent_24h = [
            h for h in recent_history 
            if datetime.fromisoformat(h['start_time']) > datetime.now() - timedelta(hours=24)
        ]
        
        success_count = sum(1 for h in recent_24h if h['status'] == TaskStatus.SUCCESS.value)
        failed_count = sum(1 for h in recent_24h if h['status'] == TaskStatus.FAILED.value)
        
        return {
            'scheduler_running': self.running,
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'running_tasks': running_tasks,
            'last_24h_executions': len(recent_24h),
            'last_24h_success': success_count,
            'last_24h_failed': failed_count,
            'success_rate': (success_count / len(recent_24h) * 100) if recent_24h else 0,
            'next_jobs': [
                {
                    'job': str(job),
                    'next_run': job.next_run.isoformat() if job.next_run else None
                }
                for job in schedule.jobs[:5]  # 显示前5个即将执行的任务
            ]
        }
    
    def generate_status_report(self) -> str:
        """生成状态报告"""
        status = self.get_task_status()
        
        report = f"""
🤖 智能调度系统状态报告
{'='*50}
📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 基本状态:
   • 调度器状态: {'🟢 运行中' if status['scheduler_running'] else '🔴 已停止'}
   • 总任务数: {status['total_tasks']}
   • 启用任务: {status['enabled_tasks']}
   • 运行中任务: {status['running_tasks']}

📈 执行统计 (最近24小时):
   • 总执行次数: {status['last_24h_executions']}
   • 成功次数: {status['last_24h_success']}
   • 失败次数: {status['last_24h_failed']}
   • 成功率: {status['success_rate']:.1f}%

⏰ 即将执行的任务:
"""
        
        for i, job_info in enumerate(status['next_jobs'], 1):
            next_run = job_info['next_run']
            if next_run:
                next_time = datetime.fromisoformat(next_run).strftime('%H:%M:%S')
                report += f"   {i}. {next_time} - {job_info['job']}\n"
        
        if not status['next_jobs']:
            report += "   暂无计划任务\n"
        
        report += f"\n⚠️ 系统监控: {'🟢 正常' if self.system_monitor.monitoring else '🔴 未启用'}"
        
        return report

def main():
    """主程序 - 调度器控制台"""
    print("🤖 智能调度系统控制台")
    print("="*50)
    
    manager = SchedulerManager()
    
    while True:
        print("\n请选择操作:")
        print("1. 🚀 启动调度器")
        print("2. ⏹️  停止调度器") 
        print("3. 📋 查看任务状态")
        print("4. ▶️  立即执行任务")
        print("5. ➕ 添加新任务")
        print("6. ❌ 删除任务")
        print("7. 🔄 启用/禁用任务")
        print("8. 📊 生成状态报告")
        print("9. 📜 查看任务历史")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-9): ").strip()
        
        if choice == "1":
            try:
                manager.start()
                print("✅ 调度器启动成功!")
            except Exception as e:
                print(f"❌ 启动失败: {e}")
        
        elif choice == "2":
            manager.stop()
            print("✅ 调度器已停止")
        
        elif choice == "3":
            status = manager.get_task_status()
            print(f"\n📊 任务状态概览:")
            print(f"   调度器: {'运行中' if status['scheduler_running'] else '已停止'}")
            print(f"   总任务: {status['total_tasks']} | 启用: {status['enabled_tasks']} | 运行中: {status['running_tasks']}")
            print(f"   24小时统计: {status['last_24h_success']}/{status['last_24h_executions']} 成功 ({status['success_rate']:.1f}%)")
        
        elif choice == "4":
            print("\n可执行的任务:")
            for i, (task_id, task) in enumerate(manager.tasks.items(), 1):
                print(f"   {i}. {task.name} ({task_id})")
            
            try:
                task_num = int(input("请输入任务编号: ")) - 1
                task_ids = list(manager.tasks.keys())
                if 0 <= task_num < len(task_ids):
                    task_id = task_ids[task_num]
                    print(f"正在执行任务: {manager.tasks[task_id].name}")
                    result = manager.run_task_now(task_id)
                    print(f"✅ 任务完成: {result.status.value} (耗时: {result.duration:.1f}秒)")
                    if result.error:
                        print(f"错误信息: {result.error}")
                else:
                    print("❌ 无效的任务编号")
            except (ValueError, IndexError):
                print("❌ 请输入有效的数字")
            except Exception as e:
                print(f"❌ 执行失败: {e}")
        
        elif choice == "8":
            print(manager.generate_status_report())
        
        elif choice == "0":
            if manager.running:
                manager.stop()
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 