"""飞书客户端实现

提供飞书表格API的统一调用接口，包含token缓存、分页获取和批量更新功能。
"""

import math
import time
import requests
from typing import Dict, List, Any, Optional

from .interfaces import FeishuClientInterface


class FeishuClient(FeishuClientInterface):
    """飞书客户端实现
    
    提供飞书表格记录的获取和更新功能，支持：
    - 自动token获取和缓存
    - 分页记录获取
    - 批量记录更新
    - 自动重试机制
    """
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_token: str,
        table_id: str,
        max_retries: int = 3,
        backoff_factor: float = 1.8
    ):
        """初始化飞书客户端
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            app_token: 飞书应用令牌
            table_id: 表格ID
            max_retries: 最大重试次数
            backoff_factor: 退避因子
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Token缓存
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # 记录映射缓存
        self.records_by_url: Dict[str, Dict] = {}  # 按商品链接映射
        self.existing_ids: set = set()  # 已存在的商品ID集合（用于去重保护）

        # API端点
        self.auth_url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        self.records_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records'
        self.batch_update_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update'
        self.batch_create_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create'
    
    def get_records(self) -> Dict[str, Dict]:
        """获取飞书表中的所有记录
        
        Returns:
            Dict[str, Dict]: 记录映射，key为productId，value为包含record_id和fields的字典
        """
        token = self._get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        existing_records = {}
        records_by_url = {}  # 新增：按商品链接映射
        existing_ids = set()  # 新增：已存在的商品ID集合
        page_token = None

        while True:
            params = {
                'page_size': 500,
                'field_names': '["商品ID","品牌名","商品标题","颜色","尺码","价格","衣服分类","性别","商品链接"]'
            }
            if page_token:
                params['page_token'] = page_token

            # 使用重试机制
            for attempt in range(self.max_retries):
                try:
                    resp = requests.get(
                        self.records_url,
                        headers=headers,
                        params=params,
                        timeout=30
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get('code') != 0:
                        print(f"飞书API返回错误: {data}")
                        break

                    # 提取记录信息
                    items = data.get('data', {}).get('items', [])
                    for item in items:
                        fields = item.get('fields', {})
                        record_info = {
                            'record_id': item.get('record_id'),
                            'fields': fields
                        }

                        # 按商品ID映射
                        product_id = fields.get('商品ID', '').strip()
                        if product_id:
                            existing_records[product_id] = record_info
                            existing_ids.add(product_id)  # 添加到ID集合

                        # 按商品链接映射（去掉末尾斜杠）
                        product_url = fields.get('商品链接', '').strip().rstrip('/')
                        if product_url:
                            records_by_url[product_url] = record_info

                    page_token = data.get('data', {}).get('page_token')
                    break

                except Exception as e:
                    print(f"获取飞书记录失败 (尝试{attempt+1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise e
                    time.sleep(2 ** attempt)  # 指数退避

            if not page_token:
                break

            time.sleep(0.2)  # 分页间隔

        # 保存URL映射和ID集合到实例变量
        self.records_by_url = records_by_url
        self.existing_ids = existing_ids

        return existing_records

    def get_existing_ids(self) -> set:
        """获取已存在的商品ID集合

        注意：必须先调用 get_records() 才能使用此方法

        Returns:
            set: 已存在的商品ID集合
        """
        return self.existing_ids

    def get_records_by_url(self) -> Dict[str, Dict]:
        """获取按商品链接映射的记录

        注意：必须先调用 get_records() 才能使用此方法

        Returns:
            Dict[str, Dict]: 记录映射，key为商品链接（去掉末尾斜杠），value为包含record_id和fields的字典
        """
        return self.records_by_url

    def batch_update(self, records: List[Dict], batch_size: int = 30) -> Dict[str, Any]:
        """批量更新记录
        
        Args:
            records: 待更新的记录列表，每个记录包含record_id和fields
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 更新结果统计
        """
        token = self._get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        total_batches = math.ceil(len(records) / batch_size)
        success_count = 0
        failed_batches = []
        
        for i in range(total_batches):
            chunk = records[i * batch_size:(i + 1) * batch_size]
            batch_records = [
                {
                    'record_id': item['record_id'],
                    'fields': item['fields']
                }
                for item in chunk
            ]
            
            payload = {'records': batch_records}
            
            try:
                batch_success = self._batch_update_with_retry(payload)
                success_count += batch_success
                print(f"批次 {i+1}/{total_batches}: ✓ 成功更新 {batch_success} 条")
                
            except Exception as e:
                failed_batches.append({
                    'batch': i + 1,
                    'error': str(e),
                    'records': [item.get('product_id', f'unknown_{j}') for j, item in enumerate(chunk)]
                })
                print(f"批次 {i+1}/{total_batches}: ✗ 失败 - {e}")
            
            # 批次间隔，避免过快调用
            time.sleep(0.2)
        
        return {
            'success_count': success_count,
            'failed_batches': failed_batches,
            'total_batches': total_batches
        }
    
    def batch_create(self, records: List[Dict], batch_size: int = 30) -> Dict[str, Any]:
        """
        批量创建记录 - 步骤4实现
        
        Args:
            records: 待创建的记录列表，每个记录包含fields和product_id
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 创建结果统计
        """
        token = self._get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        total_batches = math.ceil(len(records) / batch_size)
        success_count = 0
        failed_batches = []
        
        print(f"开始批量创建 {len(records)} 条记录，分 {total_batches} 个批次...")
        
        for i in range(total_batches):
            chunk = records[i * batch_size:(i + 1) * batch_size]
            batch_records = [
                {
                    'fields': item['fields']
                }
                for item in chunk
            ]
            
            payload = {'records': batch_records}
            
            try:
                batch_success = self._batch_create_with_retry(payload)
                success_count += batch_success
                print(f"批次 {i+1}/{total_batches}: ✓ 成功创建 {batch_success} 条")
                
            except Exception as e:
                failed_batches.append({
                    'batch': i + 1,
                    'error': str(e),
                    'records': [item.get('product_id', f'unknown_{j}') for j, item in enumerate(chunk)]
                })
                print(f"批次 {i+1}/{total_batches}: ✗ 失败 - {e}")
            
            # 批次间隔，避免过快调用
            time.sleep(0.2)
        
        result = {
            'success_count': success_count,
            'failed_batches': failed_batches,
            'total_batches': total_batches
        }
        
        print(f"批量创建完成：成功 {success_count} 条，失败 {len(failed_batches)} 个批次")
        return result
    
    def _get_token(self) -> str:
        """获取飞书访问令牌，支持缓存
        
        Returns:
            str: 访问令牌
        """
        current_time = time.time()
        
        # 检查缓存的token是否还有效（提前5分钟过期）
        if self._cached_token and current_time < (self._token_expires_at - 300):
            return self._cached_token
        
        # 获取新token
        resp = requests.post(
            self.auth_url, 
            json={'app_id': self.app_id, 'app_secret': self.app_secret}, 
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('code') != 0:
            raise RuntimeError(f"获取飞书token失败: {data}")
        
        self._cached_token = data['tenant_access_token']
        # 假设token有效期为2小时
        self._token_expires_at = current_time + 7200
        
        return self._cached_token
    
    def _batch_update_with_retry(self, payload: Dict) -> int:
        """带重试机制的批量更新
        
        Args:
            payload: 更新数据载荷
            
        Returns:
            int: 成功更新的记录数
        """
        token = self._get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(
                    self.batch_update_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                
                if data.get('code') != 0:
                    raise RuntimeError(f"飞书API错误: {data}")
                
                return len(payload['records'])
                
            except requests.exceptions.HTTPError as e:
                # 检查是否是429错误
                if e.response.status_code == 429 or "Too Many Requests" in str(e):
                    if attempt < self.max_retries:
                        backoff_time = 1.0 * (self.backoff_factor ** attempt)
                        print(f"飞书API限流重试，等待{backoff_time}秒...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        raise e
                else:
                    raise e
                    
            except Exception as e:
                error_msg = str(e)
                if "Too Many Requests" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries:
                        backoff_time = 1.0 * (self.backoff_factor ** attempt)
                        print(f"飞书API限流重试，等待{backoff_time}秒...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        raise e
                else:
                    # 非429错误，使用原有的退避策略
                    if attempt == self.max_retries:
                        raise e
                    time.sleep(2 ** attempt)  # 指数退避
        
        return 0
    
    def _batch_create_with_retry(self, payload: Dict) -> int:
        """
        带重试机制的批量创建
        
        Args:
            payload: 创建数据载荷
            
        Returns:
            int: 成功创建的记录数
        """
        token = self._get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(
                    self.batch_create_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                
                if data.get('code') != 0:
                    raise RuntimeError(f"飞书API错误: {data}")
                
                return len(payload['records'])
                
            except requests.exceptions.HTTPError as e:
                # 检查是否是429错误
                if e.response.status_code == 429 or "Too Many Requests" in str(e):
                    if attempt < self.max_retries:
                        backoff_time = 1.0 * (self.backoff_factor ** attempt)
                        print(f"飞书API限流重试，等待{backoff_time}秒...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        raise e
                else:
                    raise e
                    
            except Exception as e:
                error_msg = str(e)
                if "Too Many Requests" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries:
                        backoff_time = 1.0 * (self.backoff_factor ** attempt)
                        print(f"飞书API限流重试，等待{backoff_time}秒...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        raise e
                else:
                    # 非429错误，使用原有的退避策略
                    if attempt == self.max_retries:
                        raise e
                    time.sleep(2 ** attempt)  # 指数退避
        
        return 0