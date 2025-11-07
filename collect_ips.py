import requests
from bs4 import BeautifulSoup
import re
import os
import json

# 目标URL列表
urls = [
    'https://www.wetest.vip/page/cloudflare/address_v4.html', 
    'https://ip.164746.xyz'
]

# 更严格的IP地址正则表达式
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# IP地址查询API（使用免费的ipapi.co）
def get_ip_country(ip):
    """获取IP地址所属国家"""
    try:
        response = requests.get(f'http://ipapi.co/{ip}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('country_name', 'Unknown')
    except:
        pass
    return 'Unknown'

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

print('开始提取IP地址...')

# 创建一个文件来存储IP地址
with open('ip.txt', 'w', encoding='utf-8') as file:
    all_ips = set()  # 使用集合来去重
    
    for url in urls:
        try:
            print(f'正在处理: {url}')
            
            # 发送HTTP请求获取网页内容
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
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
                
                # 如果找到IP地址,则验证并添加到集合
                for ip in ip_matches:
                    if is_valid_ip(ip):
                        all_ips.add(ip)
                        ip_count += 1
            
            print(f'从 {url} 提取了 {ip_count} 个IP地址')
            
        except requests.exceptions.RequestException as e:
            print(f'请求 {url} 时出错: {e}')
        except Exception as e:
            print(f'处理 {url} 时发生错误: {e}')

    print(f'\n开始查询IP地址的国家信息...')
    print(f'总共需要查询 {len(all_ips)} 个唯一的IP地址')
    
    # 查询每个IP的国家信息并写入文件
    processed = 0
    for ip in all_ips:
        try:
            country = get_ip_country(ip)
            file.write(f'{ip}#{country}\n')
            processed += 1
            print(f'进度: {processed}/{len(all_ips)} - {ip}#{country}')
        except Exception as e:
            print(f'查询 {ip} 的国家信息时出错: {e}')
            file.write(f'{ip}#Unknown\n')
            processed += 1

print('\nIP地址及国家信息已保存到ip.txt文件中。')

# 显示统计信息
if os.path.exists('ip.txt'):
    with open('ip.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        countries = {}
        for line in lines:
            if '#' in line:
                country = line.split('#')[1].strip()
                countries[country] = countries.get(country, 0) + 1
        
        print(f'\n统计信息:')
        print(f'总IP数量: {len(lines)}')
        print('国家分布:')
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
            print(f'  {country}: {count}个IP')
