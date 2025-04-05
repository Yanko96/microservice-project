#!/usr/bin/env python3
"""
社交平台微服务测试脚本
测试 user-service, post-service 和 notification-service 的基本功能

用法:
    python test_services.py
"""

import requests
import json
import time
import sys
import random
import string
import argparse
from datetime import datetime

class ServiceTester:
    def __init__(self, base_url="http://localhost", verbose=False):
        """初始化测试器"""
        self.base_url = base_url
        self.verbose = verbose
        self.token = None
        self.user_id = None
        self.username = None
        self.email = None
        self.password = None
        self.post_id = None
        self.comment_id = None
        self.notification_id = None
        
        # 测试结果统计
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # 颜色代码
        self.GREEN = '\033[92m'
        self.RED = '\033[91m'
        self.YELLOW = '\033[93m'
        self.RESET = '\033[0m'
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if level == "INFO":
            prefix = f"{timestamp} [INFO] "
        elif level == "SUCCESS":
            prefix = f"{timestamp} [{self.GREEN}SUCCESS{self.RESET}] "
        elif level == "ERROR":
            prefix = f"{timestamp} [{self.RED}ERROR{self.RESET}] "
        elif level == "WARNING":
            prefix = f"{timestamp} [{self.YELLOW}WARNING{self.RESET}] "
        else:
            prefix = f"{timestamp} [{level}] "
        
        print(f"{prefix}{message}")
    
    def assert_test(self, condition, message):
        """测试断言"""
        self.total_tests += 1
        
        if condition:
            self.passed_tests += 1
            self.log(f"✅ {message}", "SUCCESS")
            return True
        else:
            self.failed_tests += 1
            self.log(f"❌ {message}", "ERROR")
            return False

    def generate_random_user(self):
        """生成随机用户数据 - 仅使用字母和数字"""
        # 只使用字母和数字，不使用下划线或其他特殊字符
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.username = f"testuser{random_string}"  # 移除了下划线
        self.email = f"{self.username}@example.com"
        self.password = f"Password123{random_string}"  # 密码也可以包含特殊字符
        
        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "full_name": f"Test User {random_string.upper()}"
        }
    
    def test_user_service(self):
        """测试用户服务"""
        self.log("\n===== 测试用户服务 =====")
        
        # 测试根健康检查
        self.log("测试根健康检查...")
        try:
            response = requests.get(f"{self.base_url}/health")
            self.assert_test(response.status_code == 200, "根健康检查成功")
            if self.verbose:
                self.log(f"响应内容: {response.json()}")
        except Exception as e:
            self.assert_test(False, f"根健康检查失败: {str(e)}")
            self.log("尝试继续其他测试...", "WARNING")
        
        # 注册用户
        self.log("注册新用户...")
        user_data = self.generate_random_user()
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            )
            success = self.assert_test(response.status_code == 200, "用户注册成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
                return False
                
            if self.verbose:
                self.log(f"响应内容: {response.json()}")
            
            self.user_id = response.json()["id"]
            self.log(f"用户ID: {self.user_id}")
        except Exception as e:
            self.assert_test(False, f"用户注册失败: {str(e)}")
            return False
        
        # 用户登录
        self.log("用户登录获取令牌...")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data={
                    "username": self.username,
                    "password": self.password
                }
            )
            success = self.assert_test(response.status_code == 200, "用户登录成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
                return False
                
            data = response.json()
            self.token = data["access_token"]
            self.log(f"获取到令牌: {self.token[:20]}...")
            
            if self.verbose:
                self.log(f"响应内容: {data}")
        except Exception as e:
            self.assert_test(False, f"用户登录失败: {str(e)}")
            return False
        
        # 获取当前用户信息
        self.log("获取当前用户信息...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers
            )
            success = self.assert_test(response.status_code == 200, "获取用户信息成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
                return False
                
            if self.verbose:
                self.log(f"响应内容: {response.json()}")
        except Exception as e:
            self.assert_test(False, f"获取用户信息失败: {str(e)}")
            return False
        
        return True
    
    def test_post_service(self):
        """测试帖子服务"""
        if not self.token:
            self.log("缺少令牌，无法测试帖子服务", "ERROR")
            return False
        
        self.log("\n===== 测试帖子服务 =====")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试帖子服务健康检查 - 正确的健康检查URL
        self.log("测试帖子服务健康检查...")
        try:
            # 正确的健康检查端点：/api/v1/health (不是 /api/v1/posts/health)
            response = requests.get(
                f"{self.base_url}/api/v1/health",
                headers=headers
            )
            self.assert_test(response.status_code == 200, "帖子服务健康检查成功")
            if self.verbose and response.status_code == 200:
                self.log(f"响应内容: {response.json()}")
        except Exception as e:
            self.log(f"帖子服务健康检查失败: {str(e)}", "WARNING")
            self.log("继续其他测试...", "INFO")
        
        # 创建帖子 - 确保包含内容
        self.log("创建新帖子...")
        post_data = {
            "content": f"这是一条测试帖子 - {int(time.time())}",  # 确保提供内容
            "visibility": "public",
            "tag_names": ["test", "automation"]
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/posts/",
                headers=headers,
                json=post_data
            )
            success = self.assert_test(response.status_code == 200, "创建帖子成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
                # 尝试使用表单提交
                if "必须提供内容或媒体文件" in response.text:
                    self.log("尝试使用表单提交...", "INFO")
                    form_data = {
                        "content": f"这是一条测试帖子(表单) - {int(time.time())}",
                        "visibility": "public",
                        "tag_names": "test,automation"
                    }
                    response = requests.post(
                        f"{self.base_url}/api/v1/posts/",
                        headers=headers,
                        data=form_data
                    )
                    success = self.assert_test(response.status_code == 200, "使用表单创建帖子成功")
                    if not success:
                        self.log(f"表单提交也失败: {response.text}", "ERROR")
                        return False
            
            data = response.json()
            self.post_id = data["id"]
            self.log(f"帖子ID: {self.post_id}")
            
            if self.verbose:
                self.log(f"响应内容: {data}")
        except Exception as e:
            self.assert_test(False, f"创建帖子失败: {str(e)}")
            return False
        
        # 获取帖子详情
        if self.post_id:
            self.log("获取帖子详情...")
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/posts/{self.post_id}",
                    headers=headers
                )
                success = self.assert_test(response.status_code == 200, "获取帖子详情成功")
                if not success:
                    self.log(f"错误: {response.text}", "ERROR")
                    
                if self.verbose and success:
                    self.log(f"响应内容: {response.json()}")
            except Exception as e:
                self.assert_test(False, f"获取帖子详情失败: {str(e)}")
        
        # 获取帖子列表
        self.log("获取帖子列表...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/posts/",
                headers=headers
            )
            success = self.assert_test(response.status_code == 200, "获取帖子列表成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
            else:
                post_count = len(response.json()["items"])
                self.log(f"帖子数量: {post_count}")
                
            if self.verbose and success:
                self.log(f"响应内容摘要: {json.dumps(response.json())[:200]}...")
        except Exception as e:
            self.assert_test(False, f"获取帖子列表失败: {str(e)}")
        
        # 发表评论
        if self.post_id:
            self.log("发表评论...")
            comment_data = {
                "content": f"这是一条测试评论 - {int(time.time())}",
                "post_id": self.post_id
            }
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/comments/",
                    headers=headers,
                    json=comment_data
                )
                success = self.assert_test(response.status_code == 200, "发表评论成功")
                if not success:
                    self.log(f"错误: {response.text}", "ERROR")
                else:
                    self.comment_id = response.json()["id"]
                    self.log(f"评论ID: {self.comment_id}")
                    
                if self.verbose and success:
                    self.log(f"响应内容: {response.json()}")
            except Exception as e:
                self.assert_test(False, f"发表评论失败: {str(e)}")
        
        # 获取评论列表
        if self.post_id:
            self.log("获取帖子评论...")
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/comments/post/{self.post_id}",
                    headers=headers
                )
                success = self.assert_test(response.status_code == 200, "获取评论列表成功")
                if not success:
                    self.log(f"错误: {response.text}", "ERROR")
                else:
                    comment_count = len(response.json()["items"])
                    self.log(f"评论数量: {comment_count}")
                    
                if self.verbose and success:
                    self.log(f"响应内容摘要: {json.dumps(response.json())[:200]}...")
            except Exception as e:
                self.assert_test(False, f"获取评论列表失败: {str(e)}")
        
        return True
    
    def test_notification_service(self):
        """测试通知服务"""
        if not self.token:
            self.log("缺少令牌，无法测试通知服务", "ERROR")
            return False
        
        self.log("\n===== 测试通知服务 =====")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 尝试获取通知列表
        self.log("获取通知列表...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/notifications/",
                headers=headers
            )
            success = self.assert_test(response.status_code == 200, "获取通知列表成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
                return False
            else:
                notification_count = len(response.json()["items"])
                unread_count = response.json().get("unread_count", 0)
                self.log(f"通知数量: {notification_count}, 未读: {unread_count}")
                
            if self.verbose:
                self.log(f"响应内容摘要: {json.dumps(response.json())[:200]}...")
        except Exception as e:
            self.assert_test(False, f"获取通知列表失败: {str(e)}")
            return False
        
        # 创建测试通知
        self.log("创建测试通知...")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/notifications/test",
                headers=headers
            )
            success = self.assert_test(response.status_code == 200, "创建测试通知成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
            else:
                self.notification_id = response.json()["id"]
                self.log(f"通知ID: {self.notification_id}")
                
            if self.verbose and success:
                self.log(f"响应内容: {response.json()}")
        except Exception as e:
            self.assert_test(False, f"创建测试通知失败: {str(e)}")
        
        # 获取未读通知数量
        self.log("获取未读通知数量...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/notifications/unread/count",
                headers=headers
            )
            success = self.assert_test(response.status_code == 200, "获取未读通知数量成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
            else:
                unread = response.json()["unread"]
                total = response.json()["total"]
                self.log(f"未读通知: {unread}/{total}")
                
            if self.verbose and success:
                self.log(f"响应内容: {response.json()}")
        except Exception as e:
            self.assert_test(False, f"获取未读通知数量失败: {str(e)}")
        
        # 标记通知为已读
        if self.notification_id:
            self.log("标记通知为已读...")
            try:
                response = requests.put(
                    f"{self.base_url}/api/v1/notifications/{self.notification_id}",
                    headers=headers,
                    json={"is_read": True}
                )
                success = self.assert_test(response.status_code == 200, "标记通知为已读成功")
                if not success:
                    self.log(f"错误: {response.text}", "ERROR")
                    
                if self.verbose and success:
                    self.log(f"响应内容: {response.json()}")
            except Exception as e:
                self.assert_test(False, f"标记通知为已读失败: {str(e)}")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始测试微服务...", "INFO")
        self.log(f"API基础URL: {self.base_url}", "INFO")
        
        # 测试用户服务
        user_test_result = self.test_user_service()
        
        # 只有在用户服务测试通过后才继续其他测试
        if user_test_result:
            # 测试帖子服务
            self.test_post_service()
            
            # 测试通知服务
            self.test_notification_service()
        
        # 显示测试结果摘要
        self.log("\n===== 测试结果摘要 =====")
        self.log(f"总测试数: {self.total_tests}")
        self.log(f"通过: {self.GREEN}{self.passed_tests}{self.RESET}")
        self.log(f"失败: {self.RED}{self.failed_tests}{self.RESET}")
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        self.log(f"成功率: {success_rate:.2f}%")
        
        if self.failed_tests == 0:
            self.log("\n所有测试通过！服务运行正常。", "SUCCESS")
        else:
            self.log("\n有些测试未通过，请检查日志了解详情。", "WARNING")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="社交平台微服务测试脚本")
    parser.add_argument("--url", default="http://localhost", help="API的基础URL")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    tester = ServiceTester(base_url=args.url, verbose=args.verbose)
    tester.run_all_tests()