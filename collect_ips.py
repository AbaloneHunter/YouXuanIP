import requests
from bs4 import BeautifulSoup
import re
import os

# 目标URL列表
urls = [
    'https://www.wetest.vip/page/cloudflare/address_v4.html', 
    'https://ip.164746.xyz'
]

# 更严格的IP地址正则表达式
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# 验证IP地址是否有效
def is_valid_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

# 检查ip.txt文件是否存在,如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 创建一个文件来存储IP地址
with open('ip.txt', 'w', encoding='utf-8') as file:
    for url in urls:
        try:
            print(f'正在处理: {url}')
            
            # 发送HTTP请求获取网页内容
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # 如果请求不成功会抛出异常
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据网站的不同结构找到包含IP地址的元素
            if 'wetest.vip' in url:
                elements = soup.find_all(['li', 'tr', 'td'])
            elif '164746.xyz' in url:
                elements = soup.find_all('tr')
            else:
                elements = soup.find_all(['li', 'tr', 'td', 'p', 'div'])
            
            ip_count = 0
            # 遍历所有元素,查找IP地址
            for element in elements:
                element_text = element.get_text()
                ip_matches = re.findall(ip_pattern, element_text)
                
                # 如果找到IP地址,则验证并写入文件
                for ip in ip_matches:
                    if is_valid_ip(ip):
                        file.write(ip + '\n')
                        ip_count += 1
            
            print(f'从 {url} 提取了 {ip_count} 个IP地址')
            
        except requests.exceptions.RequestException as e:
            print(f'请求 {url} 时出错: {e}')
        except Exception as e:
            print(f'处理 {url} 时发生错误: {e}')

print('IP地址已保存到ip.txt文件中。')

# 统计提取的IP数量
if os.path.exists('ip.txt'):
    with open('ip.txt', 'r', encoding='utf-8') as file:
        ips = file.readlines()
        print(f'总共提取了 {len(ips)} 个唯一的IP地址')
