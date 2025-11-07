import requests
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# 目标URL列表
urls = [
    'https://ip.164746.xyz', 
    'https://cf.090227.xyz', 
    'https://stock.hostmonit.com/CloudFlareYes',
    'https://www.wetest.vip/page/cloudflare/address_v4.html'
]

# 匹配IPv4地址的正则表达式
ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

# 删除旧的 ip.txt 文件
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 用集合存储IP地址，自动去重
unique_ips = set()

# 获取IP地址对应的国家
def get_ip_country(ip: str) -> str:
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('country', 'Unknown')
    except:
        pass
    return 'Unknown'

# 获取IP延迟（3次ping，每次间隔1秒，计算平均延迟）
def get_ping_latency(ip: str, num_pings: int = 3, interval: int = 1) -> tuple[str, float]:
    latencies = []
    for _ in range(num_pings):
        try:
            start = time.time()
            # 使用HTTPS并忽略证书验证，增加成功率
            requests.get(f"https://{ip}", timeout=5, verify=False)
            latency = (time.time() - start) * 1000  # 毫秒
            latencies.append(round(latency, 3))
            time.sleep(interval)  # 每次ping之间的间隔时间
        except requests.RequestException:
            latencies.append(float('inf'))  # 请求失败返回无限延迟
    # 计算平均延迟
    avg_latency = sum(latencies) / len(latencies) if latencies else float('inf')
    return ip, avg_latency

# 从URLs抓取IP地址，避免无效请求并提高异常处理
def fetch_ips():
    for url in urls:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                ips = re.findall(ip_pattern, resp.text)
                unique_ips.update(ips)
                print(f"从 {url} 获取到 {len(ips)} 个IP")
        except requests.RequestException as e:
            print(f"警告: 获取IP失败，URL: {url}, 错误: {e}")

# 并发获取延迟和国家信息
def fetch_ip_info() -> dict:
    ip_info = {}
    
    # 首先获取所有IP的延迟
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_ping_latency, ip): ip for ip in unique_ips}
        for future in as_completed(futures):
            ip, latency = future.result()
            ip_info[ip] = {'latency': latency, 'country': 'Unknown'}
    
    # 然后获取国家信息（限制并发数以遵守API限制）
    print("正在获取IP地址的国家信息...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        country_futures = {executor.submit(get_ip_country, ip): ip for ip in ip_info.keys()}
        for future in as_completed(country_futures):
            ip = country_futures[future]
            country = future.result()
            ip_info[ip]['country'] = country
    
    return ip_info

# 主流程
print("开始从源URL获取IP地址...")
fetch_ips()
print(f"总共获取到 {len(unique_ips)} 个唯一IP地址")

print("开始测试IP延迟...")
ip_info = fetch_ip_info()

# 过滤掉延迟为无穷大的IP
valid_ips = {ip: info for ip, info in ip_info.items() if info['latency'] != float('inf')}

# 按延迟排序并选择前60个
if valid_ips:
    sorted_ips = sorted(valid_ips.items(), key=lambda x: x[1]['latency'])[:60]
    
    # 写入文件
    with open('ip.txt', 'w', encoding='utf-8') as f:
        f.write("IP地址\t\t延迟\t\t国家\n")
        f.write("=" * 50 + "\n")
        for ip, info in sorted_ips:
            f.write(f'{ip}\t{info["latency"]:.2f}ms\t\t{info["country"]}\n')
    
    print(f'已保存 {len(sorted_ips)} 个IP到 ip.txt')
    
    # 在控制台也输出结果
    print("\n前60个最低延迟的IP地址:")
    print("IP地址\t\t延迟\t\t国家")
    print("=" * 50)
    for ip, info in sorted_ips[:20]:  # 控制台只显示前20个
        print(f'{ip}\t{info["latency"]:.2f}ms\t\t{info["country"]}')
    if len(sorted_ips) > 20:
        print(f"... 还有 {len(sorted_ips) - 20} 个IP已保存到文件")
else:
    print('未找到有效的IP地址')

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
