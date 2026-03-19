#!/usr/bin/env python3
"""
小红书 lululemon 评价采集 MVP (Headless Mode)
适配服务器运行环境
"""

import json
import csv
import time
import random
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


class XHSCrawler:
    def __init__(self, output_dir="./xhs_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.cookies_file = self.output_dir / "cookies.json"
        self.data = []
        
    def random_delay(self, min_sec=2, max_sec=5):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
        
    def save_cookies(self, context):
        """保存登录状态"""
        cookies = context.cookies()
        with open(self.cookies_file, "w") as f:
            json.dump(cookies, f)
        print(f"✅ 登录状态已保存: {self.cookies_file}")
        
    def load_cookies(self, context):
        """加载登录状态"""
        if self.cookies_file.exists():
            with open(self.cookies_file, "r") as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
            print("✅ 已加载登录状态")
            return True
        return False
        
    def extract_note_data(self, page):
        """提取笔记数据"""
        try:
            # 等待内容加载
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # 使用更通用的选择器
            data = {
                "url": page.url,
                "title": "",
                "content": "",
                "author": "",
                "likes": "0",
                "collected_at": datetime.now().isoformat(),
            }
            
            # 尝试多种选择器提取标题
            try:
                # 笔记标题
                if page.locator('h1[class*="title"]').count() > 0:
                    data["title"] = page.locator('h1[class*="title"]').first.inner_text(timeout=3000)
                elif page.locator('[class*="title"]').count() > 0:
                    data["title"] = page.locator('[class*="title"]').first.inner_text(timeout=3000)
            except:
                pass
                
            # 提取内容
            try:
                if page.locator('div[class*="content"]').count() > 0:
                    data["content"] = page.locator('div[class*="content"]').first.inner_text(timeout=3000)
                elif page.locator('div[class*="desc"]').count() > 0:
                    data["content"] = page.locator('div[class*="desc"]').first.inner_text(timeout=3000)
            except:
                pass
                
            # 提取作者
            try:
                if page.locator('a[class*="author"]').count() > 0:
                    data["author"] = page.locator('a[class*="author"]').first.inner_text(timeout=3000)
            except:
                pass
                
            return data if data["content"] or data["title"] else None
            
        except Exception as e:
            print(f"❌ 提取详情失败: {e}")
            return None
            
    def crawl(self, keyword="lululemon", max_notes=10):
        """主采集流程"""
        
        print(f"🚀 启动小红书采集 - 关键词: {keyword}")
        print(f"📊 计划采集: {max_notes} 条笔记")
        print("-" * 50)
        
        with sync_playwright() as p:
            # 启动浏览器（无头模式）
            browser = p.chromium.launch(
                headless=True,  # 服务器模式
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # 加载登录状态
            has_cookies = self.load_cookies(context)
            
            page = context.new_page()
            
            # 访问小红书
            print("🌐 正在访问小红书...")
            page.goto("https://www.xiaohongshu.com", timeout=60000)
            self.random_delay(3, 5)
            
            # 检查登录状态
            if not has_cookies:
                print("⚠️  未找到登录凭证")
                print("💡 提示：小红书需要登录才能搜索")
                print("📱 请在本地运行此脚本完成首次登录，然后上传 cookies.json")
                browser.close()
                return
            
            # 检查是否登录成功
            if "login" in page.url:
                print("⚠️  登录已过期，需要重新登录")
                browser.close()
                return
                
            print("✅ 登录状态有效")
            
            # 搜索关键词
            print(f"🔍 正在搜索: {keyword}")
            try:
                # 找到搜索框
                search_box = page.locator("input[placeholder*='搜索']").first
                search_box.fill(keyword)
                self.random_delay(1, 2)
                search_box.press("Enter")
                self.random_delay(4, 6)
            except Exception as e:
                print(f"❌ 搜索失败: {e}")
                browser.close()
                return
            
            # 等待笔记列表加载
            print("📜 正在加载笔记列表...")
            try:
                page.wait_for_selector('div[class*="note-item"], a[href*="/explore/"]', timeout=10000)
            except:
                print("⚠️  未找到笔记列表，可能需要更新选择器")
                # 保存页面源码供调试
                html_file = self.output_dir / "debug_page.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(page.content())
                print(f"💾 已保存页面源码: {html_file}")
                browser.close()
                return
            
            # 获取笔记链接
            note_links = []
            link_elements = page.locator('a[href*="/explore/"]').all()
            
            for link in link_elements[:max_notes]:
                href = link.get_attribute("href")
                if href and "/explore/" in href:
                    full_url = f"https://www.xiaohongshu.com{href}" if not href.startswith("http") else href
                    if full_url not in [n["url"] for n in note_links]:
                        note_links.append({"url": full_url, "element": link})
            
            print(f"📌 发现 {len(note_links)} 条笔记")
            
            # 采集详情
            for idx, note_info in enumerate(note_links, 1):
                try:
                    print(f"\n[{idx}/{len(note_links)}] 正在采集: {note_info['url'][:60]}...")
                    
                    # 在新页面打开
                    note_page = context.new_page()
                    note_page.goto(note_info["url"], timeout=30000)
                    self.random_delay(3, 5)
                    
                    # 提取数据
                    detail = self.extract_note_data(note_page)
                    if detail:
                        self.data.append(detail)
                        title = detail.get("title", "无标题")[:40]
                        content = detail.get("content", "")[:60]
                        print(f"✅ 成功: {title}...")
                        print(f"   内容: {content}...")
                    else:
                        print("⚠️  未能提取有效数据")
                    
                    note_page.close()
                    self.random_delay(2, 4)
                    
                except Exception as e:
                    print(f"❌ 采集失败: {e}")
                    continue
                    
            browser.close()
            
        # 保存数据
        self.save_data()
        
    def save_data(self):
        """保存数据"""
        if not self.data:
            print("\n⚠️  没有采集到数据")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存 JSON
        json_file = self.output_dir / f"lululemon_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
        # 保存 CSV
        csv_file = self.output_dir / f"lululemon_{timestamp}.csv"
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.data[0].keys())
            writer.writeheader()
            writer.writerows(self.data)
            
        print(f"\n" + "=" * 50)
        print(f"✅ 数据采集完成!")
        print(f"📁 保存位置: {self.output_dir}")
        print(f"📝 JSON: {json_file.name}")
        print(f"📊 CSV: {csv_file.name}")
        print(f"🔢 总计: {len(self.data)} 条笔记")
        print("=" * 50)


if __name__ == "__main__":
    output_dir = Path.home() / ".openclaw/workspace/xhs_data"
    crawler = XHSCrawler(output_dir=str(output_dir))
    crawler.crawl(keyword="lululemon", max_notes=10)
