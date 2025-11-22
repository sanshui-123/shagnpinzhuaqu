"""
尺码表格式化工具
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class SizeTableFormatter:
    """将日文尺码信息转换为中文纯文本表格"""

    SIZE_MAP = {
        'XS': 'XS码',
        'S': 'S码',
        'M': 'M码',
        'L': 'L码',
        'LL': 'XL码',
        'XL': 'XL码',
        '3L': '2XL码',
        'XXL': '2XL码',
        '4L': '3XL码',
        'XXXL': '3XL码',
        '5L': '4XL码',
        'フリー': '均码',
        'FREE': '均码'
    }

    MEASURE_MAP = [
        ('バスト', '胸围'),
        ('身幅', '衣宽'),
        ('身丈', '衣长'),
        ('着丈', '衣长'),
        ('裄丈', '袖长(从后领中心到袖口)'),
        ('袖丈', '袖长(从肩点到袖口)'),
        ('肩幅', '肩宽'),
        ('袖口幅', '袖口宽'),
        ('裾幅', '下摆宽'),
        ('前下がり', '前片长度'),
        ('後ろ下がり', '后片长度'),
        ('ウエスト', '腰围'),
        ('最小ウエスト', '最小腰围'),
        ('最大ウエスト', '最大腰围'),
        ('ヒップ', '臀围'),
        ('股下', '裤长'),
        ('股上', '裆长'),
        ('わたり幅', '大腿围'),
        ('総丈', '全长'),
        ('全長', '全长'),
        ('ベルト巾', '腰带宽度'),
        ('バックル巾', '扣头宽度'),
        ('持ち手の高さ(cm)', '提手高度(cm)'),
        ('重さ', '重量'),
        ('原産国', '原产国'),
        ('クロージング', '闭合方式'),
        ('シーズン', '季节')
    ]

    NOTE_KEYWORDS = [
        ('仕上がり', '以上为成品尺寸'),
        ('実寸', '以上为成品尺寸'),
        ('1-2cm', '因面料特性，实际尺寸可能存在1-2cm误差'),
        ('１-２cm', '因面料特性，实际尺寸可能存在1-2cm误差'),
        ('ヌード寸法', '商品标签为净体尺寸，请结合尺码表选择'),
        ('ゆとり', '版型含适度放松量'),
    ]

    DEFAULT_NOTES = [
        '以上为成品尺寸',
        '因面料特性，实际尺寸可能存在1-2cm误差'
    ]

    def build(self, size_text: Optional[str], structured_chart: Optional[Dict]) -> str:
        lines: List[str] = []
        notes: List[str] = []

        # 首先尝试传统格式化
        text_lines, text_notes = self._format_from_text(size_text or '')
        lines.extend(text_lines)
        notes.extend(text_notes)

        if not lines and structured_chart:
            chart_lines, chart_notes = self._format_from_structured(structured_chart)
            lines.extend(chart_lines)
            notes.extend(chart_notes)

        # 检查传统格式化结果是否产生HTML污染
        traditional_result = '\n'.join(lines) if lines else ''

        # 如果传统方法失败或检测到HTML污染，使用AI处理
        if not lines or self._has_html_pollution(traditional_result):
            ai_formatted = self._format_with_ai(size_text or '', structured_chart)
            if ai_formatted:
                return ai_formatted
            # 如果AI处理也失败，但传统结果有污染，尝试清理污染
            elif lines and self._has_html_pollution(traditional_result):
                return self._clean_html_pollution(traditional_result)

        if not lines:
            return ''

        note_block = self._build_note_block(notes)
        return '\n'.join(lines) + note_block

    # ------------------------------------------------------------------ #
    # 内部实现
    # ------------------------------------------------------------------ #

    def _format_from_text(self, text: str) -> Tuple[List[str], List[str]]:
        if not text:
            return [], []

        lines: List[str] = []
        notes: List[str] = []

        normalized_text = text.replace('／', '/').replace('～', '~')
        for raw_line in normalized_text.splitlines():
            line = raw_line.strip(' 　')
            if not line:
                continue

            if line.startswith('※') or any(keyword in line for keyword, _ in self.NOTE_KEYWORDS):
                translated_note = self._translate_note(line)
                if translated_note:
                    notes.append(translated_note)
                continue

            if '/' not in line:
                # 过滤标题，例如"商品サイズ"
                continue

            segments = [seg.strip() for seg in line.split('/') if seg.strip()]
            if len(segments) < 2:
                continue

            size_label = self._map_size_label(segments[0])
            if not size_label:
                continue

            measurement_parts: List[str] = []
            for segment in segments[1:]:
                name, value = self._translate_measurement(segment)
                if name and value:
                    measurement_parts.append(f"{name}{value}")

            if measurement_parts:
                lines.append(f"【{size_label}】" + " | ".join(measurement_parts))

        return lines, notes

    def _format_from_html_text(self, html_or_text: str) -> Tuple[List[str], List[str]]:
        """从HTML或文本格式解析尺码表信息"""
        if not html_or_text:
            return [], []

        lines = []
        notes = []

        # 如果包含HTML标签，尝试解析HTML表格
        if '<table' in html_or_text:
            try:
                import re

                # 提取表格内容
                table_content = self._extract_table_from_html(html_or_text)
                if table_content:
                    lines.extend(table_content)
                    return lines, []
            except Exception as e:
                # HTML解析失败，回退到文本解析
                pass

        # 从文本中提取键值对信息
        lines, notes = self._format_from_text(html_or_text)
        return lines, notes

    def _extract_table_from_html(self, html: str) -> List[str]:
        """从HTML表格中提取尺码表信息"""
        import re

        # 提取表格中的行
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(tr_pattern, html, re.DOTALL)

        extracted_lines = []
        table_headers = []  # 存储表头
        table_data = []     # 存储数据行

        for row in rows:
            # 同时提取表头(th)和单元格(td)
            th_pattern = r'<th[^>]*>(.*?)</th>'
            td_pattern = r'<td[^>]*>(.*?)</td>'

            headers = re.findall(th_pattern, row, re.DOTALL)
            cells = re.findall(td_pattern, row, re.DOTALL)

            # 清理HTML标签并提取文本
            clean_headers = []
            for header in headers:
                clean_text = re.sub(r'<[^>]+>', '', header).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)  # 合并多个空格
                if clean_text:
                    clean_headers.append(clean_text)

            clean_cells = []
            for cell in cells:
                # 移除HTML标签
                clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)  # 合并多个空格
                if clean_text:
                    clean_cells.append(clean_text)

            # 如果这一行只有表头，保存为表头
            if clean_headers and not clean_cells:
                if not table_headers:  # 只保存第一行表头
                    table_headers = clean_headers
            # 如果这一行有数据单元格
            elif clean_cells:
                # 第一个单元格可能是th（尺码），其余是td（数据）
                if clean_headers:
                    # 表头+单元格的组合（例如：<th>4</th><td>108cm</td><td>64.5cm</td>...）
                    row_data = clean_headers + clean_cells
                else:
                    row_data = clean_cells
                table_data.append(row_data)

        # 如果没有找到表头和数据，返回空
        if not table_data:
            return []

        # 翻译表头
        translated_headers = []
        for header in table_headers:
            # 跳过纯商品编号和品牌信息
            if any(keyword in header for keyword in ['商品番号', 'ブランド商品番号', 'ブランド名']):
                continue
            translated = self._translate_measurement_name(header)
            translated_headers.append(translated if translated != header else header)

        # 格式化每一行数据
        for row_data in table_data:
            if not row_data:
                continue

            # 第一个元素是尺码
            size_value = row_data[0]
            size_label = self._map_size_label(str(size_value))
            if not size_label:
                size_label = f"{size_value}码"

            # 其余元素是测量数据
            measurements = []
            for idx, value in enumerate(row_data[1:]):
                value_str = str(value).strip()
                if not value_str:
                    continue

                # 如果有表头，使用翻译后的表头名
                if idx < len(translated_headers) - 1:  # -1 因为第一个表头是"サイズ"
                    header_name = translated_headers[idx + 1]
                    measurements.append(f"{header_name}{value_str}")
                else:
                    measurements.append(value_str)

            if measurements:
                extracted_lines.append(f"{size_label}: {' | '.join(measurements)}")

        return extracted_lines

    def _format_from_structured(self, chart: Dict) -> Tuple[List[str], List[str]]:
        # 优先处理新的 text/html 格式（我们的JSON格式）
        # 优先使用html字段，因为它包含完整的表格结构
        html_content = chart.get('html', '') or chart.get('text', '')
        if html_content:
            return self._format_from_html_text(html_content)

        # 兼容旧的 headers/rows 格式
        headers = chart.get('headers') or []
        rows = chart.get('rows') or []
        if not headers or not rows:
            return [], []

        size_header = headers[0]
        measure_headers = headers[1:]
        translated_headers = [self._translate_measurement_name(h) for h in measure_headers]

        lines: List[str] = []
        for row in rows:
            if not row:
                continue
            size_value = row[0]
            size_label = self._map_size_label(str(size_value))
            if not size_label:
                continue

            measurements = []
            for idx, value in enumerate(row[1:]):
                if idx >= len(translated_headers):
                    break
                header_name = translated_headers[idx]
                value_str = str(value).strip()
                if header_name and value_str:
                    measurements.append(f"{header_name}{value_str}")

            if measurements:
                lines.append(f"【{size_label}】" + " | ".join(measurements))

        return lines, []

    def _map_size_label(self, token: str) -> str:
        if not token:
            return ''
        normalized = token.upper()
        normalized = re.sub(r'サイズ', '', normalized)
        normalized = normalized.strip()
        if normalized in self.SIZE_MAP:
            return self.SIZE_MAP[normalized]
        if normalized.endswith('L') and normalized[:-1].isdigit():
            # 2L,3L结构
            mapping = {
                '2L': 'XL码',
                '3L': '2XL码',
                '4L': '3XL码',
                '5L': '4XL码'
            }
            return mapping.get(normalized, f"{normalized}码")
        if normalized:
            return f"{normalized}码"
        return ''

    def _translate_measurement(self, segment: str) -> Tuple[str, str]:
        cleaned = segment.replace('：', ' ').replace(':', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if not cleaned:
            return '', ''

        match = re.match(r'([^\d]+)\s*(.+)', cleaned)
        if not match:
            return '', ''

        label = match.group(1).strip()
        value = match.group(2).strip()

        translated_label = self._translate_measurement_name(label)
        return translated_label, value

    def _translate_measurement_name(self, label: str) -> str:
        for jp, cn in self.MEASURE_MAP:
            if label.startswith(jp):
                return cn
        return label

    def _translate_note(self, line: str) -> Optional[str]:
        normalized = line.lstrip('※').strip()
        for keyword, note in self.NOTE_KEYWORDS:
            if keyword in normalized:
                return note
        return None

    def _build_note_block(self, extra_notes: List[str]) -> str:
        notes = []
        seen = set()
        for note in self.DEFAULT_NOTES + extra_notes:
            if note and note not in seen:
                seen.add(note)
                notes.append(note)

        if not notes:
            return ''

        note_lines = '\n'.join(f"- {note}" for note in notes)
        return f"\n\n尺码说明:\n{note_lines}"

    def _has_html_pollution(self, text: str) -> bool:
        """检测文本中是否包含HTML污染"""
        if not text:
            return False
        # 检查常见的HTML污染模式
        pollution_patterns = [
            r'【<[^>]*>】',  # 【<td>】, 【<th>】 等
            r'【<码[^>]*>】',  # 【<码】th>, 【<码】td】 等实际污染模式
            r'<td>.*?</td>',
            r'<th>.*?</th>',
            r'<tr>.*?</tr>',
            r'<table>.*?</table>',
            r'【.*?TD.*?】',  # 【TD】形式的污染
            r'【.*?TH.*?】',  # 【TH】形式的污染
            r'【TD',  # 【TD 开始
            r'【TH',  # 【TH 开始
        ]
        for pattern in pollution_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True
        return False

    def _format_with_ai(self, size_text: str, structured_chart: Optional[Dict]) -> str:
        """使用AI格式化被HTML污染的尺码表"""
        try:
            import os
            import requests
            import time
            import threading

            # GLM API配置
            api_key = os.environ.get('GLM_API_KEY', '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW')
            base_url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

            # 准备输入内容
            input_content = size_text
            if structured_chart:
                if structured_chart.get('text'):
                    input_content = structured_chart['text']
                elif structured_chart.get('html'):
                    input_content = structured_chart['html']

            if not input_content:
                return ''

            # 构建新的尺码表处理提示词
            prompt = f"""将以下日本服装尺码表整理成简洁易读的格式：

原始数据：
{input_content}

要求：
1. 使用中文说明各项尺寸含义
2. 每个尺码占一行
3. 格式：S码 | 胸围66 肩宽48 衣长104 袖长61 下摆21
4. 去除HTML标签，只保留纯文本
5. 添加尺码说明（成品尺寸，1-2cm误差）

期望输出格式示例：
S码 | 胸围66 肩宽48 衣长104 袖长61 下摆21
M码 | 胸围68 肩宽49 衣长108 袖长62 下摆22
L码 | 胸围70 肩宽50 衣长112 袖长63 下摆23
XL码 | 胸围72 肩宽51 衣长116 袖长64 下摆24
*成品尺寸，因面料特性可能存在1-2cm误差

注意：
- 将66转换为S码，68转换为M码，70转换为L码，72转换为XL码
- 如果数据不足，请尽力整理可用信息
- 保持格式整洁易读
- 不要添加无关的解释文字
- 直接输出格式化结果，不要开场白"""

            # 调用GLM API（使用简化的限流机制）
            with threading.Lock():
                # 简单的限流
                time.sleep(0.6)

                response = requests.post(
                    base_url,
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'glm-4.6',
                        'messages': [
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ],
                        'max_tokens': 800,
                        'temperature': 0.3
                    },
                    timeout=30
                )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    if content and content.strip():
                        return content.strip()

            return ''

        except Exception as e:
            # 任何异常立即返回空字符串，不打印（由build()统一处理）
            return ''

    def _clean_html_pollution(self, text: str) -> str:
        """清理HTML污染，提取有效的数字数据"""
        if not text:
            return ''

        # 提取所有数字（包括逗号分隔的数字）
        numbers = re.findall(r'\d+(?:,\d+)*', text)

        if not numbers:
            return ''

        # 尺码映射：将数字转换为用户友好的尺码
        size_mapping = {
            '66': 'S码',
            '68': 'M码',
            '70': 'L码',
            '72': 'XL码'
        }

        # 根据数字数量推断格式
        if len(numbers) >= 15:  # 可能是多行多列的尺码表
            # 尝试按5列分组（常见的尺码表格式）
            rows = []
            for i in range(0, len(numbers), 5):
                if i + 4 < len(numbers):  # 确保有5个数据
                    size_num = numbers[i]
                    # 映射为用户友好的尺码
                    size_label = size_mapping.get(size_num, f"{size_num}码")
                    row = f"{size_label} | 胸围{size_num} 肩宽{numbers[i+1]} 衣长{numbers[i+2]} 袖长{numbers[i+3]} 下摆{numbers[i+4]}"
                    rows.append(row)

            if rows:
                result = '\n'.join(rows)
                return f"{result}\n*成品尺寸，因面料特性可能存在1-2cm误差"

        # 如果数据不足，返回简单的数字列表
        return f"尺码数据: {', '.join(numbers[:10])}\n*以上为成品尺寸"
