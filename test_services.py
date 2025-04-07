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
        
        # 测试帖子服务健康检查
        self.log("测试帖子服务健康检查...")
        try:
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
        
        # 创建纯文本帖子 - 使用新的 /text 端点
        self.log("创建纯文本帖子...")
        post_content = f"这是一条测试纯文本帖子 - {int(time.time())}"
        try:
            # 使用表单数据发送到新的文本帖子端点
            form_data = {
                "content": post_content,
                "visibility": "PUBLIC",
                "tag_names": "test,automation"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/posts/text",
                headers=headers,
                data=form_data
            )
            success = self.assert_test(response.status_code == 200, "创建纯文本帖子成功")
            if not success:
                self.log(f"错误: {response.text}", "ERROR")
                return False
            
            data = response.json()
            self.post_id = data["id"]
            self.log(f"帖子ID: {self.post_id}")
            
            if self.verbose:
                self.log(f"响应内容: {data}")
        except Exception as e:
            self.assert_test(False, f"创建纯文本帖子失败: {str(e)}")
            return False
            
        # 测试媒体帖子创建 - 使用 /media 端点
        self.log("测试创建媒体帖子...")
        try:
            # 创建一个测试图片文件
            import io
            from PIL import Image
            
            # 创建一个简单的测试图片
            img = Image.new('RGB', (100, 100), color = (73, 109, 137))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            
            # 准备上传表单数据
            files = {
                'files': ('test_image.jpg', img_byte_arr, 'image/jpeg')
            }
            
            form_data = {
                'visibility': 'PUBLIC',
                'tag_names': 'test,media,image'
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/api/v1/posts/media",
                headers=headers,
                data=form_data,
                files=files
            )
            
            # 如果PIL库不可用，则改用简单的测试
            if response.status_code != 200:
                self.log("PIL库可能不可用，使用模拟图片测试...", "INFO")
                # 创建模拟图片数据
                mock_image_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0C\x14\r\x0C\x0B\x0B\x0C\x19\x12\x13\x0F\x14\x1D\x1A\x1F\x1E\x1D\x1A\x1C\x1C $.\' ",#\x1C\x1C(7),01444\x1F\'9=82<.342'
                files = {
                    'files': ('test_image.jpg', mock_image_data, 'image/jpeg')
                }
                response = requests.post(
                    f"{self.base_url}/api/v1/posts/media",
                    headers=headers,
                    data=form_data,
                    files=files
                )
            
            # 检查结果
            if response.status_code == 200:
                media_post_id = response.json()["id"]
                self.assert_test(True, "创建媒体帖子成功")
                self.log(f"媒体帖子ID: {media_post_id}")
                
                # 获取媒体帖子详情，并检查媒体类型
                details_response = requests.get(
                    f"{self.base_url}/api/v1/posts/{media_post_id}",
                    headers=headers
                )
                if details_response.status_code == 200:
                    media_type = details_response.json().get("media_type")
                    self.assert_test(media_type == "IMAGE", f"媒体类型检查: {media_type}")
                    
                    if self.verbose:
                        self.log(f"媒体帖子详情: {details_response.json()}")
            else:
                self.log(f"媒体上传可能存在问题: {response.text}", "WARNING")
                self.assert_test(False, "创建媒体帖子")
                
        except ImportError:
            self.log("PIL库不可用，跳过媒体帖子测试", "WARNING")
        except Exception as e:
            self.log(f"创建媒体帖子异常: {str(e)}", "ERROR")
            self.assert_test(False, "创建媒体帖子出错")
        
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
                
                if success:
                    # 验证帖子内容是否匹配
                    data = response.json()
                    content_match = data.get("content") == post_content
                    self.assert_test(content_match, "帖子内容匹配")
                    
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
        
        # 测试对帖子的反应功能
        if self.post_id:
            self.log("测试对帖子添加反应...")
            reaction_data = {
                "type": "like",
                "post_id": self.post_id
            }
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/reactions/",
                    headers=headers,
                    json=reaction_data
                )
                success = self.assert_test(response.status_code == 200, "添加反应成功")
                if not success:
                    self.log(f"错误: {response.text}", "ERROR")
                    
                if self.verbose and success:
                    self.log(f"响应内容: {response.json()}")
            except Exception as e:
                self.assert_test(False, f"添加反应失败: {str(e)}")
            
            # 获取帖子反应摘要
            self.log("获取帖子反应摘要...")
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/reactions/post/{self.post_id}/summary",
                    headers=headers
                )
                success = self.assert_test(response.status_code == 200, "获取反应摘要成功")
                if not success:
                    self.log(f"错误: {response.text}", "ERROR")
                else:
                    reaction_total = response.json()["total"]
                    self.log(f"反应数量: {reaction_total}")
                    
                if self.verbose and success:
                    self.log(f"响应内容: {response.json()}")
            except Exception as e:
                self.assert_test(False, f"获取反应摘要失败: {str(e)}")
        
        # 测试搜索功能
        self.log("测试搜索功能...")
        try:
            # 尝试不同的搜索端点
            search_endpoints = [
                f"{self.base_url}/api/v1/search/?query=test",
                f"{self.base_url}/api/v1/search?query=test",  # 移除尾部斜杠
                f"{self.base_url}/api/v1/posts/search/?query=test",  # 可能的替代路径
                f"{self.base_url}/api/v1/posts/search?query=test"  # 可能的替代路径
            ]
            
            search_success = False
            for endpoint in search_endpoints:
                self.log(f"尝试搜索端点: {endpoint}", "INFO")
                response = requests.get(endpoint, headers=headers)
                print(response)
                if response.status_code == 200:
                    search_success = True
                    search_count = response.json()["total"]
                    self.log(f"搜索结果数: {search_count}")
                    
                    if self.verbose:
                        self.log(f"响应内容摘要: {json.dumps(response.json())[:200]}...")
                    break
            
            if not search_success:
                self.log("所有搜索端点都失败，尝试使用POST请求高级搜索", "INFO")
                # 尝试使用POST请求的高级搜索API
                search_data = {
                    "query": "test",
                    "tags": ["test"]
                }
                response = requests.post(
                    f"{self.base_url}/api/v1/search/",
                    headers=headers,
                    json=search_data
                )
                
                success = self.assert_test(response.status_code == 200, "使用高级搜索API成功")
                if success:
                    search_count = response.json()["total"]
                    self.log(f"高级搜索结果数: {search_count}")
                else:
                    self.log(f"高级搜索也失败: {response.text}", "ERROR")
                    self.log("搜索功能可能尚未实现或路径不正确，请检查API文档。", "WARNING")
            else:
                self.assert_test(True, "搜索帖子成功")
                
        except Exception as e:
            self.assert_test(False, f"搜索帖子失败: {str(e)}")
        
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
    
    def test_follow_unfollow(self):
        """测试关注和取关功能"""
        self.log("\n===== 测试关注与取关 =====")

        # 注册另一个用户作为被关注者
        self.log("注册另一个测试用户以进行关注测试...")
        another_user = self.generate_random_user()
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=another_user
            )
            self.assert_test(response.status_code == 200, "另一个用户注册成功")
            another_user_id = response.json()["id"]
        except Exception as e:
            self.assert_test(False, f"另一个用户注册失败: {str(e)}")
            return

        # 当前用户关注另一个用户
        self.log("执行关注操作...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/users/{another_user_id}/follow",
                headers=headers
            )
            self.assert_test(response.status_code == 201, "关注用户成功")
        except Exception as e:
            self.assert_test(False, f"关注用户失败: {str(e)}")
            return

        # 获取关注列表
        self.log("验证关注列表...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/v1/users/{self.user_id}/following",
                headers=headers
            )
            success = self.assert_test(response.status_code == 200, "获取关注列表成功")
            if success:
                ids = response.json().get("following", [])
                self.assert_test(another_user_id in ids, "已关注目标用户")
        except Exception as e:
            self.assert_test(False, f"获取关注列表失败: {str(e)}")

        # 取消关注
        self.log("执行取消关注操作...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(
                f"{self.base_url}/api/v1/users/{another_user_id}/unfollow",
                headers=headers
            )
            self.assert_test(response.status_code == 200, "取消关注成功")
        except Exception as e:
            self.assert_test(False, f"取消关注失败: {str(e)}")

    
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

            self.test_follow_unfollow()
        
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